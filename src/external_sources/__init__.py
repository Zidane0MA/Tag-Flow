"""
Tag-Flow V2 - External Sources Module
Modular external source handlers organized by platform
"""

from .manager import ExternalSourcesManager
from .youtube import YouTube4KHandler
from .tiktok import TikTokTokkitHandler
from .instagram import InstagramStogramHandler
from .organized import OrganizedFoldersHandler

# Main interface
__all__ = [
    'ExternalSourcesManager',
    'YouTube4KHandler',
    'TikTokTokkitHandler', 
    'InstagramStogramHandler',
    'OrganizedFoldersHandler'
]

# Legacy compatibility - create default manager instance
def get_external_sources_manager(config=None):
    """Get external sources manager instance"""
    return ExternalSourcesManager(config)