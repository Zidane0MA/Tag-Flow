"""
Tag-Flow V2 - Cache LRU Inteligente para Optimizaciones de BD
Sistema de cache para mejorar rendimiento de consultas frecuentes en main.py
"""

import time
from typing import Set, List, Dict, Optional, Any, Callable
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class PatternCache:
    """Cache LRU para patrones de personajes con gestión automática"""
    
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.cache = {}
        self.access_order = []
        self.hits = 0
        self.misses = 0
        
    def get_or_compute(self, key: str, compute_func: Callable, *args, **kwargs):
        """Obtener valor del cache o computarlo"""
        if key in self.cache:
            self.hits += 1
            # Mover al final (más reciente)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        
        # Cache miss - computar valor
        self.misses += 1
        value = compute_func(*args, **kwargs)
        
        # Agregar al cache
        self.cache[key] = value
        self.access_order.append(key)
        
        # Limpiar si excede tamaño máximo
        if len(self.cache) > self.max_size:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
            
        return value
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del cache"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / max(1, total_requests)) * 100
        
        return {
            'max_size': self.max_size,
            'current_size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total_requests,
            'hit_rate': round(hit_rate, 1),
            'efficiency_score': round(hit_rate, 1)
        }
    
    def clear(self):
        """Limpiar cache"""
        self.cache.clear()
        self.access_order.clear()
        self.hits = 0
        self.misses = 0

class DatabaseCache:
    """Cache LRU para consultas frecuentes de main.py con gestión automática"""
    
    def __init__(self, max_size=1000, ttl_seconds=300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        
        # Cache de paths existentes
        self.path_cache = None
        self.path_cache_time = 0
        
        # Cache de videos pendientes por filtro
        self.pending_cache = {}
        
        # Cache de estadísticas
        self.stats_cache = None
        self.stats_cache_time = 0
        
        # Métricas de rendimiento
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_queries = 0
        
        logger.debug("DatabaseCache inicializado con configuración enterprise")
        
    def get_existing_paths(self, db_manager) -> Set[str]:
        """✅ Cache de paths existentes con TTL automático"""
        current_time = time.time()
        
        # Verificar si cache es válido
        if (self.path_cache is None or 
            current_time - self.path_cache_time > self.ttl_seconds):
            
            # Cache miss - actualizar
            self.path_cache = db_manager.get_existing_paths_only()
            self.path_cache_time = current_time
            self.cache_misses += 1
            
            logger.debug(f"🔄 Cache MISS - paths actualizados: {len(self.path_cache)} paths")
        else:
            # Cache hit
            self.cache_hits += 1
            logger.debug(f"💾 Cache HIT - paths: {len(self.path_cache)} paths")
        
        self.total_queries += 1
        return self.path_cache
        
    def get_pending_videos_cached(self, cache_key: str, db_manager, platform_filter: str, source_filter: str, limit: int) -> List[Dict]:
        """✅ Cache de videos pendientes con gestión inteligente"""
        current_time = time.time()
        
        # Verificar cache
        if cache_key in self.pending_cache:
            cached_data, cache_time = self.pending_cache[cache_key]
            if current_time - cache_time < self.ttl_seconds:
                self.cache_hits += 1
                self.total_queries += 1
                logger.debug(f"💾 Cache HIT para pendientes: {cache_key}")
                return cached_data
        
        # Cache miss - actualizar
        pending_videos = db_manager.get_pending_videos_filtered(platform_filter, source_filter, limit)
        self.pending_cache[cache_key] = (pending_videos, current_time)
        
        # Limpiar cache si es muy grande
        if len(self.pending_cache) > self.max_size:
            oldest_key = min(self.pending_cache.keys(), 
                           key=lambda k: self.pending_cache[k][1])
            del self.pending_cache[oldest_key]
            logger.debug(f"🗑️ Cache pendientes limpiado (tamaño máximo alcanzado)")
        
        self.cache_misses += 1
        self.total_queries += 1
        logger.debug(f"🔄 Cache MISS para pendientes: {cache_key}, {len(pending_videos)} videos")
        return pending_videos
        
    def invalidate_paths(self):
        """✅ Invalidar cache de paths cuando se modifica BD"""
        self.path_cache = None
        self.path_cache_time = 0
        logger.debug("🗑️ Cache de paths invalidado")
        
    def invalidate_pending(self):
        """✅ Invalidar cache de pendientes cuando cambia estado"""
        self.pending_cache.clear()
        logger.debug("🗑️ Cache de pendientes invalidado")
        
    def invalidate_all(self):
        """✅ Invalidar todo el cache"""
        self.invalidate_paths()
        self.invalidate_pending()
        self.stats_cache = None
        self.stats_cache_time = 0
        logger.debug("🗑️ Cache completo invalidado")
        
    def get_cache_stats(self) -> Dict:
        """✅ Estadísticas de rendimiento del cache"""
        hit_rate = (self.cache_hits / max(1, self.total_queries)) * 100
        
        return {
            'total_queries': self.total_queries,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate_percentage': round(hit_rate, 1),
            'paths_cached': self.path_cache is not None,
            'pending_cache_size': len(self.pending_cache),
            'paths_cache_age_seconds': time.time() - self.path_cache_time if self.path_cache else 0,
            'cache_efficiency': 'EXCELLENT' if hit_rate > 90 else 'GOOD' if hit_rate > 70 else 'NEEDS_IMPROVEMENT'
        }
    
    def get_memory_usage(self) -> Dict:
        """✅ Estimación de uso de memoria del cache"""
        import sys
        
        paths_memory = sys.getsizeof(self.path_cache) if self.path_cache else 0
        pending_memory = sum(sys.getsizeof(data[0]) for data in self.pending_cache.values())
        
        return {
            'paths_cache_mb': round(paths_memory / (1024*1024), 2),
            'pending_cache_mb': round(pending_memory / (1024*1024), 2),
            'total_cache_mb': round((paths_memory + pending_memory) / (1024*1024), 2)
        }
    
    def clear_detection_cache(self):
        """✅ Limpiar cache para forzar actualización"""
        self.invalidate_all()
        
        # Reset métricas
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_queries = 0
        
        logger.info("🔄 Cache de detección limpiado completamente")


# Instancia global del cache para usar en toda la aplicación
_global_cache = None
_global_pattern_cache = None

def get_global_cache() -> PatternCache:
    """Obtener instancia global del cache de patrones"""
    global _global_pattern_cache
    if _global_pattern_cache is None:
        _global_pattern_cache = PatternCache()
    return _global_pattern_cache

def get_global_database_cache() -> DatabaseCache:
    """Obtener instancia global del cache de base de datos"""
    global _global_cache
    if _global_cache is None:
        _global_cache = DatabaseCache()
    return _global_cache

def clear_global_cache():
    """Limpiar cache global"""
    global _global_cache, _global_pattern_cache
    if _global_cache:
        _global_cache.clear_detection_cache()
    if _global_pattern_cache:
        _global_pattern_cache.clear()
