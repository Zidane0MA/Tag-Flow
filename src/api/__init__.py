"""
Tag-Flow V2 - API Package
Blueprints para organizar las rutas de la aplicación
"""

from .gallery import gallery_bp
from .videos import videos_core_bp, videos_streaming_bp, videos_bulk_bp
from .stats import stats_bp
from .admin import admin_bp
from .maintenance import maintenance_bp
from .creators import creators_bp
from .pagination.routes import cursor_pagination_bp

__all__ = [
    'gallery_bp',
    'videos_core_bp',
    'videos_streaming_bp',
    'videos_bulk_bp',
    'stats_bp',
    'admin_bp',
    'maintenance_bp',
    'creators_bp',
    'cursor_pagination_bp'  # ⚡ NEW - Cursor pagination endpoints
]