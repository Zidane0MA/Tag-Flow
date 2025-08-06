/**
 * Hook para manejar datos reales del backend
 * Reemplaza useMockData con conexión real a la API
 */

import React, { createContext, useState, useContext, useCallback, useEffect } from 'react';
import { Post, Platform, EditStatus, ProcessStatus, Difficulty, DataContextType, Creator, SubscriptionInfo, SubscriptionType } from '../types';
import { apiService, VideoFilters } from '../services/apiService';

interface RealDataContextType extends DataContextType {
  loading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
  loadVideos: (filters?: VideoFilters) => Promise<void>;
}

const RealDataContext = createContext<RealDataContextType | undefined>(undefined);

export const RealDataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Estados principales
  const [posts, setPosts] = useState<Post[]>([]);
  const [trash, setTrash] = useState<Post[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Estados para creadores y suscripciones
  const [backendCreators, setBackendCreators] = useState<Creator[]>([]);
  
  // Estados derivados que se calculan de los posts
  const creators = React.useMemo(() => {
    // Si tenemos creadores desde el backend, usarlos
    if (backendCreators.length > 0) {
      return backendCreators;
    }
    
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

    return Array.from(creatorsMap.entries()).map(([creatorName, platforms]) => ({
      name: creatorName,
      displayName: creatorName,
      platforms
    }));
  }, [posts, backendCreators]);

  /**
   * Cargar videos desde el backend
   */
  const loadVideos = useCallback(async (filters: VideoFilters = {}) => {
    setLoading(true);
    setError(null);
    try {
      // Solicitar un límite alto para mostrar todos los videos disponibles
      const filtersWithLimit = { ...filters, limit: filters.limit || 1500 };
      const { posts: newPosts } = await apiService.getVideos(filtersWithLimit);
      setPosts(newPosts);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error loading videos';
      setError(errorMessage);
      console.error('Error loading videos:', err);
    } finally {
      setLoading(false);
    }
  }, []);

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
   * Refrescar todos los datos
   */
  const refreshData = useCallback(async () => {
    await Promise.all([
      loadVideos(),
      loadCreators()
    ]);
  }, [loadVideos, loadCreators]);

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
   * Obtener estadísticas
   */
  const getStats = useCallback(() => {
    return {
      total: posts.length,
      withMusic: posts.filter(p => p.music).length,
      withCharacters: posts.filter(p => p.characters && p.characters.length > 0).length,
      processed: posts.filter(p => p.processStatus === ProcessStatus.COMPLETED).length,
      inTrash: trash.length,
      pending: posts.filter(p => p.processStatus === ProcessStatus.PENDING).length,
    };
  }, [posts, trash]);

  /**
   * Obtener creador por nombre
   */
  const getCreatorByName = useCallback((name: string) => {
    return creators.find(c => c.name === name);
  }, [creators]);

  /**
   * Obtener posts por creador
   */
  const getPostsByCreator = useCallback(async (creatorName: string, platform?: Platform, listId?: string) => {
    try {
      // Usar API del backend para obtener videos del creador
      const { posts: creatorPosts } = await apiService.getCreatorVideos(
        creatorName, 
        platform, 
        listId
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
   * Obtener información de suscripción (placeholder)
   */
  const getSubscriptionInfo = useCallback((type: SubscriptionType, id: string): SubscriptionInfo | undefined => {
    // TODO: Implementar cuando tengamos sistema de suscripciones en backend
    return undefined;
  }, []);

  /**
   * Obtener posts por suscripción (placeholder)
   */
  const getPostsBySubscription = useCallback((type: SubscriptionType, id: string, list?: string) => {
    // TODO: Implementar cuando tengamos sistema de suscripciones en backend
    return [];
  }, []);

  // Cargar datos iniciales
  useEffect(() => {
    refreshData();
  }, [refreshData]);

  const contextValue: RealDataContextType = {
    posts,
    trash,
    creators,
    loading,
    error,
    refreshData,
    loadVideos,
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
  };

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