
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useRealData } from '../hooks/useRealData';
import { Post, Difficulty, PostType } from '../types';
import { ICONS } from '../constants';

// Utilidad para detectar dispositivos móviles
const isMobileDevice = (): boolean => {
  return /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
         (window.innerWidth <= 768);
};


const ImageCarousel: React.FC<{ post: Post, isActive: boolean }> = ({ post, isActive }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const imageUrls = post.imageUrls && post.imageUrls.length > 0 ? post.imageUrls : [post.postUrl];
  
  useEffect(() => {
    if (isActive) {
      setCurrentIndex(0);
    }
  }, [isActive]);

  const handleNext = () => setCurrentIndex(i => Math.min(i + 1, imageUrls.length - 1));
  const handlePrev = () => setCurrentIndex(i => Math.max(i - 1, 0));

  return (
    <div className="w-full h-full relative">
      <div className="w-full h-full relative">
        {imageUrls.map((url, index) => (
          <img
            key={url}
            src={url}
            className={`absolute inset-0 w-full h-full object-contain transition-opacity duration-300 ease-in-out ${currentIndex === index ? 'opacity-100' : 'opacity-0'}`}
            alt={`Image ${index + 1} for post ${post.title}`}
          />
        ))}
      </div>

      <div className="absolute inset-0 flex">
        <div className="w-1/2 h-full cursor-pointer" onClick={handlePrev}></div>
        <div className="w-1/2 h-full cursor-pointer" onClick={handleNext}></div>
      </div>
      
      {imageUrls.length > 1 && (
          <div className="absolute top-6 right-6 bg-black/50 text-white text-sm font-semibold px-3 py-1.5 rounded-full z-20">
              {currentIndex + 1} / {imageUrls.length}
          </div>
      )}

      {imageUrls.length > 1 && (
          <div className="absolute bottom-20 left-1/2 -translate-x-1/2 flex gap-2 z-20">
              {imageUrls.map((_, index) => (
                  <div key={index} className={`h-2 rounded-full transition-all duration-300 ${currentIndex === index ? 'w-6 bg-white' : 'w-2 bg-white/50'}`}></div>
              ))}
          </div>
      )}
    </div>
  );
};


