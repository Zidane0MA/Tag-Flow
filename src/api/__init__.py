"""
Tag-Flow V2 - API Package
Blueprints para organizar las rutas de la aplicación
"""

from .gallery import gallery_bp
from .videos import videos_bp  
from .admin import admin_bp
from .maintenance import maintenance_bp
from .creators import creators_bp

__all__ = ['gallery_bp', 'videos_bp', 'admin_bp', 'maintenance_bp', 'creators_bp']