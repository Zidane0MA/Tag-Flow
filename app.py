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
        if request.args.get('difficulty'):
            filters['difficulty_level'] = request.args.get('difficulty')
        
        # Paginación
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        # Obtener videos
        videos = db.get_videos(filters=filters, limit=per_page, offset=offset)
        
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
        
        return render_template('gallery.html',
                             videos=videos,
                             creators=creators,
                             music_tracks=music_tracks,
                             stats=stats,
                             current_filters=filters,
                             page=page,
                             per_page=per_page)
        
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
        
        return render_template('video_detail.html', video=video)
        
    except Exception as e:
        logger.error(f"Error mostrando video {video_id}: {e}")
        abort(500)

@app.route('/thumbnail/<filename>')
def serve_thumbnail(filename):
    """Servir thumbnails generados"""
    try:
        thumbnail_path = config.THUMBNAILS_PATH / filename
        if thumbnail_path.exists():
            return send_file(thumbnail_path)
        else:
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
        for key in ['creator_name', 'platform', 'edit_status', 'difficulty_level']:
            value = request.args.get(key)
            if value:
                filters[key] = value
        
        search_query = request.args.get('search')
        if search_query:
            # Implementar búsqueda por texto (simplificada)
            filters['search'] = search_query
        
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        videos = db.get_videos(filters=filters, limit=limit, offset=offset)
        
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
        
        return jsonify({
            'success': True,
            'videos': videos,
            'total': len(videos)
        })
        
    except Exception as e:
        logger.error(f"Error en API videos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/video/<int:video_id>/update', methods=['POST'])
def api_update_video(video_id):
    """API para actualizar un video (edición inline)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validar campos permitidos
        allowed_fields = {
            'final_music', 'final_music_artist', 'final_characters', 
            'difficulty_level', 'edit_status', 'notes'
        }
        
        updates = {}
        for field, value in data.items():
            if field in allowed_fields:
                updates[field] = value
        
        if not updates:
            return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
        
        # Actualizar en BD
        success = db.update_video(video_id, updates)
        
        if success:
            # Obtener video actualizado
            updated_video = db.get_video(video_id)
            return jsonify({
                'success': True,
                'video': updated_video,
                'message': 'Video actualizado exitosamente'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update video'}), 500
            
    except Exception as e:
        logger.error(f"Error actualizando video {video_id}: {e}")
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