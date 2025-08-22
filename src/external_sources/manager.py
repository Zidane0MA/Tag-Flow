"""
Tag-Flow V2 - External Sources Manager
Unified interface for all external source handlers
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .youtube import YouTube4KHandler
from .tiktok import TikTokTokkitHandler
from .instagram import InstagramStogramHandler
from .organized import OrganizedFoldersHandler

import logging
logger = logging.getLogger(__name__)


class ExternalSourcesManager:
    """Unified manager for all external source handlers"""
    
    def __init__(self, config=None):
        """Initialize all external source handlers"""
        self.config = config or {}
        self.logger = logger
        
        # Initialize handlers
        self._init_handlers()
    
    def _init_handlers(self):
        """Initialize all platform handlers"""
        try:
            # YouTube 4K Video Downloader
            youtube_db_path = self._get_config_path('EXTERNAL_YOUTUBE_DB')
            self.youtube_handler = YouTube4KHandler(youtube_db_path)
            
            # TikTok 4K Tokkit (base_path auto-derived from db_path)
            tiktok_db_path = self._get_config_path('EXTERNAL_TIKTOK_DB')
            self.tiktok_handler = TikTokTokkitHandler(tiktok_db_path)
            
            # Instagram 4K Stogram (base_path auto-derived from db_path)
            instagram_db_path = self._get_config_path('EXTERNAL_INSTAGRAM_DB')
            self.instagram_handler = InstagramStogramHandler(instagram_db_path)
            
            # Organized Folders
            organized_base_path = self._get_config_path('ORGANIZED_BASE_PATH')
            self.organized_handler = OrganizedFoldersHandler(organized_base_path)
            
            self.logger.debug("External source handlers initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing external source handlers: {e}")
    
    def _get_config_path(self, key: str) -> Optional[Path]:
        """Get path from configuration or environment"""
        try:
            # Try config object attribute first, then environment
            path_value = None
            if hasattr(self.config, key):
                path_value = getattr(self.config, key)
            elif isinstance(self.config, dict):
                path_value = self.config.get(key)
            
            if not path_value:
                path_value = os.getenv(key)
            
            if path_value:
                path = Path(path_value)
                return path if path.exists() else None
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting config path for {key}: {e}")
            return None
    
    # YouTube Methods
    def get_youtube_platforms(self) -> Dict[str, int]:
        """Get available platforms from YouTube 4K Video Downloader"""
        try:
            return self.youtube_handler.get_available_platforms()
        except Exception as e:
            self.logger.error(f"Error getting YouTube platforms: {e}")
            return {}
    
    def extract_youtube_videos(self, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """Extract videos from YouTube 4K Video Downloader"""
        try:
            return self.youtube_handler.extract_videos(offset, limit)
        except Exception as e:
            self.logger.error(f"Error extracting YouTube videos: {e}")
            return []
    
    def extract_youtube_by_platform(self, platform: str, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """Extract videos from specific platform in YouTube 4K Video Downloader"""
        try:
            return self.youtube_handler.extract_by_platform(platform, offset, limit)
        except Exception as e:
            self.logger.error(f"Error extracting YouTube videos by platform {platform}: {e}")
            return []
    
    # TikTok Methods
    def extract_tiktok_videos(self, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """Extract videos from TikTok 4K Tokkit"""
        try:
            return self.tiktok_handler.extract_videos(offset, limit)
        except Exception as e:
            self.logger.error(f"Error extracting TikTok videos: {e}")
            return []
    
    # Instagram Methods
    def extract_instagram_videos(self, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """Extract content from Instagram 4K Stogram"""
        try:
            return self.instagram_handler.extract_videos(offset, limit)
        except Exception as e:
            self.logger.error(f"Error extracting Instagram content: {e}")
            return []
    
    # Organized Folders Methods
    def get_organized_platforms(self) -> Dict:
        """Get available platforms from organized folders"""
        try:
            return self.organized_handler.get_available_platforms()
        except Exception as e:
            self.logger.error(f"Error getting organized platforms: {e}")
            return {'main': {}, 'additional': {}}
    
    def extract_organized_videos(self, platform_filter: Optional[str] = None) -> List[Dict]:
        """Extract videos from organized folders"""
        try:
            return self.organized_handler.extract_videos(platform_filter)
        except Exception as e:
            self.logger.error(f"Error extracting organized videos: {e}")
            return []
    
    # Unified Methods
    def get_all_available_platforms(self) -> Dict[str, Any]:
        """Get all available platforms from all sources"""
        platforms = {
            'youtube_4k': self.get_youtube_platforms(),
            'organized': self.get_organized_platforms(),
            'tiktok_available': self.tiktok_handler.is_available(),
            'instagram_available': self.instagram_handler.is_available()
        }
        return platforms
    
    def get_available_platforms(self) -> Dict[str, Dict]:
        """Auto-detect all available platforms (main interface for video analyzer)"""
        platforms = {
            'main': {
                'youtube': {
                    'has_db': self.is_youtube_available(),
                    'has_organized': False,  # Will be filled from organized handler
                    'folder_name': 'Youtube'
                },
                'tiktok': {
                    'has_db': self.is_tiktok_available(),
                    'has_organized': False,
                    'folder_name': 'Tiktok'
                },
                'instagram': {
                    'has_db': self.is_instagram_available(),
                    'has_organized': False,
                    'folder_name': 'Instagram'
                }
            },
            'additional': {}
        }
        
        # Get organized folder information
        organized_platforms = self.get_organized_platforms()
        
        # Update main platforms with organized folder info
        for platform in ['youtube', 'tiktok', 'instagram']:
            if platform in organized_platforms['main']:
                platforms['main'][platform]['has_organized'] = organized_platforms['main'][platform]['has_organized']
        
        # Add additional platforms from organized folders
        platforms['additional'] = organized_platforms['additional']
        
        return platforms
    
    def get_all_videos_from_source(self, source: str, platform: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Main interface for getting videos from external sources with dynamic offset strategy"""
        try:
            all_videos = []
            
            # Normalize platform parameter
            normalized_platform = None if platform in [None, 'all-platforms'] else platform
            
            if source in ['db', 'all']:
                # Extract from database sources with dynamic offset
                if normalized_platform is None:
                    # All platforms with dynamic offset
                    youtube_offset = self._get_dynamic_offset('youtube')
                    tiktok_offset = self._get_dynamic_offset('tiktok')
                    instagram_offset = self._get_dynamic_offset('instagram')
                    
                    self.logger.debug(f"🔍 Using dynamic offsets - YouTube: {youtube_offset}, TikTok: {tiktok_offset}, Instagram: {instagram_offset}")
                    
                    all_videos.extend(self.extract_youtube_videos(youtube_offset, limit))
                    all_videos.extend(self.extract_tiktok_videos(tiktok_offset, limit))
                    all_videos.extend(self.extract_instagram_videos(instagram_offset, limit))
                elif normalized_platform == 'youtube':
                    offset = self._get_dynamic_offset('youtube')
                    self.logger.debug(f"🔍 Using dynamic offset for YouTube: {offset}")
                    # Use platform-specific extraction to get ONLY YouTube videos from 4K DB
                    all_videos.extend(self.extract_youtube_by_platform('youtube', offset, limit))
                elif normalized_platform == 'tiktok':
                    offset = self._get_dynamic_offset('tiktok')
                    self.logger.debug(f"🔍 Using dynamic offset for TikTok: {offset}")
                    all_videos.extend(self.extract_tiktok_videos(offset, limit))
                elif normalized_platform == 'instagram':
                    offset = self._get_dynamic_offset('instagram')
                    self.logger.debug(f"🔍 Using dynamic offset for Instagram: {offset}")
                    all_videos.extend(self.extract_instagram_videos(offset, limit))
                else:
                    # Handle other platforms that might be in 4K Video Downloader (facebook, bilibili, etc.)
                    offset = self._get_dynamic_offset(normalized_platform)
                    self.logger.debug(f"🔍 Using dynamic offset for {normalized_platform}: {offset}")
                    # Try to extract from 4K DB first (supports multiple platforms)
                    all_videos.extend(self.extract_youtube_by_platform(normalized_platform, offset, limit))
            
            if source in ['organized', 'all']:
                # Extract from organized folders
                all_videos.extend(self.extract_organized_videos(normalized_platform))
            
            # Remove duplicates based on file path
            seen_paths = set()
            unique_videos = []
            for video in all_videos:
                file_path = video.get('file_path')
                if file_path and file_path not in seen_paths:
                    seen_paths.add(file_path)
                    unique_videos.append(video)
            
            # Apply limit if specified
            if limit is not None:
                unique_videos = unique_videos[:limit]
            
            self.logger.debug(f"Total unique videos extracted: {len(unique_videos)}")
            return unique_videos
            
        except Exception as e:
            self.logger.error(f"Error getting all videos from source {source}: {e}")
            return []
    
    def extract_videos_by_source(self, source: str, platform: Optional[str] = None, 
                                offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """Extract videos by source type"""
        try:
            if source == 'db':
                # Database sources
                if platform == 'youtube':
                    return self.extract_youtube_videos(offset, limit)
                elif platform == 'tiktok':
                    return self.extract_tiktok_videos(offset, limit)
                elif platform == 'instagram':
                    return self.extract_instagram_videos(offset, limit)
                else:
                    # All database sources
                    videos = []
                    videos.extend(self.extract_youtube_videos(offset, limit))
                    videos.extend(self.extract_tiktok_videos(offset, limit))
                    videos.extend(self.extract_instagram_videos(offset, limit))
                    return videos
            
            elif source == 'organized':
                # Organized folder sources
                return self.extract_organized_videos(platform)
            
            else:
                self.logger.warning(f"Unknown source: {source}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error extracting videos by source {source}: {e}")
            return []
    
    # Availability Methods
    def is_youtube_available(self) -> bool:
        """Check if YouTube 4K Video Downloader is available"""
        return self.youtube_handler.is_available()
    
    def is_tiktok_available(self) -> bool:
        """Check if TikTok 4K Tokkit is available"""
        return self.tiktok_handler.is_available()
    
    def is_instagram_available(self) -> bool:
        """Check if Instagram 4K Stogram is available"""
        return self.instagram_handler.is_available()
    
    def is_organized_available(self) -> bool:
        """Check if organized folders are available"""
        return self.organized_handler.is_available()
    
    def get_availability_status(self) -> Dict[str, bool]:
        """Get availability status of all sources"""
        return {
            'youtube_4k': self.is_youtube_available(),
            'tiktok_tokkit': self.is_tiktok_available(),
            'instagram_stogram': self.is_instagram_available(),
            'organized_folders': self.is_organized_available()
        }
    
    # Legacy compatibility methods
    def extract_videos_from_youtube_4k(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """Legacy method for YouTube extraction"""
        return self.extract_youtube_videos(offset, limit)
    
    def extract_videos_from_tiktok_tokkit(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """Legacy method for TikTok extraction"""
        return self.extract_tiktok_videos(offset, limit)
    
    def extract_videos_from_instagram_stogram(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """Legacy method for Instagram extraction"""
        return self.extract_instagram_videos(offset, limit)
    
    def extract_videos_from_organized_folders(self, platform: Optional[str] = None) -> List[Dict]:
        """Legacy method for organized folders extraction"""
        return self.extract_organized_videos(platform)
    
    def _get_dynamic_offset(self, platform_name: str) -> int:
        """🚀 Calculate dynamic offset based on existing videos in database"""
        try:
            from src.service_factory import get_database
            db = get_database()
            with db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM videos WHERE platform = ? AND deleted_at IS NULL",
                    (platform_name,)
                )
                offset = cursor.fetchone()[0]
                return offset
        except Exception as e:
            self.logger.debug(f"Error calculating offset for {platform_name}: {e}")
            return 0