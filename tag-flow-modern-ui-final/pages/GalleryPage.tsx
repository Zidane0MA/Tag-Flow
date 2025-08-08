import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useRealData } from '../hooks/useRealData';
import useInfiniteScroll from '../hooks/useInfiniteScroll';
import { Post, EditStatus, Difficulty, Platform, ProcessStatus } from '../types';
import PostCard from '../components/VideoCard';
import EditModal from '../components/EditModal';
import BulkActionBar from '../components/BulkActionBar';
import { VideoFilters } from '../services/apiService';

const initialFilters = {
  search: '',
  creator_name: '',
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
        moveMultipleToTrash, 
        reanalyzePosts, 
        loading, 
        loadingMore,
        hasMore,
        error, 
        loadVideos,
        loadMoreVideos,
        creators,
        getStats
    } = useRealData();
    
    // Navigation state for video highlighting and scrolling
    const highlightVideoId = location.state?.highlightVideoId;
    const scrollToVideoId = location.state?.scrollToVideoId;
    const [highlightedVideoId, setHighlightedVideoId] = useState<string | null>(highlightVideoId || null);
    const scrolledToVideoRef = useRef(false);
    
    // Obtener estadísticas para mostrar total de videos
    const stats = getStats();
    const totalVideos = stats.total;

    const [selectedPosts, setSelectedPosts] = useState<string[]>([]);
    const [editingPost, setEditingPost] = useState<Post | null>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    
    const [filters, setFilters] = useState(initialFilters);
    const [sort, setSort] = useState({ by: 'downloadDate', order: 'desc' });
    const [appliedFilters, setAppliedFilters] = useState<VideoFilters>({});

    // Convertir filtros locales a formato del API
    const buildApiFilters = useCallback((localFilters: typeof initialFilters): VideoFilters => {
        const apiFilters: VideoFilters = {};
        
        if (localFilters.search) apiFilters.search = localFilters.search;
        if (localFilters.creator_name && localFilters.creator_name !== 'All') apiFilters.creator_name = localFilters.creator_name;
        if (localFilters.platform && localFilters.platform !== 'All') {
            // Mapear plataformas del frontend al backend
            const platformMap: { [key: string]: string } = {
                'YouTube': 'youtube',
                'TikTok': 'tiktok',
                'Instagram': 'instagram',
                'Vimeo': 'vimeo',
                'Facebook': 'facebook',
                'Twitter': 'twitter',
                'Twitch': 'twitch',
                'Discord': 'discord',
                'bilibili': 'bilibili',
                'bilibili.tv': 'bilibili/video/tv'
            };
            apiFilters.platform = platformMap[localFilters.platform] || localFilters.platform.toLowerCase();
        }
        if (localFilters.edit_status && localFilters.edit_status !== 'All') {
            // Mapear estados de edición del frontend al backend
            const statusMap: { [key: string]: string } = {
                'Pendiente': 'nulo',
                'En Progreso': 'en_proceso',
                'Completado': 'hecho'
            };
            apiFilters.edit_status = statusMap[localFilters.edit_status] || localFilters.edit_status;
        }
        if (localFilters.processing_status && localFilters.processing_status !== 'All') {
            // Mapear estados de procesamiento del frontend al backend
            const statusMap: { [key: string]: string } = {
                'Pendiente': 'pendiente',
                'Procesando': 'procesando',
                'Completado': 'completado',
                'Error': 'error'
            };
            apiFilters.processing_status = statusMap[localFilters.processing_status] || localFilters.processing_status;
        }
        if (localFilters.difficulty_level && localFilters.difficulty_level !== 'All') {
            // Mapear dificultad del frontend al backend
            const difficultyMap: { [key: string]: string } = {
                'Bajo': 'bajo',
                'Medio': 'medio',
                'Alto': 'alto'
            };
            apiFilters.difficulty_level = difficultyMap[localFilters.difficulty_level] || localFilters.difficulty_level;
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

    // Aplicar filtros (llamar al backend)
    const applyFilters = useCallback(async () => {
        const apiFilters = buildApiFilters(filters);
        setAppliedFilters(apiFilters);
        await loadVideos(apiFilters);
    }, [filters, buildApiFilters, loadVideos]);

    // Memoizar el callback para evitar recreaciones constantes
    const infiniteScrollCallback = useCallback(() => {
        if (!loadingMore && hasMore) {
            loadMoreVideos();
        }
    }, [loadingMore, hasMore, loadMoreVideos]);

    // Simplificar enabled - solo usar hasMore ya que es el más estable
    const infiniteScrollEnabled = hasMore && posts.length > 0;
    
    // Memoizar las opciones para evitar recreaciones constantes
    const infiniteScrollOptions = useMemo(() => ({
        threshold: 400,
        enabled: infiniteScrollEnabled
    }), [infiniteScrollEnabled]);

    // Hook para scroll infinito
    useInfiniteScroll(infiniteScrollCallback, infiniteScrollOptions);

    // Aplicar filtros cuando cambien
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            applyFilters();
        }, 500); // Debounce de 500ms

        return () => clearTimeout(timeoutId);
    }, [applyFilters]);

    // Ordenación local (ya que los posts vienen del backend)
    const sortedPosts = useMemo(() => {
        return [...posts].sort((a, b) => {
            const aVal = a[sort.by as keyof Post];
            const bVal = b[sort.by as keyof Post];
            if (aVal < bVal) return sort.order === 'asc' ? -1 : 1;
            if (aVal > bVal) return sort.order === 'asc' ? 1 : -1;
            return 0;
        });
    }, [posts, sort]);

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

    const handleRemoveFilter = (filterKey: string) => {
        setFilters(prev => ({ ...prev, [filterKey]: initialFilters[filterKey as keyof typeof initialFilters] }));
    };

    const handleResetFilters = () => {
        setFilters(initialFilters);
    };
    
    const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setSort(prev => ({...prev, [e.target.name]: e.target.value}));
    }

    const activeFilters = useMemo(() =>
        Object.entries(filters).filter(([key, value]) => value !== initialFilters[key as keyof typeof initialFilters]),
      [filters]
    );

    // Lista de creadores únicos para el filtro
    const uniqueCreators = useMemo(() => {
        if (creators && creators.length > 0) {
            return creators.map(c => c.name);
        }
        return [...new Set(posts.map(p => p.creator))];
    }, [creators, posts]);

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
                        Haga clic para expandir/colapsar
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
                     <select name="creator_name" value={filters.creator_name} onChange={handleFilterChange} className="bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none">
                        <option value="">Todos los Creadores</option>
                        <option value="All">Todos los Creadores</option>
                        {uniqueCreators.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                    <select name="platform" value={filters.platform} onChange={handleFilterChange} className="bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none">
                        <option value="">Todas las Plataformas</option>
                        <option value="All">Todas las Plataformas</option>
                        {Object.values(Platform).map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                    <select name="edit_status" value={filters.edit_status} onChange={handleFilterChange} className="bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none">
                        <option value="">Todos los Estados</option>
                        <option value="All">Todos los Estados</option>
                        {Object.values(EditStatus).map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                     <select name="difficulty_level" value={filters.difficulty_level} onChange={handleFilterChange} className="bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none">
                        <option value="">Toda la Dificultad</option>
                        <option value="All">Toda la Dificultad</option>
                        {Object.values(Difficulty).map(d => <option key={d} value={d}>{d}</option>)}
                    </select>
                    <select name="processing_status" value={filters.processing_status} onChange={handleFilterChange} className="bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none">
                        <option value="">Todos los Procesos</option>
                        <option value="All">Todos los Procesos</option>
                        {Object.values(ProcessStatus).map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                    <div className="flex gap-2">
                        <select name="by" value={sort.by} onChange={handleSortChange} className="bg-gray-700 text-white rounded p-2 w-full focus:ring-2 focus:ring-red-500 focus:outline-none">
                            <option value="downloadDate">Fecha Descarga</option>
                            <option value="id">ID</option>
                            <option value="title">Nombre</option>
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
                    {activeFilters.map(([key, value]) => (
                        <span key={key} className="flex items-center bg-gray-600 text-white text-xs font-semibold px-2.5 py-1 rounded-full">
                            {filterLabels[key]}: {String(value)}
                            <button onClick={() => handleRemoveFilter(key)} className="ml-2 text-gray-300 hover:text-white text-base leading-none">
                                &times;
                            </button>
                        </span>
                    ))}
                    <button onClick={handleResetFilters} className="text-sm text-red-500 hover:text-red-400 hover:underline ml-2">
                        Limpiar Todo
                    </button>
                </div>
            )}
            
            <div className={selectedPosts.length > 0 ? 'pb-24' : ''}>
                {sortedPosts.length > 0 ? (
                    <>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                            {sortedPosts.map(post => (
                                <PostCard
                                    key={post.id}
                                    video={post}
                                    videos={sortedPosts}
                                    isSelected={selectedPosts.includes(post.id)} 
                                    onSelect={handleSelectPost}
                                    onEdit={setEditingPost}
                                    isHighlighted={highlightedVideoId === post.id}
                                />
                            ))}
                        </div>

                        {/* Indicador de carga para más contenido */}
                        {loadingMore && <LoadingMoreIndicator />}
                        
                        {/* Mensaje de final de contenido */}
                        {!hasMore && posts.length > 0 && (
                            <div className="text-center py-8 text-gray-400">
                                <p>Has visto todos los videos disponibles ({posts.length} videos)</p>
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