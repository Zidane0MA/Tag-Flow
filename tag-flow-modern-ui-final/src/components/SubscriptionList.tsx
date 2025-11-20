import React from 'react';
import { Subscription, Platform } from '../types';
import { getSubscriptionIcon } from '../constants';

interface SubscriptionListProps {
    subscriptions: Subscription[];
    activeSubscriptionId?: string;
    onSubscriptionClick: (id: string) => void;
    platform?: Platform;
}

const SubscriptionList: React.FC<SubscriptionListProps> = ({ 
    subscriptions, 
    activeSubscriptionId, 
    onSubscriptionClick,
    platform 
}) => {
    if (!subscriptions || subscriptions.length === 0) {
        return null;
    }

    return (
        <div className="flex flex-col gap-1 w-full">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-3">
                Playlists & Feeds
            </h3>
            {subscriptions.map((sub) => {
                const isActive = activeSubscriptionId === sub.id;
                const icon = getSubscriptionIcon(sub.type, platform);
                
                return (
                    <button
                        key={sub.id}
                        onClick={() => onSubscriptionClick(sub.id)}
                        className={`
                            flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 w-full text-left group
                            ${isActive 
                                ? 'bg-red-600 text-white shadow-md shadow-red-900/20' 
                                : 'text-gray-400 hover:bg-[#2a2a2a] hover:text-white'
                            }
                        `}
                    >
                        <div className={`
                            flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-md
                            ${isActive ? 'bg-white/20' : 'bg-[#1a1a1a] group-hover:bg-[#333]'}
                        `}>
                            {React.cloneElement(icon as React.ReactElement, { 
                                className: `h-4 w-4 ${isActive ? 'text-white' : 'text-gray-400 group-hover:text-white'}` 
                            })}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                            <span className="truncate block">{sub.name}</span>
                        </div>
                    </button>
                );
            })}
        </div>
    );
};

export default SubscriptionList;
