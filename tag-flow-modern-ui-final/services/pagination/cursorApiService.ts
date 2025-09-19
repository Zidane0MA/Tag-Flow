/**
 * Tag-Flow V2 - Cursor API Service
 * API service for cursor-based pagination endpoints
 */

import { Post } from '../../types';
import { CursorPaginationParams, CursorPaginationResult, FilterParams } from './types';

const API_BASE_URL = 'http://localhost:5000';

class CursorApiService {
  private cache = new Map<string, any>();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  /**
   * Get videos with cursor pagination
   */
  async getVideosCursor(params: CursorPaginationParams = {}): Promise<CursorPaginationResult<Post>> {
    const searchParams = new URLSearchParams();

    if (params.cursor) searchParams.append('cursor', params.cursor);
    if (params.direction) searchParams.append('direction', params.direction);
    if (params.limit) searchParams.append('limit', params.limit.toString());

    // Add filters
    if (params.filters) {
      Object.entries(params.filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, value.toString());
        }
      });
    }

    const url = `${API_BASE_URL}/api/cursor/videos?${searchParams.toString()}`;

    // Check cache
    const cacheKey = url;
    const cached = this.getFromCache(cacheKey);
    if (cached) {
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

      // Cache result
      this.setCache(cacheKey, transformedResult);

      return transformedResult;

    } catch (error) {
      console.error('Error fetching videos with cursor:', error);
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
      console.error('Error fetching creator videos with cursor:', error);
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

      // Clear local cache too
      this.cache.clear();

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
      postUrl: `${API_BASE_URL}/api/video/${video.id}/stream`,
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
      downloadDate: video.download_date || video.created_at || new Date().toISOString(),
      publicationDate: video.publication_date || video.created_at || new Date().toISOString(),

      // Additional fields
      notes: video.notes || '',
      isCarousel: video.is_carousel || false,
      carouselCount: video.carousel_count || 1,

      // Subscription and lists (from processed data)
      subscription: video.subscription_info || {
        id: 'unknown',
        name: 'Individual',
        type: 'individual' as any
      },
      lists: video.video_lists || []
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
    if (!status || typeof status !== 'string') return 'pending';

    const statusMap: Record<string, any> = {
      'pending': 'pending',
      'in_progress': 'in_progress',
      'completed': 'completed',
      'cancelled': 'cancelled'
    };
    return statusMap[status.toLowerCase()] || 'pending';
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

  private mapDifficulty(difficulty: string | number) {
    if (typeof difficulty === 'number') {
      if (difficulty <= 1) return 'easy';
      if (difficulty <= 2) return 'medium';
      return 'hard';
    }
    return difficulty?.toLowerCase() || 'unknown';
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

  private getFromCache(key: string): any {
    const cached = this.cache.get(key);
    if (!cached) return null;

    const { data, timestamp } = cached;
    if (Date.now() - timestamp > this.CACHE_TTL) {
      this.cache.delete(key);
      return null;
    }

    return data;
  }

  private setCache(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });

    // Simple cache size management
    if (this.cache.size > 50) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
  }
}

export const cursorApiService = new CursorApiService();