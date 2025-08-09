
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
}> = ({ post, isActive, onDelete, onDifficultyChange, shouldPreload = false }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showDifficultyOptions, setShowDifficultyOptions] = useState(false);
  const [titleExpanded, setTitleExpanded] = useState(false);
  const [videoLoaded, setVideoLoaded] = useState(false);

  // Cargar video cuando se vuelve activo o debe precargar
  useEffect(() => {
    if (!videoLoaded && post.type === PostType.VIDEO) {
      if (isActive) {
        setVideoLoaded(true);
      } else if (shouldPreload) {
        // Precargar con delay para videos adyacentes
        const timer = setTimeout(() => {
          setVideoLoaded(true);
        }, 1000);
        return () => clearTimeout(timer);
      }
    }
  }, [isActive, shouldPreload, videoLoaded, post.type]);

  useEffect(() => {
    const videoElement = videoRef.current;
    if (post.type === PostType.VIDEO && videoElement && videoLoaded) {
        if (isActive) {
            videoElement.play().catch(() => {}); // Autoplay might be blocked
            setIsPlaying(true);
        } else {
            videoElement.pause();
            videoElement.currentTime = 0;
            setIsPlaying(false);
        }
    }
  }, [isActive, post.type, videoLoaded]);


  const handleVideoClick = () => {
    if (post.type !== PostType.VIDEO) return;
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
          className="w-full h-full object-contain"
          onClick={handleVideoClick}
        />
      ) : (
        <ImageCarousel post={post} isActive={isActive} />
      )}
      
      {post.type === PostType.VIDEO && (
        <div className={`absolute inset-0 flex items-center justify-center transition-opacity duration-300 ${!isPlaying && isActive ? 'opacity-100' : 'opacity-0'} pointer-events-none`}>
            <div className="bg-black/50 p-6 rounded-full">
                {React.cloneElement(ICONS.play, { className: 'h-12 w-12 text-white' })}
            </div>
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

        let touchStartY = 0;
        let touchStartTime = 0;
        let touchHandled = false;
        
        const handleTouchStart = (e: TouchEvent) => { 
            touchStartY = e.touches[0].clientY; 
            touchStartTime = Date.now();
            touchHandled = false;
        };
        
        const handleTouchMove = (e: TouchEvent) => {
            if (touchHandled) return;
            
            const currentY = e.touches[0].clientY;
            const deltaY = touchStartY - currentY;
            const deltaTime = Date.now() - touchStartTime;
            
            // Solo manejar gestos rápidos y significativos
            if (Math.abs(deltaY) > 80 && deltaTime < 200) {
                // Intentar prevenir, pero no depender de ello
                try {
                    e.preventDefault();
                } catch (err) {
                    // Ignorar errores de preventDefault
                }
                touchHandled = true;
                handleControlledScroll(deltaY > 0 ? 'down' : 'up');
            }
        };
        
        const handleTouchEnd = (e: TouchEvent) => {
            if (touchHandled) return;
            
            const deltaY = touchStartY - e.changedTouches[0].clientY;
            const deltaTime = Date.now() - touchStartTime;
            
            // Fallback: manejar en touchend si no se manejó en touchmove
            if (Math.abs(deltaY) > 100 && deltaTime < 300) {
                handleControlledScroll(deltaY > 0 ? 'down' : 'up');
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
                const shouldPreload = Math.abs(index - currentActiveIndex) <= 1; // Precargar video actual y adyacentes
                
                return (
                    <ReelItem
                        key={post.id}
                        post={post}
                        isActive={post.id === activePostId}
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
