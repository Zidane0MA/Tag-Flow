/**
 * 🚀 Unified Cache Manager para Tag-Flow V2
 * Sistema de cache unificado que coordina entre frontend y backend
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time To Live en milliseconds
  accessCount: number;
  size: number; // Estimación de tamaño en bytes
  source: 'local' | 'api' | 'prefetch';
}

interface CacheStats {
  totalEntries: number;
  hitCount: number;
  missCount: number;
  hitRate: number;
  totalSizeBytes: number;
  avgSizeBytes: number;
  mostAccessed: Array<{ key: string; accessCount: number }>;
}

interface CacheInvalidationEvent {
  type: 'pattern' | 'specific' | 'category' | 'clear';
  target: string;
  timestamp: number;
}

class UnifiedCacheManager {
  private cache: Map<string, CacheEntry<any>> = new Map();
  private maxEntries: number;
  private defaultTtl: number;
  private hitCount: number = 0;
  private missCount: number = 0;
  private invalidationListeners: Array<(event: CacheInvalidationEvent) => void> = [];

  // Configuración por categoría
  private categoryTtls: Map<string, number> = new Map([
    ['videos', 5 * 60 * 1000], // 5 minutos
    ['creators', 10 * 60 * 1000], // 10 minutos
    ['stats', 2 * 60 * 1000], // 2 minutos
    ['prefetch', 15 * 60 * 1000], // 15 minutos
    ['cursor-results', 3 * 60 * 1000], // 3 minutos
    ['subscription', 10 * 60 * 1000], // 10 minutos
  ]);

  constructor(maxEntries: number = 500, defaultTtl: number = 5 * 60 * 1000) {
    this.maxEntries = maxEntries;
    this.defaultTtl = defaultTtl;

    // Auto-cleanup cada 2 minutos
    setInterval(() => {
      this.cleanupExpired();
    }, 2 * 60 * 1000);

    console.log(`🚀 UnifiedCacheManager initialized: max=${maxEntries}, ttl=${defaultTtl}ms`);
  }

  /**
   * Obtener datos del cache con validación TTL
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      this.missCount++;
      return null;
    }

    // Verificar TTL
    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      this.missCount++;
      console.debug(`🗑️ Cache expired: ${key}`);
      return null;
    }

    // Cache hit válido
    entry.accessCount++;
    this.hitCount++;
    console.debug(`💾 Cache HIT: ${key}`);
    return entry.data;
  }

  /**
   * Establecer datos en cache con TTL automático por categoría
   */
  set<T>(key: string, data: T, options: {
    ttl?: number;
    category?: string;
    source?: 'local' | 'api' | 'prefetch';
  } = {}): void {
    const { ttl, category, source = 'local' } = options;

    // Determinar TTL efectivo
    const effectiveTtl = ttl ||
      (category && this.categoryTtls.get(category)) ||
      this.defaultTtl;

    // Crear entrada de cache
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl: effectiveTtl,
      accessCount: 1,
      size: this.estimateSize(data),
      source
    };

    this.cache.set(key, entry);

    // Eviction si es necesario
    this.evictIfNeeded();

    console.debug(`📝 Cache SET: ${key}, ttl=${effectiveTtl}ms, source=${source}`);
  }

  /**
   * Obtener o computar valor con cache automático
   */
  async getOrCompute<T>(
    key: string,
    computeFn: () => Promise<T>,
    options: {
      ttl?: number;
      category?: string;
      source?: 'local' | 'api' | 'prefetch';
    } = {}
  ): Promise<T> {
    // Intentar obtener del cache primero
    const cached = this.get<T>(key);
    if (cached !== null) {
      return cached;
    }

    // Computar valor
    const data = await computeFn();

    // Guardar en cache
    this.set(key, data, options);

    return data;
  }

  /**
   * Invalidar entrada específica
   */
  invalidate(key: string): boolean {
    const deleted = this.cache.delete(key);
    if (deleted) {
      console.debug(`🗑️ Cache invalidated: ${key}`);
      this.notifyInvalidation({ type: 'specific', target: key, timestamp: Date.now() });
    }
    return deleted;
  }

  /**
   * Invalidar por patrón (wildcards soportados)
   */
  invalidatePattern(pattern: string): number {
    const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
    const keysToDelete: string[] = [];

    Array.from(this.cache.keys()).forEach(key => {
      if (regex.test(key)) {
        keysToDelete.push(key);
      }
    });

    keysToDelete.forEach(key => this.cache.delete(key));

    if (keysToDelete.length > 0) {
      console.log(`🗑️ Cache pattern invalidation: '${pattern}' -> ${keysToDelete.length} keys`);
      this.notifyInvalidation({ type: 'pattern', target: pattern, timestamp: Date.now() });
    }

    return keysToDelete.length;
  }

  /**
   * Invalidar por categoría
   */
  invalidateCategory(category: string): number {
    return this.invalidatePattern(`${category}:*`);
  }

  /**
   * Invalidaciones específicas para entidades
   */
  invalidateCreator(creatorName: string): number {
    return this.invalidatePattern(`*creator:${creatorName}*`);
  }

  invalidatePlatform(platform: string): number {
    return this.invalidatePattern(`*platform:${platform}*`);
  }

  invalidateVideo(videoId: string): number {
    return this.invalidatePattern(`*video:${videoId}*`);
  }

  /**
   * Limpiar todo el cache
   */
  clear(): number {
    const count = this.cache.size;
    this.cache.clear();
    this.hitCount = 0;
    this.missCount = 0;

    console.log(`🧹 Cache cleared: ${count} entries removed`);
    this.notifyInvalidation({ type: 'clear', target: 'all', timestamp: Date.now() });

    return count;
  }

  /**
   * Limpiar entradas expiradas manualmente
   */
  cleanupExpired(): number {
    const now = Date.now();
    const expiredKeys: string[] = [];

    Array.from(this.cache.entries()).forEach(([key, entry]) => {
      if (now - entry.timestamp > entry.ttl) {
        expiredKeys.push(key);
      }
    });

    expiredKeys.forEach(key => this.cache.delete(key));

    if (expiredKeys.length > 0) {
      console.debug(`🧹 Cache cleanup: ${expiredKeys.length} expired entries removed`);
    }

    return expiredKeys.length;
  }

  /**
   * Obtener estadísticas del cache
   */
  getStats(): CacheStats {
    const totalRequests = this.hitCount + this.missCount;
    const hitRate = totalRequests > 0 ? (this.hitCount / totalRequests) * 100 : 0;

    // Calcular tamaño total
    let totalSize = 0;
    const accessCounts: Array<{ key: string; accessCount: number }> = [];

    Array.from(this.cache.entries()).forEach(([key, entry]) => {
      totalSize += entry.size;
      accessCounts.push({ key, accessCount: entry.accessCount });
    });

    // Ordenar por acceso
    accessCounts.sort((a, b) => b.accessCount - a.accessCount);

    return {
      totalEntries: this.cache.size,
      hitCount: this.hitCount,
      missCount: this.missCount,
      hitRate: Math.round(hitRate * 100) / 100,
      totalSizeBytes: totalSize,
      avgSizeBytes: this.cache.size > 0 ? Math.round(totalSize / this.cache.size) : 0,
      mostAccessed: accessCounts.slice(0, 5)
    };
  }

  /**
   * Construir clave de cache consistente
   */
  buildKey(prefix: string, params: Record<string, any>): string {
    const keyParts = [prefix];

    // Ordenar parámetros para consistencia
    const sortedParams = Object.keys(params)
      .sort()
      .map(key => {
        const value = params[key];
        if (value !== null && value !== undefined) {
          return `${key}:${value}`;
        }
        return null;
      })
      .filter(Boolean);

    return [...keyParts, ...sortedParams].join(':');
  }

  /**
   * Funciones específicas para cursor pagination
   */
  cacheCursorResult(filters: Record<string, any>, cursor: string | undefined, result: any): string {
    const key = this.buildKey('cursor:videos', { cursor, ...filters });
    this.set(key, result, { category: 'cursor-results', source: 'api' });
    return key;
  }

  getCursorResult(filters: Record<string, any>, cursor: string | undefined): any | null {
    const key = this.buildKey('cursor:videos', { cursor, ...filters });
    return this.get(key);
  }

  /**
   * Funciones para prefetching
   */
  cachePrefetchResult(cursor: string, result: any): string {
    const key = this.buildKey('prefetch:data', { cursor });
    this.set(key, result, { category: 'prefetch', source: 'prefetch' });
    return key;
  }

  getPrefetchResult(cursor: string): any | null {
    const key = this.buildKey('prefetch:data', { cursor });
    return this.get(key);
  }

  /**
   * Funciones para coordinar con WebSocket invalidation
   */
  onInvalidation(listener: (event: CacheInvalidationEvent) => void): void {
    this.invalidationListeners.push(listener);
  }

  offInvalidation(listener: (event: CacheInvalidationEvent) => void): void {
    const index = this.invalidationListeners.indexOf(listener);
    if (index > -1) {
      this.invalidationListeners.splice(index, 1);
    }
  }

  private notifyInvalidation(event: CacheInvalidationEvent): void {
    this.invalidationListeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('Error in cache invalidation listener:', error);
      }
    });
  }

  /**
   * Eviction LRU cuando se alcanza el límite
   */
  private evictIfNeeded(): void {
    if (this.cache.size <= this.maxEntries) {
      return;
    }

    // Calcular score LRU (edad + factor de acceso)
    const entries: Array<{ key: string; score: number }> = [];
    const now = Date.now();

    Array.from(this.cache.entries()).forEach(([key, entry]) => {
      const ageScore = now - entry.timestamp;
      const accessScore = 1000 / (entry.accessCount + 1); // Invertir para menos acceso = más score
      const score = ageScore + accessScore;
      entries.push({ key, score });
    });

    // Ordenar por score LRU (mayor score = más candidato a eviction)
    entries.sort((a, b) => b.score - a.score);

    // Eliminar entradas hasta estar dentro del límite
    const entriesToRemove = this.cache.size - this.maxEntries + 1;
    for (let i = 0; i < entriesToRemove && i < entries.length; i++) {
      const keyToRemove = entries[i].key;
      this.cache.delete(keyToRemove);
      console.debug(`🚮 Cache LRU eviction: ${keyToRemove}`);
    }
  }

  /**
   * Estimar tamaño en bytes de los datos
   */
  private estimateSize(data: any): number {
    try {
      if (typeof data === 'string') {
        return data.length * 2; // Unicode aprox
      } else if (typeof data === 'number') {
        return 8; // 64-bit number
      } else if (typeof data === 'boolean') {
        return 1;
      } else if (Array.isArray(data) || typeof data === 'object') {
        return JSON.stringify(data).length * 2;
      }
      return 1024; // Default
    } catch {
      return 1024; // Fallback
    }
  }
}

