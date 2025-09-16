"""
Tag-Flow V2 - Smart Caching System
Sistema de cacheo inteligente para datos frecuentemente accedidos
"""

import json
import time
import threading
import logging
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Entrada de cache con metadatos"""
    data: Any
    timestamp: float
    access_count: int
    ttl: float
    size_bytes: int

class SmartCache:
    """
    Sistema de cache inteligente con:
    - TTL (Time To Live) configurable
    - LRU eviction
    - Estadísticas de uso
    - Invalidación selectiva
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'invalidations': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None

            entry = self._cache[key]
            current_time = time.time()

            # Verificar TTL
            if current_time - entry.timestamp > entry.ttl:
                del self._cache[key]
                self._stats['misses'] += 1
                return None

            # Actualizar estadísticas de acceso
            entry.access_count += 1
            self._stats['hits'] += 1

            logger.debug(f"Cache HIT: {key} (accessed {entry.access_count} times)")
            return entry.data

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Almacenar valor en cache"""
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl

            # Calcular tamaño aproximado
            size_bytes = len(json.dumps(value, default=str)) if value else 0

            entry = CacheEntry(
                data=value,
                timestamp=time.time(),
                access_count=0,
                ttl=ttl,
                size_bytes=size_bytes
            )

            # Eviction si estamos en el límite
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            self._cache[key] = entry
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s, Size: {size_bytes}B)")

    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self._cache:
            return

        # Encontrar entry con menor access_count y más antiguo
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].access_count, self._cache[k].timestamp)
        )

        del self._cache[lru_key]
        self._stats['evictions'] += 1
        logger.debug(f"Cache EVICT: {lru_key}")

    def invalidate(self, pattern: str) -> int:
        """Invalidar entradas que coincidan con el patrón"""
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if pattern in key
            ]

            for key in keys_to_remove:
                del self._cache[key]
                self._stats['invalidations'] += 1

            logger.info(f"Cache INVALIDATE: {len(keys_to_remove)} entries with pattern '{pattern}'")
            return len(keys_to_remove)

    def clear(self) -> None:
        """Limpiar todo el cache"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache CLEAR: All entries removed")

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0

            total_size = sum(entry.size_bytes for entry in self._cache.values())

            return {
                **self._stats,
                'total_requests': total_requests,
                'hit_rate_percent': round(hit_rate, 2),
                'current_entries': len(self._cache),
                'max_size': self.max_size,
                'total_size_bytes': total_size,
                'avg_entry_size': total_size // len(self._cache) if self._cache else 0
            }

# Instancia global del cache
smart_cache = SmartCache(max_size=2000, default_ttl=600)  # 10 minutos TTL por defecto

def cached(ttl: int = 600, key_func: Optional[Callable] = None):
    """
    Decorador para cachear resultados de funciones

    Args:
        ttl: Tiempo de vida en segundos
        key_func: Función para generar la clave de cache
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Clave por defecto basada en función y argumentos
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Intentar obtener del cache
            result = smart_cache.get(cache_key)
            if result is not None:
                return result

            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            smart_cache.set(cache_key, result, ttl)
            return result

        # Agregar métodos útiles al wrapper
        wrapper.cache_invalidate = lambda pattern=None: smart_cache.invalidate(pattern or func.__name__)
        wrapper.cache_key = lambda *args, **kwargs: key_func(*args, **kwargs) if key_func else f"{func.__name__}:{args}:{kwargs}"

        return wrapper
    return decorator

# Funciones de utilidad para cache específico
class CacheManager:
    """Manager para operaciones de cache específicas del dominio"""

    @staticmethod
    def invalidate_creator_data(creator_name: str) -> None:
        """Invalidar todos los datos de cache relacionados con un creador"""
        patterns = [
            f"creator:{creator_name}",
            f"creator_stats:{creator_name}",
            f"creator_videos:{creator_name}"
        ]

        total_invalidated = 0
        for pattern in patterns:
            total_invalidated += smart_cache.invalidate(pattern)

        logger.info(f"Invalidated {total_invalidated} cache entries for creator: {creator_name}")

    @staticmethod
    def invalidate_platform_data(platform: str) -> None:
        """Invalidar datos de cache de una plataforma específica"""
        patterns = [
            f"platform:{platform}",
            f"platform_stats:{platform}"
        ]

        total_invalidated = 0
        for pattern in patterns:
            total_invalidated += smart_cache.invalidate(pattern)

        logger.info(f"Invalidated {total_invalidated} cache entries for platform: {platform}")

    @staticmethod
    def invalidate_global_stats() -> None:
        """Invalidar estadísticas globales"""
        smart_cache.invalidate("global_stats")
        smart_cache.invalidate("dashboard_stats")
        logger.info("Invalidated global stats cache")

    @staticmethod
    def warm_cache(db_connection) -> None:
        """Pre-cargar datos frecuentemente accedidos"""
        logger.info("🔥 Warming up cache with frequently accessed data...")

        try:
            # Pre-cargar estadísticas globales
            from src.api.stats.core import get_global_stats_cached
            get_global_stats_cached(db_connection)

            # Pre-cargar top creadores
            from src.api.creators import get_top_creators_cached
            get_top_creators_cached(db_connection, limit=20)

            logger.info("✅ Cache warmed up successfully")
        except Exception as e:
            logger.warning(f"Cache warm-up failed: {e}")

# Métricas de cache para monitoreo
def get_cache_metrics() -> Dict[str, Any]:
    """Obtener métricas detalladas del cache para monitoreo"""
    stats = smart_cache.get_stats()

    return {
        'cache_performance': {
            'hit_rate': stats['hit_rate_percent'],
            'total_requests': stats['total_requests'],
            'hits': stats['hits'],
            'misses': stats['misses']
        },
        'cache_management': {
            'current_entries': stats['current_entries'],
            'max_entries': stats['max_size'],
            'evictions': stats['evictions'],
            'invalidations': stats['invalidations']
        },
        'memory_usage': {
            'total_size_mb': stats['total_size_bytes'] / (1024 * 1024),
            'avg_entry_size_kb': stats['avg_entry_size'] / 1024,
            'utilization_percent': (stats['current_entries'] / stats['max_size']) * 100
        }
    }