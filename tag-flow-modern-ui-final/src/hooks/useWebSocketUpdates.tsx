/**
 * 🔗 Hook WebSocket Updates - Manejo de actualizaciones en tiempo real
 * Integra WebSocket con hooks cursor para invalidación automática
 */

import { useEffect, useCallback, useRef } from 'react';
import websocketService from '../services/websocketService';
import { cacheManager } from '../services/unifiedCacheManager';

interface VideoUpdateData {
  video_id: string;
  action: 'update' | 'delete' | 'restore' | 'move_to_trash';
  changes: Record<string, any>;
  timestamp: string;
}

interface CacheInvalidationData {
  cache_keys: string[];
  reason: string;
  timestamp: string;
}

interface WebSocketHookOptions {
  onVideoUpdate?: (data: VideoUpdateData) => void;
  onCacheInvalidation?: (data: CacheInvalidationData) => void;
  onConnectionChange?: (connected: boolean) => void;
  autoRefresh?: boolean; // Si debe auto-refrescar datos en updates
}

/**
 * Hook principal para manejar WebSocket updates
 */
export const useWebSocketUpdates = (options: WebSocketHookOptions = {}) => {
  const {
    onVideoUpdate,
    onCacheInvalidation,
    onConnectionChange,
    autoRefresh = true
  } = options;

  const connectionStatusRef = useRef<boolean>(false);

  // Handler para updates de video
  const handleVideoUpdate = useCallback((data: VideoUpdateData) => {
    console.log('🔗 Video update:', data);

    // Invalidar cache relacionado con el video
    cacheManager.invalidateVideo(data.video_id);

    // Invalidar cache de cursor results que puedan incluir este video
    cacheManager.invalidatePattern('cursor:videos:*');

    // Si el video cambió de creador, invalidar cache de creador
    if (data.changes?.creator_name) {
      cacheManager.invalidateCreator(data.changes.creator_name);
    }

    if (onVideoUpdate) {
      onVideoUpdate(data);
    }

    // Auto-refresh logic si está habilitado
    if (autoRefresh) {
      // Trigger refresh en hooks que lo soporten
      window.dispatchEvent(new CustomEvent('websocket-video-update', {
        detail: data
      }));
    }
  }, [onVideoUpdate, autoRefresh]);

  // Handler para invalidación de cache
  const handleCacheInvalidation = useCallback((data: CacheInvalidationData) => {
    console.log('🔗 Cache invalidation:', data);

    // Invalidar claves específicas en el cache unificado
    data.cache_keys.forEach(key => {
      if (key.includes('*')) {
        // Es un patrón, usar invalidatePattern
        cacheManager.invalidatePattern(key);
      } else {
        // Es una clave específica
        cacheManager.invalidate(key);
      }
    });

    if (onCacheInvalidation) {
      onCacheInvalidation(data);
    }

    // Auto-refresh logic si está habilitado
    if (autoRefresh) {
      // Trigger refresh en hooks que lo soporten
      window.dispatchEvent(new CustomEvent('websocket-cache-invalidation', {
        detail: data
      }));
    }
  }, [onCacheInvalidation, autoRefresh]);

  // Handler para cambios de conexión
  const handleConnectionChange = useCallback((connected: boolean) => {
    if (connectionStatusRef.current !== connected) {
      connectionStatusRef.current = connected;
      console.log(`🔗 Conexión WebSocket: ${connected ? 'conectado' : 'desconectado'}`);

      if (onConnectionChange) {
        onConnectionChange(connected);
      }
    }
  }, [onConnectionChange]);

  // Setup y cleanup de event listeners
  useEffect(() => {
    // Registrar handlers
    websocketService.on('video_update', handleVideoUpdate);
    websocketService.on('cache_invalidation', handleCacheInvalidation);
    websocketService.on('connected', () => handleConnectionChange(true));
    websocketService.on('disconnected', () => handleConnectionChange(false));

    // Estado inicial
    handleConnectionChange(websocketService.isConnected());

    // Cleanup
    return () => {
      websocketService.off('video_update', handleVideoUpdate);
      websocketService.off('cache_invalidation', handleCacheInvalidation);
      websocketService.off('connected', () => handleConnectionChange(true));
      websocketService.off('disconnected', () => handleConnectionChange(false));
    };
  }, [handleVideoUpdate, handleCacheInvalidation, handleConnectionChange]);

  return {
    connected: connectionStatusRef.current,
    connectionStats: websocketService.getConnectionStats(),
    subscribeToOperation: websocketService.subscribeToOperation.bind(websocketService),
    unsubscribeFromOperation: websocketService.unsubscribeFromOperation.bind(websocketService),
    disconnect: websocketService.disconnect.bind(websocketService),
    connect: websocketService.connect.bind(websocketService)
  };
};

