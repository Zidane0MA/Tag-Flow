"""
Tag-Flow V2 - External Sources Base Classes
Common functionality and interfaces for all external source handlers
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ExternalSourceHandler(ABC):
    """Base class for all external source handlers"""
    
    def __init__(self, source_path: Optional[Path] = None):
        self.source_path = source_path
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def extract_videos(self, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """Extract videos from this external source"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this external source is available"""
        pass
    
    def _get_connection(self, db_path: Path) -> Optional[sqlite3.Connection]:
        """Create database connection with error handling"""
        if not db_path or not db_path.exists():
            return None
        
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            self.logger.error(f"Error connecting to {db_path}: {e}")
            return None
    
    def _safe_int(self, value, default: int = 0) -> int:
        """Safely convert value to int"""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_str(self, value, default: str = "") -> str:
        """Safely convert value to string"""
        if value is None:
            return default
        return str(value).strip()
    
    def _normalize_platform_name(self, platform: str) -> str:
        """Normalize platform names to consistent format"""
        platform_map = {
            'youtube.com': 'youtube',
            'tiktok.com': 'tiktok', 
            'instagram.com': 'instagram',
            'facebook.com': 'facebook',
            'twitter.com': 'twitter',
            'x.com': 'twitter'
        }
        
        platform_lower = platform.lower()
        for key, normalized in platform_map.items():
            if key in platform_lower:
                return normalized
        
        return platform_lower
    
    def _extract_creator_from_path(self, file_path: Path) -> Optional[str]:
        """Extract creator name from file path using common patterns"""
        try:
            parts = file_path.parts
            
            # Look for creator patterns in path
            for part in reversed(parts):
                part_clean = part.strip()
                
                # Skip common folder names
                skip_folders = {
                    'downloads', 'videos', 'content', 'media', 'files',
                    'youtube', 'tiktok', 'instagram', 'facebook'
                }
                
                if (part_clean and 
                    part_clean.lower() not in skip_folders and
                    not part_clean.startswith('.') and
                    len(part_clean) > 2):
                    return part_clean
            
            return None
        except Exception:
            return None


class DatabaseExtractor(ExternalSourceHandler):
    """Base class for database-based external sources"""
    
    def __init__(self, db_path: Optional[Path] = None):
        super().__init__(db_path)
        self.db_path = db_path
    
    def is_available(self) -> bool:
        """Check if database is available"""
        return self.db_path and self.db_path.exists()
    
    def _execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute query with error handling"""
        if not self.is_available():
            return []
        
        try:
            conn = self._get_connection(self.db_path)
            if not conn:
                return []
            
            with conn:
                cursor = conn.execute(query, params)
                return cursor.fetchall()
                
        except Exception as e:
            self.logger.error(f"Database query error: {e}")
            return []


class FolderExtractor(ExternalSourceHandler):
    """Base class for folder-based external sources"""
    
    def __init__(self, base_path: Optional[Path] = None):
        super().__init__(base_path)
        self.base_path = base_path
    
    def is_available(self) -> bool:
        """Check if base folder is available"""
        return self.base_path and self.base_path.exists() and self.base_path.is_dir()
    
    def _get_video_files(self, directory: Path) -> List[Path]:
        """Get all video files in directory"""
        if not directory.exists():
            return []
        
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
        video_files = []
        
        try:
            for file_path in directory.rglob('*'):
                if (file_path.is_file() and 
                    file_path.suffix.lower() in video_extensions):
                    video_files.append(file_path)
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
        
        return video_files
    
    def _get_file_stats(self, file_path: Path) -> Dict:
        """Get file statistics"""
        try:
            stat = file_path.stat()
            return {
                'file_size': stat.st_size,
                'created_at': stat.st_ctime,
                'modified_at': stat.st_mtime
            }
        except Exception:
            return {
                'file_size': 0,
                'created_at': None,
                'modified_at': None
            }