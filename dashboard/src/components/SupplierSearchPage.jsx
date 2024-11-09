// SupplierSearchPage.jsx
import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Skeleton } from './ui/skeleton'; // Añade esta importación
import { motion, AnimatePresence } from 'framer-motion';
import MetricCard from './ui/MetricCard';
import RiskBadge from './ui/RiskBadge';
import { formatCurrency, getRiskLevel } from '../utils/formatters';
import {
    Building2,
    Search,
    DollarSign,
    Users,
    Clock
} from 'lucide-react';
import neo4j from 'neo4j-driver';

// Componente de Skeleton para carga
const SupplierCardSkeleton = () => (
    <div className="space-y-3">
        <Skeleton className="h-[125px] w-full rounded-lg" />
        <div className="space-y-2">
            <Skeleton className="h-4 w-[250px]" />
            <Skeleton className="h-4 w-[200px]" />
        </div>
    </div>
);

const SupplierSearchPage = () => {
    const [searchTerm, setSearchTerm] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [selectedSupplier, setSelectedSupplier] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleSearch = async () => {
        setIsLoading(true);
        let driver = null;
        let session = null;

        try {
            driver = neo4j.driver(
                'bolt://localhost:7687',
                neo4j.auth.basic('neo4j', ':kJ7k,G+87.W')
            );

            session = driver.session();

            const result = await session.run(`
                MATCH (s:Supplier)
                WHERE toLower(s.name) CONTAINS toLower($searchTerm)
                OPTIONAL MATCH (s)<-[:AWARDED_TO]-(a)
                OPTIONAL MATCH (a)-[:HAS_AWARD]->(p:Procurement)-[:PUBLISHED]->(b:Buyer)
                WITH s, a, b, p
                RETURN 
                    s.name AS NombreProveedor, 
                    s.ruc AS RUC,
                    count(DISTINCT a) AS TotalAdjudicaciones,
                    count(DISTINCT b) AS CompradoresUnicos,
                    CASE 
                        WHEN count(a) > 0 
                        THEN round(100.0 * count(CASE WHEN p.quickAward = true THEN 1 END) / count(a))
                        ELSE 0 
                    END AS PorcentajeAdjudicacionesRapidas,
                    CASE 
                        WHEN count(a) > 0 
                        THEN round(avg(toFloat(a.value)))
                        ELSE 0 
                    END AS ValorPromedioContrato
            `, { searchTerm: searchTerm });

            console.log('Resultado de la consulta:', result.records);

            const formattedResults = result.records.map(record => ({
                name: record.get('NombreProveedor'),
                ruc: record.get('RUC') || 'No disponible',
                totalAwards: record.get('TotalAdjudicaciones').low,
                uniqueBuyers: record.get('CompradoresUnicos').low,
                quickAwardRatio: parseFloat(record.get('PorcentajeAdjudicacionesRapidas')),
                avgContractValue: parseFloat(record.get('ValorPromedioContrato'))
            }));

            console.log('Resultados formateados:', formattedResults);
            setSearchResults(formattedResults);

        } catch (error) {
            console.error('Error en la búsqueda:', error);
        } finally {
            if (session) await session.close();
            if (driver) await driver.close();
            setIsLoading(false);
        }
    };

    const handleSupplierSelect = (supplier) => {
        setSelectedSupplier(supplier);
    };

    return (
        <div className="w-full max-w-7xl mx-auto p-4 space-y-4">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">Buscador de Proveedores</h1>

            <div className="flex items-center justify-center mb-6 space-x-4">
                <input
                    type="text"
                    className="w-full max-w-md px-4 py-3 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Buscar proveedor..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
                <button
                    className={`px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700 transition duration-300 ${isLoading ? 'animate-pulse' : ''}`}
                    onClick={handleSearch}
                    disabled={isLoading || !searchTerm.trim()}
                >
                    {isLoading ? 'Buscando...' : 'Buscar'}
                </button>
            </div>

            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {[1, 2, 3, 4].map(i => (
                        <SupplierCardSkeleton key={i} />
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {searchResults.map((supplier, index) => (
                        <motion.div
                            key={supplier.name}
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: index * 0.1 }}
                        >
                            <Card
                                className={`cursor-pointer transform transition-all duration-300
                                    hover:scale-[1.02] hover:shadow-xl
                                    ${selectedSupplier?.name === supplier.name ? 'ring-2 ring-blue-500 shadow-lg' : ''}
                                    ${getRiskLevel(supplier) === 'high' ? 'border-l-red-500' :
                                    getRiskLevel(supplier) === 'medium' ? 'border-l-yellow-500' :
                                        'border-l-green-500'}`}
                                onClick={() => handleSupplierSelect(supplier)}
                            >
                                <CardHeader className="border-b border-gray-100 pb-4">
                                    <RiskBadge level={getRiskLevel(supplier)} />
                                </CardHeader>
                                <CardContent className="pt-6">
                                    <MetricCard
                                        icon={Users}
                                        title="Nombre"
                                        value={supplier.name}
                                        bgColor="bg-blue-50"
                                        textColor="text-blue-700"
                                    />
                                    <MetricCard
                                        icon={DollarSign}
                                        title="Valor Promedio Contrato"
                                        value={formatCurrency(supplier.avgContractValue)}
                                        bgColor="bg-blue-50"
                                        textColor="text-blue-700"
                                    />
                                    <MetricCard
                                        icon={Users}
                                        title="Cantidad Total de contratos"
                                        value={supplier.totalAwards}
                                        bgColor="bg-yellow-50"
                                        textColor="text-yellow-700"
                                    />




                                </CardContent>
                            </Card>
                        </motion.div>
                    ))}
                </div>
            )}


        </div>
    );
};

export default SupplierSearchPage;
