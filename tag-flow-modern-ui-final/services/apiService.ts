/**
 * API Service para conectar el frontend React con el backend Flask
 * Maneja todas las comunicaciones con los endpoints del backend
 */

import { Post, Platform, EditStatus, ProcessStatus, Difficulty, Creator, SubscriptionInfo, SubscriptionType, PostType } from '../types';

const API_BASE_URL = 'http://192.168.1.135:5000/api';

export interface VideoFilters {
  search?: string;
  creator_name?: string;
  platform?: string;
  edit_status?: string;
  processing_status?: string;
  difficulty_level?: string;
  limit?: number;
  offset?: number;
}

export interface BackendVideo {
  id: number;
  title: string;
  file_path: string;
  file_name: string;
  thumbnail_path?: string;
  file_size?: number;
  duration_seconds?: number;
  creator_name: string;
  platform: string;
  detected_music?: string;
  detected_music_artist?: string;
  detected_characters?: string; // JSON string
  final_music?: string;
  final_music_artist?: string;
  final_characters?: string; // JSON string
  difficulty_level?: string;
  edit_status: string;
  processing_status: string;
  notes?: string;
  created_at: string;
  last_updated: string;
  post_url?: string;
  external_video_id?: string;
}

export interface BackendResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  total?: number;
}

class ApiService {
  /**
   * Convierte un video del backend al formato del frontend
   */
  private convertBackendVideoToPost(video: BackendVideo): Post {
    // Parsear personajes desde JSON
    let characters: string[] = [];
    try {
      // Priorizar final_characters sobre detected_characters
      const charactersData = video.final_characters || video.detected_characters;
      
      if (charactersData) {
        // Si ya es un array, usarlo directamente
        if (Array.isArray(charactersData)) {
          characters = charactersData;
        }
        // Si es string, intentar parsear JSON
        else if (typeof charactersData === 'string' && charactersData.trim()) {
          characters = JSON.parse(charactersData);
        }
        // Si es objeto, intentar convertir a array
        else if (typeof charactersData === 'object') {
          characters = Array.isArray(charactersData)
            ? charactersData
            : Object.values(charactersData).filter((v): v is string => typeof v === 'string' && Boolean(v));
        }
      }
      
      // Asegurar que characters es un array de strings
      characters = Array.isArray(characters) ? characters.filter(c => typeof c === 'string') : [];
      
    } catch (e) {
      console.warn('Error parsing characters for video', video.id, '- charactersData:', video.final_characters || video.detected_characters, e);
      characters = [];
    }

    // Mapear estados
    const editStatusMap: { [key: string]: EditStatus } = {
      'nulo': EditStatus.PENDING,
      'en_proceso': EditStatus.IN_PROGRESS,
      'hecho': EditStatus.COMPLETED
    };

    const processStatusMap: { [key: string]: ProcessStatus } = {
      'pendiente': ProcessStatus.PENDING,
      'procesando': ProcessStatus.PROCESSING,
      'completado': ProcessStatus.COMPLETED,
      'error': ProcessStatus.ERROR
    };

    const difficultyMap: { [key: string]: Difficulty } = {
      'bajo': Difficulty.LOW,
      'medio': Difficulty.MEDIUM,
      'alto': Difficulty.HIGH
    };

    const platformMap: { [key: string]: Platform } = {
      'youtube': Platform.YOUTUBE,
      'tiktok': Platform.TIKTOK,
      'instagram': Platform.INSTAGRAM,
      'vimeo': Platform.VIMEO,
      'facebook': Platform.FACEBOOK,
      'twitter': Platform.TWITTER,
      'twitch': Platform.TWITCH,
      'discord': Platform.DISCORD,
      'bilibili/video': Platform.BILIBILI,
      'bilibili/video/tv': Platform.BILIBILI_TV
    };

    // ✅ USAR INFORMACIÓN REAL DE SUSCRIPCIONES Y LISTAS DESDE EL BACKEND
    let subscription: any = null;
    let lists: any[] = [];
    
    // Usar información real de suscripción si está disponible
    if ((video as any).subscription_info) {
      const subInfo = (video as any).subscription_info;
      subscription = {
        type: subInfo.type,
        id: subInfo.id.toString(),
        name: subInfo.name
      };
    }
    
    // Usar información real de listas si está disponible
    if ((video as any).video_lists && Array.isArray((video as any).video_lists)) {
      lists = (video as any).video_lists.map((list: any) => ({
        type: list.type,
        name: list.name
      }));
    }

    return {
      id: video.id.toString(),
      title: video.title || video.file_name || 'Sin título',
      description: video.title || video.file_name || '',
      thumbnailUrl: (() => {
        if (!video.thumbnail_path || !video.thumbnail_path.trim()) {
          return 'http://192.168.1.135:5000/static/img/no-thumbnail.svg';
        }
        
        let filename = video.thumbnail_path.split(/[/\\]/).pop();
        if (!filename || !filename.trim()) {
          return 'http://192.168.1.135:5000/static/img/no-thumbnail.svg';
        }
        
        // Si el filename no termina con _thumb.jpg, intentar construirlo desde file_name
        if (!filename.includes('_thumb.')) {
          // Usar file_name para construir el nombre esperado del thumbnail
          if (video.file_name) {
            const baseName = video.file_name.replace(/\.[^/.]+$/, ''); // Remover extensión
            filename = `${baseName}_thumb.jpg`;
          }
        }
        
        return `http://192.168.1.135:5000/thumbnail/${encodeURIComponent(filename)}`;
      })(),
      postUrl: `http://192.168.1.135:5000/video-stream/${video.id}`,
      type: (() => {
        // Detectar tipo basándose en la extensión del archivo
        const isImage = /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(video.file_path || '');
        return isImage ? PostType.IMAGE : PostType.VIDEO;
      })(),
      imageUrls: (() => {
        // Para imágenes, agregar la URL al array de imageUrls
        const isImage = /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(video.file_path || '');
        return isImage ? [`http://192.168.1.135:5000/video-stream/${video.id}`] : undefined;
      })(),
      creator: video.creator_name,
      platform: platformMap[video.platform.toLowerCase()] || Platform.CUSTOM,
      editStatus: editStatusMap[video.edit_status] || EditStatus.PENDING,
      processStatus: processStatusMap[video.processing_status] || ProcessStatus.PENDING,
      difficulty: difficultyMap[video.difficulty_level || 'bajo'] || Difficulty.LOW,
      music: video.final_music || video.detected_music,
      artist: video.final_music_artist || video.detected_music_artist,
      characters,
      notes: video.notes,
      duration: video.duration_seconds || 0,
      size: video.file_size ? Math.round(video.file_size / (1024 * 1024)) : 0, // Convert to MB
      downloadDate: video.created_at,
      uploadDate: video.created_at,
      subscription,
      lists: lists.length > 0 ? lists : undefined,
    };
  }

