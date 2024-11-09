// src/utils/formatters.js
export const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-PE', {
        style: 'currency',
        currency: 'PEN',
        minimumFractionDigits: 2
    }).format(amount);
};

export const getRiskLevel = (supplier) => {
    if (supplier.quickAwardRatio > 50 || supplier.avgContractValue > 1000000) {
        return 'high';
    }
    if (supplier.quickAwardRatio > 30 || supplier.avgContractValue > 500000) {
        return 'medium';
    }
    return 'low';
};