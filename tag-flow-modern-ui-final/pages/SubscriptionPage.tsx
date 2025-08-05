
import React, { useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useData } from '../hooks/useMockData';
import { SubscriptionType, SubscriptionInfo } from '../types';
import Breadcrumbs, { Crumb } from '../components/Breadcrumbs';
import { ICONS } from '../constants';
import PostCard from '../components/VideoCard';
import PlatformTabs, { Tab } from '../components/PlatformTabs';

const getSubscriptionIcon = (type: SubscriptionType) => {
    const iconMap: Record<SubscriptionType, React.ReactElement> = {
        'playlist': ICONS.list,
        'music': ICONS.music,
        'hashtag': ICONS.hashtag,
        'saved': ICONS.bookmark,
        'location': ICONS.location_marker,
        'feed': ICONS.reels,
        'liked': ICONS.reels,
        'reels': ICONS.reels,
        'stories': ICONS.stories,
        'highlights': ICONS.highlights,
        'tagged': ICONS.reels,
        'channel': ICONS.user,
        'account': ICONS.user,
        'watch_later': ICONS.clock,
        'favorites': ICONS.bookmark
    };
    return iconMap[type] || ICONS.folder;
};

const SubscriptionPage: React.FC = () => {
    const { type, id, list } = useParams<{ type: SubscriptionType, id: string, list?: string }>();
    const { getSubscriptionInfo, getPostsBySubscription, getCreatorByName } = useData();

    const subscriptionInfo = useMemo<SubscriptionInfo | undefined>(() => {
        if (!type || !id) return undefined;
        // The "account" type is special; its ID is the creator's name.
        if (type === 'account') {
            const creator = getCreatorByName(id);
            if (!creator) return undefined;

            // Find which platform this account subscription is for by looking for a 'feed' or similar.
            // This is a mock data simplification.
            const platformKey = Object.keys(creator.platforms)[0] as any;

            return {
                id: creator.name,
                type: 'account' as SubscriptionType,
                name: creator.displayName,
                platform: platformKey,
                postCount: Object.values(creator.platforms).reduce((acc, p) => acc + (p?.postCount || 0), 0),
                creator: creator.name,
                url: creator.platforms[platformKey]?.url,
            };
        }
        return getSubscriptionInfo(type, id);
    }, [type, id, getSubscriptionInfo, getCreatorByName]);

    const displayedPosts = useMemo(() => {
        if (!type || !id) return [];
        return getPostsBySubscription(type, id, list);
    }, [type, id, list, getPostsBySubscription]);


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
    
    const accountSubscriptionTabs: Tab[] | undefined = useMemo(() => {
        if (type === 'account') {
            const creator = getCreatorByName(id);
            if (!creator || !subscriptionInfo) return undefined;
            const subs = creator.platforms[subscriptionInfo.platform]?.subscriptions || [];
            if (subs.length > 0) {
                 return [
                    { id: 'all', label: 'All', count: subscriptionInfo.postCount, icon: undefined },
                    ...subs.map(sub => ({
                        id: sub.id,
                        label: sub.name,
                        count: getPostsBySubscription(type, id, sub.id).length
                    }))
                ];
            }
        }
        return undefined;
    }, [type, id, getCreatorByName, subscriptionInfo, getPostsBySubscription]);

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
