"""
Tag-Flow V2 - Pattern Cache
Cache inteligente LRU para resultados de detección con métricas avanzadas
"""

import hashlib
import time
from typing import Any, Callable, Dict, Optional, List, Tuple
from collections import OrderedDict

class PatternCache:
    """Cache LRU optimizado para resultados de detección"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = OrderedDict()
        self.max_size = max_size
        
        # Estadísticas de rendimiento
        self.hit_count = 0
        self.miss_count = 0
        self.total_computation_time = 0.0
        self.total_cache_time = 0.0
        
        # Métricas de eficiencia
        self.cache_sizes_history = []
        self.hit_rates_history = []
    
    def get_or_compute(self, key: str, compute_func: Callable, *args, **kwargs) -> Any:
        """Obtener del cache o computar y cachear"""
        cache_key = self._generate_cache_key(key, args, kwargs)
        
        # Verificar cache
        start_time = time.time()
        if cache_key in self.cache:
            # Cache hit - mover al final (más reciente)
            result = self.cache.pop(cache_key)
            self.cache[cache_key] = result
            
            self.hit_count += 1
            self.total_cache_time += time.time() - start_time
            
            return result
        
        # Cache miss - computar resultado
        self.miss_count += 1
        
        compute_start = time.time()
        result = compute_func(*args, **kwargs)
        computation_time = time.time() - compute_start
        
        self.total_computation_time += computation_time
        
        # Almacenar en cache
        self._store_in_cache(cache_key, result)
        
        return result
    
    def _generate_cache_key(self, key: str, args: Tuple, kwargs: Dict) -> str:
        """Generar clave única para cache"""
        # Combinar key, args y kwargs en un hash único
        combined = f"{key}_{str(args)}_{str(sorted(kwargs.items()))}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _store_in_cache(self, cache_key: str, result: Any):
        """Almacenar resultado en cache con gestión LRU"""
        # Si cache está lleno, remover el más antiguo (LRU)
        if len(self.cache) >= self.max_size:
            # Remover 10% de entradas más antiguas para evitar thrashing
            remove_count = max(1, self.max_size // 10)
            for _ in range(remove_count):
                if self.cache:
                    self.cache.popitem(last=False)  # Remover el más antiguo
        
        self.cache[cache_key] = result
    
    def invalidate(self, pattern: str = None):
        """Invalidar cache completo o por patrón"""
        if pattern is None:
            self.cache.clear()
        else:
            # Remover entradas que coincidan con el patrón
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.cache[key]
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas completas del cache"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        # Calcular tiempo promedio ahorrado por cache hit
        avg_computation_time = (
            self.total_computation_time / self.miss_count 
            if self.miss_count > 0 else 0
        )
        avg_cache_time = (
            self.total_cache_time / self.hit_count 
            if self.hit_count > 0 else 0
        )
        
        time_saved = self.hit_count * (avg_computation_time - avg_cache_time)
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "utilization": len(self.cache) / self.max_size * 100,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),
            "avg_computation_time_ms": round(avg_computation_time * 1000, 2),
            "avg_cache_time_ms": round(avg_cache_time * 1000, 2),
            "total_time_saved_ms": round(time_saved * 1000, 2),
            "efficiency_score": self._calculate_efficiency_score()
        }
    
    def _calculate_efficiency_score(self) -> float:
        """Calcular score de eficiencia del cache (0-100)"""
        if self.hit_count + self.miss_count == 0:
            return 0.0
        
        hit_rate = self.hit_count / (self.hit_count + self.miss_count)
        utilization = len(self.cache) / self.max_size
        
        # Score basado en hit rate (70%) y utilización óptima (30%)
        # Utilización óptima está entre 70-90%
        optimal_utilization = 1.0 if 0.7 <= utilization <= 0.9 else (
            0.8 if utilization < 0.7 else max(0.2, 1.0 - (utilization - 0.9) * 2)
        )
        
        return round((hit_rate * 0.7 + optimal_utilization * 0.3) * 100, 1)
    
    def optimize_size(self, target_hit_rate: float = 0.85):
        """Optimizar tamaño del cache para alcanzar hit rate objetivo"""
        current_hit_rate = self.hit_count / (self.hit_count + self.miss_count) if (self.hit_count + self.miss_count) > 0 else 0
        
        if current_hit_rate < target_hit_rate:
            # Aumentar tamaño del cache
            new_size = min(self.max_size * 1.5, 2000)  # Máximo 2000 entradas
            self.max_size = int(new_size)
        elif current_hit_rate > target_hit_rate + 0.1 and len(self.cache) < self.max_size * 0.5:
            # Reducir tamaño si está muy subutilizado
            new_size = max(self.max_size * 0.8, 100)  # Mínimo 100 entradas
            self.max_size = int(new_size)
            
            # Recortar cache si es necesario
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
    
    def get_memory_usage(self) -> Dict:
        """Estimar uso de memoria del cache"""
        import sys
        
        total_size = 0
        for key, value in self.cache.items():
            total_size += sys.getsizeof(key) + sys.getsizeof(value)
        
        return {
            "total_bytes": total_size,
            "total_kb": round(total_size / 1024, 2),
            "total_mb": round(total_size / (1024 * 1024), 2),
            "avg_entry_bytes": round(total_size / len(self.cache), 2) if self.cache else 0,
            "entries": len(self.cache)
        }
    
    def export_analytics(self) -> Dict:
        """Exportar analytics completos para análisis"""
        stats = self.get_stats()
        memory = self.get_memory_usage()
        
        return {
            "timestamp": time.time(),
            "performance": stats,
            "memory": memory,
            "configuration": {
                "max_size": self.max_size,
                "current_size": len(self.cache)
            },
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generar recomendaciones para optimización"""
        recommendations = []
        stats = self.get_stats()
        
        if stats["hit_rate"] < 50:
            recommendations.append("Hit rate bajo - considera aumentar tamaño del cache")
        
        if stats["utilization"] > 95:
            recommendations.append("Cache casi lleno - considera aumentar max_size")
        
        if stats["utilization"] < 30 and len(self.cache) > 100:
            recommendations.append("Cache subutilizado - considera reducir max_size")
        
        if stats["efficiency_score"] < 60:
            recommendations.append("Eficiencia baja - revisa patrones de acceso")
        
        if not recommendations:
            recommendations.append("Cache funcionando óptimamente")
        
        return recommendations

# Cache global para uso en el sistema
_global_pattern_cache = None

def get_global_cache(max_size: int = 1000) -> PatternCache:
    """Obtener instancia global del cache"""
    global _global_pattern_cache
    if _global_pattern_cache is None:
        _global_pattern_cache = PatternCache(max_size)
    return _global_pattern_cache

def clear_global_cache():
    """Limpiar cache global"""
    global _global_pattern_cache
    if _global_pattern_cache:
        _global_pattern_cache.invalidate()
