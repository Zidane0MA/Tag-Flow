
import React, { useMemo, useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useRealData } from '../hooks/useRealData';
import { Platform } from '../types';
import PostCard from '../components/VideoCard';
import Breadcrumbs, { Crumb } from '../components/Breadcrumbs';
import PlatformTabs, { Tab } from '../components/PlatformTabs';
import { ICONS, getSubscriptionIcon, getListIcon } from '../constants';

const CreatorPage: React.FC = () => {
    const { creatorName, platform: platformParam, subscriptionId } = useParams<{ creatorName: string, platform?: string, subscriptionId?: string }>();
    
    // Decode URL-encoded platform parameter
    const decodedPlatform = platformParam ? decodeURIComponent(platformParam) : undefined;
    const { getCreatorByName, getPostsByCreator, loading } = useRealData();
    const navigate = useNavigate();
    
    const [displayedPosts, setDisplayedPosts] = useState<any[]>([]);
    const [postsLoading, setPostsLoading] = useState(false);

    const creator = useMemo(() => creatorName ? getCreatorByName(creatorName) : undefined, [creatorName, getCreatorByName]);
    
    const activePlatform = useMemo(() => {
        // If no platform param, we're showing "All"
        if (!decodedPlatform) {
            return undefined;
        }
        // If platform param exists and is valid, use it
        if (creator && creator.platforms[decodedPlatform as Platform]) {
            return decodedPlatform as Platform;
        }
        // If platform param is invalid, default to first platform
        return creator ? Object.keys(creator.platforms)[0] as Platform : undefined;
    }, [creator, decodedPlatform]);

    // Cargar posts del creador de forma asíncrona
    useEffect(() => {
        if (!creatorName) {
            setDisplayedPosts([]);
            return;
        }

        const loadCreatorPosts = async () => {
            setPostsLoading(true);
            try {
                const posts = await getPostsByCreator(creatorName, activePlatform, subscriptionId);
                setDisplayedPosts(posts);
            } catch (error) {
                console.error('Error loading creator posts:', error);
                setDisplayedPosts([]);
            } finally {
                setPostsLoading(false);
            }
        };

        loadCreatorPosts();
    }, [creatorName, activePlatform, subscriptionId, getPostsByCreator]);
    
    // Calculate total post count based on current view
    const totalPostCount = useMemo(() => {
        if (activePlatform === undefined) {
            // When showing "All", use sum of all platform counts or displayed posts length
            if (creator) {
                return Object.values(creator.platforms).reduce((acc, p) => acc + (p?.postCount || 0), 0);
            }
            return displayedPosts.length;
        } else {
            // For specific platforms, use displayed posts count to ensure accuracy
            return displayedPosts.length;
        }
    }, [creator, displayedPosts, activePlatform]);

    const subscriptionTabs: Tab[] | undefined = useMemo(() => {
        if (activePlatform && creator?.platforms[activePlatform]) {
            const platformSubscriptions = creator.platforms[activePlatform]?.subscriptions || [];
            if (platformSubscriptions.length > 1) { // Only show sub-tabs if there's more than one list
                return [
                    { id: 'sub-all', label: 'All', count: creator.platforms[activePlatform]?.postCount || 0, icon: undefined },
                    ...platformSubscriptions.map((sub, index) => ({
                        id: `sub-${index}-${sub.type}-${sub.name.replace(/[^a-zA-Z0-9]/g, '-')}`, // ID único
                        label: sub.name,
                        count: 0, // Por ahora 0, se podría calcular después de forma asíncrona
                        subscriptionId: sub.id || sub.name // Mantener ID original para navegación
                    }))
                ];
            }
        }
        return undefined;
    }, [creator, activePlatform]);

    // Early returns after all hooks
    if (loading || postsLoading) {
        return (
            <div className="text-center py-16">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
                <p className="text-gray-400 mt-4">Cargando...</p>
            </div>
        );
    }

    if (!creator || !creatorName) {
        return (
            <div className="text-center py-16">
                <h3 className="text-2xl font-semibold text-white">Creador no encontrado</h3>
                <p className="text-gray-400 mt-2">No se pudo encontrar al creador solicitado.</p>
                <Link to="/gallery" className="mt-4 inline-block px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-md transition">
                    Volver a la Galería
                </Link>
            </div>
        );
    }
    
    const platformTabs: Tab[] = [
        { id: 'all', label: 'All', count: totalPostCount },
        ...Object.entries(creator.platforms).map(([p, data], index) => ({
            id: `platform-${index}-${p.replace(/[^a-zA-Z0-9]/g, '-')}`, // Generar ID único y seguro
            label: p,
            count: data?.postCount || 0,
            platformName: p // Mantener el nombre original de plataforma para navegación
        }))
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
        { label: creator.displayName, href: `/creator/${creatorName}`, icon: ICONS.user },
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
                        <h1 className="text-3xl font-bold text-white">{creator.displayName}</h1>
                        <p className="text-gray-400 mt-1">{totalPostCount} videos • {Object.keys(creator.platforms).length} plataformas</p>
                    </div>
                    
                    {/* Creator and Subscription Icons Section */}
                    <div className="flex flex-col items-end gap-4">
                        {/* Platform Links */}
                        <div className="flex items-center gap-2">
                            <span className="text-gray-400 text-sm">Plataformas:</span>
                            {Object.entries(creator.platforms).map(([p, data]) => data?.url && (
                                 <a key={p} href={data.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 p-1.5 rounded-md bg-[#212121]/50 border border-gray-700/50 hover:bg-red-500/20 text-gray-300 hover:text-white transition-colors" title={`Ver en ${p}`}>
                                    <span className="text-xs font-medium">{p}</span>
                                    {React.cloneElement(ICONS.external_link, { className: 'h-3 w-3' })}
                                 </a>
                            ))}
                        </div>
                        
                        {/* Subscriptions and Lists */}
                        <div className="flex flex-col gap-2">
                            {Object.entries(creator.platforms).map(([platform, data]) => {
                                if (!data?.subscriptions || data.subscriptions.length === 0) return null;
                                
                                return (
                                    <div key={platform} className="flex items-center gap-2">
                                        <span className="text-gray-400 text-xs">{platform}:</span>
                                        <div className="flex items-center gap-1">
                                            {data.subscriptions.map((subscription, idx) => {
                                                const subscriptionIcon = getSubscriptionIcon(subscription.type || 'account');
                                                return (
                                                    <div key={idx} className="flex items-center gap-1 p-1 rounded bg-gray-800/50 border border-gray-600/50" title={`${subscription.name} (${subscription.type})`}>
                                                        {React.cloneElement(subscriptionIcon, { className: 'h-3 w-3 text-blue-400' })}
                                                        <span className="text-xs text-gray-300 max-w-16 truncate">{subscription.name}</span>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        
                        {/* Available Lists */}
                        {activePlatform && creator.platforms[activePlatform]?.lists && (
                            <div className="flex items-center gap-2">
                                <span className="text-gray-400 text-xs">Listas:</span>
                                <div className="flex items-center gap-1">
                                    {creator.platforms[activePlatform]?.lists?.map((listType, idx) => {
                                        const listIcon = getListIcon(listType);
                                        return (
                                            <div key={idx} className="p-1 rounded bg-green-800/30 border border-green-600/50" title={`Lista: ${listType}`}>
                                                {React.cloneElement(listIcon, { className: 'h-3 w-3 text-green-400' })}
                                            </div>
                                        );
                                    })}
                                </div>
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
            
            {postsLoading ? (
                <div className="flex items-center justify-center min-h-[400px]">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500 mx-auto mb-4"></div>
                        <p className="text-white text-lg">Cargando videos del creador...</p>
                    </div>
                </div>
            ) : (
                <>
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
                            <p className="text-gray-400 mt-2">No hay contenido que coincida con los filtros seleccionados.</p>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default CreatorPage;
