"""
Tag-Flow V2 - Aplicación Flask Refactorizada
Interfaz web moderna con arquitectura de blueprints
"""

import sys
from pathlib import Path
import logging
from flask import Flask, send_file, abort, render_template
from flask_cors import CORS

# Agregar src al path
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config
# Database will be imported lazily within functions
from src.api import gallery_bp, videos_bp, admin_bp, maintenance_bp

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
    
    # Registrar blueprints
    app.register_blueprint(gallery_bp)
    app.register_blueprint(videos_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(maintenance_bp)
    
    # Rutas estáticas y archivos
    @app.route('/thumbnail/<path:filename>')
    def serve_thumbnail(filename):
        """Servir thumbnails generados"""
        try:
            thumbnail_path = config.DATA_DIR / 'thumbnails' / filename
            if thumbnail_path.exists():
                return send_file(thumbnail_path)
            else:
                # Thumbnail por defecto
                return send_file(config.STATIC_DIR / 'img' / 'no-thumbnail.svg')
        except Exception as e:
            logger.error(f"Error sirviendo thumbnail {filename}: {e}")
            abort(404)
    
    @app.route('/video-stream/<int:video_id>')
    def stream_video(video_id):
        """Servir video para streaming (para reproducción en navegador)"""
        try:
            from src.service_factory import get_database
            db = get_database()
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
    
    # Manejadores de errores
    @app.errorhandler(404)
    def not_found_error(error):
        """Página 404 personalizada"""
        return render_template('error.html', 
                             error="Página no encontrada",
                             details="La página que buscas no existe."), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Página 500 personalizada"""
        return render_template('error.html', 
                             error="Error interno del servidor",
                             details="Ha ocurrido un error inesperado."), 500
    
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