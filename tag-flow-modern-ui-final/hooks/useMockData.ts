
import React, { createContext, useState, useContext, useCallback, useMemo } from 'react';
import { Post, Platform, EditStatus, ProcessStatus, Difficulty, DataContextType, PostType, Creator, Subscription, SubscriptionInfo, SubscriptionType } from '../types';
import { geminiAnalyzePostContent } from '../services/geminiService';

const MOCK_CREATORS: Creator[] = [
    {
        name: 'MMD_Creator_X',
        displayName: 'MMD Creator X',
        platforms: {
            [Platform.YOUTUBE]: {
                url: 'https://youtube.com/@mmdcreatorx',
                postCount: 0, // Will be calculated
                subscriptions: [
                    { type: 'channel', id: 'mmd_creator_x_channel', name: 'Canal Principal' },
                    { type: 'playlist', id: 'mmd_tutorials', name: 'MMD Tutorials' },
                ],
            },
            [Platform.TIKTOK]: {
                url: 'https://tiktok.com/@mmdcreatorx',
                postCount: 0,
                subscriptions: [
                    { type: 'feed', id: 'mmd_creator_x_tiktok_feed', name: 'Feed' },
                    { type: 'liked', id: 'mmd_creator_x_tiktok_liked', name: 'Liked' },
                ],
            },
        },
    },
    {
        name: 'VFX_Master',
        displayName: 'VFX Master',
        platforms: {
            [Platform.INSTAGRAM]: {
                url: 'https://instagram.com/vfxmaster',
                postCount: 0,
                subscriptions: [
                    { type: 'reels', id: 'vfx_master_reels', name: 'Reels' },
                    { type: 'stories', id: 'vfx_master_stories', name: 'Stories' },
                ],
            },
            [Platform.VIMEO]: {
                url: 'https://vimeo.com/vfxmaster',
                postCount: 0,
                subscriptions: [{ type: 'channel', id: 'vfx_master_vimeo_channel', name: 'Portfolio' }],
            },
        },
    },
    {
        name: 'GamerGirl_95',
        displayName: 'GamerGirl 🎮',
        platforms: {
            [Platform.TIKTOK]: {
                url: 'https://tiktok.com/@gamergirl95',
                postCount: 0,
                subscriptions: [
                    { type: 'feed', id: 'gamergirl_95_feed', name: 'Feed' },
                    { type: 'music', id: 'fortnite-dance-music', name: 'Fortnite Dances' },
                ],
            },
             [Platform.YOUTUBE]: {
                url: 'https://youtube.com/@gamergirl95',
                postCount: 0, // Will be calculated
                subscriptions: [
                    { type: 'channel', id: 'gamergirl_95_channel', name: 'Canal Principal' },
                    { type: 'playlist', id: 'lets-play-valorant', name: "Let's Play Valorant" },
                    { type: 'liked', id: 'gamergirl_95_liked', name: 'Liked Videos' },
                ],
            },
        }
    }
];

const MOCK_SPECIAL_LISTS: SubscriptionInfo[] = [
    { type: 'hashtag', id: 'c4d', name: 'Cinema4D', platform: Platform.INSTAGRAM, postCount: 0, url: 'https://instagram.com/explore/tags/c4d' },
    { type: 'music', id: 'lo-fi-beats', name: 'Lofi Beats', platform: Platform.TIKTOK, postCount: 0, url: 'https://tiktok.com/music/lofi-beats' },
    { type: 'saved', id: 'design_inspiration_ig', name: 'Inspiración Diseño', platform: Platform.INSTAGRAM, creator: 'VFX_Master', postCount: 0 },
];


