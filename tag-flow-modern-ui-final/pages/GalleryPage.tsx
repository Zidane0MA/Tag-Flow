import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useCursorData } from '../hooks/useCursorData';
import { Post, EditStatus, Difficulty, Platform, ProcessStatus } from '../types';
import PostCard from '../components/VideoCard';
import VirtualizedGallery from '../components/VirtualizedGallery';
import EditModal from '../components/EditModal';
import BulkActionBar from '../components/BulkActionBar';
import { FilterParams } from '../services/pagination/types';
import { apiService } from '../services/apiService';

const initialFilters = {
  search: '',
  creator_name: [] as string[], // Cambiado a array para selección múltiple
  platform: '',
  edit_status: '',
  difficulty_level: '',
  processing_status: '',
};

const filterLabels: { [key: string]: string } = {
  search: 'Búsqueda',
  creator_name: 'Creador',
  platform: 'Plataforma',
  edit_status: 'Estado Edición',
  difficulty_level: 'Dificultad',
  processing_status: 'Estado Procesamiento',
};

const GalleryPage: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const {
        posts,
        creators,
        loading,
        loadingMore,
        error,
        scrollState,
        loadVideos,
        loadMoreVideos,
        refreshData,
        setFilters: setCursorFilters,
        clearFilters: clearCursorFilters,
        getStats
    } = useCursorData();

    // Obtenemos hasMore del scrollState del cursor system
    const hasMore = scrollState.hasMore;
    
    // Navigation state for video highlighting and scrolling
    const highlightVideoId = location.state?.highlightVideoId;
    const scrollToVideoId = location.state?.scrollToVideoId;
    const [highlightedVideoId, setHighlightedVideoId] = useState<string | null>(highlightVideoId || null);
    const scrolledToVideoRef = useRef(false);
    
    // Obtener estadísticas para mostrar total de videos
    const stats = getStats();
    const totalVideos = stats.loaded; // En cursor pagination, mostramos los cargados hasta ahora

    // Funciones de bulk actions que no están en useCursorData
    const moveMultipleToTrash = useCallback(async (ids: string[]) => {
        try {
            const success = await apiService.moveToTrash(ids);
            if (success) {
                // Refresh data para actualizar la lista
                await refreshData();
            }
        } catch (error) {
            console.error('Error moving videos to trash:', error);
        }
    }, [refreshData]);

    const reanalyzePosts = useCallback(async (ids: string[]) => {
        try {
            const success = await apiService.reanalyzeVideos(ids);
            if (success) {
                // Refresh data para mostrar los cambios
                await refreshData();
            }
        } catch (error) {
            console.error('Error reanalyzing videos:', error);
        }
    }, [refreshData]);

    const [selectedPosts, setSelectedPosts] = useState<string[]>([]);
    const [editingPost, setEditingPost] = useState<Post | null>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isCreatorDropdownOpen, setIsCreatorDropdownOpen] = useState(false);
    const [creatorSearchTerm, setCreatorSearchTerm] = useState('');
    const creatorDropdownRef = useRef<HTMLDivElement>(null);
    const mainContainerRef = useRef<HTMLElement | null>(null);

    // UNIFIED SCROLL STATE
    const [scrollTop, setScrollTop] = useState(0);
    const [containerHeight, setContainerHeight] = useState(0);

    // Virtualización state (inicializar después de calcular sortedPosts)
    const [useVirtualization, setUseVirtualization] = useState(false);

    // Refs para acceder a valores actuales en el scroll handler
    const loadingMoreRef = useRef(loadingMore);
    const hasMoreRef = useRef(scrollState.hasMore);
    const loadMoreVideosRef = useRef(loadMoreVideos);

    // Actualizar refs cuando cambien los valores
    useEffect(() => {
        loadingMoreRef.current = loadingMore;
    }, [loadingMore]);

    useEffect(() => {
        hasMoreRef.current = scrollState.hasMore;
    }, [scrollState.hasMore]);

    useEffect(() => {
        loadMoreVideosRef.current = loadMoreVideos;
    }, [loadMoreVideos]);
    
    const [filters, setFilters] = useState(initialFilters);
    const [sort, setSort] = useState({ by: 'id', order: 'desc' });
    const [appliedFilters, setAppliedFilters] = useState<FilterParams>({});

    // Convertir filtros locales a formato del API
    const buildApiFilters = useCallback((localFilters: typeof initialFilters): FilterParams => {
        const apiFilters: FilterParams = {};
        
        if (localFilters.search) apiFilters.search = localFilters.search;
        if (localFilters.creator_name && Array.isArray(localFilters.creator_name) && localFilters.creator_name.length > 0) {
            // Enviar múltiples creadores como string separado por comas
            apiFilters.creator_name = localFilters.creator_name.join(',');
        }
        if (localFilters.platform && localFilters.platform !== 'All') {
            // Mapear plataformas del frontend al backend (nuevo esquema)
            const platformMap: { [key: string]: string } = {
                'YouTube': 'youtube',
                'TikTok': 'tiktok',
                'Instagram': 'instagram',
                'Bilibili': 'bilibili',
                'Facebook': 'facebook',
                'Twitter': 'twitter'
            };
            apiFilters.platform = platformMap[localFilters.platform] || localFilters.platform.toLowerCase();
        }
        if (localFilters.edit_status && localFilters.edit_status !== 'All') {
            // Mapear estados de edición del frontend al backend (nuevo esquema)
            const statusMap: { [key: string]: string } = {
                'Pendiente': 'pendiente',
                'En Progreso': 'en_proceso',
                'Completado': 'completado',
                'Descartado': 'descartado'
            };
            apiFilters.edit_status = statusMap[localFilters.edit_status] || localFilters.edit_status.toLowerCase();
        }
        if (localFilters.processing_status && localFilters.processing_status !== 'All') {
            // Mapear estados de procesamiento del frontend al backend (nuevo esquema)
            const statusMap: { [key: string]: string } = {
                'Pendiente': 'pending',
                'Procesando': 'processing',
                'Completado': 'completed',
                'Error': 'failed',
                'Omitido': 'skipped'
            };
            apiFilters.processing_status = statusMap[localFilters.processing_status] || localFilters.processing_status.toLowerCase();
        }
        if (localFilters.difficulty_level && localFilters.difficulty_level !== 'All') {
            // Mapear dificultad del frontend al backend (nuevo esquema)
            const difficultyMap: { [key: string]: string } = {
                'Bajo': 'low',
                'Medio': 'medium',
                'Alto': 'high'
            };
            apiFilters.difficulty_level = difficultyMap[localFilters.difficulty_level] || localFilters.difficulty_level.toLowerCase();
        }

        return apiFilters;
    }, []);

    // Handle navigation from video player - scroll to video and highlight
    useEffect(() => {
        if (scrollToVideoId && posts.length > 0 && !scrolledToVideoRef.current) {
            scrolledToVideoRef.current = true;
            // Wait a bit for posts to render
            setTimeout(() => {
                const videoElement = document.getElementById(`video-card-${scrollToVideoId}`);
                if (videoElement) {
                    videoElement.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center' 
                    });
                }
                // Clear navigation state after using it
                navigate(location.pathname + location.search, { replace: true, state: null });
            }, 100);
        }
        
        // Clear highlight after 3 seconds
        if (highlightedVideoId) {
            const timer = setTimeout(() => {
                setHighlightedVideoId(null);
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [scrollToVideoId, highlightedVideoId, posts, navigate, location.pathname, location.search]);

    // Hook para cerrar dropdown al hacer clic fuera
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (creatorDropdownRef.current && !creatorDropdownRef.current.contains(event.target as Node)) {
                setIsCreatorDropdownOpen(false);
                setCreatorSearchTerm(''); // Limpiar búsqueda al cerrar
            }
        };

        if (isCreatorDropdownOpen) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [isCreatorDropdownOpen]);

    // Aplicar filtros (llamar al backend con cursor system)
    const applyFilters = useCallback(async () => {
        const apiFilters = buildApiFilters(filters);
        setAppliedFilters(apiFilters);
        const backendSortField = sort.by === 'downloadDate' ? 'download_date' : sort.by === 'publicationDate' ? 'publication_date' : sort.by === 'fileName' ? 'file_name' : sort.by;
        await setCursorFilters(apiFilters, backendSortField, sort.order as 'asc' | 'desc');
    }, [filters, sort, buildApiFilters, setCursorFilters]);

    // UNIFIED SCROLL HANDLER
    useEffect(() => {
        const mainElement = document.querySelector('main');
        if (!mainElement) {
            console.warn('Main container not found');
            return;
        }
        mainContainerRef.current = mainElement;

        const handleResize = () => {
            setContainerHeight(mainElement.clientHeight);
        };

        const handleScroll = () => {
            if (!mainContainerRef.current) return;
            const { scrollTop, scrollHeight, clientHeight } = mainContainerRef.current;
            
            // Update scroll position for virtualizer
            setScrollTop(scrollTop);

            // Infinite scroll logic
            if (!loadingMoreRef.current && hasMoreRef.current) {
                const scrollPercentage = scrollTop / (scrollHeight - clientHeight);
                if (scrollPercentage > 0.8) {
                    loadMoreVideosRef.current();
                }
            }
        };

        handleResize(); // Initial size
        mainElement.addEventListener('scroll', handleScroll, { passive: true });
        window.addEventListener('resize', handleResize);

        return () => {
            mainElement.removeEventListener('scroll', handleScroll);
            window.removeEventListener('resize', handleResize);
        };
    }, []); // Empty dependency array, runs once

    // Aplicar filtros cuando cambien (usando dependencia estable)
    useEffect(() => {
        // Solo aplicar si no son los filtros iniciales
        const isInitialFilters = Object.keys(filters).every(key => {
            const value = filters[key as keyof typeof filters];
            const initialValue = initialFilters[key as keyof typeof initialFilters];
            return JSON.stringify(value) === JSON.stringify(initialValue);
        });

        if (!isInitialFilters) {
            const timeoutId = setTimeout(applyFilters, 1500);

            return () => {
                clearTimeout(timeoutId);
            };
        }
    }, [JSON.stringify(filters)]); // Usar JSON.stringify para dependencia estable

    // Aplicar cambios de ordenamiento inmediatamente
    useEffect(() => {
        // Aplicar solo si hay posts cargados (evitar aplicar en el primer render)
        if (posts.length > 0) {
            console.log('📊 SORT CHANGED - Applying immediately:', sort);
            applyFilters();
        }
    }, [sort.by, sort.order]); // Dependencies separadas para detectar cambios específicos

    // Los posts ya vienen ordenados del backend via cursor pagination
    // ✅ ELIMINAMOS ordenamiento local redundante para mejor performance
    const sortedPosts = posts;

    // Virtualización automática para performance (después de sortedPosts)
    const shouldUseVirtualization = sortedPosts.length > 100;
    useEffect(() => {
        setUseVirtualization(shouldUseVirtualization);
    }, [shouldUseVirtualization]);

    const handleSelectPost = (id: string, isSelected: boolean) => {
        if (isSelected) {
            setSelectedPosts(prev => [...prev, id]);
        } else {
            setSelectedPosts(prev => prev.filter(pid => pid !== id));
        }
    };

    const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setFilters(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleCreatorToggle = (creatorName: string) => {
        setFilters(prev => {
            const currentCreators = Array.isArray(prev.creator_name) ? prev.creator_name : [];
            const isSelected = currentCreators.includes(creatorName);
            
            if (isSelected) {
                // Remover si ya está seleccionado
                return { ...prev, creator_name: currentCreators.filter(name => name !== creatorName) };
            } else {
                // Añadir si no está seleccionado
                return { ...prev, creator_name: [...currentCreators, creatorName] };
            }
        });
    };

    const handleRemoveFilter = (filterKey: string) => {
        setFilters(prev => ({ ...prev, [filterKey]: initialFilters[filterKey as keyof typeof initialFilters] }));
    };

    const handleRemoveCreator = (creatorName: string) => {
        setFilters(prev => ({
            ...prev,
            creator_name: Array.isArray(prev.creator_name) 
                ? prev.creator_name.filter(name => name !== creatorName)
                : []
        }));
    };

    const handleResetFilters = async () => {
        setFilters(initialFilters);
        setAppliedFilters({});
        // Limpiar filtros en el cursor system también
        await clearCursorFilters();
    };
    
    const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setSort(prev => ({...prev, [e.target.name]: e.target.value}));
    }

    const activeFilters = useMemo(() => {
        return Object.entries(filters).filter(([key, value]) => {
            const initialValue = initialFilters[key as keyof typeof initialFilters];
            if (key === 'creator_name') {
                return Array.isArray(value) && value.length > 0;
            }
            return value !== initialValue;
        });
    }, [filters]);

    // Lista de creadores únicos para el filtro (siempre todos los de la BD)
    const allCreators = useMemo(() => {
        if (creators && creators.length > 0) {
            return creators.map(c => c.name).sort();
        }
        // Fallback: si no hay creators del API, usar un set vacío para evitar inconsistencias
        return [];
    }, [creators]);

    // Filtrar creadores por el término de búsqueda
    const filteredCreators = useMemo(() => {
        if (!creatorSearchTerm) return allCreators;
        return allCreators.filter(creator => 
            creator.toLowerCase().includes(creatorSearchTerm.toLowerCase())
        );
    }, [allCreators, creatorSearchTerm]);

    // Componente skeleton para loading
    const SkeletonCard = () => (
        <div className="bg-[#212121] rounded-lg overflow-hidden shadow-lg flex flex-col animate-pulse">
            <div className="h-[168px] bg-gray-700"></div>
            <div className="p-3 space-y-3">
                <div className="h-4 bg-gray-700 rounded w-3/4"></div>
                <div className="h-3 bg-gray-700 rounded w-1/2"></div>
                <div className="space-y-2">
                    <div className="h-3 bg-gray-700 rounded w-full"></div>
                    <div className="h-3 bg-gray-700 rounded w-2/3"></div>
                </div>
                <div className="flex justify-between pt-2 border-t border-gray-700">
                    <div className="h-3 bg-gray-700 rounded w-16"></div>
                    <div className="h-3 bg-gray-700 rounded w-16"></div>
                    <div className="h-3 bg-gray-700 rounded w-20"></div>
                </div>
            </div>
        </div>
    );

    // Componente de loading para cargar más
    const LoadingMoreIndicator = () => (
        <div className="flex justify-center items-center py-8">
            <div className="flex items-center space-x-2 text-gray-400">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-red-500"></div>
                <span>Cargando más videos...</span>
            </div>
        </div>
    );

    // Mostrar loading inicial
    if (loading && posts.length === 0) {
        return (
            <>
                {/* Filtros skeleton */}
                <details className="bg-[#212121] p-4 rounded-lg mb-6 shadow-lg animate-pulse">
                    <summary className="font-semibold text-white cursor-pointer select-none flex justify-between items-center list-none">
                        <div className="h-6 bg-gray-700 rounded w-48"></div>
                        <div className="h-4 bg-gray-700 rounded w-32"></div>
                    </summary>
                </details>
                
                {/* Grid skeleton */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                    {Array.from({ length: 12 }).map((_, i) => (
                        <SkeletonCard key={i} />
                    ))}
                </div>
            </>
        );
    }

    // Mostrar error
    if (error) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center bg-red-900/20 border border-red-500 rounded-lg p-8 max-w-md">
                    <div className="text-red-500 text-4xl mb-4">⚠️</div>
                    <h3 className="text-xl font-semibold text-white mb-2">Error al cargar videos</h3>
                    <p className="text-gray-300 mb-4">{error}</p>
                    <button 
                        onClick={() => window.location.reload()} 
                        className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-md transition"
                    >
                        Reintentar
                    </button>
                </div>
            </div>
        );
    }

    return (
        <>
            <details className="bg-[#212121] p-4 rounded-lg mb-6 shadow-lg" open>
                <summary className="font-semibold text-white cursor-pointer select-none flex justify-between items-center list-none">
                    <span className="text-lg">Filtros y Ordenación</span>
                    <span className="text-xs font-normal text-gray-400 hover:text-white transition-colors">
                        expandir/colapsar
                    </span>
                </summary>
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                     <input 
                        type="text" 
                        name="search" 
                        placeholder="Buscar por título, creador, descripción, etc..."
                        value={filters.search} 
                        onChange={handleFilterChange} 
                        className="bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none md:col-span-2 lg:col-span-4"
                    />
                    {/* Selector múltiple de creadores */}
                    <div className="relative" ref={creatorDropdownRef}>
                        <div className="bg-gray-700 text-white rounded focus-within:ring-2 focus-within:ring-red-500">
                            <button 
                                type="button"
                                onClick={() => {
                                    setIsCreatorDropdownOpen(!isCreatorDropdownOpen);
                                    if (isCreatorDropdownOpen) {
                                        setCreatorSearchTerm(''); // Limpiar búsqueda al cerrar
                                    }
                                }}
                                className="w-full h-10 px-2 text-left flex justify-between items-center focus:outline-none focus:ring-2 focus:ring-red-500 min-h-[2.5rem]"
                            >
                                <span className="truncate flex-1">
                                    {Array.isArray(filters.creator_name) && filters.creator_name.length > 0 
                                        ? `${filters.creator_name.length} creador(es) seleccionado(s)`
                                        : 'Seleccionar Creadores'
                                    }
                                </span>
                                <svg className={`w-4 h-4 flex-shrink-0 ml-2 transition-transform ${isCreatorDropdownOpen ? 'rotate-180' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                </svg>
                            </button>
                            {isCreatorDropdownOpen && (
                                <div className="absolute z-10 w-full bg-gray-700 border border-gray-600 rounded-b shadow-lg">
                                    {/* Buscador de creadores */}
                                    <div className="p-2 border-b border-gray-600">
                                        <input
                                            type="text"
                                            placeholder="Buscar creadores..."
                                            value={creatorSearchTerm}
                                            onChange={(e) => setCreatorSearchTerm(e.target.value)}
                                            className="w-full px-2 py-1 text-sm bg-gray-600 text-white rounded border border-gray-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                            onClick={(e) => e.stopPropagation()}
                                        />
                                    </div>
                                    
                                    {/* Lista de creadores con scroll personalizado */}
                                    <div className="max-h-60 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-500 scrollbar-track-gray-700">
                                        {filteredCreators.length > 0 ? (
                                            filteredCreators.map(creator => (
                                                <label key={creator} className="flex items-center p-2 hover:bg-gray-600 cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        checked={Array.isArray(filters.creator_name) && filters.creator_name.includes(creator)}
                                                        onChange={() => handleCreatorToggle(creator)}
                                                        className="mr-2 rounded focus:ring-red-500"
                                                    />
                                                    <span className="truncate text-sm">{creator}</span>
                                                </label>
                                            ))
                                        ) : (
                                            <div className="p-4 text-center text-gray-400 text-sm">
                                                No se encontraron creadores
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                    <select name="platform" value={filters.platform} onChange={handleFilterChange} className="bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none">
                        <option value="">Todas las Plataformas</option>
                        <option value="All">Todas las Plataformas</option>
                        {Object.values(Platform).map(p => (
                            <option key={p} value={p}>
                                {p === 'youtube' ? 'YouTube' :
                                 p === 'tiktok' ? 'TikTok' :
                                 p === 'instagram' ? 'Instagram' :
                                 p === 'bilibili' ? 'Bilibili' :
                                 p === 'facebook' ? 'Facebook' :
                                 p === 'twitter' ? 'Twitter' : p}
                            </option>
                        ))}
                    </select>
                    <select name="edit_status" value={filters.edit_status} onChange={handleFilterChange} className="bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none">
                        <option value="">Todos los Estados</option>
                        <option value="All">Todos los Estados</option>
                        {Object.values(EditStatus).map(s => (
                            <option key={s} value={s}>
                                {s === 'pendiente' ? 'Pendiente' :
                                 s === 'en_proceso' ? 'En Proceso' :
                                 s === 'completado' ? 'Completado' :
                                 s === 'descartado' ? 'Descartado' : s}
                            </option>
                        ))}
                    </select>
                     <select name="difficulty_level" value={filters.difficulty_level} onChange={handleFilterChange} className="bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none">
                        <option value="">Toda la Dificultad</option>
                        <option value="All">Toda la Dificultad</option>
                        {Object.values(Difficulty).map(d => (
                            <option key={d} value={d}>
                                {d === 'low' ? 'Bajo' :
                                 d === 'medium' ? 'Medio' :
                                 d === 'high' ? 'Alto' : d}
                            </option>
                        ))}
                    </select>
                    <select name="processing_status" value={filters.processing_status} onChange={handleFilterChange} className="bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none">
                        <option value="">Todos los Procesos</option>
                        <option value="All">Todos los Procesos</option>
                        {Object.values(ProcessStatus).map(p => (
                            <option key={p} value={p}>
                                {p === 'pending' ? 'Pendiente' :
                                 p === 'processing' ? 'Procesando' :
                                 p === 'completed' ? 'Completado' :
                                 p === 'failed' ? 'Error' :
                                 p === 'skipped' ? 'Omitido' : p}
                            </option>
                        ))}
                    </select>
                    <div className="flex gap-2">
                        <select name="by" value={sort.by} onChange={handleSortChange} className="bg-gray-700 text-white rounded p-2 w-full focus:ring-2 focus:ring-red-500 focus:outline-none">
                            <option value="id">ID</option>
                            <option value="title">Título</option>
                            <option value="size">Tamaño</option>
                            <option value="duration">Duración</option>
                            <option value="fileName">Nombre Archivo</option>
                            <option value="downloadDate">Fecha Descarga</option>
                            <option value="publicationDate">Fecha Publicación</option>
                        </select>
                         <select name="order" value={sort.order} onChange={handleSortChange} className="bg-gray-700 text-white rounded p-2 w-full focus:ring-2 focus:ring-red-500 focus:outline-none">
                            <option value="desc">Desc</option>
                            <option value="asc">Asc</option>
                        </select>
                    </div>
                </div>
            </details>

             {activeFilters.length > 0 && (
                <div className="mb-6 flex items-center flex-wrap gap-2">
                    <span className="text-sm font-medium text-gray-400">Filtros Activos:</span>
                    {activeFilters.flatMap(([key, value]) => {
                        if (key === 'creator_name' && Array.isArray(value)) {
                            // Mostrar cada creador como un chip individual
                            return value.map((creator: string) => (
                                <span key={`${key}-${creator}`} className="flex items-center bg-gray-600 text-white text-xs font-semibold px-2.5 py-1 rounded-full">
                                    {filterLabels[key]}: {creator}
                                    <button onClick={() => handleRemoveCreator(creator)} className="ml-2 text-gray-300 hover:text-white text-base leading-none">
                                        &times;
                                    </button>
                                </span>
                            ));
                        } else {
                            // Filtros normales
                            return (
                                <span key={key} className="flex items-center bg-gray-600 text-white text-xs font-semibold px-2.5 py-1 rounded-full">
                                    {filterLabels[key]}: {String(value)}
                                    <button onClick={() => handleRemoveFilter(key)} className="ml-2 text-gray-300 hover:text-white text-base leading-none">
                                        &times;
                                    </button>
                                </span>
                            );
                        }
                    })}
                    <button onClick={handleResetFilters} className="text-sm text-red-500 hover:text-red-400 hover:underline ml-2">
                        Limpiar Todo
                    </button>
                </div>
            )}

            {/* Notificación flotante de virtualización */}
            {sortedPosts.length > 50 && (
                <div className="fixed bottom-4 right-4 z-50 max-w-xs">
                    <div className="bg-[#1a1a1a] border border-gray-600 rounded-lg shadow-2xl p-3">
                        <div className="flex items-center justify-between mb-2">
                            <div className="text-sm font-medium text-white">
                                🚀 Performance
                            </div>
                            <button
                                onClick={() => setUseVirtualization(!useVirtualization)}
                                className={`ml-3 px-2 py-1 text-xs font-medium rounded transition-colors ${
                                    useVirtualization
                                        ? 'bg-green-600 text-white hover:bg-green-500'
                                        : 'bg-blue-600 text-white hover:bg-blue-500'
                                }`}
                            >
                                {useVirtualization ? '✅' : '⚡'}
                            </button>
                        </div>
                        <div className="text-xs text-gray-300">
                            {sortedPosts.length} posts cargados
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                            {useVirtualization ? 'Virtualizado' : 'Recomendado: virtualizaón'}
                        </div>
                    </div>
                </div>
            )}
            
            <div className={selectedPosts.length > 0 ? 'pb-24' : ''}>
                {sortedPosts.length > 0 ? (
                    <>
                        {useVirtualization ? (
                            /* Galería virtualizada simplificada */
                            <VirtualizedGallery
                                posts={sortedPosts}
                                loadingMore={loadingMore}
                                selectedPosts={selectedPosts}
                                onSelectPost={(id: string) => handleSelectPost(id, !selectedPosts.includes(id))}
                                onEditPost={setEditingPost}
                                onRefreshData={refreshData}
                                highlightedVideoId={highlightedVideoId}
                                scrollTop={scrollTop}
                                containerHeight={containerHeight}
                            />
                        ) : (
                            /* Galería normal para funcionalidad completa */
                            <>
                                <div id="gallery-container" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                                    {sortedPosts.map(post => (
                                        <PostCard
                                            key={post.id}
                                            video={post}
                                            videos={sortedPosts}
                                            isSelected={selectedPosts.includes(post.id)}
                                            onSelect={handleSelectPost}
                                            onEdit={setEditingPost}
                                            isHighlighted={highlightedVideoId === post.id}
                                            onRefresh={refreshData}
                                        />
                                    ))}
                                </div>

                                {/* Indicador de carga para más contenido */}
                                {loadingMore && <LoadingMoreIndicator />}
                            </>
                        )}

                        {/* Mensaje de final de contenido */}
                        {!hasMore && posts.length > 0 && (
                            <div className="text-center py-8 text-gray-400">
                                <p>Todos los videos cargados ({posts.length} total)</p>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="text-center py-16">
                        <h3 className="text-2xl font-semibold text-white">No se encontraron videos</h3>
                        <p className="text-gray-400 mt-2">Intenta ajustar tus filtros o búsqueda para encontrar lo que buscas.</p>
                        <button onClick={handleResetFilters} className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-md transition">
                            Limpiar Filtros
                        </button>
                    </div>
                )}
            </div>

            <BulkActionBar
                isVisible={selectedPosts.length > 0}
                selectedCount={selectedPosts.length}
                onReanalyze={() => reanalyzePosts(selectedPosts)}
                onEdit={() => setIsEditModalOpen(true)}
                onDelete={() => {moveMultipleToTrash(selectedPosts); setSelectedPosts([])}}
                onClear={() => setSelectedPosts([])}
            />
            
            {editingPost && <EditModal video={editingPost} onClose={() => setEditingPost(null)} />}
            {isEditModalOpen && <EditModal videoIds={selectedPosts} onClose={() => { setIsEditModalOpen(false); setSelectedPosts([]); }} />}
        </>
    );
};

export default GalleryPage;