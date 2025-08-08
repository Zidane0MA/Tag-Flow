/**
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
  getSubscriptionStats: (type: SubscriptionType, id: string) => Promise<any>;
  // Nuevas funciones para infinite scroll
  loadCreatorPosts: (creatorName: string, platform?: Platform, listId?: string) => Promise<Post[]>;
  loadMoreCreatorPosts: (creatorName: string, platform?: Platform, listId?: string) => Promise<void>;
  getCreatorScrollData: (creatorName: string, platform?: Platform, listId?: string) => {posts: Post[], offset: number, hasMore: boolean, loading: boolean, initialLoaded: boolean};
  loadSubscriptionPosts: (type: SubscriptionType, id: string, list?: string) => Promise<Post[]>;
  loadMoreSubscriptionPosts: (type: SubscriptionType, id: string, list?: string) => Promise<void>;
  getSubscriptionScrollData: (type: SubscriptionType, id: string, list?: string) => {posts: Post[], offset: number, hasMore: boolean, loading: boolean, initialLoaded: boolean};
  clearScrollData: () => void;
  clearCreatorScrollData: (creatorName: string, platform?: Platform, listId?: string) => void;
  clearSubscriptionScrollData: (type: SubscriptionType, id: string, list?: string) => void;
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
    // Solo recalcular si cambió algo relevante
    if (backendCreators.length > 0 && lastBackendCreatorsLengthRef.current !== backendCreators.length) {
      lastBackendCreatorsLengthRef.current = backendCreators.length;
      creatorsRef.current = backendCreators;
      return backendCreators;
    }
    
    // Solo recalcular si cambió la longitud de posts (nuevos posts agregados)
    if (lastPostsLengthRef.current === posts.length && creatorsRef.current.length > 0) {
      return creatorsRef.current;
    }
    
    lastPostsLengthRef.current = posts.length;
    
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
  }, [posts.length, backendCreators.length]); // Solo depender de longitudes, no del array completo

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
      
      const { posts: newPosts, total } = await apiService.getVideos(filtersWithPagination);
      
      setPosts(newPosts);
      setCurrentFilters(filters);
      setCurrentOffset(PAGE_SIZE);
      setTotalVideos(total);
      setHasMore(newPosts.length === PAGE_SIZE && newPosts.length < total);
      
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
        offset: currentOffset
      };
      
      const { posts: newPosts, total } = await apiService.getVideos(filtersWithPagination);
      
      setPosts(prevPosts => {
        // Evitar duplicados basándose en el ID
        const existingIds = new Set(prevPosts.map(p => p.id));
        const uniqueNewPosts = newPosts.filter(p => !existingIds.has(p.id));
        return [...prevPosts, ...uniqueNewPosts];
      });
      
      const newOffset = currentOffset + PAGE_SIZE;
      setCurrentOffset(newOffset);
      setTotalVideos(total);
      
      const hasMoreVideos = newPosts.length === PAGE_SIZE && newOffset < total;
      setHasMore(hasMoreVideos);
      
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
      
      const [{ posts: newPosts, total }, creatorsData] = await Promise.all([
        apiService.getVideos(filtersWithPagination),
        apiService.getCreators()
      ]);
      
      setPosts(newPosts);
      setCurrentFilters({});
      setCurrentOffset(PAGE_SIZE);
      setTotalVideos(total);
      setHasMore(newPosts.length === PAGE_SIZE && newPosts.length < total);
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
   * Restaurar desde trash (por implementar en backend)
   */
  const restoreFromTrash = useCallback(async (id: string) => {
    // TODO: Implementar cuando el backend tenga restore endpoint
    console.warn('Restore from trash not implemented yet');
  }, []);

  /**
   * Eliminar permanentemente (por implementar en backend)
   */
  const deletePermanently = useCallback(async (id: string) => {
    // TODO: Implementar cuando el backend tenga delete permanente
    console.warn('Permanent delete not implemented yet');
  }, []);

  /**
   * Vaciar trash (por implementar en backend)
   */
  const emptyTrash = useCallback(async () => {
    // TODO: Implementar cuando el backend tenga empty trash
    console.warn('Empty trash not implemented yet');
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
  
  // Referencias para controlar si los datos ya fueron cargados para una key específica
  const creatorDataLoadedRef = useRef<Set<string>>(new Set());
  const subscriptionDataLoadedRef = useRef<Set<string>>(new Set());
  
  // Referencias para mantener siempre los datos más actuales sin causar re-renders
  const creatorScrollDataRef = useRef(creatorScrollData);
  const subscriptionScrollDataRef = useRef(subscriptionScrollData);
  
  // Mantener refs actualizadas
  creatorScrollDataRef.current = creatorScrollData;
  subscriptionScrollDataRef.current = subscriptionScrollData;

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
    
    // Solo cargar si no se han cargado datos para esta key antes
    if (creatorDataLoadedRef.current.has(key)) {
      // Asegurar que el estado tenga initialLoaded = true si ya se cargó antes
      setCreatorScrollData(prev => {
        const existing = prev[key];
        if (existing && !existing.initialLoaded) {
          return {
            ...prev,
            [key]: { ...existing, initialLoaded: true }
          };
        }
        return prev;
      });
      
      return creatorScrollDataRef.current[key]?.posts || [];
    }
    
    // Marcar como cargado ANTES de hacer la petición para prevenir dobles llamadas
    creatorDataLoadedRef.current.add(key);
    
    try {
      const PAGE_SIZE = 50;
      const { posts: creatorPosts } = await apiService.getCreatorVideos(
        creatorName, 
        platform, 
        listId,
        PAGE_SIZE,
        0
      );
      
      setCreatorScrollData(prev => ({
        ...prev,
        [key]: {
          posts: creatorPosts,
          offset: PAGE_SIZE,
          hasMore: creatorPosts.length === PAGE_SIZE,
          loading: false,
          initialLoaded: true
        }
      }));
      
      return creatorPosts;
    } catch (error) {
      console.error('Error loading creator posts:', error);
      setCreatorScrollData(prev => ({
        ...prev,
        [key]: {
          posts: [],
          offset: 0,
          hasMore: false,
          loading: false,
          initialLoaded: true
        }
      }));
      return [];
    }
  }, []);

  /**
   * Cargar más posts de creador (infinite scroll)
   */
  const loadMoreCreatorPosts = useCallback(async (creatorName: string, platform?: Platform, listId?: string) => {
    const key = `${creatorName}-${platform || 'all'}-${listId || 'all'}`;
    
    // Get current scroll data from ref
    const currentScrollData = creatorScrollDataRef.current[key];
    
    if (!currentScrollData || currentScrollData.loading || !currentScrollData.hasMore) {
      return;
    }

    // Set loading state
    setCreatorScrollData(prev => ({
      ...prev,
      [key]: { ...currentScrollData, loading: true }
    }));

    try {
      const PAGE_SIZE = 50;
      const { posts: newPosts } = await apiService.getCreatorVideos(
        creatorName, 
        platform, 
        listId,
        PAGE_SIZE,
        currentScrollData.offset
      );
      
      // Preservar posición de scroll antes de la actualización
      const scrollContainer = document.querySelector('.flex-1.overflow-y-auto') || document.querySelector('main') || window;
      const currentScrollTop = scrollContainer === window ? window.scrollY : (scrollContainer as Element).scrollTop;
      
      setCreatorScrollData(prev => {
        const scrollData = prev[key];
        if (!scrollData) return prev;
        
        // Evitar duplicados al combinar posts
        const existingIds = new Set(scrollData.posts.map(p => p.id));
        const uniqueNewPosts = newPosts.filter(p => !existingIds.has(p.id));
        
        return {
          ...prev,
          [key]: {
            posts: [...scrollData.posts, ...uniqueNewPosts],
            offset: scrollData.offset + PAGE_SIZE,
            hasMore: newPosts.length === PAGE_SIZE,
            loading: false,
            initialLoaded: true
          }
        };
      });
      
      // Restaurar posición de scroll después de la actualización
      requestAnimationFrame(() => {
        if (scrollContainer === window) {
          window.scrollTo(0, currentScrollTop);
        } else {
          (scrollContainer as Element).scrollTop = currentScrollTop;
        }
      });
      
    } catch (error) {
      console.error('Error loading more creator posts:', error);
      setCreatorScrollData(prev => ({
        ...prev,
        [key]: prev[key] ? { ...prev[key], loading: false } : prev[key]
      }));
    }
  }, []);

  /**
   * Obtener datos de scroll de creador
   */
  const getCreatorScrollData = useCallback((creatorName: string, platform?: Platform, listId?: string) => {
    const key = `${creatorName}-${platform || 'all'}-${listId || 'all'}`;
    
    // Obtener datos actuales desde la ref para evitar re-renders
    const currentData = creatorScrollDataRef.current[key];
    
    
    // Si no hay datos y no se han cargado antes, mostrar como cargando inicialmente
    if (!currentData && !creatorDataLoadedRef.current.has(key)) {
      return { posts: [], offset: 0, hasMore: true, loading: true, initialLoaded: false };
    }
    
    return currentData || { posts: [], offset: 0, hasMore: true, loading: false, initialLoaded: false };
  }, []); // SIN DEPENDENCIAS - usar ref para datos actuales

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
  const getSubscriptionStats = useCallback(async (type: SubscriptionType, id: string) => {
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
  const loadSubscriptionPosts = useCallback(async (type: SubscriptionType, id: string, list?: string) => {
    const key = `${type}-${id}-${list || 'all'}`;
    
    // Solo cargar si no se han cargado datos para esta key antes
    if (subscriptionDataLoadedRef.current.has(key)) {
      // Asegurar que el estado tenga initialLoaded = true si ya se cargó antes
      setSubscriptionScrollData(prev => {
        const existing = prev[key];
        if (existing && !existing.initialLoaded) {
          return {
            ...prev,
            [key]: { ...existing, initialLoaded: true }
          };
        }
        return prev;
      });
      
      return subscriptionScrollDataRef.current[key]?.posts || [];
    }
    
    // Marcar como cargado ANTES de hacer la petición para prevenir dobles llamadas
    subscriptionDataLoadedRef.current.add(key);
    
    try {
      const PAGE_SIZE = 50;
      const { posts: subscriptionPosts } = await apiService.getSubscriptionVideos(type, id, list, PAGE_SIZE, 0);
      
      setSubscriptionScrollData(prev => ({
        ...prev,
        [key]: {
          posts: subscriptionPosts,
          offset: PAGE_SIZE,
          hasMore: subscriptionPosts.length === PAGE_SIZE,
          loading: false,
          initialLoaded: true
        }
      }));
      
      return subscriptionPosts;
    } catch (error) {
      console.error('Error loading subscription posts:', error);
      setSubscriptionScrollData(prev => ({
        ...prev,
        [key]: {
          posts: [],
          offset: 0,
          hasMore: false,
          loading: false,
          initialLoaded: true
        }
      }));
      return [];
    }
  }, []);

  /**
   * Cargar más posts de suscripción (infinite scroll)
   */
  const loadMoreSubscriptionPosts = useCallback(async (type: SubscriptionType, id: string, list?: string) => {
    const key = `${type}-${id}-${list || 'all'}`;
    
    // Get current scroll data from ref
    const currentScrollData = subscriptionScrollDataRef.current[key];
    
    if (!currentScrollData || currentScrollData.loading || !currentScrollData.hasMore) {
      return;
    }

    // Set loading state
    setSubscriptionScrollData(prev => ({
      ...prev,
      [key]: { ...currentScrollData, loading: true }
    }));

    try {
      const PAGE_SIZE = 50;
      const { posts: newPosts } = await apiService.getSubscriptionVideos(type, id, list, PAGE_SIZE, currentScrollData.offset);
      
      // Preservar posición de scroll antes de la actualización
      const scrollContainer = document.querySelector('.flex-1.overflow-y-auto') || document.querySelector('main') || window;
      const currentScrollTop = scrollContainer === window ? window.scrollY : (scrollContainer as Element).scrollTop;
      
      setSubscriptionScrollData(prev => {
        const scrollData = prev[key];
        if (!scrollData) return prev;
        
        // Evitar duplicados al combinar posts
        const existingIds = new Set(scrollData.posts.map(p => p.id));
        const uniqueNewPosts = newPosts.filter(p => !existingIds.has(p.id));
        
        return {
          ...prev,
          [key]: {
            posts: [...scrollData.posts, ...uniqueNewPosts],
            offset: scrollData.offset + PAGE_SIZE,
            hasMore: newPosts.length === PAGE_SIZE,
            loading: false,
            initialLoaded: true
          }
        };
      });
      
      // Restaurar posición de scroll después de la actualización
      requestAnimationFrame(() => {
        if (scrollContainer === window) {
          window.scrollTo(0, currentScrollTop);
        } else {
          (scrollContainer as Element).scrollTop = currentScrollTop;
        }
      });
      
    } catch (error) {
      console.error('Error loading more subscription posts:', error);
      setSubscriptionScrollData(prev => ({
        ...prev,
        [key]: prev[key] ? { ...prev[key], loading: false } : prev[key]
      }));
    }
  }, []);

  /**
   * Obtener datos de scroll de suscripción
   */
  const getSubscriptionScrollData = useCallback((type: SubscriptionType, id: string, list?: string) => {
    const key = `${type}-${id}-${list || 'all'}`;
    
    // Obtener datos actuales desde la ref para evitar re-renders
    const currentData = subscriptionScrollDataRef.current[key];
    
    
    // Si no hay datos y no se han cargado antes, mostrar como cargando inicialmente
    if (!currentData && !subscriptionDataLoadedRef.current.has(key)) {
      return { posts: [], offset: 0, hasMore: true, loading: true, initialLoaded: false };
    }
    
    return currentData || { posts: [], offset: 0, hasMore: true, loading: false, initialLoaded: false };
  }, []); // SIN DEPENDENCIAS - usar ref para datos actuales

  /**
   * Limpiar datos de scroll específicos
   */
  const clearCreatorScrollData = useCallback((creatorName: string, platform?: Platform, listId?: string) => {
    const key = `${creatorName}-${platform || 'all'}-${listId || 'all'}`;
    creatorDataLoadedRef.current.delete(key);
    setCreatorScrollData(prev => {
      const newData = { ...prev };
      delete newData[key];
      return newData;
    });
  }, []);

  const clearSubscriptionScrollData = useCallback((type: SubscriptionType, id: string, list?: string) => {
    const key = `${type}-${id}-${list || 'all'}`;
    subscriptionDataLoadedRef.current.delete(key);
    setSubscriptionScrollData(prev => {
      const newData = { ...prev };
      delete newData[key];
      return newData;
    });
  }, []);

  /**
   * Limpiar todos los datos de scroll para permitir recarga
   */
  const clearScrollData = useCallback(() => {
    creatorDataLoadedRef.current.clear();
    subscriptionDataLoadedRef.current.clear();
    setCreatorScrollData({});
    setSubscriptionScrollData({});
  }, []);

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

  // Cargar datos iniciales
  const initialLoadRef = useRef(false);
  useEffect(() => {
    if (!initialLoadRef.current) {
      initialLoadRef.current = true;
      refreshData();
    }
  }, []); // Solo cargar una vez al montar

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
    getSubscriptionStats,
    getPostsBySubscription,
    // Nuevas funciones para infinite scroll en otras páginas
    loadCreatorPosts,
    loadMoreCreatorPosts,
    getCreatorScrollData,
    loadSubscriptionPosts,
    loadMoreSubscriptionPosts,
    getSubscriptionScrollData,
    clearScrollData,
    clearCreatorScrollData,
    clearSubscriptionScrollData,
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
    getSubscriptionStats,
    getPostsBySubscription,
    loadCreatorPosts,
    loadMoreCreatorPosts,
    getCreatorScrollData,
    loadSubscriptionPosts,
    loadMoreSubscriptionPosts,
    getSubscriptionScrollData,
    clearScrollData,
    clearCreatorScrollData,
    clearSubscriptionScrollData,
  ]);

  return (
    <RealDataContext.Provider value={contextValue}>
      {children}
    </RealDataContext.Provider>
  );
};

export const useRealData = (): RealDataContextType => {
  const context = useContext(RealDataContext);
  if (!context) {
    throw new Error('useRealData must be used within a RealDataProvider');
  }
  return context;
};