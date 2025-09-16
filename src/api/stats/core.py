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
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN p.deleted_at IS NULL THEN 1 END) as active,
                COUNT(CASE WHEN p.deleted_at IS NOT NULL THEN 1 END) as in_trash,
                COUNT(CASE WHEN p.deleted_at IS NULL AND (m.final_music IS NOT NULL AND m.final_music != '') THEN 1 END) as with_music,
                COUNT(CASE WHEN p.deleted_at IS NULL AND (m.final_characters IS NOT NULL AND m.final_characters != '' AND m.final_characters != '[]') THEN 1 END) as with_characters,
                COUNT(CASE WHEN p.deleted_at IS NULL AND m.processing_status = 'completed' THEN 1 END) as processed,
                COUNT(CASE WHEN p.deleted_at IS NULL AND m.processing_status = 'pending' THEN 1 END) as pending
            FROM media m
            JOIN posts p ON m.post_id = p.id
        """)
        stats = cursor.fetchone()

        return {
            'total': stats[0] or 0,
            'total_in_db': stats[1] or 0,  # Para compatibilidad con el frontend
            'with_music': stats[3] or 0,
            'with_characters': stats[4] or 0,
            'processed': stats[5] or 0,
            'in_trash': stats[2] or 0,
            'pending': stats[6] or 0,
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


@stats_bp.route('/videos')
def api_videos_stats():
    """API para obtener estadísticas de videos"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        with db.get_connection() as conn:
            # Estadísticas básicas
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active,
                    COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as deleted
                FROM videos
            """)
            basic_stats = cursor.fetchone()
            
            # Estadísticas por plataforma
            cursor = conn.execute("""
                SELECT platform, COUNT(*) as count
                FROM videos 
                WHERE deleted_at IS NULL
                GROUP BY platform
                ORDER BY count DESC
            """)
            platform_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Estadísticas por estado de edición
            cursor = conn.execute("""
                SELECT edit_status, COUNT(*) as count
                FROM videos 
                WHERE deleted_at IS NULL
                GROUP BY edit_status
                ORDER BY count DESC
            """)
            edit_status_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Estadísticas por estado de procesamiento
            cursor = conn.execute("""
                SELECT processing_status, COUNT(*) as count
                FROM videos 
                WHERE deleted_at IS NULL
                GROUP BY processing_status
                ORDER BY count DESC
            """)
            processing_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        return jsonify({
            'success': True,
            'stats': {
                'total_videos': basic_stats[0],
                'active_videos': basic_stats[1],
                'deleted_videos': basic_stats[2],
                'by_platform': platform_stats,
                'by_edit_status': edit_status_stats,
                'by_processing_status': processing_stats
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de videos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@stats_bp.route('/trash')
def api_trash_stats():
    """API para obtener estadísticas de la papelera"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_deleted,
                    platform,
                    COUNT(*) as platform_count
                FROM videos 
                WHERE deleted_at IS NOT NULL
                GROUP BY platform
                ORDER BY platform_count DESC
            """)
            
            platform_stats = {}
            total_deleted = 0
            
            for row in cursor.fetchall():
                if not total_deleted:
                    total_deleted = db.count_deleted_videos()
                platform_stats[row[1]] = row[2]
        
        return jsonify({
            'success': True,
            'stats': {
                'total_deleted': total_deleted,
                'by_platform': platform_stats
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de papelera: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@stats_bp.route('/database')
def api_database_stats():
    """Estadísticas detalladas de la base de datos"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        with db.get_connection() as conn:
            # Estadísticas básicas de tablas
            tables_stats = {}
            tables = ['videos', 'creators', 'subscriptions', 'video_lists', 'downloader_mapping']
            
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                tables_stats[table] = cursor.fetchone()[0]
            
            # Información de la base de datos
            cursor = conn.execute("PRAGMA database_list")
            db_info = cursor.fetchall()
            
            # Tamaño de archivo de la BD
            import os
            db_size = 0
            if db_info and os.path.exists(db_info[0][2]):
                db_size = os.path.getsize(db_info[0][2])
        
        return jsonify({
            'success': True,
            'stats': {
                'tables': tables_stats,
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / (1024 * 1024), 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@stats_bp.route('/characters')
def api_character_stats():
    """Estadísticas del sistema de detección de personajes"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        with db.get_connection() as conn:
            # Videos con personajes detectados
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_videos,
                    COUNT(CASE WHEN final_characters IS NOT NULL AND final_characters != '[]' THEN 1 END) as videos_with_characters,
                    COUNT(CASE WHEN detected_characters IS NOT NULL AND detected_characters != '[]' THEN 1 END) as videos_with_detection
                FROM videos 
                WHERE deleted_at IS NULL
            """)
            basic_stats = cursor.fetchone()
            
            # Estadísticas por juego/serie (requiere parsear JSON, simplificado)
            cursor = conn.execute("""
                SELECT final_characters, COUNT(*) as count
                FROM videos 
                WHERE deleted_at IS NULL 
                AND final_characters IS NOT NULL 
                AND final_characters != '[]'
                GROUP BY final_characters
                LIMIT 10
            """)
            
            character_data = []
            for row in cursor.fetchall():
                try:
                    import json
                    chars = json.loads(row[0])
                    if chars:
                        character_data.append({
                            'characters': chars,
                            'count': row[1]
                        })
                except:
                    continue
        
        return jsonify({
            'success': True,
            'stats': {
                'total_videos': basic_stats[0],
                'videos_with_characters': basic_stats[1],
                'videos_with_detection': basic_stats[2],
                'detection_rate': round((basic_stats[1] / basic_stats[0] * 100), 2) if basic_stats[0] > 0 else 0,
                'top_character_combinations': character_data[:5]
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de personajes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@stats_bp.route('/thumbnails')
def api_thumbnail_stats():
    """Estadísticas del sistema de thumbnails"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        with db.get_connection() as conn:
            # Videos con thumbnails
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_videos,
                    COUNT(CASE WHEN thumbnail_path IS NOT NULL THEN 1 END) as videos_with_thumbnails
                FROM videos 
                WHERE deleted_at IS NULL
            """)
            basic_stats = cursor.fetchone()
            
            # Verificar thumbnails existentes en disco
            import os
            from config import config
            thumbnail_dir = config.DATA_DIR / 'thumbnails'
            
            physical_thumbnails = 0
            total_size = 0
            
            if thumbnail_dir.exists():
                for file in thumbnail_dir.iterdir():
                    if file.is_file():
                        physical_thumbnails += 1
                        total_size += file.stat().st_size
        
        return jsonify({
            'success': True,
            'stats': {
                'total_videos': basic_stats[0],
                'videos_with_thumbnails': basic_stats[1],
                'physical_thumbnails': physical_thumbnails,
                'thumbnail_coverage': round((basic_stats[1] / basic_stats[0] * 100), 2) if basic_stats[0] > 0 else 0,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de thumbnails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@stats_bp.route('/system')
def api_system_stats():
    """Estadísticas generales del sistema"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Combinar todas las estadísticas básicas
        with db.get_connection() as conn:
            # Conteos básicos
            cursor = conn.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM videos WHERE deleted_at IS NULL) as active_videos,
                    (SELECT COUNT(*) FROM creators) as total_creators,
                    (SELECT COUNT(*) FROM subscriptions) as total_subscriptions,
                    (SELECT COUNT(DISTINCT platform) FROM videos WHERE deleted_at IS NULL) as platforms
            """)
            basic_counts = cursor.fetchone()
            
            # Información del sistema
            import psutil
            import platform
            
            system_info = {
                'platform': platform.system(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_usage': {
                    'total_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
                    'used_gb': round(psutil.disk_usage('/').used / (1024**3), 2),
                    'free_gb': round(psutil.disk_usage('/').free / (1024**3), 2)
                }
            }
        
        return jsonify({
            'success': True,
            'stats': {
                'content': {
                    'active_videos': basic_counts[0],
                    'total_creators': basic_counts[1],
                    'total_subscriptions': basic_counts[2],
                    'platforms_supported': basic_counts[3]
                },
                'system': system_info
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas del sistema: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@stats_bp.route('/creators/<int:creator_id>')
def api_creator_stats(creator_id):
    """Estadísticas específicas de un creador"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        with db.get_connection() as conn:
            # Verificar que el creador existe
            cursor = conn.execute("SELECT name FROM creators WHERE id = ?", (creator_id,))
            creator = cursor.fetchone()
            if not creator:
                return jsonify({'success': False, 'error': 'Creator not found'}), 404
            
            # Estadísticas del creador
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_videos,
                    COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_videos,
                    COUNT(DISTINCT platform) as platforms,
                    MIN(created_at) as first_video_date,
                    MAX(created_at) as last_video_date
                FROM videos 
                WHERE creator_id = ?
            """, (creator_id,))
            stats = cursor.fetchone()
            
            # Videos por plataforma
            cursor = conn.execute("""
                SELECT platform, COUNT(*) as count
                FROM videos 
                WHERE creator_id = ? AND deleted_at IS NULL
                GROUP BY platform
                ORDER BY count DESC
            """, (creator_id,))
            platform_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        return jsonify({
            'success': True,
            'creator_name': creator[0],
            'stats': {
                'total_videos': stats[0],
                'active_videos': stats[1],
                'platforms': stats[2],
                'first_video_date': stats[3],
                'last_video_date': stats[4],
                'by_platform': platform_stats
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas del creador {creator_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@stats_bp.route('/subscriptions/<subscription_type>/<subscription_id>')
def api_subscription_stats(subscription_type, subscription_id):
    """Estadísticas específicas de una suscripción"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        with db.get_connection() as conn:
            # Buscar suscripción por tipo y ID
            if subscription_type == 'id':
                # Búsqueda por ID numérico
                cursor = conn.execute("SELECT name, type FROM subscriptions WHERE id = ?", (subscription_id,))
            else:
                # Búsqueda por tipo y nombre
                cursor = conn.execute("SELECT name, type FROM subscriptions WHERE type = ? AND name = ?", 
                                    (subscription_type, subscription_id))
            
            subscription = cursor.fetchone()
            if not subscription:
                return jsonify({'success': False, 'error': 'Subscription not found'}), 404
            
            # Obtener ID de la suscripción para las consultas
            if subscription_type == 'id':
                sub_id = subscription_id
            else:
                cursor = conn.execute("SELECT id FROM subscriptions WHERE type = ? AND name = ?", 
                                    (subscription_type, subscription_id))
                sub_id = cursor.fetchone()[0]
            
            # Estadísticas de la suscripción
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_videos,
                    COUNT(CASE WHEN v.deleted_at IS NULL THEN 1 END) as active_videos,
                    MIN(v.created_at) as first_video_date,
                    MAX(v.created_at) as last_video_date
                FROM videos v
                WHERE v.subscription_id = ?
            """, (sub_id,))
            stats = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'subscription_name': subscription[0],
            'subscription_type': subscription[1],
            'stats': {
                'total_videos': stats[0],
                'active_videos': stats[1],
                'first_video_date': stats[2],
                'last_video_date': stats[3]
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de suscripción {subscription_type}/{subscription_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500