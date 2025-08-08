
import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useRealData } from '../hooks/useRealData';
import { SubscriptionType, SubscriptionInfo } from '../types';
import Breadcrumbs, { Crumb } from '../components/Breadcrumbs';
import { ICONS, getSubscriptionIcon, getListIcon } from '../constants';
import PostCard from '../components/VideoCard';
import PlatformTabs, { Tab } from '../components/PlatformTabs';
import useInfiniteScroll from '../hooks/useInfiniteScroll';


const SubscriptionPage: React.FC = () => {
    const { type, id, list } = useParams<{ type: SubscriptionType, id: string, list?: string }>();
    const navigate = useNavigate();
    
    const { 
        getSubscriptionInfo, 
        getSubscriptionStats, 
        getPostsBySubscription, 
        getCreatorByName,
        loadSubscriptionPosts,
        loadMoreSubscriptionPosts,
        getSubscriptionScrollData
    } = useRealData();

    // ⚠️ IMPORTANTE: Mantener todos los hooks en el mismo orden siempre
    const [subscriptionInfo, setSubscriptionInfo] = useState<SubscriptionInfo | undefined>(undefined);
    const [subscriptionStats, setSubscriptionStats] = useState<{total: number, listCounts: {[key: string]: number}} | null>(null);
    const [subscriptionInfoLoading, setSubscriptionInfoLoading] = useState(true);
    
    // Usar infinite scroll data en lugar de estado local
    const scrollData = getSubscriptionScrollData(type || 'account', id || '', list);
    const displayedPosts = scrollData.posts;
    const postsLoading = scrollData.loading;
    

    // Generar subtabs dinámicos por plataforma para suscripciones tipo account
    const accountSubscriptionTabs: Tab[] | undefined = useMemo(() => {
        if (type === 'account' && subscriptionInfo && subscriptionStats) {
            // Definir subtabs por plataforma
            const platformSubtabs: { [key: string]: Array<{id: string, label: string, icon?: React.ReactElement}> } = {
                'tiktok': [
                    { id: 'feed', label: 'Videos', icon: getListIcon('feed') },
                    { id: 'liked', label: 'Liked', icon: getListIcon('liked') },
                    { id: 'favorites', label: 'Favorites', icon: getListIcon('favorites') }
                ],
                'youtube': [
                    { id: 'feed', label: 'Videos', icon: getListIcon('feed') },
                    { id: 'shorts', label: 'Shorts', icon: getListIcon('reels') },
                    { id: 'playlist', label: 'Playlists', icon: getListIcon('playlist') }
                ],
                'instagram': [
                    { id: 'feed', label: 'Posts', icon: getListIcon('feed') },
                    { id: 'reels', label: 'Reels', icon: getListIcon('reels') },
                    { id: 'stories', label: 'Stories', icon: getListIcon('stories') },
                    { id: 'highlights', label: 'Highlights', icon: getListIcon('highlights') },
                    { id: 'tagged', label: 'Tagged', icon: getListIcon('tagged') }
                ]
            };
            
            const subtabs = platformSubtabs[subscriptionInfo.platform] || [
                { id: 'feed', label: 'Feed', icon: getListIcon('feed') }
            ];
            
            return [
                { id: 'all', label: 'Todos', count: subscriptionStats.total, icon: ICONS.gallery },
                ...subtabs.map(subtab => ({
                    id: subtab.id,
                    label: subtab.label,
                    count: subscriptionStats.listCounts[subtab.id] || 0, // Usar conteos reales
                    icon: subtab.icon
                }))
            ];
        }
        return undefined;
    }, [type, subscriptionInfo, subscriptionStats]);

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
                            id: creator.name,
                            type: 'account' as SubscriptionType,
                            name: creator.displayName,
                            platform: platformKey,
                            postCount: Object.values(creator.platforms).reduce((acc, p) => acc + (p?.postCount || 0), 0),
                            creator: creator.name,
                            url: creator.platforms[platformKey]?.url,
                        });
                        setSubscriptionInfoLoading(false);
                        return;
                    }
                }
                
                // Para otros tipos, usar el backend
                const [info, stats] = await Promise.all([
                    getSubscriptionInfo(type, id),
                    getSubscriptionStats(type, id)
                ]);
                setSubscriptionInfo(info);
                setSubscriptionStats(stats);
            } catch (error) {
                console.error('Error loading subscription info:', error);
                setSubscriptionInfo(undefined);
            } finally {
                setSubscriptionInfoLoading(false);
            }
        };

        loadSubscriptionInfo();
    }, [type, id, getSubscriptionInfo, getSubscriptionStats, getCreatorByName]);

    useEffect(() => {
        if (type && id) {
            loadSubscriptionPosts(type, id, list);
        }
    }, [type, id, list]);

    // Infinite scroll callback - SIMPLIFICADO COMO GALLERY
    const infiniteScrollCallback = useCallback(() => {
        if (type && id && !postsLoading && scrollData.hasMore) {
            loadMoreSubscriptionPosts(type, id, list);
        }
    }, [postsLoading, scrollData.hasMore, loadMoreSubscriptionPosts]); // Dependencias mínimas

    // Simplificar enabled - solo usar condiciones estables como Gallery
    const infiniteScrollEnabled = scrollData.hasMore && displayedPosts.length > 0;
    
    // Memoizar las opciones para evitar recreaciones constantes
    const infiniteScrollOptions = useMemo(() => ({
        threshold: 400, // Mismo threshold que Gallery
        enabled: infiniteScrollEnabled
    }), [infiniteScrollEnabled]);

    // Hook para scroll infinito
    useInfiniteScroll(infiniteScrollCallback, infiniteScrollOptions);

    // Early returns después de todos los hooks
    if (postsLoading && !scrollData.initialLoaded) {
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

            {postsLoading ? (
                <div className="flex items-center justify-center min-h-[400px]">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500 mx-auto mb-4"></div>
                        <p className="text-white text-lg">Cargando videos de la suscripción...</p>
                    </div>
                </div>
            ) : (
                <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                        {displayedPosts.map(post => (
                            <PostCard 
                                key={post.id} 
                                video={post}
                                videos={[]} // Empty array to avoid re-renders - player navigation handled differently
                                isSelected={false} 
                                onSelect={() => {}}
                                onEdit={() => {}}
                            />
                        ))}
                    </div>
                    
                    {/* Indicador de carga para más contenido */}
                    {postsLoading && (
                        <div className="flex items-center justify-center py-8">
                            <div className="flex items-center space-x-2 text-gray-400">
                                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-red-500"></div>
                                <span>Cargando más videos...</span>
                            </div>
                        </div>
                    )}
                    
                    {/* Mensaje de final de contenido */}
                    {!scrollData.hasMore && displayedPosts.length > 0 && (
                        <div className="text-center py-8 text-gray-400">
                            <p>Has visto todos los videos disponibles de la suscripción ({displayedPosts.length} videos)</p>
                        </div>
                    )}
                    
                    {displayedPosts.length === 0 && !postsLoading && scrollData.initialLoaded && (
                        <div className="text-center py-16">
                            <h3 className="text-2xl font-semibold text-white">No se encontraron posts</h3>
                            <p className="text-gray-400 mt-2">No hay contenido que coincida con esta suscripción.</p>
                        </div>
                    )}
                </>
            )}

        </div>
    );
};

export default SubscriptionPage;