  /**
   * Obtener videos con filtros
   */
  async getVideos(filters: VideoFilters = {}): Promise<{ posts: Post[], total: number }> {
    try {
      const params = new URLSearchParams();
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '' && value !== 'All') {
          params.append(key, value.toString());
        }
      });

      const response = await fetch(`${API_BASE_URL}/videos?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Error fetching videos');
      }

      const posts = data.videos.map((video: BackendVideo) => this.convertBackendVideoToPost(video));
      
      return {
        posts,
        total: data.total || data.total_videos || posts.length
      };
    } catch (error) {
      console.error('Error fetching videos:', error);
      throw error;
    }
  }

  /**
   * Obtener un video específico
   */
  async getVideo(id: string): Promise<Post> {
    try {
      const response = await fetch(`${API_BASE_URL}/video/${id}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Error fetching video');
      }

      return this.convertBackendVideoToPost(data.video);
    } catch (error) {
      console.error('Error fetching video:', error);
      throw error;
    }
  }

  /**
   * Actualizar un video
   */
  async updateVideo(id: string, updates: Partial<Post>): Promise<boolean> {
    try {
      // Convertir updates del frontend al formato del backend
      const backendUpdates: any = {};
      
      if (updates.music !== undefined) backendUpdates.final_music = updates.music;
      if (updates.artist !== undefined) backendUpdates.final_music_artist = updates.artist;
      if (updates.characters !== undefined) backendUpdates.final_characters = JSON.stringify(updates.characters);
      if (updates.notes !== undefined) backendUpdates.notes = updates.notes;
      
      // Mapear estados de vuelta al backend
      if (updates.editStatus !== undefined) {
        const editStatusReverseMap = {
          [EditStatus.PENDING]: 'nulo',
          [EditStatus.IN_PROGRESS]: 'en_proceso',
          [EditStatus.COMPLETED]: 'hecho'
        };
        backendUpdates.edit_status = editStatusReverseMap[updates.editStatus];
      }

      if (updates.difficulty !== undefined) {
        const difficultyReverseMap = {
          [Difficulty.LOW]: 'bajo',
          [Difficulty.MEDIUM]: 'medio',
          [Difficulty.HIGH]: 'alto'
        };
        backendUpdates.difficulty_level = difficultyReverseMap[updates.difficulty];
      }

      const response = await fetch(`${API_BASE_URL}/video/${id}/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(backendUpdates),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.success;
    } catch (error) {
      console.error('Error updating video:', error);
      throw error;
    }
  }

  /**
   * Actualizar múltiples videos
   */
  async updateMultipleVideos(ids: string[], updates: Partial<Post>): Promise<boolean> {
    try {
      const promises = ids.map(id => this.updateVideo(id, updates));
      const results = await Promise.all(promises);
      return results.every(result => result);
    } catch (error) {
      console.error('Error updating multiple videos:', error);
      throw error;
    }
  }

  /**
   * Mover videos a la papelera (soft delete)
   */
  async moveToTrash(ids: string[]): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/videos/bulk-delete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ video_ids: ids.map(id => parseInt(id)) }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.success;
    } catch (error) {
      console.error('Error moving videos to trash:', error);
      throw error;
    }
  }

  /**
   * Reanalizar videos
   */
  async reanalyzeVideos(ids: string[]): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/videos/reanalyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ video_ids: ids.map(id => parseInt(id)) }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.success;
    } catch (error) {
      console.error('Error reanalyzing videos:', error);
      throw error;
    }
  }


  /**
   * Obtener estadísticas globales del sistema
   */
  async getGlobalStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/stats`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Error fetching global stats');
      }

      return {
        total: data.stats.total,
        withMusic: data.stats.with_music,
        withCharacters: data.stats.with_characters,
        processed: data.stats.processed,
        inTrash: data.stats.in_trash,
        pending: data.stats.pending,
      };
    } catch (error) {
      console.error('Error fetching global stats:', error);
      return {
        total: 0,
        withMusic: 0,
        withCharacters: 0,
        processed: 0,
        inTrash: 0,
        pending: 0,
      };
    }
  }

  /**
   * Obtener estadísticas (solo para compatibilidad)
   */
  async getStats() {
    return this.getGlobalStats();
  }

  /**
   * Obtener todos los creadores con sus plataformas
   */
  async getCreators(): Promise<Creator[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/creators`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Error fetching creators');
      }

      return data.creators.map((creator: any) => ({
        name: creator.name,
        displayName: creator.displayName,
        platforms: creator.platforms
      }));
    } catch (error) {
      console.error('Error fetching creators:', error);
      throw error;
    }
  }

  /**
   * Obtener información de un creador específico
   */
  async getCreator(creatorName: string): Promise<Creator> {
    try {
      const response = await fetch(`${API_BASE_URL}/creator/${encodeURIComponent(creatorName)}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Error fetching creator');
      }

      return {
        name: data.creator.name,
        displayName: data.creator.displayName,
        platforms: data.creator.platforms
      };
    } catch (error) {
      console.error('Error fetching creator:', error);
      throw error;
    }
  }

  /**
   * Obtener videos de un creador específico
   */
  async getCreatorVideos(
    creatorName: string, 
    platform?: string, 
    subscriptionId?: string,
    limit: number = 0, // 0 = sin límite por defecto
    offset: number = 0
  ): Promise<{ posts: Post[], total: number }> {
    try {
      const params = new URLSearchParams();
      if (platform && platform !== 'all') params.append('platform', platform);
      if (subscriptionId) params.append('subscription_id', subscriptionId);
      if (limit > 0) params.append('limit', limit.toString());
      if (offset > 0) params.append('offset', offset.toString());

      const response = await fetch(`${API_BASE_URL}/creator/${encodeURIComponent(creatorName)}/videos?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Error fetching creator videos');
      }

      const posts = data.videos.map((video: BackendVideo) => this.convertBackendVideoToPost(video));
      
      return {
        posts,
        total: data.total || posts.length
      };
    } catch (error) {
      console.error('Error fetching creator videos:', error);
      throw error;
    }
  }

  /**
   * Obtener suscripciones especiales (hashtags, música, etc.)
   */
  async getSubscriptions(): Promise<SubscriptionInfo[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/subscriptions`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Error fetching subscriptions');
      }

      return data.subscriptions;
    } catch (error) {
      console.error('Error fetching subscriptions:', error);
      throw error;
    }
  }

  /**
   * Obtener información específica de una suscripción
   */
  async getSubscriptionInfo(type: string, id: string): Promise<SubscriptionInfo | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/subscription/${type}/${id}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Error fetching subscription info');
      }

      return data.subscription;
    } catch (error) {
      console.error('Error fetching subscription info:', error);
      throw error;
    }
  }

  /**
   * Obtener estadísticas de una suscripción (conteos por tipo de lista)
   */
  async getSubscriptionStats(type: string, id: string): Promise<{total: number, listCounts: {[key: string]: number}} | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/subscription/${type}/${id}/stats`);
      
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Error fetching subscription stats');
      }

      return {
        total: data.total,
        listCounts: data.list_counts
      };
    } catch (error) {
      console.error('Error fetching subscription stats:', error);
      throw error;
    }
  }

  /**
   * Obtener videos de una suscripción específica
   */
  async getSubscriptionVideos(
    type: string,
    id: string,
    listFilter?: string,
    limit: number = 0, // 0 = sin límite por defecto
    offset: number = 0
  ): Promise<{ posts: Post[], total: number }> {
    try {
      const params = new URLSearchParams();
      if (listFilter && listFilter !== 'all') params.append('list', listFilter);
      if (limit > 0) params.append('limit', limit.toString());
      if (offset > 0) params.append('offset', offset.toString());

      const response = await fetch(`${API_BASE_URL}/subscription/${type}/${id}/videos?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Error fetching subscription videos');
      }

      const posts = data.videos.map((video: BackendVideo) => this.convertBackendVideoToPost(video));
      
      return {
        posts,
        total: data.total || posts.length
      };
    } catch (error) {
      console.error('Error fetching subscription videos:', error);
      throw error;
    }
  }
}

export const apiService = new ApiService();