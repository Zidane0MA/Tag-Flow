/**
 * Tag-Flow V2 - Cursor API Service
 * API service for cursor-based pagination endpoints
 */

import { Post } from '../../types';
import { CursorPaginationParams, CursorPaginationResult, FilterParams } from './types';
import { cacheManager } from '../unifiedCacheManager';

const API_BASE_URL = 'http://localhost:5000';

class CursorApiService {

  /**
   * Get videos with cursor pagination
   */
  async getVideosCursor(params: CursorPaginationParams = {}): Promise<CursorPaginationResult<Post>> {
    const searchParams = new URLSearchParams();

    if (params.cursor) searchParams.append('cursor', params.cursor);
    if (params.direction) searchParams.append('direction', params.direction);
    if (params.limit) searchParams.append('limit', params.limit.toString());

    // Add sorting parameters
    if (params.sort_by) searchParams.append('sort_by', params.sort_by);
    if (params.sort_order) searchParams.append('sort_order', params.sort_order);

    // Add filters
    if (params.filters) {
      Object.entries(params.filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, value.toString());
        }
      });
    }

    const url = `${API_BASE_URL}/api/cursor/videos?${searchParams.toString()}`;

    // Check unified cache
    const cached = cacheManager.getCursorResult(params.filters || {}, params.cursor);
    if (cached) {
      console.log('🚀 Using cached cursor result');
      return cached;
    }

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'API request failed');
      }

      // Transform backend data to frontend format
      const transformedResult: CursorPaginationResult<Post> = {
        data: result.data.map((video: any) => this.transformVideoToPost(video)),
        pagination: result.pagination,
        performance: {
          ...result.performance,
          cache_hit: result.cache_hit || false
        },
        success: result.success
      };

      // Cache result using unified cache manager
      cacheManager.cacheCursorResult(params.filters || {}, params.cursor, transformedResult);

      return transformedResult;

    } catch (error) {
      console.error('Error fetching videos with cursor:', error);
      throw error;
    }
  }

  /**
   * Get subscription videos with cursor pagination
   */
  async getSubscriptionVideosCursor(
    subscriptionType: string,
    subscriptionId: number,
    params: CursorPaginationParams = {}
  ): Promise<CursorPaginationResult<Post>> {
    const searchParams = new URLSearchParams();

    if (params.cursor) searchParams.append('cursor', params.cursor);
    if (params.limit) searchParams.append('limit', params.limit.toString());

    const url = `${API_BASE_URL}/api/cursor/subscriptions/${encodeURIComponent(subscriptionType)}/${subscriptionId}/videos?${searchParams.toString()}`;

    // Check cache
    const cacheKey = cacheManager.buildKey('subscription:videos', {
      type: subscriptionType,
      id: subscriptionId,
      cursor: params.cursor,
      limit: params.limit
    });

    const cached = this.getCachedApiResult(cacheKey);
    if (cached) {
      console.log('🚀 Using cached subscription result');
      return cached;
    }

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'API request failed');
      }

      const transformedResult = {
        data: result.data.map((video: any) => this.transformVideoToPost(video)),
        pagination: result.pagination,
        performance: result.performance,
        success: result.success
      };

      // Cache the result
      this.cacheApiResult(cacheKey, transformedResult, 'subscription');

      return transformedResult;

    } catch (error) {
      console.error('Error fetching subscription videos with cursor:', error);
      throw error;
    }
  }

  /**
   * Get creator videos with cursor pagination
   */
  async getCreatorVideosCursor(
    creatorName: string,
    params: CursorPaginationParams = {}
  ): Promise<CursorPaginationResult<Post>> {
    const searchParams = new URLSearchParams();

    if (params.cursor) searchParams.append('cursor', params.cursor);
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.filters?.platform) searchParams.append('platform', params.filters.platform);

    const url = `${API_BASE_URL}/api/cursor/creators/${encodeURIComponent(creatorName)}/videos?${searchParams.toString()}`;

    // Check cache
    const cacheKey = cacheManager.buildKey('creator:videos', {
      creator: creatorName,
      cursor: params.cursor,
      limit: params.limit,
      platform: params.filters?.platform
    });

    const cached = this.getCachedApiResult(cacheKey);
    if (cached) {
      console.log('🚀 Using cached creator result');
      return cached;
    }

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'API request failed');
      }

      const transformedResult = {
        data: result.data.map((video: any) => this.transformVideoToPost(video)),
        pagination: result.pagination,
        performance: result.performance,
        success: result.success
      };

      // Cache the result
      this.cacheApiResult(cacheKey, transformedResult, 'creators');

      return transformedResult;

    } catch (error) {
      console.error('Error fetching creator videos with cursor:', error);
      throw error;
    }
  }

  /**
   * Get trash videos with cursor pagination
   */
  async getTrashVideosCursor(
    params: CursorPaginationParams = {}
  ): Promise<CursorPaginationResult<Post>> {
    const searchParams = new URLSearchParams();

    if (params.cursor) searchParams.append('cursor', params.cursor);
    if (params.limit) searchParams.append('limit', params.limit.toString());

    const url = `${API_BASE_URL}/api/cursor/trash/videos?${searchParams.toString()}`;

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'API request failed');
      }

      return {
        data: result.data.map((video: any) => this.transformVideoToPost(video)),
        pagination: result.pagination,
        performance: result.performance,
        success: result.success
      };

    } catch (error) {
      console.error('Error fetching trash videos with cursor:', error);
      throw error;
    }
  }

  /**
   * Get performance stats
   */
  async getPerformanceStats(windowSeconds = 60): Promise<any> {
    const url = `${API_BASE_URL}/api/cursor/performance/stats?window=${windowSeconds}`;

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error fetching performance stats:', error);
      throw error;
    }
  }

  /**
   * Invalidate cache
   */
  async invalidateCache(pattern = '*'): Promise<any> {
    const url = `${API_BASE_URL}/api/cursor/cache/invalidate`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pattern }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      // Clear unified cache too
      cacheManager.clear();

      return result;

    } catch (error) {
      console.error('Error invalidating cache:', error);
      throw error;
    }
  }

  /**
   * Transform backend video to frontend Post
   */
  private transformVideoToPost(video: any): Post {
    return {
      id: video.id?.toString() || '',
      title: video.title_post || video.file_name || 'Sin título',
      creator: video.creator_name || 'Desconocido',
      platform: this.mapPlatform(video.platform),
      thumbnailUrl: video.thumbnail_path ? `${API_BASE_URL}/thumbnail/${encodeURIComponent(video.thumbnail_path)}` : `${API_BASE_URL}/static/img/no-thumbnail.svg`,
      postUrl: `${API_BASE_URL}/api/video-stream/${video.id}`,
      type: video.duration_seconds > 60 ? 'Video' as any : 'Video' as any, // Default to Video
      editStatus: this.mapEditStatus(video.edit_status),
      processStatus: this.mapProcessStatus(video.processing_status),
      difficulty: this.mapDifficulty(video.difficulty_level),

      // Media details
      duration: video.duration_seconds || 0,
      size: video.file_size ? (video.file_size / (1024 * 1024)) : 0, // Convert bytes to MB

      // AI Analysis
      music: video.final_music || video.detected_music || null,
      artist: video.final_music_artist || video.detected_music_artist || null,
      characters: this.parseCharacters(video.final_characters || video.detected_characters),

      // Dates
      downloadDate: video.download_date ? new Date(video.download_date * 1000).toISOString() : undefined,
      publicationDate: video.publication_date || video.created_at || new Date().toISOString(),

      // Additional fields
      originalUrl: video.post_url || '',
      notes: video.notes || '',
      isCarousel: video.is_carousel || false,
      carouselCount: video.carousel_count || 1,

      // Subscription and lists (from processed data)
      subscription: video.subscription_info || {
        id: 'unknown',
        name: 'Individual',
        type: 'individual' as any
      },
      lists: (video.categories || []).map((cat: any) => ({ type: cat.type }))
    };
  }

  private mapPlatform(platform: string | null | undefined) {
    if (!platform || typeof platform !== 'string') return 'unknown';

    const platformMap: Record<string, any> = {
      'youtube': 'youtube',
      'tiktok': 'tiktok',
      'instagram': 'instagram',
      'facebook': 'facebook',
      'twitter': 'twitter',
      'bilibili': 'bilibili'
    };
    return platformMap[platform.toLowerCase()] || 'unknown';
  }

  private mapEditStatus(status: string | null | undefined) {
    if (!status || typeof status !== 'string') return 'pendiente';

    const statusMap: Record<string, any> = {
      // Valores en español desde la BD → tipos TypeScript
      'pendiente': 'pendiente',
      'en_proceso': 'en_proceso',
      'completado': 'completado',
      'descartado': 'descartado',
      // Valores en inglés (fallback) → tipos TypeScript
      'pending': 'pendiente',
      'in_progress': 'en_proceso',
      'completed': 'completado',
      'cancelled': 'descartado'
    };
    return statusMap[status.toLowerCase()] || 'pendiente';
  }

  private mapProcessStatus(status: string | null | undefined) {
    if (!status || typeof status !== 'string') return 'pending';

    const statusMap: Record<string, any> = {
      'pending': 'pending',
      'processing': 'processing',
      'completed': 'completed',
      'failed': 'failed'
    };
    return statusMap[status.toLowerCase()] || 'pending';
  }

  private mapDifficulty(difficulty: string | number | null | undefined) {
    // Si es null o undefined, mantener como null
    if (difficulty === null || difficulty === undefined) {
      return null;
    }

    if (typeof difficulty === 'number') {
      if (difficulty <= 1) return 'low';
      if (difficulty <= 2) return 'medium';
      return 'high';
    }

    const difficultyMap: Record<string, any> = {
      'low': 'low',
      'medium': 'medium',
      'high': 'high',
      'bajo': 'low',
      'medio': 'medium',
      'alto': 'high',
      'easy': 'low',
      'hard': 'high'
    };

    return difficultyMap[difficulty?.toLowerCase()] || null;
  }

  private parseCharacters(characters: string | null | any): string[] {
    if (!characters) return [];

    // If it's already an array, return it
    if (Array.isArray(characters)) {
      return characters.filter(c => typeof c === 'string');
    }

    // If it's not a string, convert to string or return empty array
    if (typeof characters !== 'string') {
      return [];
    }

    try {
      const parsed = JSON.parse(characters);
      if (Array.isArray(parsed)) {
        return parsed.filter(c => typeof c === 'string');
      }
      return [];
    } catch {
      return characters.split(',').map(c => c.trim()).filter(Boolean);
    }
  }

  // Funciones de conveniencia para cache unificado
  private cacheApiResult(key: string, data: any, category: string = 'cursor-results'): void {
    cacheManager.set(key, data, { category, source: 'api' });
  }

  private getCachedApiResult(key: string): any | null {
    return cacheManager.get(key);
  }
}

export const cursorApiService = new CursorApiService();