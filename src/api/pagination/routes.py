"""
Tag-Flow V2 - Cursor Pagination Routes
Nuevos endpoints optimizados con cursor pagination
"""

import logging
from flask import Blueprint, request, jsonify
from src.database.manager import DatabaseManager

from .cursor_service import CursorPaginationService
from .cache_coordinator import CacheCoordinator
from .performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

# Blueprint para cursor pagination
cursor_pagination_bp = Blueprint('cursor_pagination', __name__, url_prefix='/api/cursor')

# Instancias globales (serán inicializadas en app startup)
cursor_service = None
cache_coordinator = None
performance_monitor = None

def init_pagination_services():
    """Inicializar servicios de paginación"""
    global cursor_service, cache_coordinator, performance_monitor

    cache_coordinator = CacheCoordinator(max_entries=100, default_ttl=300.0)
    performance_monitor = PerformanceMonitor(history_size=1000)

    # cursor_service se inicializa por request ya que necesita conexión DB

# Inicializar servicios al importar el módulo
init_pagination_services()

@cursor_pagination_bp.route('/videos', methods=['GET'])
def get_videos_cursor():
    """
    Endpoint optimizado para obtener videos con cursor pagination

    Query Parameters:
        cursor (str): Cursor de paginación (timestamp)
        direction (str): 'next' o 'prev' (default: 'next')
        limit (int): Número de resultados (1-100, default: 50)
        sort_by (str): Campo de ordenamiento (default: 'created_at')
        sort_order (str): Orden 'asc' o 'desc' (default: 'desc')
        creator_name (str): Filtrar por creador
        platform (str): Filtrar por plataforma
        edit_status (str): Filtrar por estado de edición
        processing_status (str): Filtrar por estado de procesamiento
        search (str): Búsqueda de texto
        has_music (bool): Filtrar por presencia de música
        has_characters (bool): Filtrar por presencia de personajes
    """
    try:
        # Inicializar cursor_service con conexión DB
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor_service = CursorPaginationService(conn)
        # Extraer parámetros
        cursor = request.args.get('cursor')
        direction = request.args.get('direction', 'next')
        limit = min(int(request.args.get('limit', 50)), 100)

        # Parámetros de ordenamiento - DEFECTO: ID DESC
        sort_by = request.args.get('sort_by', 'id')
        sort_order = request.args.get('sort_order', 'desc')

        # Validar campos de ordenamiento permitidos
        allowed_sort_fields = {
            'id': 'm.id',
            'title': 'p.title_post',
            'download_date': 'p.download_date',
            'publication_date': 'p.publication_date',
            'file_name': 'm.file_name',
            'duration': 'm.duration_seconds',
            'size': 'm.file_size_mb'
        }

        if sort_by not in allowed_sort_fields:
            sort_by = 'id'

        # Validar orden
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'

        # Inicializar cursor service con campo de ordenamiento configurado
        cursor_service = CursorPaginationService(conn, cursor_field=allowed_sort_fields[sort_by])

        # Filtros
        filters = {}
        for param in ['creator_name', 'platform', 'edit_status', 'processing_status', 'search']:
            value = request.args.get(param)
            if value:
                filters[param] = value

        # Filtros booleanos
        has_music = request.args.get('has_music')
        if has_music is not None:
            filters['has_music'] = has_music.lower() == 'true'

        has_characters = request.args.get('has_characters')
        if has_characters is not None:
            filters['has_characters'] = has_characters.lower() == 'true'

        # Agregar parámetros de ordenamiento a filters para cache
        filters['sort_by'] = sort_by
        filters['sort_order'] = sort_order

        # Verificar cache
        cached_result = cache_coordinator.get_cursor_result(filters, cursor)
        if cached_result:
            performance_monitor.record_query(
                query_type='cursor_videos',
                execution_time_ms=0,
                items_returned=len(cached_result.data),
                cache_hit=True,
                filters_count=len(filters),
                cursor_used=cursor is not None
            )

            return jsonify({
                'success': True,
                'data': cached_result.data,
                'pagination': {
                    'next_cursor': cached_result.next_cursor,
                    'prev_cursor': cached_result.prev_cursor,
                    'has_more': cached_result.has_more,
                    'total_estimated': cached_result.total_estimated
                },
                'performance': cached_result.performance_info,
                'cache_hit': True
            })

        # Ejecutar query con ordenamiento
        result = cursor_service.get_videos(filters, cursor, direction, limit, sort_order=sort_order)

        # Procesar datos para API (aplicar transformaciones de carousels)
        from src.api.videos.carousels import process_video_data_for_api, add_video_categories

        processed_data = []
        for video in result.data:
            processed_video = process_video_data_for_api(video)
            processed_data.append(processed_video)

        # Añadir categorías
        db_manager = DatabaseManager()
        with db_manager.get_connection() as conn:
            processed_data = add_video_categories(db_manager, processed_data)

        # Actualizar resultado
        result.data = processed_data

        # Cache resultado
        cache_coordinator.cache_cursor_result(filters, cursor, result)

        # Registrar métrica
        performance_monitor.record_query(
            query_type='cursor_videos',
            execution_time_ms=result.performance_info.get('query_time_ms', 0),
            items_returned=len(result.data),
            cache_hit=False,
            filters_count=len(filters),
            cursor_used=cursor is not None,
            error=result.performance_info.get('error')
        )

        return jsonify({
            'success': True,
            'data': result.data,
            'pagination': {
                'next_cursor': result.next_cursor,
                'prev_cursor': result.prev_cursor,
                'has_more': result.has_more,
                'total_estimated': result.total_estimated
            },
            'performance': result.performance_info,
            'cache_hit': False
        })

    except Exception as e:
        logger.error(f"Error in cursor videos endpoint: {e}")

        # Registrar error
        performance_monitor.record_query(
            query_type='cursor_videos',
            execution_time_ms=0,
            items_returned=0,
            cache_hit=False,
            filters_count=len(filters) if 'filters' in locals() else 0,
            cursor_used=cursor is not None if 'cursor' in locals() else False,
            error=str(e)
        )

        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e) if logger.level == logging.DEBUG else 'Error processing request'
        }), 500

    finally:
        # Cerrar conexión si existe
        if 'conn' in locals():
            conn.close()

