/**
 * @deprecated Este hook está obsoleto. Use los hooks específicos del sistema cursor:
 * - useCursorData: Para datos de galería principal
 * - useCursorCreatorData: Para datos de creadores específicos
 * - useCursorSubscriptionData: Para datos de suscripciones
 * - useCursorTrashData: Para datos de papelera
 * - useCursorCRUD: Para operaciones CRUD (crear, actualizar, eliminar)
 *
 * El sistema cursor ofrece 99.2% mejor performance (2ms vs 250ms+) y
 * soporte para datasets de 100K+ videos sin degradación.
 *
 * Hook para manejar datos reales del backend
 * Reemplaza useMockData con conexión real a la API
 */

import React, { createContext, useState, useContext, useCallback, useEffect, useRef, useMemo } from 'react';
import { Post, Platform, EditStatus, ProcessStatus, Difficulty, DataContextType, Creator, SubscriptionInfo, SubscriptionType } from '../types';
import { apiService, VideoFilters } from '../services/apiService';

interface RealDataContextType extends DataContextType {
  loading: boolean;
  loadingMore: boolean;
  hasMore: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
  loadVideos: (filters?: VideoFilters) => Promise<void>;
  loadMoreVideos: () => Promise<void>;
  loadTrashVideos: () => Promise<void>;
  restoreMultipleFromTrash: (ids: string[]) => Promise<void>;
  getSubscriptionStats: (type: SubscriptionType, id: number) => Promise<any>;
  // Nuevas funciones para infinite scroll
  loadCreatorPosts: (creatorName: string, platform?: Platform, listId?: string) => Promise<Post[]>;
  loadMoreCreatorPosts: (creatorName: string, platform?: Platform, listId?: string) => Promise<void>;
  getCreatorScrollData: (creatorName: string, platform?: Platform, listId?: string) => {posts: Post[], offset: number, hasMore: boolean, loading: boolean, initialLoaded: boolean};
  loadSubscriptionPosts: (type: SubscriptionType, id: number, list?: string) => Promise<Post[]>;
  loadMoreSubscriptionPosts: (type: SubscriptionType, id: number, list?: string) => Promise<void>;
  getSubscriptionScrollData: (type: SubscriptionType, id: number, list?: string) => {posts: Post[], offset: number, hasMore: boolean, loading: boolean, initialLoaded: boolean};
}

const RealDataContext = createContext<RealDataContextType | undefined>(undefined);

