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
        
        if not processed_updates and not any(options.values()):
            return jsonify({'success': False, 'error': 'No changes to apply'}), 400
        
        # Preparar updates para batch
        video_updates = []
        for video_id in video_ids:
            video_updates.append({
                'video_id': video_id,
                'updates': processed_updates
            })
        
        successful, failed = db.batch_update_videos(video_updates)
        
        # Manejar opciones avanzadas (placeholder para futuras funcionalidades)
        additional_actions = []
        if options.get('reprocess'):
            additional_actions.append('reprocesar (pendiente de implementar)')
        if options.get('regenerate_thumbnails'):
            additional_actions.append('regenerar thumbnails (pendiente de implementar)')
        
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
                'python', 'main.py', 
                '--reanalyze-video', str(video_id),
                '--limit', '1'
            ]
            
            if force:
                cmd.append('--force')
            
            # Ejecutar comando de forma asíncrona
            process = subprocess.Popen(
                cmd,
                cwd=str(Path(__file__).parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.info(f"Iniciado reanálisis del video {video_id} con PID {process.pid}")
            
            return jsonify({
                'success': True,
                'message': f'Reanálisis iniciado para video {video_id}',
                'video_id': video_id,
                'process_id': process.pid
            })
            
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
        limit = data.get('limit', 50)
        
        # Ejecutar comando maintenance.py populate-db
        import subprocess
        import sys
        
        cmd = [
            sys.executable, 'maintenance.py', 'populate-db',
            '--source', str(source),
            '--limit', str(limit)
        ]
        
        logger.info(f"Ejecutando comando: {' '.join(cmd)}")
        
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
                'message': f'Poblado completado exitosamente',
                'output': result.stdout,
                'source': source,
                'limit': limit
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Error ejecutando comando: {result.stderr}',
                'output': result.stdout
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
    """API para analizar videos desde dashboard"""
    try:
        data = request.get_json() or {}
        platform = data.get('platform')
        limit = data.get('limit', 10)
        pending_only = data.get('pending_only', True)
        
        # Construir comando main.py
        import subprocess
        import sys
        
        cmd = [sys.executable, 'main.py', '--limit', str(limit)]
        
        if platform:
            cmd.extend(['--platform', platform])
        
        if pending_only:
            cmd.extend(['--source', 'db'])
        
        logger.info(f"Ejecutando análisis: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos timeout
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Análisis completado exitosamente',
                'output': result.stdout,
                'processed': limit  # Aproximado
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Error en análisis: {result.stderr}',
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