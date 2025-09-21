/**
 * Tag-Flow V2 - Cursor Data Hook
 * React hook para cursor pagination que reemplaza useRealData
 */

import React, { createContext, useState, useContext, useCallback, useEffect, useRef } from 'react';
import { Post, Platform, Creator } from '../types';
import { cursorApiService } from '../services/pagination/cursorApiService';
import {
  CursorPaginationParams,
  FilterParams,
  ScrollState,
  CursorDataState
} from '../services/pagination/types';
import { useCursorWebSocketSync } from './useWebSocketUpdates';
import { useCursorWithPrefetch } from './usePrefetch';
import { cacheManager } from '../services/unifiedCacheManager';

interface CursorDataContextType {
  // Data
  posts: Post[];
  creators: Creator[];
  loading: boolean;
  loadingMore: boolean;
  error: string | null;

  // Pagination state
  scrollState: ScrollState;
  filters: FilterParams;

  // Core methods
  loadVideos: (newFilters?: FilterParams) => Promise<void>;
  loadMoreVideos: () => Promise<void>;
  refreshData: () => Promise<void>;
  clearData: () => void;

  // Filter management
  setFilters: (filters: FilterParams, sortBy?: string, sortOrder?: 'asc' | 'desc') => Promise<void>;
  clearFilters: () => void;

  // Performance & cache
  getPerformanceStats: () => Promise<any>;
  invalidateCache: () => Promise<void>;

  // Statistics
  getStats: () => {
    total: number;
    loaded: number;
    hasMore: boolean;
    performance: {
      avgQueryTime: number;
      cacheHitRate: number;
      totalQueries: number;
    };
  };
}

const CursorDataContext = createContext<CursorDataContextType | undefined>(undefined);