// Instancia global singleton
let globalCacheManager: UnifiedCacheManager | null = null;

export const getCacheManager = (): UnifiedCacheManager => {
  if (!globalCacheManager) {
    globalCacheManager = new UnifiedCacheManager();
  }
  return globalCacheManager;
};

// Funciones de conveniencia
export const cacheManager = {
  get: <T>(key: string) => getCacheManager().get<T>(key),
  set: <T>(key: string, data: T, options?: any) => getCacheManager().set(key, data, options),
  getOrCompute: <T>(key: string, computeFn: () => Promise<T>, options?: any) =>
    getCacheManager().getOrCompute(key, computeFn, options),
  invalidate: (key: string) => getCacheManager().invalidate(key),
  invalidatePattern: (pattern: string) => getCacheManager().invalidatePattern(pattern),
  invalidateCategory: (category: string) => getCacheManager().invalidateCategory(category),
  invalidateCreator: (creatorName: string) => getCacheManager().invalidateCreator(creatorName),
  invalidatePlatform: (platform: string) => getCacheManager().invalidatePlatform(platform),
  invalidateVideo: (videoId: string) => getCacheManager().invalidateVideo(videoId),
  clear: () => getCacheManager().clear(),
  getStats: () => getCacheManager().getStats(),
  buildKey: (prefix: string, params: Record<string, any>) => getCacheManager().buildKey(prefix, params),

  // Cache específico para cursor pagination
  cacheCursorResult: (filters: Record<string, any>, cursor: string | undefined, result: any) =>
    getCacheManager().cacheCursorResult(filters, cursor, result),
  getCursorResult: (filters: Record<string, any>, cursor: string | undefined) =>
    getCacheManager().getCursorResult(filters, cursor),

  // Cache para prefetching
  cachePrefetchResult: (cursor: string, result: any) =>
    getCacheManager().cachePrefetchResult(cursor, result),
  getPrefetchResult: (cursor: string) =>
    getCacheManager().getPrefetchResult(cursor)
};

export default UnifiedCacheManager;
export type { CacheStats, CacheInvalidationEvent };