
import React, { useMemo, useState, useEffect, useCallback, useRef } from 'react';
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import { useCursorSubscriptionData } from '../hooks/useCursorSubscriptionData';
import { useCursorData } from '../hooks/useCursorData';
import { apiService } from '../services/apiService';
import { SubscriptionType, SubscriptionInfo, CreatorPlatformInfo } from '../types';
import Breadcrumbs, { Crumb } from '../components/Breadcrumbs';
import { ICONS, getSubscriptionIcon, getCategoryIcon } from '../constants';
import PostCard from '../components/VideoCard';
import PlatformTabs, { Tab } from '../components/PlatformTabs';


const SubscriptionPage: React.FC = () => {
    const { type, id, list } = useParams<{ type: SubscriptionType, id: string, list?: string }>();
    const navigate = useNavigate();
    const location = useLocation();
    
    // Cursor pagination for subscription videos
    const {
        posts: displayedPosts,
        loading: postsLoading,
        loadingMore,
        error: videosError,
        scrollState,
        loadSubscriptionVideos,
        loadMoreVideos,
        refreshData,
        clearData
    } = useCursorSubscriptionData();

    // 🚀 Cursor implementation: Get creators from cursor data
    const { creators } = useCursorData();

    // Helper functions (migrated from useRealData)
    const getCreatorByName = useCallback((name: string) => {
        return creators.find(c => c.name === name);
    }, [creators]);

    const getSubscriptionInfo = useCallback(async (type: SubscriptionType, id: string) => {
        try {
            return await apiService.getSubscriptionInfo(type, parseInt(id, 10));
        } catch (error) {
            console.error('Error getting subscription info:', error);
            return undefined;
        }
    }, []);

    // Navigation state for video highlighting and scrolling
    const highlightVideoId = location.state?.highlightVideoId;
    const scrollToVideoId = location.state?.scrollToVideoId;
    const [highlightedVideoId, setHighlightedVideoId] = useState<string | null>(highlightVideoId || null);
    const scrolledToVideoRef = useRef(false);

    // ⚠️ IMPORTANTE: Mantener todos los hooks en el mismo orden siempre
    const [subscriptionInfo, setSubscriptionInfo] = useState<SubscriptionInfo | undefined>(undefined);
    const [subscriptionInfoLoading, setSubscriptionInfoLoading] = useState(true);
    

    // Simplified total post count based on displayed posts
    const totalPostCount = useMemo(() => {
        return displayedPosts.length;
    }, [displayedPosts.length]);

    // Simplified: No dynamic subscription tabs for now (would require additional endpoints)
    const accountSubscriptionTabs: Tab[] | undefined = useMemo(() => {
        if (type === 'account' && subscriptionInfo) {
            return [
                { id: 'all', label: 'Todos', count: totalPostCount, icon: ICONS.gallery }
            ];
        }
        return undefined;
    }, [type, subscriptionInfo, totalPostCount]);

    // Cargar información de la suscripción
    useEffect(() => {
        if (!type || !id) {
            setSubscriptionInfoLoading(false);
            return;
        }

        const loadSubscriptionInfo = async () => {
            setSubscriptionInfoLoading(true);
            try {
                // The "account" type is special; its ID is the creator's name.
                if (type === 'account') {
                    const creator = getCreatorByName(id);
                    if (creator) {
                        const platformKey = Object.keys(creator.platforms)[0] as any;
                        setSubscriptionInfo({
                            id: creator.name, // Use name as ID for account type
                            type: 'account' as SubscriptionType,
                            name: creator.displayName,
                            platform: platformKey,
                            postCount: Object.values(creator.platforms).reduce((acc: number, p) => acc + ((p as CreatorPlatformInfo)?.postCount || 0), 0),
                            creator: creator.name,
                            url: creator.platforms[platformKey]?.url,
                        });
                        setSubscriptionInfoLoading(false);
                        return;
                    }
                }
                
                // Para otros tipos, usar el backend
                const info = await getSubscriptionInfo(type, id);
                setSubscriptionInfo(info);
            } catch (error) {
                console.error('Error loading subscription info:', error);
                setSubscriptionInfo(undefined);
            } finally {
                setSubscriptionInfoLoading(false);
            }
        };

        loadSubscriptionInfo();
    }, [type, id, getSubscriptionInfo, getCreatorByName]);

    // Load subscription videos when params change (with ref to prevent duplicates)
    const lastLoadParamsRef = useRef<string>('');
    useEffect(() => {
        if (type && id) {
            const loadKey = `${type}|${id}|${list || 'all'}`;
            if (lastLoadParamsRef.current !== loadKey) {
                lastLoadParamsRef.current = loadKey;
                // Convert string ID to number for API call
                const numericId = parseInt(id, 10);
                if (!isNaN(numericId)) {
                    loadSubscriptionVideos(type, numericId);
                }
            }
        } else {
            lastLoadParamsRef.current = '';
            clearData();
        }
    }, [type, id, list, loadSubscriptionVideos, clearData]);

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

    // Infinite scroll implementation using refs to prevent re-renders (IGUAL QUE GALLERY)
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

    // Early returns después de todos los hooks
    if (postsLoading && !scrollState.initialLoaded) {
        return (
            <div className="text-center py-16">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
                <p className="text-gray-400 mt-4">Cargando suscripción...</p>
            </div>
        );
    }

    if (!subscriptionInfo || !type) {
        return <div className="text-center py-16 text-white">Suscripción no encontrada.</div>;
    }

    const breadcrumbs: Crumb[] = [
        { label: 'Galería', href: '/gallery', icon: ICONS.gallery },
        { label: subscriptionInfo.name, href: `/subscription/${type}/${id}`, icon: getSubscriptionIcon(type) }
    ];
    
    if(list) {
        // Find list name
        const creator = subscriptionInfo.creator ? getCreatorByName(subscriptionInfo.creator) : undefined;
        const subList = creator?.platforms[subscriptionInfo.platform]?.subscriptions.find(s => s.id === list);
        if (subList) {
            breadcrumbs.push({ label: subList.name, href: `/subscription/${type}/${id}/${list}` });
        }
    }

    const handleSubTabClick = (subId: string) => {
        if (subId === 'all') {
            navigate(`/subscription/${type}/${id}`);
        } else {
            navigate(`/subscription/${type}/${id}/${subId}`);
        }
    };


    return (
        <div className="space-y-6">
            <header>
                <Breadcrumbs crumbs={breadcrumbs} />
                <div className="flex flex-wrap justify-between items-center gap-4">
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        {React.cloneElement(getSubscriptionIcon(type), {className: "h-8 w-8"})}
                        {subscriptionInfo.name}
                    </h1>
                     <div className="flex items-center gap-3">
                         <div className="p-2 rounded-lg bg-[#212121]/50 border border-gray-700/50 text-gray-300 text-sm">
                            <span className="font-semibold text-white">{subscriptionInfo.postCount}</span> posts
                         </div>
                         {subscriptionInfo.creatorCount && (
                             <div className="p-2 rounded-lg bg-[#212121]/50 border border-gray-700/50 text-gray-300 text-sm">
                                de <span className="font-semibold text-white">{subscriptionInfo.creatorCount}</span> creadores
                             </div>
                         )}
                         {subscriptionInfo.url && (
                             <a href={subscriptionInfo.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-2 rounded-lg bg-[#212121]/50 border border-gray-700/50 hover:bg-red-500/20 text-gray-300 hover:text-white transition-colors">
                                <span className="font-semibold text-sm">{subscriptionInfo.platform}</span>
                                {React.cloneElement(ICONS.external_link, { className: 'h-4 w-4' })}
                             </a>
                         )}
                     </div>
                </div>
            </header>
            
            {accountSubscriptionTabs && (
                <PlatformTabs
                    tabs={accountSubscriptionTabs}
                    activeTab={list || 'all'}
                    onTabClick={handleSubTabClick}
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
                            <div className="text-center pt-8 text-gray-400">
                                <p>Has visto todos los videos disponibles de la suscripción ({displayedPosts.length} videos)</p>
                            </div>
                        )}
                    </>
                ) : postsLoading && !scrollState.initialLoaded ? (
                    <div className="flex items-center justify-center min-h-[400px]">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500 mx-auto mb-4"></div>
                            <p className="text-white text-lg">Cargando videos de la suscripción...</p>
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-16">
                        <h3 className="text-2xl font-semibold text-white">No se encontraron posts</h3>
                        <p className="text-gray-400 mt-2">No hay contenido que coincida con esta suscripción.</p>
                    </div>
                )}
            </div>

        </div>
    );
};

export default SubscriptionPage;
