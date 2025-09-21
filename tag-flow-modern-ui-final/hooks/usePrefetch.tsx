/**
 * 🚀 usePrefetch Hook - Intelligent Prefetching para Cursor Pagination
 * Integra prefetching predictivo con hooks cursor
 */

import { useEffect, useRef, useCallback } from 'react';
import IntelligentPrefetchManager, { PrefetchResult, DataLoader } from '../services/prefetchManager';
import { Post } from '../types';

interface UsePrefetchOptions {
  containerId: string;
  enabled?: boolean;
  threshold?: number;
  maxPrefetchPages?: number;
  enablePredictive?: boolean;
}

interface PrefetchHookReturn {
  getPrefetchedData: (cursor: string) => PrefetchResult<Post> | null;
  updateCursor: (cursor: string | undefined) => void;
  getStats: () => any;
  cleanup: () => void;
}

/**
 * Hook para intelligent prefetching en cursor pagination
 */
export const usePrefetch = (
  dataLoader: DataLoader<Post>,
  options: UsePrefetchOptions
): PrefetchHookReturn => {

  const {
    containerId,
    enabled = true,
    threshold = 0.75,
    maxPrefetchPages = 2,
    enablePredictive = true
  } = options;

  // Referencia al manager para evitar recreación
  const managerRef = useRef<IntelligentPrefetchManager<Post> | null>(null);
  const dataLoaderRef = useRef(dataLoader);

  // Actualizar dataLoader ref cuando cambie
  dataLoaderRef.current = dataLoader;

  // Inicializar manager una vez
  useEffect(() => {
    if (!enabled) return;

    managerRef.current = new IntelligentPrefetchManager<Post>({
      threshold,
      maxPrefetchPages,
      enablePredictive,
      debounceMs: 150
    });

    console.log(`🚀 Prefetch manager inicializado para ${containerId}`);

    return () => {
      if (managerRef.current) {
        managerRef.current.cleanup(containerId);
        managerRef.current = null;
      }
    };
  }, [containerId, enabled, threshold, maxPrefetchPages, enablePredictive]);

  // Inicializar prefetching cuando el container esté listo
  useEffect(() => {
    if (!enabled || !managerRef.current) return;

    const initPrefetch = () => {
      const container = document.getElementById(containerId);
      if (container && managerRef.current) {
        managerRef.current.initPrefetch(
          containerId,
          dataLoaderRef.current
        );
      } else {
        // Retry si el container no está listo
        setTimeout(initPrefetch, 100);
      }
    };

    initPrefetch();

    return () => {
      if (managerRef.current) {
        managerRef.current.cleanup(containerId);
      }
    };
  }, [containerId, enabled]);

  // Función para obtener datos prefetched
  const getPrefetchedData = useCallback((cursor: string): PrefetchResult<Post> | null => {
    if (!managerRef.current) return null;
    return managerRef.current.getPrefetchedData(cursor);
  }, []);

  // Función para actualizar cursor actual
  const updateCursor = useCallback((cursor: string | undefined) => {
    if (managerRef.current) {
      managerRef.current.updateCurrentCursor(cursor);
    }
  }, []);

  // Función para obtener estadísticas
  const getStats = useCallback(() => {
    return managerRef.current?.getStats() || null;
  }, []);

  // Función para cleanup manual
  const cleanup = useCallback(() => {
    if (managerRef.current) {
      managerRef.current.cleanup(containerId);
    }
  }, [containerId]);

  return {
    getPrefetchedData,
    updateCursor,
    getStats,
    cleanup
  };
};

/**
 * Hook específico para useCursorData con prefetching
 */
export const useCursorWithPrefetch = (
  dataLoader: DataLoader<Post>,
  containerId: string = 'gallery-container',
  options: Partial<UsePrefetchOptions> = {}
) => {
  const prefetch = usePrefetch(dataLoader, {
    containerId,
    enabled: true,
    threshold: 0.8,
    maxPrefetchPages: 3,
    enablePredictive: true,
    ...options
  });

  // Wrapper del dataLoader que usa prefetch
  const optimizedDataLoader = useCallback(async (cursor?: string): Promise<PrefetchResult<Post>> => {
    // Intentar obtener desde prefetch cache primero
    if (cursor) {
      const prefetched = prefetch.getPrefetchedData(cursor);
      if (prefetched) {
        console.log(`🚀 Using prefetched data for cursor: ${cursor}`);
        return prefetched;
      }
    }

    // Si no está en cache, cargar normalmente
    console.log(`🚀 Loading data normally for cursor: ${cursor}`);
    const result = await dataLoader(cursor);

    // Actualizar cursor para próximo prefetch
    prefetch.updateCursor(result.cursor);

    return result;
  }, [dataLoader, prefetch]);

  return {
    optimizedDataLoader,
    ...prefetch
  };
};

export default usePrefetch;