const ReelItem: React.FC<{
  post: Post;
  isActive: boolean;
  onDelete: (id: string) => void;
  onDifficultyChange: (id: string, difficulty: Difficulty) => void;
  shouldPreload?: boolean;
}> = ({ post, isActive, onDelete, onDifficultyChange, shouldPreload = false }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showDifficultyOptions, setShowDifficultyOptions] = useState(false);
  const [titleExpanded, setTitleExpanded] = useState(false);
  const [videoError, setVideoError] = useState(false);
  const [videoLoading, setVideoLoading] = useState(true);

  // Detectar dispositivo móvil una sola vez
  const isMobile = isMobileDevice();

  // Efecto principal para manejo de video
  useEffect(() => {
    const videoElement = videoRef.current;
    if (!videoElement || post.type !== PostType.VIDEO) return;

    const handleLoadStart = () => setVideoLoading(true);
    const handleCanPlay = () => setVideoLoading(false);
    const handleError = () => {
      setVideoError(true);
      setVideoLoading(false);
    };
    
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    // Agregar event listeners
    videoElement.addEventListener('loadstart', handleLoadStart);
    videoElement.addEventListener('canplay', handleCanPlay);
    videoElement.addEventListener('error', handleError);
    videoElement.addEventListener('play', handlePlay);
    videoElement.addEventListener('pause', handlePause);

    // Manejo de reproducción basado en visibilidad
    if (isActive) {
      const playPromise = videoElement.play();
      if (playPromise !== undefined) {
        playPromise.catch(error => {
          console.log("Autoplay prevented:", error);
          setIsPlaying(false);
        });
      }
    } else {
      videoElement.pause();
      // No resetear currentTime para mejor UX
    }

    return () => {
      videoElement.removeEventListener('loadstart', handleLoadStart);
      videoElement.removeEventListener('canplay', handleCanPlay);
      videoElement.removeEventListener('error', handleError);
      videoElement.removeEventListener('play', handlePlay);
      videoElement.removeEventListener('pause', handlePause);
    };
  }, [isActive, post.type]);

  const handleVideoClick = () => {
    const videoElement = videoRef.current;
    if (!videoElement || post.type !== PostType.VIDEO) return;
    
    if (isPlaying) {
      videoElement.pause();
    } else {
      videoElement.play().catch(() => {
        console.log("Play failed");
      });
    }
  };
  
  const handleDifficultyClick = (d: Difficulty) => {
      onDifficultyChange(post.id, d);
      setShowDifficultyOptions(false);
  }

  return (
    <div id={`post-item-${post.id}`} className="video-item h-screen w-screen relative snap-start flex-shrink-0 flex items-center justify-center bg-black">
      {post.type === PostType.VIDEO ? (
        <>
          <video
            ref={videoRef}
            src={post.postUrl}
            loop
            autoPlay
            muted
            playsInline
            preload={shouldPreload || isActive ? "metadata" : "none"}
            controls={false}
            disablePictureInPicture
            className="w-full h-full object-cover"
            onClick={handleVideoClick}
            style={{ 
              backgroundColor: '#000',
              objectFit: 'cover'
            }}
            // Propiedades específicas de móvil
            {...(isMobile && {
              'webkit-playsinline': 'true',
              'x5-video-player-type': 'h5',
              'x5-video-orientation': 'portraint'
            })}
          />
          
          {/* Indicador de carga */}
          {videoLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/80">
              <div className="flex items-center gap-2 text-white">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm">Cargando video...</span>
              </div>
            </div>
          )}

          {/* Indicador de error */}
          {videoError && (
            <div className="absolute inset-0 flex items-center justify-center bg-black">
              <div className="text-center text-white">
                <div className="text-4xl mb-2">⚠️</div>
                <div className="text-sm">Error al cargar video</div>
              </div>
            </div>
          )}

          {/* Botón de play superpuesto */}
          {!videoLoading && !videoError && !isPlaying && isActive && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="bg-black/50 p-4 rounded-full">
                {React.cloneElement(ICONS.play, { className: 'h-12 w-12 text-white' })}
              </div>
            </div>
          )}
        </>
      ) : (
        <ImageCarousel post={post} isActive={isActive} />
      )}
      
      <div className="absolute bottom-0 left-0 right-0 p-4 pb-6 text-white bg-gradient-to-t from-black/70 to-transparent z-10">
        <h3 className="font-bold text-lg">@{post.creator}</h3>
        <div className="mt-1">
          <p className={`text-sm transition-all duration-300 ${
            titleExpanded ? 'line-clamp-none' : 'line-clamp-2'
          }`}>
            {post.title}
          </p>
          {post.title && post.title.length > 80 && (
            <button 
              onClick={() => setTitleExpanded(!titleExpanded)}
              className="text-xs text-gray-300 hover:text-white mt-1 transition-colors"
            >
              {titleExpanded ? 'menos' : 'más'}
            </button>
          )}
        </div>
        {post.music && (
          <div className="flex items-center gap-2 mt-2 text-sm">
             {React.cloneElement(ICONS.music, { className: 'h-4 w-4 flex-shrink-0' })}
             <span className="truncate">{post.music} - {post.artist}</span>
          </div>
        )}
      </div>

      <div className="absolute right-3 bottom-24 md:bottom-32 flex flex-col items-center gap-6 text-white z-10">
        <div className="relative flex flex-col items-center gap-1">
            <button onClick={() => setShowDifficultyOptions(s => !s)} className="bg-black/40 rounded-full p-3 hover:bg-black/60 transition-colors">
                {React.cloneElement(ICONS.wrench, { className: 'h-7 w-7' })}
            </button>
            <span className="text-xs font-bold">{post.difficulty}</span>

            {showDifficultyOptions && (
                <div className="absolute right-full bottom-0 mr-4 bg-black/60 backdrop-blur-sm rounded-lg p-2 flex flex-col gap-1 w-28">
                    {Object.values(Difficulty).map(d => (
                        <button key={d} onClick={() => handleDifficultyClick(d)} className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${post.difficulty === d ? 'bg-red-600 text-white' : 'hover:bg-white/20'}`}>
                            {d}
                        </button>
                    ))}
                </div>
            )}
        </div>
        <div className="flex flex-col items-center gap-1">
            <button onClick={() => onDelete(post.id)} className="bg-black/40 rounded-full p-3 hover:bg-red-500/80 transition-colors">
                {React.cloneElement(ICONS.delete, { className: 'h-7 w-7' })}
            </button>
            <span className="text-xs font-bold">Delete</span>
        </div>
      </div>
    </div>
  );
};


const PostPlayerPage: React.FC = () => {
    const { postId } = useParams<{ postId: string }>();
    const navigate = useNavigate();
    const location = useLocation();
    const { posts: allPosts, updatePost, moveToTrash } = useRealData();

    const [postsToDisplay, setPostsToDisplay] = useState<Post[]>(location.state?.posts || allPosts);
    const [activePostId, setActivePostId] = useState(postId);
    const [preloadedVideos, setPreloadedVideos] = useState<Set<string>>(new Set());
    
    // Get return path and original video from navigation state
    const returnPath = location.state?.returnTo || '/gallery';
    const originalVideoId = location.state?.currentVideoId || postId;
    
    
    const containerRef = useRef<HTMLDivElement>(null);
    const observerRef = useRef<IntersectionObserver | null>(null);
    const initialScrollDone = useRef(false);
    const isScrollingRef = useRef(false);
    const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const lastScrollTimeRef = useRef(0);
    
    const activePostIdRef = useRef(activePostId);
    useEffect(() => {
        activePostIdRef.current = activePostId;
    }, [activePostId]);


    useEffect(() => {
        setPostsToDisplay(location.state?.posts || allPosts);
    }, [location.state, allPosts]);
    
    useEffect(() => {
        if (postsToDisplay.length > 0 && postId && !initialScrollDone.current) {
            const postElement = document.getElementById(`post-item-${postId}`);
            if (postElement) {
                postElement.scrollIntoView({ behavior: 'auto' });
                initialScrollDone.current = true;
            }
        }
    }, [postsToDisplay, postId]);

    useEffect(() => {
      const handleIntersect = (entries: IntersectionObserverEntry[]) => {
        let mostVisibleEntry = entries.reduce((prev, current) => {
          return (current.intersectionRatio > prev.intersectionRatio) ? current : prev;
        }, entries[0]);

        if (mostVisibleEntry && mostVisibleEntry.isIntersecting) {
          const newPostId = mostVisibleEntry.target.id.replace('post-item-', '');
          if(newPostId && newPostId !== activePostIdRef.current) {
              setActivePostId(newPostId);
              navigate(`/post/${newPostId}/player`, { 
                  replace: true, 
                  state: { 
                      posts: postsToDisplay,
                      returnTo: returnPath,
                      currentVideoId: originalVideoId
                  } 
              });
          }
        }
      };

      // Observer más simple y confiable
      observerRef.current = new IntersectionObserver(handleIntersect, { 
        root: null, // Usar viewport completo
        threshold: [0.1, 0.5, 0.9], // Múltiples thresholds para mejor detección
        rootMargin: '-10% 0px -10% 0px' // Pequeño margen para center detection
      });
      
      const currentObserver = observerRef.current;
      const postItems = document.querySelectorAll('.video-item');
      if (postItems.length > 0) {
        postItems.forEach(item => currentObserver.observe(item));
      }
      return () => {
        if (currentObserver) {
          postItems.forEach(item => currentObserver.unobserve(item));
        }
      };
    }, [postsToDisplay, navigate]);

    // Simplificar el scroll - usar solo el intersection observer nativo
    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        // Solo manejar scroll nativo del CSS snap-scroll
        // Eliminar eventos personalizados que causan conflictos
        
        return () => {
            // Limpiar timeout al desmontar
            if (scrollTimeoutRef.current) {
                clearTimeout(scrollTimeoutRef.current);
                scrollTimeoutRef.current = null;
            }
        };
    }, [postsToDisplay]);


    const handleDelete = (idToDelete: string) => {
        const currentIndex = postsToDisplay.findIndex(p => p.id === idToDelete);
        if (currentIndex === -1) return;

        moveToTrash(idToDelete);
        const nextPosts = postsToDisplay.filter(p => p.id !== idToDelete);
        
        if (nextPosts.length > 0) {
            const nextIndex = Math.min(currentIndex, nextPosts.length - 1);
            const nextPostId = nextPosts[nextIndex].id;
            setActivePostId(nextPostId);
            navigate(`/post/${nextPostId}/player`, { 
                replace: true, 
                state: { 
                    posts: nextPosts,
                    returnTo: returnPath, // Preserve the original return path
                    currentVideoId: originalVideoId // Preserve the original video ID
                } 
            });
        } else {
            navigate(returnPath, { replace: true });
        }
    };
    
    const handleDifficultyChange = (id: string, newDifficulty: Difficulty) => {
        updatePost(id, { difficulty: newDifficulty });
        setPostsToDisplay(prev => prev.map(p => p.id === id ? {...p, difficulty: newDifficulty} : p));
    };

    if (!postsToDisplay || postsToDisplay.length === 0) {
        return <div className="w-full h-screen flex items-center justify-center bg-[#0f0f0f]"><div className="text-white">{ICONS.spinner}</div></div>;
    }
    
    return (
        <div
            ref={containerRef}
            className="h-screen w-screen overflow-y-auto snap-y snap-mandatory bg-black no-scrollbar"
            style={{ 
                scrollSnapStop: 'always', 
                overscrollBehavior: 'none',
                scrollBehavior: 'smooth',
                WebkitOverflowScrolling: 'touch' // Mejor scroll en iOS
            }}
        >
            <div className="absolute top-4 left-4 z-20">
                <button 
                    onClick={() => {
                        // Use replace instead of push to avoid double navigation
                        navigate(returnPath, { 
                            replace: true,
                            state: { 
                                highlightVideoId: activePostId, // Highlight the video we're currently viewing
                                scrollToVideoId: originalVideoId // Scroll to the original video that was clicked
                            } 
                        });
                    }} 
                    className="flex items-center gap-2 px-4 py-2 bg-black/50 backdrop-blur-sm rounded-lg hover:bg-white/20 transition-colors text-white"
                >
                    {React.cloneElement(ICONS.chevronRight, {className: "h-5 w-5 transform rotate-180"})}
                    <span className="font-semibold">Atrás</span>
                </button>
            </div>
            
            {postsToDisplay.map((post, index) => {
                const currentActiveIndex = postsToDisplay.findIndex(p => p.id === activePostId);
                const isCurrentlyActive = post.id === activePostId;
                
                // Estrategia de preload más conservadora:
                // - Video actual: siempre se carga
                // - Video siguiente: preload para smooth transition  
                // - Video anterior: solo si es adyacente
                const distanceFromActive = Math.abs(index - currentActiveIndex);
                const shouldPreload = distanceFromActive <= 1;
                
                return (
                    <ReelItem
                        key={post.id}
                        post={post}
                        isActive={isCurrentlyActive}
                        shouldPreload={shouldPreload}
                        onDelete={handleDelete}
                        onDifficultyChange={handleDifficultyChange}
                    />
                );
            })}
        </div>
    );
};

export default PostPlayerPage;
