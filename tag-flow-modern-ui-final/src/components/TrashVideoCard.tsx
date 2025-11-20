
import React, { useState } from 'react';
import { Post } from '../types';
import { ICONS, getSubscriptionIcon, getCategoryIcon } from '../constants';

interface TrashPostCardProps {
    video: Post; // Renamed to video for less refactoring, but it's a Post
    timeAgo: string;
    isSelected: boolean;
    onSelect: (id: string, isSelected: boolean) => void;
    onRestore: (id: string) => void;
    onDelete: (video: Post) => void;
}

const TrashPostCard: React.FC<TrashPostCardProps> = ({ video: post, timeAgo, isSelected, onSelect, onRestore, onDelete }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [imageLoaded, setImageLoaded] = useState(false);
    const [imageError, setImageError] = useState(false);
    
    const handleRestore = async () => {
        setIsLoading(true);
        // We don't await here to allow the UI to feel instant, 
        // the item will just disappear from the list via the parent's state update.
        onRestore(post.id);
        // No need to setIsLoading(false) because the component will unmount.
    };

    const handleDeleteClick = () => {
        onDelete(post);
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
                {/* Skeleton placeholder que se mantiene hasta que la imagen carga */}
                {!imageLoaded && !imageError && (
                    <div className="w-full h-[168px] bg-gray-700 animate-pulse flex items-center justify-center rounded-t-lg">
                        <div className="text-gray-500 text-sm">Cargando...</div>
                    </div>
                )}
                
                {/* Imagen real */}
                <img 
                    src={post.thumbnailUrl} 
                    alt={post.title} 
                    className={`w-full h-[168px] object-cover rounded-t-lg transition-opacity duration-300 ${
                        imageLoaded ? 'opacity-100' : 'opacity-0 absolute inset-0'
                    }`}
                    onLoad={() => setImageLoaded(true)}
                    onError={() => {
                        setImageError(true);
                        setImageLoaded(true); // Para que se oculte el skeleton
                    }}
                />
                
                {/* Fallback si la imagen falla */}
                {imageError && (
                    <div className="w-full h-[168px] bg-gray-800 flex items-center justify-center border-2 border-dashed border-gray-600 rounded-t-lg">
                        <div className="text-center text-gray-500">
                            <div className="text-2xl mb-2">📷</div>
                            <div className="text-xs">Sin thumbnail</div>
                        </div>
                    </div>
                )}
                
                <div className="absolute inset-0 bg-black/30 group-hover:bg-black/50 transition-colors duration-300 pointer-events-none z-10 rounded-t-lg"></div>
                
                {/* Selection Checkbox (Top Left) */}
                <div className="absolute top-2 left-2 z-40">
                    <div 
                        onClick={(e) => {
                            e.stopPropagation();
                            onSelect(post.id, !isSelected);
                        }}
                        className={`h-4 w-4 rounded-[3px] border-[1.5px] cursor-pointer transition-all duration-200 flex items-center justify-center ${
                            isSelected 
                                ? 'bg-red-600 border-red-600' 
                                : 'bg-gray-800 border-gray-500 hover:border-gray-400'
                        }`}
                    >
                        {isSelected && (
                            <svg className="h-3 w-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                        )}
                    </div>
                </div>
                
                {/* Platform Badge (Bottom Right) */}
                <div className="absolute bottom-2 right-2 z-20">
                     <span className="bg-black/70 text-white !px-2.5 !py-1 text-xs font-semibold rounded-full">
                        {post.platform}
                     </span>
                </div>
                
                {/* Hover Actions */}
                 <div className="absolute inset-0 flex items-center justify-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none group-hover:pointer-events-auto z-30">
                    <button onClick={handleRestore} title="Restaurar" className="p-3 bg-black/50 backdrop-blur-sm rounded-full text-white hover:bg-green-600 transition-colors">{ICONS.restore}</button>
                    <button onClick={handleDeleteClick} title="Eliminar Permanentemente" className="p-3 bg-black/50 backdrop-blur-sm rounded-full text-white hover:bg-red-700 transition-colors">{ICONS.delete}</button>
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
                    
                    {/* Subscription and Lists Info */}
                    <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1">
                            {post.subscription && (
                                <div className="flex items-center gap-1" title={`${post.subscription.name} (${post.subscription.type})`}>
                                    {React.cloneElement(getSubscriptionIcon(post.subscription.type), {className: "h-3 w-3 text-blue-400"})}
                                    <span className="text-xs truncate max-w-[60px]">{post.subscription.name}</span>
                                </div>
                            )}
                        </div>
                        
                        <div className="flex items-center gap-0.5">
                            {post.lists && post.lists.length > 0 ? (
                                <>
                                    {post.lists.slice(0, 2).map((list, idx) => (
                                        <div key={idx} className="p-0.5 rounded bg-green-800/20 border border-green-600/30" title={list.name}>
                                            {React.cloneElement(getCategoryIcon(list.type), {className: "h-2.5 w-2.5 text-green-400"})}
                                        </div>
                                    ))}
                                    {post.lists.length > 2 && (
                                        <div className="p-0.5 rounded bg-green-800/20 border border-green-600/30">
                                            <span className="text-xs text-green-400 font-bold">+{post.lists.length - 2}</span>
                                        </div>
                                    )}
                                </>
                            ) : !post.subscription && (
                                <div className="p-0.5 rounded bg-gray-800/20 border border-gray-600/30" title="Video individual">
                                    {React.cloneElement(ICONS.folder, {className: "h-2.5 w-2.5 text-gray-500"})}
                                </div>
                            )}
                        </div>
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
