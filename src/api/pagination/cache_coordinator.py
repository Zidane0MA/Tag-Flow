"""
Tag-Flow V2 - Cache Coordinator
Coordinador de cachés unificado para optimizar performance de cursor pagination
"""

import time
import json
import logging
from typing import Dict, Any, Optional, List
from threading import Lock
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Entrada de cache con TTL y metadatos"""
    data: Any
    timestamp: float
    ttl: float
    access_count: int
    cache_key: str
    size_bytes: int

class CacheCoordinator:
    """
    Coordinador de cachés unificado
    Maneja invalidación, TTL y optimización de memoria
    """

    def __init__(self, max_entries: int = 100, default_ttl: float = 300.0):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.lock = Lock()
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        """Obtener entrada del cache con validación TTL"""
        with self.lock:
            entry = self.cache.get(key)
            if not entry:
                self.miss_count += 1
                return None

            # Verificar TTL
            if time.time() - entry.timestamp > entry.ttl:
                del self.cache[key]
                self.miss_count += 1
                logger.debug(f"Cache entry expired: {key}")
                return None

            # Actualizar estadísticas
            entry.access_count += 1
            self.hit_count += 1
            logger.debug(f"Cache hit: {key}")
            return entry.data

    def set(self, key: str, data: Any, ttl: Optional[float] = None) -> bool:
        """Almacenar entrada en cache con TTL"""
        with self.lock:
            try:
                # Calcular tamaño aproximado
                size_bytes = self._estimate_size(data)

                entry = CacheEntry(
                    data=data,
                    timestamp=time.time(),
                    ttl=ttl or self.default_ttl,
                    access_count=1,
                    cache_key=key,
                    size_bytes=size_bytes
                )

                self.cache[key] = entry

                # Eviction si es necesario
                self._evict_if_needed()

                logger.debug(f"Cache set: {key}, size: {size_bytes} bytes")
                return True

            except Exception as e:
                logger.error(f"Error setting cache entry {key}: {e}")
                return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidar entradas que coincidan con patrón
        Soporta wildcards básicos (*)
        """
        with self.lock:
            keys_to_delete = []

            # Convertir patrón a regex simple
            import re
            regex_pattern = pattern.replace('*', '.*')
            regex = re.compile(f"^{regex_pattern}$")

            for key in self.cache.keys():
                if regex.match(key):
                    keys_to_delete.append(key)

            # Eliminar entradas
            for key in keys_to_delete:
                del self.cache[key]

            logger.info(f"Invalidated {len(keys_to_delete)} cache entries with pattern: {pattern}")
            return len(keys_to_delete)

    def invalidate_creator(self, creator_name: str) -> int:
        """Invalidar cache relacionado con un creador específico"""
        return self.invalidate_pattern(f"*creator:{creator_name}*")

    def invalidate_platform(self, platform: str) -> int:
        """Invalidar cache relacionado con una plataforma específica"""
        return self.invalidate_pattern(f"*platform:{platform}*")

    def invalidate_subscription(self, subscription_id: int) -> int:
        """Invalidar cache relacionado con una suscripción específica"""
        return self.invalidate_pattern(f"*subscription:{subscription_id}*")

    def clear_all(self) -> int:
        """Limpiar todo el cache"""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            self.hit_count = 0
            self.miss_count = 0
            logger.info(f"Cache cleared: {count} entries removed")
            return count

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0

            # Calcular uso de memoria
            total_size = sum(entry.size_bytes for entry in self.cache.values())

            # Obtener entradas más accedidas
            most_accessed = sorted(
                self.cache.items(),
                key=lambda x: x[1].access_count,
                reverse=True
            )[:5]

            return {
                'total_entries': len(self.cache),
                'max_entries': self.max_entries,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate_percent': round(hit_rate, 2),
                'total_size_bytes': total_size,
                'avg_size_bytes': round(total_size / len(self.cache)) if self.cache else 0,
                'most_accessed': [
                    {'key': key, 'access_count': entry.access_count}
                    for key, entry in most_accessed
                ]
            }

    def _evict_if_needed(self):
        """Eviction LRU cuando se alcanza el límite"""
        if len(self.cache) <= self.max_entries:
            return

        # Calcular LRU score (menos accedido + más viejo)
        entries_with_score = []
        current_time = time.time()

        for key, entry in self.cache.items():
            age_score = current_time - entry.timestamp
            access_score = 1.0 / (entry.access_count + 1)  # Invertir para que menos acceso = más score
            lru_score = age_score + access_score
            entries_with_score.append((key, lru_score))

        # Ordenar por score LRU (mayor score = más candidato a eviction)
        entries_with_score.sort(key=lambda x: x[1], reverse=True)

        # Eliminar las entradas más viejas/menos usadas
        entries_to_remove = len(self.cache) - self.max_entries + 1
        for i in range(entries_to_remove):
            if i < len(entries_with_score):
                key_to_remove = entries_with_score[i][0]
                removed_entry = self.cache.pop(key_to_remove, None)
                if removed_entry:
                    logger.debug(f"Evicted cache entry: {key_to_remove}")

    def _estimate_size(self, data: Any) -> int:
        """Estimar tamaño en bytes de los datos"""
        try:
            if isinstance(data, (str, int, float, bool)):
                return len(str(data).encode('utf-8'))
            elif isinstance(data, (list, dict)):
                return len(json.dumps(data, default=str).encode('utf-8'))
            else:
                return len(str(data).encode('utf-8'))
        except Exception:
            return 1024  # Tamaño por defecto si no se puede estimar

    def build_cache_key(self, prefix: str, **kwargs) -> str:
        """
        Construir clave de cache consistente

        Args:
            prefix: Prefijo del cache (ej: 'videos', 'creator', 'subscription')
            **kwargs: Parámetros para la clave
        """
        key_parts = [prefix]

        for key, value in sorted(kwargs.items()):
            if value is not None:
                key_parts.append(f"{key}:{value}")

        return ":".join(key_parts)

    def cache_cursor_result(self, filters: Dict[str, Any], cursor: Optional[str], result: Any) -> str:
        """Cache específico para resultados de cursor pagination"""
        cache_key = self.build_cache_key(
            'cursor_videos',
            cursor=cursor,
            **{k: v for k, v in filters.items() if v is not None}
        )

        # TTL más corto para resultados de cursor (más dinámicos)
        cursor_ttl = 120.0  # 2 minutos

        self.set(cache_key, result, cursor_ttl)
        return cache_key

    def get_cursor_result(self, filters: Dict[str, Any], cursor: Optional[str]) -> Optional[Any]:
        """Obtener resultado cacheado de cursor pagination"""
        cache_key = self.build_cache_key(
            'cursor_videos',
            cursor=cursor,
            **{k: v for k, v in filters.items() if v is not None}
        )

        return self.get(cache_key)