@cursor_pagination_bp.route('/creators/<creator_name>/videos', methods=['GET'])
def get_creator_videos_cursor(creator_name: str):
    """Endpoint optimizado para videos de creador con cursor pagination"""
    try:
        # Inicializar cursor_service con conexión DB
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor_service = CursorPaginationService(conn)

        cursor = request.args.get('cursor')
        limit = min(int(request.args.get('limit', 50)), 100)
        platform = request.args.get('platform')

        result = cursor_service.get_creator_videos(creator_name, platform, cursor, limit)

        # Procesar datos
        from src.api.videos.carousels import process_video_data_for_api, add_video_categories

        processed_data = []
        for video in result.data:
            processed_video = process_video_data_for_api(video)
            processed_data.append(processed_video)

        db_manager = DatabaseManager()
        with db_manager.get_connection() as conn:
            processed_data = add_video_categories(db_manager, processed_data)

        result.data = processed_data

        # Cache resultado
        filters = {'creator_name': creator_name}
        if platform:
            filters['platform'] = platform
        cache_coordinator.cache_cursor_result(filters, cursor, result)

        # Registrar métrica
        performance_monitor.record_query(
            query_type='cursor_creator_videos',
            execution_time_ms=result.performance_info.get('query_time_ms', 0),
            items_returned=len(result.data),
            cache_hit=False,
            filters_count=len(filters),
            cursor_used=cursor is not None
        )

        return jsonify({
            'success': True,
            'data': result.data,
            'pagination': {
                'next_cursor': result.next_cursor,
                'prev_cursor': result.prev_cursor,
                'has_more': result.has_more,
                'total_estimated': result.total_estimated
            },
            'performance': result.performance_info
        })

    except Exception as e:
        logger.error(f"Error in cursor creator videos endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

    finally:
        # Cerrar conexión si existe
        if 'conn' in locals():
            conn.close()

@cursor_pagination_bp.route('/subscriptions/<subscription_type>/<int:subscription_id>/videos', methods=['GET'])
def get_subscription_videos_cursor(subscription_type: str, subscription_id: int):
    """Endpoint optimizado para videos de suscripción con cursor pagination"""
    try:
        # Inicializar cursor_service con conexión DB
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor_service = CursorPaginationService(conn)

        cursor = request.args.get('cursor')
        limit = min(int(request.args.get('limit', 50)), 100)

        result = cursor_service.get_subscription_videos(subscription_type, subscription_id, cursor, limit)

        # Procesar datos
        from src.api.videos.carousels import process_video_data_for_api, add_video_categories

        processed_data = []
        for video in result.data:
            processed_video = process_video_data_for_api(video)
            processed_data.append(processed_video)

        db_manager = DatabaseManager()
        with db_manager.get_connection() as conn:
            processed_data = add_video_categories(db_manager, processed_data)

        result.data = processed_data

        # Cache resultado
        filters = {
            'subscription_type': subscription_type,
            'subscription_id': subscription_id
        }
        cache_coordinator.cache_cursor_result(filters, cursor, result)

        # Registrar métrica
        performance_monitor.record_query(
            query_type='cursor_subscription_videos',
            execution_time_ms=result.performance_info.get('query_time_ms', 0),
            items_returned=len(result.data),
            cache_hit=False,
            filters_count=len(filters),
            cursor_used=cursor is not None
        )

        return jsonify({
            'success': True,
            'data': result.data,
            'pagination': {
                'next_cursor': result.next_cursor,
                'prev_cursor': result.prev_cursor,
                'has_more': result.has_more,
                'total_estimated': result.total_estimated
            },
            'performance': result.performance_info
        })

    except Exception as e:
        logger.error(f"Error in cursor subscription videos endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

    finally:
        # Cerrar conexión si existe
        if 'conn' in locals():
            conn.close()

@cursor_pagination_bp.route('/trash/videos', methods=['GET'])
def get_trash_videos_cursor():
    """Endpoint optimizado para videos eliminados (papelera) con cursor pagination"""
    try:
        # Inicializar cursor_service con conexión DB
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor_service = CursorPaginationService(conn)

        cursor = request.args.get('cursor')
        limit = min(int(request.args.get('limit', 50)), 100)

        result = cursor_service.get_trash_videos(cursor, limit)

        # Procesar datos
        from src.api.videos.carousels import process_video_data_for_api, add_video_categories

        processed_data = []
        for video in result.data:
            processed_video = process_video_data_for_api(video)
            # Agregar deleted_at para trash
            processed_video['deletedAt'] = video.get('deleted_at')
            processed_data.append(processed_video)

        db_manager = DatabaseManager()
        with db_manager.get_connection() as conn:
            processed_data = add_video_categories(db_manager, processed_data)

        result.data = processed_data

        # Cache resultado
        cache_coordinator.cache_cursor_result({'trash': True}, cursor, result)

        # Registrar métrica
        performance_monitor.record_query(
            query_type='cursor_trash_videos',
            execution_time_ms=result.performance_info.get('query_time_ms', 0),
            items_returned=len(result.data),
            cache_hit=False,
            filters_count=1,  # trash filter
            cursor_used=cursor is not None
        )

        return jsonify({
            'success': True,
            'data': result.data,
            'pagination': {
                'next_cursor': result.next_cursor,
                'prev_cursor': result.prev_cursor,
                'has_more': result.has_more,
                'total_estimated': result.total_estimated
            },
            'performance': result.performance_info
        })

    except Exception as e:
        logger.error(f"Error in cursor trash videos endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

    finally:
        # Cerrar conexión si existe
        if 'conn' in locals():
            conn.close()

@cursor_pagination_bp.route('/performance/stats', methods=['GET'])
def get_performance_stats():
    """Obtener estadísticas de performance del sistema cursor"""
    try:
        window_seconds = int(request.args.get('window', 60))

        current_stats = performance_monitor.get_current_stats(window_seconds)
        performance_grade = performance_monitor.get_performance_grade()
        query_breakdown = performance_monitor.get_query_type_breakdown()
        cache_stats = cache_coordinator.get_stats()

        return jsonify({
            'success': True,
            'window_seconds': window_seconds,
            'current_stats': current_stats.__dict__,
            'performance_grade': performance_grade,
            'query_breakdown': query_breakdown,
            'cache_stats': cache_stats
        })

    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Error retrieving performance stats'
        }), 500

@cursor_pagination_bp.route('/cache/invalidate', methods=['POST'])
def invalidate_cache():
    """Invalidar entradas de cache"""
    try:
        data = request.get_json() or {}
        pattern = data.get('pattern', '*')

        invalidated_count = cache_coordinator.invalidate_pattern(pattern)

        return jsonify({
            'success': True,
            'invalidated_count': invalidated_count,
            'pattern': pattern
        })

    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        return jsonify({
            'success': False,
            'error': 'Error invalidating cache'
        }), 500