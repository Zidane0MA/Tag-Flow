
import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon }) => {
  return (
    <div className="bg-slate-800 rounded-lg p-6 flex items-center shadow-lg">
      <div className="p-3 bg-cyan-500/20 rounded-full text-cyan-400">
        {icon}
      </div>
      <div className="ml-4">
        <p className="text-sm font-medium text-slate-400">{title}</p>
        <p className="text-2xl font-bold text-white">{value}</p>
      </div>
    </div>
  );
};

export default StatCard;
