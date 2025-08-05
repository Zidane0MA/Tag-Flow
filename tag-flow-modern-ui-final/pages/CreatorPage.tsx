
import React, { useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useData } from '../hooks/useMockData';
import { Platform } from '../types';
import PostCard from '../components/VideoCard';
import Breadcrumbs, { Crumb } from '../components/Breadcrumbs';
import PlatformTabs, { Tab } from '../components/PlatformTabs';
import { ICONS } from '../constants';

const CreatorPage: React.FC = () => {
    const { creatorName, platform: platformParam, subscriptionId } = useParams<{ creatorName: string, platform?: Platform, subscriptionId?: string }>();
    const { getCreatorByName, getPostsByCreator } = useData();
    const navigate = useNavigate();

    const creator = useMemo(() => creatorName ? getCreatorByName(creatorName) : undefined, [creatorName, getCreatorByName]);
    
    const activePlatform = useMemo(() => {
        if (platformParam && creator && creator.platforms[platformParam]) {
            return platformParam;
        }
        // Default to the first platform if none is selected or the selected one is invalid
        return creator ? Object.keys(creator.platforms)[0] as Platform : undefined;
    }, [creator, platformParam]);

    const displayedPosts = useMemo(() => {
        if (!creatorName) return [];
        return getPostsByCreator(creatorName, activePlatform, subscriptionId);
    }, [creatorName, activePlatform, subscriptionId, getPostsByCreator]);
    
    const totalPostCount = useMemo(() => creator ? Object.values(creator.platforms).reduce((acc, p) => acc + (p?.postCount || 0), 0) : 0, [creator]);


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
        ...Object.entries(creator.platforms).map(([p, data]) => ({
            id: p,
            label: p,
            count: data?.postCount || 0
        }))
    ];

    const handlePlatformTabClick = (platformId: string) => {
        if (platformId === 'all') {
            navigate(`/creator/${creatorName}`);
        } else {
            navigate(`/creator/${creatorName}/${platformId}`);
        }
    };
    
    const subscriptionTabs: Tab[] | undefined = useMemo(() => {
        if (activePlatform && creator.platforms[activePlatform]) {
            const platformSubscriptions = creator.platforms[activePlatform]?.subscriptions || [];
            if (platformSubscriptions.length > 1) { // Only show sub-tabs if there's more than one list
                return [
                    { id: 'all', label: 'All', count: creator.platforms[activePlatform]?.postCount || 0, icon: undefined },
                    ...platformSubscriptions.map(sub => ({
                        id: sub.id,
                        label: sub.name,
                        count: getPostsByCreator(creatorName, activePlatform, sub.id).length
                    }))
                ];
            }
        }
        return undefined;
    }, [creator, activePlatform, getPostsByCreator, creatorName]);

    const handleSubscriptionTabClick = (subId: string) => {
        if (subId === 'all') {
             navigate(`/creator/${creatorName}/${activePlatform}`);
        } else {
            navigate(`/creator/${creatorName}/${activePlatform}/${subId}`);
        }
    }
    
    const breadcrumbs: Crumb[] = [
        { label: 'Galería', href: '/gallery', icon: ICONS.gallery },
        { label: creator.displayName, href: `/creator/${creatorName}`, icon: ICONS.user },
    ];

    if(activePlatform && platformParam) {
        breadcrumbs.push({ label: activePlatform, href: `/creator/${creatorName}/${activePlatform}`});
        if(subscriptionId && subscriptionTabs) {
            const sub = subscriptionTabs.find(s => s.id === subscriptionId);
            if(sub) {
                breadcrumbs.push({ label: sub.label, href: `/creator/${creatorName}/${activePlatform}/${subscriptionId}`});
            }
        }
    }


    return (
        <div className="space-y-6">
            <header>
                <Breadcrumbs crumbs={breadcrumbs} />
                <div className="flex flex-wrap justify-between items-center gap-4">
                    <h1 className="text-3xl font-bold text-white">{creator.displayName}</h1>
                    <div className="flex items-center gap-3">
                        {Object.entries(creator.platforms).map(([p, data]) => data?.url && (
                             <a key={p} href={data.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-2 rounded-lg bg-[#212121]/50 border border-gray-700/50 hover:bg-red-500/20 text-gray-300 hover:text-white transition-colors">
                                <span className="font-semibold text-sm">{p}</span>
                                {React.cloneElement(ICONS.external_link, { className: 'h-4 w-4' })}
                             </a>
                        ))}
                    </div>
                </div>
            </header>
            
            <PlatformTabs
                tabs={platformTabs}
                activeTab={platformParam || 'all'}
                onTabClick={handlePlatformTabClick}
            />

            {subscriptionTabs && (
                 <PlatformTabs
                    tabs={subscriptionTabs}
                    activeTab={subscriptionId || 'all'}
                    onTabClick={handleSubscriptionTabClick}
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
                    <p className="text-gray-400 mt-2">No hay contenido que coincida con los filtros seleccionados.</p>
                </div>
             )}
        </div>
    );
};

export default CreatorPage;