export const RealDataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Estados principales
  const [posts, setPosts] = useState<Post[]>([]);
  const [trash, setTrash] = useState<Post[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Estados para paginación
  const [currentFilters, setCurrentFilters] = useState<VideoFilters>({});
  const [currentOffset, setCurrentOffset] = useState(0);
  const [totalVideos, setTotalVideos] = useState(0);

  // Estados para creadores y suscripciones
  const [backendCreators, setBackendCreators] = useState<Creator[]>([]);
  
  // Estados derivados que se calculan de los posts
  const creatorsRef = useRef<Creator[]>([]);
  const lastPostsLengthRef = useRef(0);
  const lastBackendCreatorsLengthRef = useRef(0);
  
  const creators = useMemo(() => {
    // PRIORIDAD 1: Si tenemos backendCreators, siempre usarlos
    if (backendCreators.length > 0) {
      return backendCreators;
    }
    
    // PRIORIDAD 2: Fallback a extraer de posts
    // Fallback: extraer de posts y construir plataformas
    const creatorsMap = new Map<string, { [key: string]: { postCount: number } }>();
    
    posts.forEach(post => {
      if (!creatorsMap.has(post.creator)) {
        creatorsMap.set(post.creator, {});
      }
      
      const creatorPlatforms = creatorsMap.get(post.creator)!;
      const platformKey = post.platform;
      
      if (!creatorPlatforms[platformKey]) {
        creatorPlatforms[platformKey] = { postCount: 0 };
      }
      creatorPlatforms[platformKey].postCount++;
    });

    const newCreators = Array.from(creatorsMap.entries()).map(([creatorName, platforms]) => {
      // Agregar datos de ejemplo para suscripciones y listas basados en la plataforma
      const enhancedPlatforms = Object.fromEntries(
        Object.entries(platforms).map(([platform, data]) => {
          let subscriptions: any[] = [];
          let lists: string[] = [];
          
          // Usar la misma lógica que el backend (creators.py líneas 47-70)
          const creatorId = creatorName.toLowerCase().replace(/\s+/g, '_');
          
          // Mapear tipos de suscripción por plataforma (igual que en el backend)
          const subscriptionMapping: { [key: string]: { type: string, name: string } } = {
            'youtube': { type: 'channel', name: 'Canal Principal' },
            'tiktok': { type: 'feed', name: 'Feed Principal' },
            'instagram': { type: 'feed', name: 'Feed Principal' },
            'facebook': { type: 'account', name: 'Página Principal' },
            'twitter': { type: 'account', name: 'Cuenta Principal' },
            'twitch': { type: 'channel', name: 'Canal Principal' },
            'discord': { type: 'account', name: 'Servidor Principal' },
            'vimeo': { type: 'channel', name: 'Canal Principal' },
            'bilibili': { type: 'feed', name: 'Feed Principal' },
            'bilibili/video': { type: 'feed', name: 'Feed Principal' },
            'bilibili/video/tv': { type: 'feed', name: 'Feed Principal' }
          };
          
          const platformMapping = subscriptionMapping[platform.toLowerCase()] || { type: 'feed', name: 'Feed Principal' };
          
          subscriptions = [
            {
              type: platformMapping.type,
              id: `${creatorId}_${platform}_main`,
              name: platformMapping.name
            }
          ];
          
          // Listas básicas por plataforma
          const listMapping: { [key: string]: string[] } = {
            'youtube': ['feed'],
            'tiktok': ['feed'],
            'instagram': ['feed', 'reels'],
            'bilibili': ['feed'],
            'bilibili/video': ['feed'],
            'bilibili/video/tv': ['feed']
          };
          
          lists = listMapping[platform.toLowerCase()] || ['feed'];
          
          return [platform, {
            ...data,
            subscriptions,
            lists,
            url: `https://${platform.toLowerCase()}.com/@${creatorName.toLowerCase().replace(/\s+/g, '')}`
          }];
        })
      );

      return {
        name: creatorName,
        displayName: creatorName,
        platforms: enhancedPlatforms
      };
    });
    
    creatorsRef.current = newCreators;
    return newCreators;
  }, [posts.length, backendCreators]); // Depender del array completo para detectar cambios

  /**
   * Cargar videos desde el backend con paginación
   */
  const loadVideos = useCallback(async (filters: VideoFilters = {}) => {
    setLoading(true);
    setError(null);
    try {
      // Usar paginación: 50 videos por página
      const PAGE_SIZE = 50;
      const filtersWithPagination = { 
        ...filters, 
        limit: PAGE_SIZE, 
        offset: 0 
      };
      
      // Cargar videos filtrados y todos los creadores en paralelo
      const [{ posts: newPosts, total, hasMore: backendHasMore }, creatorsData] = await Promise.all([
        apiService.getVideos(filtersWithPagination),
        apiService.getCreators()
      ]);
      
      
      setPosts(newPosts);
      setCurrentFilters(filters);
      setCurrentOffset(PAGE_SIZE);
      setTotalVideos(total);
      setHasMore(backendHasMore); // Usar hasMore del backend
      setBackendCreators(creatorsData);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error loading videos';
      setError(errorMessage);
      console.error('Error loading videos:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Cargar más videos (paginación infinita)
   */
  const loadMoreVideos = useCallback(async () => {
    if (loadingMore || !hasMore) {
      return;
    }

    setLoadingMore(true);
    setError(null);

    try {
      const PAGE_SIZE = 50;

      const filtersWithPagination = {
        ...currentFilters,
        limit: PAGE_SIZE,
        offset: currentOffset  // ✅ Usar currentOffset (actual)
      };

      const { posts: newPosts, total, hasMore: backendHasMore } = await apiService.getVideos(filtersWithPagination);

      setPosts(prevPosts => {
        // Evitar duplicados basándose en el ID
        const existingIds = new Set(prevPosts.map(p => p.id));
        const uniqueNewPosts = newPosts.filter(p => !existingIds.has(p.id));
        return [...prevPosts, ...uniqueNewPosts];
      });

      const newOffset = currentOffset + PAGE_SIZE;
      setCurrentOffset(newOffset);
      setTotalVideos(total);
      setHasMore(backendHasMore); // Usar hasMore del backend
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error loading more videos';
      setError(errorMessage);
      console.error('Error loading more videos:', err);
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, hasMore, currentFilters, currentOffset]);

  /**
   * Cargar creadores desde el backend
   */
  const loadCreators = useCallback(async () => {
    try {
      const creatorsData = await apiService.getCreators();
      setBackendCreators(creatorsData);
    } catch (err) {
      console.error('Error loading creators:', err);
      // No mostrar error crítico, los creadores se pueden extraer de los posts
    }
  }, []);

  /**
   * Refrescar todos los datos (reinicia la paginación)
   */
  const refreshData = useCallback(async () => {
    // Reiniciar estado de paginación
    setCurrentOffset(0);
    setHasMore(true);
    
    // Llamar funciones directamente sin dependencias
    try {
      // Usar paginación: 50 videos por página
      const PAGE_SIZE = 50;
      const filtersWithPagination = { 
        limit: PAGE_SIZE, 
        offset: 0 
      };
      
      const [{ posts: newPosts, total, hasMore: backendHasMore }, creatorsData] = await Promise.all([
        apiService.getVideos(filtersWithPagination),
        apiService.getCreators()
      ]);
      
      setPosts(newPosts);
      setCurrentFilters({});
      setCurrentOffset(PAGE_SIZE);
      setTotalVideos(total);
      setHasMore(backendHasMore); // Usar hasMore del backend
      setBackendCreators(creatorsData);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error loading data';
      setError(errorMessage);
      console.error('Error refreshing data:', err);
    }
  }, []); // Sin dependencias para evitar ciclos

  /**
   * Actualizar un post
   */
  const updatePost = useCallback(async (id: string, updates: Partial<Post>) => {
    try {
      setLoading(true);
      const success = await apiService.updateVideo(id, updates);
      
      if (success) {
        setPosts(prevPosts => 
          prevPosts.map(post => 
            post.id === id ? { ...post, ...updates } : post
          )
        );
      } else {
        throw new Error('Failed to update video');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error updating video';
      setError(errorMessage);
      console.error('Error updating post:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Actualizar múltiples posts
   */
  const updateMultiplePosts = useCallback(async (ids: string[], updates: Partial<Post>) => {
    try {
      setLoading(true);
      const success = await apiService.updateMultipleVideos(ids, updates);
      
      if (success) {
        setPosts(prevPosts => 
          prevPosts.map(post => 
            ids.includes(post.id) ? { ...post, ...updates } : post
          )
        );
      } else {
        throw new Error('Failed to update videos');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error updating videos';
      setError(errorMessage);
      console.error('Error updating multiple posts:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Mover al trash (soft delete)
   */
  const moveToTrash = useCallback(async (id: string) => {
    try {
      const success = await apiService.moveToTrash([id]);
      
      if (success) {
        const postToMove = posts.find(p => p.id === id);
        if (postToMove) {
          setPosts(prevPosts => prevPosts.filter(p => p.id !== id));
          setTrash(prevTrash => [...prevTrash, { ...postToMove, deletedAt: new Date().toISOString() }]);
          
          // Also remove from creator scroll data
          setCreatorScrollData(prev => {
            const updatedData = { ...prev };
            Object.keys(updatedData).forEach(key => {
              if (updatedData[key].posts.some(p => p.id === id)) {
                updatedData[key] = {
                  ...updatedData[key],
                  posts: updatedData[key].posts.filter(p => p.id !== id)
                };
              }
            });
            return updatedData;
          });
          
          // Also remove from subscription scroll data
          setSubscriptionScrollData(prev => {
            const updatedData = { ...prev };
            Object.keys(updatedData).forEach(key => {
              if (updatedData[key].posts.some(p => p.id === id)) {
                updatedData[key] = {
                  ...updatedData[key],
                  posts: updatedData[key].posts.filter(p => p.id !== id)
                };
              }
            });
            return updatedData;
          });
        }
      } else {
        throw new Error('Failed to move video to trash');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error moving video to trash';
      setError(errorMessage);
      console.error('Error moving to trash:', err);
      throw err;
    }
  }, [posts]);

  /**
   * Mover múltiples al trash
   */
  const moveMultipleToTrash = useCallback(async (ids: string[]) => {
    try {
      setLoading(true);
      const success = await apiService.moveToTrash(ids);
      
      if (success) {
        const postsToMove = posts.filter(p => ids.includes(p.id));
        setPosts(prevPosts => prevPosts.filter(p => !ids.includes(p.id)));
        setTrash(prevTrash => [
          ...prevTrash, 
          ...postsToMove.map(post => ({ ...post, deletedAt: new Date().toISOString() }))
        ]);
        
        // Also remove from creator scroll data
        setCreatorScrollData(prev => {
          const updatedData = { ...prev };
          Object.keys(updatedData).forEach(key => {
            const hasAnyDeletedVideo = updatedData[key].posts.some(p => ids.includes(p.id));
            if (hasAnyDeletedVideo) {
              updatedData[key] = {
                ...updatedData[key],
                posts: updatedData[key].posts.filter(p => !ids.includes(p.id))
              };
            }
          });
          return updatedData;
        });
        
        // Also remove from subscription scroll data
        setSubscriptionScrollData(prev => {
          const updatedData = { ...prev };
          Object.keys(updatedData).forEach(key => {
            const hasAnyDeletedVideo = updatedData[key].posts.some(p => ids.includes(p.id));
            if (hasAnyDeletedVideo) {
              updatedData[key] = {
                ...updatedData[key],
                posts: updatedData[key].posts.filter(p => !ids.includes(p.id))
              };
            }
          });
          return updatedData;
        });
      } else {
        throw new Error('Failed to move videos to trash');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error moving videos to trash';
      setError(errorMessage);
      console.error('Error moving multiple to trash:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [posts]);

  /**
   * Cargar videos de la papelera
   */
  const loadTrashVideos = useCallback(async () => {
    try {
      const { posts: trashPosts } = await apiService.getTrashVideos();
      setTrash(trashPosts.map(post => ({ ...post, deletedAt: post.downloadDate || post.uploadDate || new Date().toISOString() })));
    } catch (err) {
      console.error('Error loading trash videos:', err);
      setTrash([]);
    }
  }, []);

  /**
   * Restaurar desde trash
   */
  const restoreFromTrash = useCallback(async (id: string) => {
    try {
      const success = await apiService.restoreVideo(id);
      
      if (success) {
        const postToRestore = trash.find(p => p.id === id);
        if (postToRestore) {
          // Remover de trash
          setTrash(prevTrash => prevTrash.filter(p => p.id !== id));
          // Agregar de vuelta a posts principales
          const { deletedAt, ...restoredPost } = postToRestore;
          setPosts(prevPosts => [restoredPost, ...prevPosts]);
          
          // Note: We don't add back to creator/subscription scroll data here
          // because those pages will reload their data from the backend when navigated to
        }
      } else {
        throw new Error('Failed to restore video');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error restoring video';
      setError(errorMessage);
      console.error('Error restoring from trash:', err);
      throw err;
    }
  }, [trash]);

  /**
   * Restaurar múltiples videos desde trash
   */
  const restoreMultipleFromTrash = useCallback(async (ids: string[]) => {
    try {
      const success = await apiService.restoreMultipleVideos(ids);
      
      if (success) {
        const postsToRestore = trash.filter(p => ids.includes(p.id));
        // Remover de trash
        setTrash(prevTrash => prevTrash.filter(p => !ids.includes(p.id)));
        // Agregar de vuelta a posts principales
        const restoredPosts = postsToRestore.map(({ deletedAt, ...post }) => post);
        setPosts(prevPosts => [...restoredPosts, ...prevPosts]);
        
        // Note: We don't add back to creator/subscription scroll data here
        // because those pages will reload their data from the backend when navigated to
      } else {
        throw new Error('Failed to restore videos');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error restoring videos';
      setError(errorMessage);
      console.error('Error restoring multiple from trash:', err);
      throw err;
    }
  }, [trash]);

  /**
   * Eliminar permanentemente
   */
  const deletePermanently = useCallback(async (id: string): Promise<{success: boolean, message?: string}> => {
    try {
      const result = await apiService.deletePermanently(id);
      
      if (result.success) {
        // Remover de trash permanentemente
        setTrash(prevTrash => prevTrash.filter(p => p.id !== id));
        return { success: true, message: result.message };
      } else {
        return { success: false, message: 'Failed to permanently delete video' };
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error permanently deleting video';
      setError(errorMessage);
      console.error('Error permanently deleting:', err);
      return { success: false, message: errorMessage };
    }
  }, []);

  /**
   * Vaciar trash
   */
  const emptyTrash = useCallback(async () => {
    try {
      const success = await apiService.emptyTrash();
      
      if (success) {
        // Limpiar todo el trash
        setTrash([]);
      } else {
        throw new Error('Failed to empty trash');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error emptying trash';
      setError(errorMessage);
      console.error('Error emptying trash:', err);
      throw err;
    }
  }, []);

  /**
   * Analizar post (usando Gemini)
   */
  const analyzePost = useCallback(async (id: string) => {
    try {
      // Por ahora mantener funcionalidad Gemini del frontend
      // TODO: Integrar con el análisis del backend
      console.log('Analyzing post:', id);
    } catch (err) {
      console.error('Error analyzing post:', err);
      throw err;
    }
  }, []);

  /**
   * Reanalizar posts
   */
  const reanalyzePosts = useCallback(async (ids: string[]) => {
    try {
      setLoading(true);
      const success = await apiService.reanalyzeVideos(ids);
      
      if (success) {
        // Actualizar estado de procesamiento
        setPosts(prevPosts => 
          prevPosts.map(post => 
            ids.includes(post.id) 
              ? { ...post, processStatus: ProcessStatus.PROCESSING }
              : post
          )
        );
        
        // Opcionalmente recargar datos después de un tiempo
        setTimeout(() => {
          refreshData();
        }, 5000);
      } else {
        throw new Error('Failed to reanalyze videos');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error reanalyzing videos';
      setError(errorMessage);
      console.error('Error reanalyzing posts:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [refreshData]);

  /**
   * Obtener estadísticas (basadas en posts cargados + información de total de la BD)
   */
  const getStats = useCallback(() => {
    return {
      total: posts.length, // Videos cargados actualmente
      totalInDB: totalVideos, // Total en la base de datos
      withMusic: posts.filter(p => p.music).length,
      withCharacters: posts.filter(p => p.characters && p.characters.length > 0).length,
      processed: posts.filter(p => p.processStatus === ProcessStatus.COMPLETED).length,
      inTrash: trash.length,
      pending: posts.filter(p => p.processStatus === ProcessStatus.PENDING).length,
    };
  }, [posts, trash, totalVideos]);

  /**
   * Obtener creador por nombre
   */
  const getCreatorByName = useCallback((name: string) => {
    return creators.find(c => c.name === name);
  }, [creators]);

  /**
   * Estados para infinite scroll en otras páginas
   */
  const [creatorScrollData, setCreatorScrollData] = useState<{[key: string]: {posts: Post[], offset: number, hasMore: boolean, loading: boolean, initialLoaded: boolean}}>({});
  const [subscriptionScrollData, setSubscriptionScrollData] = useState<{[key: string]: {posts: Post[], offset: number, hasMore: boolean, loading: boolean, initialLoaded: boolean}}>({});

  /**
   * Obtener posts por creador (con infinite scroll)
   */
  const getPostsByCreator = useCallback(async (creatorName: string, platform?: Platform, listId?: string) => {
    try {
      // Usar API del backend para obtener todos los videos del creador sin límite
      const { posts: creatorPosts } = await apiService.getCreatorVideos(
        creatorName, 
        platform, 
        listId,
        0, // Sin límite
        0  // Sin offset
      );
      return creatorPosts;
    } catch (error) {
      console.error('Error fetching creator posts from API, falling back to local data:', error);
      // Fallback: filtrar desde posts locales
      return posts.filter(post => {
        const matchesCreator = post.creator === creatorName;
        const matchesPlatform = !platform || post.platform === platform;
        return matchesCreator && matchesPlatform;
      });
    }
  }, [posts]);

  /**
   * Cargar posts iniciales de creador con infinite scroll
   */
  const loadCreatorPosts = useCallback(async (creatorName: string, platform?: Platform, listId?: string) => {
    const key = `${creatorName}-${platform || 'all'}-${listId || 'all'}`;

    if (creatorScrollData[key]?.loading) return creatorScrollData[key].posts;

    setCreatorScrollData(prev => ({ ...prev, [key]: { posts: [], offset: 0, hasMore: true, loading: true, initialLoaded: false } }));

    try {
      const PAGE_SIZE = 50;
      const { posts: creatorPosts, hasMore: backendHasMore } = await apiService.getCreatorVideos(creatorName, platform, listId, PAGE_SIZE, 0);
      setCreatorScrollData(prev => ({ ...prev, [key]: { posts: creatorPosts, offset: PAGE_SIZE, hasMore: backendHasMore, loading: false, initialLoaded: true } }));
      return creatorPosts;
    } catch (error) {
      console.error('Error loading creator posts:', error);
      setCreatorScrollData(prev => ({ ...prev, [key]: { posts: [], offset: 0, hasMore: false, loading: false, initialLoaded: true } }));
      return [];
    }
  }, [creatorScrollData]);

  /**
   * Cargar más posts de creador (infinite scroll)
   */
  const loadMoreCreatorPosts = useCallback(async (creatorName: string, platform?: Platform, listId?: string) => {
    const key = `${creatorName}-${platform || 'all'}-${listId || 'all'}`;
    const currentData = creatorScrollData[key];

    if (!currentData || currentData.loading || !currentData.hasMore) return;

    setCreatorScrollData(prev => ({ ...prev, [key]: { ...currentData, loading: true } }));

    try {
      const PAGE_SIZE = 50;
      const { posts: newPosts, hasMore: backendHasMore } = await apiService.getCreatorVideos(creatorName, platform, listId, PAGE_SIZE, currentData.offset);
      
      setCreatorScrollData(prev => {
        const currentScrollData = prev[key];
        if (!currentScrollData) return prev;
        
        // Concatenación simple como en galería - MANTENER REFERENCIA DEL OBJETO
        const existingIds = new Set(currentScrollData.posts.map(p => p.id));
        const uniqueNewPosts = newPosts.filter(p => !existingIds.has(p.id));

        return { 
          ...prev, 
          [key]: { 
            ...currentScrollData,  // Mantener referencia del objeto existente
            posts: [...currentScrollData.posts, ...uniqueNewPosts], // Concatenación simple
            offset: currentScrollData.offset + PAGE_SIZE,
            hasMore: backendHasMore, // Usar hasMore del backend
            loading: false
          } 
        };
      });

    } catch (error) {
      console.error('Error loading more creator posts:', error);
      setCreatorScrollData(prev => ({ ...prev, [key]: { ...currentData, loading: false } }));
    }
  }, [creatorScrollData]);

  /**
   * Obtener datos de scroll de creador
   */
  const getCreatorScrollData = useCallback((creatorName: string, platform?: Platform, listId?: string) => {
    const key = `${creatorName}-${platform || 'all'}-${listId || 'all'}`;
    const currentData = creatorScrollData[key];
    if (!currentData) {
      return { posts: [], offset: 0, hasMore: true, loading: true, initialLoaded: false };
    }
    return currentData;
  }, [creatorScrollData]);

  /**
   * Obtener información de suscripción desde el backend
   */
  const getSubscriptionInfo = useCallback(async (type: SubscriptionType, id: string): Promise<SubscriptionInfo | undefined> => {
    try {
      const subscriptionInfo = await apiService.getSubscriptionInfo(type, id);
      return subscriptionInfo || undefined;
    } catch (error) {
      console.error('Error getting subscription info:', error);
      
      // Fallback: crear información básica desde posts locales
      return {
        id: id,
        type: type,
        name: type === 'playlist' ? 'Lista de Reproducción' : type.replace('_', ' ').replace(/^\w/, c => c.toUpperCase()),
        platform: 'youtube' as any,
        postCount: posts.filter(p => p.subscription?.id === id).length,
        creator: undefined,
        url: undefined
      };
    }
  }, [posts]);

  /**
   * Obtener estadísticas de suscripción desde el backend
   */
  const getSubscriptionStats = useCallback(async (type: SubscriptionType, id: number) => {
    try {
      const stats = await apiService.getSubscriptionStats(type, id);
      return stats;
    } catch (error) {
      console.error('Error getting subscription stats:', error);
      return null;
    }
  }, []);

  /**
   * Cargar posts iniciales de suscripción con infinite scroll
   */
  const loadSubscriptionPosts = useCallback(async (type: SubscriptionType, id: number, list?: string) => {
    const key = `${type}-${id}-${list || 'all'}`;

    if (subscriptionScrollData[key]?.loading) return subscriptionScrollData[key].posts;

    setSubscriptionScrollData(prev => ({ ...prev, [key]: { posts: [], offset: 0, hasMore: true, loading: true, initialLoaded: false } }));

    try {
      const PAGE_SIZE = 50;
      const { posts: subscriptionPosts, hasMore: backendHasMore } = await apiService.getSubscriptionVideos(type, id, list, PAGE_SIZE, 0);
      setSubscriptionScrollData(prev => ({ ...prev, [key]: { posts: subscriptionPosts, offset: PAGE_SIZE, hasMore: backendHasMore, loading: false, initialLoaded: true } }));
      return subscriptionPosts;
    } catch (error) {
      console.error('Error loading subscription posts:', error);
      setSubscriptionScrollData(prev => ({ ...prev, [key]: { posts: [], offset: 0, hasMore: false, loading: false, initialLoaded: true } }));
      return [];
    }
  }, [subscriptionScrollData]);

  /**
   * Cargar más posts de suscripción (infinite scroll)
   */
  const loadMoreSubscriptionPosts = useCallback(async (type: SubscriptionType, id: number, list?: string) => {
    const key = `${type}-${id}-${list || 'all'}`;
    const currentData = subscriptionScrollData[key];

    if (!currentData || currentData.loading || !currentData.hasMore) return;

    setSubscriptionScrollData(prev => ({ ...prev, [key]: { ...currentData, loading: true } }));

    try {
      const PAGE_SIZE = 50;
      const { posts: newPosts, hasMore: backendHasMore } = await apiService.getSubscriptionVideos(type, id, list, PAGE_SIZE, currentData.offset);

      setSubscriptionScrollData(prev => {
        const currentScrollData = prev[key];
        if (!currentScrollData) return prev;
        
        // Concatenación simple como en galería - MANTENER REFERENCIA DEL OBJETO
        const existingIds = new Set(currentScrollData.posts.map(p => p.id));
        const uniqueNewPosts = newPosts.filter(p => !existingIds.has(p.id));

        return { 
          ...prev, 
          [key]: { 
            ...currentScrollData,  // Mantener referencia del objeto existente
            posts: [...currentScrollData.posts, ...uniqueNewPosts], // Concatenación simple
            offset: currentScrollData.offset + PAGE_SIZE,
            hasMore: backendHasMore, // Usar hasMore del backend
            loading: false
          } 
        };
      });

    } catch (error) {
      console.error('Error loading more subscription posts:', error);
      setSubscriptionScrollData(prev => ({ ...prev, [key]: { ...currentData, loading: false } }));
    }
  }, [subscriptionScrollData]);

  /**
   * Obtener datos de scroll de suscripción
   */
  const getSubscriptionScrollData = useCallback((type: SubscriptionType, id: number, list?: string) => {
    const key = `${type}-${id}-${list || 'all'}`;
    const currentData = subscriptionScrollData[key];

    if (!currentData) {
      return { posts: [], offset: 0, hasMore: true, loading: true, initialLoaded: false };
    }

    return currentData;
  }, [subscriptionScrollData]);

  /**
   * Limpiar datos de scroll específicos
   */
  

  /**
   * Limpiar todos los datos de scroll para permitir recarga
   */
  

  /**
   * Obtener posts por suscripción desde el backend (legacy, mantener para compatibilidad)
   */
  const getPostsBySubscription = useCallback(async (type: SubscriptionType, id: string, list?: string): Promise<Post[]> => {
    try {
      // Obtener todos los posts sin límite para páginas de suscripción
      const { posts: subscriptionPosts } = await apiService.getSubscriptionVideos(type, id, list, 0); // 0 = sin límite
      return subscriptionPosts;
    } catch (error) {
      console.error('Error getting subscription posts:', error);
      
      // Fallback: filtrar desde posts locales
      let filteredPosts = posts;
      
      // Filtrar por suscripción
      if (type && id) {
        filteredPosts = posts.filter(post => {
          if (!post.subscription) return false;
          return post.subscription.type === type && (post.subscription.id === id || post.subscription.name === id);
        });
      }
      
      // Filtrar por lista específica si se proporciona
      if (list && list !== 'all') {
        filteredPosts = filteredPosts.filter(post => {
          if (!post.lists || post.lists.length === 0) return false;
          return post.lists.some(l => l.type === list || l.name === list);
        });
      }
      
      return filteredPosts;
    }
  }, [posts]);

  // 🚫 TEMPORAL: Deshabilitada carga automática para evitar conflicto con cursor pagination
  // const initialLoadRef = useRef(false);
  // useEffect(() => {
  //   if (!initialLoadRef.current) {
  //     initialLoadRef.current = true;
  //     refreshData();
  //   }
  // }, []); // Solo cargar una vez al montar

  const contextValue: RealDataContextType = useMemo(() => ({
    posts,
    trash,
    creators,
    loading,
    loadingMore,
    hasMore,
    error,
    refreshData,
    loadVideos,
    loadMoreVideos,
    loadTrashVideos,
    updatePost,
    updateMultiplePosts,
    moveToTrash,
    moveMultipleToTrash,
    restoreFromTrash,
    restoreMultipleFromTrash,
    deletePermanently,
    emptyTrash,
    analyzePost,
    reanalyzePosts,
    getStats,
    getCreatorByName,
    getPostsByCreator,
    getSubscriptionInfo,
    getSubscriptionStats,
    getPostsBySubscription,
    // Nuevas funciones para infinite scroll en otras páginas
    loadCreatorPosts,
    loadMoreCreatorPosts,
    getCreatorScrollData,
    loadSubscriptionPosts,
    loadMoreSubscriptionPosts,
    getSubscriptionScrollData,
    

  }), [
    posts,
    trash,
    creators,
    loading,
    loadingMore,
    hasMore,
    error,
    refreshData,
    loadVideos,
    loadMoreVideos,
    loadTrashVideos,
    updatePost,
    updateMultiplePosts,
    moveToTrash,
    moveMultipleToTrash,
    restoreFromTrash,
    restoreMultipleFromTrash,
    deletePermanently,
    emptyTrash,
    analyzePost,
    reanalyzePosts,
    getStats,
    getCreatorByName,
    getPostsByCreator,
    getSubscriptionInfo,
    getSubscriptionStats,
    getPostsBySubscription,
    loadCreatorPosts,
    loadMoreCreatorPosts,
    getCreatorScrollData,
    loadSubscriptionPosts,
    loadMoreSubscriptionPosts,
    getSubscriptionScrollData,
  ]);

  return (
    <RealDataContext.Provider value={contextValue}>
      {children}
    </RealDataContext.Provider>
  );
};

/**
 * @deprecated Este hook está obsoleto. Use los hooks específicos del sistema cursor:
 * - useCursorData: Para datos de galería principal
 * - useCursorCreatorData: Para datos de creadores específicos
 * - useCursorSubscriptionData: Para datos de suscripciones
 * - useCursorTrashData: Para datos de papelera
 * - useCursorCRUD: Para operaciones CRUD (crear, actualizar, eliminar)
 */
export const useRealData = (): RealDataContextType => {
  const context = useContext(RealDataContext);
  if (!context) {
    throw new Error('useRealData must be used within a RealDataProvider');
  }
  return context;
};