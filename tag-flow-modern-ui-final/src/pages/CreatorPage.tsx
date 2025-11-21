
import React, { useMemo, useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom';
import { useCursorCreatorData } from '../hooks/useCursorCreatorData';
import { useCursorData } from '../hooks/useCursorData';
import { Creator, Platform, CreatorPlatformInfo, CategoryType } from '../types';
import PostCard from '../components/VideoCard';
import Breadcrumbs, { Crumb } from '../components/Breadcrumbs';
import PlatformTabs, { Tab } from '../components/PlatformTabs';
import SubscriptionList from '../components/SubscriptionList'; // New import
import { ICONS, getSubscriptionIcon, getCategoryIcon } from '../constants';
import { apiService } from '../services/apiService';

const CreatorPage: React.FC = () => {
    const { creatorName, platform: platformParam, subscriptionId } = useParams<{ creatorName: string, platform?: string, subscriptionId?: string }>();
    const location = useLocation();
    
    // State for fetched creator metadata
    const [fetchedCreator, setFetchedCreator] = useState<Creator | null>(null);
    const [creatorMetadataLoading, setCreatorMetadataLoading] = useState<boolean>(true);
    const [creatorMetadataError, setCreatorMetadataError] = useState<string | null>(null);
    
    // Decode URL-encoded platform parameter
    const decodedPlatform = platformParam ? decodeURIComponent(platformParam) : undefined;
    // Cursor pagination for creator videos
    const {
        posts: displayedPosts,
        loading: postsLoading,
        loadingMore,
        loading: videosLoading, // Add this if available in hook, otherwise use postsLoading
        error: videosError,
        scrollState,
        loadCreatorVideos,
        loadMoreVideos,
        refreshData,
        clearData
    } = useCursorCreatorData();
    const navigate = useNavigate();
    
    // Navigation state for video highlighting and scrolling
    const highlightVideoId = location.state?.highlightVideoId;
    const scrollToVideoId = location.state?.scrollToVideoId;
    const [highlightedVideoId, setHighlightedVideoId] = useState<string | null>(highlightVideoId || null);
    const scrolledToVideoRef = useRef(false);
    
    // Search, Filter, Sort State
    const [showSearch, setShowSearch] = useState(false);
    const [searchText, setSearchText] = useState('');
    const [showFilterMenu, setShowFilterMenu] = useState(false);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
    const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
    const searchInputRef = useRef<HTMLInputElement>(null);

    const activePlatform = useMemo(() => {
        return decodedPlatform as Platform | undefined;
    }, [decodedPlatform]);

    // Focus search input when shown
    useEffect(() => {
        if (showSearch && searchInputRef.current) {
            searchInputRef.current.focus();
        }
    }, [showSearch]);

    // Close filter menu when clicking outside
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

    const toggleSort = () => {
        setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    };

    const toggleFilter = (filter: string) => {
        setSelectedFilters(prev => 
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
                return ['videos']; // TikTok usually just has videos (rack)
            default:
                return ['videos'];
        }
    };

    const availableCategories = useMemo(() => getPlatformCategories(activePlatform), [activePlatform]);

    // Fetch creator metadata
    useEffect(() => {
        if (creatorName) {
            setCreatorMetadataLoading(true);
            setCreatorMetadataError(null);
            apiService.getCreator(creatorName)
                .then(data => {
                    setFetchedCreator(data);
                    setCreatorMetadataLoading(false);
                })
                .catch(err => {
                    console.error('Error fetching creator metadata:', err);
                    setCreatorMetadataError('Error al cargar la información del creador.');
                    setCreatorMetadataLoading(false);
                });
        } else {
            setFetchedCreator(null);
            setCreatorMetadataLoading(false);
        }
    }, [creatorName]);

    // Use fetched creator data for display
    const creator = useMemo(() => {
        return fetchedCreator;
    }, [fetchedCreator]);
    
    // Get subscriptions for the active platform
    const activePlatformSubscriptions = useMemo(() => {
        if (!creator || !activePlatform || !creator.platforms) return [];
        const platformInfo = creator.platforms[activePlatform];
        return platformInfo?.subscriptions || [];
    }, [creator, activePlatform]);

    // Load creator videos when params change (with ref to prevent duplicates)
    const lastLoadParamsRef = useRef<string>('');
    useEffect(() => {
        if (creatorName) {
            // If subscriptionId is present, we need to wait for creator data to get the subscription type
            // unless creator data is already loaded or we failed to load it.
            if (subscriptionId && creatorMetadataLoading) {
                return;
            }

            let subType: string | undefined = undefined;
            let effectiveSubId: string | undefined = undefined;

            if (subscriptionId && activePlatformSubscriptions.length > 0) {
                const sub = activePlatformSubscriptions.find(s => s.id.toString() === subscriptionId);
                if (sub) {
                    // If the ID is a number, it's a real DB subscription.
                    // If it's a string, it's a generated "Main Feed" (which means all videos for platform).
                    if (typeof sub.id === 'number') {
                        subType = sub.type;
                        effectiveSubId = subscriptionId;
                    }
                }
            }

            const loadKey = `${creatorName}|${activePlatform || 'all'}|${effectiveSubId || 'all'}|${subType || 'none'}`;
            
            if (lastLoadParamsRef.current !== loadKey) {
                lastLoadParamsRef.current = loadKey;
                loadCreatorVideos(creatorName, activePlatform, effectiveSubId, subType); 
            }
        } else {
            lastLoadParamsRef.current = '';
            clearData();
        }
    }, [creatorName, activePlatform, subscriptionId, loadCreatorVideos, clearData, creatorMetadataLoading, activePlatformSubscriptions]);

    // Handle navigation from video player - scroll to video and highlight
    useEffect(() => {
        if (scrollToVideoId && displayedPosts.length > 0 && !scrolledToVideoRef.current) {
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
    }, [scrollToVideoId, highlightedVideoId, displayedPosts, navigate, location.pathname, location.search]);

    // Infinite scroll implementation using refs to prevent re-renders
    const loadingMoreRef = useRef(false);
    const hasMoreRef = useRef(true);
    const loadMoreVideosRef = useRef(loadMoreVideos);
    const mainContainerRef = useRef<HTMLElement | null>(null);

    // Update refs when state changes
    useEffect(() => {
        loadingMoreRef.current = loadingMore;
        hasMoreRef.current = scrollState.hasMore;
        loadMoreVideosRef.current = loadMoreVideos;
    }, [loadingMore, scrollState.hasMore, loadMoreVideos]);

    // Infinite scroll handler usando refs
    const handleScroll = useCallback(() => {
        if (loadingMoreRef.current || !hasMoreRef.current) return;

        const container = mainContainerRef.current;
        if (!container) return;

        const { scrollTop, scrollHeight, clientHeight } = container;
        const scrollPercentage = scrollTop / (scrollHeight - clientHeight);

        // Load more when 80% scrolled
        if (scrollPercentage > 0.8) {
            loadMoreVideosRef.current();
        }
    }, []); // Sin dependencias!

    // Find and attach scroll listener to main container (solo una vez)
    useEffect(() => {
        // Find the main container (Layout's main element)
        const mainElement = document.querySelector('main');
        mainContainerRef.current = mainElement;

        if (!mainElement) {
            console.warn('Main container not found');
            return;
        }

        mainElement.addEventListener('scroll', handleScroll, { passive: true });
        return () => mainElement.removeEventListener('scroll', handleScroll);
    }, [handleScroll]);
    
    // Simplified total post count based on displayed posts
    const totalPostCount = useMemo(() => {
        return displayedPosts.length;
    }, [displayedPosts.length]);

    // Filter and Sort Posts
    const filteredPosts = useMemo(() => {
        let posts = [...displayedPosts];

        // Filter by search text
        if (searchText) {
            const lowerSearch = searchText.toLowerCase();
            posts = posts.filter(post => 
                post.title.toLowerCase().includes(lowerSearch) || 
                (post.notes && post.notes.toLowerCase().includes(lowerSearch))
            );
        }

        // Filter by selected filters
        if (selectedFilters.length > 0) {
            const categoryFilters = selectedFilters.filter(f => availableCategories.includes(f as CategoryType));
            const normalFilters = selectedFilters.filter(f => !availableCategories.includes(f as CategoryType));

            posts = posts.filter(post => {
                // Check "Normales" filters
                if (normalFilters.includes('Descargados') && !post.downloadDate) return false;
                // if (normalFilters.includes('Pendientes') && post.processStatus !== 'pending') return false; 
                // if (normalFilters.includes('Favoritos') && post.subscription?.type !== 'liked') return false;

                // Check "Dinámicos" filters (categories)
                if (categoryFilters.length > 0) {
                    if (!post.categories || !post.categories.some(c => categoryFilters.includes(c.type))) {
                        return false;
                    }
                }
                
                return true;
            });
        }

        // Sort
        return posts.sort((a, b) => {
            const dateA = new Date(a.publicationDate || a.downloadDate || 0).getTime();
            const dateB = new Date(b.publicationDate || b.downloadDate || 0).getTime();
            
            if (sortOrder === 'asc') {
                return dateA - dateB;
            } else {
                return dateB - dateA;
            }
        });
    }, [displayedPosts, searchText, selectedFilters, sortOrder, availableCategories]);

    // Dynamically generate platform tabs
    const platformTabs: Tab[] = useMemo(() => {
        const tabs: Tab[] = [{ id: 'all', label: 'All', count: creator?.platforms ? (Object.values(creator.platforms) as CreatorPlatformInfo[]).reduce((sum, p) => sum + p.postCount, 0) : totalPostCount }];

        if (creator && creator.platforms) {
            Object.entries(creator.platforms).forEach(([platformId, platformInfo]) => {
                tabs.push({
                    id: platformId,
                    label: platformId.charAt(0).toUpperCase() + platformId.slice(1), // Capitalize platform name
                    count: (platformInfo as CreatorPlatformInfo).postCount
                });
            });
        }
        return tabs.sort((a, b) => { // Sort "All" first, then alphabetically
            if (a.id === 'all') return -1;
            if (b.id === 'all') return 1;
            return a.label.localeCompare(b.label);
        });
    }, [creator, totalPostCount]);

    const handlePlatformTabClick = (platformId: string) => {
        if (platformId === 'all') {
            navigate(`/creator/${encodeURIComponent(creatorName || '')}`);
        }
        else {
            navigate(`/creator/${encodeURIComponent(creatorName || '')}/${encodeURIComponent(platformId)}`);
        }
    };
    
    const handleSubscriptionClick = (subId: string) => {
        navigate(`/creator/${creatorName}/${encodeURIComponent(activePlatform || '')}/${encodeURIComponent(subId)}`);
    }

    // Early returns for loading and errors
    if (creatorMetadataLoading || (postsLoading && !scrollState.initialLoaded)) {
        return (
            <div className="text-center py-16">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
                <p className="text-gray-400 mt-4">Cargando...</p>
            </div>
        );
    }
    
    if (creatorMetadataError) {
        return (
            <div className="text-center py-16">
                <h3 className="text-2xl font-semibold text-white">Error</h3>
                <p className="text-gray-400 mt-2">{creatorMetadataError}</p>
            </div>
        );
    }

    // Only show error if we have no creator AND have finished loading
    if (!creator && !creatorMetadataLoading) { // Check if metadata loading is complete
        return (
            <div className="text-center py-16">
                <h3 className="text-2xl font-semibold text-white">Creador no encontrado</h3>
                <p className="text-gray-400 mt-2">No se pudo encontrar al creador "{creatorName}".</p>
                <Link to="/gallery" className="mt-4 inline-block px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-md transition">
                    Volver a la Galería
                </Link>
            </div>
        );
    }
    
    const breadcrumbs: Crumb[] = [
        { label: 'Galería', href: '/gallery', icon: ICONS.gallery },
        { label: creator?.displayName || creatorName, href: `/creator/${creatorName}`, icon: ICONS.user },
    ];

    if(activePlatform && decodedPlatform) {
        breadcrumbs.push({ label: activePlatform, href: `/creator/${creatorName}/${encodeURIComponent(activePlatform)}`});
        if(subscriptionId) {
            const sub = activePlatformSubscriptions.find(s => s.id.toString() === subscriptionId);
            if(sub) {
                breadcrumbs.push({ label: sub.name, href: `/creator/${creatorName}/${encodeURIComponent(activePlatform)}/${encodeURIComponent(subscriptionId)}`});
            }
        }
    }


    return (
        <div className="space-y-6">
            <header>
                <Breadcrumbs crumbs={breadcrumbs} />
                <div className="flex flex-wrap justify-between items-start gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-white">{creator?.displayName || creatorName}</h1>
                    </div>
                    
                    {/* Display platform links */}
                    <div className="flex items-center gap-3">
                        {creator?.platforms && Object.entries(creator.platforms).map(([platformName, platformInfo]) => (
                            (platformInfo as CreatorPlatformInfo).url && ( // Only render if URL exists for the platform
                                <a key={platformName} href={(platformInfo as CreatorPlatformInfo).url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-2 rounded-lg bg-[#212121]/50 border border-gray-700/50 hover:bg-red-500/20 text-gray-300 hover:text-white transition-colors">
                                    <span className="font-semibold text-sm">{platformName.charAt(0).toUpperCase() + platformName.slice(1)}</span> {/* Capitalize platform name */}
                                    {React.cloneElement(ICONS.external_link, { className: 'h-4 w-4' })}
                                </a>
                            )
                        ))}
                    </div>
                </div>
            </header>
            
            <div className="flex flex-col md:flex-row justify-between items-end gap-4">
                <div className="flex-1 w-full md:w-auto">
                    <PlatformTabs
                        tabs={platformTabs}
                        activeTab={activePlatform || 'all'}
                        onTabClick={handlePlatformTabClick}
                    />
                </div>

                <div className="flex items-center gap-2 bg-black/30 p-1.5 rounded-lg mb-6">
                    {/* Search Input */}
                    <div className={`transition-all duration-300 overflow-hidden flex items-center ${showSearch ? 'w-48 opacity-100 border-b border-gray-500 mr-2' : 'w-0 opacity-0'}`}>
                        <input 
                            ref={searchInputRef}
                            type="text" 
                            className="bg-transparent text-white px-2 py-1 focus:outline-none w-full text-sm"
                            placeholder="Buscar..."
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                        />
                    </div>
                    <button 
                        onClick={() => setShowSearch(!showSearch)} 
                        className={`p-2 hover:bg-white/10 rounded-lg transition ${showSearch ? 'text-white' : 'text-gray-400'}`}
                        title="Buscar"
                    >
                        {React.cloneElement(ICONS.search, { className: 'h-5 w-5' })}
                    </button>

                    {/* Filter Button & Popover */}
                    <div className="relative filter-menu-container">
                        <button 
                            onClick={() => setShowFilterMenu(!showFilterMenu)} 
                            className={`p-2 hover:bg-white/10 rounded-lg transition ${showFilterMenu || selectedFilters.length > 0 ? 'text-white' : 'text-gray-400'}`}
                            title="Filtrar"
                        >
                            {React.cloneElement(ICONS.filter, { className: 'h-5 w-5' })}
                            {selectedFilters.length > 0 && (
                                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                            )}
                        </button>
                        
                        {showFilterMenu && (
                            <div className="absolute right-0 top-full mt-2 w-64 bg-[#1a1a1a] border border-gray-700 rounded-lg shadow-xl z-50 p-3">
                                <div className="mb-3">
                                    <div className="text-xs font-bold text-gray-500 uppercase mb-2 px-1">Normales</div>
                                    <div className="space-y-1">
                                        {['Descargados', 'Pendientes', 'Favoritos'].map(filter => (
                                            <label key={filter} className="flex items-center gap-2 px-2 py-1.5 hover:bg-white/5 rounded cursor-pointer">
                                                <input 
                                                    type="checkbox" 
                                                    checked={selectedFilters.includes(filter)}
                                                    onChange={() => toggleFilter(filter)}
                                                    className="rounded border-gray-600 bg-gray-800 text-red-600 focus:ring-red-500"
                                                />
                                                <span className="text-sm text-gray-300">{filter}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                                
                                <div className="border-t border-gray-700 my-2"></div>
                                
                                <div>
                                    <div className="text-xs font-bold text-gray-500 uppercase mb-2 px-1">Dinámicos</div>
                                    <div className="space-y-1">
                                        {availableCategories.map(category => (
                                            <label key={category} className="flex items-center gap-2 px-2 py-1.5 hover:bg-white/5 rounded cursor-pointer">
                                                <input 
                                                    type="checkbox" 
                                                    checked={selectedFilters.includes(category)}
                                                    onChange={() => toggleFilter(category)}
                                                    className="rounded border-gray-600 bg-gray-800 text-red-600 focus:ring-red-500"
                                                />
                                                <span className="flex items-center gap-2 text-sm text-gray-300">
                                                    {getCategoryIcon(category, activePlatform)}
                                                    <span className="capitalize">{category}</span>
                                                </span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Sort Button */}
                    <button 
                        onClick={toggleSort} 
                        className="p-2 hover:bg-white/10 rounded-lg transition text-gray-400 hover:text-white"
                        title={`Ordenar ${sortOrder === 'asc' ? 'Ascendente' : 'Descendente'}`}
                    >
                        {sortOrder === 'asc' 
                            ? React.cloneElement(ICONS.sort_asc, { className: 'h-5 w-5' })
                            : React.cloneElement(ICONS.sort_desc, { className: 'h-5 w-5' })
                        }
                    </button>
                </div>
            </div>

            <div className="flex flex-col lg:flex-row gap-6">
                {/* Sidebar for Subscriptions - Only show if we have subscriptions and a platform is selected */}
                {activePlatform && activePlatformSubscriptions.length > 0 && (
                    <aside className="w-full lg:w-64 flex-shrink-0 space-y-4">
                        <div className="bg-[#1a1a1a] rounded-xl p-4 border border-gray-800/50">
                            <SubscriptionList 
                                subscriptions={activePlatformSubscriptions}
                                activeSubscriptionId={subscriptionId}
                                onSubscriptionClick={(id) => handleSubscriptionClick(id.toString())}
                                platform={activePlatform}
                            />
                        </div>
                    </aside>
                )}

                {/* Main Content Grid */}
                <div className="flex-1 min-w-0">
                    {filteredPosts.length > 0 ? (
                        <>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                                {filteredPosts.map(post => (
                                    <PostCard
                                        key={post.id}
                                        video={post}
                                        videos={filteredPosts}
                                        isSelected={false}
                                        onSelect={() => {}}
                                        onEdit={() => {}}
                                        isHighlighted={highlightedVideoId === post.id}
                                        onRefresh={refreshData}
                                    />
                                ))}
                            </div>
                            
                            {/* Indicador de carga para más contenido */}
                            {loadingMore && (
                                <div className="flex items-center justify-center py-8">
                                    <div className="flex items-center space-x-2 text-gray-400">
                                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-red-500"></div>
                                        <span>Cargando más videos...</span>
                                    </div>
                                </div>
                            )}

                            {/* Mensaje de final de contenido */}
                            {!scrollState.hasMore && filteredPosts.length > 0 && (
                                <div className="text-center py-8 text-gray-400">
                                    <p>Has visto todos los videos disponibles ({filteredPosts.length} videos)</p>
                                </div>
                            )}
                        </>
                    ) : postsLoading && !scrollState.initialLoaded ? (
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