/**
 * Hook específico para cursor data que se auto-refresca con WebSocket
 */
export const useCursorWebSocketSync = (refreshCallback?: () => Promise<void>) => {
  const refreshCallbackRef = useRef(refreshCallback);
  refreshCallbackRef.current = refreshCallback;

  useEffect(() => {
    // Verificar si refreshCallback es válido
    if (!refreshCallback) {
      console.warn('🔗 useCursorWebSocketSync: refreshCallback is undefined, skipping WebSocket sync');
      return;
    }

    const handleVideoUpdate = (event: CustomEvent<VideoUpdateData>) => {
      const data = event.detail;
      console.log('🔗 Cursor sync - Video update:', data.action, data.video_id);

      // Refresh data cuando hay cambios
      if (refreshCallbackRef.current) {
        refreshCallbackRef.current().catch(error => {
          console.error('🔗 Error refreshing cursor data:', error);
        });
      }
    };

    const handleCacheInvalidation = (event: CustomEvent<CacheInvalidationData>) => {
      const data = event.detail;
      console.log('🔗 Cursor sync - Cache invalidation:', data.cache_keys);

      // Refresh data cuando se invalida cache
      if (refreshCallbackRef.current) {
        refreshCallbackRef.current().catch(error => {
          console.error('🔗 Error refreshing cursor data:', error);
        });
      }
    };

    // Registrar event listeners
    window.addEventListener('websocket-video-update', handleVideoUpdate as EventListener);
    window.addEventListener('websocket-cache-invalidation', handleCacheInvalidation as EventListener);

    // Cleanup
    return () => {
      window.removeEventListener('websocket-video-update', handleVideoUpdate as EventListener);
      window.removeEventListener('websocket-cache-invalidation', handleCacheInvalidation as EventListener);
    };
  }, [refreshCallback]);

  return {
    // Proporcionar función para trigger manual refresh
    triggerRefresh: useCallback(() => {
      if (refreshCallbackRef.current) {
        return refreshCallbackRef.current();
      }
      return Promise.resolve();
    }, [])
  };
};

/**
 * Hook para integrar WebSocket con useCursorCRUD operations
 */
export const useCursorCRUDWebSocket = () => {

  // Función para notificar cambios via WebSocket
  const notifyVideoUpdate = useCallback(async (
    videoId: string,
    action: 'update' | 'delete' | 'restore' | 'move_to_trash',
    changes: Record<string, any> = {}
  ) => {
    try {
      const response = await fetch('/api/websocket/broadcast/video-update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_id: videoId,
          action,
          changes
        })
      });

      if (!response.ok) {
        console.warn('🔗 Error enviando video update via WebSocket');
      }
    } catch (error) {
      console.error('🔗 Error notificando video update:', error);
    }
  }, []);

  // Función para notificar invalidación de cache
  const notifyCacheInvalidation = useCallback(async (
    cacheKeys: string[],
    reason: string = 'manual_invalidation'
  ) => {
    try {
      const response = await fetch('/api/websocket/broadcast/cache-invalidate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          cache_keys: cacheKeys,
          reason
        })
      });

      if (!response.ok) {
        console.warn('🔗 Error enviando cache invalidation via WebSocket');
      }
    } catch (error) {
      console.error('🔗 Error notificando cache invalidation:', error);
    }
  }, []);

  return {
    notifyVideoUpdate,
    notifyCacheInvalidation
  };
};

export default useWebSocketUpdates;