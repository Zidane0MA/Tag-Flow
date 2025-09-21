/**
 * Tag-Flow V2 - Cursor Creator Data Hook
 * Hook especializado para paginas de creadores con cursor pagination
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
}

interface UseCursorCreatorDataResult extends CreatorDataState {
  loadCreatorVideos: (creatorName: string, platform?: string) => Promise<void>;
  loadMoreVideos: () => Promise<void>;
  refreshData: () => Promise<void>;
  clearData: () => void;
}

export const useCursorCreatorData = (): UseCursorCreatorDataResult => {
  // State
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scrollState, setScrollState] = useState<ScrollState>({
    hasMore: true,
    loading: false,
    initialLoaded: false
  });

  // Refs para evitar stale closures
  const currentCreatorRef = useRef<string>('');
  const currentPlatformRef = useRef<string | undefined>(undefined);
  const loadingMoreRef = useRef(false);
  const hasMoreRef = useRef(true);

  // WebSocket integration (will be initialized after refreshData is defined)
  const refreshDataRef = useRef<(() => Promise<void>) | null>(null);

  // Update refs cuando cambien los estados
  useEffect(() => {
    loadingMoreRef.current = loadingMore;
    hasMoreRef.current = scrollState.hasMore;
  }, [loadingMore, scrollState.hasMore]);

  /**
   * Load creator videos (primera página)
   */
  const loadCreatorVideos = useCallback(async (creatorName: string, platform?: string) => {
    if (!creatorName) return;

    try {
      setLoading(true);
      setError(null);
      setPosts([]);

      // Update refs
      currentCreatorRef.current = creatorName;
      currentPlatformRef.current = platform;

      setScrollState({
        cursor: undefined,
        hasMore: true,
        loading: true,
        initialLoaded: false
      });

      const filters: FilterParams = {};
      if (platform) {
        filters.platform = platform;
      }

      const result = await cursorApiService.getCreatorVideosCursor(creatorName, {
        limit: 20,
        filters
      });

      setPosts(result.data);
      setScrollState({
        cursor: result.pagination.next_cursor,
        hasMore: result.pagination.has_more,
        loading: false,
        initialLoaded: true
      });

      console.log(`✅ Loaded ${result.data.length} creator videos, hasMore: ${result.pagination.has_more}`);

    } catch (error: any) {
      console.error('Error loading creator videos:', error);
      setError(error.message || 'Error loading creator videos');
      setScrollState(prev => ({
        ...prev,
        loading: false,
        initialLoaded: true
      }));
    } finally {
      setLoading(false);
    }
  }, []); // Remover dependencia loading temporalmente

  /**
   * Load more videos (páginas siguientes)
   */
  const loadMoreVideos = useCallback(async () => {
    if (loadingMore || !scrollState.hasMore || !scrollState.cursor || !currentCreatorRef.current) {
      return;
    }

    try {
      setLoadingMore(true);
      setError(null);

      const filters: FilterParams = {};
      if (currentPlatformRef.current) {
        filters.platform = currentPlatformRef.current;
      }

      const result = await cursorApiService.getCreatorVideosCursor(currentCreatorRef.current, {
        cursor: scrollState.cursor,
        limit: 20,
        filters
      });

      // Evitar duplicados por ID
      setPosts(prevPosts => {
        const existingIds = new Set(prevPosts.map(post => post.id));
        const uniqueNewPosts = result.data.filter(post => !existingIds.has(post.id));
        return [...prevPosts, ...uniqueNewPosts];
      });

      setScrollState({
        cursor: result.pagination.next_cursor,
        hasMore: result.pagination.has_more,
        loading: false,
        initialLoaded: true
      });
    } catch (error: any) {
      console.error('Error loading more creator videos:', error);
      setError(error.message || 'Error loading more videos');
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, scrollState.hasMore, scrollState.cursor]);

  /**
   * Refresh data (reload current creator)
   */
  const refreshData = useCallback(async () => {
    if (currentCreatorRef.current) {
      await loadCreatorVideos(currentCreatorRef.current, currentPlatformRef.current);
    }
  }, [loadCreatorVideos]);

  // Update refresh ref and setup WebSocket sync
  useEffect(() => {
    refreshDataRef.current = refreshData;
  }, [refreshData]);

  // WebSocket integration for real-time updates
  useCursorWebSocketSync(() => refreshDataRef.current?.() || Promise.resolve());

  /**
   * Clear all data
   */
  const clearData = useCallback(() => {
    setPosts([]);
    setScrollState({
      hasMore: true,
      loading: false,
      initialLoaded: false
    });
    setError(null);
    currentCreatorRef.current = '';
    currentPlatformRef.current = undefined;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Cleanup if needed
    };
  }, []);

  return {
    // Data
    posts,
    loading,
    loadingMore,
    error,
    scrollState,

    // Actions
    loadCreatorVideos,
    loadMoreVideos,
    refreshData,
    clearData
  };
};