const generateMockPosts = (): Post[] => {
    const posts: Post[] = [];
    let postId = 1;

    MOCK_CREATORS.forEach(creator => {
        Object.entries(creator.platforms).forEach(([platform, platformInfo]) => {
            platformInfo.subscriptions.forEach(sub => {
                const numPosts = 10 + Math.floor(Math.random() * 15);
                for (let i = 0; i < numPosts; i++) {
                    const isImagePost = (platform as Platform) === Platform.INSTAGRAM && Math.random() > 0.5;
                    const imageUrls = isImagePost ? Array.from({length: Math.floor(Math.random() * 5) + 1}, (_, j) => `https://picsum.photos/seed/${postId}_${j}/1080/1920`) : undefined;

                    const post: Post = {
                        id: `post_${postId}`,
                        title: `${isImagePost ? 'Image' : 'Video'} for ${creator.displayName} - ${sub.name} #${i + 1}`,
                        description: `Description for content from ${creator.displayName} in ${sub.name}.`,
                        thumbnailUrl: `https://picsum.photos/seed/${postId}/400/225`,
                        postUrl: isImagePost ? (imageUrls?.[0] || '') : 'https://www.w3schools.com/html/mov_bbb.mp4',
                        type: isImagePost ? PostType.IMAGE : PostType.VIDEO,
                        imageUrls,
                        creator: creator.name,
                        platform: platform as Platform,
                        subscription: sub,
                        editStatus: Object.values(EditStatus)[postId % Object.values(EditStatus).length],
                        processStatus: Object.values(ProcessStatus)[postId % Object.values(ProcessStatus).length],
                        difficulty: Object.values(Difficulty)[postId % Object.values(Difficulty).length],
                        music: postId % 3 === 0 ? `Trending Song ${postId}` : undefined,
                        artist: postId % 3 === 0 ? `Artist ${postId}` : undefined,
                        characters: postId % 2 === 0 ? [`Character A`, `Character B`] : undefined,
                        duration: isImagePost ? 0 : 60 + Math.random() * 120,
                        size: 5 + Math.random() * 50,
                        downloadDate: new Date(2023, 10, 1 + postId).toISOString(),
                    };
                    posts.push(post);
                    postId++;
                }
            });
        });
    });

    MOCK_SPECIAL_LISTS.forEach(list => {
        const numPosts = 15 + Math.floor(Math.random() * 20);
        for (let i = 0; i < numPosts; i++) {
             const randomCreator = MOCK_CREATORS[Math.floor(Math.random() * MOCK_CREATORS.length)];
             const post: Post = {
                id: `post_${postId}`,
                title: `Special list content #${i+1}`,
                description: `Post from special list ${list.name}`,
                thumbnailUrl: `https://picsum.photos/seed/${postId}/400/225`,
                postUrl: 'https://www.w3schools.com/html/mov_bbb.mp4',
                type: PostType.VIDEO,
                creator: randomCreator.name,
                platform: list.platform,
                subscription: { type: list.type, id: list.id, name: list.name },
                editStatus: Object.values(EditStatus)[postId % Object.values(EditStatus).length],
                processStatus: Object.values(ProcessStatus)[postId % Object.values(ProcessStatus).length],
                difficulty: Object.values(Difficulty)[postId % Object.values(Difficulty).length],
                duration: 60 + Math.random() * 120,
                size: 5 + Math.random() * 50,
                downloadDate: new Date(2023, 10, 1 + postId).toISOString(),
            };
            posts.push(post);
            postId++;
        }
    });

    return posts;
};


const DataContext = createContext<DataContextType | null>(null);

