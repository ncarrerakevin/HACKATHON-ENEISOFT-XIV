from neo4j import GraphDatabase
import json
import os

class Neo4jLoader:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def analyze_json_structure(self, data):
        print("\nAnalizando estructura del JSON:")
        for record in data['records'][:5]:  # Analizamos los primeros 5 registros como muestra
            compile_release = record.get('compiledRelease', {})
            print("\nRegistro ID:", compile_release.get('id'))

            # Analizar partes involucradas
            parties = compile_release.get('parties', [])
            print(f"Número de parties: {len(parties)}")
            for party in parties:
                print("\nParte involucrada:")
                print(f"- ID: {party.get('id')}")
                print(f"- Roles: {party.get('roles', [])}")
                if 'address' in party:
                    print(f"- Dirección:")
                    print(f"  - Region: {party['address'].get('region')}")
                    print(f"  - Department: {party['address'].get('department')}")
                    print(f"  - Locality: {party['address'].get('locality')}")

            # Analizar proveedores en adjudicaciones
            awards = compile_release.get('awards', [])
            print(f"\nNúmero de awards: {len(awards)}")
            for award in awards:
                suppliers = award.get('suppliers', [])
                print(f"\nProveedores en award {award.get('id')}:")
                for supplier in suppliers:
                    print(f"- ID: {supplier.get('id')}")
                    if 'address' in supplier:
                        print(f"  Dirección:")
                        print(f"  - Region: {supplier['address'].get('region')}")
                        print(f"  - Department: {supplier['address'].get('department')}")

    def cleanup_database(self):
        with self.driver.session() as session:
            print("Eliminando constraints existentes...")
            try:
                result = session.run("SHOW CONSTRAINTS")
                constraints = [record['name'] for record in result]
                for constraint in constraints:
                    session.run(f"DROP CONSTRAINT {constraint}")
            except Exception as e:
                print(f"Nota al eliminar constraints: {e}")

            print("Eliminando todos los nodos y relaciones...")
            session.run("MATCH (n) DETACH DELETE n")
            print("Base de datos limpiada exitosamente!")

    def verify_data_before_load(self, data):
        """Verifica y limpia los datos antes de cargarlos"""
        print("\nVerificando datos antes de cargar...")

        # Verificar duplicados de ocid
        ocids = {}
        for record in data['records']:
            ocid = record.get('compiledRelease', {}).get('ocid')
            if ocid:
                if ocid in ocids:
                    ocids[ocid].append(record)
                else:
                    ocids[ocid] = [record]

        # Mantener solo el registro más reciente para cada ocid
        cleaned_records = []
        duplicates_removed = 0
        for ocid, records in ocids.items():
            if len(records) > 1:
                # Ordenar por fecha de publicación y tomar el más reciente
                sorted_records = sorted(
                    records,
                    key=lambda x: x.get('compiledRelease', {}).get('publishedDate', ''),
                    reverse=True
                )
                cleaned_records.append(sorted_records[0])
                duplicates_removed += len(records) - 1
                print(f"- Removiendo {len(records) - 1} duplicados para OCID {ocid}")
            else:
                cleaned_records.append(records[0])

        print(f"- Total de registros duplicados removidos: {duplicates_removed}")
        print(f"- Registros originales: {len(data['records'])}")
        print(f"- Registros después de limpieza: {len(cleaned_records)}")

        # Verificar contratos sin award
        contracts_without_award = 0
        for record in cleaned_records:
            contracts = record.get('compiledRelease', {}).get('contracts', [])
            for contract in contracts:
                if not contract.get('awardID'):
                    contracts_without_award += 1

        if contracts_without_award > 0:
            print(f"- ¡Advertencia! {contracts_without_award} contratos sin award detectados")

        return {'records': cleaned_records}

    def load_data(self, data):
        try:
            # Primero limpiamos y verificamos los datos
            cleaned_data = self.verify_data_before_load(data)

            self.analyze_json_structure(cleaned_data)

            print("\n1. Limpiando base de datos existente...")
            self.cleanup_database()

            # Usamos cleaned_data en lugar de data para todas las operaciones
            data = cleaned_data  # Esta es la línea clave

            print("\n2. Creando nuevos constraints...")
            with self.driver.session() as session:
                constraints = [
                    "CREATE CONSTRAINT buyer_id IF NOT EXISTS FOR (b:Buyer) REQUIRE b.id IS UNIQUE",
                    "CREATE CONSTRAINT item_id IF NOT EXISTS FOR (i:Item) REQUIRE i.id IS UNIQUE",
                    "CREATE CONSTRAINT award_id IF NOT EXISTS FOR (a:Award) REQUIRE a.id IS UNIQUE",
                    "CREATE CONSTRAINT contract_id IF NOT EXISTS FOR (c:Contract) REQUIRE c.id IS UNIQUE",
                    "CREATE CONSTRAINT procurement_ocid IF NOT EXISTS FOR (p:Procurement) REQUIRE p.ocid IS UNIQUE"
                ]
                for constraint in constraints:
                    try:
                        session.run(constraint)
                    except Exception as e:
                        print(f"Nota al crear constraint: {e}")

            print("\n3. Cargando compradores con información extendida...")
            with self.driver.session() as session:
                session.run("""
                    UNWIND $records AS record
                    WITH record
                    WHERE record.compiledRelease.buyer IS NOT NULL AND record.compiledRelease.buyer.id IS NOT NULL
                    MERGE (b:Buyer {id: record.compiledRelease.buyer.id})
                    ON CREATE SET
                        b.name = record.compiledRelease.buyer.name,
                        b.ruc = COALESCE(record.compiledRelease.parties[0].additionalIdentifiers[0].id, "N/A"),
                        b.address = COALESCE(record.compiledRelease.parties[0].address.streetAddress, "No Address"),
                        b.contactPoint = COALESCE(record.compiledRelease.parties[0].contactPoint.name, "No Contact"),
                        b.email = COALESCE(record.compiledRelease.parties[0].contactPoint.email, "No Email"),
                        b.telephone = COALESCE(record.compiledRelease.parties[0].contactPoint.telephone, "No Phone")
                """, records=data['records'])

            print("4. Cargando contrataciones...")
            with self.driver.session() as session:
                session.run("""
                UNWIND $records AS record
                WITH record
                WHERE record.compiledRelease.tender IS NOT NULL 
                      AND record.compiledRelease.ocid IS NOT NULL
                MERGE (p:Procurement {ocid: record.compiledRelease.ocid})
                ON CREATE SET
                    p.id = record.compiledRelease.tender.id,
                    p.title = COALESCE(record.compiledRelease.tender.title, "No Title"),
                    p.description = COALESCE(record.compiledRelease.tender.description, "No Description"),
                    p.publishedDate = datetime(record.compiledRelease.publishedDate),
                    p.procurementMethod = COALESCE(record.compiledRelease.tender.procurementMethod, "N/A"),
                    p.procurementMethodDetails = COALESCE(record.compiledRelease.tender.procurementMethodDetails, "N/A"),
                    p.mainCategory = COALESCE(record.compiledRelease.tender.mainProcurementCategory, "No Category")
                """, records=data['records'])

            print("5. Cargando ítems...")
            # Primero, recopilamos todos los ítems únicos
            unique_items = {}
            for record in data['records']:
                items = record.get('compiledRelease', {}).get('tender', {}).get('items', [])
                for item in items:
                    if item.get('id') and item.get('id') not in unique_items:
                        unique_items[item['id']] = {
                            'id': item['id'],
                            'description': item.get('description', "No Description"),
                            'status': item.get('status', "No Status"),
                            'quantity': item.get('quantity', 0)
                        }

            with self.driver.session() as session:
                for item in unique_items.values():
                    session.run("""
                    MERGE (i:Item {id: $id})
                    ON CREATE SET
                        i.description = $description,
                        i.status = $status,
                        i.quantity = $quantity
                    """, item)

            print("6. Cargando adjudicaciones...")
            with self.driver.session() as session:
                session.run("""
                UNWIND $records AS record
                UNWIND COALESCE(record.compiledRelease.awards, []) AS award
                WITH award
                WHERE award.id IS NOT NULL
                MERGE (a:Award {id: award.id})
                ON CREATE SET
                    a.title = COALESCE(award.title, "No Title"),
                    a.value = COALESCE(award.value.amount, 0),
                    a.currency = COALESCE(award.value.currency, "N/A"),
                    a.date = COALESCE(award.date, null)
                """, records=data['records'])

            # Modificación en la carga de contratos para asegurar la relación con Award
            print("7. Cargando contratos...")
            with self.driver.session() as session:
                session.run("""
                            UNWIND $records AS record
                            UNWIND COALESCE(record.compiledRelease.contracts, []) AS contract
                            WITH contract
                            WHERE contract.id IS NOT NULL 
                              AND contract.awardID IS NOT NULL
                              // Aseguramos que existe el Award antes de crear el Contract
                              AND EXISTS {
                                MATCH (a:Award {id: contract.awardID})
                                RETURN a
                              }
                            MERGE (c:Contract {id: contract.id})
                            ON CREATE SET
                                c.title = COALESCE(contract.title, "No Title"),
                                c.description = COALESCE(contract.description, "No Description"),
                                c.value = COALESCE(contract.value.amount, 0),
                                c.currency = COALESCE(contract.value.currency, "N/A"),
                                c.awardID = contract.awardID,
                                c.status = COALESCE(contract.status, "No Status")
                            """, records=data['records'])  # Cambiado cleaned_data por data

            print("8. Cargando proveedores con información extendida...")
            with self.driver.session() as session:
                session.run("""
                    UNWIND $records AS record
                    UNWIND COALESCE(record.compiledRelease.awards, []) AS award
                    UNWIND COALESCE(award.suppliers, []) AS supplier
                    WITH supplier, award, record
                    WHERE supplier.id IS NOT NULL
                    MERGE (s:Supplier {id: supplier.id})
                    ON CREATE SET
                        s.name = COALESCE(supplier.name, "No Name"),
                        s.ruc = COALESCE(supplier.identifier.id, "No RUC"),
                        s.legalName = COALESCE(supplier.identifier.legalName, "No Legal Name"),
                        s.address = COALESCE(supplier.address.streetAddress, "No Address")
                """, records=data['records'])

            print("9. Creando relaciones...")
            with self.driver.session() as session:
                # Relaciones Buyer-Procurement
                session.run("""
                                UNWIND $records AS record
                                WITH record
                                WHERE record.compiledRelease.buyer IS NOT NULL
                                MATCH (b:Buyer {id: record.compiledRelease.buyer.id})
                                MATCH (p:Procurement {ocid: record.compiledRelease.ocid})
                                MERGE (b)-[:PUBLISHED]->(p)
                                """, records=data['records'])

                # Relaciones Procurement-Item
                session.run("""
                            UNWIND $records AS record
                            UNWIND COALESCE(record.compiledRelease.tender.items, []) AS item
                            WITH record, item
                            WHERE item.id IS NOT NULL
                            MATCH (p:Procurement {ocid: record.compiledRelease.ocid})
                            MATCH (i:Item {id: item.id})
                            MERGE (p)-[:INCLUDES]->(i)
                            """, records=data['records'])

                # Relaciones Award-Supplier
                session.run("""
                            UNWIND $records AS record
                            UNWIND COALESCE(record.compiledRelease.awards, []) AS award
                            UNWIND COALESCE(award.suppliers, []) AS supplier
                            WITH award, supplier
                            WHERE award.id IS NOT NULL AND supplier.id IS NOT NULL
                            MATCH (a:Award {id: award.id})
                            MATCH (s:Supplier {id: supplier.id})
                            MERGE (a)-[:AWARDED_TO]->(s)
                            """, records=data['records'])

                # Relaciones Procurement-Award
                session.run("""
                            UNWIND $records AS record
                            UNWIND COALESCE(record.compiledRelease.awards, []) AS award
                            WITH record, award
                            WHERE award.id IS NOT NULL
                            MATCH (p:Procurement {ocid: record.compiledRelease.ocid})
                            MATCH (a:Award {id: award.id})
                            MERGE (p)-[:HAS_AWARD]->(a)
                            """, records=data['records'])

                # Relaciones Award-Contract
                session.run("""
                            UNWIND $records AS record
                            UNWIND COALESCE(record.compiledRelease.contracts, []) AS contract
                            WITH contract
                            WHERE contract.id IS NOT NULL AND contract.awardID IS NOT NULL
                            MATCH (a:Award {id: contract.awardID})
                            MATCH (c:Contract {id: contract.id})
                            MERGE (a)-[:HAS_CONTRACT]->(c)
                            """, records=data['records'])

                print("\nCreando relaciones adicionales para análisis de patrones...")

                # 1. Relaciones temporales entre contrataciones del mismo comprador (ajustado)
                session.run("""
                                MATCH (p1:Procurement)-[:PUBLISHED]-(b:Buyer)-[:PUBLISHED]-(p2:Procurement)
                                WHERE p1.publishedDate <= p2.publishedDate
                                AND p1 <> p2
                                AND datetime(p1.publishedDate) IS NOT NULL 
                                AND datetime(p2.publishedDate) IS NOT NULL
                                AND duration.inDays(datetime(p1.publishedDate), datetime(p2.publishedDate)).days <= 30
                                MERGE (p1)-[r:RELATED_TIME]->(p2)
                                SET r.daysBetween = duration.inDays(datetime(p1.publishedDate), datetime(p2.publishedDate)).days,
                                    r.sameCategory = p1.mainCategory = p2.mainCategory
                                """)

                # 2. Análisis detallado de proveedores frecuentes
                session.run("""
                                MATCH (s:Supplier)<-[:AWARDED_TO]-(a:Award)
                                WITH s, count(a) as awards_count, collect(a) as awards,
                                     sum(a.value) as total_value,
                                     collect(DISTINCT a.currency) as currencies
                                WHERE awards_count >= 3
                                SET s.highFrequencySupplier = true,
                                    s.totalAwards = awards_count,
                                    s.totalValue = total_value,
                                    s.averageAwardValue = total_value / awards_count,
                                    s.currencies = currencies,
                                    s.riskLevel = CASE 
                                        WHEN awards_count >= 10 THEN 'ALTO'
                                        WHEN awards_count >= 5 THEN 'MEDIO'
                                        ELSE 'BAJO'
                                    END
                                """)

                # 3. Identificar adjudicaciones rápidas con más detalle
                session.run("""
                                MATCH (p:Procurement)-[:HAS_AWARD]->(a:Award)
                                WHERE a.date IS NOT NULL 
                                AND p.publishedDate IS NOT NULL
                                AND datetime(a.date) IS NOT NULL
                                AND datetime(p.publishedDate) IS NOT NULL
                                WITH p, a, duration.inDays(datetime(p.publishedDate), datetime(a.date)).days as days
                                WHERE days <= 3
                                SET p.quickAward = true,
                                    p.awardDays = days,
                                    p.awardSpeed = CASE 
                                        WHEN days = 0 THEN 'MISMO_DIA'
                                        WHEN days = 1 THEN 'UN_DIA'
                                        ELSE 'DOS_A_TRES_DIAS'
                                    END,
                                    p.riskLevel = CASE 
                                        WHEN days = 0 THEN 'ALTO'
                                        WHEN days = 1 THEN 'MEDIO'
                                        ELSE 'BAJO'
                                    END
                                """)

                # 4. Análisis detallado de montos inusuales por categoría
                session.run("""
                                MATCH (p:Procurement)-[:HAS_AWARD]->(a:Award)
                                WITH p.mainCategory as category, 
                                     avg(a.value) as avgValue, 
                                     stDev(a.value) as stdValue,
                                     collect(a) as awards,
                                     count(a) as total_awards
                                MATCH (p2:Procurement)-[:HAS_AWARD]->(a2:Award)
                                WHERE p2.mainCategory = category
                                AND a2.value > (avgValue + 2 * stdValue)
                                SET a2.unusualAmount = true,
                                    a2.categoryAvg = avgValue,
                                    a2.categoryStdDev = stdValue,
                                    a2.deviation = (a2.value - avgValue) / stdValue,
                                    a2.percentileRank = toFloat(size([a IN awards WHERE a.value <= a2.value])) / total_awards * 100,
                                    a2.riskLevel = CASE 
                                        WHEN a2.value > (avgValue + 3 * stdValue) THEN 'ALTO'
                                        ELSE 'MEDIO'
                                    END
                                """)

                # 5. Análisis detallado de patrones regionales
                session.run("""
                                MATCH (s1:Supplier)<-[:AWARDED_TO]-(:Award)<-[:HAS_AWARD]-(p:Procurement)
                                MATCH (s2:Supplier)<-[:AWARDED_TO]-(:Award)<-[:HAS_AWARD]-(p)
                                WHERE s1.region = s2.region 
                                AND s1 <> s2
                                AND s1.id < s2.id
                                WITH s1, s2, p.region as buyer_region, count(DISTINCT p) as shared_procurements
                                MERGE (s1)-[r:REGIONAL_COOPERATION]->(s2)
                                SET r.sharedProcurements = shared_procurements,
                                    r.buyerRegion = buyer_region,
                                    r.sameRegionAsBuyer = buyer_region = s1.region,
                                    r.riskLevel = CASE 
                                        WHEN shared_procurements >= 5 THEN 'ALTO'
                                        WHEN shared_procurements >= 3 THEN 'MEDIO'
                                        ELSE 'BAJO'
                                    END
                                """)

                # 6. Análisis de fraccionamiento (nuevo)
                session.run("""
                                MATCH (b:Buyer)-[:PUBLISHED]->(p:Procurement)-[:HAS_AWARD]->(a:Award)
                                WITH b, p.mainCategory as category,
                                     date(p.publishedDate) as baseDate,
                                     sum(a.value) as total_value,
                                     count(p) as proc_count
                                WHERE proc_count >= 3
                                SET b.potentialSplitting = true,
                                    b.splittingCategory = category,
                                    b.splittingDate = baseDate,
                                    b.splittingValue = total_value,
                                    b.splittingCount = proc_count,
                                    b.riskLevel = CASE 
                                        WHEN proc_count >= 5 THEN 'ALTO'
                                        WHEN proc_count >= 3 THEN 'MEDIO'
                                        ELSE 'BAJO'
                                    END
                                """)

                # Modificar el análisis de concentración regional
                print("\nAnálisis de concentración regional...")
                session.run("""
                        MATCH (s:Supplier)<-[:AWARDED_TO]-(a:Award)
                        WHERE s.region <> 'No Region'  // Excluir explícitamente "No Region"
                        WITH s.region as region, 
                             count(DISTINCT s) as supplier_count,
                             sum(a.value) as total_value,
                             collect(DISTINCT s) as suppliers
                        WHERE region IS NOT NULL
                        WITH region, supplier_count, total_value, 
                             CASE 
                                 WHEN supplier_count <= 3 THEN 'ALTA'
                                 WHEN supplier_count <= 5 THEN 'MEDIA'
                                 ELSE 'BAJA'
                             END as concentration
                        ORDER BY total_value DESC
                        LIMIT 5
                        RETURN region, concentration, supplier_count, total_value
                    """)

                # Modificar la consulta de estadísticas regionales
                region_stats = session.run("""
                        MATCH (s:Supplier)<-[:AWARDED_TO]-(a:Award)
                        WHERE s.region <> 'No Region'  // Excluir explícitamente "No Region"
                        WITH s.region as region,
                             count(DISTINCT s) as supplier_count,
                             sum(a.value) as total_value
                        WHERE region IS NOT NULL
                        WITH region, supplier_count, total_value
                        ORDER BY total_value DESC
                        LIMIT 5
                        RETURN 
                            region,
                            supplier_count,
                            total_value,
                            CASE 
                                WHEN supplier_count <= 3 THEN 'ALTA'
                                WHEN supplier_count <= 5 THEN 'MEDIA'
                                ELSE 'BAJA'
                            END as concentration
                    """).data()

                print("\nTop 5 regiones por concentración de contratos:")
                for stat in region_stats:
                    print(f"Región: {stat['region']}")
                    print(f"- Concentración: {stat['concentration']}")
                    print(f"- Proveedores: {stat['supplier_count']}")
                    print(f"- Valor total: S/. {stat['total_value']:,.2f}")
                    print("---")

                # Análisis de variación temporal de montos
                session.run("""
                            MATCH (p:Procurement)-[:HAS_AWARD]->(a:Award)
                            WHERE p.publishedDate IS NOT NULL
                            WITH p, date(p.publishedDate) as award_date, avg(a.value) as avg_daily_value, count(a) as daily_awards
                            SET p.avgDailyValue = avg_daily_value,
                                p.dailyAwards = daily_awards,
                                p.unusualDailyActivity = CASE
                                    WHEN daily_awards >= 10 THEN 'ALTO'
                                    WHEN daily_awards >= 5 THEN 'MEDIO'
                                    ELSE 'NORMAL'
                                END
                            """)

                temporal_stats = session.run("""
                            MATCH (p:Procurement)
                            WHERE p.unusualDailyActivity = 'ALTO'
                            RETURN count(p) as high_activity_days,
                                   avg(p.dailyAwards) as avg_awards_per_day,
                                   max(p.dailyAwards) as max_awards_per_day
                            """).single()

                print("\nEstadísticas de actividad diaria:")
                print(f"- Días con actividad inusual: {temporal_stats['high_activity_days']}")
                print(
                    f"- Promedio de adjudicaciones en días de alta actividad: {temporal_stats['avg_awards_per_day']:.2f}")
                print(f"- Máximo de adjudicaciones en un día: {temporal_stats['max_awards_per_day']}")

                print("Relaciones adicionales creadas exitosamente")

                # Estadísticas detalladas (mejorada)
                stats = session.run("""
                                MATCH (p:Procurement)
                                WHERE p.quickAward = true AND p.awardSpeed IS NOT NULL
                                WITH 
                                    count(p) as quick_awards,
                                    count(CASE WHEN p.awardSpeed = 'MISMO_DIA' THEN p END) as same_day,
                                    count(CASE WHEN p.awardSpeed = 'UN_DIA' THEN p END) as one_day,
                                    count(CASE WHEN p.awardSpeed = 'DOS_A_TRES_DIAS' THEN p END) as two_to_three_days
                                RETURN 
                                    quick_awards, 
                                    same_day, 
                                    one_day,
                                    two_to_three_days,
                                    round(100.0 * same_day / quick_awards, 2) as same_day_percentage,
                                    round(100.0 * one_day / quick_awards, 2) as one_day_percentage
                                """).single()

                print("\nEstadísticas detalladas de adjudicaciones rápidas:")
                print(f"- Total adjudicaciones rápidas: {stats['quick_awards']}")
                print(f"- Mismo día: {stats['same_day']} ({stats['same_day_percentage']}%)")
                print(f"- Un día: {stats['one_day']} ({stats['one_day_percentage']}%)")
                print(f"- 2-3 días: {stats['two_to_three_days']}")

                # Análisis de proveedores de alto riesgo
                high_risk = session.run("""
                                MATCH (s:Supplier)
                                WHERE s.riskLevel = 'ALTO'
                                RETURN count(s) as count, avg(s.totalValue) as avg_value
                                """).single()

                print(f"- Proveedores de alto riesgo: {high_risk['count']}")
                print(f"- Valor promedio de contratos de alto riesgo: {high_risk['avg_value']:,.2f}")

            print("\n¡Datos cargados exitosamente!")
            self.verify_data_load()
            self.verify_data_integrity()


        except Exception as e:
            print(f"Error durante la carga de datos: {e}")
            raise e

    def verify_data_load(self):
        with self.driver.session() as session:
            print("\nVerificación de datos cargados:")
            # Conteo de nodos
            buyers = session.run("MATCH (b:Buyer) RETURN count(b) AS count").single()["count"]
            procurements = session.run("MATCH (p:Procurement) RETURN count(p) AS count").single()["count"]
            items = session.run("MATCH (i:Item) RETURN count(i) AS count").single()["count"]
            awards = session.run("MATCH (a:Award) RETURN count(a) AS count").single()["count"]
            contracts = session.run("MATCH (c:Contract) RETURN count(c) AS count").single()["count"]
            suppliers = session.run("MATCH (s:Supplier) RETURN count(s) AS count").single()["count"]

            print(f"- Buyers: {buyers}")
            print(f"- Procurements: {procurements}")
            print(f"- Items: {items}")
            print(f"- Awards: {awards}")
            print(f"- Contracts: {contracts}")
            print(f"- Suppliers: {suppliers}")

            # Conteo de relaciones básicas
            buyer_proc = session.run("MATCH ()-[r:PUBLISHED]->() RETURN count(r) AS count").single()["count"]
            proc_items = session.run("MATCH ()-[r:INCLUDES]->() RETURN count(r) AS count").single()["count"]
            award_suppliers = session.run("MATCH ()-[r:AWARDED_TO]->() RETURN count(r) AS count").single()["count"]
            proc_awards = session.run("MATCH ()-[r:HAS_AWARD]->() RETURN count(r) AS count").single()["count"]
            award_contracts = session.run("MATCH ()-[r:HAS_CONTRACT]->() RETURN count(r) AS count").single()["count"]

            print(f"- Relaciones Buyer-Procurement: {buyer_proc}")
            print(f"- Relaciones Procurement-Item: {proc_items}")
            print(f"- Relaciones Award-Supplier: {award_suppliers}")
            print(f"- Relaciones Procurement-Award: {proc_awards}")
            print(f"- Relaciones Award-Contract: {award_contracts}")

            # Conteo de patrones de riesgo
            related_time = session.run("MATCH ()-[r:RELATED_TIME]->() RETURN count(r) AS count").single()["count"]
            high_freq_suppliers = \
            session.run("MATCH (s:Supplier) WHERE s.highFrequencySupplier = true RETURN count(s) AS count").single()[
                "count"]
            quick_awards = \
            session.run("MATCH (p:Procurement) WHERE p.quickAward = true RETURN count(p) AS count").single()["count"]
            unusual_amounts = \
            session.run("MATCH (a:Award) WHERE a.unusualAmount = true RETURN count(a) AS count").single()["count"]
            regional_coop = session.run("MATCH ()-[r:REGIONAL_COOPERATION]->() RETURN count(r) AS count").single()[
                "count"]

            print("\nPatrones de riesgo detectados:")
            print(f"- Contrataciones relacionadas temporalmente: {related_time}")
            print(f"- Proveedores de alta frecuencia: {high_freq_suppliers}")
            print(f"- Adjudicaciones rápidas: {quick_awards}")
            print(f"- Montos inusuales: {unusual_amounts}")
            print(f"- Cooperaciones regionales: {regional_coop}")

    def verify_data_integrity(self):
        print("\nVerificando integridad de los datos:")
        with self.driver.session() as session:
            print("\n1. Verificando IDs y duplicados...")
            result = session.run("""
            MATCH (p:Procurement)
            WITH p.ocid as ocid, COUNT(*) as count
            WHERE count > 1
            RETURN ocid, count as duplicate_count
            """)
            for record in result:
                print(f"¡Advertencia! OCID {record['ocid']} está duplicado {record['duplicate_count']} veces")

            print("\n2. Verificando relaciones...")
            orphan_procs = session.run("""
            MATCH (p:Procurement)
            WHERE NOT (()-[:PUBLISHED]->(p))
            RETURN COUNT(p) as count
            """).single()['count']
            print(f"- Procurements sin Buyer: {orphan_procs}")

            orphan_items = session.run("""
            MATCH (i:Item)
            WHERE NOT (()-[:INCLUDES]->(i))
            RETURN COUNT(i) as count
            """).single()['count']
            print(f"- Items sin Procurement: {orphan_items}")

            orphan_awards = session.run("""
            MATCH (a:Award)
            WHERE NOT (()-[:HAS_AWARD]->(a))
            RETURN COUNT(a) as count
            """).single()['count']
            print(f"- Awards sin Procurement: {orphan_awards}")

            orphan_contracts = session.run("""
            MATCH (c:Contract)
            WHERE NOT (()-[:HAS_CONTRACT]->(c))
            RETURN COUNT(c) as count
            """).single()['count']
            print(f"- Contracts sin Award: {orphan_contracts}")

            print("\n3. Verificando campos obligatorios...")
            missing_fields = session.run("""
            MATCH (p:Procurement)
            WHERE p.title IS NULL OR p.publishedDate IS NULL
            OR p.procurementMethod IS NULL OR p.mainCategory IS NULL
            RETURN COUNT(p) as count
            """).single()['count']
            if missing_fields > 0:
                print(f"¡Advertencia! {missing_fields} Procurements tienen campos obligatorios faltantes")

            print("\n4. Verificando coherencia de fechas...")
            invalid_dates = session.run("""
            MATCH (p:Procurement)
            WHERE p.publishedDate > datetime()
            RETURN COUNT(p) as count
            """).single()['count']
            if invalid_dates > 0:
                print(f"¡Advertencia! {invalid_dates} Procurements tienen fechas futuras")

            print("\nVerificación de integridad completada.")


def main():
    print(f"Directorio actual: {os.getcwd()}")

    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = ":kJ7k,G+87.W"

    print("Cargando datos desde contratos_completos.json...")
    try:
        with open('contratos_completos.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            print(f"Cantidad de registros en 'records': {len(data['records'])}")
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'contratos_completos.json' en el directorio actual.")
        return
    except json.JSONDecodeError:
        print("Error: El archivo 'contratos_completos.json' no contiene un JSON válido.")
        return
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return

    loader = Neo4jLoader(uri, username, password)
    try:
        loader.load_data(data)
    except Exception as e:
        print(f"Error durante la carga de datos: {e}")
    finally:
        loader.close()

if __name__ == "__main__":
    main()