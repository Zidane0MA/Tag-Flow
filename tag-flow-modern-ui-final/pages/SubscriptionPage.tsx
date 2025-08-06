
import React, { useMemo, useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useRealData } from '../hooks/useRealData';
import { SubscriptionType, SubscriptionInfo } from '../types';
import Breadcrumbs, { Crumb } from '../components/Breadcrumbs';
import { ICONS, getSubscriptionIcon, getListIcon } from '../constants';
import PostCard from '../components/VideoCard';
import PlatformTabs, { Tab } from '../components/PlatformTabs';


const SubscriptionPage: React.FC = () => {
    const { type, id, list } = useParams<{ type: SubscriptionType, id: string, list?: string }>();
    const { getSubscriptionInfo, getSubscriptionStats, getPostsBySubscription, getCreatorByName } = useRealData();

    // ⚠️ IMPORTANTE: Mantener todos los hooks en el mismo orden siempre
    const [subscriptionInfo, setSubscriptionInfo] = useState<SubscriptionInfo | undefined>(undefined);
    const [subscriptionStats, setSubscriptionStats] = useState<{total: number, listCounts: {[key: string]: number}} | null>(null);
    const [displayedPosts, setDisplayedPosts] = useState<any[]>([]);
    const [postsLoading, setPostsLoading] = useState(false);
    const [loading, setLoading] = useState(true);

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
            setLoading(false);
            return;
        }

        const loadSubscriptionInfo = async () => {
            setLoading(true);
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
                        setLoading(false);
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
                setLoading(false);
            }
        };

        loadSubscriptionInfo();
    }, [type, id, getSubscriptionInfo, getSubscriptionStats, getCreatorByName]);

    // Cargar posts de la suscripción
    useEffect(() => {
        if (!type || !id) {
            setDisplayedPosts([]);
            return;
        }

        const loadSubscriptionPosts = async () => {
            setPostsLoading(true);
            try {
                // Obtener todos los posts sin límite
                const posts = await getPostsBySubscription(type, id, list);
                setDisplayedPosts(posts);
            } catch (error) {
                console.error('Error loading subscription posts:', error);
                setDisplayedPosts([]);
            } finally {
                setPostsLoading(false);
            }
        };

        loadSubscriptionPosts();
    }, [type, id, list, getPostsBySubscription]);

    // Early returns después de todos los hooks
    if (loading) {
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
             history.pushState(null, '', `#/subscription/${type}/${id}`);
             window.dispatchEvent(new Event('popstate'));
        } else {
             history.pushState(null, '', `#/subscription/${type}/${id}/${subId}`);
             window.dispatchEvent(new Event('popstate'));
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

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                {displayedPosts.map(post => (
                    <PostCard 
                        key={post.id} 
                        video={post}
                        videos={displayedPosts}
                        isSelected={false} 
                        onSelect={() => {}}
                        onEdit={() => {}}
                    />
                ))}
            </div>
             {displayedPosts.length === 0 && (
                 <div className="text-center py-16">
                    <h3 className="text-2xl font-semibold text-white">No se encontraron posts</h3>
                    <p className="text-gray-400 mt-2">No hay contenido que coincida con esta suscripción.</p>
                </div>
             )}

        </div>
    );
};

export default SubscriptionPage;
