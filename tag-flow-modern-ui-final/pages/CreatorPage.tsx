
import React, { useMemo, useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom';
import { useCursorCreatorData } from '../hooks/useCursorCreatorData';
import { useCursorData } from '../hooks/useCursorData';
import { Platform, CreatorPlatformInfo } from '../types';
import PostCard from '../components/VideoCard';
import Breadcrumbs, { Crumb } from '../components/Breadcrumbs';
import PlatformTabs, { Tab } from '../components/PlatformTabs';
import { ICONS, getSubscriptionIcon, getCategoryIcon } from '../constants';

const CreatorPage: React.FC = () => {
    const { creatorName, platform: platformParam, subscriptionId } = useParams<{ creatorName: string, platform?: string, subscriptionId?: string }>();
    const location = useLocation();
    
    // Decode URL-encoded platform parameter
    const decodedPlatform = platformParam ? decodeURIComponent(platformParam) : undefined;
    // Cursor pagination for creator videos
    const {
        posts: displayedPosts,
        loading: postsLoading,
        loadingMore,
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
    
    
    const activePlatform = useMemo(() => {
        return decodedPlatform as Platform | undefined;
    }, [decodedPlatform]);

    // Temporary: Creator metadata will be minimal for now
    // TODO: Add proper creator metadata endpoint or integrate with cursor system
    const creator = useMemo(() => {
        if (!creatorName) return undefined;
        // Basic creator object for display purposes
        return {
            displayName: creatorName,
            platforms: {} // Empty for now, will be populated later
        };
    }, [creatorName]);
    

    // Load creator videos when params change (with ref to prevent duplicates)
    const lastLoadParamsRef = useRef<string>('');
    useEffect(() => {
        if (creatorName) {
            const loadKey = `${creatorName}|${activePlatform || 'all'}`;
            if (lastLoadParamsRef.current !== loadKey) {
                lastLoadParamsRef.current = loadKey;
                loadCreatorVideos(creatorName, activePlatform);
            }
        } else {
            lastLoadParamsRef.current = '';
            clearData();
        }
    }, [creatorName, activePlatform, loadCreatorVideos, clearData]);

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

    // Simplified: No subscription tabs for now
    const subscriptionTabs: Tab[] | undefined = undefined;

    // Early returns after all hooks
    if (postsLoading && !scrollState.initialLoaded) {
        return (
            <div className="text-center py-16">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
                <p className="text-gray-400 mt-4">Cargando...</p>
            </div>
        );
    }

    // Show "creator not found" only in specific cases
    if (!creatorName) {
        return (
            <div className="text-center py-16">
                <h3 className="text-2xl font-semibold text-white">Creador no encontrado</h3>
                <p className="text-gray-400 mt-2">No se especificó un creador válido.</p>
                <Link to="/gallery" className="mt-4 inline-block px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-md transition">
                    Volver a la Galería
                </Link>
            </div>
        );
    }
    
    // Only show error if we have no creator AND have finished loading with no results
    if (!creator && scrollState.initialLoaded && displayedPosts.length === 0) {
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
    
    // Simplified platform tabs
    const platformTabs: Tab[] = [
        { id: 'all', label: 'All', count: totalPostCount }
        // TODO: Add platform-specific tabs when metadata is available
    ];

    const handlePlatformTabClick = (platformId: string) => {
        if (platformId === 'all') {
            navigate(`/creator/${creatorName}`);
        } else {
            // Encontrar el nombre real de la plataforma usando el ID
            const platformTab = platformTabs.find(tab => tab.id === platformId);
            const platformName = (platformTab as any)?.platformName || platformId;
            // URL encode platform name to handle special characters like slashes
            navigate(`/creator/${creatorName}/${encodeURIComponent(platformName)}`);
        }
    };
    
    const handleSubscriptionTabClick = (subId: string) => {
        if (subId === 'sub-all') {
             navigate(`/creator/${creatorName}/${encodeURIComponent(activePlatform || '')}`);
        } else {
            // Encontrar el ID real de la suscripción usando el ID del tab
            const subTab = subscriptionTabs?.find(tab => tab.id === subId);
            const realSubId = (subTab as any)?.subscriptionId || subId;
            navigate(`/creator/${creatorName}/${encodeURIComponent(activePlatform || '')}/${encodeURIComponent(realSubId)}`);
        }
    }
    
    const breadcrumbs: Crumb[] = [
        { label: 'Galería', href: '/gallery', icon: ICONS.gallery },
        { label: creator?.displayName || creatorName, href: `/creator/${creatorName}`, icon: ICONS.user },
    ];

    if(activePlatform && decodedPlatform) {
        breadcrumbs.push({ label: activePlatform, href: `/creator/${creatorName}/${encodeURIComponent(activePlatform)}`});
        if(subscriptionId && subscriptionTabs) {
            const sub = subscriptionTabs.find(s => s.id === subscriptionId);
            if(sub) {
                breadcrumbs.push({ label: sub.label, href: `/creator/${creatorName}/${encodeURIComponent(activePlatform)}/${encodeURIComponent(subscriptionId)}`});
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
                        <p className="text-gray-400 mt-1">{totalPostCount} videos{activePlatform ? ` • ${activePlatform}` : ' • Todas las plataformas'}</p>
                    </div>
                    
                    {/* Simplified metadata section */}
                    <div className="flex flex-col items-end gap-4">
                        {activePlatform && (
                            <div className="flex items-center gap-2">
                                <span className="text-gray-400 text-sm">Plataforma:</span>
                                <span className="text-white text-sm">{activePlatform}</span>
                            </div>
                        )}
                    </div>
                </div>
            </header>
            
            <PlatformTabs
                tabs={platformTabs}
                activeTab={(() => {
                    if (!decodedPlatform) return 'all';
                    // Encontrar el tab ID que corresponde a la plataforma actual
                    const platformTab = platformTabs.find(tab => (tab as any).platformName === decodedPlatform);
                    return platformTab?.id || 'all';
                })()}
                onTabClick={handlePlatformTabClick}
            />

            {subscriptionTabs && (
                 <PlatformTabs
                    tabs={subscriptionTabs}
                    activeTab={(() => {
                        if (!subscriptionId) return 'sub-all';
                        // Encontrar el tab ID que corresponde a la suscripción actual
                        const subTab = subscriptionTabs.find(tab => (tab as any).subscriptionId === subscriptionId);
                        return subTab?.id || 'sub-all';
                    })()}
                    onTabClick={handleSubscriptionTabClick}
                    isSubTabs
                />
            )}
            
            {/* EXACTAMENTE IGUAL QUE GALLERY - NUNCA OCULTAR EL GRID */}
            <div>
                {displayedPosts.length > 0 ? (
                    <>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                            {displayedPosts.map(post => (
                                <PostCard
                                    key={post.id}
                                    video={post}
                                    videos={displayedPosts} // IGUAL QUE GALLERY - pasar array completo
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
                        {!scrollState.hasMore && displayedPosts.length > 0 && (
                            <div className="text-center py-8 text-gray-400">
                                <p>Has visto todos los videos disponibles del creador ({displayedPosts.length} videos)</p>
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
                    <div className="text-center py-16">
                        <h3 className="text-2xl font-semibold text-white">No se encontraron posts</h3>
                        <p className="text-gray-400 mt-2">No hay contenido que coincida con los filtros seleccionados.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CreatorPage;
