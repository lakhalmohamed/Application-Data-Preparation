import React from 'react';

const KPICard = ({ title, value, icon: Icon }) => {
  return (
    <div className="bg-card rounded-lg border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-500 text-sm font-medium uppercase tracking-wide">
            {title}
          </p>
          <p className="text-2xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        {Icon && (
          <div className="p-3 bg-blue-50 rounded-lg">
            <Icon className="w-6 h-6 text-primary" />
          </div>
        )}
      </div>
    </div>
  );
};

export default KPICard;
