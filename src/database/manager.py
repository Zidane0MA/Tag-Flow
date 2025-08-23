"""
Tag-Flow V2 - Database Manager
Unified database interface coordinating all specialized modules
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from .core import DatabaseCore
from .videos import VideoOperations
from .deletion import DeletionOperations
from .batch import BatchOperations
from .creators import CreatorOperations
from .subscriptions import SubscriptionOperations
from .statistics import StatisticsOperations
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Unified database manager coordinating all specialized operations"""
    
    def __init__(self, db_path: Path = None):
        """Initialize database manager with all operation modules"""
        self.db_path = db_path
        
        # Initialize all operation modules with shared db_path
        self.core = DatabaseCore(db_path)
        self.videos = VideoOperations(db_path)
        self.deletion = DeletionOperations(db_path)
        self.batch = BatchOperations(db_path)
        self.creators = CreatorOperations(db_path)
        self.subscriptions = SubscriptionOperations(db_path)
        self.statistics = StatisticsOperations(db_path)
        
        # Share performance tracking across all modules
        self._sync_performance_tracking()
        
        # Initialize database on first access
        self.init_database()
    
    def _sync_performance_tracking(self):
        """Synchronize performance tracking across all modules"""
        modules = [self.videos, self.deletion, self.batch, self.creators, self.subscriptions, self.statistics]
        
        # Use core module as the main tracker
        for module in modules:
            module.query_times = self.core.query_times
            module.total_queries = self.core.total_queries
            module.cache_hits = self.core.cache_hits
            module.cache_misses = self.core.cache_misses
    
    def get_connection(self):
        """Get database connection"""
        return self.core.get_connection()
    
    def init_database(self):
        """Initialize database schema"""
        return self.core.init_database()
    
    # ===========================================
    # VIDEO OPERATIONS (delegate to VideoOperations)
    # ===========================================
    
    def add_video(self, video_data: Dict) -> int:
        """Add new video to database"""
        return self.videos.add_video(video_data)
    
    def batch_insert_videos(self, videos_data: List[Dict], force: bool = False) -> Tuple[int, int]:
        """Insert multiple videos in batch"""
        return self.videos.batch_insert_videos(videos_data, force)
    
    def get_video(self, video_id: int, include_deleted: bool = False) -> Optional[Dict]:
        """Get video by ID"""
        return self.videos.get_video(video_id, include_deleted)
    
    def get_video_by_path(self, file_path: str, include_deleted: bool = False) -> Optional[Dict]:
        """Get video by file path"""
        return self.videos.get_video_by_path(file_path, include_deleted)
    
    def get_videos(self, filters: Dict = None, limit: int = None, offset: int = 0, include_deleted: bool = False) -> List[Dict]:
        """Get videos with filters"""
        return self.videos.get_videos(filters, limit, offset, include_deleted)
    
    def count_videos(self, filters: Dict = None, include_deleted: bool = False) -> int:
        """Count videos with filters"""
        return self.videos.count_videos(filters, include_deleted)
    
    def update_video(self, video_id: int, updates: Dict) -> bool:
        """Update video"""
        return self.videos.update_video(video_id, updates)
    
    def batch_update_videos(self, video_updates: List[Dict]) -> Tuple[int, int]:
        """Update multiple videos in batch"""
        return self.videos.batch_update_videos(video_updates)
    
    def update_video_characters(self, video_id: int, characters_json: str = None) -> bool:
        """Update video characters"""
        return self.videos.update_video_characters(video_id, characters_json)
    
    def delete_video(self, video_id: int) -> bool:
        """Hard delete video"""
        return self.videos.delete_video(video_id)
    
    # ===========================================
    # DELETION OPERATIONS (delegate to DeletionOperations)
    # ===========================================
    
    def soft_delete_video(self, video_id: int, deleted_by: str = "user", deletion_reason: str = "") -> bool:
        """Soft delete video"""
        return self.deletion.soft_delete_video(video_id, deleted_by, deletion_reason)
    
    def restore_video(self, video_id: int) -> bool:
        """Restore soft deleted video"""
        return self.deletion.restore_video(video_id)
    
    def permanent_delete_video(self, video_id: int) -> bool:
        """Permanently delete video"""
        return self.deletion.permanent_delete_video(video_id)
    
    def get_deleted_videos(self, limit: int = None, offset: int = 0) -> List[Dict]:
        """Get soft deleted videos"""
        return self.deletion.get_deleted_videos(limit, offset)
    
    def count_deleted_videos(self) -> int:
        """Count soft deleted videos"""
        return self.deletion.count_deleted_videos()
    
    def bulk_delete_videos(self, video_ids: List[int], deleted_by: str = "user", deletion_reason: str = "") -> Tuple[int, int]:
        """Bulk soft delete videos"""
        return self.deletion.bulk_delete_videos(video_ids, deleted_by, deletion_reason)
    
    def bulk_restore_videos(self, video_ids: List[int]) -> Tuple[int, int]:
        """Bulk restore videos"""
        return self.deletion.bulk_restore_videos(video_ids)
    
    # ===========================================
    # BATCH OPERATIONS (delegate to BatchOperations)
    # ===========================================
    
    def get_existing_paths_only(self) -> Set[str]:
        """Get existing file paths for duplicate checking"""
        return self.batch.get_existing_paths_only()
    
    def get_video_by_path_or_name(self, file_path: str, file_name: str) -> Optional[Dict]:
        """Get video by path or name"""
        return self.batch.get_video_by_path_or_name(file_path, file_name)
    
    def get_pending_videos_filtered(self, platform_filter: str = None, 
                                   source_filter: str = 'all', limit: int = None) -> List[Dict]:
        """Get pending videos with filters"""
        return self.batch.get_pending_videos_filtered(platform_filter, source_filter, limit)
    
    def check_videos_exist_batch(self, file_paths: List[str]) -> Dict[str, bool]:
        """Check if multiple videos exist in batch"""
        return self.batch.check_videos_exist_batch(file_paths)
    
    def get_videos_by_paths_batch(self, file_paths: List[str]) -> Dict[str, Dict]:
        """Get multiple videos by paths in batch"""
        return self.batch.get_videos_by_paths_batch(file_paths)
    
    def get_videos_by_ids_batch(self, video_ids: List[int]) -> Dict[int, Dict]:
        """Get multiple videos by IDs in batch"""
        return self.batch.get_videos_by_ids_batch(video_ids)
    
    def bulk_update_status(self, video_ids: List[int], new_status: str) -> int:
        """Bulk update processing status"""
        return self.batch.bulk_update_status(video_ids, new_status)
    
    def vacuum_database(self) -> bool:
        """Run database VACUUM"""
        return self.batch.vacuum_database()
    
    def analyze_database(self) -> bool:
        """Run database ANALYZE"""
        return self.batch.analyze_database()
    
    # ===========================================
    # CREATOR OPERATIONS (delegate to CreatorOperations)
    # ===========================================
    
    def create_creator(self, name: str, parent_creator_id: int = None, 
                      is_primary: bool = True, alias_type: str = 'main') -> int:
        """Create new creator"""
        return self.creators.create_creator(name, parent_creator_id, is_primary, alias_type)
    
    def get_creator_by_name(self, name: str) -> Optional[Dict]:
        """Get creator by name"""
        return self.creators.get_creator_by_name(name)
    
    def get_creator_with_urls(self, creator_id: int) -> Optional[Dict]:
        """Get creator with URLs"""
        return self.creators.get_creator_with_urls(creator_id)
    
    def add_creator_url(self, creator_id: int, platform: str, url: str) -> bool:
        """Add creator URL for platform"""
        return self.creators.add_creator_url(creator_id, platform, url)
    
    def batch_create_creators(self, creators_data: List[Dict]) -> tuple[Dict[str, int], int]:
        """Batch create multiple creators"""
        return self.creators.batch_create_creators(creators_data)
    
    def batch_add_creator_urls(self, url_data: List[Dict]) -> int:
        """Batch add creator URLs"""
        return self.creators.batch_add_creator_urls(url_data)
    
    def link_creator_as_secondary(self, secondary_creator_id: int, primary_creator_id: int, 
                                 alias_type: str = 'secondary') -> bool:
        """Link creator as secondary account"""
        return self.creators.link_creator_as_secondary(secondary_creator_id, primary_creator_id, alias_type)
    
    def unlink_secondary_creator(self, secondary_creator_id: int) -> bool:
        """Unlink secondary creator"""
        return self.creators.unlink_secondary_creator(secondary_creator_id)
    
    def get_creator_with_secondaries(self, creator_id: int) -> Optional[Dict]:
        """Get creator with all secondary accounts"""
        return self.creators.get_creator_with_secondaries(creator_id)
    
    def get_primary_creator_for_video(self, video_id: int) -> Optional[Dict]:
        """Get primary creator for video"""
        return self.creators.get_primary_creator_for_video(video_id)
    
    def search_creators_with_hierarchy(self, search_term: str) -> List[Dict]:
        """Search creators with hierarchy info"""
        return self.creators.search_creators_with_hierarchy(search_term)
    
    def get_creator_hierarchy_stats(self, creator_id: int) -> Dict:
        """Get creator hierarchy statistics"""
        return self.creators.get_creator_hierarchy_stats(creator_id)
    
    def get_unique_creators(self) -> List[str]:
        """Get unique creator names"""
        return self.creators.get_unique_creators()
    
    # ===========================================
    # SUBSCRIPTION OPERATIONS (delegate to SubscriptionOperations)
    # ===========================================
    
    def create_subscription(self, name: str, type: str, platform: str, 
                          creator_id: int = None, subscription_url: str = None) -> int:
        """Create new subscription"""
        return self.subscriptions.create_subscription(name, type, platform, creator_id, subscription_url)
    
    def get_subscription_by_name_and_platform(self, name: str, platform: str, type: str = None) -> Optional[Dict]:
        """Get subscription by name and platform"""
        return self.subscriptions.get_subscription_by_name_and_platform(name, platform, type)
    
    def get_subscriptions_by_creator(self, creator_id: int) -> List[Dict]:
        """Get subscriptions by creator"""
        return self.subscriptions.get_subscriptions_by_creator(creator_id)
    
    def get_subscriptions_by_platform_and_type(self, platform: str, type: str) -> List[Dict]:
        """Get subscriptions by platform and type"""
        return self.subscriptions.get_subscriptions_by_platform_and_type(platform, type)
    
    def add_video_to_list(self, video_id: int, list_type: str) -> bool:
        """Add video to list"""
        return self.subscriptions.add_video_to_list(video_id, list_type)
    
    def get_video_lists(self, video_id: int) -> List[str]:
        """Get video lists"""
        return self.subscriptions.get_video_lists(video_id)
    
    def get_videos_by_list_type(self, list_type: str, platform: str = None, limit: int = None) -> List[Dict]:
        """Get videos by list type"""
        return self.subscriptions.get_videos_by_list_type(list_type, platform, limit)
    
    def get_videos_by_creator_with_metadata(self, creator_id: int, platform: str = None, limit: int = None) -> List[Dict]:
        """Get videos by creator with metadata"""
        return self.subscriptions.get_videos_by_creator_with_metadata(creator_id, platform, limit)
    
    def get_videos_by_subscription_with_metadata(self, subscription_id: int, limit: int = None) -> List[Dict]:
        """Get videos by subscription with metadata"""
        return self.subscriptions.get_videos_by_subscription_with_metadata(subscription_id, limit)
    
    # ===========================================
    # STATISTICS OPERATIONS (delegate to StatisticsOperations)
    # ===========================================
    
    def get_stats(self) -> Dict:
        """Get general database statistics"""
        return self.statistics.get_stats()
    
    def get_creator_stats(self, creator_id: int) -> Dict:
        """Get creator statistics"""
        return self.statistics.get_creator_stats(creator_id)
    
    def get_platform_stats_external_sources(self) -> Dict:
        """Get platform statistics from external sources"""
        return self.statistics.get_platform_stats_external_sources()
    
    def get_performance_report(self) -> Dict:
        """Get performance report"""
        return self.statistics.get_performance_report()
    
    def log_performance_summary(self):
        """Log performance summary"""
        return self.statistics.log_performance_summary()
    
    def get_unique_music(self) -> List[str]:
        """Get unique music tracks"""
        return self.statistics.get_unique_music()
    
    def get_database_health_check(self) -> Dict:
        """Get database health check"""
        return self.statistics.get_database_health_check()
    
    # ===========================================
    # PERFORMANCE TRACKING (shared across modules)
    # ===========================================
    
    def _track_query(self, query_name: str, execution_time: float):
        """Track query performance (delegated to core)"""
        return self.core._track_query(query_name, execution_time)


# Legacy compatibility proxy for existing code
class DatabaseProxy:
    """Compatibility proxy for legacy code using direct imports"""
    
    def __init__(self, db_path: Path = None):
        self._manager = DatabaseManager(db_path)
    
    def __getattr__(self, name):
        """Delegate all method calls to the manager"""
        return getattr(self._manager, name)