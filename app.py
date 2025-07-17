"""
Tag-Flow V2 - Aplicación Flask
Interfaz web para gestión y edición de videos TikTok/MMD
"""

import sys
from pathlib import Path
import json
import subprocess
import os
from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_cors import CORS
import logging

# Agregar src al path
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config
from src.database import db

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
app.config.from_object(config)
CORS(app)

# Asegurar que los directorios existen
config.ensure_directories()

@app.route('/')
def index():
    """Página principal - galería de videos"""
    try:
        # Obtener filtros de la query string
        filters = {}
        if request.args.get('creator'):
            filters['creator_name'] = request.args.get('creator')
        if request.args.get('platform'):
            filters['platform'] = request.args.get('platform')
        if request.args.get('status'):
            filters['edit_status'] = request.args.get('status')
        if request.args.get('processing_status'):
            filters['processing_status'] = request.args.get('processing_status')
        if request.args.get('difficulty'):
            filters['difficulty_level'] = request.args.get('difficulty')
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        # Paginación
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        # Obtener videos y contar totales
        videos = db.get_videos(filters=filters, limit=per_page, offset=offset)
        total_videos = db.count_videos(filters=filters)
        total_pages = (total_videos + per_page - 1) // per_page  # Redondear hacia arriba
        
        # Obtener datos para filtros
        creators = db.get_unique_creators()
        music_tracks = db.get_unique_music()
        stats = db.get_stats()
        
        # Procesar videos para el template
        for video in videos:
            # Parsear JSON de personajes
            if video.get('detected_characters'):
                try:
                    video['detected_characters'] = json.loads(video['detected_characters'])
                except:
                    video['detected_characters'] = []
            else:
                video['detected_characters'] = []
            
            if video.get('final_characters'):
                try:
                    video['final_characters'] = json.loads(video['final_characters'])
                except:
                    video['final_characters'] = []
            else:
                video['final_characters'] = []
            
            
            # URL del thumbnail
            if video.get('thumbnail_path'):
                video['thumbnail_url'] = f"/thumbnail/{Path(video['thumbnail_path']).name}"
            else:
                video['thumbnail_url'] = "/static/img/no-thumbnail.jpg"
            
            # Preparar título apropiado para el frontend
            if video.get('platform') in ['tiktok', 'instagram'] and video.get('description'):
                # Para TikTok e Instagram: usar descripción como título si está disponible
                # Para Instagram: verificar que no sea solo el nombre del archivo
                if (video.get('platform') == 'instagram' and 
                    video.get('description') and 
                    video.get('description') != video.get('file_name', '').replace('.mp4', '')):
                    video['display_title'] = video['description']
                elif video.get('platform') == 'tiktok':
                    video['display_title'] = video['description']
                else:
                    video['display_title'] = video['file_name']
            else:
                # Para otras plataformas: usar nombre del archivo
                video['display_title'] = video['file_name']
        
        return render_template('gallery.html',
                             videos=videos,
                             creators=creators,
                             music_tracks=music_tracks,
                             stats=stats,
                             current_filters=filters,
                             page=page,
                             per_page=per_page,
                             total_pages=total_pages,
                             total_videos=total_videos)
        
    except Exception as e:
        logger.error(f"Error en página principal: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/video/<int:video_id>')
def view_video(video_id):
    """Vista detallada de un video individual"""
    try:
        video = db.get_video(video_id)
        if not video:
            abort(404)
        
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
        
        # Preparar título apropiado para el frontend
        if video.get('platform') in ['tiktok', 'instagram'] and video.get('description'):
            # Para TikTok e Instagram: usar descripción como título si está disponible
            # Para Instagram: verificar que no sea solo el nombre del archivo
            if (video.get('platform') == 'instagram' and 
                video.get('description') and 
                video.get('description') != video.get('file_name', '').replace('.mp4', '')):
                video['display_title'] = video['description']
            elif video.get('platform') == 'tiktok':
                video['display_title'] = video['description']
            else:
                video['display_title'] = video['file_name']
        else:
            # Para otras plataformas: usar nombre del archivo
            video['display_title'] = video['file_name']
        
        return render_template('video_detail.html', video=video)
        
    except Exception as e:
        logger.error(f"Error mostrando video {video_id}: {e}")
        abort(500)

@app.route('/thumbnail/<path:filename>')
def serve_thumbnail(filename):
    """Servir thumbnails generados con manejo de caracteres especiales"""
    try:
        import urllib.parse
        # Decodificar URL para manejar caracteres especiales
        decoded_filename = urllib.parse.unquote(filename)
        thumbnail_path = config.THUMBNAILS_PATH / decoded_filename
        
        if thumbnail_path.exists():
            return send_file(thumbnail_path)
        else:
            # Si no existe, buscar archivos similares
            similar_files = list(config.THUMBNAILS_PATH.glob(f"*{Path(decoded_filename).stem}*"))
            if similar_files:
                return send_file(similar_files[0])
            abort(404)
    except Exception as e:
        logger.error(f"Error sirviendo thumbnail {filename}: {e}")
        abort(500)

@app.route('/api/videos')
def api_videos():
    """API endpoint para obtener videos (AJAX)"""
    try:
        # Obtener parámetros
        filters = {}
        for key in ['creator_name', 'platform', 'edit_status', 'processing_status', 'difficulty_level']:
            value = request.args.get(key)
            if value:
                filters[key] = value
        
        search_query = request.args.get('search')
        if search_query:
            filters['search'] = search_query
        
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        videos = db.get_videos(filters=filters, limit=limit, offset=offset)
        total_videos = db.count_videos(filters=filters)
        
        # Procesar para JSON
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
            
            # Preparar título apropiado para el frontend (mismo que en la galería)
            if video.get('platform') in ['tiktok', 'instagram'] and video.get('description'):
                # Para TikTok e Instagram: usar descripción como título si está disponible
                # Para Instagram: verificar que no sea solo el nombre del archivo
                if (video.get('platform') == 'instagram' and 
                    video.get('description') and 
                    video.get('description') != video.get('file_name', '').replace('.mp4', '')):
                    video['display_title'] = video['description']
                elif video.get('platform') == 'tiktok':
                    video['display_title'] = video['description']
                else:
                    video['display_title'] = video['file_name']
            else:
                video['display_title'] = video['file_name']
        
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

@app.route('/api/video/<int:video_id>')
def api_get_video(video_id):
    """API para obtener un video específico"""
    try:
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        # Procesar datos JSON
        if video.get('detected_characters'):
            try:
                import json
                video['detected_characters'] = json.loads(video['detected_characters'])
            except:
                video['detected_characters'] = []
        
        if video.get('final_characters'):
            try:
                import json
                video['final_characters'] = json.loads(video['final_characters'])
            except:
                video['final_characters'] = []
        else:
            video['final_characters'] = []
        
        # Preparar título apropiado para el frontend (mismo que en la galería)
        if video.get('platform') in ['tiktok', 'instagram'] and video.get('description'):
            # Para TikTok e Instagram: usar descripción como título si está disponible
            # Para Instagram: verificar que no sea solo el nombre del archivo
            if (video.get('platform') == 'instagram' and 
                video.get('description') and 
                video.get('description') != video.get('file_name', '').replace('.mp4', '')):
                video['display_title'] = video['description']
            elif video.get('platform') == 'tiktok':
                video['display_title'] = video['description']
            else:
                video['display_title'] = video['file_name']
        else:
            # Para otras plataformas: usar nombre del archivo
            video['display_title'] = video['file_name']
        
        return jsonify({
            'success': True,
            'video': video
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/video/<int:video_id>/play')
def api_play_video(video_id):
    """API para obtener información de reproducción del video"""
    try:
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

@app.route('/video-stream/<int:video_id>')
def stream_video(video_id):
    """Servir video para streaming (para reproducción en navegador)"""
    try:
        video = db.get_video(video_id)
        if not video:
            abort(404)
        
        video_path = Path(video['file_path'])
        if not video_path.exists():
            abort(404)
        
        # Servir archivo de video con soporte para streaming
        return send_file(
            video_path,
            as_attachment=False,
            mimetype='video/mp4'  # Ajustar según el tipo de archivo
        )
        
    except Exception as e:
        logger.error(f"Error streaming video {video_id}: {e}")
        abort(500)
@app.route('/api/video/<int:video_id>/update', methods=['POST'])
def api_update_video(video_id):
    """API para actualizar un video (edición inline mejorada)"""
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
                    import json
                    updates[field] = json.dumps(value)
                else:
                    updates[field] = value
            else:
                logger.warning(f"Campo no permitido ignorado: {field}")
        
        if not updates:
            logger.error(f"No valid fields to update for video {video_id}")
            return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
        
        # Actualizar timestamp
        from datetime import datetime
        updates['last_updated'] = datetime.now().isoformat()
        
        logger.info(f"Actualizando video {video_id} con campos: {list(updates.keys())}")
        
        # Actualizar en BD
        success = db.update_video(video_id, updates)
        
        if success:
            # Obtener video actualizado
            updated_video = db.get_video(video_id)
            
            if not updated_video:
                logger.error(f"Video {video_id} not found after update")
                return jsonify({'success': False, 'error': 'Video not found after update'}), 404
            
            # Procesar datos JSON para respuesta
            if updated_video.get('final_characters'):
                try:
                    import json
                    updated_video['final_characters'] = json.loads(updated_video['final_characters'])
                except:
                    updated_video['final_characters'] = []
            
            if updated_video.get('detected_characters'):
                try:
                    import json
                    updated_video['detected_characters'] = json.loads(updated_video['detected_characters'])
                except:
                    updated_video['detected_characters'] = []
            
            logger.info(f"Video {video_id} actualizado exitosamente")
            
            return jsonify({
                'success': True,
                'video': updated_video,
                'message': 'Video actualizado exitosamente',
                'updated_fields': list(updates.keys())
            })
        else:
            logger.error(f"Failed to update video {video_id} in database")
            return jsonify({'success': False, 'error': 'Failed to update video in database'}), 500
            
    except Exception as e:
        logger.error(f"Error actualizando video {video_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/video/<int:video_id>/open-folder', methods=['POST'])
def api_open_folder(video_id):
    """Abrir carpeta del video en el explorador"""
    try:
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        video_path = Path(video['file_path'])
        if not video_path.exists():
            return jsonify({'success': False, 'error': 'Video file not found'}), 404
        
        folder_path = video_path.parent
        
        # Abrir carpeta según el OS
        try:
            if os.name == 'nt':  # Windows
                os.startfile(str(folder_path))
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open', str(folder_path)] if sys.platform == 'darwin' else ['xdg-open', str(folder_path)])
            
            return jsonify({
                'success': True,
                'message': f'Carpeta abierta: {folder_path}'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'Cannot open folder: {e}'}), 500
            
    except Exception as e:
        logger.error(f"Error abriendo carpeta para video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """API para obtener estadísticas del sistema"""
    try:
        stats = db.get_stats()
        creators = db.get_unique_creators()
        music_tracks = db.get_unique_music()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'creators_count': len(creators),
            'music_tracks_count': len(music_tracks),
            'creators': creators[:10],  # Top 10
            'music_tracks': music_tracks[:10]  # Top 10
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search')
def api_search():
    """API de búsqueda inteligente"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': False, 'error': 'Query required'}), 400
        
        # Búsqueda simple en múltiples campos
        # En una implementación más avanzada, usar FTS (Full-Text Search)
        videos = db.get_videos()
        
        results = []
        query_lower = query.lower()
        
        for video in videos:
            # Buscar en múltiples campos
            searchable_text = ' '.join([
                video.get('creator_name', ''),
                video.get('file_name', ''),
                video.get('detected_music', '') or '',
                video.get('final_music', '') or '',
                video.get('detected_music_artist', '') or '',
                video.get('final_music_artist', '') or '',
                video.get('notes', '') or ''
            ]).lower()
            
            if query_lower in searchable_text:
                results.append(video)
        
        return jsonify({
            'success': True,
            'results': results[:20],  # Limitar resultados
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/video/<int:video_id>/delete', methods=['POST'])
def api_delete_video(video_id):
    """API para eliminar un video (soft delete)"""
    try:
        data = request.get_json() or {}
        deletion_reason = data.get('reason', 'Usuario')
        deleted_by = data.get('deleted_by', 'web_user')
        
        success = db.soft_delete_video(video_id, deleted_by, deletion_reason)
        
        if success:
            logger.info(f"Video {video_id} eliminado por {deleted_by}")
            return jsonify({
                'success': True,
                'message': 'Video eliminado exitosamente',
                'video_id': video_id
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Video no encontrado o ya estaba eliminado'
            }), 404
            
    except Exception as e:
        logger.error(f"Error eliminando video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/video/<int:video_id>/restore', methods=['POST'])
def api_restore_video(video_id):
    """API para restaurar un video eliminado"""
    try:
        success = db.restore_video(video_id)
        
        if success:
            logger.info(f"Video {video_id} restaurado")
            return jsonify({
                'success': True,
                'message': 'Video restaurado exitosamente',
                'video_id': video_id
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Video no encontrado o no estaba eliminado'
            }), 404
            
    except Exception as e:
        logger.error(f"Error restaurando video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/video/<int:video_id>/permanent-delete', methods=['POST'])
def api_permanent_delete_video(video_id):
    """API para eliminar permanentemente un video"""
    try:
        data = request.get_json() or {}
        confirmation = data.get('confirm', False)
        
        if not confirmation:
            return jsonify({
                'success': False,
                'error': 'Confirmación requerida para eliminación permanente'
            }), 400
        
        success = db.permanent_delete_video(video_id)
        
        if success:
            logger.warning(f"Video {video_id} ELIMINADO PERMANENTEMENTE")
            return jsonify({
                'success': True,
                'message': 'Video eliminado permanentemente',
                'video_id': video_id
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Video no encontrado'
            }), 404
            
    except Exception as e:
        logger.error(f"Error eliminando permanentemente video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/delete-bulk', methods=['POST'])
def api_bulk_delete_videos():
    """API para eliminar múltiples videos"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        video_ids = data.get('video_ids', [])
        deletion_reason = data.get('reason', 'Eliminación masiva')
        deleted_by = data.get('deleted_by', 'web_user')
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No video IDs provided'}), 400
        
        successful, failed = db.bulk_delete_videos(video_ids, deleted_by, deletion_reason)
        
        return jsonify({
            'success': True,
            'message': f'{successful} videos eliminados, {failed} fallidos',
            'successful': successful,
            'failed': failed,
            'total': len(video_ids)
        })
        
    except Exception as e:
        logger.error(f"Error en eliminación masiva: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/restore-bulk', methods=['POST'])
def api_bulk_restore_videos():
    """API para restaurar múltiples videos"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        video_ids = data.get('video_ids', [])
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No video IDs provided'}), 400
        
        successful, failed = db.bulk_restore_videos(video_ids)
        
        return jsonify({
            'success': True,
            'message': f'{successful} videos restaurados, {failed} fallidos',
            'successful': successful,
            'failed': failed,
            'total': len(video_ids)
        })
        
    except Exception as e:
        logger.error(f"Error en restauración masiva: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/bulk-update', methods=['POST'])
def api_bulk_update_videos():
    """API para actualizar múltiples videos (actualización masiva simple)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        video_ids = data.get('video_ids', [])
        updates = data.get('updates', {})
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No video IDs provided'}), 400
        
        if not updates:
            return jsonify({'success': False, 'error': 'No updates provided'}), 400
        
        # Preparar updates para batch
        video_updates = []
        for video_id in video_ids:
            video_updates.append({
                'video_id': video_id,
                'updates': updates
            })
        
        successful, failed = db.batch_update_videos(video_updates)
        
        return jsonify({
            'success': True,
            'message': f'{successful} videos actualizados, {failed} fallidos',
            'successful': successful,
            'failed': failed,
            'total': len(video_ids)
        })
        
    except Exception as e:
        logger.error(f"Error en actualización masiva: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/bulk-edit', methods=['POST'])
def api_bulk_edit_videos():
    """API para edición masiva avanzada de videos"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        video_ids = data.get('video_ids', [])
        updates = data.get('updates', {})
        options = data.get('options', {})
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No video IDs provided'}), 400
        
        # Validar campos permitidos
        allowed_fields = {
            'final_music', 'final_music_artist', 'final_characters', 
            'difficulty_level', 'edit_status', 'notes'
        }
        
        # Preparar updates con opciones de limpieza
        processed_updates = {}
        for field, value in updates.items():
            if field in allowed_fields and value is not None and value != '':
                if field == 'final_characters' and isinstance(value, list):
                    processed_updates[field] = value
                else:
                    processed_updates[field] = value
        
        # Aplicar opciones de limpieza
        if options.get('clear_music'):
            processed_updates['final_music'] = None
        if options.get('clear_artist'):
            processed_updates['final_music_artist'] = None
        if options.get('clear_characters'):
            processed_updates['final_characters'] = []
        if options.get('clear_notes'):
            processed_updates['notes'] = None
        
        # Aplicar revert analysis (limpiar información detectada automáticamente)
        if options.get('revert_analysis'):
            processed_updates.update({
                'detected_music': None,
                'detected_music_artist': None,
                'detected_music_confidence': None,
                'detected_characters': '[]',
                'music_source': None,
                'processing_status': 'pendiente'
            })
        
        if not processed_updates and not any(options.values()):
            return jsonify({'success': False, 'error': 'No changes to apply'}), 400
        
        # Si solo se va a reprocesar sin cambios de datos, no necesitamos actualizar la BD aún
        if not processed_updates and options.get('reprocess'):
            successful, failed = len(video_ids), 0
        else:
            # Preparar updates para batch
            video_updates = []
            for video_id in video_ids:
                video_updates.append({
                    'video_id': video_id,
                    'updates': processed_updates
                })
            
            successful, failed = db.batch_update_videos(video_updates)
        
        # Manejar opciones avanzadas
        additional_actions = []
        
        # Ejecutar reprocesamiento automático
        if options.get('reprocess'):
            try:
                # Ejecutar comando de reprocesamiento para todos los videos seleccionados
                cmd = [
                    sys.executable, 'main.py',
                    '--reanalyze-video', ','.join(map(str, video_ids)),
                    '--force'  # Forzar para asegurar que se actualicen los datos
                ]
                
                # Ejecutar comando
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                env['PYTHONUNBUFFERED'] = '1'
                
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=300,  # 5 minutos de timeout
                    env=env,
                    cwd=Path(__file__).parent
                )
                
                if result.returncode == 0:
                    additional_actions.append('reprocesamiento completado exitosamente')
                else:
                    additional_actions.append(f'reprocesamiento falló: {result.stderr}')
                    logger.error(f"Error en reprocesamiento: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                additional_actions.append('reprocesamiento timeout (proceso muy largo)')
                logger.error("Timeout en reprocesamiento masivo")
            except Exception as e:
                additional_actions.append(f'error en reprocesamiento: {str(e)}')
                logger.error(f"Error ejecutando reprocesamiento: {e}")
        
        if options.get('regenerate_thumbnails'):
            try:
                from src.maintenance_api import get_maintenance_api
                
                logger.info(f"🖼️ Regenerando thumbnails para {len(video_ids)} videos usando API asíncrona...")
                api = get_maintenance_api()
                operation_id = api.regenerate_thumbnails_bulk(video_ids, force=True)
                
                # Esperar brevemente para obtener estado inicial
                import time
                time.sleep(0.5)
                
                operation = api.get_operation_progress(operation_id)
                if operation:
                    additional_actions.append(f"regeneración iniciada: {operation_id[:8]}...")
                else:
                    additional_actions.append("regeneración iniciada (procesando en segundo plano)")
                    
            except Exception as e:
                # Fallback a método síncrono
                logger.warning(f"Error con API asíncrona, usando método síncrono: {e}")
                try:
                    from src.maintenance.thumbnail_ops import regenerate_thumbnails_by_ids
                    
                    result = regenerate_thumbnails_by_ids(video_ids, force=True)
                    
                    if result['success']:
                        additional_actions.append(f"thumbnails regenerados: {result['successful']}")
                        if result.get('duration'):
                            additional_actions.append(f"tiempo: {result['duration']:.2f}s")
                    else:
                        additional_actions.append(f"error regenerando thumbnails: {result.get('error', 'Unknown error')}")
                        
                except Exception as e2:
                    additional_actions.append(f'error regenerando thumbnails: {str(e2)}')
                    logger.error(f"Error regenerando thumbnails: {e2}")
        if options.get('revert_analysis'):
            additional_actions.append('información detectada revertida')
        
        message = f'{successful} videos editados, {failed} fallidos'
        if additional_actions:
            message += f'. Acciones adicionales: {", ".join(additional_actions)}'
        
        return jsonify({
            'success': True,
            'message': message,
            'successful': successful,
            'failed': failed,
            'total': len(video_ids),
            'additional_actions': additional_actions
        })
        
    except Exception as e:
        logger.error(f"Error en edición masiva: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/bulk-delete', methods=['POST'])
def api_bulk_delete_videos_alias():
    """Alias para compatibilidad con nomenclatura consistente"""
    return api_bulk_delete_videos()

# ===== API ENDPOINTS PARA REANÁLISIS DE VIDEOS =====

@app.route('/api/video/<int:video_id>/reanalyze', methods=['POST'])
def api_reanalyze_video(video_id):
    """API para reanalizar un video específico"""
    try:
        data = request.get_json() or {}
        force = data.get('force', False)  # Forzar reanálisis aunque ya esté procesado
        
        # Verificar que el video existe
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video no encontrado'}), 404
        
        # Verificar que el archivo existe
        video_path = Path(video['file_path'])
        if not video_path.exists():
            return jsonify({'success': False, 'error': 'Archivo de video no encontrado'}), 404
        
        # Marcar como procesando
        db.update_video(video_id, {
            'processing_status': 'procesando',
            'error_message': None
        })
        
        # Ejecutar reanálisis en background usando subprocess
        try:
            cmd = [
                sys.executable, 'main.py', 
                '--reanalyze-video', str(video_id)
            ]
            
            if force:
                cmd.append('--force')
            
            # Ejecutar comando de forma síncrona para garantizar resultado
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'  # Forzar UTF-8 para stdout/stderr
            env['PYTHONUNBUFFERED'] = '1'  # Asegurar output en tiempo real
            
            process = subprocess.run(
                cmd,
                cwd=str(Path(__file__).parent),
                capture_output=True,
                text=True,
                encoding='utf-8',  # Especificar UTF-8 para manejar caracteres Unicode
                env=env,  # Usar entorno modificado
                timeout=300  # 5 minutos máximo
            )
            
            logger.info(f"Ejecutado reanálisis del video {video_id} con código de salida: {process.returncode}")
            
            # Debug: Log stdout and stderr para diagnóstico
            if process.stdout:
                logger.info(f"STDOUT: {process.stdout}")
            if process.stderr:
                logger.warning(f"STDERR: {process.stderr}")
            
            if process.returncode == 0:
                return jsonify({
                    'success': True,
                    'message': f'Reanálisis completado exitosamente para video {video_id}',
                    'video_id': video_id
                })
            else:
                error_msg = process.stderr or 'Error desconocido en el reanálisis'
                logger.error(f"Error en reanálisis del video {video_id}: {error_msg}")
                
                # Marcar como error en BD
                db.update_video(video_id, {
                    'processing_status': 'error',
                    'error_message': error_msg
                })
                
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 500
            
        except Exception as e:
            # Revertir estado en caso de error
            db.update_video(video_id, {
                'processing_status': 'error',
                'error_message': f'Error iniciando reanálisis: {str(e)}'
            })
            raise e
            
    except Exception as e:
        logger.error(f"Error reanalizing video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/bulk-reanalyze', methods=['POST'])
def api_bulk_reanalyze_videos():
    """API para reanalizar múltiples videos usando una sola llamada al subprocess"""
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
        
        # Ejecutar reanálisis masivo en background usando subprocess
        try:
            cmd = [
                sys.executable, 'main.py', 
                '--reanalyze-video', ','.join(map(str, video_ids))
            ]
            
            if force:
                cmd.append('--force')
            
            # Ejecutar comando con encoding UTF-8
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUNBUFFERED'] = '1'
            
            process = subprocess.run(
                cmd,
                cwd=str(Path(__file__).parent),
                capture_output=True,
                text=True,
                encoding='utf-8',
                env=env,
                timeout=600  # 10 minutos máximo para procesos masivos
            )
            
            logger.info(f"Ejecutado reanálisis masivo de {len(video_ids)} videos con código de salida: {process.returncode}")
            
            # Debug: Log stdout and stderr
            if process.stdout:
                logger.info(f"STDOUT: {process.stdout}")
            if process.stderr:
                logger.warning(f"STDERR: {process.stderr}")
            
            if process.returncode == 0:
                return jsonify({
                    'success': True,
                    'message': f'Reanálisis masivo completado exitosamente para {len(video_ids)} videos',
                    'video_ids': video_ids,
                    'total_videos': len(video_ids)
                })
            else:
                error_msg = process.stderr or 'Error desconocido en el reanálisis masivo'
                logger.error(f"Error en reanálisis masivo: {error_msg}")
                
                # Marcar videos como error en BD
                for video_id in video_ids:
                    db.update_video(video_id, {
                        'processing_status': 'error',
                        'error_message': error_msg
                    })
                
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 500
            
        except subprocess.TimeoutExpired:
            error_msg = 'Timeout: El reanálisis masivo tomó demasiado tiempo'
            logger.error(f"Timeout en reanálisis masivo: {error_msg}")
            
            # Marcar videos como error
            for video_id in video_ids:
                db.update_video(video_id, {
                    'processing_status': 'error',
                    'error_message': error_msg
                })
            
            return jsonify({
                'success': False,
                'error': error_msg
            }), 504
            
        except Exception as e:
            # Revertir estado en caso de error
            for video_id in video_ids:
                db.update_video(video_id, {
                    'processing_status': 'error',
                    'error_message': f'Error iniciando reanálisis masivo: {str(e)}'
                })
            raise e
            
    except Exception as e:
        logger.error(f"Error en reanálisis masivo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/trash')
def trash():
    """Página de papelera de videos eliminados"""
    try:
        # Obtener filtros y paginación
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        # Obtener videos eliminados
        deleted_videos = db.get_deleted_videos(limit=per_page, offset=offset)
        total_deleted = db.count_deleted_videos()
        total_pages = (total_deleted + per_page - 1) // per_page
        
        # Procesar videos para el template
        for video in deleted_videos:
            # Parsear JSON de personajes
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
            
            # URL del thumbnail
            if video.get('thumbnail_path'):
                video['thumbnail_url'] = f"/thumbnail/{Path(video['thumbnail_path']).name}"
            else:
                video['thumbnail_url'] = "/static/img/no-thumbnail.svg"
        
        return render_template('trash.html',
                             videos=deleted_videos,
                             page=page,
                             per_page=per_page,
                             total_pages=total_pages,
                             total_deleted=total_deleted)
        
    except Exception as e:
        logger.error(f"Error en página de papelera: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/trash/stats')
def api_trash_stats():
    """API para obtener estadísticas de papelera"""
    try:
        total_deleted = db.count_deleted_videos()
        
        return jsonify({
            'success': True,
            'total_deleted': total_deleted
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de papelera: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin')
def admin_dashboard():
    """Dashboard administrativo"""
    try:
        return render_template('admin.html')
    except Exception as e:
        logger.error(f"Error en dashboard admin: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/admin/populate-db', methods=['POST'])
def api_admin_populate_db():
    """API para poblar base de datos desde dashboard"""
    try:
        data = request.get_json() or {}
        source = data.get('source', 'all')
        platform = data.get('platform')
        limit = data.get('limit', 50)
        force = data.get('force', False)
        file_path = data.get('file')
        
        # Ejecutar comando maintenance.py populate-db
        import subprocess
        import sys
        
        # Manejar archivo específico
        if file_path:
            cmd = [
                sys.executable, 'maintenance.py', 'populate-db',
                '--file', str(file_path)
            ]
            
            # Agregar --force si se especifica
            if force:
                cmd.append('--force')
                
        else:
            # Comando normal con source
            cmd = [
                sys.executable, 'maintenance.py', 'populate-db',
                '--source', str(source),
                '--limit', str(limit)
            ]
            
            # Agregar parámetro platform si se especifica
            if platform:
                cmd.extend(['--platform', str(platform)])
                
            # Agregar --force si se especifica
            if force:
                cmd.append('--force')
        
        logger.info(f"Ejecutando comando: {' '.join(cmd)}")
        logger.info(f"Directorio de trabajo: {Path(__file__).parent}")
        
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutos timeout
            env=os.environ.copy()  # Heredar variables de entorno
        )
        
        # Procesar salida para el terminal del frontend
        terminal_output = []
        
        # Agregar STDOUT línea por línea
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    terminal_output.append(line.strip())
        
        # Agregar STDERR línea por línea (típicamente contiene los logs INFO)
        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                if line.strip():
                    terminal_output.append(line.strip())
        
        # Log básico para debug del servidor
        logger.info(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            message = 'Archivo importado exitosamente' if file_path else 'Poblado completado exitosamente'
            response_data = {
                'success': True,
                'message': message,
                'terminal_output': terminal_output,  # Líneas para mostrar en terminal
                'force': force
            }
            
            if file_path:
                response_data['file'] = file_path
            else:
                response_data.update({
                    'source': source,
                    'platform': platform,
                    'limit': limit
                })
                
            return jsonify(response_data)
        else:
            logger.error(f"Comando falló con código {result.returncode}")
            
            # En caso de error, también enviar la salida al terminal
            error_output = []
            if result.stderr:
                error_output.extend(result.stderr.strip().split('\n'))
            if result.stdout:
                error_output.extend(result.stdout.strip().split('\n'))
                
            return jsonify({
                'success': False,
                'error': f'Error ejecutando comando: Código de salida {result.returncode}',
                'terminal_output': error_output
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Comando expiró (timeout de 5 minutos)'
        }), 500
    except Exception as e:
        logger.error(f"Error en populate-db: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/analyze-videos', methods=['POST'])
def api_admin_analyze_videos():
    """API para analizar videos desde dashboard con opciones modernas"""
    try:
        data = request.get_json() or {}
        source = data.get('source', 'all')
        platform = data.get('platform')
        limit = data.get('limit')
        force = data.get('force', False)
        
        # Construir comando main.py
        import subprocess
        import sys
        
        cmd = [sys.executable, 'main.py']
        
        if limit:
            cmd.extend(['--limit', str(limit)])
        
        if source != 'all':
            cmd.extend(['--source', source])
        
        if platform:
            cmd.extend(['--platform', platform])
        
        if force:
            cmd.append('--force')
        
        logger.info(f"Ejecutando análisis: {' '.join(cmd)}")
        
        # Ejecutar comando con encoding UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUNBUFFERED'] = '1'
        
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            encoding='utf-8',
            env=env,
            timeout=600  # 10 minutos timeout
        )
        
        logger.info(f"Análisis completado con código de salida: {result.returncode}")
        
        # Debug: Log stdout and stderr
        if result.stdout:
            logger.info(f"STDOUT: {result.stdout}")
        if result.stderr:
            logger.warning(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Análisis completado exitosamente',
                'output': result.stdout,
                'processed': limit or 'sin límite'
            })
        else:
            error_msg = result.stderr or 'Error desconocido en análisis'
            return jsonify({
                'success': False,
                'error': f'Error en análisis: {error_msg}',
                'output': result.stdout
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Análisis expiró (timeout de 10 minutos)'
        }), 500
    except Exception as e:
        logger.error(f"Error en analyze-videos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/generate-thumbnails', methods=['POST'])
def api_admin_generate_thumbnails():
    """API para generar thumbnails desde dashboard"""
    try:
        data = request.get_json() or {}
        platform = data.get('platform')
        limit = data.get('limit', 20)
        
        # Ejecutar comando maintenance.py populate-thumbnails
        import subprocess
        import sys
        
        cmd = [sys.executable, 'maintenance.py', 'populate-thumbnails']
        
        if platform:
            cmd.extend(['--platform', platform])
        
        cmd.extend(['--limit', str(limit)])
        
        logger.info(f"Generando thumbnails: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': f'Thumbnails generados exitosamente',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Error generando thumbnails: {result.stderr}',
                'output': result.stdout
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Generación expiró (timeout de 5 minutos)'
        }), 500
    except Exception as e:
        logger.error(f"Error en generate-thumbnails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/backup', methods=['POST'])
def api_admin_backup():
    """API para crear backup del sistema"""
    try:
        import subprocess
        import sys
        
        cmd = [sys.executable, 'maintenance.py', 'backup']
        
        logger.info("Creando backup del sistema")
        
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=120  # 2 minutos timeout
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Backup creado exitosamente',
                'backup_path': 'backup creado',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Error creando backup: {result.stderr}',
                'output': result.stdout
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Backup expiró (timeout de 2 minutos)'
        }), 500
    except Exception as e:
        logger.error(f"Error en backup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/optimize-db', methods=['POST'])
def api_admin_optimize_db():
    """API para optimizar base de datos"""
    try:
        import subprocess
        import sys
        
        cmd = [sys.executable, 'maintenance.py', 'optimize-db']
        
        logger.info("Optimizando base de datos")
        
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=120  # 2 minutos timeout
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Base de datos optimizada exitosamente',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Error optimizando BD: {result.stderr}',
                'output': result.stdout
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Optimización expiró (timeout de 2 minutos)'
        }), 500
    except Exception as e:
        logger.error(f"Error en optimize-db: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# 🚀 NUEVOS ENDPOINTS PARA MAINTENANCE API (FASE 2)

@app.route('/api/maintenance/operations', methods=['GET'])
def api_maintenance_operations():
    """Obtener todas las operaciones de mantenimiento"""
    try:
        from src.maintenance_api import get_maintenance_api
        
        api = get_maintenance_api()
        operations = api.get_all_operations()
        
        return jsonify({
            'success': True,
            'operations': operations,
            'total': len(operations)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo operaciones: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/operation/<operation_id>', methods=['GET'])
def api_maintenance_operation_status(operation_id):
    """Obtener estado de una operación específica"""
    try:
        from src.maintenance_api import get_maintenance_api
        
        api = get_maintenance_api()
        operation = api.get_operation_progress(operation_id)
        
        if operation:
            return jsonify({
                'success': True,
                'operation': operation
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Operación no encontrada'
            }), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo estado de operación: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/operation/<operation_id>/cancel', methods=['POST'])
def api_maintenance_cancel_operation(operation_id):
    """Cancelar una operación específica"""
    try:
        from src.maintenance_api import get_maintenance_api
        
        api = get_maintenance_api()
        cancelled = api.cancel_operation(operation_id)
        
        if cancelled:
            return jsonify({
                'success': True,
                'message': 'Operación cancelada exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo cancelar la operación'
            }), 400
            
    except Exception as e:
        logger.error(f"Error cancelando operación: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/thumbnails/regenerate', methods=['POST'])
def api_maintenance_regenerate_thumbnails():
    """Iniciar regeneración asíncrona de thumbnails"""
    try:
        from src.maintenance_api import get_maintenance_api
        
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        force = data.get('force', False)
        
        if not video_ids:
            return jsonify({
                'success': False,
                'error': 'Se requieren video_ids'
            }), 400
        
        api = get_maintenance_api()
        operation_id = api.regenerate_thumbnails_bulk(video_ids, force)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': f'Regeneración iniciada para {len(video_ids)} videos'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando regeneración: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/thumbnails/populate', methods=['POST'])
def api_maintenance_populate_thumbnails():
    """Iniciar población asíncrona de thumbnails"""
    try:
        from src.maintenance_api import get_maintenance_api
        
        data = request.get_json() or {}
        platform = data.get('platform')
        limit = data.get('limit')
        force = data.get('force', False)
        
        api = get_maintenance_api()
        operation_id = api.populate_thumbnails_bulk(platform, limit, force)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': f'Población iniciada para {platform or "todas las plataformas"}'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando población: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/thumbnails/clean', methods=['POST'])
def api_maintenance_clean_thumbnails():
    """Iniciar limpieza asíncrona de thumbnails"""
    try:
        from src.maintenance_api import get_maintenance_api
        
        data = request.get_json() or {}
        force = data.get('force', False)
        
        api = get_maintenance_api()
        operation_id = api.clean_thumbnails_bulk(force)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': 'Limpieza de thumbnails iniciada'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando limpieza: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/system/health', methods=['GET'])
def api_maintenance_system_health():
    """Obtener salud del sistema"""
    try:
        from src.maintenance_api import get_maintenance_api
        
        api = get_maintenance_api()
        health = api.get_system_health()
        
        return jsonify({
            'success': True,
            'health': health
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo salud del sistema: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/operations/cleanup', methods=['POST'])
def api_maintenance_cleanup_operations():
    """Limpiar operaciones completadas antiguas"""
    try:
        from src.maintenance_api import get_maintenance_api
        
        data = request.get_json() or {}
        max_age_hours = data.get('max_age_hours', 24)
        
        api = get_maintenance_api()
        cleaned = api.cleanup_completed_operations(max_age_hours)
        
        return jsonify({
            'success': True,
            'cleaned_operations': cleaned,
            'message': f'Limpiadas {cleaned} operaciones antiguas'
        })
        
    except Exception as e:
        logger.error(f"Error limpiando operaciones: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 🗃️ NUEVOS ENDPOINTS PARA DATABASE OPERATIONS (FASE 3)

@app.route('/api/maintenance/database/populate', methods=['POST'])
def api_maintenance_populate_database():
    """Iniciar población asíncrona de base de datos"""
    try:
        from src.maintenance_api import get_maintenance_api
        
        data = request.get_json() or {}
        source = data.get('source', 'all')
        platform = data.get('platform')
        limit = data.get('limit')
        force = data.get('force', False)
        
        api = get_maintenance_api()
        operation_id = api.populate_database_bulk(source, platform, limit, force)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': f'Población de BD iniciada desde {source}'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando población de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/database/optimize', methods=['POST'])
def api_maintenance_optimize_database():
    """Iniciar optimización asíncrona de base de datos"""
    try:
        from src.maintenance_api import get_maintenance_api
        
        api = get_maintenance_api()
        operation_id = api.optimize_database_bulk()
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': 'Optimización de BD iniciada'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando optimización de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/database/clear', methods=['POST'])
def api_maintenance_clear_database():
    """Iniciar limpieza asíncrona de base de datos"""
    try:
        from src.maintenance_api import get_maintenance_api
        
        data = request.get_json() or {}
        platform = data.get('platform')
        force = data.get('force', False)
        
        api = get_maintenance_api()
        operation_id = api.clear_database_bulk(platform, force)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': f'Limpieza de BD iniciada para {platform or "todas las plataformas"}'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando limpieza de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/database/backup', methods=['POST'])
def api_maintenance_backup_database():
    """Iniciar backup asíncrono de base de datos"""
    try:
        from src.maintenance_api import get_maintenance_api
        
        data = request.get_json() or {}
        backup_path = data.get('backup_path')
        
        api = get_maintenance_api()
        operation_id = api.backup_database_bulk(backup_path)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': 'Backup de BD iniciado'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando backup de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/database/stats', methods=['GET'])
def api_maintenance_database_stats():
    """Obtener estadísticas detalladas de la base de datos"""
    try:
        from src.maintenance.database_ops import get_database_stats
        
        stats = get_database_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/maintenance-monitor')
def maintenance_monitor():
    """Página del monitor de operaciones de mantenimiento"""
    return render_template('maintenance_monitor.html')

@app.route('/api/admin/verify', methods=['POST'])
def api_admin_verify():
    """API para verificar sistema"""
    try:
        import subprocess
        import sys
        
        cmd = [sys.executable, 'maintenance.py', 'verify']
        
        logger.info("Verificando sistema")
        
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=60  # 1 minuto timeout
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Sistema verificado correctamente',
                'output': result.stdout
            })
        else:
            # Verificación puede devolver advertencias sin error
            return jsonify({
                'success': True,
                'message': 'Verificación completada con advertencias',
                'warnings': result.stderr,
                'output': result.stdout
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Verificación expiró (timeout de 1 minuto)'
        }), 500
    except Exception as e:
        logger.error(f"Error en verify: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/empty-trash', methods=['POST'])
def api_admin_empty_trash():
    """API para vaciar papelera (eliminación permanente)"""
    try:
        # Obtener todos los videos eliminados
        deleted_videos = db.get_deleted_videos()
        
        if not deleted_videos:
            return jsonify({
                'success': True,
                'message': 'La papelera ya está vacía',
                'deleted_count': 0
            })
        
        # Eliminar permanentemente cada video
        deleted_count = 0
        for video in deleted_videos:
            success = db.permanent_delete_video(video['id'])
            if success:
                deleted_count += 1
        
        logger.warning(f"Papelera vaciada: {deleted_count} videos eliminados permanentemente")
        
        return jsonify({
            'success': True,
            'message': f'Papelera vaciada exitosamente',
            'deleted_count': deleted_count,
            'total_found': len(deleted_videos)
        })
        
    except Exception as e:
        logger.error(f"Error vaciando papelera: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/reset-database', methods=['POST'])
def api_admin_reset_database():
    """API para reset completo de base de datos"""
    try:
        # Construir comando
        command = ['python', 'maintenance.py', 'clear-db', '--force']
        
        logger.warning("🔥 INICIANDO RESET COMPLETO DE BASE DE DATOS")
        logger.warning(f"Comando: {' '.join(command)}")
        
        # Ejecutar comando con timeout de 2 minutos
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutos
            cwd=str(Path(__file__).parent)
        )
        
        # Procesar salida para el terminal
        terminal_output = []
        if result.stdout:
            terminal_output.extend(result.stdout.strip().split('\n'))
        if result.stderr:
            terminal_output.extend(result.stderr.strip().split('\n'))
        
        if result.returncode == 0:
            logger.warning("💀 RESET DE BASE DE DATOS COMPLETADO")
            return jsonify({
                'success': True,
                'message': 'Base de datos reseteada completamente',
                'terminal_output': terminal_output
            })
        else:
            logger.error(f"Error en reset de BD: {result.stderr}")
            return jsonify({
                'success': False,
                'error': result.stderr or 'Error desconocido en reset',
                'terminal_output': terminal_output
            }), 500
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout en reset de BD")
        return jsonify({
            'success': False,
            'error': 'Reset expiró (timeout de 2 minutos)'
        }), 500
    except Exception as e:
        logger.error(f"Error en reset de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/platforms', methods=['GET'])
def api_admin_platforms():
    """API para obtener plataformas disponibles"""
    try:
        from src.external_sources import ExternalSourcesManager
        
        external_sources = ExternalSourcesManager()
        platforms = external_sources.get_available_platforms()
        
        # Formatear las plataformas para el frontend
        formatted_platforms = {
            'main': {},
            'additional': {}
        }
        
        # Plataformas principales
        for platform_key, platform_info in platforms.get('main', {}).items():
            formatted_platforms['main'][platform_key] = {
                'name': platform_key.title(),
                'has_db': platform_info.get('has_db', False),
                'has_organized': platform_info.get('has_organized', False)
            }
        
        # Plataformas adicionales (autodetectadas)
        for platform_key, platform_info in platforms.get('additional', {}).items():
            formatted_platforms['additional'][platform_key] = {
                'name': platform_info.get('folder_name', platform_key.title()),
                'has_db': False,
                'has_organized': True
            }
        
        return jsonify({
            'success': True,
            'platforms': formatted_platforms
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo plataformas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Página de error 404"""
    return render_template('error.html', 
                         error="Página no encontrada",
                         error_code=404), 404

@app.errorhandler(500)
def internal_error(error):
    """Página de error 500"""
    return render_template('error.html',
                         error="Error interno del servidor",
                         error_code=500), 500

def main():
    """Función principal para ejecutar la aplicación"""
    logger.info("=== INICIANDO TAG-FLOW V2 WEB APP ===")
    logger.info(f"Modo: {config.FLASK_ENV}")
    logger.info(f"Base de datos: {config.DATABASE_PATH}")
    logger.info(f"Thumbnails: {config.THUMBNAILS_PATH}")
    
    # Mostrar estadísticas al inicio
    try:
        stats = db.get_stats()
        logger.info(f"Videos en base de datos: {stats['total_videos']}")
    except Exception as e:
        logger.warning(f"Error obteniendo estadísticas iniciales: {e}")
    
    # Ejecutar aplicación
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )

if __name__ == '__main__':
    main()