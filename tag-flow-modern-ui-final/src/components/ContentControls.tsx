import React, { useRef, useEffect } from 'react';
import { ICONS, getCategoryIcon } from '../constants';
import { Platform } from '../types';

interface ContentControlsProps {
    showSearch: boolean;
    setShowSearch: (show: boolean) => void;
    searchText: string;
    setSearchText: (text: string) => void;
    onSearchSubmit: () => void;
    showFilterMenu: boolean;
    setShowFilterMenu: (show: boolean) => void;
    selectedDynamicFilters: string[];
    toggleDynamicFilter: (filter: string) => void;
    availableCategories: string[];
    activePlatform?: Platform;
    sortBy: string;
    onSortByChange: (value: string) => void;
    sortOrder: 'asc' | 'desc';
    toggleSortOrder: () => void;
    showMobileTools: boolean;
    setShowMobileTools: (show: boolean) => void;
}

const ContentControls: React.FC<ContentControlsProps> = ({
    showSearch,
    setShowSearch,
    searchText,
    setSearchText,
    onSearchSubmit,
    showFilterMenu,
    setShowFilterMenu,
    selectedDynamicFilters,
    toggleDynamicFilter,
    availableCategories,
    activePlatform,
    sortBy,
    onSortByChange,
    sortOrder,
    toggleSortOrder,
    showMobileTools,
    setShowMobileTools
}) => {
    const searchInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (showSearch && searchInputRef.current) {
            searchInputRef.current.focus();
        }
    }, [showSearch]);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            const target = event.target as HTMLElement;
            if (showFilterMenu && !target.closest('.filter-menu-container')) {
                setShowFilterMenu(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showFilterMenu, setShowFilterMenu]);

    return (
        <>
            {/* Mobile Tools Toggle */}
            <button 
                onClick={() => setShowMobileTools(!showMobileTools)}
                className="md:hidden p-2 rounded-lg bg-[#212121]/50 text-gray-400 hover:text-white hover:bg-[#212121] transition-colors flex-shrink-0"
            >
                {showMobileTools ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                )}
            </button>

            <div className={`flex items-center gap-2 bg-black/30 rounded-lg flex-shrink-0 transition-all duration-300 ease-in-out ${showMobileTools ? 'max-w-[500px] opacity-100 p-1.5' : 'max-w-0 opacity-0 p-0 overflow-hidden md:max-w-none md:opacity-100 md:p-1.5'}`}>
                <div className={`transition-all duration-300 overflow-hidden flex items-center ${showSearch ? 'w-24 opacity-100 border-b border-gray-500 mr-2' : 'w-0 opacity-0'}`}>
                    <input 
                        ref={searchInputRef} 
                        type="text" 
                        className="bg-transparent text-white px-2 py-1 focus:outline-none w-full text-sm" 
                        placeholder="Buscar..." 
                        value={searchText} 
                        onChange={(e) => setSearchText(e.target.value)} 
                        onKeyDown={(e) => { if (e.key === 'Enter') onSearchSubmit(); }} 
                    />
                </div>
                <button onClick={() => setShowSearch(!showSearch)} className={`p-2 hover:bg-white/10 rounded-lg transition ${showSearch ? 'text-white' : 'text-gray-400'}`} title="Buscar">
                    {React.cloneElement(ICONS.search, { className: 'h-5 w-5' })}
                </button>
                <div className="relative filter-menu-container">
                    <button onClick={() => setShowFilterMenu(!showFilterMenu)} className={`p-2 hover:bg-white/10 rounded-lg transition ${showFilterMenu || selectedDynamicFilters.length > 0 ? 'text-white' : 'text-gray-400'}`} title="Filtrar y Ordenar">
                        {React.cloneElement(ICONS.filter, { className: 'h-5 w-5' })}
                        {selectedDynamicFilters.length > 0 && (<span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>)}
                    </button>
                    {showFilterMenu && (
                        <div className="absolute right-0 top-full mt-2 w-56 bg-[#1a1a1a] border border-gray-700 rounded-lg shadow-xl z-50 p-3">
                            <div className="mb-3">
                                <div className="text-xs font-bold text-gray-500 uppercase mb-2 px-1">Ordenar por</div>
                                <div className="relative">
                                    <select value={sortBy} onChange={(e) => onSortByChange(e.target.value)} className="w-full bg-gray-800 text-white text-sm rounded-md border-gray-600 focus:outline-none focus:ring-1 focus:ring-red-500 focus:border-red-500 p-2 pr-10 cursor-pointer hover:border-gray-500 transition-colors appearance-none">
                                        <option value="publication_date">Publicación</option>
                                        <option value="download_date">Descarga</option>
                                        <option value="title">Título</option>
                                        <option value="size">Tamaño</option>
                                        <option value="duration">Duración</option>
                                        <option value="id">ID</option>
                                    </select>
                                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none text-gray-400">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7 7" />
                                        </svg>
                                    </div>
                                </div>
                            </div>
                            <div className="border-t border-gray-700 my-2"></div>
                            <div>
                                <div className="text-xs font-bold text-gray-500 uppercase mb-2 px-1">Tipos de Contenido</div>
                                <div className="space-y-1">
                                    {availableCategories.map(category => (
                                        <label key={category} className="flex items-center gap-2 px-2 py-1.5 hover:bg-white/5 rounded cursor-pointer">
                                            <input type="checkbox" checked={selectedDynamicFilters.includes(category)} onChange={() => toggleDynamicFilter(category)} className="rounded border-gray-600 bg-gray-800 text-red-600 focus:ring-red-500" />
                                            <span className="flex items-center gap-2 text-sm text-gray-300">{getCategoryIcon(category, activePlatform)}<span className="capitalize">{category}</span></span>
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
                <button onClick={toggleSortOrder} className="p-2 hover:bg-white/10 rounded-lg transition text-gray-400 hover:text-white" title={`Ordenar ${sortOrder === 'asc' ? 'Ascendente' : 'Descendente'}`}>
                    {sortOrder === 'asc' ? React.cloneElement(ICONS.sort_asc, { className: 'h-5 w-5' }) : React.cloneElement(ICONS.sort_desc, { className: 'h-5 w-5' })}
                </button>
            </div>
        </>
    );
};

export default ContentControls;
