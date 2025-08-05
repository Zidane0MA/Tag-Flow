
import React from 'react';
import { NavLink } from 'react-router-dom';
import { NAV_LINKS, ICONS } from '../constants';
import { useData } from '../hooks/useMockData';

interface SidebarProps {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, setIsOpen }) => {
  const { getStats } = useData();
  const stats = getStats();

  const handleNavClick = () => {
    // Close sidebar on navigation in mobile view
    if (window.innerWidth < 1024) {
      setIsOpen(false);
    }
  };

  return (
    <div
      className={`fixed top-0 left-0 h-full bg-[#212121]/80 backdrop-blur-sm lg:bg-[#212121] lg:backdrop-blur-none text-gray-200 transition-all duration-300 ease-in-out z-40 transform 
                 w-64 lg:translate-x-0 
                 ${isOpen ? 'translate-x-0' : '-translate-x-full'}
                 lg:${isOpen ? 'w-64' : 'w-20'}`}
      role="navigation"
    >
      <div className={`flex items-center h-16 lg:h-20 border-b border-white/10 lg:border-gray-700 transition-all duration-300 ${isOpen ? 'justify-between px-4 lg:px-6' : 'justify-center px-2'}`}>
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
      <nav className="mt-2 mx-2">
        {NAV_LINKS.map((link) => (
          <NavLink
            key={link.name}
            to={link.href}
            title={!isOpen ? link.name : ''}
            onClick={handleNavClick}
            className={({ isActive }) =>
              `flex items-center py-3 my-1 rounded-lg transition-colors duration-200 ${isOpen ? 'px-4' : 'justify-center'} ${
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
                <div className="flex justify-between text-gray-300">
                    <span>Total Posts</span>
                    <span className="font-medium text-white">{stats.total}</span>
                </div>
                <div className="flex justify-between text-gray-300">
                    <span>Procesados</span>
                    <span className="font-medium text-white">{stats.processed}</span>
                </div>
                <div className="flex justify-between text-gray-300">
                    <span>Pendientes</span>
                    <span className="font-medium text-white">{stats.pending}</span>
                </div>
                <div className="flex justify-between text-gray-300">
                    <span>En Papelera</span>
                    <span className="font-medium text-white">{stats.inTrash}</span>
                </div>
            </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;
