

import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Post, EditStatus, ProcessStatus, Difficulty, PostType, SubscriptionType } from '../types';
import { ICONS, getSubscriptionIcon, getListIcon } from '../constants';
import { useRealData } from '../hooks/useRealData';
import { apiService } from '../services/apiService';

interface PostCardProps {
    video: Post; // Renamed to video to avoid large-scale refactor in GalleryPage for now. It is a Post object.
    videos: Post[]; // The full list of (filtered) posts for context
    isSelected: boolean;
    onSelect: (id: string, isSelected: boolean) => void;
    onEdit: (video: Post) => void;
    isHighlighted?: boolean;
}

const getEditStatusIcon = (status: EditStatus) => {
    const iconProps = { className: 'h-4 w-4' };
    let icon;
    let title;
    let colorClass;
    
    switch (status) {
        case EditStatus.PENDING:
            icon = ICONS.status_pending;
            title = 'Pendiente';
            colorClass = 'text-gray-300';
            break;
        case EditStatus.IN_PROGRESS:
            icon = ICONS.status_in_progress;
            title = 'En Progreso';
            colorClass = 'text-yellow-400';
            break;
        case EditStatus.COMPLETED:
            icon = ICONS.status_completed;
            title = 'Completado';
            colorClass = 'text-green-400';
            break;
        case EditStatus.DISCARDED:
            icon = ICONS.close;
            title = 'Descartado';
            colorClass = 'text-red-400';
            break;
        default:
            return null;
    }
    // By wrapping the icon in a fixed-size flex container, we can guarantee centering.
    return (
      <span title={title} className={`${colorClass} flex h-5 w-5 items-center justify-center`}>
        {React.cloneElement(icon, iconProps)}
      </span>
    );
};

const DifficultyIndicator: React.FC<{ difficulty: Difficulty }> = ({ difficulty }) => {
  const colorMap = {
    [Difficulty.LOW]: 'bg-green-500',
    [Difficulty.MEDIUM]: 'bg-yellow-400',
    [Difficulty.HIGH]: 'bg-red-500',
  };
  const levelMap = {
    [Difficulty.LOW]: 1,
    [Difficulty.MEDIUM]: 2,
    [Difficulty.HIGH]: 3,
  };

  const difficultyDisplayMap = {
    [Difficulty.LOW]: 'Bajo',
    [Difficulty.MEDIUM]: 'Medio',
    [Difficulty.HIGH]: 'Alto',
  };

  const level = levelMap[difficulty] || 0;
  
  const dotClass = 'h-1.5 w-1.5 rounded-full'; // Make dots smaller

  return (
    <div title={`Dificultad: ${difficultyDisplayMap[difficulty] || difficulty}`} className="flex items-center gap-0.5">
      {[...Array(3)].map((_, i) => (
        <span
          key={i}
          className={`${dotClass} ${i < level ? colorMap[difficulty] : 'bg-white/30'}`}
        ></span>
      ))}
    </div>
  );
};

const StatusIndicator: React.FC<{ status: ProcessStatus, isAnalyzing: boolean }> = ({ status, isAnalyzing }) => {
    let indicator: { icon: React.ReactElement, className: string, title: string } | null = null;
    
    const currentStatus = isAnalyzing ? ProcessStatus.PROCESSING : status;

    const iconClass = 'h-3 w-3 text-white'; // Made icon smaller

    switch (currentStatus) {
        case ProcessStatus.COMPLETED:
            indicator = {
                icon: React.cloneElement(ICONS.check_plain, { className: iconClass }),
                className: 'bg-green-500/80', // Increased opacity slightly for visibility
                title: 'Estado: Completado'
            };
            break;
        case ProcessStatus.PROCESSING:
            indicator = {
                icon: React.cloneElement(ICONS.spinner, { className: `animate-spin ${iconClass}` }),
                className: 'bg-purple-600/80',
                title: 'Estado: Procesando'
            };
            break;
        case ProcessStatus.PENDING:
            indicator = {
                icon: React.cloneElement(ICONS.exclamation_simple, { className: iconClass }),
                className: 'bg-gray-400/80',
                title: 'Estado: Pendiente'
            };
            break;
        case ProcessStatus.FAILED:
            indicator = {
                icon: React.cloneElement(ICONS.close, { className: iconClass }),
                className: 'bg-red-500/80',
                title: 'Estado: Error'
            };
            break;
        case ProcessStatus.SKIPPED:
            indicator = {
                icon: React.cloneElement(ICONS.close, { className: iconClass }),
                className: 'bg-orange-500/80',
                title: 'Estado: Omitido'
            };
            break;
        default:
            return null;
    }
    
    if (!indicator) return null;

    return (
        <div title={indicator.title} className={`absolute top-2 right-2 z-20 h-5 w-5 rounded-full flex items-center justify-center ${indicator.className}`}>
            {indicator.icon}
        </div>
    );
};



