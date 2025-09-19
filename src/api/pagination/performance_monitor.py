"""
Tag-Flow V2 - Performance Monitor
Monitor de performance en tiempo real para cursor pagination
"""

import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import deque
from threading import Lock

logger = logging.getLogger(__name__)

@dataclass
class QueryMetric:
    """Métrica de una query individual"""
    timestamp: float
    query_type: str
    execution_time_ms: float
    items_returned: int
    cache_hit: bool
    filters_count: int
    cursor_used: bool
    error: Optional[str] = None

@dataclass
class PerformanceSnapshot:
    """Snapshot de performance en un momento dado"""
    timestamp: float
    avg_query_time_ms: float
    queries_per_second: float
    cache_hit_rate: float
    total_queries: int
    error_rate: float
    p95_query_time_ms: float
    slowest_query_ms: float

class PerformanceMonitor:
    """
    Monitor de performance en tiempo real
    Rastrea métricas de cursor pagination para optimización
    """

    def __init__(self, history_size: int = 1000):
        self.metrics: deque = deque(maxlen=history_size)
        self.lock = Lock()
        self.start_time = time.time()

    def record_query(
        self,
        query_type: str,
        execution_time_ms: float,
        items_returned: int,
        cache_hit: bool = False,
        filters_count: int = 0,
        cursor_used: bool = False,
        error: str = None
    ):
        """Registrar métrica de una query"""
        metric = QueryMetric(
            timestamp=time.time(),
            query_type=query_type,
            execution_time_ms=execution_time_ms,
            items_returned=items_returned,
            cache_hit=cache_hit,
            filters_count=filters_count,
            cursor_used=cursor_used,
            error=error
        )

        with self.lock:
            self.metrics.append(metric)

        # Log queries lentas
        if execution_time_ms > 1000:  # > 1 segundo
            logger.warning(
                f"Slow query detected: {query_type} took {execution_time_ms:.2f}ms, "
                f"returned {items_returned} items"
            )

    def get_current_stats(self, window_seconds: int = 60) -> PerformanceSnapshot:
        """Obtener estadísticas actuales en una ventana de tiempo"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - window_seconds

            # Filtrar métricas en la ventana de tiempo
            recent_metrics = [
                m for m in self.metrics
                if m.timestamp >= cutoff_time
            ]

            if not recent_metrics:
                return PerformanceSnapshot(
                    timestamp=current_time,
                    avg_query_time_ms=0,
                    queries_per_second=0,
                    cache_hit_rate=0,
                    total_queries=0,
                    error_rate=0,
                    p95_query_time_ms=0,
                    slowest_query_ms=0
                )

            # Calcular métricas
            execution_times = [m.execution_time_ms for m in recent_metrics]
            avg_query_time = sum(execution_times) / len(execution_times)

            queries_per_second = len(recent_metrics) / window_seconds

            cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
            cache_hit_rate = (cache_hits / len(recent_metrics)) * 100

            errors = sum(1 for m in recent_metrics if m.error is not None)
            error_rate = (errors / len(recent_metrics)) * 100

            # Percentil 95
            execution_times_sorted = sorted(execution_times)
            p95_index = int(0.95 * len(execution_times_sorted))
            p95_query_time = execution_times_sorted[p95_index] if execution_times_sorted else 0

            slowest_query = max(execution_times) if execution_times else 0

            return PerformanceSnapshot(
                timestamp=current_time,
                avg_query_time_ms=round(avg_query_time, 2),
                queries_per_second=round(queries_per_second, 2),
                cache_hit_rate=round(cache_hit_rate, 2),
                total_queries=len(recent_metrics),
                error_rate=round(error_rate, 2),
                p95_query_time_ms=round(p95_query_time, 2),
                slowest_query_ms=round(slowest_query, 2)
            )

    def get_performance_grade(self) -> Dict[str, Any]:
        """Obtener calificación de performance basada en métricas"""
        stats = self.get_current_stats()

        # Criterios de calificación
        grade_criteria = {
            'avg_query_time': {
                'excellent': 50,   # < 50ms
                'good': 200,       # < 200ms
                'fair': 500,       # < 500ms
                'poor': float('inf')
            },
            'cache_hit_rate': {
                'excellent': 80,   # > 80%
                'good': 60,        # > 60%
                'fair': 40,        # > 40%
                'poor': 0
            },
            'error_rate': {
                'excellent': 1,    # < 1%
                'good': 5,         # < 5%
                'fair': 10,        # < 10%
                'poor': float('inf')
            }
        }

        def get_grade(value, criteria, higher_is_better=False):
            if higher_is_better:
                if value >= criteria['excellent']:
                    return 'excellent'
                elif value >= criteria['good']:
                    return 'good'
                elif value >= criteria['fair']:
                    return 'fair'
                else:
                    return 'poor'
            else:
                if value <= criteria['excellent']:
                    return 'excellent'
                elif value <= criteria['good']:
                    return 'good'
                elif value <= criteria['fair']:
                    return 'fair'
                else:
                    return 'poor'

        grades = {
            'avg_query_time': get_grade(stats.avg_query_time_ms, grade_criteria['avg_query_time']),
            'cache_hit_rate': get_grade(stats.cache_hit_rate, grade_criteria['cache_hit_rate'], True),
            'error_rate': get_grade(stats.error_rate, grade_criteria['error_rate'])
        }

        # Calificación general
        grade_values = {'excellent': 4, 'good': 3, 'fair': 2, 'poor': 1}
        avg_grade_value = sum(grade_values[grade] for grade in grades.values()) / len(grades)

        if avg_grade_value >= 3.5:
            overall_grade = 'excellent'
        elif avg_grade_value >= 2.5:
            overall_grade = 'good'
        elif avg_grade_value >= 1.5:
            overall_grade = 'fair'
        else:
            overall_grade = 'poor'

        return {
            'overall_grade': overall_grade,
            'grades': grades,
            'stats': asdict(stats),
            'recommendations': self._get_recommendations(grades, stats)
        }

    def _get_recommendations(self, grades: Dict[str, str], stats: PerformanceSnapshot) -> List[str]:
        """Generar recomendaciones basadas en las métricas"""
        recommendations = []

        if grades['avg_query_time'] in ['fair', 'poor']:
            recommendations.append(
                f"Query time is {stats.avg_query_time_ms:.1f}ms. Consider adding database indices "
                "or optimizing query filters."
            )

        if grades['cache_hit_rate'] in ['fair', 'poor']:
            recommendations.append(
                f"Cache hit rate is {stats.cache_hit_rate:.1f}%. Consider increasing cache TTL "
                "or optimizing cache keys."
            )

        if grades['error_rate'] in ['fair', 'poor']:
            recommendations.append(
                f"Error rate is {stats.error_rate:.1f}%. Check logs for query errors and "
                "data validation issues."
            )

        if stats.p95_query_time_ms > 1000:
            recommendations.append(
                f"95th percentile query time is {stats.p95_query_time_ms:.1f}ms. "
                "Some queries are significantly slower than average."
            )

        if not recommendations:
            recommendations.append("Performance is optimal. No immediate optimizations needed.")

        return recommendations

    def get_query_type_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Obtener breakdown de performance por tipo de query"""
        with self.lock:
            query_types = {}

            for metric in self.metrics:
                query_type = metric.query_type
                if query_type not in query_types:
                    query_types[query_type] = {
                        'count': 0,
                        'total_time': 0,
                        'errors': 0,
                        'cache_hits': 0
                    }

                stats = query_types[query_type]
                stats['count'] += 1
                stats['total_time'] += metric.execution_time_ms
                if metric.error:
                    stats['errors'] += 1
                if metric.cache_hit:
                    stats['cache_hits'] += 1

            # Calcular promedios
            for query_type, stats in query_types.items():
                stats['avg_time_ms'] = round(stats['total_time'] / stats['count'], 2)
                stats['error_rate'] = round((stats['errors'] / stats['count']) * 100, 2)
                stats['cache_hit_rate'] = round((stats['cache_hits'] / stats['count']) * 100, 2)

            return query_types

    def export_metrics(self, filename: str = None) -> str:
        """Exportar métricas a archivo JSON para análisis"""
        import json
        import os

        with self.lock:
            export_data = {
                'export_timestamp': time.time(),
                'monitoring_duration_seconds': time.time() - self.start_time,
                'total_metrics': len(self.metrics),
                'current_stats': asdict(self.get_current_stats()),
                'performance_grade': self.get_performance_grade(),
                'query_breakdown': self.get_query_type_breakdown(),
                'raw_metrics': [asdict(metric) for metric in self.metrics]
            }

            if not filename:
                timestamp = int(time.time())
                filename = f"cursor_pagination_metrics_{timestamp}.json"

            filepath = os.path.join("backups", filename)
            os.makedirs("backups", exist_ok=True)

            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Performance metrics exported to: {filepath}")
            return filepath