export const DataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [posts, setPosts] = useState<Post[]>(() => generateMockPosts());
  const [trash, setTrash] = useState<Post[]>([]);

  const updatePost = useCallback((id: string, updates: Partial<Post>) => {
    setPosts(prev => prev.map(p => p.id === id ? { ...p, ...updates } : p));
  }, []);
  
  const updateMultiplePosts = useCallback((ids: string[], updates: Partial<Post>) => {
    setPosts(prev => prev.map(p => ids.includes(p.id) ? { ...p, ...updates } : p));
  }, []);

  const moveToTrash = useCallback((id: string) => {
    setPosts(prev => {
      const postToTrash = prev.find(p => p.id === id);
      if (postToTrash) {
        setTrash(t => [...t, { ...postToTrash, deletedAt: new Date().toISOString() }]);
      }
      return prev.filter(p => p.id !== id);
    });
  }, []);

  const moveMultipleToTrash = useCallback((ids: string[]) => {
     const postsToTrash = posts.filter(p => ids.includes(p.id));
     setTrash(t => [...t, ...postsToTrash.map(p => ({...p, deletedAt: new Date().toISOString()}))]);
     setPosts(prev => prev.filter(p => !ids.includes(p.id)));
  }, [posts]);

  const restoreFromTrash = useCallback((id: string) => {
    setTrash(prev => {
      const postToRestore = prev.find(p => p.id === id);
      if (postToRestore) {
        const { deletedAt, ...restoredPost } = postToRestore;
        setPosts(p => [restoredPost, ...p]);
      }
      return prev.filter(p => p.id !== id);
    });
  }, []);

  const deletePermanently = useCallback((id: string) => {
    setTrash(prev => prev.filter(p => p.id !== id));
  }, []);

  const emptyTrash = useCallback(() => {
    setTrash([]);
  }, []);

  const analyzePost = useCallback(async (id: string) => {
    const post = posts.find(p => p.id === id);
    if (!post) return;

    updatePost(id, { processStatus: ProcessStatus.PROCESSING });
    try {
      const analysis = await geminiAnalyzePostContent(post.title);
      updatePost(id, {
        ...analysis,
        processStatus: ProcessStatus.COMPLETED
      });
    } catch (error) {
      console.error("Analysis failed:", error);
      updatePost(id, { processStatus: ProcessStatus.ERROR });
    }
  }, [posts, updatePost]);

  const reanalyzePosts = useCallback(async (ids: string[]) => {
    ids.forEach(id => updatePost(id, { processStatus: ProcessStatus.PROCESSING }));
    try {
      await Promise.all(ids.map(async id => {
        const post = posts.find(p => p.id === id);
        if (post) {
           const analysis = await geminiAnalyzePostContent(post.title);
           updatePost(id, {
             ...analysis,
             processStatus: ProcessStatus.COMPLETED
           });
        }
      }));
    } catch (error) {
       console.error("Re-analysis failed:", error);
       ids.forEach(id => updatePost(id, { processStatus: ProcessStatus.ERROR }));
    }
  }, [posts, updatePost]);


  const getStats = useCallback(() => {
    return {
      total: posts.length,
      withMusic: posts.filter(p => p.music).length,
      withCharacters: posts.filter(p => p.characters && p.characters.length > 0).length,
      processed: posts.filter(p => p.processStatus === ProcessStatus.COMPLETED).length,
      inTrash: trash.length,
      pending: posts.filter(p => p.processStatus === ProcessStatus.PENDING).length
    };
  }, [posts, trash]);

  const creators = useMemo(() => {
    return MOCK_CREATORS.map(creator => {
        const updatedPlatforms = { ...creator.platforms };
        Object.entries(creator.platforms).forEach(([platformKey, platformValue]) => {
            if(platformValue) {
                const subs = platformValue.subscriptions.map(sub => {
                    const postCount = posts.filter(p => p.subscription?.id === sub.id).length;
                    return {...sub, postCount};
                });
                updatedPlatforms[platformKey as Platform] = {
                    ...platformValue,
                    subscriptions: subs,
                    postCount: posts.filter(p => p.creator === creator.name && p.platform === platformKey).length
                };
            }
        });
        return { ...creator, platforms: updatedPlatforms };
    });
}, [posts]);

  const getCreatorByName = useCallback((name: string) => {
      return creators.find(c => c.name === name);
  }, [creators]);

  const getPostsByCreator = useCallback((creatorName: string, platform?: Platform, listId?: string) => {
      return posts.filter(p => {
          if (p.creator !== creatorName) return false;
          if (platform && p.platform !== platform) return false;
          if (listId && p.subscription?.id !== listId) return false;
          return true;
      });
  }, [posts]);

  const getSubscriptionInfo = useCallback((type: SubscriptionType, id: string): SubscriptionInfo | undefined => {
    for (const creator of creators) {
      for (const platform of Object.values(creator.platforms)) {
        if(platform) {
            const sub = platform.subscriptions.find(s => s.type === type && s.id === id);
            if (sub) {
                return {
                    ...sub,
                    platform: Object.keys(creator.platforms).find(p => creator.platforms[p as Platform] === platform) as Platform,
                    postCount: posts.filter(p => p.subscription?.id === id).length,
                    creator: creator.name,
                };
            }
        }
      }
    }
    const specialList = MOCK_SPECIAL_LISTS.find(l => l.type === type && l.id === id);
    if(specialList) {
        const relatedPosts = posts.filter(p => p.subscription?.id === id);
        const uniqueCreators = new Set(relatedPosts.map(p => p.creator));
        return {
            ...specialList,
            postCount: relatedPosts.length,
            creatorCount: uniqueCreators.size
        }
    }
    return undefined;
  }, [posts, creators]);

  const getPostsBySubscription = useCallback((type: SubscriptionType, id: string, list?: string) => {
      return posts.filter(p => {
          if (type === 'account') {
            return p.creator === id && (list ? p.subscription?.id === list : true);
          }
          return p.subscription?.type === type && p.subscription?.id === id;
      });
  }, [posts]);


  const value = useMemo(() => ({
    posts,
    trash,
    creators,
    updatePost,
    updateMultiplePosts,
    moveToTrash,
    moveMultipleToTrash,
    restoreFromTrash,
    deletePermanently,
    emptyTrash,
    analyzePost,
    reanalyzePosts,
    getStats,
    getCreatorByName,
    getPostsByCreator,
    getSubscriptionInfo,
    getPostsBySubscription,
  }), [posts, trash, creators, updatePost, updateMultiplePosts, moveToTrash, moveMultipleToTrash, restoreFromTrash, deletePermanently, emptyTrash, analyzePost, reanalyzePosts, getStats, getCreatorByName, getPostsByCreator, getSubscriptionInfo, getPostsBySubscription]);


  return React.createElement(DataContext.Provider, { value: value }, children);
};

export const useData = (): DataContextType => {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};
