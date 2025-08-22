"""
Tag-Flow V2 - Gallery Blueprint
Rutas para vistas principales: galería, detalle de video, trash
"""

import json
from pathlib import Path
from flask import Blueprint, render_template, request, abort
import logging

# Database will be imported lazily within functions

logger = logging.getLogger(__name__)

gallery_bp = Blueprint('gallery', __name__)

@gallery_bp.route('/')
def index():
    """Página principal - galería de videos"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
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
                video['thumbnail_url'] = "/static/img/no-thumbnail.svg"
            
            # Preparar título apropiado para el frontend
            if video.get('platform') in ['tiktok', 'instagram'] and video.get('title'):
                # Para TikTok e Instagram: usar título si está disponible
                # Para Instagram: verificar que no sea solo el nombre del archivo
                if (video.get('platform') == 'instagram' and 
                    video.get('title') and 
                    video.get('title') != video.get('file_name', '').replace('.mp4', '')):
                    video['display_title'] = video['title']
                elif video.get('platform') == 'tiktok':
                    video['display_title'] = video['title']
                else:
                    video['display_title'] = video.get('title', video.get('file_name', 'Sin título'))
            else:
                video['display_title'] = video.get('title', video.get('file_name', 'Sin título'))
        
        return render_template('gallery.html', 
                             videos=videos,
                             creators=creators,
                             music_tracks=music_tracks,
                             stats=stats,
                             page=page,
                             current_page=page,
                             total_pages=total_pages,
                             total_videos=total_videos,
                             per_page=per_page,
                             filters=request.args)
    
    except Exception as e:
        logger.error(f"Error en galería: {e}")
        return render_template('error.html', 
                             error="Error al cargar la galería",
                             details=str(e)), 500

@gallery_bp.route('/video/<int:video_id>')
def video_detail(video_id):
    """Página de detalle de un video específico"""
    try:
        from src.service_factory import get_database
        db = get_database()
        video = db.get_video_by_id(video_id)
        if not video:
            abort(404)
        
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
            video['thumbnail_url'] = "/static/img/no-thumbnail.svg"
        
        return render_template('video_detail.html', video=video)
    
    except Exception as e:
        logger.error(f"Error en detalle de video {video_id}: {e}")
        return render_template('error.html', 
                             error=f"Error al cargar el video {video_id}",
                             details=str(e)), 500

@gallery_bp.route('/trash')
def trash():
    """Página de videos eliminados"""
    try:
        # Obtener filtros específicos para trash
        filters = {}
        if request.args.get('creator'):
            filters['creator_name'] = request.args.get('creator')
        if request.args.get('platform'):
            filters['platform'] = request.args.get('platform')
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        # Paginación
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        from src.service_factory import get_database
        db = get_database()
        
        # Obtener solo videos eliminados - necesitamos filtrar manualmente
        # Por ahora obtenemos todos con include_deleted=True y luego filtramos
        all_videos = db.get_videos(filters=filters, include_deleted=True)
        deleted_videos = [v for v in all_videos if v.get('deleted_at') is not None]
        
        # Aplicar paginación manual
        total_videos = len(deleted_videos)
        videos = deleted_videos[offset:offset + per_page]
        total_pages = (total_videos + per_page - 1) // per_page
        
        # Procesar videos para el template (mismo procesamiento que galería)
        for video in videos:
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
            
            if video.get('thumbnail_path'):
                video['thumbnail_url'] = f"/thumbnail/{Path(video['thumbnail_path']).name}"
            else:
                video['thumbnail_url'] = "/static/img/no-thumbnail.svg"
        
        return render_template('trash.html', 
                             videos=videos,
                             page=page,
                             current_page=page,
                             total_pages=total_pages,
                             total_videos=total_videos,
                             total_deleted=total_videos,
                             per_page=per_page,
                             filters=request.args)
    
    except Exception as e:
        logger.error(f"Error en página de papelera: {e}")
        return render_template('error.html', 
                             error="Error al cargar la papelera",
                             details=str(e)), 500