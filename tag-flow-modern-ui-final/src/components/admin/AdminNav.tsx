import React from 'react';
import { NavLink } from 'react-router-dom';
import { ICONS } from '../../constants';
import { useAdminData } from '../../hooks/useAdminData';

const AdminNav: React.FC = () => {
    const { stats } = useAdminData();

    const navLinks = [
        { name: 'Dashboard', href: '/admin', exact: true, icon: ICONS.gallery, badge: null },
        { name: 'Operaciones', href: '/admin/operations', icon: ICONS.terminal, badge: stats.activeOperations > 0 ? stats.activeOperations : null},
        { name: 'Configuración', href: '/admin/config', icon: ICONS.wrench, badge: null },
        { name: 'Personajes', href: '/admin/characters', icon: ICONS.users, badge: stats.totalCharacters },
    ];

    const getNavLinkClass = (isActive: boolean) =>
      `flex items-center gap-3 px-3 py-2 font-medium rounded-md transition-colors text-sm ${
        isActive
          ? 'bg-red-600 text-white'
          : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
      }`;
      
    return (
        <nav className="flex flex-wrap items-center gap-2 p-2 bg-[#212121] rounded-lg">
            {navLinks.map(link => (
                <NavLink 
                    key={link.name} 
                    to={link.href} 
                    end={link.exact}
                    className={({ isActive }) => getNavLinkClass(isActive)}
                    title={link.name}
                >
                    {React.cloneElement(link.icon, { className: 'h-5 w-5' })}
                    <span className="hidden sm:inline">{link.name}</span>
                    {link.badge !== null && (
                         <span className="px-2 py-0.5 text-xs font-bold bg-red-500 rounded-full">{link.badge}</span>
                    )}
                </NavLink>
            ))}
        </nav>
    );
};

export default AdminNav;