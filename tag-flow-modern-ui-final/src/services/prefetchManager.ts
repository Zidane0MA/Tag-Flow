/**
 * 🚀 Intelligent Prefetching Manager
 * Sistema de prefetching predictivo para scroll infinito optimizado
 */

interface PrefetchConfig {
  threshold: number;        // % de scroll para activar prefetch
  maxPrefetchPages: number; // Máximo páginas a prefetch
  debounceMs: number;       // Debounce para scroll events
  enablePredictive: boolean; // Prefetch predictivo basado en patterns
}

interface ScrollMetrics {
  lastScrollTop: number;
  scrollDirection: 'up' | 'down' | 'idle';
  scrollVelocity: number; // pixels per second
  lastScrollTime: number;
  averageScrollSpeed: number;
}

interface PrefetchResult<T> {
  data: T[];
  cursor?: string;
  hasMore: boolean;
  cached: boolean;
  timestamp: number;
}

type DataLoader<T> = (cursor?: string) => Promise<PrefetchResult<T>>;

class IntelligentPrefetchManager<T = any> {
  private config: PrefetchConfig = {
    threshold: 0.75,     // 75% del scroll
    maxPrefetchPages: 3, // 3 páginas adelante
    debounceMs: 150,     // 150ms debounce
    enablePredictive: true
  };

  private prefetchCache = new Map<string, PrefetchResult<T>>();
  private prefetchPromises = new Map<string, Promise<PrefetchResult<T>>>();
  private scrollMetrics: ScrollMetrics = {
    lastScrollTop: 0,
    scrollDirection: 'idle',
    scrollVelocity: 0,
    lastScrollTime: Date.now(),
    averageScrollSpeed: 0
  };

  private scrollHandler: (event: Event) => void;
  private isActive = false;
  private dataLoader: DataLoader<T> | null = null;
  private currentCursor: string | undefined;

  constructor(config?: Partial<PrefetchConfig>) {
    this.config = { ...this.config, ...config };
    this.scrollHandler = this.debounce(this.handleScroll.bind(this), this.config.debounceMs);
  }

  /**
   * Inicializar prefetching para un contenedor
   */
  initPrefetch(
    containerId: string,
    dataLoader: DataLoader<T>,
    initialCursor?: string
  ): void {
    const container = document.getElementById(containerId);
    if (!container) {
      console.warn(`🚀 Prefetch: Container ${containerId} not found`);
      return;
    }

    this.dataLoader = dataLoader;
    this.currentCursor = initialCursor;
    this.isActive = true;

    // Registrar scroll listener
    container.addEventListener('scroll', this.scrollHandler, { passive: true });

    // Prefetch inicial si tenemos cursor
    if (initialCursor && this.config.enablePredictive) {
      this.prefetchNext(initialCursor, 1);
    }

    console.log(`🚀 Prefetch inicializado para ${containerId}`);
  }

  /**
   * Cleanup de event listeners
   */
  cleanup(containerId?: string): void {
    this.isActive = false;

    if (containerId) {
      const container = document.getElementById(containerId);
      if (container) {
        container.removeEventListener('scroll', this.scrollHandler);
      }
    }

    // Clear caches
    this.prefetchCache.clear();
    this.prefetchPromises.clear();

    console.log('🚀 Prefetch cleanup completado');
  }

  /**
   * Obtener datos prefetched si están disponibles
   */
  getPrefetchedData(cursor: string): PrefetchResult<T> | null {
    const cached = this.prefetchCache.get(cursor);
    if (cached && Date.now() - cached.timestamp < 300000) { // 5 minutos TTL
      console.log(`🚀 Cache hit para cursor: ${cursor}`);
      return { ...cached, cached: true };
    }
    return null;
  }

  /**
   * Actualizar cursor actual para prefetching
   */
  updateCurrentCursor(cursor: string | undefined): void {
    this.currentCursor = cursor;

    // Trigger prefetch si estamos cerca del final
    if (cursor && this.config.enablePredictive && this.isActive) {
      // Prefetch preventivo
      this.prefetchNext(cursor, 1);
    }
  }

  /**
   * Manejar evento de scroll
   */
  private handleScroll(event: Event): void {
    if (!this.isActive || !this.dataLoader) return;

    const container = event.target as HTMLElement;
    if (!container) return;

    // Actualizar métricas de scroll
    this.updateScrollMetrics(container);

    // Calcular progreso de scroll
    const scrollPercent = this.calculateScrollPercent(container);

    // Decidir si prefetch
    if (this.shouldPrefetch(scrollPercent)) {
      const cursor = this.getCurrentCursor(container);
      if (cursor) {
        // Determinar cuántas páginas prefetch basado en velocidad
        const pagesToPrefetch = this.calculatePrefetchPages();
        this.prefetchNext(cursor, pagesToPrefetch);
      }
    }
  }

  /**
   * Actualizar métricas de scroll
   */
  private updateScrollMetrics(container: HTMLElement): void {
    const now = Date.now();
    const currentScrollTop = container.scrollTop;
    const timeDelta = now - this.scrollMetrics.lastScrollTime;

    if (timeDelta > 0) {
      const scrollDelta = currentScrollTop - this.scrollMetrics.lastScrollTop;
      const velocity = Math.abs(scrollDelta) / timeDelta; // pixels per ms

      // Determinar dirección
      let direction: 'up' | 'down' | 'idle' = 'idle';
      if (scrollDelta > 2) direction = 'down';
      else if (scrollDelta < -2) direction = 'up';

      // Actualizar métricas
      this.scrollMetrics = {
        lastScrollTop: currentScrollTop,
        scrollDirection: direction,
        scrollVelocity: velocity,
        lastScrollTime: now,
        averageScrollSpeed: (this.scrollMetrics.averageScrollSpeed * 0.8) + (velocity * 0.2) // Moving average
      };
    }
  }

