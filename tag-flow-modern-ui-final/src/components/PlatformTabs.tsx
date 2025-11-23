import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Subscription } from '../types';
import { getSubscriptionIcon } from '../constants';

export interface Tab {
    id: string;
    label: string;
    count: number;
    icon?: React.ReactElement;
}

interface PlatformTabsProps {
    tabs: Tab[];
    activeTab: string;
    onTabClick: (id: string) => void;
    isSubTabs?: boolean;
    subscriptions?: Subscription[];
    activeSubscriptionId?: string;
}

const PlatformTabs: React.FC<PlatformTabsProps> = ({ 
    tabs, 
    activeTab, 
    onTabClick, 
    isSubTabs = false,
    subscriptions = [],
    activeSubscriptionId
}) => {
    const [showSubscriptionMenu, setShowSubscriptionMenu] = useState(false);
    const [dropdownPos, setDropdownPos] = useState<{top: number, left: number} | null>(null);
    const menuButtonRef = useRef<HTMLButtonElement>(null);
    const menuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            // Check if click is outside both the button and the dropdown
            const target = event.target as Node;
            const isOutsideButton = menuButtonRef.current && !menuButtonRef.current.contains(target);
            const isOutsideMenu = menuRef.current && !menuRef.current.contains(target);
            
            if (isOutsideButton && isOutsideMenu) {
                setShowSubscriptionMenu(false);
            }
        };

        const handleScroll = () => {
             if (showSubscriptionMenu) setShowSubscriptionMenu(false);
        };

        document.addEventListener('mousedown', handleClickOutside);
        window.addEventListener('scroll', handleScroll, { capture: true }); // Close on any scroll
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
            window.removeEventListener('scroll', handleScroll, { capture: true });
        };
    }, [showSubscriptionMenu]);

    const toggleMenu = () => {
        if (showSubscriptionMenu) {
            setShowSubscriptionMenu(false);
        } else {
            if (menuButtonRef.current) {
                const rect = menuButtonRef.current.getBoundingClientRect();
                // Position dropdown below the button, aligned to the right if possible, or left
                // We'll align to the left of the button by default, but check for overflow
                let left = rect.left;
                const dropdownWidth = 224; // w-56 = 14rem = 224px
                if (left + dropdownWidth > window.innerWidth) {
                    left = window.innerWidth - dropdownWidth - 10;
                }
                setDropdownPos({ top: rect.bottom + 8, left });
            }
            setShowSubscriptionMenu(true);
        }
    };

    const baseClasses = 'flex items-center gap-2 whitespace-nowrap py-2 px-3 text-sm font-semibold rounded-md transition-colors duration-200';
    const activeClasses = 'bg-red-600 text-white';
    const inactiveClasses = 'text-gray-300 hover:bg-gray-700/50 hover:text-white';

    const subTabBaseClasses = 'pb-2 px-1 text-sm font-medium border-b-2';
    const subTabActiveClasses = 'border-red-500 text-white';
    const subTabInactiveClasses = 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-500';

    if (isSubTabs) {
        return (
             <div className="border-b border-gray-700/80">
                <nav className="-mb-px flex space-x-6 overflow-x-auto no-scrollbar" aria-label="Sub-tabs">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => onTabClick(tab.id)}
                            className={`${subTabBaseClasses} ${activeTab === tab.id ? subTabActiveClasses : subTabInactiveClasses}`}
                        >
                            {tab.label}
                            <span className={`ml-2 text-xs py-0.5 px-1.5 rounded-full ${activeTab === tab.id ? 'bg-white/20' : 'bg-gray-700'}`}>
                                {tab.count}
                            </span>
                        </button>
                    ))}
                </nav>
            </div>
        )
    }

    return (
        <div className="flex items-center gap-2 w-full">
            <nav className="flex flex-nowrap items-center gap-2 p-1.5 bg-black/30 rounded-lg overflow-x-auto no-scrollbar min-w-0 flex-1">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => onTabClick(tab.id)}
                        className={`${baseClasses} ${activeTab === tab.id ? activeClasses : inactiveClasses}`}
                    >
                        {tab.icon && React.cloneElement(tab.icon, { ...tab.icon.props, className: "h-5 w-5" })}
                        <span>{tab.label}</span>
                        <span className="text-xs font-normal opacity-80">{tab.count}</span>
                    </button>
                ))}

                {subscriptions.length > 0 && (
                    <>
                        <div className="w-px h-6 bg-gray-700 mx-1 flex-shrink-0"></div>
                        <button 
                            ref={menuButtonRef}
                            onClick={toggleMenu}
                            className={`p-2 rounded-lg transition-colors flex-shrink-0 ${showSubscriptionMenu || activeSubscriptionId ? 'bg-red-600 text-white' : 'bg-[#212121]/50 text-gray-400 hover:text-white hover:bg-[#212121]'}`}
                            title="Suscripciones"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                            </svg>
                        </button>
                    </>
                )}
            </nav>

            {showSubscriptionMenu && dropdownPos && (
                <div 
                    ref={menuRef}
                    className="fixed z-50 w-56 bg-[#1a1a1a] border border-gray-700 rounded-lg shadow-xl p-3"
                    style={{ top: dropdownPos.top, left: dropdownPos.left }}
                >
                    <div>
                        <div className="text-xs font-bold text-gray-500 uppercase mb-2 px-1">Suscripciones</div>
                        <div className="max-h-64 overflow-y-auto space-y-1">
                            {subscriptions.map(sub => (
                                <Link 
                                    key={sub.id} 
                                    to={`/subscription/${sub.type}/${sub.id}`}
                                    className={`block px-2 py-2 hover:bg-white/5 rounded-md transition-colors ${activeSubscriptionId === sub.id.toString() ? 'bg-white/10' : ''}`}
                                    onClick={() => setShowSubscriptionMenu(false)}
                                >
                                    <div className="flex items-center gap-2">
                                        {React.cloneElement(getSubscriptionIcon(sub.type), { className: 'h-4 w-4 text-red-500' })}
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs font-medium text-gray-200 truncate">{sub.name}</p>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PlatformTabs;
