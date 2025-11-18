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
from .carousels import process_video_data_for_api

logger = logging.getLogger(__name__)

videos_core_bp = Blueprint('videos_core', __name__, url_prefix='/api')

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

