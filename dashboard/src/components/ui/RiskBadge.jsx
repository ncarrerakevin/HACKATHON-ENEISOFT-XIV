import React from 'react';
import { AlertTriangle, Clock, FileCheck } from 'lucide-react';

const RiskBadge = ({ level }) => {
    const variants = {
        high: "bg-red-100 text-red-700 border-red-200",
        medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
        low: "bg-green-100 text-green-700 border-green-200"
    };

    const icons = {
        high: <AlertTriangle className="w-4 h-4 mr-1" />,
        medium: <Clock className="w-4 h-4 mr-1" />,
        low: <FileCheck className="w-4 h-4 mr-1" />
    };

    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variants[level]}`}>
            {icons[level]}
            {level === 'high' ? 'Alto Riesgo' : level === 'medium' ? 'Riesgo Medio' : 'Riesgo Bajo'}
        </span>
    );
};

export default RiskBadge;