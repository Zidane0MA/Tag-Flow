"""
Tag-Flow V2 - Performance Module
Sistema de optimización de rendimiento integrado
"""

from .core import performance_bp
from .cache import smart_cache, cached, CacheManager
from .monitor import get_database_monitor

__all__ = [
    'performance_bp',
    'smart_cache',
    'cached',
    'CacheManager',
    'get_database_monitor'
]