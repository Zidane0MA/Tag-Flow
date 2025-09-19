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
  setFilters: (filters: FilterParams) => void;
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
        filters: effectiveFilters
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
    if (loadingMore || !scrollState.hasMore || !scrollState.cursor) {
      return;
    }

    setLoadingMore(true);
    setError(null);

    try {
      const params: CursorPaginationParams = {
        cursor: scrollState.cursor,
        direction: 'next',
        limit: 50,
        filters: currentFiltersRef.current
      };

      const result = await cursorApiService.getVideosCursor(params);

      // Agregar nuevos posts (evitar duplicados)
      setPosts(prevPosts => {
        const existingIds = new Set(prevPosts.map(p => p.id));
        const uniqueNewPosts = result.data.filter(p => !existingIds.has(p.id));
        return [...prevPosts, ...uniqueNewPosts];
      });

      // Actualizar estado de scroll
      setScrollState(prev => ({
        ...prev,
        cursor: result.pagination.next_cursor,
        hasMore: result.pagination.has_more,
        loading: false
      }));

      // Actualizar stats
      setPerformanceStats(prev => ({
        avgQueryTime: (prev.avgQueryTime + result.performance.query_time_ms) / 2,
        cacheHitRate: result.performance.cache_hit ?
          (prev.cacheHitRate + 100) / 2 :
          prev.cacheHitRate / 2,
        totalQueries: prev.totalQueries + 1
      }));

      console.log(`✅ Loaded ${result.data.length} more videos, total: ${posts.length + result.data.length}`);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error loading more videos';
      setError(errorMessage);
      console.error('Error loading more videos:', err);
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, scrollState, posts.length]);

  /**
   * Refresh data (reload from beginning)
   */
  const refreshData = useCallback(async () => {
    setScrollState(prev => ({ ...prev, cursor: undefined, hasMore: true }));
    await loadVideos(currentFiltersRef.current);
  }, [loadVideos]);

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
  const setFilters = useCallback(async (newFilters: FilterParams) => {
    setFiltersState(newFilters);
    currentFiltersRef.current = newFilters;
    await loadVideos(newFilters);
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
    return {
      total: scrollState.initialLoaded ? posts.length : 0,
      loaded: posts.length,
      hasMore: scrollState.hasMore,
      performance: performanceStats
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