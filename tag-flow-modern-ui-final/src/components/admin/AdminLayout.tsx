import React from 'react';
import { useLocation } from 'react-router-dom';
import { useAdminData } from '../../hooks/useAdminData';
import AdminNav from './AdminNav';
import { ICONS } from '../../constants';

const pageTitles: { [key: string]: string } = {
  '/admin': 'Dashboard',
  '/admin/operations': 'Operaciones',
  '/admin/config': 'Configuración',
  '/admin/characters': 'Personajes',
};

const AdminLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const { stats } = useAdminData();
  const pathParts = location.pathname.split('/').filter(p => p);
  const currentPageTitle = pageTitles[location.pathname] || 'Admin';

  const healthStatusConfig = {
    good: { style: 'bg-green-500', text: 'Operativo' },
    warning: { style: 'bg-yellow-500', text: 'Advertencia' },
    error: { style: 'bg-red-500', text: 'Error' },
  };

  const currentHealth = healthStatusConfig[stats.systemHealth.status];

  return (
    <div className="text-white flex flex-col gap-6">
        <header className="flex flex-wrap justify-between items-center gap-y-2 gap-x-4">
            <div>
                <div className="flex items-center text-sm text-gray-400 mb-1">
                    <span className="font-semibold">Admin</span>
                    {pathParts.slice(1).map(part => (
                        <React.Fragment key={part}>
                          {React.cloneElement(ICONS.chevronRight, { className: 'h-4 w-4 text-gray-500 mx-1' })}
                          <span className="capitalize">{part}</span>
                        </React.Fragment>
                    ))}
                </div>
                <h1 className="text-3xl font-bold">{currentPageTitle}</h1>
            </div>
            <div 
                className="flex items-center gap-2 p-2 rounded-lg bg-[#212121]/50 border border-gray-700/50"
                title={stats.systemHealth.message}
            >
                <span className="text-sm font-medium text-gray-400">Estado:</span>
                <span className={`h-2 w-2 rounded-full ${currentHealth.style}`}></span>
                <span className="text-sm font-semibold text-white">{currentHealth.text}</span>
            </div>
        </header>
        
        <AdminNav />

        <main className="bg-[#181818] p-4 sm:p-6 rounded-lg shadow-xl min-h-[60vh]">
            {children}
        </main>
    </div>
  );
};

export default AdminLayout;