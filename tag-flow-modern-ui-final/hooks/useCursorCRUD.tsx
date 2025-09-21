/**
 * Tag-Flow V2 - Cursor CRUD Hook
 * Hook híbrido que combina cursor pagination con operaciones CRUD
 */

import { useCallback } from 'react';
import { apiService } from '../services/apiService';
import { Post } from '../types';
import { useCursorCRUDWebSocket } from './useWebSocketUpdates';

export interface CursorCRUDOperations {
  // CRUD Operations
  updatePost: (id: string, updates: Partial<Post>) => Promise<{ success: boolean; message?: string }>;
  updateMultiplePosts: (ids: string[], updates: Partial<Post>) => Promise<{ success: boolean; message?: string }>;
  moveToTrash: (id: string) => Promise<{ success: boolean; message?: string }>;
  restoreFromTrash: (id: string) => Promise<{ success: boolean; message?: string }>;
  deletePermanently: (id: string) => Promise<{ success: boolean; message?: string }>;
  analyzePost: (id: string) => Promise<{ success: boolean; message?: string }>;

  // Utility functions
  invalidateCache: () => void;
  refreshCurrentView: () => Promise<void>;
}

/**
 * Hook híbrido para operaciones CRUD que funciona con cursor pagination
 */
export const useCursorCRUD = (
  refreshCallback?: () => Promise<void>
): CursorCRUDOperations => {

  // WebSocket notifications
  const { notifyVideoUpdate, notifyCacheInvalidation } = useCursorCRUDWebSocket();

  /**
   * Actualizar un post individual
   */
  const updatePost = useCallback(async (id: string, updates: Partial<Post>) => {
    try {
      const success = await apiService.updateVideo(id, updates);

      if (success) {
        // Notify WebSocket about the update
        await notifyVideoUpdate(id, 'update', updates);

        // Refresh current view if callback provided
        if (refreshCallback) {
          await refreshCallback();
        }
      }

      return { success, message: success ? 'Post updated successfully' : 'Update failed' };
    } catch (error: any) {
      console.error('Error updating post:', error);
      return { success: false, message: error.message || 'Error updating post' };
    }
  }, [refreshCallback, notifyVideoUpdate]);

  /**
   * Actualizar múltiples posts
   */
  const updateMultiplePosts = useCallback(async (ids: string[], updates: Partial<Post>) => {
    try {
      const success = await apiService.updateMultipleVideos(ids, updates);

      if (success) {
        // Notify WebSocket about multiple updates
        for (const id of ids) {
          await notifyVideoUpdate(id, 'update', updates);
        }

        // Refresh current view if callback provided
        if (refreshCallback) {
          await refreshCallback();
        }
      }

      return { success, message: success ? 'Posts updated successfully' : 'Update failed' };
    } catch (error: any) {
      console.error('Error updating multiple posts:', error);
      return { success: false, message: error.message || 'Error updating posts' };
    }
  }, [refreshCallback, notifyVideoUpdate]);

  /**
   * Mover post a papelera
   */
  const moveToTrash = useCallback(async (id: string) => {
    try {
      const success = await apiService.moveToTrash([id]);

      if (success) {
        // Notify WebSocket about move to trash
        await notifyVideoUpdate(id, 'move_to_trash', {});

        // Refresh current view if callback provided
        if (refreshCallback) {
          await refreshCallback();
        }
      }

      return { success, message: success ? 'Post moved to trash' : 'Move to trash failed' };
    } catch (error: any) {
      console.error('Error moving to trash:', error);
      return { success: false, message: error.message || 'Error moving to trash' };
    }
  }, [refreshCallback, notifyVideoUpdate]);

  /**
   * Restaurar post de papelera
   */
  const restoreFromTrash = useCallback(async (id: string) => {
    try {
      const success = await apiService.restoreVideo(id);

      if (success) {
        // Notify WebSocket about restore
        await notifyVideoUpdate(id, 'restore', {});

        // Refresh current view if callback provided
        if (refreshCallback) {
          await refreshCallback();
        }
      }

      return { success, message: success ? 'Post restored successfully' : 'Restore failed' };
    } catch (error: any) {
      console.error('Error restoring from trash:', error);
      return { success: false, message: error.message || 'Error restoring from trash' };
    }
  }, [refreshCallback, notifyVideoUpdate]);

  /**
   * Eliminar permanentemente
   */
  const deletePermanently = useCallback(async (id: string) => {
    try {
      const response = await apiService.deletePermanently(id);

      if (response.success) {
        // Notify WebSocket about permanent deletion
        await notifyVideoUpdate(id, 'delete', {});

        // Refresh current view if callback provided
        if (refreshCallback) {
          await refreshCallback();
        }
      }

      return response;
    } catch (error: any) {
      console.error('Error deleting permanently:', error);
      return { success: false, message: error.message || 'Error deleting permanently' };
    }
  }, [refreshCallback, notifyVideoUpdate]);

  /**
   * Analizar post con AI
   */
  const analyzePost = useCallback(async (id: string) => {
    try {
      const success = await apiService.reanalyzeVideos([id]);

      // Refresh current view if callback provided
      if (refreshCallback && success) {
        await refreshCallback();
      }

      return { success, message: success ? 'Post analysis started' : 'Analysis failed' };
    } catch (error: any) {
      console.error('Error analyzing post:', error);
      return { success: false, message: error.message || 'Error analyzing post' };
    }
  }, [refreshCallback]);

  /**
   * Invalidar cache (placeholder for future cache implementation)
   */
  const invalidateCache = useCallback(() => {
    // Future: Invalidate cursor cache
    console.log('Cache invalidation requested');
  }, []);

  /**
   * Refresh current view
   */
  const refreshCurrentView = useCallback(async () => {
    if (refreshCallback) {
      await refreshCallback();
    }
  }, [refreshCallback]);

  return {
    updatePost,
    updateMultiplePosts,
    moveToTrash,
    restoreFromTrash,
    deletePermanently,
    analyzePost,
    invalidateCache,
    refreshCurrentView
  };
};