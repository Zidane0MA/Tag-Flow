
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
}> = ({ post, isActive, onDelete, onDifficultyChange }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showDifficultyOptions, setShowDifficultyOptions] = useState(false);

  useEffect(() => {
    const videoElement = videoRef.current;
    if (post.type === PostType.VIDEO && videoElement) {
        if (isActive) {
            videoElement.play().catch(() => {}); // Autoplay might be blocked
            setIsPlaying(true);
        } else {
            videoElement.pause();
            videoElement.currentTime = 0;
            setIsPlaying(false);
        }
    }
  }, [isActive, post.type]);


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
    <div id={`post-item-${post.id}`} className="video-item h-screen w-screen relative snap-start flex-shrink-0 flex items-center justify-center bg-black">
      {post.type === PostType.VIDEO ? (
        <video
          ref={videoRef}
          src={post.postUrl}
          loop
          muted
          playsInline
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
      
      <div className="absolute bottom-0 left-0 right-0 p-4 pb-6 text-white bg-gradient-to-t from-black/70 to-transparent z-10">
        <h3 className="font-bold text-lg">@{post.creator}</h3>
        <p className="text-sm mt-1">{post.title}</p>
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
                navigate(`/post/${newPostId}/player`, { replace: true, state: { posts: postsToDisplay } });
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
        const handleTouchStart = (e: TouchEvent) => { touchStartY = e.touches[0].clientY; };
        const handleTouchEnd = (e: TouchEvent) => {
            const deltaY = touchStartY - e.changedTouches[0].clientY;
            if (Math.abs(deltaY) > 40) {
                e.preventDefault();
                handleControlledScroll(deltaY > 0 ? 'down' : 'up');
            }
        };

        container.addEventListener('wheel', handleWheel, { passive: false });
        container.addEventListener('touchstart', handleTouchStart, { passive: true });
        container.addEventListener('touchend', handleTouchEnd, { passive: true });

        return () => {
            container.removeEventListener('wheel', handleWheel);
            container.removeEventListener('touchstart', handleTouchStart);
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
            navigate(`/post/${nextPostId}/player`, { replace: true, state: { posts: nextPosts } });
        } else {
            navigate('/gallery', { replace: true });
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
            style={{ scrollSnapStop: 'always', overscrollBehavior: 'contain' }}
        >
            <div className="absolute top-4 left-4 z-20">
                <button onClick={() => navigate('/gallery')} className="flex items-center gap-2 px-4 py-2 bg-black/50 backdrop-blur-sm rounded-lg hover:bg-white/20 transition-colors text-white">
                    {React.cloneElement(ICONS.chevronRight, {className: "h-5 w-5 transform rotate-180"})}
                    <span className="font-semibold">Galería</span>
                </button>
            </div>
            
            {postsToDisplay.map(post => (
                 <ReelItem
                    key={post.id}
                    post={post}
                    isActive={post.id === activePostId}
                    onDelete={handleDelete}
                    onDifficultyChange={handleDifficultyChange}
                />
            ))}
        </div>
    );
};

export default PostPlayerPage;
