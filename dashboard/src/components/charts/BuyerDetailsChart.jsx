import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { AlertTriangle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import neo4j from 'neo4j-driver';

const BuyerDetailsChart = ({ data }) => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [buyerDetails, setBuyerDetails] = useState(null);

    const handleBarClick = async (data) => {
        if (!data.payload) return;

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
                WHERE b.name = $buyerName
                RETURN s.name as proveedor,
                       count(a) as adjudicaciones,
                       sum(toFloat(a.value)) as montoTotal
                ORDER BY adjudicaciones DESC
                LIMIT 10
            `, {
                buyerName: data.payload.name
            });

            const details = {
                name: data.payload.name,
                total: data.payload.total,
                suppliers: result.records.map(record => ({
                    proveedor: record.get('proveedor'),
                    adjudicaciones: record.get('adjudicaciones').toNumber(),
                    montoTotal: record.get('montoTotal')
                }))
            };

            setBuyerDetails(details);
            setIsModalOpen(true);

        } catch (error) {
            console.error("Error:", error);
        } finally {
            if (session) await session.close();
            if (driver) await driver.close();
        }
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle>Top 5 Entidades por Procesos</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data}>
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Bar
                                dataKey="total"
                                fill="#60a5fa"
                                cursor="pointer"
                                onClick={handleBarClick}
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>

            <Dialog open={isModalOpen} onOpenChange={() => setIsModalOpen(false)}>
                <DialogContent className="fixed top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] max-h-[90vh] w-[90vw] max-w-3xl overflow-hidden bg-white rounded-lg shadow-lg">
                    <DialogHeader>
                        <DialogTitle className="text-xl font-bold">
                            Detalles de Entidad
                        </DialogTitle>
                    </DialogHeader>
                    <div className="overflow-y-auto max-h-[calc(90vh-8rem)]">
                        {buyerDetails && (
                            <div className="space-y-6 p-6">
                                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                                    <h3 className="font-semibold text-blue-800">
                                        {buyerDetails.name}
                                    </h3>
                                    <p className="text-sm text-blue-700">
                                        Total de procesos: {buyerDetails.total}
                                    </p>
                                </div>

                                <div className="bg-white rounded-lg border">
                                    <div className="p-4 border-b">
                                        <h3 className="font-semibold">Principales Proveedores</h3>
                                    </div>
                                    <div className="p-4">
                                        {buyerDetails.suppliers.map((supplier, index) => (
                                            <div key={index} className="mb-4 p-4 bg-gray-50 rounded-lg">
                                                <div className="grid grid-cols-2 gap-4">
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-600">Proveedor</p>
                                                        <p className="text-sm">{supplier.proveedor}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-600">Adjudicaciones</p>
                                                        <p className="text-sm">{supplier.adjudicaciones}</p>
                                                    </div>
                                                    <div className="col-span-2">
                                                        <p className="text-sm font-medium text-gray-600">Monto Total</p>
                                                        <p className="text-sm">S/ {supplier.montoTotal?.toLocaleString()}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </DialogContent>
            </Dialog>
        </Card>
    );
};

export default BuyerDetailsChart;