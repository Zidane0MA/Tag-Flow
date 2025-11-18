"""
Tag-Flow V2 - Consolidated Statistics API
All system statistics in one unified module
"""

import logging
from flask import Blueprint, request, jsonify
from src.api.performance.cache import cached, CacheManager

logger = logging.getLogger(__name__)

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')


@cached(ttl=180, key_func=lambda: "global_stats")  # Cache por 3 minutos
def get_global_stats_cached():
    """Obtener estadísticas globales cacheadas"""
    from src.service_factory import get_database
    db = get_database()

    with db.get_connection() as conn:
        # Query única optimizada para todas las estadísticas de media
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_media,
                COUNT(CASE WHEN m.processing_status = 'completed' THEN 1 END) as processed,
                COUNT(CASE WHEN m.processing_status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN (m.final_characters IS NOT NULL AND m.final_characters != '' AND m.final_characters != '[]')
                            OR (m.detected_characters IS NOT NULL AND m.detected_characters != '' AND m.detected_characters != '[]')
                       THEN 1 END) as with_characters,
                COUNT(CASE WHEN m.final_music IS NOT NULL AND m.final_music != '' THEN 1 END) as with_music
            FROM media m
            JOIN posts p ON m.post_id = p.id
            WHERE p.deleted_at IS NULL
        """)
        media_stats = cursor.fetchone()

        # Query única para estadísticas de posts
        cursor = conn.execute("""
            SELECT
                COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as total_posts,
                COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as in_trash
            FROM posts
        """)
        post_stats = cursor.fetchone()

        return {
            'total_posts': post_stats[0] or 0,  # Total de posts sin eliminar
            'total_media': media_stats[0] or 0,  # Total de archivos de media
            'with_music': media_stats[4] or 0,
            'with_characters': media_stats[3] or 0,
            'processed': media_stats[1] or 0,
            'in_trash': post_stats[1] or 0,
            'pending': media_stats[2] or 0,
        }

@stats_bp.route('/')
def api_general_stats():
    """API endpoint general para estadísticas básicas del sistema"""
    try:
        stats = get_global_stats_cached()
        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas generales: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500