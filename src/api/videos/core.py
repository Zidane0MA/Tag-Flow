"""
Tag-Flow V2 - Video Core CRUD Operations API
Core video operations: list, get, update, delete, restore, search, stats
"""

import json
import os
import subprocess
import sys
import threading
from src.api.performance.pagination import smart_paginator
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify

# Import carousel processing functions
from .carousels import process_video_data_for_api, process_image_carousels, add_video_categories

logger = logging.getLogger(__name__)

videos_core_bp = Blueprint('videos_core', __name__, url_prefix='/api')


@videos_core_bp.route('/videos')
def api_videos():
    """
    API endpoint para obtener videos (AJAX) con paginación optimizada

    @deprecated: El sistema OFFSET está marcado para obsolescencia.
    Use /api/cursor/videos para mejor rendimiento y escalabilidad.
    """
    try:
        from src.service_factory import get_database
        db = get_database()

        # Obtener parámetros de filtros
        filters = {}
        for key in ['creator_name', 'platform', 'edit_status', 'processing_status', 'difficulty_level']:
            value = request.args.get(key)
            if value and value != 'All':  # Ignorar 'All' values
                filters[key] = value

        search_query = request.args.get('search')
        if search_query:
            filters['search'] = search_query

        # Parámetros de paginación
        page = int(request.args.get('page', 1))
        cursor = request.args.get('cursor')  # Para cursor-based pagination

        # ✅ CORREGIDO: Soportar offset del frontend
        offset = request.args.get('offset')
        if offset is not None:
            # Convertir offset a página para el paginador
            offset_int = int(offset)
            per_page = int(request.args.get('limit', 50))
            page = (offset_int // per_page) + 1

        # Usar paginación inteligente
        with db.get_connection() as conn:
            result = smart_paginator.paginate_posts(conn, filters, page, cursor)

        # Procesar cada video para la API usando función helper
        for video in result.data:
            process_video_data_for_api(video)

        # ✅ AGREGAR CATEGORÍAS DE POST
        try:
            add_video_categories(db, result.data)
        except Exception as e:
            logger.warning(f"Error agregando categorías: {e}")

        # Procesar carruseles de imágenes
        try:
            processed_videos = process_image_carousels(db, result.data, filters)
        except Exception as e:
            logger.warning(f"Error procesando carruseles: {e}")
            # Si falla el procesado de carruseles, usar videos sin procesar
            processed_videos = result.data

        # Crear respuesta optimizada con información de performance
        response = {
            'success': True,
            'videos': processed_videos,
            'pagination': {
                'current_page': result.meta.current_page,
                'per_page': result.meta.per_page,
                'total_items': result.meta.total_items,
                'total_pages': result.meta.total_pages,
                'has_next': result.meta.has_next,
                'has_prev': result.meta.has_prev,
                'next_page': result.meta.next_page,
                'prev_page': result.meta.prev_page
            },
            'performance': result.performance_info,
            'returned_count': len(processed_videos)
        }

        # Mantener compatibilidad con frontend existente
        response.update({
            'total': result.meta.total_items,
            'total_videos': result.meta.total_items,
            'has_more': result.meta.has_next,
            'limit': result.meta.per_page,
            'offset': (result.meta.current_page - 1) * result.meta.per_page
        })

        return jsonify(response)
        
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
                    video['categories'] = [
                        {
                            'type': row[0]
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

        # Verificar que el video existe usando el nuevo esquema
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.id FROM media m
                JOIN posts p ON m.post_id = p.id
                WHERE m.id = ? AND p.deleted_at IS NULL
            """, (video_id,))

            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Video not found'}), 404

            # Actualizar media table directamente
            set_clauses = []
            params = []
            for key, value in update_data.items():
                set_clauses.append(f"{key} = ?")
                params.append(value)

            if set_clauses:
                update_query = f"UPDATE media SET {', '.join(set_clauses)} WHERE id = ?"
                params.append(video_id)

                cursor = conn.execute(update_query, params)
                success = cursor.rowcount > 0
            else:
                success = False

        if success:
            logger.info(f"Video {video_id} actualizado exitosamente")

            # Obtener video actualizado usando nuevo esquema
            with db.get_connection() as conn:
                cursor = conn.execute("""
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
                        p.carousel_count
                    FROM media m
                    JOIN posts p ON m.post_id = p.id
                    LEFT JOIN creators c ON p.creator_id = c.id
                    LEFT JOIN platforms pl ON p.platform_id = pl.id
                    WHERE m.id = ?
                """, (video_id,))

                row = cursor.fetchone()
                if row:
                    updated_video = {
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
                    }
                    process_video_data_for_api(updated_video)

                    return jsonify({
                        'success': True,
                        'message': 'Video updated successfully',
                        'video': updated_video
                    })
                else:
                    logger.error(f"No se pudo recuperar video actualizado {video_id}")
                    return jsonify({'success': False, 'error': 'Update failed - could not retrieve updated video'}), 500
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
    """
    API para búsqueda de videos

    @deprecated: El sistema OFFSET está marcado para obsolescencia.
    Use /api/cursor/videos con parámetro 'search' para mejor rendimiento.
    """
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