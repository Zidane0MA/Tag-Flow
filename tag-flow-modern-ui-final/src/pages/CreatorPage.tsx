import React, { useMemo, useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom';
import { useCursorCreatorData } from '../hooks/useCursorCreatorData';
import { Creator, Platform, CreatorPlatformInfo, CategoryType } from '../types';
import PostCard from '../components/VideoCard';
import Breadcrumbs, { Crumb } from '../components/Breadcrumbs';
import PlatformTabs, { Tab } from '../components/PlatformTabs';
import SubscriptionList from '../components/SubscriptionList';
import { ICONS, getSubscriptionIcon, getCategoryIcon } from '../constants';
import { apiService } from '../services/apiService';

const CreatorPage: React.FC = () => {
    const { creatorName, platform: platformParam, subscriptionId } = useParams<{ creatorName: string, platform?: string, subscriptionId?: string }>();
    const location = useLocation();

    const [fetchedCreator, setFetchedCreator] = useState<Creator | null>(null);
    const [creatorMetadataLoading, setCreatorMetadataLoading] = useState<boolean>(true);
    const [creatorMetadataError, setCreatorMetadataError] = useState<string | null>(null);

    const decodedPlatform = platformParam ? decodeURIComponent(platformParam) : undefined;

    const {
        posts: displayedPosts,
        loading: postsLoading,
        loadingMore,
        error: videosError,
        scrollState,
        loadCreatorVideos,
        loadMoreVideos,
        refreshData,
        clearData,
        filters,
        setAndReloadFilters
    } = useCursorCreatorData();
    const navigate = useNavigate();

    const highlightVideoId = location.state?.highlightVideoId;
    const scrollToVideoId = location.state?.scrollToVideoId;
    const [highlightedVideoId, setHighlightedVideoId] = useState<string | null>(highlightVideoId || null);
    const scrolledToVideoRef = useRef(false);

    const [showSearch, setShowSearch] = useState(false);
    const [searchText, setSearchText] = useState('');
    const [showFilterMenu, setShowFilterMenu] = useState(false);
    const [selectedDynamicFilters, setSelectedDynamicFilters] = useState<string[]>([]);
    const searchInputRef = useRef<HTMLInputElement>(null);

    const activePlatform = useMemo(() => {
        return decodedPlatform as Platform | undefined;
    }, [decodedPlatform]);

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
    }, [showFilterMenu]);

    const handleSearchSubmit = useCallback(() => {
        if (searchText !== filters.search) {
            setAndReloadFilters({ search: searchText });
        }
    }, [searchText, filters.search, setAndReloadFilters]);

    const toggleSortOrder = useCallback(() => {
        setAndReloadFilters({ sort_order: filters.sort_order === 'asc' ? 'desc' : 'asc' });
    }, [filters.sort_order, setAndReloadFilters]);

    const handleSortByChange = useCallback((newSortBy: string) => {
        setAndReloadFilters({ sort_by: newSortBy });
    }, [setAndReloadFilters]);

    const toggleDynamicFilter = (filter: string) => {
        setSelectedDynamicFilters(prev => 
            prev.includes(filter) 
                ? prev.filter(f => f !== filter)
                : [...prev, filter]
        );
    };

    const getPlatformCategories = (platform?: Platform): CategoryType[] => {
        switch (platform) {
            case Platform.INSTAGRAM:
                return ['feed', 'reels', 'stories', 'highlights', 'tagged'];
            case Platform.YOUTUBE:
                return ['videos', 'shorts'];
            case Platform.TIKTOK:
                return ['videos'];
            default:
                return ['videos'];
        }
    };

    const availableCategories = useMemo(() => getPlatformCategories(activePlatform), [activePlatform]);

    useEffect(() => {
        if (creatorName) {
            setCreatorMetadataLoading(true);
            setCreatorMetadataError(null);
            apiService.getCreator(creatorName)
                .then(data => {
                    setFetchedCreator(data);
                })
                .catch(err => {
                    console.error('Error fetching creator metadata:', err);
                    setCreatorMetadataError('Error al cargar la información del creador.');
                })
                .finally(() => {
                    setCreatorMetadataLoading(false);
                });
        } else {
            setFetchedCreator(null);
            setCreatorMetadataLoading(false);
        }
    }, [creatorName]);

    const creator = useMemo(() => fetchedCreator, [fetchedCreator]);

    const activePlatformSubscriptions = useMemo(() => {
        if (!creator || !activePlatform || !creator.platforms) return [];
        const platformInfo = creator.platforms[activePlatform];
        return platformInfo?.subscriptions || [];
    }, [creator, activePlatform]);

    useEffect(() => {
        if (creatorName) {
            if (subscriptionId && creatorMetadataLoading) return;

            let subType: string | undefined = undefined;
            let effectiveSubId: string | undefined = undefined;

            if (subscriptionId && activePlatformSubscriptions.length > 0) {
                const sub = activePlatformSubscriptions.find(s => s.id.toString() === subscriptionId);
                if (sub && typeof sub.id === 'number') {
                    subType = sub.type;
                    effectiveSubId = subscriptionId;
                }
            }
            loadCreatorVideos(creatorName, activePlatform);
        } else {
            clearData();
        }
    }, [creatorName, activePlatform, subscriptionId, creatorMetadataLoading, activePlatformSubscriptions, filters, loadCreatorVideos, clearData]);

    useEffect(() => {
        if (scrollToVideoId && displayedPosts.length > 0 && !scrolledToVideoRef.current) {
            scrolledToVideoRef.current = true;
            setTimeout(() => {
                const videoElement = document.getElementById(`video-card-${scrollToVideoId}`);
                if (videoElement) {
                    videoElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                navigate(location.pathname + location.search, { replace: true, state: null });
            }, 100);
        }
        if (highlightedVideoId) {
            const timer = setTimeout(() => setHighlightedVideoId(null), 3000);
            return () => clearTimeout(timer);
        }
    }, [scrollToVideoId, highlightedVideoId, displayedPosts, navigate, location.pathname, location.search]);

    const loadingMoreRef = useRef(false);
    const hasMoreRef = useRef(true);
    const loadMoreVideosRef = useRef(loadMoreVideos);
    const mainContainerRef = useRef<HTMLElement | null>(null);

    useEffect(() => {
        loadingMoreRef.current = loadingMore;
        hasMoreRef.current = scrollState.hasMore;
        loadMoreVideosRef.current = loadMoreVideos;
    }, [loadingMore, scrollState.hasMore, loadMoreVideos]);

    const handleScroll = useCallback(() => {
        if (loadingMoreRef.current || !hasMoreRef.current) return;
        const container = mainContainerRef.current;
        if (!container) return;
        const { scrollTop, scrollHeight, clientHeight } = container;
        if ((scrollTop + clientHeight) / scrollHeight > 0.8) {
            loadMoreVideosRef.current();
        }
    }, []);

    useEffect(() => {
        const mainElement = document.querySelector('main');
        mainContainerRef.current = mainElement;
        if (!mainElement) return;
        mainElement.addEventListener('scroll', handleScroll, { passive: true });
        return () => mainElement.removeEventListener('scroll', handleScroll);
    }, [handleScroll]);

    const totalPostCount = useMemo(() => {
        if (creator?.platforms) {
            return Object.values(creator.platforms).reduce((sum: number, p: any) => {
                const platformInfo = p as CreatorPlatformInfo;
                return sum + (platformInfo.postCount || 0);
            }, 0);
        }
        return 0;
    }, [creator]);

    const platformTabs: Tab[] = useMemo(() => {
        const tabs: Tab[] = [{ id: 'all', label: 'All', count: totalPostCount }];
        if (creator && creator.platforms) {
            Object.entries(creator.platforms).forEach(([platformId, platformInfo]) => {
                tabs.push({
                    id: platformId,
                    label: platformId.charAt(0).toUpperCase() + platformId.slice(1),
                    count: (platformInfo as CreatorPlatformInfo).postCount
                });
            });
        }
        return tabs.sort((a, b) => {
            if (a.id === 'all') return -1;
            if (b.id === 'all') return 1;
            return a.label.localeCompare(b.label);
        });
    }, [creator, totalPostCount]);

    const handlePlatformTabClick = (platformId: string) => {
        navigate(`/creator/${encodeURIComponent(creatorName || '')}${platformId === 'all' ? '' : `/${encodeURIComponent(platformId)}`}`);
    };
    
    const handleSubscriptionClick = (subId: string) => {
        navigate(`/creator/${creatorName}/${encodeURIComponent(activePlatform || '')}/${encodeURIComponent(subId)}`);
    }

    if (creatorMetadataLoading || (postsLoading && !scrollState.initialLoaded)) {
        return <div className="text-center py-16"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div><p className="text-gray-400 mt-4">Cargando...</p></div>;
    }
    
    if (creatorMetadataError) {
        return <div className="text-center py-16"><h3 className="text-2xl font-semibold text-white">Error</h3><p className="text-gray-400 mt-2">{creatorMetadataError}</p></div>;
    }

    if (!creator && !creatorMetadataLoading) {
        return <div className="text-center py-16"><h3 className="text-2xl font-semibold text-white">Creador no encontrado</h3><p className="text-gray-400 mt-2">No se pudo encontrar al creador "{creatorName}".</p><Link to="/gallery" className="mt-4 inline-block px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-md transition">Volver a la Galería</Link></div>;
    }
    
    const breadcrumbs: Crumb[] = [
        { label: 'Galería', href: '/gallery', icon: ICONS.gallery },
        { label: creator?.displayName || creatorName, href: `/creator/${creatorName}`, icon: ICONS.user },
    ];
    if(activePlatform) {
        breadcrumbs.push({ label: activePlatform, href: `/creator/${creatorName}/${encodeURIComponent(activePlatform)}`});
        if(subscriptionId) {
            const sub = activePlatformSubscriptions.find(s => s.id.toString() === subscriptionId);
            if(sub) breadcrumbs.push({ label: sub.name, href: `/creator/${creatorName}/${encodeURIComponent(activePlatform)}/${encodeURIComponent(subscriptionId)}`});
        }
    }

    return (
        <div className="space-y-6">
            <header>
                <Breadcrumbs crumbs={breadcrumbs} />
                <div className="flex flex-wrap justify-between items-start gap-4">
                    <div><h1 className="text-3xl font-bold text-white">{creator?.displayName || creatorName}</h1></div>
                    <div className="flex items-center gap-3">
                        {creator?.platforms && Object.entries(creator.platforms).map(([platformName, platformInfo]) => (
                            (platformInfo as CreatorPlatformInfo).url && (
                                <a key={platformName} href={(platformInfo as CreatorPlatformInfo).url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-2 rounded-lg bg-[#212121]/50 border border-gray-700/50 hover:bg-red-500/20 text-gray-300 hover:text-white transition-colors">
                                    <span className="font-semibold text-sm">{platformName.charAt(0).toUpperCase() + platformName.slice(1)}</span>
                                    {React.cloneElement(ICONS.external_link, { className: 'h-4 w-4' })}
                                </a>
                            )
                        ))}
                    </div>
                </div>
            </header>
            
            <div className="flex flex-col md:flex-row justify-between items-end gap-4">
                <div className="flex-1 w-full md:w-auto">
                    <PlatformTabs tabs={platformTabs} activeTab={activePlatform || 'all'} onTabClick={handlePlatformTabClick} />
                </div>
                <div className="flex items-center gap-2 bg-black/30 p-1.5 rounded-lg">
                    <div className={`transition-all duration-300 overflow-hidden flex items-center ${showSearch ? 'w-48 opacity-100 border-b border-gray-500 mr-2' : 'w-0 opacity-0'}`}>
                        <input ref={searchInputRef} type="text" className="bg-transparent text-white px-2 py-1 focus:outline-none w-full text-sm" placeholder="Buscar en este creador..." value={searchText} onChange={(e) => setSearchText(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') handleSearchSubmit(); }} />
                    </div>
                    <button onClick={() => setShowSearch(!showSearch)} className={`p-2 hover:bg-white/10 rounded-lg transition ${showSearch ? 'text-white' : 'text-gray-400'}`} title="Buscar">{React.cloneElement(ICONS.search, { className: 'h-5 w-5' })}</button>
                    <div className="relative filter-menu-container">
                        <button onClick={() => setShowFilterMenu(!showFilterMenu)} className={`p-2 hover:bg-white/10 rounded-lg transition ${showFilterMenu || selectedDynamicFilters.length > 0 ? 'text-white' : 'text-gray-400'}`} title="Filtrar y Ordenar">
                            {React.cloneElement(ICONS.filter, { className: 'h-5 w-5' })}
                            {selectedDynamicFilters.length > 0 && (<span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>)}
                        </button>
                        {showFilterMenu && (
                            <div className="absolute right-0 top-full mt-2 w-64 bg-[#1a1a1a] border border-gray-700 rounded-lg shadow-xl z-50 p-3">
                                <div className="mb-3">
                                    <div className="text-xs font-bold text-gray-500 uppercase mb-2 px-1">Ordenar por</div>
                                    <div className="relative">
                                        <select value={filters.sort_by} onChange={(e) => handleSortByChange(e.target.value)} className="w-full bg-gray-800 text-white text-sm rounded-md border-gray-600 focus:outline-none focus:ring-1 focus:ring-red-500 focus:border-red-500 p-2 pr-10 cursor-pointer hover:border-gray-500 transition-colors appearance-none">
                                            <option value="publication_date">Publicación</option>
                                            <option value="download_date">Descarga</option>
                                            <option value="title">Título</option>
                                            <option value="size">Tamaño</option>
                                            <option value="duration">Duración</option>
                                            <option value="id">ID</option>
                                        </select>
                                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none text-gray-400">
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
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
                    <button onClick={toggleSortOrder} className="p-2 hover:bg-white/10 rounded-lg transition text-gray-400 hover:text-white" title={`Ordenar ${filters.sort_order === 'asc' ? 'Ascendente' : 'Descendente'}`}>
                        {filters.sort_order === 'asc' ? React.cloneElement(ICONS.sort_asc, { className: 'h-5 w-5' }) : React.cloneElement(ICONS.sort_desc, { className: 'h-5 w-5' })}
                    </button>
                </div>
            </div>
            <div className="flex flex-col lg:flex-row gap-6">
                {activePlatform && activePlatformSubscriptions.length > 0 && (
                    <aside className="w-full lg:w-64 flex-shrink-0 space-y-4">
                        <div className="bg-[#1a1a1a] rounded-xl p-4 border border-gray-800/50">
                            <SubscriptionList subscriptions={activePlatformSubscriptions} activeSubscriptionId={subscriptionId} onSubscriptionClick={(id) => handleSubscriptionClick(id.toString())} platform={activePlatform} />
                        </div>
                    </aside>
                )}
                <div className="flex-1 min-w-0">
                    {displayedPosts.length > 0 ? (
                        <>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                                {displayedPosts.map(post => (
                                    <PostCard key={post.id} video={post} videos={displayedPosts} isSelected={false} onSelect={() => {}} onEdit={() => {}} isHighlighted={highlightedVideoId === post.id} onRefresh={refreshData} />
                                ))}
                            </div>
                            {loadingMore && (
                                <div className="flex items-center justify-center py-8">
                                    <div className="flex items-center space-x-2 text-gray-400">
                                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-red-500"></div>
                                        <span>Cargando más videos...</span>
                                    </div>
                                </div>
                            )}
                            {!scrollState.hasMore && displayedPosts.length > 0 && (
                                <div className="text-center pt-8 text-gray-400">
                                    <p>Has visto todos los videos disponibles ({displayedPosts.length} videos)</p>
                                </div>
                            )}
                        </>
                    ) : postsLoading ? (
                        <div className="flex items-center justify-center min-h-[400px]">
                            <div className="text-center">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500 mx-auto mb-4"></div>
                                <p className="text-white text-lg">Cargando videos del creador...</p>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center py-16 bg-[#1a1a1a] rounded-xl border border-gray-800/50">
                            <h3 className="text-2xl font-semibold text-white">No se encontraron posts</h3>
                            <p className="text-gray-400 mt-2">No hay contenido que coincida con los filtros seleccionados.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CreatorPage;