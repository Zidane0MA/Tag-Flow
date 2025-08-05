
import React, { useState } from 'react';
import { Post } from '../types';
import { ICONS } from '../constants';

interface TrashPostCardProps {
    video: Post; // Renamed to video for less refactoring, but it's a Post
    timeAgo: string;
    isSelected: boolean;
    onSelect: (id: string, isSelected: boolean) => void;
    onRestore: (id: string) => void;
    onDelete: (id: string) => void;
}

const TrashPostCard: React.FC<TrashPostCardProps> = ({ video: post, timeAgo, isSelected, onSelect, onRestore, onDelete }) => {
    const [isLoading, setIsLoading] = useState(false);
    
    const handleAction = async (action: (id: string) => void) => {
        setIsLoading(true);
        // We don't await here to allow the UI to feel instant, 
        // the item will just disappear from the list via the parent's state update.
        action(post.id);
        // No need to setIsLoading(false) because the component will unmount.
    };

    return (
        <div className={`bg-[#212121] rounded-lg shadow-lg flex flex-col group text-sm transition-all duration-300 ease-in-out hover:shadow-2xl will-change-[transform,box-shadow] relative ${isSelected ? 'ring-2 ring-red-500' : 'ring-2 ring-transparent'}`}>
            {isLoading && (
                 <div className="absolute inset-0 bg-black/70 z-50 flex items-center justify-center rounded-lg">
                     {ICONS.spinner}
                 </div>
            )}
            
            {/* === Thumbnail Area === */}
            <div className="relative">
                <img src={post.thumbnailUrl} alt={post.title} className="w-full h-40 object-cover rounded-t-lg" />
                <div className="absolute inset-0 bg-black/30 group-hover:bg-black/50 transition-colors duration-300 pointer-events-none z-10 rounded-t-lg"></div>
                
                {/* Selection Checkbox (Top Left) */}
                <div className="absolute top-2 left-2 z-40">
                    <input 
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => onSelect(post.id, e.target.checked)}
                        className="h-5 w-5 rounded text-red-600 bg-gray-900 border-gray-500 focus:ring-red-500 cursor-pointer"
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                
                {/* Platform Badge (Bottom Right) */}
                <div className="absolute bottom-2 right-2 z-20">
                     <span className="bg-black/70 text-white !px-2.5 !py-1 text-xs font-semibold rounded-full">
                        {post.platform}
                     </span>
                </div>
                
                {/* Hover Actions */}
                 <div className="absolute inset-0 flex items-center justify-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none group-hover:pointer-events-auto z-30">
                    <button onClick={() => handleAction(onRestore)} title="Restaurar" className="p-3 bg-black/50 backdrop-blur-sm rounded-full text-white hover:bg-green-600 transition-colors">{ICONS.restore}</button>
                    <button onClick={() => handleAction(onDelete)} title="Eliminar Permanentemente" className="p-3 bg-black/50 backdrop-blur-sm rounded-full text-white hover:bg-red-700 transition-colors">{ICONS.delete}</button>
                </div>
            </div>

            {/* === Information Area === */}
            <div className="p-4 flex-grow flex flex-col justify-between space-y-3">
                <h3 className="font-bold text-base text-white leading-tight truncate" title={post.title}>
                    {post.title}
                </h3>
                <div className="space-y-1 text-xs text-gray-400">
                     <div className="flex items-center gap-1.5 truncate" title={post.creator}>
                        {React.cloneElement(ICONS.user, { className: 'h-4 w-4 flex-shrink-0' })}
                        <span>{post.creator}</span>
                    </div>
                    <div className="flex items-center gap-1.5" title={`Eliminado ${new Date(post.deletedAt!).toLocaleString()}`}>
                        {React.cloneElement(ICONS.trash, { className: 'h-4 w-4 flex-shrink-0' })}
                        <span>Eliminado {timeAgo}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TrashPostCard;
