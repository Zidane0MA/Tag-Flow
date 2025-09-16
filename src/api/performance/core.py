"""
Tag-Flow V2 - Performance Monitoring API
API endpoints para métricas de performance y monitoreo del sistema
"""

import logging
from flask import Blueprint, request, jsonify
from .monitor import get_database_monitor
from .cache import get_cache_metrics
from pathlib import Path

logger = logging.getLogger(__name__)

performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')

@performance_bp.route('/database/health')
def get_database_health():
    """Obtener métricas de salud de la base de datos"""
    try:
        # Inicializar monitor si es necesario
        db_path = Path(__file__).parent.parent.parent / 'data' / 'videos.db'
        monitor = get_database_monitor(str(db_path))

        if not monitor:
            return jsonify({
                'success': False,
                'error': 'Database monitor not available'
            }), 500

        health_metrics = monitor.get_current_health_metrics()

        return jsonify({
            'success': True,
            'health_metrics': {
                'timestamp': health_metrics.timestamp.isoformat(),
                'database_size': {
                    'size_mb': round(health_metrics.db_size_mb, 2),
                    'page_count': health_metrics.page_count,
                    'page_size': health_metrics.page_size,
                    'fragmentation_percent': round(health_metrics.fragmentation_percent, 2)
                },
                'performance': {
                    'cache_hit_ratio': round(health_metrics.cache_hit_ratio, 2),
                    'avg_query_time_ms': round(health_metrics.avg_query_time_ms, 2),
                    'active_connections': health_metrics.active_connections
                },
                'query_stats': {
                    'total_queries': health_metrics.total_queries,
                    'slow_queries': health_metrics.slow_queries,
                    'failed_queries': health_metrics.failed_queries,
                    'success_rate_percent': round(
                        ((health_metrics.total_queries - health_metrics.failed_queries) /
                         max(health_metrics.total_queries, 1)) * 100, 2
                    )
                }
            }
        })

    except Exception as e:
        logger.error(f"Error obteniendo métricas de salud de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@performance_bp.route('/database/tables')
def get_table_statistics():
    """Obtener estadísticas de tablas"""
    try:
        db_path = Path(__file__).parent.parent.parent / 'data' / 'videos.db'
        monitor = get_database_monitor(str(db_path))

        if not monitor:
            return jsonify({
                'success': False,
                'error': 'Database monitor not available'
            }), 500

        table_stats = monitor.get_table_statistics()

        return jsonify({
            'success': True,
            'table_statistics': [
                {
                    'table_name': stat.table_name,
                    'row_count': stat.row_count,
                    'size_mb': round(stat.size_mb, 2),
                    'index_count': stat.index_count,
                    'last_analyzed': stat.last_analyzed.isoformat()
                }
                for stat in table_stats
            ],
            'total_tables': len(table_stats),
            'total_rows': sum(stat.row_count for stat in table_stats)
        })

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de tablas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@performance_bp.route('/database/slow-queries')
def get_slow_queries():
    """Obtener reporte de consultas lentas"""
    try:
        hours = int(request.args.get('hours', 1))

        db_path = Path(__file__).parent.parent.parent / 'data' / 'videos.db'
        monitor = get_database_monitor(str(db_path))

        if not monitor:
            return jsonify({
                'success': False,
                'error': 'Database monitor not available'
            }), 500

        slow_queries = monitor.get_slow_queries_report(hours)

        return jsonify({
            'success': True,
            'report_period_hours': hours,
            'slow_queries': slow_queries,
            'total_slow_queries': len(slow_queries)
        })

    except Exception as e:
        logger.error(f"Error obteniendo consultas lentas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@performance_bp.route('/database/summary')
def get_performance_summary():
    """Obtener resumen de performance"""
    try:
        hours = int(request.args.get('hours', 24))

        db_path = Path(__file__).parent.parent.parent / 'data' / 'videos.db'
        monitor = get_database_monitor(str(db_path))

        if not monitor:
            return jsonify({
                'success': False,
                'error': 'Database monitor not available'
            }), 500

        summary = monitor.get_performance_summary(hours)

        return jsonify({
            'success': True,
            'performance_summary': summary
        })

    except Exception as e:
        logger.error(f"Error obteniendo resumen de performance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@performance_bp.route('/database/optimize', methods=['POST'])
def optimize_database():
    """Optimizar la base de datos"""
    try:
        db_path = Path(__file__).parent.parent.parent / 'data' / 'videos.db'
        monitor = get_database_monitor(str(db_path))

        if not monitor:
            return jsonify({
                'success': False,
                'error': 'Database monitor not available'
            }), 500

        optimization_result = monitor.optimize_database()

        return jsonify({
            'success': optimization_result['success'],
            'optimization_result': optimization_result
        })

    except Exception as e:
        logger.error(f"Error optimizando base de datos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@performance_bp.route('/cache/metrics')
def get_cache_performance():
    """Obtener métricas de performance del cache"""
    try:
        cache_metrics = get_cache_metrics()

        return jsonify({
            'success': True,
            'cache_metrics': cache_metrics
        })

    except Exception as e:
        logger.error(f"Error obteniendo métricas de cache: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@performance_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Limpiar cache del sistema"""
    try:
        from .cache import smart_cache

        # Obtener estadísticas antes del clear
        before_stats = smart_cache.get_stats()

        # Limpiar cache
        smart_cache.clear()

        # Estadísticas después del clear
        after_stats = smart_cache.get_stats()

        return jsonify({
            'success': True,
            'cache_cleared': True,
            'entries_cleared': before_stats['current_entries'],
            'memory_freed_bytes': before_stats['total_size_bytes']
        })

    except Exception as e:
        logger.error(f"Error limpiando cache: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@performance_bp.route('/system/overview')
def get_system_overview():
    """Obtener vista general del sistema de performance"""
    try:
        # Métricas de base de datos
        db_path = Path(__file__).parent.parent.parent / 'data' / 'videos.db'
        monitor = get_database_monitor(str(db_path))

        system_overview = {
            'database': {
                'monitoring_enabled': monitor is not None,
                'health_status': 'unknown'
            },
            'cache': {
                'enabled': True
            },
            'pagination': {
                'smart_pagination_enabled': True,
                'cursor_pagination_available': True
            }
        }

        if monitor:
            health_metrics = monitor.get_current_health_metrics()
            performance_summary = monitor.get_performance_summary(1)  # Última hora

            # Determinar estado de salud
            health_status = 'excellent'
            if health_metrics.fragmentation_percent > 20:
                health_status = 'poor'
            elif health_metrics.fragmentation_percent > 10:
                health_status = 'fair'
            elif health_metrics.avg_query_time_ms > 100:
                health_status = 'good'

            system_overview['database'].update({
                'health_status': health_status,
                'size_mb': round(health_metrics.db_size_mb, 2),
                'fragmentation_percent': round(health_metrics.fragmentation_percent, 2),
                'cache_hit_ratio': round(health_metrics.cache_hit_ratio, 2),
                'queries_last_hour': performance_summary['total_queries'],
                'slow_queries_last_hour': performance_summary['slow_queries'],
                'avg_query_time_ms': round(performance_summary['avg_execution_time_ms'], 2)
            })

        # Métricas de cache
        cache_metrics = get_cache_metrics()
        system_overview['cache'].update({
            'hit_rate_percent': cache_metrics['cache_performance']['hit_rate'],
            'current_entries': cache_metrics['cache_management']['current_entries'],
            'memory_usage_mb': cache_metrics['memory_usage']['total_size_mb'],
            'utilization_percent': round(cache_metrics['memory_usage']['utilization_percent'], 2)
        })

        return jsonify({
            'success': True,
            'system_overview': system_overview,
            'recommendations': _get_performance_recommendations(system_overview)
        })

    except Exception as e:
        logger.error(f"Error obteniendo vista general del sistema: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def _get_performance_recommendations(overview: dict) -> list:
    """Generar recomendaciones de performance basadas en métricas"""
    recommendations = []

    # Recomendaciones de base de datos
    if overview['database']['monitoring_enabled']:
        db_metrics = overview['database']

        if db_metrics['fragmentation_percent'] > 20:
            recommendations.append({
                'type': 'database',
                'priority': 'high',
                'title': 'Alta fragmentación detectada',
                'description': f"La base de datos tiene {db_metrics['fragmentation_percent']:.1f}% de fragmentación.",
                'action': 'Ejecutar VACUUM para optimizar el almacenamiento',
                'endpoint': '/api/performance/database/optimize'
            })

        if db_metrics['avg_query_time_ms'] > 100:
            recommendations.append({
                'type': 'database',
                'priority': 'medium',
                'title': 'Consultas lentas detectadas',
                'description': f"Tiempo promedio de consulta: {db_metrics['avg_query_time_ms']:.1f}ms",
                'action': 'Revisar índices y optimizar consultas',
                'endpoint': '/api/performance/database/slow-queries'
            })

        if db_metrics['cache_hit_ratio'] < 80:
            recommendations.append({
                'type': 'database',
                'priority': 'medium',
                'title': 'Baja tasa de aciertos en cache',
                'description': f"Cache hit ratio: {db_metrics['cache_hit_ratio']:.1f}%",
                'action': 'Considerar aumentar el tamaño del cache',
                'endpoint': None
            })

    # Recomendaciones de cache
    if overview['cache']['hit_rate_percent'] < 70:
        recommendations.append({
            'type': 'cache',
            'priority': 'medium',
            'title': 'Baja eficiencia de cache',
            'description': f"Hit rate: {overview['cache']['hit_rate_percent']:.1f}%",
            'action': 'Revisar configuración de TTL y patrones de acceso',
            'endpoint': '/api/performance/cache/metrics'
        })

    if overview['cache']['utilization_percent'] > 90:
        recommendations.append({
            'type': 'cache',
            'priority': 'low',
            'title': 'Cache casi lleno',
            'description': f"Utilización: {overview['cache']['utilization_percent']:.1f}%",
            'action': 'Considerar aumentar el tamaño máximo del cache',
            'endpoint': '/api/performance/cache/clear'
        })

    return recommendations

@performance_bp.route('/monitoring/enable', methods=['POST'])
def enable_monitoring():
    """Habilitar monitoreo de performance"""
    try:
        db_path = Path(__file__).parent.parent.parent / 'data' / 'videos.db'
        monitor = get_database_monitor(str(db_path))

        if not monitor:
            return jsonify({
                'success': False,
                'error': 'Database monitor not available'
            }), 500

        monitor.enable_monitoring()

        return jsonify({
            'success': True,
            'monitoring_enabled': True
        })

    except Exception as e:
        logger.error(f"Error habilitando monitoreo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@performance_bp.route('/monitoring/disable', methods=['POST'])
def disable_monitoring():
    """Deshabilitar monitoreo de performance"""
    try:
        db_path = Path(__file__).parent.parent.parent / 'data' / 'videos.db'
        monitor = get_database_monitor(str(db_path))

        if not monitor:
            return jsonify({
                'success': False,
                'error': 'Database monitor not available'
            }), 500

        monitor.disable_monitoring()

        return jsonify({
            'success': True,
            'monitoring_enabled': False
        })

    except Exception as e:
        logger.error(f"Error deshabilitando monitoreo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500