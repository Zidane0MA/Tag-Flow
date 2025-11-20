/**
 * Tag-Flow V2 - Cursor Subscription Data Hook
 * Hook especializado para paginas de subscriptions con cursor pagination
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

interface SubscriptionDataState {
  posts: Post[];
  loading: boolean;
  loadingMore: boolean;
  error: string | null;
  scrollState: ScrollState;
}

interface UseCursorSubscriptionDataResult extends SubscriptionDataState {
  loadSubscriptionVideos: (subscriptionType: string, subscriptionId: number) => Promise<void>;
  loadMoreVideos: () => Promise<void>;
  refreshData: () => Promise<void>;
  clearData: () => void;
}

export const useCursorSubscriptionData = (): UseCursorSubscriptionDataResult => {
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
  const currentSubscriptionTypeRef = useRef<string>('');
  const currentSubscriptionIdRef = useRef<number>(0);
  const loadingMoreRef = useRef(false);
  const hasMoreRef = useRef(true);

  // Update refs cuando cambien los estados
  useEffect(() => {
    loadingMoreRef.current = loadingMore;
    hasMoreRef.current = scrollState.hasMore;
  }, [loadingMore, scrollState.hasMore]);

  /**
   * Load subscription videos (primera página)
   */
  const loadSubscriptionVideos = useCallback(async (subscriptionType: string, subscriptionId: number) => {
    if (!subscriptionType || !subscriptionId) return;

    try {
      setLoading(true);
      setError(null);
      setPosts([]);

      // Update refs
      currentSubscriptionTypeRef.current = subscriptionType;
      currentSubscriptionIdRef.current = subscriptionId;

      setScrollState({
        cursor: undefined,
        hasMore: true,
        loading: true,
        initialLoaded: false
      });

      const result = await cursorApiService.getSubscriptionVideosCursor(subscriptionType, subscriptionId, {
        limit: 20
      });

      setPosts(result.data);
      setScrollState({
        cursor: result.pagination.next_cursor,
        hasMore: result.pagination.has_more,
        loading: false,
        initialLoaded: true
      });

      console.log(`✅ Loaded ${result.data.length} subscription videos, hasMore: ${result.pagination.has_more}`);

    } catch (error: any) {
      console.error('Error loading subscription videos:', error);
      setError(error.message || 'Error loading subscription videos');
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
    if (loadingMore || !scrollState.hasMore || !scrollState.cursor || !currentSubscriptionTypeRef.current || !currentSubscriptionIdRef.current) {
      return;
    }

    try {
      setLoadingMore(true);
      setError(null);

      const result = await cursorApiService.getSubscriptionVideosCursor(
        currentSubscriptionTypeRef.current,
        currentSubscriptionIdRef.current,
        {
          cursor: scrollState.cursor,
          limit: 20
        }
      );

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
      console.error('Error loading more subscription videos:', error);
      setError(error.message || 'Error loading more videos');
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, scrollState.hasMore, scrollState.cursor]);

  /**
   * Refresh data (reload current subscription)
   */
  const refreshData = useCallback(async () => {
    if (currentSubscriptionTypeRef.current && currentSubscriptionIdRef.current) {
      await loadSubscriptionVideos(currentSubscriptionTypeRef.current, currentSubscriptionIdRef.current);
    }
  }, [loadSubscriptionVideos]);

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
    currentSubscriptionTypeRef.current = '';
    currentSubscriptionIdRef.current = 0;
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
    loadSubscriptionVideos,
    loadMoreVideos,
    refreshData,
    clearData
  };
};