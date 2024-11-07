import requests
import json

# Configura la URL de la API y los parámetros de la consulta
url = 'https://contratacionesabiertas.osce.gob.pe/api/v1/records'
params = {
    'page': 1,
    'order': 'desc',
    'sourceId': 'seace_v3',
    'startDate': '2024-11-05',
    'endDate': '2024-11-06'
}

# Realiza la solicitud a la API
response = requests.get(url, params=params)
data = response.json()

# Inicializa la lista para almacenar datos limpios
cleaned_data = []
unique_ids = set()

# Procesa cada registro y realiza la limpieza en el mismo bucle
for record in data['records']:
    compiled_release = record['compiledRelease']
    contract_id = compiled_release['id']

    # Verifica y elimina duplicados
    if contract_id not in unique_ids:
        unique_ids.add(contract_id)

        # Normaliza y selecciona los campos necesarios
        cleaned_record = {
            "ocid": compiled_release.get("ocid"),
            "contract_id": contract_id,
            "date": compiled_release.get("date"),
            "buyer": {
                "id": compiled_release['buyer'].get("id"),
                "name": compiled_release['buyer'].get("name", "").strip().upper()
            },
            "tender": {
                "id": compiled_release['tender'].get("id"),
                "title": compiled_release['tender'].get("title"),
                "description": compiled_release['tender'].get("description"),
                "procurementMethod": compiled_release['tender'].get("procurementMethod"),
                "procurementMethodDetails": compiled_release['tender'].get("procurementMethodDetails"),
                "mainProcurementCategory": compiled_release['tender'].get("mainProcurementCategory"),
                "value": compiled_release['tender']['value'].get("amount"),
                "currency": compiled_release['tender']['value'].get("currency"),
                "datePublished": compiled_release['tender'].get("datePublished"),
                "items": []
            },
            "parties": [],
            "documents": []
        }

        # Procesa los elementos (items) de la licitación
        for item in compiled_release['tender'].get("items", []):
            cleaned_record["tender"]["items"].append({
                "id": item.get("id"),
                "description": item.get("description"),
                "quantity": item.get("quantity"),
                "unit": item.get("unit", {}).get("name"),
                "totalValue": item.get("totalValue", {}).get("amount")
            })

        # Procesa los participantes
        for party in compiled_release.get("parties", []):
            cleaned_record["parties"].append({
                "id": party.get("id"),
                "name": party.get("name"),
                "roles": party.get("roles"),
                "address": party.get("address", {}).get("streetAddress"),
                "region": party.get("address", {}).get("region"),
                "countryName": party.get("address", {}).get("countryName")
            })

        # Procesa los documentos
        for document in compiled_release['tender'].get("documents", []):
            cleaned_record["documents"].append({
                "id": document.get("id"),
                "title": document.get("title"),
                "url": document.get("url"),
                "datePublished": document.get("datePublished"),
                "documentType": document.get("documentType"),
                "language": document.get("language")
            })

        # Agrega el registro limpio a la lista
        cleaned_data.append(cleaned_record)

# Guarda los datos limpios en un archivo
with open('contratos_limpios.json', 'w') as file:
    json.dump({'records': cleaned_data}, file, indent=4)

print("Extracción y limpieza completada. Datos guardados en 'contratos_limpios.json'")
