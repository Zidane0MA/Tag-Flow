
import React from 'react';

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
}

const PlatformTabs: React.FC<PlatformTabsProps> = ({ tabs, activeTab, onTabClick, isSubTabs = false }) => {
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
        <nav className="flex flex-nowrap items-center gap-2 p-1.5 bg-black/30 rounded-lg overflow-x-auto no-scrollbar">
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
        </nav>
    );
};

export default PlatformTabs;
