"""
Tag-Flow V2 - Aplicación Flask Refactorizada
Interfaz web moderna con arquitectura de blueprints
"""

import sys
from pathlib import Path
import logging
from flask import Flask, send_file, abort, render_template, jsonify
from flask_cors import CORS

# Agregar src al path
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config
# Database will be imported lazily within functions
from src.api import gallery_bp, videos_core_bp, videos_streaming_bp, videos_bulk_bp, stats_bp, admin_bp, maintenance_bp, creators_bp, cursor_pagination_bp
from src.api.performance import performance_bp
from src.api.websocket_api import websocket_bp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Factory function para crear la aplicación Flask"""
    
    # Crear aplicación Flask
    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app)
    
    # Asegurar que los directorios existen
    config.ensure_directories()

    # Aplicar migraciones y optimizaciones de base de datos automáticamente
    try:
        from src.database.migrations import ensure_database_optimized
        db_path = str(config.DATABASE_PATH)
        if ensure_database_optimized(db_path):
            logger.info("✅ Base de datos optimizada automáticamente al iniciar")
        else:
            logger.warning("⚠️ Algunas optimizaciones de BD no se pudieron aplicar")
    except Exception as e:
        logger.error(f"❌ Error aplicando optimizaciones de BD: {e}")

    # Registrar blueprints
    app.register_blueprint(gallery_bp)
    app.register_blueprint(videos_core_bp)
    app.register_blueprint(videos_streaming_bp)
    app.register_blueprint(videos_bulk_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(creators_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(cursor_pagination_bp)  # ⚡ NEW - Cursor pagination endpoints
    app.register_blueprint(websocket_bp)  # 🔗 WebSocket real-time updates
    
    # Rutas estáticas y archivos
    @app.route('/thumbnail/<path:filename>')
    def serve_thumbnail(filename):
        """Servir thumbnails generados"""
        try:
            # Limpiar filename para evitar path traversal y problemas de encoding
            import os
            clean_filename = os.path.basename(filename)
            
            # Si el filename está vacío o es solo una carpeta, usar thumbnail por defecto
            if not clean_filename or clean_filename.endswith('/') or clean_filename.endswith('\\') or clean_filename.strip() == '':
                logger.warning(f"Filename inválido o vacío: '{filename}' -> '{clean_filename}'")
                return send_file(config.STATIC_DIR / 'img' / 'no-thumbnail.svg')
            
            thumbnail_path = config.DATA_DIR / 'thumbnails' / clean_filename
            
            if thumbnail_path.exists() and thumbnail_path.is_file():
                return send_file(thumbnail_path)
            else:
                logger.warning(f"Thumbnail no encontrado: {thumbnail_path}")
                
                # 🎠 FALLBACK: Verificar si es un carrusel de imágenes y servir la primera imagen
                try:
                    from src.service_factory import get_database
                    from pathlib import Path
                    
                    # Extraer nombre base del archivo (remover _thumb.jpg)
                    if clean_filename.endswith('_thumb.jpg'):
                        base_filename = clean_filename[:-10]  # Remover '_thumb.jpg'
                        
                        # Buscar video por file_name usando nuevo esquema
                        db = get_database()
                        with db.get_connection() as conn:
                            cursor = conn.execute('''
                                SELECT m.id, m.file_path, p.is_carousel, p.carousel_count
                                FROM media m
                                JOIN posts p ON m.post_id = p.id
                                WHERE m.file_name = ? OR m.file_path LIKE ?
                                AND p.deleted_at IS NULL
                            ''', (base_filename, f'%{base_filename}%'))

                            video_row = cursor.fetchone()
                            if video_row:
                                video_id, file_path, is_carousel, carousel_count = video_row

                                # Si es parte de un carrusel, usar el archivo encontrado directamente
                                if is_carousel and carousel_count > 1:
                                    # Para carruseles, buscar la primera imagen del mismo post
                                    cursor = conn.execute('''
                                        SELECT m.file_path
                                        FROM media m
                                        JOIN posts p ON m.post_id = p.id
                                        WHERE p.id = (SELECT p2.id FROM media m2 JOIN posts p2 ON m2.post_id = p2.id WHERE m2.id = ?)
                                        AND m.media_type = 'image'
                                        ORDER BY m.carousel_order ASC
                                        LIMIT 1
                                    ''', (video_id,))

                                    first_image_row = cursor.fetchone()
                                    if first_image_row:
                                        first_image_path = Path(first_image_row[0])
                                        # Verificar si es imagen y existe
                                        if (first_image_path.exists() and
                                            any(first_image_path.suffix.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])):
                                            logger.info(f"🖼️ CAROUSEL FALLBACK - Serving first image: {first_image_path}")
                                            return send_file(first_image_path)
                                
                                # Si es imagen individual, servirla directamente  
                                elif file_path:
                                    image_path = Path(file_path)
                                    if (image_path.exists() and 
                                        any(image_path.suffix.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])):
                                        logger.info(f"🖼️ IMAGE FALLBACK - Serving original image: {image_path}")
                                        return send_file(image_path)
                
                except Exception as e:
                    logger.warning(f"Error en fallback de carrusel para {clean_filename}: {e}")
                
                # Thumbnail por defecto si no se puede resolver
                return send_file(config.STATIC_DIR / 'img' / 'no-thumbnail.svg')
        except Exception as e:
            logger.error(f"Error sirviendo thumbnail {filename}: {e}")
            # En caso de error, devolver thumbnail por defecto en lugar de 404
            return send_file(config.STATIC_DIR / 'img' / 'no-thumbnail.svg')
    
    @app.route('/video-stream/<int:video_id>')
    def stream_video(video_id):
        """Servir video/imagen para streaming (para reproducción en navegador)"""
        try:
            from src.service_factory import get_database
            db = get_database()

            # Consultar usando el nuevo esquema (media table)
            with db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT m.file_path, m.file_name
                    FROM media m
                    JOIN posts p ON m.post_id = p.id
                    WHERE m.id = ? AND p.deleted_at IS NULL
                """, (video_id,))

                row = cursor.fetchone()
                if not row:
                    abort(404)

                file_path, file_name = row

            video_path = Path(file_path)
            if not video_path.exists():
                abort(404)
            
            # Detectar MIME type basándose en la extensión del archivo
            file_extension = video_path.suffix.lower()
            
            # Mapear extensiones a MIME types
            mime_types = {
                # Videos
                '.mp4': 'video/mp4',
                '.avi': 'video/avi',
                '.mov': 'video/quicktime',
                '.mkv': 'video/x-matroska',
                '.webm': 'video/webm',
                '.flv': 'video/x-flv',
                # Imágenes
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.webp': 'image/webp'
            }
            
            mimetype = mime_types.get(file_extension, 'application/octet-stream')
            
            # Servir archivo con el MIME type correcto
            return send_file(
                video_path,
                as_attachment=False,
                mimetype=mimetype
            )
            
        except Exception as e:
            logger.error(f"Error streaming media {video_id}: {e}")
            abort(500)
    
    # Manejadores de errores - JSON responses para API
    @app.errorhandler(404)
    def not_found_error(error):
        """Respuesta 404 personalizada"""
        return jsonify({
            'success': False,
            'error': 'Página no encontrada',
            'details': 'La página que buscas no existe.'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Respuesta 500 personalizada"""
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor',
            'details': 'Ha ocurrido un error inesperado.'
        }), 500
    
    # Context processors para templates
    @app.context_processor
    def inject_config():
        """Inyectar configuración en templates"""
        return {
            'config': config,
            'app_name': 'Tag-Flow V2',
            'version': '2.0.0'
        }
    
    @app.context_processor
    def inject_stats():
        """Inyectar estadísticas básicas en templates"""
        try:
            from src.service_factory import get_database
            db = get_database()
            stats = db.get_stats()
            return {'global_stats': stats}
        except:
            return {'global_stats': {}}
    
    return app

# Crear instancia de la aplicación
app = create_app()

if __name__ == '__main__':
    logger.info("🚀 Iniciando Tag-Flow V2 (Refactorizado)")
    logger.info(f"📊 Puerto: {config.FLASK_PORT}")
    logger.info(f"🔧 Debug: {config.FLASK_DEBUG}")
    
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )