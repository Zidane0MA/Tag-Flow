"""
🚀 MIGRADO: Cache Manager Unificado con TTL
Sistema centralizado de cache combinando las mejores funcionalidades de pattern_cache.py
"""

import time
import threading
from typing import Any, Callable, Dict, Set, List, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """
    🚀 OPTIMIZADO: Gestor de cache unificado con TTL y LRU
    
    Características migradas:
    - Cache LRU con límite de tamaño
    - TTL (Time-To-Live) automático
    - Thread-safe para concurrencia
    - Invalidación selectiva por patrón
    - Métricas de performance
    - Estimación de uso de memoria
    """
    
    def __init__(self, max_size: int = 1000, default_ttl_seconds: int = 300):
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        
        # Cache principal: {key: (value, timestamp, ttl_seconds)}
        self.cache = {}
        
        # Control de acceso para LRU
        self.access_order = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Métricas de performance
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.invalidations = 0
        
        # Configuración por categoría
        self.category_ttls = {}  # {category: ttl_seconds}
        
        logger.info(f"🚀 CacheManager inicializado: max_size={max_size}, ttl={default_ttl_seconds}s")
    
    def get_or_compute(self, key: str, compute_func: Callable, *args, 
                      ttl_seconds: Optional[int] = None, category: str = None, **kwargs) -> Any:
        """
        🚀 OPTIMIZADO: Obtener valor del cache o computarlo con TTL
        
        Args:
            key: Clave única del cache
            compute_func: Función para computar el valor si no está en cache
            ttl_seconds: TTL específico (usa default si no se proporciona)
            category: Categoría para organización y TTL específico
            *args, **kwargs: Argumentos para compute_func
            
        Returns:
            Valor cacheado o recién computado
        """
        with self._lock:
            current_time = time.time()
            
            # Verificar si existe y es válido
            if key in self.cache:
                if len(self.cache[key]) == 3:
                    value, timestamp, stored_ttl = self.cache[key]
                    effective_ttl = stored_ttl if stored_ttl else self._get_effective_ttl(key, ttl_seconds, category)
                else:
                    # Formato anterior (value, timestamp) - migrar
                    value, timestamp = self.cache[key]
                    effective_ttl = self._get_effective_ttl(key, ttl_seconds, category)
                
                if current_time - timestamp < effective_ttl:
                    # Cache hit válido
                    self.hits += 1
                    self._update_access_order(key)
                    logger.debug(f"💾 Cache HIT: {key}")
                    return value
                else:
                    # TTL expirado, remover
                    del self.cache[key]
                    if key in self.access_order:
                        self.access_order.remove(key)
                    logger.debug(f"⏰ Cache EXPIRED: {key}")
            
            # Cache miss - computar valor
            self.misses += 1
            logger.debug(f"🔄 Cache MISS: {key}")
            
            value = compute_func(*args, **kwargs)
            
            # Determinar TTL efectivo para almacenar
            effective_ttl = self._get_effective_ttl(key, ttl_seconds, category)
            
            # Agregar al cache
            self._add_to_cache(key, value, current_time, effective_ttl)
            
            return value
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache sin computar (puede retornar None)"""
        with self._lock:
            if key not in self.cache:
                return None
            
            if len(self.cache[key]) == 3:
                value, timestamp, stored_ttl = self.cache[key]
                effective_ttl = stored_ttl if stored_ttl else self._get_effective_ttl(key)
            else:
                # Formato anterior (value, timestamp)
                value, timestamp = self.cache[key]
                effective_ttl = self._get_effective_ttl(key)
            
            current_time = time.time()
            
            # Verificar TTL
            if current_time - timestamp >= effective_ttl:
                # Expirado
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                return None
            
            self.hits += 1
            self._update_access_order(key)
            return value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, category: str = None):
        """Establecer valor en cache manualmente"""
        with self._lock:
            current_time = time.time()
            
            # Determinar TTL efectivo
            effective_ttl = ttl_seconds if ttl_seconds else self._get_effective_ttl(key, ttl_seconds, category)
            
            self._add_to_cache(key, value, current_time, effective_ttl)
            
            # Configurar TTL por categoría si se proporciona
            if category and ttl_seconds:
                self.category_ttls[category] = ttl_seconds
    
    def invalidate(self, key: str):
        """Invalidar una clave específica"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                self.invalidations += 1
                logger.debug(f"🗑️ Cache INVALIDATED: {key}")
    
    def invalidate_by_pattern(self, pattern: str):
        """Invalidar todas las claves que contengan el patrón"""
        with self._lock:
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            
            for key in keys_to_remove:
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                self.invalidations += 1
            
            if keys_to_remove:
                logger.info(f"🗑️ Cache PATTERN INVALIDATION: '{pattern}' -> {len(keys_to_remove)} keys")
    
    def invalidate_category(self, category: str):
        """Invalidar todas las claves de una categoría"""
        self.invalidate_by_pattern(f"{category}:")
    
    def clear(self):
        """Limpiar todo el cache"""
        with self._lock:
            cleared_count = len(self.cache)
            self.cache.clear()
            self.access_order.clear()
            self.invalidations += cleared_count
            logger.info(f"🗑️ Cache CLEARED: {cleared_count} keys removed")
    
    def cleanup_expired(self):
        """Limpiar entradas expiradas manualmente"""
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, cache_entry in self.cache.items():
                if len(cache_entry) == 3:
                    value, timestamp, stored_ttl = cache_entry
                    effective_ttl = stored_ttl if stored_ttl else self._get_effective_ttl(key)
                else:
                    value, timestamp = cache_entry
                    effective_ttl = self._get_effective_ttl(key)
                
                if current_time - timestamp >= effective_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
            
            if expired_keys:
                logger.info(f"🧹 Cache CLEANUP: {len(expired_keys)} expired keys removed")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        🚀 OPTIMIZADO: Obtener estadísticas detalladas del cache
        
        Returns:
            Diccionario con métricas completas
        """
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / max(1, total_requests)) * 100
            
            # Análisis de TTL por categoría
            category_stats = {}
            for category, ttl in self.category_ttls.items():
                category_keys = [k for k in self.cache.keys() if k.startswith(f"{category}:")]
                category_stats[category] = {
                    'ttl_seconds': ttl,
                    'keys_count': len(category_keys)
                }
            
            return {
                'cache_size': len(self.cache),
                'max_size': self.max_size,
                'usage_percentage': round((len(self.cache) / self.max_size) * 100, 1),
                'hits': self.hits,
                'misses': self.misses,
                'total_requests': total_requests,
                'hit_rate_percentage': round(hit_rate, 1),
                'evictions': self.evictions,
                'invalidations': self.invalidations,
                'default_ttl_seconds': self.default_ttl_seconds,
                'categories': category_stats,
                'efficiency_grade': self._calculate_efficiency_grade(hit_rate)
            }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        🚀 OPTIMIZADO: Estimación de uso de memoria
        
        Returns:
            Diccionario con estimaciones de memoria
        """
        import sys
        
        with self._lock:
            # Estimar memoria del cache principal
            cache_memory = sys.getsizeof(self.cache)
            for key, cache_entry in self.cache.items():
                cache_memory += sys.getsizeof(key)
                if len(cache_entry) == 3:
                    value, timestamp, stored_ttl = cache_entry
                    cache_memory += sys.getsizeof(value) + sys.getsizeof(timestamp) + sys.getsizeof(stored_ttl)
                else:
                    value, timestamp = cache_entry
                    cache_memory += sys.getsizeof(value) + sys.getsizeof(timestamp)
            
            # Memoria de estructuras auxiliares
            access_order_memory = sys.getsizeof(self.access_order)
            category_ttls_memory = sys.getsizeof(self.category_ttls)
            
            total_memory = cache_memory + access_order_memory + category_ttls_memory
            
            return {
                'cache_memory_bytes': cache_memory,
                'cache_memory_mb': round(cache_memory / (1024 * 1024), 2),
                'auxiliary_memory_bytes': access_order_memory + category_ttls_memory,
                'total_memory_mb': round(total_memory / (1024 * 1024), 2),
                'avg_memory_per_key_bytes': round(cache_memory / max(1, len(self.cache)), 2)
            }
    
    def _add_to_cache(self, key: str, value: Any, timestamp: float, ttl_seconds: Optional[int] = None):
        """Agregar valor al cache con gestión de tamaño"""
        # Verificar si necesitamos hacer espacio
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()
        
        # Agregar/actualizar valor con TTL
        self.cache[key] = (value, timestamp, ttl_seconds)
        self._update_access_order(key)
    
    def _update_access_order(self, key: str):
        """Actualizar orden de acceso para LRU"""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def _evict_lru(self):
        """Eliminar la entrada menos recientemente usada"""
        if self.access_order:
            lru_key = self.access_order.pop(0)
            if lru_key in self.cache:
                del self.cache[lru_key]
                self.evictions += 1
                logger.debug(f"🚮 Cache LRU EVICTION: {lru_key}")
    
    def _get_effective_ttl(self, key: str, ttl_seconds: Optional[int] = None, 
                          category: str = None) -> int:
        """Determinar TTL efectivo para una clave"""
        if ttl_seconds:
            return ttl_seconds
        
        # Buscar TTL por categoría
        if category and category in self.category_ttls:
            return self.category_ttls[category]
        
        # Intentar extraer categoría del key (formato "category:key")
        if ':' in key:
            key_category = key.split(':', 1)[0]
            if key_category in self.category_ttls:
                return self.category_ttls[key_category]
        
        return self.default_ttl_seconds
    
    def _calculate_efficiency_grade(self, hit_rate: float) -> str:
        """Calcular grado de eficiencia del cache"""
        if hit_rate >= 90:
            return 'EXCELLENT'
        elif hit_rate >= 75:
            return 'GOOD'
        elif hit_rate >= 60:
            return 'AVERAGE'
        else:
            return 'NEEDS_IMPROVEMENT'

# Instancia global del cache manager
_global_cache_manager = None
_cache_lock = threading.Lock()

def get_global_cache_manager() -> CacheManager:
    """
    🚀 OPTIMIZADO: Obtener instancia global del cache manager
    
    Returns:
        Instancia singleton thread-safe del CacheManager
    """
    global _global_cache_manager
    
    if _global_cache_manager is None:
        with _cache_lock:
            if _global_cache_manager is None:
                _global_cache_manager = CacheManager()
                logger.info("🚀 Global CacheManager creado")
    
    return _global_cache_manager

def get_specialized_cache(category: str, ttl_seconds: int = 300, max_size: int = 500) -> CacheManager:
    """
    🚀 OPTIMIZADO: Crear cache especializado para una categoría específica
    
    Args:
        category: Nombre de la categoría
        ttl_seconds: TTL específico para esta categoría
        max_size: Tamaño máximo específico
        
    Returns:
        CacheManager configurado para la categoría
    """
    cache = CacheManager(max_size=max_size, default_ttl_seconds=ttl_seconds)
    cache.category_ttls[category] = ttl_seconds
    logger.info(f"🚀 Specialized cache created for '{category}': ttl={ttl_seconds}s, max_size={max_size}")
    return cache

# Funciones de conveniencia para compatibilidad con pattern_cache.py
def clear_global_cache():
    """Limpiar cache global (compatibilidad)"""
    cache = get_global_cache_manager()
    cache.clear()

def get_cache_stats() -> Dict[str, Any]:
    """Obtener estadísticas del cache global (compatibilidad)"""
    cache = get_global_cache_manager()
    return cache.get_stats()

def get_pending_videos_cached(cache_key: str, db_manager, platform_filter: str = None, 
                             source_filter: str = 'all', limit: int = None) -> List[Dict]:
    """
    🚀 OPTIMIZADO: Cache inteligente para videos pendientes
    
    Args:
        cache_key: Clave única para el cache
        db_manager: Manager de base de datos
        platform_filter: Filtro de plataforma
        source_filter: Filtro de fuente
        limit: Límite de resultados
        
    Returns:
        Lista de videos pendientes cacheados
    """
    cache = get_global_cache_manager()
    
    def fetch_pending_videos():
        return db_manager.get_pending_videos_filtered(platform_filter, source_filter, limit)
    
    # Usar TTL de 5 minutos para videos pendientes (datos que cambian frecuentemente)
    return cache.get_or_compute(cache_key, fetch_pending_videos, ttl_seconds=300)

def get_existing_paths_cached(db_manager) -> set:
    """
    🚀 OPTIMIZADO: Cache para paths existentes con invalidación inteligente
    
    Args:
        db_manager: Manager de base de datos
        
    Returns:
        Set de paths existentes cacheados
    """
    cache = get_global_cache_manager()
    
    def fetch_existing_paths():
        return db_manager.get_existing_paths_only()
    
    # Usar TTL de 10 minutos para paths existentes (datos más estables)
    return cache.get_or_compute("existing_paths", fetch_existing_paths, ttl_seconds=600)

def invalidate_paths_cache():
    """Invalidar cache de paths cuando se modifica la BD"""
    cache = get_global_cache_manager()
    cache.invalidate_by_pattern("existing_paths")
    logger.info("🗑️ Cache de paths invalidado")

def invalidate_pending_cache():
    """Invalidar cache de videos pendientes cuando cambia el estado"""
    cache = get_global_cache_manager()
    cache.invalidate_by_pattern("pending_")
    logger.info("🗑️ Cache de videos pendientes invalidado")