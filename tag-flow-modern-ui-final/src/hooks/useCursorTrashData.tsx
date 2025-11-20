/**
 * Tag-Flow V2 - Cursor Trash Data Hook
 * Hook especializado para TrashPage con cursor pagination
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { Post } from '../types';
import { cursorApiService } from '../services/pagination/cursorApiService';
import { useCursorWebSocketSync } from './useWebSocketUpdates';

interface ScrollState {
  cursor?: string;
  hasMore: boolean;
  loading: boolean;
  initialLoaded: boolean;
}

interface TrashDataState {
  posts: Post[];
  loading: boolean;
  loadingMore: boolean;
  error: string | null;
  scrollState: ScrollState;
}

interface UseCursorTrashDataResult extends TrashDataState {
  loadTrashVideos: () => Promise<void>;
  loadMoreVideos: () => Promise<void>;
  refreshData: () => Promise<void>;
  clearData: () => void;
}

export const useCursorTrashData = (): UseCursorTrashDataResult => {
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
  const loadingMoreRef = useRef(false);
  const hasMoreRef = useRef(true);

  // Update refs cuando cambien los estados
  useEffect(() => {
    loadingMoreRef.current = loadingMore;
    hasMoreRef.current = scrollState.hasMore;
  }, [loadingMore, scrollState.hasMore]);

  /**
   * Load trash videos (primera página)
   */
  const loadTrashVideos = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setPosts([]);

      setScrollState({
        cursor: undefined,
        hasMore: true,
        loading: true,
        initialLoaded: false
      });

      const result = await cursorApiService.getTrashVideosCursor({
        limit: 20
      });

      setPosts(result.data);
      setScrollState({
        cursor: result.pagination.next_cursor,
        hasMore: result.pagination.has_more,
        loading: false,
        initialLoaded: true
      });

      console.log(`✅ Loaded ${result.data.length} trash videos, hasMore: ${result.pagination.has_more}`);

    } catch (error: any) {
      console.error('Error loading trash videos:', error);
      setError(error.message || 'Error loading trash videos');
      setScrollState(prev => ({
        ...prev,
        loading: false,
        initialLoaded: true
      }));
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Load more videos (páginas siguientes)
   */
  const loadMoreVideos = useCallback(async () => {
    if (loadingMore || !scrollState.hasMore || !scrollState.cursor) {
      return;
    }

    try {
      setLoadingMore(true);
      setError(null);

      const result = await cursorApiService.getTrashVideosCursor({
        cursor: scrollState.cursor,
        limit: 20
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
      console.error('Error loading more trash videos:', error);
      setError(error.message || 'Error loading more videos');
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, scrollState.hasMore, scrollState.cursor]);

  /**
   * Refresh data (reload trash)
   */
  const refreshData = useCallback(async () => {
    await loadTrashVideos();
  }, [loadTrashVideos]);

  // WebSocket integration for real-time updates
  useCursorWebSocketSync(refreshData);

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
    loadTrashVideos,
    loadMoreVideos,
    refreshData,
    clearData
  };
};