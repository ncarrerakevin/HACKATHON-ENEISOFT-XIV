import React from 'react';

const MetricCard = ({ icon: Icon, title, value, bgColor, textColor }) => (
    <div className="flex items-center space-x-3">
        <div className={`p-2 ${bgColor} rounded-lg`}>
            <Icon className={`h-5 w-5 ${textColor}`} />
        </div>
        <div>
            <p className="text-sm text-gray-500">{title}</p>
            <p className="text-lg font-semibold text-gray-800">{value}</p>
        </div>
    </div>
);

export default MetricCard;