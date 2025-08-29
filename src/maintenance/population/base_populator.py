"""
Base Populator - Abstract Base Class for Platform Population
==========================================================

Defines the common interface and shared functionality for all platform-specific
population implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class BasePopulator(ABC):
    """
    Abstract base class for platform-specific database population.
    
    Each platform (TikTok, YouTube, Instagram) should inherit from this class
    and implement the required abstract methods.
    """
    
    def __init__(self):
        self._db = None
        self._external_sources = None
    
    @property
    def db(self):
        """Lazy initialization of DatabaseManager via ServiceFactory"""
        if self._db is None:
            from src.service_factory import get_database
            self._db = get_database()
        return self._db
    
    @property
    def external_sources(self):
        """Lazy initialization of ExternalSourcesManager via ServiceFactory"""
        if self._external_sources is None:
            from src.service_factory import get_external_sources
            self._external_sources = get_external_sources()
        return self._external_sources
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the name of the platform this populator handles"""
        pass
    
    @property
    @abstractmethod
    def supported_sources(self) -> List[str]:
        """Return list of supported sources for this platform"""
        pass
    
    @abstractmethod
    def get_last_processed_id(self, source: str, specific_platform: str = None) -> tuple[Any, List[str]]:
        """
        Get the last processed ID for incremental population.
        
        Args:
            source: Source type ('db', 'organized', etc.)
            specific_platform: Optional platform filter for multi-platform handlers
        
        Returns:
            tuple: (last_processed_id, missing_files_list)
        """
        pass
    
    @abstractmethod
    def extract_videos(self, source: str, limit: Optional[int], last_processed_id: Any, specific_platform: str = None) -> List[Dict]:
        """
        Extract videos from external source.
        
        Args:
            source: Source type ('db', 'organized', etc.)
            limit: Maximum number of videos to extract
            last_processed_id: Last processed ID for incremental extraction
            specific_platform: Optional platform filter for multi-platform handlers
            
        Returns:
            List of video data dictionaries
        """
        pass
    
    @abstractmethod
    def process_videos(self, videos: List[Dict], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Process extracted videos and insert them into the database.
        
        Args:
            videos: List of video data to process
            progress_callback: Optional callback for progress reporting
            
        Returns:
            Dictionary with processing results
        """
        pass
    
    def populate(self, source: str, limit: Optional[int] = None, 
                force: bool = False, progress_callback: Optional[Callable] = None, 
                specific_platform: str = None) -> Dict[str, Any]:
        """
        Main population method - orchestrates the entire process.
        
        This is the template method that coordinates:
        1. Get last processed ID
        2. Extract videos
        3. Process videos
        4. Return results
        """
        start_time = time.time()
        
        logger.info(f"🚀 Starting {self.platform_name} population from {source}")
        
        try:
            # Step 1: Get incremental position
            last_processed_id, missing_files = self.get_last_processed_id(source, specific_platform)
            
            # Step 2: Extract videos
            videos = self.extract_videos(source, limit, last_processed_id, specific_platform)
            
            if not videos:
                logger.warning(f"No videos found for {self.platform_name} from {source}")
                return {
                    'success': True,
                    'platform': self.platform_name,
                    'source': source,
                    'videos_added': 0,
                    'videos_updated': 0,
                    'creators_created': 0,
                    'subscriptions_created': 0,
                    'execution_time': time.time() - start_time,
                    'message': f"No videos found for {self.platform_name}"
                }
            
            # Step 3: Process videos
            result = self.process_videos(videos, progress_callback)
            
            # Step 4: Add common metadata
            result.update({
                'success': True,
                'platform': self.platform_name,
                'source': source,
                'execution_time': time.time() - start_time,
                'missing_files_count': len(missing_files) if missing_files else 0
            })
            
            return result
            
        except Exception as e:
            logger.error(f"💥 Error during {self.platform_name} population: {e}")
            return {
                'success': False,
                'platform': self.platform_name,
                'source': source,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def _validate_source(self, source: str) -> bool:
        """Validate if source is supported by this populator"""
        if source not in self.supported_sources:
            logger.error(f"Source '{source}' not supported by {self.platform_name} populator")
            return False
        return True
    
    def _log_results(self, result: Dict[str, Any]):
        """Log population results in a standardized format"""
        if result.get('success'):
            logger.info(
                f"✅ {self.platform_name} population completed: "
                f"{result.get('videos_added', 0)} videos added, "
                f"{result.get('creators_created', 0)} creators, "
                f"{result.get('subscriptions_created', 0)} subscriptions "
                f"in {result.get('execution_time', 0):.2f}s"
            )
        else:
            logger.error(f"❌ {self.platform_name} population failed: {result.get('error', 'Unknown error')}")