export const CursorDataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Core state
  const [posts, setPosts] = useState<Post[]>([]);
  const [creators, setCreators] = useState<Creator[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pagination state
  const [scrollState, setScrollState] = useState<ScrollState>({
    hasMore: true,
    loading: false,
    initialLoaded: false
  });

  const [filters, setFiltersState] = useState<FilterParams>({});

  // Performance tracking
  const [performanceStats, setPerformanceStats] = useState({
    avgQueryTime: 0,
    cacheHitRate: 0,
    totalQueries: 0
  });

  // Refs para evitar re-renders innecesarios
  const currentFiltersRef = useRef<FilterParams>({});
  const abortControllerRef = useRef<AbortController | null>(null);

  // Create data loader for prefetching
  const cursorDataLoader = useCallback(async (cursor?: string) => {
    const result = await cursorApiService.getVideosCursor({
      filters: currentFiltersRef.current,
      cursor,
      limit: 50
    });

    // Update performance stats
    setPerformanceStats(prev => ({
      avgQueryTime: (prev.avgQueryTime + result.performance.query_time_ms) / 2,
      cacheHitRate: result.performance.cache_hit ? 100 : prev.cacheHitRate,
      totalQueries: prev.totalQueries + 1
    }));

    return {
      data: result.data,
      cursor: result.pagination.next_cursor,
      hasMore: result.pagination.has_more,
      cached: false,
      timestamp: Date.now()
    };
  }, []);

  // Initialize prefetching - Configuración más agresiva
  const prefetch = useCursorWithPrefetch(cursorDataLoader, 'gallery-container', {
    threshold: 0.6,        // Activar prefetch al 60% del scroll (antes 80%)
    maxPrefetchPages: 5,   // Prefetch hasta 5 páginas (antes 3)
    enablePredictive: true,
    debounceMs: 100        // Reducir debounce para respuesta más rápida
  });

  /**
   * Load initial videos with filters
   */
  const loadVideos = useCallback(async (newFilters: FilterParams = {}) => {
    // Cancelar request anterior si existe
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    setLoading(true);
    setError(null);

    try {
      const effectiveFilters = { ...filters, ...newFilters };
      currentFiltersRef.current = effectiveFilters;

      const params: CursorPaginationParams = {
        cursor: undefined, // Primera carga sin cursor
        direction: 'next',
        limit: 50,
        filters: effectiveFilters,
        // Configurar ordenamiento por defecto: ID DESC
        sort_by: effectiveFilters.sort_by || 'id',
        sort_order: effectiveFilters.sort_order || 'desc'
      };

      const result = await cursorApiService.getVideosCursor(params);

      // Actualizar datos
      setPosts(result.data);
      setFiltersState(effectiveFilters);

      // Actualizar estado de scroll
      setScrollState({
        cursor: result.pagination.next_cursor,
        hasMore: result.pagination.has_more,
        loading: false,
        initialLoaded: true
      });

      // Actualizar stats de performance
      setPerformanceStats(prev => ({
        avgQueryTime: result.performance.query_time_ms,
        cacheHitRate: result.performance.cache_hit ? 100 : 0,
        totalQueries: prev.totalQueries + 1
      }));

      console.log(`✅ Loaded ${result.data.length} videos with cursor pagination in ${result.performance.query_time_ms}ms`);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error loading videos';
      setError(errorMessage);
      console.error('Error loading videos with cursor:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  /**
   * Load more videos (infinite scroll)
   */
  const loadMoreVideos = useCallback(async () => {
    if (loadingMore || !scrollState.hasMore) {
      console.log(`🛑 LoadMore blocked: loading=${loadingMore}, hasMore=${scrollState.hasMore}, cursor=${scrollState.cursor}`);
      return;
    }

    setLoadingMore(true);
    setError(null);

    try {
      // Check unified cache first, then prefetch
      const cacheKey = cacheManager.buildKey('cursor:videos', {
        cursor: scrollState.cursor,
        ...currentFiltersRef.current
      });

      console.log(`🔑 Cache key: ${cacheKey}, cursor: ${scrollState.cursor}`);

      let result: any;
      const cachedResult = cacheManager.get(cacheKey);

      if (cachedResult) {
        console.log('🚀 Using unified cache for loadMore');
        console.log(`📊 Cached data preview: ${cachedResult.data?.length} items, next_cursor: ${cachedResult.pagination?.next_cursor}`);

        // ⚠️ DETECCIÓN DE BUCLE INFINITO
        if (cachedResult.pagination?.next_cursor === scrollState.cursor) {
          console.error(`🚨 INFINITE LOOP DETECTED: next_cursor (${cachedResult.pagination?.next_cursor}) equals current cursor (${scrollState.cursor})`);
          console.log('🔄 Bypassing cache and fetching fresh data...');
          // Invalidar cache problemático
          cacheManager.invalidate(cacheKey);
        } else {
          result = cachedResult;
        }
      }

      // Si no hay resultado válido del cache, continuar con API/prefetch
      if (!result) {
        // Check if data is prefetched
        const prefetched = prefetch.getPrefetchedData(scrollState.cursor);

        if (prefetched) {
          console.log('🚀 Using prefetched data for loadMore');
          // Convert prefetched data to expected format
          result = {
            data: prefetched.data,
            pagination: {
              next_cursor: prefetched.cursor,
              has_more: prefetched.hasMore
            },
            performance: {
              query_time_ms: 0, // Instant from cache
              cache_hit_rate: 100
            }
          };

          // Store in unified cache too
          cacheManager.set(cacheKey, result, { category: 'cursor-results', source: 'prefetch' });
        } else {
          console.log('🚀 Loading more data from API');
          const params: CursorPaginationParams = {
            cursor: scrollState.cursor,
            direction: 'next',
            limit: 50,
            filters: currentFiltersRef.current,
            // Mantener ordenamiento consistente: ID DESC por defecto
            sort_by: currentFiltersRef.current.sort_by || 'id',
            sort_order: currentFiltersRef.current.sort_order || 'desc'
          };

          result = await cursorApiService.getVideosCursor(params);
        }
      }

      // Agregar nuevos posts (evitar duplicados)
      let uniqueNewPosts: any[] = [];
      setPosts(prevPosts => {
        const existingIds = new Set(prevPosts.map(p => p.id));
        uniqueNewPosts = result.data.filter(p => !existingIds.has(p.id));
        console.log(`🔍 Deduplication: ${result.data.length} received, ${uniqueNewPosts.length} unique, ${result.data.length - uniqueNewPosts.length} duplicates`);
        return [...prevPosts, ...uniqueNewPosts];
      });

      // Actualizar estado de scroll
      setScrollState(prev => ({
        ...prev,
        cursor: result.pagination.next_cursor,
        hasMore: result.pagination.has_more,
        loading: false
      }));

      console.log(`📊 Pagination state updated: cursor=${result.pagination.next_cursor}, hasMore=${result.pagination.has_more}`);

      // Actualizar stats
      setPerformanceStats(prev => ({
        avgQueryTime: (prev.avgQueryTime + result.performance.query_time_ms) / 2,
        cacheHitRate: result.performance.cache_hit ? 100 : prev.cacheHitRate,
        totalQueries: prev.totalQueries + 1
      }));

      // Update prefetch cursor for intelligent prefetching
      prefetch.updateCursor(result.pagination.next_cursor);

      console.log(`✅ Loaded ${uniqueNewPosts.length} NEW videos (${result.data.length} total received)`);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error loading more videos';
      setError(errorMessage);
      console.error('Error loading more videos:', err);
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, scrollState, posts.length, prefetch]);

  /**
   * Refresh data (reload from beginning)
   */
  const refreshData = useCallback(async () => {
    setScrollState(prev => ({ ...prev, cursor: undefined, hasMore: true }));
    await loadVideos(currentFiltersRef.current);
  }, [loadVideos]);

  // WebSocket integration for real-time updates (after refreshData is defined)
  useCursorWebSocketSync(refreshData);

  /**
   * Clear all data
   */
  const clearData = useCallback(() => {
    setPosts([]);
    setCreators([]);
    setScrollState({
      hasMore: true,
      loading: false,
      initialLoaded: false
    });
    setError(null);
  }, []);

  /**
   * Set filters and reload
   */
  const setFilters = useCallback(async (newFilters: FilterParams, sortBy?: string, sortOrder?: 'asc' | 'desc') => {
    // Agregar parámetros de ordenamiento si se proporcionan
    const filtersWithSort = {
      ...newFilters,
      ...(sortBy && { sort_by: sortBy }),
      ...(sortOrder && { sort_order: sortOrder })
    };

    setFiltersState(filtersWithSort);
    currentFiltersRef.current = filtersWithSort;
    await loadVideos(filtersWithSort);
  }, [loadVideos]);

  /**
   * Clear filters
   */
  const clearFilters = useCallback(async () => {
    const emptyFilters = {};
    setFiltersState(emptyFilters);
    currentFiltersRef.current = emptyFilters;
    await loadVideos(emptyFilters);
  }, [loadVideos]);

  /**
   * Get performance statistics
   */
  const getPerformanceStats = useCallback(async () => {
    try {
      return await cursorApiService.getPerformanceStats();
    } catch (error) {
      console.error('Error getting performance stats:', error);
      return null;
    }
  }, []);

  /**
   * Invalidate cache and refresh
   */
  const invalidateCache = useCallback(async () => {
    try {
      await cursorApiService.invalidateCache();
      await refreshData();
    } catch (error) {
      console.error('Error invalidating cache:', error);
    }
  }, [refreshData]);

  /**
   * Get current statistics
   */
  const getStats = useCallback(() => {
    // Include cache stats from unified cache manager
    const cacheStats = cacheManager.getStats();

    return {
      total: scrollState.initialLoaded ? posts.length : 0,
      loaded: posts.length,
      hasMore: scrollState.hasMore,
      performance: performanceStats,
      cache: {
        hitRate: cacheStats.hitRate,
        totalEntries: cacheStats.totalEntries,
        totalSizeBytes: cacheStats.totalSizeBytes,
        mostAccessed: cacheStats.mostAccessed
      }
    };
  }, [posts.length, scrollState, performanceStats]);

  // Auto-load on mount
  const initialLoadRef = useRef(false);
  useEffect(() => {
    if (!initialLoadRef.current) {
      initialLoadRef.current = true;
      loadVideos();
    }
  }, [loadVideos]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const contextValue: CursorDataContextType = {
    // Data
    posts,
    creators,
    loading,
    loadingMore,
    error,

    // Pagination state
    scrollState,
    filters,

    // Core methods
    loadVideos,
    loadMoreVideos,
    refreshData,
    clearData,

    // Filter management
    setFilters,
    clearFilters,

    // Performance & cache
    getPerformanceStats,
    invalidateCache,

    // Statistics
    getStats
  };

  return (
    <CursorDataContext.Provider value={contextValue}>
      {children}
    </CursorDataContext.Provider>
  );
};

export const useCursorData = (): CursorDataContextType => {
  const context = useContext(CursorDataContext);
  if (!context) {
    throw new Error('useCursorData must be used within a CursorDataProvider');
  }
  return context;
};