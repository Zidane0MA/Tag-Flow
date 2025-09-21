import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { NAV_LINKS, ICONS } from '../constants';
import { apiService } from '../services/apiService';

interface SidebarProps {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  localStats?: {
    loaded?: number;
    [key: string]: any;
  }; // Optional local stats from cursor hooks
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, setIsOpen, localStats }) => {
  const location = useLocation();
  const [globalStats, setGlobalStats] = useState({
    totalPosts: 0,
    totalMedia: 0,
    processed: 0,
    inTrash: 0,
  });

  // Cargar estadísticas globales
  useEffect(() => {
    const loadGlobalStats = async () => {
      try {
        const stats = await apiService.getGlobalStats();
        setGlobalStats(stats);
      } catch (error) {
        console.error('Error loading global stats:', error);
      }
    };

    loadGlobalStats();
    // Actualizar cada 30 segundos
    const interval = setInterval(loadGlobalStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleNavClick = () => {
    // Close sidebar on navigation in mobile view
    if (window.innerWidth < 1024) {
      setIsOpen(false);
    }
  };

  // Determinar si mostrar estadísticas locales
  const showLocalStats = localStats && Object.keys(localStats).length > 0;
  const localStatsData = localStats || { loaded: 0 };

  const sidebarClasses = `
    lg:relative lg:h-full fixed top-0 left-0 h-full 
    bg-[#212121]/80 backdrop-blur-sm lg:bg-[#212121] lg:backdrop-blur-none 
    text-gray-200 transition-all duration-300 ease-in-out z-40 transform
    ${isOpen ? 'translate-x-0' : '-translate-x-full'} 
    w-64 lg:translate-x-0 
    ${isOpen ? 'lg:w-64' : 'lg:w-20'}
  `.trim().replace(/\s+/g, ' ');

  return (
    <div
      className={sidebarClasses}
      role="navigation"
    >
      <div className={`flex items-center h-16 lg:h-20 border-b border-white/10 lg:border-gray-700 transition-all duration-300 ${isOpen ? 'justify-between px-4 lg:px-6' : 'justify-center px-2 lg:px-3'}`}>
        {isOpen && (
          <span className="font-bold text-xl lg:text-2xl text-white whitespace-nowrap">
            Tag-Flow
          </span>
        )}
        
        {/* Desktop Toggle Button */}
        <button 
          onClick={() => setIsOpen(!isOpen)} 
          className="hidden lg:block text-gray-400 hover:text-white p-2 rounded-full hover:bg-gray-700"
          aria-label={isOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
           <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7" />
          </svg>
        </button>

        {/* Mobile Close Button */}
        <button 
          onClick={() => setIsOpen(false)} 
          className="lg:hidden text-gray-400 hover:text-white p-2 rounded-full hover:bg-gray-700"
          aria-label="Close sidebar"
        >
          {ICONS.close}
        </button>
      </div>
      <nav className={`mt-2 transition-all duration-300 ${isOpen ? 'mx-2' : 'mx-1 lg:mx-2'}`}>
        {NAV_LINKS.map((link) => (
          <NavLink
            key={link.name}
            to={link.href}
            title={!isOpen ? link.name : ''}
            onClick={handleNavClick}
            className={({ isActive }) =>
              `flex items-center py-3 my-1 rounded-lg transition-colors duration-200 ${isOpen ? 'px-4' : 'px-2 lg:px-3 justify-center'} ${
                isActive
                  ? 'bg-gray-600 font-semibold text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`
            }
          >
            {link.icon}
            {isOpen && <span className="ml-6 font-medium whitespace-nowrap">{link.name}</span>}
          </NavLink>
        ))}
      </nav>
      {isOpen && (
        <div className="px-6 mt-8 overflow-hidden">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">Estadísticas</h3>
          <div className="mt-4 space-y-3 text-sm">
            {/* Estadísticas locales (solo en gallery) */}
            {showLocalStats && (
              <div className="mb-4 pb-3 border-b border-gray-700">
                <div className="flex justify-between text-gray-300">
                  <span>Cargados</span>
                  <span className="font-medium text-green-400">{localStatsData.loaded}</span>
                </div>
              </div>
            )}
            
            {/* Estadísticas globales */}
            <div className="flex justify-between text-gray-300">
              <span>Total Posts</span>
              <span className="font-medium text-white">{globalStats.totalPosts}</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>Total Media</span>
              <span className="font-medium text-white">{globalStats.totalMedia}</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>Procesados</span>
              <span className="font-medium text-white">{globalStats.processed}</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>En Papelera</span>
              <span className="font-medium text-white">{globalStats.inTrash}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;