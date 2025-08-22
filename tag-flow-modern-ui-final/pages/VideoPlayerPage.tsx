
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useRealData } from '../hooks/useRealData';
import { Post, Difficulty, PostType } from '../types';
import { ICONS } from '../constants';


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
  globalAudioEnabled: boolean;
  setGlobalAudioEnabled: (enabled: boolean) => void;
}> = ({ post, isActive, onDelete, onDifficultyChange, shouldPreload = false, globalAudioEnabled, setGlobalAudioEnabled }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showDifficultyOptions, setShowDifficultyOptions] = useState(false);
  const [titleExpanded, setTitleExpanded] = useState(false);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const [videoError, setVideoError] = useState(false);
  const [videoSuspended, setVideoSuspended] = useState(false);
  const lastReactivationRef = useRef<number>(0);
  const reactivationCountRef = useRef<number>(0);
  
  // El estado muted depende del estado global
  const isMuted = !globalAudioEnabled;

  // Cargar video cuando se vuelve activo o debe precargar
  useEffect(() => {
    if (post.type === PostType.VIDEO) {
      if (isActive && !videoLoaded) {
        setVideoLoaded(true);
      } else if (shouldPreload && !videoLoaded) {
        // Precargar con delay para videos adyacentes
        const timer = setTimeout(() => {
          setVideoLoaded(true);
        }, 1000);
        return () => clearTimeout(timer);
      } else if (!isActive && !shouldPreload && videoLoaded) {
        // Liberar memoria de videos lejanos para prevenir problemas en móvil
        const timer = setTimeout(() => {
          setVideoLoaded(false);
        }, 3000);
        return () => clearTimeout(timer);
      }
    }
  }, [isActive, shouldPreload, videoLoaded, post.type]);

  useEffect(() => {
    const videoElement = videoRef.current;
    if (post.type === PostType.VIDEO && videoElement && videoLoaded) {
        // Actualizar muted state basado en configuración global
        videoElement.muted = isMuted;
        
        if (isActive) {
            // Resetear error cuando se vuelve activo
            setVideoError(false);
            videoElement.play().catch(() => {}); // Autoplay might be blocked
            setIsPlaying(true);
        } else {
            videoElement.pause();
            videoElement.currentTime = 0;
            setIsPlaying(false);
        }
    }
  }, [isActive, post.type, videoLoaded, isMuted]);

  // Detectar y recuperar videos con problemas
  useEffect(() => {
    const videoElement = videoRef.current;
    if (!videoElement || post.type !== PostType.VIDEO) return;

    const handleError = (e: Event) => {
      setVideoError(true);
      // Intentar recargar después de un breve delay
      setTimeout(() => {
        setVideoLoaded(false);
        setTimeout(() => {
          if (isActive) { // Solo recargar si el video está activo
            setVideoLoaded(true);
            setVideoError(false);
          }
        }, 200);
      }, 800);
    };

    const handleLoadedData = () => {
      setVideoError(false);
      setVideoSuspended(false);
      reactivationCountRef.current = 0; // Resetear contador de reactivaciones
    };

    const handleStalled = () => {
      if (isActive) {
        setVideoError(true);
      }
    };

    const handleSuspend = () => {
      if (isActive) {
        setVideoSuspended(true);
      }
    };

    const handleEmptied = () => {
      // No reactivar automáticamente en emptied - puede causar bucles
      // Solo marcar como suspendido si está activo
      if (isActive) {
        setVideoSuspended(true);
      }
    };

    videoElement.addEventListener('error', handleError);
    videoElement.addEventListener('loadeddata', handleLoadedData);
    videoElement.addEventListener('stalled', handleStalled);
    videoElement.addEventListener('suspend', handleSuspend);
    videoElement.addEventListener('emptied', handleEmptied);

    return () => {
      videoElement.removeEventListener('error', handleError);
      videoElement.removeEventListener('loadeddata', handleLoadedData);
      videoElement.removeEventListener('stalled', handleStalled);
      videoElement.removeEventListener('suspend', handleSuspend);
      videoElement.removeEventListener('emptied', handleEmptied);
    };
  }, [post.id, post.type, videoLoaded, isActive]);

  // Detectar y reactivar videos suspendidos cuando se vuelven activos (con throttling)
  useEffect(() => {
    if (isActive && videoSuspended && videoLoaded && post.type === PostType.VIDEO) {
      const now = Date.now();
      const timeSinceLastReactivation = now - lastReactivationRef.current;
      
      // Solo reactivar si han pasado al menos 2 segundos desde la última reactivación
      // Y no hemos intentado más de 3 veces
      if (timeSinceLastReactivation > 2000 && reactivationCountRef.current < 3) {
        const videoElement = videoRef.current;
        if (videoElement) {
          reactivationCountRef.current += 1;
          lastReactivationRef.current = now;
          
          videoElement.load();
          setVideoSuspended(false);
          
          setTimeout(() => {
            if (isActive && videoElement) {
              videoElement.muted = isMuted; // Restaurar estado de mute
              videoElement.play().catch(() => {});
              setIsPlaying(true);
            }
          }, 500);
        }
      } else if (reactivationCountRef.current >= 3) {
        setVideoSuspended(false); // Parar de intentar
      }
    }
    
    // Resetear contador cuando el video se vuelve inactivo
    if (!isActive) {
      reactivationCountRef.current = 0;
    }
  }, [isActive, videoSuspended, videoLoaded, post.type, post.id]);

  const handleVideoClick = () => {
    if (post.type !== PostType.VIDEO) return;
    
    // Si es el primer click global, activar audio para todos los videos
    if (!globalAudioEnabled && videoRef.current) {
      setGlobalAudioEnabled(true);
      videoRef.current.muted = false;
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
      return; // Salir aquí, no hacer toggle de play/pause
    }
    
    // Control normal de play/pause cuando audio ya está habilitado
    if (isPlaying) {
      videoRef.current?.pause();
      setIsPlaying(false);
    } else {
      videoRef.current?.play().catch(() => {});
      setIsPlaying(true);
    }
  };
  
  const handleDifficultyClick = (d: Difficulty) => {
      onDifficultyChange(post.id, d);
      setShowDifficultyOptions(false);
  }

  return (
    <div id={`post-item-${post.id}`} className="video-item w-screen relative snap-start flex-shrink-0 flex items-center justify-center bg-black" 
         style={{ height: '100dvh' }}>
      {post.type === PostType.VIDEO ? (
        <video
          ref={videoRef}
          src={videoLoaded ? post.postUrl : undefined}
          loop
          playsInline
          preload="none"
          muted={isMuted}
          className="w-full h-full object-contain"
          onClick={handleVideoClick}
          onCanPlay={() => {
            setVideoError(false);
          }}
          onWaiting={() => {
            if (isActive) setVideoError(true);
          }}
          onLoadStart={() => {
            // Video starting to load
          }}
        />
      ) : (
        <ImageCarousel post={post} isActive={isActive} />
      )}
      
      {post.type === PostType.VIDEO && (
        <div className={`absolute inset-0 flex items-center justify-center transition-opacity duration-300 ${!isPlaying && isActive ? 'opacity-100' : 'opacity-0'} pointer-events-none`}>
            <div className="bg-black/40 p-4 rounded-full">
                <div className="flex flex-col items-center">
                  <svg className="h-8 w-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 6.82v10.36c0 .79.87 1.27 1.54.84l8.14-5.18c.62-.39.62-1.29 0-1.68L9.54 5.98C8.87 5.55 8 6.03 8 6.82z"/>
                  </svg>
                  {!globalAudioEnabled && (
                    <span className="text-xs mt-1 text-white/80">Tap to enable audio</span>
                  )}
                </div>
            </div>
        </div>
      )}

      {/* Indicador de estado de audio global en esquina */}
      {post.type === PostType.VIDEO && isActive && (
        <div className="absolute top-4 right-4 bg-black/50 rounded-full p-2">
          {globalAudioEnabled ? (
            <svg className="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
            </svg>
          ) : (
            <svg className="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
            </svg>
          )}
        </div>
      )}
      
      <div className="absolute bottom-0 left-0 right-0 p-4 pb-safe text-white bg-gradient-to-t from-black/70 to-transparent z-10" 
           style={{ paddingBottom: 'max(1.5rem, env(safe-area-inset-bottom))' }}>
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

      <div className="absolute right-3 flex flex-col items-center gap-6 text-white z-10" 
           style={{ bottom: 'max(6rem, calc(6rem + env(safe-area-inset-bottom)))' }}>
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
    const [globalAudioEnabled, setGlobalAudioEnabled] = useState(false);
    
    // Get return path and original video from navigation state
    const returnPath = location.state?.returnTo || '/gallery';
    const originalVideoId = location.state?.currentVideoId || postId;
    
    
    const containerRef = useRef<HTMLDivElement>(null);
    const observerRef = useRef<IntersectionObserver | null>(null);
    const initialScrollDone = useRef(false);
    const isScrollingRef = useRef(false);
    
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
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const newPostId = entry.target.id.replace('post-item-', '');
            if(newPostId && newPostId !== activePostIdRef.current) {
                setActivePostId(newPostId);
                navigate(`/post/${newPostId}/player`, { 
                    replace: true, 
                    state: { 
                        posts: postsToDisplay,
                        returnTo: returnPath, // Preserve the original return path
                        currentVideoId: originalVideoId // Preserve the original video ID
                    } 
                });
            }
          }
        });
      };

      observerRef.current = new IntersectionObserver(handleIntersect, { root: containerRef.current, threshold: 0.8 });
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

    useEffect(() => {
        const container = containerRef.current;
        if (!container || postsToDisplay.length <= 1) return;

        const handleControlledScroll = (direction: 'up' | 'down') => {
            if (isScrollingRef.current) return;

            const currentIndex = postsToDisplay.findIndex(p => p.id === activePostIdRef.current);
            if (currentIndex === -1) return;

            let nextIndex = currentIndex;
            if (direction === 'down') {
                nextIndex = Math.min(currentIndex + 1, postsToDisplay.length - 1);
            } else { 
                nextIndex = Math.max(currentIndex - 1, 0);
            }

            if (nextIndex !== currentIndex) {
                isScrollingRef.current = true;
                const nextPostId = postsToDisplay[nextIndex].id;
                const targetElement = document.getElementById(`post-item-${nextPostId}`);
                targetElement?.scrollIntoView({ behavior: 'smooth' });

                setTimeout(() => {
                    isScrollingRef.current = false;
                }, 600);
            }
        };

        const handleWheel = (e: WheelEvent) => {
            e.preventDefault();
            if (Math.abs(e.deltaY) < 10) return;
            handleControlledScroll(e.deltaY > 0 ? 'down' : 'up');
        };

        let touchStartY = 1;
        let lastTouchY = 0;
        let touchStartTime = 0;
        let scrollProcessed = false;
        let scrollDirection: 'up' | 'down' | null = null;
        
        // Normalizador: convierte cualquier scroll en nuestro scroll controlado
        const processNormalizedScroll = (direction: 'up' | 'down') => {
            if (scrollProcessed) return;
            scrollProcessed = true;
            handleControlledScroll(direction);
        };
        
        const handleTouchStart = (e: TouchEvent) => { 
            touchStartY = e.touches[0].clientY;
            lastTouchY = touchStartY;
            touchStartTime = Date.now();
            scrollProcessed = false;
            scrollDirection = null;
        };
        
        const handleTouchMove = (e: TouchEvent) => {
            const currentY = e.touches[0].clientY;
            const totalDelta = touchStartY - currentY;
            const moveDelta = lastTouchY - currentY;
            
            // Detectar dirección en cualquier movimiento > 10px
            if (Math.abs(totalDelta) > 10 && !scrollDirection) {
                scrollDirection = totalDelta > 0 ? 'down' : 'up';
            }
            
            // Si hay dirección establecida, bloquear scroll nativo
            if (scrollDirection) {
                try {
                    e.preventDefault();
                } catch (err) {}
            }
            
            // Procesar cambio de video en cualquier movimiento significativo
            if (scrollDirection && !scrollProcessed && Math.abs(totalDelta) > 30) {
                processNormalizedScroll(scrollDirection);
            }
            
            lastTouchY = currentY;
        };
        
        const handleTouchEnd = (e: TouchEvent) => {
            const totalDelta = touchStartY - e.changedTouches[0].clientY;
            
            // Fallback: procesar si no se procesó y hay movimiento mínimo
            if (!scrollProcessed && Math.abs(totalDelta) > 20) {
                processNormalizedScroll(totalDelta > 0 ? 'down' : 'up');
            }
        };

        container.addEventListener('wheel', handleWheel, { passive: false });
        container.addEventListener('touchstart', handleTouchStart, { passive: true });
        container.addEventListener('touchmove', handleTouchMove, { passive: false });
        container.addEventListener('touchend', handleTouchEnd, { passive: true });

        return () => {
            container.removeEventListener('wheel', handleWheel);
            container.removeEventListener('touchstart', handleTouchStart);
            container.removeEventListener('touchmove', handleTouchMove);
            container.removeEventListener('touchend', handleTouchEnd);
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
              overscrollBehavior: 'contain',
              height: '100dvh' // Use dynamic viewport height for mobile
            }}
        >
            <div className="absolute z-20" 
                 style={{ 
                   top: 'max(1rem, env(safe-area-inset-top))', 
                   left: '1rem' 
                 }}>
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
                const distance = Math.abs(index - currentActiveIndex);
                const shouldPreload = distance <= 1; // Solo video actual y adyacentes
                const shouldRender = distance <= 5; // Solo renderizar videos cercanos para optimizar memoria
                
                if (!shouldRender) {
                    // Placeholder para videos lejanos
                    return (
                        <div 
                            key={post.id} 
                            id={`post-item-${post.id}`}
                            className="video-item w-screen relative snap-start flex-shrink-0 flex items-center justify-center bg-black" 
                            style={{ height: '100dvh' }}
                        >
                            <div className="text-white">Loading...</div>
                        </div>
                    );
                }
                
                return (
                    <ReelItem
                        key={post.id}
                        post={post}
                        isActive={post.id === activePostId}
                        shouldPreload={shouldPreload}
                        onDelete={handleDelete}
                        onDifficultyChange={handleDifficultyChange}
                        globalAudioEnabled={globalAudioEnabled}
                        setGlobalAudioEnabled={setGlobalAudioEnabled}
                    />
                );
            })}
        </div>
    );
};

export default PostPlayerPage;