  /**
   * Calcular progreso de scroll
   */
  private calculateScrollPercent(container: HTMLElement): number {
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;

    if (scrollHeight <= clientHeight) return 1; // Already at bottom

    return scrollTop / (scrollHeight - clientHeight);
  }

  /**
   * Decidir si hacer prefetch
   */
  private shouldPrefetch(scrollPercent: number): boolean {
    // Prefetch basado en threshold normal
    if (scrollPercent >= this.config.threshold) return true;

    // Prefetch predictivo basado en velocidad
    if (this.config.enablePredictive && this.scrollMetrics.scrollDirection === 'down') {
      // Si está scrolleando rápido, prefetch antes
      const velocityThreshold = this.config.threshold - (this.scrollMetrics.averageScrollSpeed * 0.1);
      return scrollPercent >= Math.max(0.5, velocityThreshold);
    }

    return false;
  }

  /**
   * Calcular número de páginas a prefetch basado en velocidad
   */
  private calculatePrefetchPages(): number {
    if (!this.config.enablePredictive) return 1;

    // Más páginas para scroll rápido
    if (this.scrollMetrics.averageScrollSpeed > 2) return Math.min(this.config.maxPrefetchPages, 3);
    if (this.scrollMetrics.averageScrollSpeed > 1) return Math.min(this.config.maxPrefetchPages, 2);

    return 1;
  }

  /**
   * Obtener cursor del último elemento visible
   */
  private getCurrentCursor(container: HTMLElement): string | null {
    const items = container.querySelectorAll('[data-cursor]');
    if (items.length === 0) return this.currentCursor || null;

    // Obtener el último elemento que esté al menos 50% visible
    let lastVisibleCursor: string | null = null;
    const containerRect = container.getBoundingClientRect();

    for (let i = items.length - 1; i >= 0; i--) {
      const item = items[i] as HTMLElement;
      const itemRect = item.getBoundingClientRect();

      // Check if item is at least 50% visible
      const visibleHeight = Math.min(itemRect.bottom, containerRect.bottom) -
                           Math.max(itemRect.top, containerRect.top);
      const itemHeight = itemRect.height;

      if (visibleHeight > 0 && (visibleHeight / itemHeight) >= 0.5) {
        lastVisibleCursor = item.getAttribute('data-cursor');
        break;
      }
    }

    return lastVisibleCursor || this.currentCursor || null;
  }

  /**
   * Prefetch páginas siguientes
   */
  private async prefetchNext(cursor: string, pagesToPrefetch: number = 1): Promise<void> {
    if (!this.dataLoader) return;

    let currentCursor = cursor;

    for (let i = 0; i < pagesToPrefetch; i++) {
      const prefetchKey = `prefetch:${currentCursor}`;

      // Evitar prefetch duplicado
      if (this.prefetchPromises.has(prefetchKey) || this.prefetchCache.has(currentCursor)) {
        continue;
      }

      try {
        console.log(`🚀 Prefetching página ${i + 1}/${pagesToPrefetch} con cursor: ${currentCursor}`);

        const prefetchPromise = this.dataLoader(currentCursor);
        this.prefetchPromises.set(prefetchKey, prefetchPromise);

        const result = await prefetchPromise;

        // Guardar en cache
        this.prefetchCache.set(currentCursor, {
          ...result,
          cached: false,
          timestamp: Date.now()
        });

        // Actualizar cursor para siguiente página
        currentCursor = result.cursor || '';

        // Si no hay más datos, parar
        if (!result.hasMore || !currentCursor) {
          console.log(`🚀 Prefetch completado: no más datos disponibles`);
          break;
        }

      } catch (error) {
        console.warn(`🚀 Prefetch falló para cursor ${currentCursor}:`, error);
        break;
      } finally {
        this.prefetchPromises.delete(prefetchKey);
      }
    }
  }

  /**
   * Limpiar cache vencido
   */
  private cleanExpiredCache(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    for (const [key, value] of this.prefetchCache.entries()) {
      if (now - value.timestamp > 300000) { // 5 minutos
        expiredKeys.push(key);
      }
    }

    expiredKeys.forEach(key => this.prefetchCache.delete(key));

    if (expiredKeys.length > 0) {
      console.log(`🚀 Cleaned ${expiredKeys.length} expired cache entries`);
    }
  }

  /**
   * Debounce utility
   */
  private debounce(func: Function, wait: number): (event: Event) => void {
    let timeout: NodeJS.Timeout;
    return (event: Event) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(event), wait);
    };
  }

  /**
   * Obtener estadísticas de prefetch
   */
  getStats() {
    return {
      cacheSize: this.prefetchCache.size,
      activePrefetches: this.prefetchPromises.size,
      scrollMetrics: this.scrollMetrics,
      config: this.config,
      isActive: this.isActive
    };
  }

  /**
   * Actualizar configuración
   */
  updateConfig(newConfig: Partial<PrefetchConfig>): void {
    this.config = { ...this.config, ...newConfig };
    console.log('🚀 Prefetch config updated:', this.config);
  }
}

export default IntelligentPrefetchManager;
export type { PrefetchConfig, PrefetchResult, DataLoader };