/**
 * Tag-Flow V2 - Cursor Creator Data Hook
 * Hook especializado para paginas de creadores con cursor pagination, ordenamiento y búsqueda.
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { Post } from '../types';
import { cursorApiService } from '../services/pagination/cursorApiService';
import { FilterParams } from '../services/pagination/types';
import { useCursorWebSocketSync } from './useWebSocketUpdates';

interface ScrollState {
  cursor?: string;
  hasMore: boolean;
  loading: boolean;
  initialLoaded: boolean;
}

interface CreatorDataState {
  posts: Post[];
  loading: boolean;
  loadingMore: boolean;
  error: string | null;
  scrollState: ScrollState;
  filters: FilterParams;
}

interface UseCursorCreatorDataResult extends CreatorDataState {
  loadCreatorVideos: (creatorName: string, platform?: string) => Promise<void>;
  loadMoreVideos: () => Promise<void>;
  refreshData: () => Promise<void>;
  clearData: () => void;
  setAndReloadFilters: (newFilters: Partial<FilterParams>) => void;
}

const INITIAL_FILTERS: FilterParams = {
  sort_by: 'publication_date',
  sort_order: 'desc',
  search: '',
};

export const useCursorCreatorData = (): UseCursorCreatorDataResult => {
  // State
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterParams>(INITIAL_FILTERS);
  const [scrollState, setScrollState] = useState<ScrollState>({
    hasMore: true,
    loading: false,
    initialLoaded: false
  });

  // Refs para evitar stale closures
  const currentCreatorRef = useRef<string>('');
  const currentPlatformRef = useRef<string | undefined>(undefined);
  const filtersRef = useRef(filters);

  // WebSocket integration
  const refreshDataRef = useRef<(() => Promise<void>) | null>(null);

  useEffect(() => {
    filtersRef.current = filters;
  }, [filters]);

  const loadCreatorVideos = useCallback(async (creatorName: string, platform?: string, currentFilters?: FilterParams) => {
    if (!creatorName) return;

    const effectiveFilters = currentFilters || filtersRef.current;

    try {
      setLoading(true);
      setError(null);
      setPosts([]);

      currentCreatorRef.current = creatorName;
      currentPlatformRef.current = platform;

      setScrollState({ cursor: undefined, hasMore: true, loading: true, initialLoaded: false });

      const apiParams: CursorPaginationParams = {
        limit: 20,
        filters: { // All filter params go inside 'filters' object
            sort_by: effectiveFilters.sort_by,
            sort_order: effectiveFilters.sort_order,
            search: effectiveFilters.search,
        }
      };
      if (platform) {
        apiParams.filters.platform = platform;
      }

      const result = await cursorApiService.getCreatorVideosCursor(creatorName, apiParams);

      setPosts(result.data);
      setScrollState({
        cursor: result.pagination.next_cursor,
        hasMore: result.pagination.has_more,
        loading: false,
        initialLoaded: true
      });

    } catch (err: any) {
      console.error('Error loading creator videos:', err);
      setError(err.message || 'Error loading creator videos');
      setScrollState(prev => ({ ...prev, loading: false, initialLoaded: true }));
    } finally {
      setLoading(false);
    }
  }, [filtersRef, setLoading, setError, setPosts, setScrollState, currentCreatorRef, currentPlatformRef, cursorApiService]);

  const loadMoreVideos = useCallback(async () => {
    if (loadingMore || !scrollState.hasMore || !scrollState.cursor || !currentCreatorRef.current) {
      return;
    }

    try {
      setLoadingMore(true);
      setError(null);

      const apiParams: CursorPaginationParams = {
        cursor: scrollState.cursor,
        limit: 20,
        filters: {
            sort_by: filtersRef.current.sort_by,
            sort_order: filtersRef.current.sort_order,
            search: filtersRef.current.search,
        }
      };
      if (currentPlatformRef.current) {
        apiParams.filters.platform = currentPlatformRef.current;
      }

      const result = await cursorApiService.getCreatorVideosCursor(currentCreatorRef.current, apiParams);

      setPosts(prevPosts => {
        const existingIds = new Set(prevPosts.map(post => post.id));
        const uniqueNewPosts = result.data.filter(post => !existingIds.has(post.id));
        return [...prevPosts, ...uniqueNewPosts];
      });

      setScrollState({
        cursor: result.pagination.next_cursor,
        hasMore: result.pagination.has_more,
        loading: false,
        initialLoaded: true,
      });
    } catch (err: any) {
      console.error('Error loading more creator videos:', err);
      setError(err.message || 'Error loading more videos');
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, scrollState.cursor, scrollState.hasMore, filtersRef, currentCreatorRef, currentPlatformRef, cursorApiService, setPosts, setLoadingMore, setError, setScrollState]);

  const setAndReloadFilters = useCallback((newFilters: Partial<FilterParams>) => {
    const updatedFilters = { ...filtersRef.current, ...newFilters };
    setFilters(updatedFilters);
    loadCreatorVideos(currentCreatorRef.current, currentPlatformRef.current, updatedFilters);
  }, [loadCreatorVideos]);

  const refreshData = useCallback(async () => {
    if (currentCreatorRef.current) {
      await loadCreatorVideos(currentCreatorRef.current, currentPlatformRef.current, filtersRef.current);
    }
  }, [loadCreatorVideos]);
  
  useEffect(() => {
    refreshDataRef.current = refreshData;
  }, [refreshData]);

  useCursorWebSocketSync(() => refreshDataRef.current?.() || Promise.resolve());

  const clearData = useCallback(() => {
    setPosts([]);
    setFilters(INITIAL_FILTERS);
    setScrollState({ hasMore: true, loading: false, initialLoaded: false });
    setError(null);
    currentCreatorRef.current = '';
    currentPlatformRef.current = undefined;
  }, []);

  return {
    posts,
    loading,
    loadingMore,
    error,
    scrollState,
    filters,
    loadCreatorVideos,
    loadMoreVideos,
    refreshData,
    clearData,
    setAndReloadFilters,
  };
};