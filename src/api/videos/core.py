"""
Tag-Flow V2 - Video Core CRUD Operations API
Core video operations: list, get, update, delete, restore, search, stats
"""

import json
import os
import subprocess
import sys
import threading
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify

# Import carousel processing functions
from .carousels import process_video_data_for_api, process_image_carousels

logger = logging.getLogger(__name__)

videos_core_bp = Blueprint('videos_core', __name__, url_prefix='/api')


@videos_core_bp.route('/videos')
def api_videos():
    """API endpoint para obtener videos (AJAX)"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Obtener parámetros
        filters = {}
        for key in ['creator_name', 'platform', 'edit_status', 'processing_status', 'difficulty_level']:
            value = request.args.get(key)
            if value and value != 'All':  # Ignorar 'All' values
                filters[key] = value
        
        search_query = request.args.get('search')
        if search_query:
            filters['search'] = search_query
        
        limit = int(request.args.get('limit', 0))  # 0 = sin límite
        offset = int(request.args.get('offset', 0))
        
        # Consulta directa usando el nuevo esquema
        with db.get_connection() as conn:
            # Construir query con el nuevo esquema
            query = """
                SELECT
                    m.id,
                    p.title_post,
                    m.file_path,
                    m.file_name,
                    m.thumbnail_path,
                    m.file_size,
                    m.duration_seconds,
                    c.name as creator_name,
                    pl.name as platform,
                    m.detected_music,
                    m.detected_music_artist,
                    m.detected_characters,
                    m.final_music,
                    m.final_music_artist,
                    m.final_characters,
                    m.difficulty_level,
                    m.edit_status,
                    m.processing_status,
                    m.notes,
                    m.created_at,
                    m.last_updated,
                    p.post_url,
                    p.publication_date,
                    p.download_date,
                    p.deleted_at,
                    p.is_carousel,
                    p.carousel_count,
                    s.id as subscription_id,
                    s.name as subscription_name,
                    s.subscription_type
                FROM media m
                JOIN posts p ON m.post_id = p.id
                LEFT JOIN creators c ON p.creator_id = c.id
                LEFT JOIN platforms pl ON p.platform_id = pl.id
                LEFT JOIN subscriptions s ON p.subscription_id = s.id
                WHERE p.deleted_at IS NULL
            """

            params = []

            # Agregar filtros
            if filters.get('search'):
                query += " AND (p.title_post LIKE ? OR m.file_name LIKE ? OR c.name LIKE ?)"
                search_param = f"%{filters['search']}%"
                params.extend([search_param, search_param, search_param])

            if filters.get('creator_name') and filters['creator_name'] != 'All':
                query += " AND c.name = ?"
                params.append(filters['creator_name'])

            if filters.get('platform') and filters['platform'] != 'All':
                query += " AND pl.name = ?"
                params.append(filters['platform'])

            if filters.get('edit_status') and filters['edit_status'] != 'All':
                query += " AND m.edit_status = ?"
                params.append(filters['edit_status'])

            if filters.get('processing_status') and filters['processing_status'] != 'All':
                query += " AND m.processing_status = ?"
                params.append(filters['processing_status'])

            if filters.get('difficulty_level') and filters['difficulty_level'] != 'All':
                query += " AND m.difficulty_level = ?"
                params.append(filters['difficulty_level'])

            # Orden y límite
            query += " ORDER BY m.created_at DESC"
            if limit > 0:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            # Obtener videos
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            # Convertir a formato de videos
            videos = []
            for row in rows:
                video = {
                    'id': row[0],
                    'title_post': row[1],
                    'file_path': row[2],
                    'file_name': row[3],
                    'thumbnail_path': row[4],
                    'file_size': row[5],
                    'duration_seconds': row[6],
                    'creator_name': row[7] or 'Unknown',
                    'platform': row[8] or 'unknown',
                    'detected_music': row[9],
                    'detected_music_artist': row[10],
                    'detected_characters': row[11],
                    'final_music': row[12],
                    'final_music_artist': row[13],
                    'final_characters': row[14],
                    'difficulty_level': row[15] or 'low',
                    'edit_status': row[16] or 'pendiente',
                    'processing_status': row[17] or 'pending',
                    'notes': row[18],
                    'created_at': row[19],
                    'last_updated': row[20],
                    'post_url': row[21],
                    'publication_date': row[22],
                    'download_date': row[23],
                    'deleted_at': row[24],
                    'is_carousel': row[25],
                    'carousel_count': row[26],
                    'subscription_id': row[27],
                }

                # Agregar información de suscripción si está disponible
                if row[27]:  # subscription_id
                    video['subscription_info'] = {
                        'id': row[27],
                        'name': row[28],
                        'type': row[29]
                    }

                videos.append(video)

            # Obtener total count
            count_query = """
                SELECT COUNT(DISTINCT m.id)
                FROM media m
                JOIN posts p ON m.post_id = p.id
                LEFT JOIN creators c ON p.creator_id = c.id
                LEFT JOIN platforms pl ON p.platform_id = pl.id
                WHERE p.deleted_at IS NULL
            """
            count_params = []

            if filters.get('search'):
                count_query += " AND (p.title_post LIKE ? OR m.file_name LIKE ? OR c.name LIKE ?)"
                count_params.extend([search_param, search_param, search_param])
            if filters.get('creator_name') and filters['creator_name'] != 'All':
                count_query += " AND c.name = ?"
                count_params.append(filters['creator_name'])
            if filters.get('platform') and filters['platform'] != 'All':
                count_query += " AND pl.name = ?"
                count_params.append(filters['platform'])
            if filters.get('edit_status') and filters['edit_status'] != 'All':
                count_query += " AND m.edit_status = ?"
                count_params.append(filters['edit_status'])
            if filters.get('processing_status') and filters['processing_status'] != 'All':
                count_query += " AND m.processing_status = ?"
                count_params.append(filters['processing_status'])
            if filters.get('difficulty_level') and filters['difficulty_level'] != 'All':
                count_query += " AND m.difficulty_level = ?"
                count_params.append(filters['difficulty_level'])

            cursor = conn.execute(count_query, count_params)
            total_videos = cursor.fetchone()[0]
        
        # Procesar cada video para la API
        for video in videos:
            process_video_data_for_api(video)

        # Procesar carruseles de imágenes
        try:
            processed_videos = process_image_carousels(db, videos, filters)
        except:
            # Si falla el procesado de carruseles, usar videos sin procesar
            processed_videos = videos
        
        # Calcular has_more correctamente considerando la consolidación de carruseles
        original_count = len(videos)
        processed_count = len(processed_videos)
        
        # Cálculo simple y directo de has_more
        if limit > 0:
            # Verificar si hay más contenido en el siguiente offset normal
            next_offset = offset + original_count
            has_more = next_offset < total_videos
            logger.info(f"📊 HAS_MORE - offset:{offset}, original_count:{original_count}, next_offset:{next_offset}, total:{total_videos}, has_more:{has_more}")
        else:
            # Sin límite, no hay más
            has_more = False
        
        return jsonify({
            'success': True,
            'videos': processed_videos,
            'total': total_videos,  # Mantener total original de la BD
            'total_videos': total_videos,  # Para compatibilidad con frontend
            'limit': limit,
            'offset': offset,
            'has_more': has_more,
            'returned_count': len(processed_videos),  # Para debugging
            'original_count': original_count,  # Para debugging
            'reduction_factor': processed_count / original_count if original_count > 0 else 1  # Para debugging
        })
        
    except Exception as e:
        logger.error(f"Error en API videos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@videos_core_bp.route('/video/<int:video_id>')
def api_get_video(video_id):
    """API para obtener detalles de un video específico"""
    try:
        from src.service_factory import get_database
        db = get_database()
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        # Procesar video para la API
        process_video_data_for_api(video)
        
        # Agregar información de suscripción si existe
        if video.get('subscription_id'):
            try:
                with db.get_connection() as conn:
                    cursor = conn.execute('''
                        SELECT s.name, s.type, s.platform, s.subscription_url 
                        FROM subscriptions s 
                        WHERE s.id = ?
                    ''', (video['subscription_id'],))
                    sub_row = cursor.fetchone()
                    if sub_row:
                        video['subscription_info'] = {
                            'id': video['subscription_id'],
                            'name': sub_row[0],
                            'type': sub_row[1], 
                            'platform': sub_row[2],
                            'url': sub_row[3]
                        }
            except Exception as e:
                logger.warning(f"Error obteniendo subscription para video {video_id}: {e}")
        
        # Agregar información de listas
        try:
            with db.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT vl.list_type 
                    FROM video_lists vl 
                    WHERE vl.video_id = ?
                ''', (video_id,))
                list_rows = cursor.fetchall()
                if list_rows:
                    video['video_lists'] = [
                        {
                            'type': row[0],
                            'name': row[0].replace('_', ' ').title()
                        } for row in list_rows
                    ]
        except Exception as e:
            logger.warning(f"Error obteniendo listas para video {video_id}: {e}")
        
        return jsonify({
            'success': True,
            'video': video
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@videos_core_bp.route('/video/<int:video_id>/update', methods=['POST'])
def api_update_video(video_id):
    """API para actualizar un video (edición inline)"""
    try:
        logger.info(f"Actualizando video {video_id}")
        
        data = request.get_json()
        if not data:
            logger.error(f"No data provided for video {video_id}")
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        logger.info(f"Datos recibidos para video {video_id}: {data}")
        
        # Validar campos permitidos
        allowed_fields = {
            'final_music', 'final_music_artist', 'final_characters', 
            'difficulty_level', 'edit_status', 'notes', 'processing_status'
        }
        
        update_data = {}
        for key, value in data.items():
            if key in allowed_fields:
                # Procesar campos JSON
                if key == 'final_characters' and isinstance(value, list):
                    update_data[key] = json.dumps(value)
                else:
                    update_data[key] = value
            else:
                logger.warning(f"Campo no permitido ignorado: {key}")
        
        if not update_data:
            return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
        
        from src.service_factory import get_database
        db = get_database()
        
        # Verificar que el video existe
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        # Actualizar video
        success = db.update_video(video_id, update_data)
        
        if success:
            logger.info(f"Video {video_id} actualizado exitosamente")
            # Obtener video actualizado
            updated_video = db.get_video(video_id)
            process_video_data_for_api(updated_video)
            
            return jsonify({
                'success': True,
                'message': 'Video updated successfully',
                'video': updated_video
            })
        else:
            logger.error(f"Error actualizando video {video_id}")
            return jsonify({'success': False, 'error': 'Update failed'}), 500
        
    except Exception as e:
        logger.error(f"Error actualizando video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@videos_core_bp.route('/video/<int:video_id>/delete', methods=['POST'])
def api_delete_video(video_id):
    """API para borrar un video (soft delete)"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Verificar que el video existe
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        # Soft delete
        success = db.delete_video(video_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Video moved to trash'})
        else:
            return jsonify({'success': False, 'error': 'Delete failed'}), 500
        
    except Exception as e:
        logger.error(f"Error borrando video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@videos_core_bp.route('/video/<int:video_id>/restore', methods=['POST'])
def api_restore_video(video_id):
    """API para restaurar un video de la papelera"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Restaurar video
        success = db.restore_video(video_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Video restored successfully'})
        else:
            return jsonify({'success': False, 'error': 'Restore failed'}), 500
        
    except Exception as e:
        logger.error(f"Error restaurando video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@videos_core_bp.route('/video/<int:video_id>/permanent-delete', methods=['POST'])
def api_permanent_delete_video(video_id):
    """API para eliminar permanentemente un video"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Verificar que el video existe y está en la papelera
        video = db.get_video(video_id, include_deleted=True)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        if not video.get('deleted_at'):
            return jsonify({'success': False, 'error': 'Video is not in trash'}), 400
        
        # Eliminar permanentemente
        success = db.permanent_delete_video(video_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Video permanently deleted'})
        else:
            return jsonify({'success': False, 'error': 'Permanent delete failed'}), 500
        
    except Exception as e:
        logger.error(f"Error eliminando permanentemente video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@videos_core_bp.route('/video/<int:video_id>/reanalyze', methods=['POST'])
def api_reanalyze_video(video_id):
    """API para reanalizar un video específico"""
    try:
        data = request.get_json() or {}
        force = data.get('force', False)
        
        from src.service_factory import get_database
        db = get_database()
        
        # Verificar que el video existe
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        # Marcar como procesando
        db.update_video(video_id, {
            'processing_status': 'procesando',
            'error_message': None
        })
        
        def run_reanalysis():
            try:
                cmd = [sys.executable, 'main.py', 'process', '--reanalyze-video', str(video_id)]
                if force:
                    cmd.append('--force')
                
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                env['PYTHONUNBUFFERED'] = '1'
                
                result = subprocess.run(
                    cmd,
                    cwd=Path.cwd(),
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    env=env,
                    timeout=300
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr or 'Error desconocido en el reanálisis'
                    db.update_video(video_id, {
                        'processing_status': 'error',
                        'error_message': error_msg
                    })
                    logger.error(f"Error en reanálisis de video {video_id}: {error_msg}")
                
            except subprocess.TimeoutExpired:
                error_msg = 'Timeout: El reanálisis tomó demasiado tiempo'
                db.update_video(video_id, {
                    'processing_status': 'error',
                    'error_message': error_msg
                })
                logger.error(f"Timeout en reanálisis de video {video_id}: {error_msg}")
            except Exception as e:
                db.update_video(video_id, {
                    'processing_status': 'error',
                    'error_message': f'Error iniciando reanálisis: {str(e)}'
                })
                logger.error(f"Error ejecutando reanálisis de video {video_id}: {e}")
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=run_reanalysis)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Reanálisis iniciado para video {video_id}',
            'video_id': video_id
        })
        
    except Exception as e:
        logger.error(f"Error en reanálisis de video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500




@videos_core_bp.route('/search')
def api_search():
    """API para búsqueda de videos"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'}), 400
        
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Crear filtros para búsqueda
        filters = {'search': query}
        
        # Agregar filtros adicionales si se proporcionan
        for key in ['platform', 'edit_status', 'processing_status']:
            value = request.args.get(key)
            if value and value != 'All':
                filters[key] = value
        
        # Buscar videos
        videos = db.get_videos(filters=filters, limit=limit, offset=offset)
        total_results = db.count_videos(filters=filters)
        
        # Procesar videos para la API
        for video in videos:
            process_video_data_for_api(video)
        
        return jsonify({
            'success': True,
            'videos': videos,
            'total': total_results,
            'limit': limit,
            'offset': offset,
            'query': query,
            'has_more': (offset + len(videos)) < total_results
        })
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500