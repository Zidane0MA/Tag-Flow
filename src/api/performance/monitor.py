"""
Tag-Flow V2 - Database Performance Monitoring System
Sistema de monitoreo de performance y salud de la base de datos
"""

import sqlite3
import time
import threading
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class QueryPerformanceMetric:
    """Métrica de rendimiento de consulta"""
    query_type: str
    execution_time_ms: float
    rows_affected: int
    timestamp: datetime
    query_hash: str
    success: bool
    error_message: Optional[str] = None

@dataclass
class DatabaseHealthMetrics:
    """Métricas de salud de la base de datos"""
    timestamp: datetime
    db_size_mb: float
    page_count: int
    page_size: int
    fragmentation_percent: float
    cache_hit_ratio: float
    active_connections: int
    total_queries: int
    slow_queries: int
    failed_queries: int
    avg_query_time_ms: float

@dataclass
class TableStatistics:
    """Estadísticas de tabla"""
    table_name: str
    row_count: int
    size_mb: float
    index_count: int
    last_analyzed: datetime

class DatabaseMonitor:
    """
    Monitor de performance de base de datos con métricas en tiempo real
    """

    def __init__(self, db_path: str, slow_query_threshold_ms: float = 100):
        self.db_path = db_path
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self._metrics_history: List[QueryPerformanceMetric] = []
        self._health_history: List[DatabaseHealthMetrics] = []
        self._lock = threading.RLock()
        self._monitoring_enabled = True

        # Contadores de métricas
        self._total_queries = 0
        self._slow_queries = 0
        self._failed_queries = 0
        self._total_execution_time = 0.0

    def log_query_performance(self, query_type: str, execution_time_ms: float,
                            rows_affected: int, query: str, success: bool = True,
                            error_message: Optional[str] = None) -> None:
        """Registrar performance de una consulta"""
        if not self._monitoring_enabled:
            return

        with self._lock:
            # Generar hash simple de la consulta para agrupación
            query_hash = str(hash(query.strip()[:100]))  # Solo primeros 100 caracteres

            metric = QueryPerformanceMetric(
                query_type=query_type,
                execution_time_ms=execution_time_ms,
                rows_affected=rows_affected,
                timestamp=datetime.now(),
                query_hash=query_hash,
                success=success,
                error_message=error_message
            )

            self._metrics_history.append(metric)
            self._update_counters(metric)

            # Mantener solo las últimas 1000 métricas
            if len(self._metrics_history) > 1000:
                self._metrics_history = self._metrics_history[-1000:]

            # Log consultas lentas
            if execution_time_ms > self.slow_query_threshold_ms:
                logger.warning(
                    f"Slow query detected: {query_type} took {execution_time_ms:.2f}ms "
                    f"(threshold: {self.slow_query_threshold_ms}ms)"
                )

    def _update_counters(self, metric: QueryPerformanceMetric) -> None:
        """Actualizar contadores internos"""
        self._total_queries += 1

        if metric.success:
            self._total_execution_time += metric.execution_time_ms
            if metric.execution_time_ms > self.slow_query_threshold_ms:
                self._slow_queries += 1
        else:
            self._failed_queries += 1

    def get_current_health_metrics(self) -> DatabaseHealthMetrics:
        """Obtener métricas actuales de salud de la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Tamaño de la base de datos
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            db_size_mb = (page_count * page_size) / (1024 * 1024)

            # Fragmentación (páginas libres)
            cursor.execute("PRAGMA freelist_count")
            free_pages = cursor.fetchone()[0]
            fragmentation_percent = (free_pages / page_count * 100) if page_count > 0 else 0

            # Cache hit ratio
            cursor.execute("PRAGMA cache_size")
            cache_size = cursor.fetchone()[0]

            # Aproximación del cache hit ratio basado en métricas internas
            cache_hit_ratio = max(0, min(100, 95 - (self._slow_queries / max(self._total_queries, 1) * 100)))

            # Estadísticas de consultas
            avg_query_time = self._total_execution_time / max(self._total_queries, 1)

            conn.close()

            return DatabaseHealthMetrics(
                timestamp=datetime.now(),
                db_size_mb=db_size_mb,
                page_count=page_count,
                page_size=page_size,
                fragmentation_percent=fragmentation_percent,
                cache_hit_ratio=cache_hit_ratio,
                active_connections=1,  # SQLite es single-connection
                total_queries=self._total_queries,
                slow_queries=self._slow_queries,
                failed_queries=self._failed_queries,
                avg_query_time_ms=avg_query_time
            )

        except Exception as e:
            logger.error(f"Error obteniendo métricas de salud: {e}")
            return DatabaseHealthMetrics(
                timestamp=datetime.now(),
                db_size_mb=0, page_count=0, page_size=0,
                fragmentation_percent=0, cache_hit_ratio=0,
                active_connections=0, total_queries=self._total_queries,
                slow_queries=self._slow_queries, failed_queries=self._failed_queries,
                avg_query_time_ms=0
            )

    def get_table_statistics(self) -> List[TableStatistics]:
        """Obtener estadísticas de tablas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Obtener todas las tablas
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]

            statistics = []
            for table in tables:
                try:
                    # Contar filas
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]

                    # Contar índices
                    cursor.execute("""
                        SELECT COUNT(*) FROM sqlite_master
                        WHERE type='index' AND tbl_name=? AND name NOT LIKE 'sqlite_%'
                    """, (table,))
                    index_count = cursor.fetchone()[0]

                    # Aproximar tamaño (no exacto en SQLite)
                    size_mb = (row_count * 100) / (1024 * 1024)  # Aproximación muy básica

                    statistics.append(TableStatistics(
                        table_name=table,
                        row_count=row_count,
                        size_mb=size_mb,
                        index_count=index_count,
                        last_analyzed=datetime.now()
                    ))

                except Exception as e:
                    logger.warning(f"Error obteniendo estadísticas para tabla {table}: {e}")

            conn.close()
            return statistics

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de tablas: {e}")
            return []

    def get_slow_queries_report(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Obtener reporte de consultas lentas"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._lock:
            slow_queries = [
                metric for metric in self._metrics_history
                if (metric.execution_time_ms > self.slow_query_threshold_ms and
                    metric.timestamp > cutoff_time)
            ]

        # Agrupar por tipo de consulta y calcular estadísticas
        grouped_queries = {}
        for metric in slow_queries:
            key = f"{metric.query_type}_{metric.query_hash}"
            if key not in grouped_queries:
                grouped_queries[key] = {
                    'query_type': metric.query_type,
                    'count': 0,
                    'total_time': 0,
                    'max_time': 0,
                    'min_time': float('inf'),
                    'avg_time': 0,
                    'last_execution': None
                }

            stats = grouped_queries[key]
            stats['count'] += 1
            stats['total_time'] += metric.execution_time_ms
            stats['max_time'] = max(stats['max_time'], metric.execution_time_ms)
            stats['min_time'] = min(stats['min_time'], metric.execution_time_ms)
            stats['last_execution'] = metric.timestamp

        # Calcular promedios y ordenar por impacto
        report = []
        for key, stats in grouped_queries.items():
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['impact_score'] = stats['count'] * stats['avg_time']  # Impacto = frecuencia * tiempo
            report.append(stats)

        return sorted(report, key=lambda x: x['impact_score'], reverse=True)

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Obtener resumen de performance"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._lock:
            recent_metrics = [
                metric for metric in self._metrics_history
                if metric.timestamp > cutoff_time
            ]

        if not recent_metrics:
            return {
                'period_hours': hours,
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'slow_queries': 0,
                'success_rate_percent': 0,
                'slow_query_rate_percent': 0,
                'avg_execution_time_ms': 0,
                'p95_execution_time_ms': 0,
                'query_types': {}
            }

        successful_queries = [m for m in recent_metrics if m.success]
        failed_queries = [m for m in recent_metrics if not m.success]
        slow_queries = [m for m in successful_queries if m.execution_time_ms > self.slow_query_threshold_ms]

        # Calcular percentiles
        execution_times = [m.execution_time_ms for m in successful_queries]
        execution_times.sort()

        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
        p95_time = execution_times[int(len(execution_times) * 0.95)] if execution_times else 0

        # Agrupar por tipo de consulta
        query_types = {}
        for metric in recent_metrics:
            qtype = metric.query_type
            if qtype not in query_types:
                query_types[qtype] = {'count': 0, 'avg_time': 0, 'total_time': 0}

            query_types[qtype]['count'] += 1
            if metric.success:
                query_types[qtype]['total_time'] += metric.execution_time_ms

        # Calcular promedios por tipo
        for qtype, stats in query_types.items():
            stats['avg_time'] = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0

        return {
            'period_hours': hours,
            'total_queries': len(recent_metrics),
            'successful_queries': len(successful_queries),
            'failed_queries': len(failed_queries),
            'slow_queries': len(slow_queries),
            'success_rate_percent': (len(successful_queries) / len(recent_metrics) * 100) if recent_metrics else 0,
            'slow_query_rate_percent': (len(slow_queries) / len(successful_queries) * 100) if successful_queries else 0,
            'avg_execution_time_ms': avg_time,
            'p95_execution_time_ms': p95_time,
            'query_types': query_types
        }

    def optimize_database(self) -> Dict[str, Any]:
        """Optimizar la base de datos y reportar mejoras"""
        start_time = time.time()

        try:
            # Métricas antes de la optimización
            before_metrics = self.get_current_health_metrics()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Ejecutar optimizaciones
            optimizations_performed = []

            # VACUUM para reducir fragmentación
            if before_metrics.fragmentation_percent > 10:
                logger.info("Ejecutando VACUUM para reducir fragmentación...")
                cursor.execute("VACUUM")
                optimizations_performed.append("VACUUM")

            # ANALYZE para actualizar estadísticas de índices
            logger.info("Ejecutando ANALYZE para actualizar estadísticas...")
            cursor.execute("ANALYZE")
            optimizations_performed.append("ANALYZE")

            # PRAGMA optimize
            cursor.execute("PRAGMA optimize")
            optimizations_performed.append("PRAGMA optimize")

            conn.close()

            # Métricas después de la optimización
            time.sleep(0.5)  # Pequeña pausa para que se apliquen cambios
            after_metrics = self.get_current_health_metrics()

            optimization_time = (time.time() - start_time) * 1000  # en ms

            return {
                'success': True,
                'optimization_time_ms': optimization_time,
                'optimizations_performed': optimizations_performed,
                'before': asdict(before_metrics),
                'after': asdict(after_metrics),
                'improvements': {
                    'size_reduction_mb': before_metrics.db_size_mb - after_metrics.db_size_mb,
                    'fragmentation_reduction_percent': before_metrics.fragmentation_percent - after_metrics.fragmentation_percent,
                    'cache_hit_improvement': after_metrics.cache_hit_ratio - before_metrics.cache_hit_ratio
                }
            }

        except Exception as e:
            logger.error(f"Error durante optimización de BD: {e}")
            return {
                'success': False,
                'error': str(e),
                'optimization_time_ms': (time.time() - start_time) * 1000
            }

    def reset_metrics(self) -> None:
        """Resetear métricas acumuladas"""
        with self._lock:
            self._metrics_history.clear()
            self._health_history.clear()
            self._total_queries = 0
            self._slow_queries = 0
            self._failed_queries = 0
            self._total_execution_time = 0.0

        logger.info("Métricas de monitoreo reseteadas")

    def enable_monitoring(self) -> None:
        """Habilitar monitoreo"""
        self._monitoring_enabled = True
        logger.info("Monitoreo de base de datos habilitado")

    def disable_monitoring(self) -> None:
        """Deshabilitar monitoreo"""
        self._monitoring_enabled = False
        logger.info("Monitoreo de base de datos deshabilitado")

# Instancia global del monitor
def get_database_monitor(db_path: str = None) -> Optional[DatabaseMonitor]:
    """Obtener instancia del monitor de base de datos"""
    if db_path:
        monitor = DatabaseMonitor(db_path)
        logger.info(f"Monitor de base de datos inicializado para: {db_path}")
        return monitor
    return None

