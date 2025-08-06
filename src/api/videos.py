"""
Tag-Flow V2 - Videos API Blueprint
API endpoints para gestión de videos: CRUD, streaming, bulk operations
"""

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, abort
import logging

# Database will be imported lazily within functions

logger = logging.getLogger(__name__)

videos_bp = Blueprint('videos', __name__, url_prefix='/api')

@videos_bp.route('/videos')
def api_videos():
    """API endpoint para obtener videos (AJAX)"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Obtener parámetros
        filters = {}
        for key in ['creator_name', 'platform', 'edit_status', 'processing_status', 'difficulty_level']:
            value = request.args.get(key)
            if value:
                filters[key] = value
        
        search_query = request.args.get('search')
        if search_query:
            filters['search'] = search_query
        
        limit = int(request.args.get('limit', 0))  # 0 = sin límite
        offset = int(request.args.get('offset', 0))
        
        videos = db.get_videos(filters=filters, limit=limit, offset=offset)
        total_videos = db.count_videos(filters=filters)
        
        # Procesar para JSON y agregar información de suscripciones/listas reales
        for video in videos:
            if video.get('detected_characters'):
                try:
                    video['detected_characters'] = json.loads(video['detected_characters'])
                except:
                    video['detected_characters'] = []
            
            if video.get('final_characters'):
                try:
                    video['final_characters'] = json.loads(video['final_characters'])
                except:
                    video['final_characters'] = []
            
            # ✅ NUEVO: Agregar información real de suscripción desde la BD
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
                    logger.warning(f"Error obteniendo subscription para video {video['id']}: {e}")
            
            # ✅ NUEVO: Agregar información real de listas desde la BD
            try:
                with db.get_connection() as conn:
                    cursor = conn.execute('''
                        SELECT vl.list_type, vl.source_path 
                        FROM video_lists vl 
                        WHERE vl.video_id = ?
                    ''', (video['id'],))
                    list_rows = cursor.fetchall()
                    if list_rows:
                        video['video_lists'] = [
                            {
                                'type': row[0],
                                'name': row[0].replace('_', ' ').title(),
                                'source_path': row[1]
                            } for row in list_rows
                        ]
            except Exception as e:
                logger.warning(f"Error obteniendo listas para video {video['id']}: {e}")
            
            # Preparar título apropiado para el frontend
            if video.get('platform') in ['tiktok', 'instagram'] and video.get('title'):
                if (video.get('platform') == 'instagram' and 
                    video.get('title') and 
                    video.get('title') != video.get('file_name', '').replace('.mp4', '')):
                    video['display_title'] = video['title']
                elif video.get('platform') == 'tiktok':
                    video['display_title'] = video['title']
                else:
                    video['display_title'] = video['file_name']
            else:
                video['display_title'] = video['file_name']
            
            # Procesar thumbnail_path para usar solo el nombre del archivo
            if video.get('thumbnail_path'):
                from pathlib import Path
                video['thumbnail_path'] = Path(video['thumbnail_path']).name
        
        return jsonify({
            'success': True,
            'videos': videos,
            'total': total_videos,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error en API videos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/video/<int:video_id>')
def api_get_video(video_id):
    """API para obtener un video específico"""
    try:
        from src.service_factory import get_database
        db = get_database()
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        # Procesar datos JSON
        if video.get('detected_characters'):
            try:
                video['detected_characters'] = json.loads(video['detected_characters'])
            except:
                video['detected_characters'] = []
        
        if video.get('final_characters'):
            try:
                video['final_characters'] = json.loads(video['final_characters'])
            except:
                video['final_characters'] = []
        else:
            video['final_characters'] = []
        
        # ✅ NUEVO: Agregar información real de suscripción desde la BD
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
        
        # ✅ NUEVO: Agregar información real de listas desde la BD
        try:
            with db.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT vl.list_type, vl.source_path 
                    FROM video_lists vl 
                    WHERE vl.video_id = ?
                ''', (video_id,))
                list_rows = cursor.fetchall()
                if list_rows:
                    video['video_lists'] = [
                        {
                            'type': row[0],
                            'name': row[0].replace('_', ' ').title(),
                            'source_path': row[1]
                        } for row in list_rows
                    ]
        except Exception as e:
            logger.warning(f"Error obteniendo listas para video {video_id}: {e}")
        
        # Preparar título apropiado para el frontend
        if video.get('platform') in ['tiktok', 'instagram'] and video.get('title'):
            if (video.get('platform') == 'instagram' and 
                video.get('title') and 
                video.get('title') != video.get('file_name', '').replace('.mp4', '')):
                video['display_title'] = video['title']
            elif video.get('platform') == 'tiktok':
                video['display_title'] = video['title']
            else:
                video['display_title'] = video['file_name']
        else:
            video['display_title'] = video['file_name']
        
        return jsonify({
            'success': True,
            'video': video
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/video/<int:video_id>/play')
def api_play_video(video_id):
    """API para obtener información de reproducción del video"""
    try:
        from src.service_factory import get_database
        db = get_database()
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        video_path = Path(video['file_path'])
        if not video_path.exists():
            return jsonify({'success': False, 'error': 'Video file not found'}), 404
        
        # Verificar que el archivo sea accesible
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(video_path))
        
        return jsonify({
            'success': True,
            'video_path': str(video_path),
            'file_name': video['file_name'],
            'mime_type': mime_type,
            'file_size': video.get('file_size', 0),
            'duration': video.get('duration_seconds', 0)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo info de reproducción para video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/video/<int:video_id>/update', methods=['POST'])
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
        
        updates = {}
        for field, value in data.items():
            if field in allowed_fields:
                # Ignorar difficulty_level si es vacío o None
                if field == 'difficulty_level' and (value is None or value == ''):
                    continue
                # Procesar listas/arrays especialmente
                if field == 'final_characters' and isinstance(value, list):
                    updates[field] = json.dumps(value)
                else:
                    updates[field] = value
            else:
                logger.warning(f"Campo no permitido ignorado: {field}")
        
        if not updates:
            logger.error(f"No valid fields to update for video {video_id}")
            return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
        
        logger.info(f"Campos a actualizar para video {video_id}: {updates}")
        
        from src.service_factory import get_database
        db = get_database()
        
        # Actualizar en base de datos
        success = db.update_video(video_id, updates)
        
        if success:
            logger.info(f"Video {video_id} actualizado exitosamente")
            # Obtener video actualizado
            updated_video = db.get_video(video_id)
            
            # Procesar datos JSON para respuesta
            if updated_video.get('detected_characters'):
                try:
                    updated_video['detected_characters'] = json.loads(updated_video['detected_characters'])
                except:
                    updated_video['detected_characters'] = []
            
            if updated_video.get('final_characters'):
                try:
                    updated_video['final_characters'] = json.loads(updated_video['final_characters'])
                except:
                    updated_video['final_characters'] = []
            
            return jsonify({
                'success': True, 
                'message': 'Video actualizado correctamente',
                'video': updated_video
            })
        else:
            logger.error(f"Error actualizando video {video_id}")
            return jsonify({'success': False, 'error': 'Error updating video'}), 500
        
    except Exception as e:
        logger.error(f"Error actualizando video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/video/<int:video_id>/open-folder', methods=['POST'])
def api_open_folder(video_id):
    """API para abrir la carpeta del video en el explorador"""
    try:
        from src.service_factory import get_database
        db = get_database()
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        video_path = Path(video['file_path'])
        if not video_path.exists():
            return jsonify({'success': False, 'error': 'Video file not found'}), 404
        
        folder_path = video_path.parent
        
        # Abrir carpeta según el sistema operativo
        import platform
        system = platform.system()
        
        if system == "Windows":
            os.startfile(folder_path)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", folder_path])
        else:  # Linux
            subprocess.run(["xdg-open", folder_path])
        
        return jsonify({'success': True, 'message': f'Carpeta abierta: {folder_path}'})
        
    except Exception as e:
        logger.error(f"Error abriendo carpeta para video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/video/<int:video_id>/delete', methods=['POST'])
def api_delete_video(video_id):
    """API para eliminar (soft delete) un video"""
    try:
        from src.service_factory import get_database
        db = get_database()
        success = db.soft_delete_video(video_id)
        if success:
            return jsonify({'success': True, 'message': 'Video moved to trash'})
        else:
            return jsonify({'success': False, 'error': 'Error deleting video'}), 500
        
    except Exception as e:
        logger.error(f"Error eliminando video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/video/<int:video_id>/restore', methods=['POST'])
def api_restore_video(video_id):
    """API para restaurar un video desde la papelera"""
    try:
        from src.service_factory import get_database
        db = get_database()
        success = db.restore_video(video_id)
        if success:
            return jsonify({'success': True, 'message': 'Video restored from trash'})
        else:
            return jsonify({'success': False, 'error': 'Error restoring video'}), 500
        
    except Exception as e:
        logger.error(f"Error restaurando video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/video/<int:video_id>/permanent-delete', methods=['POST'])
def api_permanent_delete_video(video_id):
    """API para eliminar permanentemente un video"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Obtener video antes de eliminarlo para mostrar información
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        success = db.permanent_delete_video(video_id)
        if success:
            return jsonify({
                'success': True, 
                'message': f'Video "{video["file_name"]}" permanently deleted'
            })
        else:
            return jsonify({'success': False, 'error': 'Error permanently deleting video'}), 500
        
    except Exception as e:
        logger.error(f"Error eliminando permanentemente video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/stats')
def api_stats():
    """API para obtener estadísticas del sistema"""
    try:
        from src.service_factory import get_database
        db = get_database()
        stats = db.get_stats()
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/video/<int:video_id>/reanalyze', methods=['POST'])
def api_reanalyze_video(video_id):
    """API para reanalizar un video específico"""
    try:
        data = request.get_json() or {}
        force = data.get('force', False)
        
        from src.service_factory import get_database
        db = get_database()
        
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
                cmd = [sys.executable, 'main.py', '--reanalyze-video', str(video_id)]
                if force:
                    cmd.append('--force')
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
                
                if result.returncode != 0:
                    db.update_video(video_id, {
                        'processing_status': 'error',
                        'error_message': result.stderr or 'Error desconocido'
                    })
                    logger.error(f"Error en reanálisis de video {video_id}: {result.stderr}")
                
            except Exception as e:
                db.update_video(video_id, {
                    'processing_status': 'error',
                    'error_message': str(e)
                })
                logger.error(f"Error ejecutando reanálisis de video {video_id}: {e}")
        
        # Ejecutar en thread separado
        import threading
        thread = threading.Thread(target=run_reanalysis)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Reanálisis iniciado para video {video_id}',
            'video_id': video_id
        })
        
    except Exception as e:
        logger.error(f"Error iniciando reanálisis de video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/videos/bulk-reanalyze', methods=['POST'])
def api_bulk_reanalyze_videos():
    """API para reanalizar múltiples videos"""
    try:
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        force = data.get('force', False)
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No se proporcionaron IDs de videos'}), 400
        
        # Validar que todos los IDs sean números enteros
        try:
            video_ids = [int(vid) for vid in video_ids]
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Todos los IDs deben ser números enteros'}), 400
        
        # Verificar que todos los videos existen
        missing_videos = []
        for video_id in video_ids:
            video = db.get_video(video_id)
            if not video:
                missing_videos.append(video_id)
        
        if missing_videos:
            return jsonify({
                'success': False, 
                'error': f'Videos no encontrados: {", ".join(map(str, missing_videos))}'
            }), 404
        
        # Marcar todos los videos como procesando
        for video_id in video_ids:
            db.update_video(video_id, {
                'processing_status': 'procesando',
                'error_message': None
            })
        
        def run_bulk_reanalysis():
            try:
                cmd = [sys.executable, 'main.py', '--reanalyze-video', ','.join(map(str, video_ids))]
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
                    timeout=600
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr or 'Error desconocido en el reanálisis masivo'
                    for video_id in video_ids:
                        db.update_video(video_id, {
                            'processing_status': 'error',
                            'error_message': error_msg
                        })
                    logger.error(f"Error en reanálisis masivo: {error_msg}")
                
            except subprocess.TimeoutExpired:
                error_msg = 'Timeout: El reanálisis masivo tomó demasiado tiempo'
                for video_id in video_ids:
                    db.update_video(video_id, {
                        'processing_status': 'error',
                        'error_message': error_msg
                    })
                logger.error(f"Timeout en reanálisis masivo: {error_msg}")
            except Exception as e:
                for video_id in video_ids:
                    db.update_video(video_id, {
                        'processing_status': 'error',
                        'error_message': f'Error iniciando reanálisis masivo: {str(e)}'
                    })
                logger.error(f"Error ejecutando reanálisis masivo: {e}")
        
        # Ejecutar en thread separado
        import threading
        thread = threading.Thread(target=run_bulk_reanalysis)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Reanálisis masivo iniciado para {len(video_ids)} videos',
            'video_ids': video_ids,
            'total_videos': len(video_ids)
        })
        
    except Exception as e:
        logger.error(f"Error en reanálisis masivo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/videos/delete-bulk', methods=['POST'])
def api_bulk_delete_videos():
    """API para eliminar múltiples videos (soft delete)"""
    try:
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No video IDs provided'}), 400
        
        success_count = 0
        for video_id in video_ids:
            if db.soft_delete_video(video_id):
                success_count += 1
        
        return jsonify({
            'success': True,
            'message': f'{success_count} videos moved to trash',
            'deleted_count': success_count
        })
        
    except Exception as e:
        logger.error(f"Error en eliminación masiva: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/videos/restore-bulk', methods=['POST'])
def api_bulk_restore_videos():
    """API para restaurar múltiples videos desde papelera"""
    try:
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No video IDs provided'}), 400
        
        success_count = 0
        for video_id in video_ids:
            if db.restore_video(video_id):
                success_count += 1
        
        return jsonify({
            'success': True,
            'message': f'{success_count} videos restored from trash',
            'restored_count': success_count
        })
        
    except Exception as e:
        logger.error(f"Error en restauración masiva: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/videos/bulk-update', methods=['POST'])
def api_bulk_update_videos():
    """API para actualizar múltiples videos"""
    try:
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        updates = data.get('updates', {})
        
        if not video_ids or not updates:
            return jsonify({'success': False, 'error': 'Video IDs and updates required'}), 400
        
        # Validar campos permitidos
        allowed_fields = {
            'final_music', 'final_music_artist', 'final_characters', 
            'difficulty_level', 'edit_status', 'notes', 'processing_status'
        }
        
        filtered_updates = {}
        for field, value in updates.items():
            if field in allowed_fields:
                if field == 'final_characters' and isinstance(value, list):
                    filtered_updates[field] = json.dumps(value)
                else:
                    filtered_updates[field] = value
        
        if not filtered_updates:
            return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
        
        from src.service_factory import get_database
        db = get_database()
        
        success_count = 0
        for video_id in video_ids:
            if db.update_video(video_id, filtered_updates):
                success_count += 1
        
        return jsonify({
            'success': True,
            'message': f'{success_count} videos updated successfully',
            'updated_count': success_count
        })
        
    except Exception as e:
        logger.error(f"Error en actualización masiva: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/videos/bulk-edit', methods=['POST'])
def api_bulk_edit_videos():
    """API para edición masiva avanzada de videos"""
    try:
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        operation = data.get('operation', 'update')
        updates = data.get('updates', {})
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No video IDs provided'}), 400
        
        from src.service_factory import get_database
        db = get_database()
        
        success_count = 0
        
        if operation == 'update':
            # Actualización normal
            allowed_fields = {
                'final_music', 'final_music_artist', 'final_characters', 
                'difficulty_level', 'edit_status', 'notes', 'processing_status'
            }
            
            filtered_updates = {}
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == 'final_characters' and isinstance(value, list):
                        filtered_updates[field] = json.dumps(value)
                    else:
                        filtered_updates[field] = value
            
            for video_id in video_ids:
                if db.update_video(video_id, filtered_updates):
                    success_count += 1
        
        elif operation == 'mark_completed':
            for video_id in video_ids:
                if db.update_video(video_id, {'edit_status': 'completado'}):
                    success_count += 1
        
        elif operation == 'mark_pending':
            for video_id in video_ids:
                if db.update_video(video_id, {'edit_status': 'pendiente'}):
                    success_count += 1
        
        elif operation == 'clear_characters':
            for video_id in video_ids:
                if db.update_video(video_id, {'final_characters': '[]'}):
                    success_count += 1
        
        else:
            return jsonify({'success': False, 'error': 'Invalid operation'}), 400
        
        return jsonify({
            'success': True,
            'message': f'{success_count} videos processed successfully',
            'operation': operation,
            'processed_count': success_count
        })
        
    except Exception as e:
        logger.error(f"Error en edición masiva: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/videos/bulk-delete', methods=['POST'])
def api_bulk_delete_final():
    """API alternativa para eliminación masiva"""
    try:
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No video IDs provided'}), 400
        
        success_count = 0
        for video_id in video_ids:
            if db.soft_delete_video(video_id):
                success_count += 1
        
        return jsonify({
            'success': True,
            'message': f'{success_count} videos moved to trash',
            'deleted_count': success_count
        })
        
    except Exception as e:
        logger.error(f"Error en eliminación masiva final: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/trash/stats')
def api_trash_stats():
    """API para obtener estadísticas de papelera"""
    try:
        total_deleted = db.count_videos({'is_deleted': True})
        
        return jsonify({
            'success': True,
            'total_deleted': total_deleted
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de papelera: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bp.route('/search')
def api_search():
    """API para búsqueda de videos"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': False, 'error': 'Query parameter required'}), 400
        
        limit = int(request.args.get('limit', 10))
        
        # Buscar en múltiples campos
        videos = db.search_videos(query, limit=limit)
        
        # Procesar resultados
        for video in videos:
            if video.get('detected_characters'):
                try:
                    video['detected_characters'] = json.loads(video['detected_characters'])
                except:
                    video['detected_characters'] = []
            
            if video.get('final_characters'):
                try:
                    video['final_characters'] = json.loads(video['final_characters'])
                except:
                    video['final_characters'] = []
        
        return jsonify({
            'success': True,
            'query': query,
            'results': videos,
            'total': len(videos)
        })
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500