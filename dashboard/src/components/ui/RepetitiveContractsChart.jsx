import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './dialog';
import { ScrollArea } from './scroll-area';
import { AlertTriangle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import neo4j from 'neo4j-driver';

// Agrega esta función al principio de tu componente, después de tus imports o estado inicial
const formatAmountWithCurrency = (amount, currency) => {
    const currencySymbols = {
        'USD': '$',
        'PEN': 'S/.'  // Asegúrate de usar el punto si es el formato que prefieres
    };
    const symbol = currencySymbols[currency] || currency;  // Uso de un valor predeterminado si la moneda no está mapeada
    return `${symbol} ${amount.toLocaleString('es-PE', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;
};

const RepetitiveContractsChart = ({ data }) => {
    console.log("Datos recibidos en RepetitiveContractsChart:", data);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [contractDetails, setContractDetails] = useState(null);

    // Log inicial
    console.log("Datos iniciales:", data);

    const handleBarClick = async (data) => {
        console.log("Click data:", data);
        const entry = data.payload;

        if (!entry) {
            console.error("No se encontraron datos del contrato");
            return;
        }

        console.log("Procesando entrada:", entry);

        let driver = null;
        let session = null;

        try {
            driver = neo4j.driver(
                'bolt://localhost:7687',
                neo4j.auth.basic('neo4j', ':kJ7k,G+87.W')
            );

            session = driver.session();

            const result = await session.run(`
            MATCH (b:Buyer)-[:PUBLISHED]->(p:Procurement)-[:HAS_AWARD]->(a:Award)-[:AWARDED_TO]->(s:Supplier)
            WHERE s.name = $supplierName
            RETURN 
                b.name as entidad,
                p.ocid as ocid,
                COALESCE(p.description, 'Sin descripción') as description,
                toFloat(a.value) as amount,
                a.currency as currency,
                p.publishedDate as date
            ORDER BY date DESC
        `, {
                supplierName: entry.proveedor
            });

            console.log("Resultado de Neo4j:", result.records);

            const contracts = result.records.map(record => {
                const amount = parseFloat(record.get('amount')); // Convertimos el monto a número si no lo es
                const currency = record.get('currency'); // Capturamos la moneda
                const date = record.get('date');

                return {
                    ocid: record.get('ocid'),
                    entidad: record.get('entidad'),
                    description: record.get('description'),
                    amount: amount || 0, // Manejamos valores nulos
                    currency: currency,
                    date: date ? new Date(date).toLocaleDateString() : 'Fecha no disponible'
                };
            });

            // Asumir una moneda común o usar la primera moneda disponible
            const commonCurrency = contracts[0]?.currency || 'PEN';

// Calcular el monto total de forma correcta, asegurando que se suman números
            const totalAmount = contracts.reduce((sum, contract) => sum + contract.amount, 0);

// Formatear el monto total como moneda
            const formattedTotalAmount = formatAmountWithCurrency(totalAmount, commonCurrency);

// Establecer los detalles del contrato incluyendo el monto total correctamente formateado
            setContractDetails({
                ...entry,
                contracts,
                totalAmount: formattedTotalAmount,
                contractCount: contracts.length
            });
            setIsModalOpen(true);

        } catch (error) {
            console.error("Error al obtener detalles del contrato:", error);
            console.error("Stack trace:", error.stack);
        } finally {
            if (session) await session.close();
            if (driver) await driver.close();
        }
    };

    return (
        <>
            <Card className="col-span-1">
                <CardHeader>
                    <CardTitle>Proveedores Recurrentes con Entidades Específicas</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={data} onClick={(data) => console.log("Click en gráfico:", data)}>
                                <XAxis dataKey="proveedor" />
                                <YAxis />
                                <Tooltip />
                                <Bar
                                    dataKey="adjudicaciones"
                                    fill="#f87171"
                                    onClick={(data) => {
                                        console.log("Click en barra:", data);
                                        handleBarClick(data);
                                    }}
                                    cursor="pointer"
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>

            <Dialog open={isModalOpen} onOpenChange={() => setIsModalOpen(false)}>
                <DialogContent
                    className="fixed top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] max-h-[90vh] w-[90vw] max-w-3xl overflow-hidden bg-white rounded-lg shadow-lg">
                    <DialogHeader>
                        <DialogTitle className="text-xl font-bold">
                            Detalles de Contratos Recurrentes
                        </DialogTitle>
                    </DialogHeader>
                    <div className="overflow-y-auto max-h-[calc(90vh-8rem)]">
                        {contractDetails && (
                            <div className="space-y-6 p-6">
                                <ScrollArea className="h-full max-h-[60vh] pr-4">
                                    {contractDetails && (
                                        <div className="space-y-6">
                                            {/* Información del Proveedor */}
                                            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <AlertTriangle className="text-yellow-500 h-5 w-5"/>
                                                    <h3 className="font-semibold text-yellow-800">
                                                        Proveedor Frecuente
                                                    </h3>
                                                </div>
                                                <p className="text-sm text-yellow-700">
                                                    Este proveedor tiene {contractDetails.adjudicaciones} adjudicaciones
                                                    con un monto total de {contractDetails.totalAmount}
                                                </p>
                                            </div>

                                            {/* Detalles Generales */}
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="p-4 bg-white rounded-lg border">
                                                    <h4 className="font-medium text-gray-700">Proveedor</h4>
                                                    <p className="mt-1">{contractDetails.proveedor}</p>
                                                </div>
                                                <div className="p-4 bg-white rounded-lg border">
                                                    <h4 className="font-medium text-gray-700">Entidad</h4>
                                                    <p className="mt-1">{contractDetails.entidad}</p>
                                                </div>
                                            </div>

                                            {/* Lista de Contratos */}
                                            <div className="bg-white rounded-lg border">
                                                <div className="p-4 border-b">
                                                    <h3 className="font-semibold">Contratos Relacionados</h3>
                                                </div>
                                                <div className="p-4">
                                                    {contractDetails.contracts?.map((contract, index) => (
                                                        <div key={index} className="mb-4 p-4 bg-gray-50 rounded-lg">
                                                            <div className="grid grid-cols-2 gap-4">
                                                                <div>
                                                                    <p className="text-sm font-medium text-gray-600">OCID</p>
                                                                    <p className="text-sm">{contract.ocid}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-sm font-medium text-gray-600">Monto</p>
                                                                    <p className="text-sm">{contract.amount}</p>
                                                                </div>
                                                                <div className="col-span-2">
                                                                    <p className="text-sm font-medium text-gray-600">Descripción</p>
                                                                    <p className="text-sm">{contract.description}</p>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Indicadores de Riesgo */}
                                            <div className="bg-white rounded-lg border">
                                                <div className="p-4 border-b">
                                                    <h3 className="font-semibold">Indicadores de Riesgo</h3>
                                                </div>
                                                <div className="p-4 space-y-4">
                                                    <div className="flex items-center gap-2">
                                                        <div className={`w-3 h-3 rounded-full ${
                                                            contractDetails.adjudicaciones > 5 ? 'bg-red-500' : 'bg-yellow-500'
                                                        }`}/>
                                                        <span className="text-sm">
                                                {contractDetails.adjudicaciones} adjudicaciones con la misma entidad
                                            </span>
                                                    </div>
                                                    {contractDetails.timeSpan && (
                                                        <div className="flex items-center gap-2">
                                                            <div className="w-3 h-3 rounded-full bg-blue-500"/>
                                                            <span className="text-sm">
                                                    Periodo de adjudicaciones: {contractDetails.timeSpan}
                                                </span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </ScrollArea>
                            </div>
                        )}
                    </div>
                </DialogContent>
            </Dialog>
        </>
    );
};

export default RepetitiveContractsChart;