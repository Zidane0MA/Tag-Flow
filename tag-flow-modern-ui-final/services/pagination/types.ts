/**
 * Tag-Flow V2 - Cursor Pagination Types
 * TypeScript definitions for cursor-based pagination
 */

export interface CursorPaginationParams {
  cursor?: string;
  direction?: 'next' | 'prev';
  limit?: number;
  filters?: Record<string, any>;
}

export interface CursorPaginationResult<T> {
  data: T[];
  pagination: {
    next_cursor?: string;
    prev_cursor?: string;
    has_more: boolean;
    total_estimated?: number;
  };
  performance: {
    query_time_ms: number;
    pagination_type: string;
    items_returned: number;
    cache_hit?: boolean;
  };
  success: boolean;
}

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  key: string;
}

export interface ScrollState {
  cursor?: string;
  hasMore: boolean;
  loading: boolean;
  initialLoaded: boolean;
  error?: string;
}

export interface FilterParams {
  creator_name?: string;
  platform?: string;
  edit_status?: string;
  processing_status?: string;
  search?: string;
  has_music?: boolean;
  has_characters?: boolean;
  min_duration?: number;
  max_duration?: number;
  date_from?: string;
  date_to?: string;
}

export interface CursorDataState<T> {
  items: T[];
  scrollState: ScrollState;
  filters: FilterParams;
  cache: Map<string, CacheEntry<T[]>>;
}