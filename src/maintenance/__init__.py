#!/usr/bin/env python3
"""
🔧 Maintenance Module
Módulo de mantenimiento refactorizado para Tag-Flow V2

Proporciona interfaces limpias para operaciones de mantenimiento
especializadas por responsabilidad.
"""

# Importar operaciones de thumbnails
from .thumbnail_ops import (
    ThumbnailOperations,
    regenerate_thumbnails,
    regenerate_thumbnails_by_ids,
    clean_thumbnails,
    get_thumbnail_stats,
    populate_thumbnails,
    clear_thumbnails
)

# Importar operaciones de base de datos
from .database_ops import (
    DatabaseOperations,
    populate_database,
    optimize_database,
    clear_database,
    backup_database,
    restore_database,
    get_database_stats
)

# Exportar interfaces públicas
__all__ = [
    # Clases principales
    'ThumbnailOperations',
    'DatabaseOperations',
    
    # Funciones de conveniencia para thumbnails
    'regenerate_thumbnails',
    'regenerate_thumbnails_by_ids',
    'clean_thumbnails',
    'get_thumbnail_stats', 
    'populate_thumbnails',
    'clear_thumbnails',
    
    # Funciones de conveniencia para base de datos
    'populate_database',
    'optimize_database',
    'clear_database',
    'backup_database',
    'restore_database',
    'get_database_stats'
]

# Metadata del módulo
__version__ = '2.0.0'
__author__ = 'Tag-Flow Development Team'
__description__ = 'Módulo de mantenimiento refactorizado para Tag-Flow V2'