const PostCard: React.FC<PostCardProps> = ({ video: post, videos: posts, isSelected, onSelect, onEdit, isHighlighted = false }) => {
    const { moveToTrash, analyzePost } = useRealData();
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [imageLoaded, setImageLoaded] = useState(false);
    const [imageError, setImageError] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();
    
    const handleAnalyze = async (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsAnalyzing(true);
        await analyzePost(post.id);
        setIsAnalyzing(false);
    }
    
    const handlePlay = (e: React.MouseEvent) => {
        e.stopPropagation();
        const returnPath = location.pathname + location.search;
        // Pass the filtered list of posts and current location info to the player page
        navigate(`/post/${post.id}/player`, { 
            state: { 
                posts,
                returnTo: returnPath,
                currentVideoId: post.id
            } 
        });
    };

    const handleOpenFolder = async (e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            const result = await apiService.openFolder(post.id);
            if (result.success) {
                console.log('Carpeta abierta exitosamente:', result.message);
            } else {
                console.error('Error al abrir carpeta');
            }
        } catch (error) {
            console.error('Error al abrir carpeta:', error);
        }
    };

    const baseClasses = "bg-[#212121] rounded-lg overflow-hidden shadow-lg flex flex-col group text-sm";
    const animationClasses = "transition-all ease-in-out hover:-translate-y-1 hover:shadow-2xl will-change-[transform,box-shadow]";
    
    // Usar una duración más larga para el efecto de resaltado, y una más corta para el hover normal.
    const durationClass = isHighlighted ? 'duration-1000' : 'duration-300';

    const highlightClasses = isHighlighted 
        ? 'ring-4 ring-gray-500 ring-opacity-5 shadow-2xl shadow-gray-500/50 scale-105'
        : '';

    return (
        <div 
            id={`video-card-${post.id}`}
            className={`${baseClasses} ${animationClasses} ${durationClass} ${highlightClasses}`}>
            {/* === Thumbnail Area === */}
            <div className="relative">
                {/* Skeleton placeholder que se mantiene hasta que la imagen carga */}
                {!imageLoaded && !imageError && (
                    <div className="w-full h-[168px] bg-gray-700 animate-pulse flex items-center justify-center">
                        <div className="text-gray-500 text-sm">Cargando...</div>
                    </div>
                )}
                
                {/* Imagen real */}
                <img 
                    src={post.thumbnailUrl} 
                    alt={post.title} 
                    className={`w-full h-[168px] object-cover transition-opacity duration-300 ${
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
                    <div className="w-full h-[168px] bg-gray-800 flex items-center justify-center border-2 border-dashed border-gray-600">
                        <div className="text-center text-gray-500">
                            <div className="text-2xl mb-2">📷</div>
                            <div className="text-xs">Sin thumbnail</div>
                        </div>
                    </div>
                )}
                
                <div className="absolute inset-0 bg-black/50 pointer-events-none z-10"></div>
                
                {/* Selection & Type Indicator (Top Left) */}
                <div className="absolute top-2 left-2 z-40 flex items-center gap-2">
                    <div 
                        onClick={(e) => {
                            e.stopPropagation();
                            onSelect(post.id, !isSelected);
                        }}
                        className={`h-4 w-4 rounded-[3px] border-[1.5px] cursor-pointer transition-all duration-200 flex items-center justify-center ${
                            isSelected 
                                ? 'bg-blue-600 border-blue-600' 
                                : 'bg-gray-800 border-gray-500 hover:border-gray-400'
                        }`}
                    >
                        {isSelected && (
                            <svg className="h-3 w-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                        )}
                    </div>
                    {post.type === PostType.IMAGE && (
                        <div className="flex items-center gap-1.5 bg-black/70 backdrop-blur-sm rounded-full px-2 py-0.5 text-gray-300" title="Publicación de imagen">
                            {React.cloneElement(ICONS.image, {className: "h-4 w-4"})}
                            {post.imageUrls && post.imageUrls.length > 1 && (
                                <span className="text-xs font-bold">{post.imageUrls.length}</span>
                            )}
                        </div>
                    )}
                </div>
                
                {/* Process Status Indicator (Top Right) */}
                <StatusIndicator status={post.processStatus} isAnalyzing={isAnalyzing || post.processStatus === 'Procesando'} />

                {/* Platform Badge (Bottom Right) */}
                <div className="absolute bottom-2 right-2 z-20 flex items-center bg-black/70 backdrop-blur-sm rounded-full px-2.5 py-0.5">
                    <span className="text-xs font-semibold text-white">{post.platform}</span>
                </div>

                {/* Edit Status & Difficulty (Bottom Left) */}
                <div className="absolute bottom-2 left-2 z-20 flex items-center gap-1.5 bg-black/70 backdrop-blur-sm rounded-full px-[0.44rem] py-[0.1rem]">
                    {getEditStatusIcon(post.editStatus)}
                    <div className="h-3 w-px bg-white/20"></div>
                    <DifficultyIndicator difficulty={post.difficulty} />
                </div>
                
                {/* Hover Actions */}
                 <div className="absolute inset-0 flex items-center justify-center gap-2 sm:gap-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none group-hover:pointer-events-auto z-30">
                    <button onClick={handlePlay} title="Reproducir" className="p-3 bg-black/50 backdrop-blur-sm rounded-full text-white hover:bg-red-600 transition-colors">{ICONS.play}</button>
                    <button onClick={(e) => { e.stopPropagation(); onEdit(post); }} title="Editar" className="p-3 bg-black/50 backdrop-blur-sm rounded-full text-white hover:bg-red-600 transition-colors">{ICONS.edit}</button>
                    <button onClick={handleAnalyze} disabled={isAnalyzing || post.processStatus === 'Procesando'} title="Analizar" className="p-3 bg-black/50 backdrop-blur-sm rounded-full text-white hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                       {isAnalyzing || post.processStatus === 'Procesando' ? ICONS.spinner : ICONS.analyze}
                    </button>
                    <button onClick={handleOpenFolder} title="Mostrar Archivo" className="p-3 bg-black/50 backdrop-blur-sm rounded-full text-white hover:bg-red-600 transition-colors">{ICONS.folder}</button>
                    <button onClick={(e) => { e.stopPropagation(); moveToTrash(post.id); }} title="Eliminar" className="p-3 bg-black/50 backdrop-blur-sm rounded-full text-white hover:bg-red-500 transition-colors">{ICONS.delete}</button>
                </div>
            </div>

            {/* === Information Area === */}
            <div className="p-3 flex-grow flex flex-col justify-between space-y-3">
                {/* Title */}
                <div className="flex items-center justify-between gap-2">
                    <h3 className="font-bold text-base text-white leading-tight truncate flex-1" title={post.description || post.title}>
                        {post.description || post.title}
                    </h3>
                    {post.originalUrl && (
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                window.open(post.originalUrl, '_blank', 'noopener,noreferrer');
                            }}
                            className="flex-shrink-0 text-gray-400 hover:text-white transition-colors rounded hover:bg-gray-700/50"
                            title="Abrir enlace original"
                        >
                            {React.cloneElement(ICONS.external_link, { className: 'h-4 w-4' })}
                        </button>
                    )}
                </div>

                {/* Creator and Subscription */}
                <div className="flex justify-between items-start gap-2">
                    <Link to={`/creator/${post.creator}`} onClick={e => e.stopPropagation()} className="flex items-center gap-1.5 text-gray-400 min-w-0 group/creator">
                        {React.cloneElement(ICONS.user, { className: 'h-4 w-4 flex-shrink-0 group-hover/creator:text-white' })}
                        <span className="truncate group-hover/creator:text-white transition-colors" title={post.creator}>{post.creator}</span>
                    </Link>
                    
                    {/* Subscriptions and Lists Icons */}
                    <div className="flex items-center gap-1 flex-shrink-0">
                        {post.subscription && (
                            <Link to={`/subscription/${post.subscription.type}/${post.subscription.id}`} onClick={e => e.stopPropagation()} title={`${post.subscription.name} (${post.subscription.type})`} className="flex items-center gap-1 text-gray-400 hover:text-white transition-colors">
                               {React.cloneElement(getSubscriptionIcon(post.subscription.type), {className: "h-4 w-4 text-blue-400"})}
                               <span className="text-xs font-medium hidden sm:inline truncate max-w-[80px]">{post.subscription.name}</span>
                            </Link>
                        )}
                        
                        {post.lists && post.lists.length > 0 && (
                            <div className="flex items-center gap-0.5" title={`Listas: ${post.lists.map(list => list.name).join(', ')}`}>
                                {post.lists.slice(0, 3).map((list, idx) => (
                                    <div key={idx} className="p-0.5 rounded bg-green-800/30 border border-green-600/50">
                                        {React.cloneElement(getListIcon(list.type), {className: "h-3 w-3 text-green-400"})}
                                    </div>
                                ))}
                                {post.lists.length > 3 && (
                                    <div className="p-0.5 rounded bg-green-800/30 border border-green-600/50">
                                        <span className="text-xs text-green-400 font-bold">+{post.lists.length - 3}</span>
                                    </div>
                                )}
                            </div>
                        )}
                        
                        {/* Fallback icon for videos sin subscription ni lists */}
                        {!post.subscription && (!post.lists || post.lists.length === 0) && (
                            <div className="p-0.5 rounded bg-gray-800/30 border border-gray-600/50" title="Video individual">
                                {React.cloneElement(ICONS.folder, {className: "h-3 w-3 text-gray-400"})}
                            </div>
                        )}
                    </div>
                </div>

                {/* Additional Info */}
                <div className="space-y-1 text-xs text-gray-400">
                    {post.music && (
                        <div className="flex items-center gap-1.5 truncate" title={`${post.music} - ${post.artist}`}>
                            {React.cloneElement(ICONS.music, { className: 'h-4 w-4 flex-shrink-0' })}
                            <span>{post.music} - {post.artist}</span>
                        </div>
                    )}
                    {post.characters && post.characters.length > 0 && (
                        <div className="flex items-center gap-1.5 truncate" title={post.characters.join(', ')}>
                            {React.cloneElement(ICONS.users, { className: 'h-4 w-4 flex-shrink-0' })}
                            <span>{post.characters.join(', ')}</span>
                        </div>
                    )}
                    {post.notes && (
                        <div className="flex items-center gap-1.5 truncate" title={post.notes}>
                            {React.cloneElement(ICONS.notes, { className: 'h-4 w-4 flex-shrink-0' })}
                            <span>{post.notes}</span>
                        </div>
                    )}
                </div>

                {/* Secondary Metadata */}
                <div className="flex justify-between items-center text-xs text-gray-500 pt-2 border-t border-gray-700/50">
                    <div className="flex items-center gap-1" title="Duración">
                        {React.cloneElement(ICONS.clock, { className: 'h-4 w-4' })}
                        <span>{post.type === PostType.VIDEO ? `${(post.duration / 60).toFixed(1)} min` : '---'}</span>
                    </div>
                    <div className="flex items-center gap-1" title="Tamaño">
                        {React.cloneElement(ICONS.file_alt, { className: 'h-4 w-4' })}
                        <span>{post.size.toFixed(1)} MB</span>
                    </div>
                    <div className="flex items-center gap-1" title="Fecha de descarga">
                        {React.cloneElement(ICONS.calendar, { className: 'h-4 w-4' })}
                        <span>{new Date(post.downloadDate).toLocaleDateString()}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PostCard;
