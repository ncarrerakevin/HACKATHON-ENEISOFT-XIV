import React, { useState, useEffect } from 'react';
import neo4j from 'neo4j-driver';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import RepetitiveContractsChart from './ui/RepetitiveContractsChart';
import BuyerDetailsChart from './charts/BuyerDetailsChart';
import { Badge } from './ui/badge';
import { AlertTriangle, DollarSign, Users, TrendingUp, Building2, FileCheck } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useNavigate } from 'react-router-dom'; // Importa useNavigate

const Dashboard = () => {
    const navigate = useNavigate(); // Inicializa useNavigate para navegación

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [metrics, setMetrics] = useState({
        generalStats: {
            buyers: 0,
            suppliers: 0,
            procurements: 0,
            awards: 0
        },
        topBuyers: [],
        topSuppliers: [],
        frequentSuppliers: 0,
        repetitiveContracts: []
    });

    useEffect(() => {
        const fetchData = async () => {
            let driver = null;
            let session = null;

            try {
                driver = neo4j.driver(
                    'bolt://localhost:7687',
                    neo4j.auth.basic('neo4j', ':kJ7k,G+87.W')
                );

                await driver.verifyConnectivity();
                session = driver.session();

                // Estadísticas generales
                const statsResult = await session.run(`
                    CALL {
                        MATCH (b:Buyer) RETURN count(b) as buyers
                    }
                    CALL {
                        MATCH (s:Supplier) RETURN count(s) as suppliers
                    }
                    CALL {
                        MATCH (p:Procurement) RETURN count(p) as procurements
                    }
                    CALL {
                        MATCH (a:Award) RETURN count(a) as awards
                    }
                    RETURN buyers, suppliers, procurements, awards
                `);

                // Top 5 compradores
                const buyersResult = await session.run(`
                    MATCH (b:Buyer)-[:PUBLISHED]->(p:Procurement)
                    WITH b.name as name, count(p) as total
                    ORDER BY total DESC
                    LIMIT 5
                    RETURN name, total
                `);

                // Top 5 proveedores
                const suppliersResult = await session.run(`
                    MATCH (s:Supplier)<-[:AWARDED_TO]-(a:Award)
                    WITH s.name as name, count(a) as awards
                    ORDER BY awards DESC
                    LIMIT 5
                    RETURN name, awards
                `);

                // Proveedores frecuentes (más de 5 adjudicaciones)
                const frequentSuppliersResult = await session.run(`
                    MATCH (s:Supplier)<-[:AWARDED_TO]-(a:Award)
                    WITH s, count(a) as awards
                    WHERE awards > 5
                    RETURN count(s) as count
                `);

                // Contratos repetitivos (más de 3 adjudicaciones por el mismo proveedor)
                const repetitiveContractsResult = await session.run(`
                    MATCH (b:Buyer)-[:PUBLISHED]->(p:Procurement)-[:HAS_AWARD]->(a:Award)-[:AWARDED_TO]->(s:Supplier)
                    WITH b.name AS entidad, s.name AS proveedor, count(a) AS adjudicaciones
                    WHERE adjudicaciones > 3
                    RETURN entidad, proveedor, adjudicaciones
                    ORDER BY adjudicaciones DESC
                    LIMIT 10
                `);

                setMetrics({
                    generalStats: {
                        buyers: statsResult.records[0].get('buyers').toNumber(),
                        suppliers: statsResult.records[0].get('suppliers').toNumber(),
                        procurements: statsResult.records[0].get('procurements').toNumber(),
                        awards: statsResult.records[0].get('awards').toNumber()
                    },
                    topBuyers: buyersResult.records.map(record => ({
                        name: record.get('name'),
                        total: record.get('total').toNumber()
                    })),
                    topSuppliers: suppliersResult.records.map(record => ({
                        name: record.get('name'),
                        awards: record.get('awards').toNumber()
                    })),
                    frequentSuppliers: frequentSuppliersResult.records[0].get('count').toNumber(),
                    repetitiveContracts: repetitiveContractsResult.records.map(record => ({
                        entidad: record.get('entidad'),
                        proveedor: record.get('proveedor'),
                        adjudicaciones: record.get('adjudicaciones').toNumber()
                    }))
                });

                setLoading(false);

            } catch (e) {
                console.error('Error:', e);
                setError(e.message);
                setLoading(false);
            } finally {
                if (session) await session.close();
                if (driver) await driver.close();
            }
        };

        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-lg font-semibold text-gray-600">
                    Cargando datos...
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-screen">
                <div className="text-lg font-semibold text-red-600 mb-4">
                    Error: {error}
                </div>
                <button
                    onClick={() => window.location.reload()}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                    Reintentar
                </button>
            </div>
        );
    }

    return (
        <div className="w-full max-w-7xl mx-auto p-4 space-y-4">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Dashboard de Contrataciones</h1>
                <button
                    onClick={() => navigate('/supplier-search')}
                    className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                >
                    Buscar
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                {/* Tarjetas Generales */}
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">
                            <Building2 className="inline-block mr-2 h-4 w-4 text-blue-500" />
                            Compradores
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{metrics.generalStats.buyers}</div>
                        <div className="text-sm text-gray-500">Entidades registradas</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">
                            <Users className="inline-block mr-2 h-4 w-4 text-green-500" />
                            Proveedores
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{metrics.generalStats.suppliers}</div>
                        <div className="text-sm text-gray-500">Empresas proveedoras</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">
                            <FileCheck className="inline-block mr-2 h-4 w-4 text-purple-500" />
                            Procesos
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{metrics.generalStats.procurements}</div>
                        <div className="text-sm text-gray-500">Procesos de contratación</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">
                            <AlertTriangle className="inline-block mr-2 h-4 w-4 text-yellow-500" />
                            Proveedores Frecuentes
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{metrics.frequentSuppliers}</div>
                        <Badge variant="warning" className="mt-2">Más de 5 adjudicaciones</Badge>
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

                {/* Nuevo Componente para Detalles del Comprador */}
                <BuyerDetailsChart data={metrics.topBuyers} />

                {/* Nuevo Componente para Contratos Repetitivos */}
                <RepetitiveContractsChart
                    data={metrics.repetitiveContracts}
                    onBarClick={(data) => console.log("Click desde dashboard:", data)}
                />
            </div>
        </div>
    );
};

export default Dashboard;
