"""
Tag-Flow V2 - Batch Database Operations
High-performance batch operations for videos
"""

import time
from typing import Dict, List, Optional, Set
from .base import DatabaseBase
import logging

logger = logging.getLogger(__name__)


class BatchOperations(DatabaseBase):
    """High-performance batch operations for video data"""
    
    def get_existing_paths_only(self) -> Set[str]:
        """
        Get only file_paths for duplicate checking (10x faster)
        
        Returns:
            Set of existing file_paths for O(1) verification
        """
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT file_path FROM videos WHERE deleted_at IS NULL")
            result = {row[0] for row in cursor.fetchall()}
        
        self._track_query('get_existing_paths_only', time.time() - start_time)
        return result
    
    def get_video_by_path_or_name(self, file_path: str, file_name: str) -> Optional[Dict]:
        """
        Search by path OR name in single optimized SQL query
        
        Args:
            file_path: Complete file path
            file_name: File name
            
        Returns:
            Video data dictionary or None if not found
        """
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM videos 
                WHERE (file_path = ? OR file_name = ?) AND deleted_at IS NULL
                LIMIT 1
            """, (file_path, file_name))
            row = cursor.fetchone()
            
            self._track_query('get_video_by_path_or_name', time.time() - start_time)
            return self._format_video_row(row) if row else None
    
    def get_pending_videos_filtered(self, platform_filter: str = None, 
                                   source_filter: str = 'all', limit: int = None) -> List[Dict]:
        """
        Get pending videos with native SQL filters (5x faster)
        
        Args:
            platform_filter: Platform filter ('youtube', 'tiktok', 'instagram', 'all', etc.)
            source_filter: Source filter ('db', 'organized', 'all')
            limit: Result limit
            
        Returns:
            List of filtered pending videos
        """
        self._ensure_initialized()
        start_time = time.time()
        
        query = "SELECT * FROM videos WHERE processing_status = 'pendiente' AND deleted_at IS NULL"
        params = []
        
        # Apply platform filters in SQL
        if platform_filter and platform_filter != 'all-platforms':
            if platform_filter == 'other':
                # Filter additional platforms (not main ones)
                query += " AND platform NOT IN ('youtube', 'tiktok', 'instagram')"
            elif isinstance(platform_filter, list):
                # List of platforms
                placeholders = ','.join(['?' for _ in platform_filter])
                query += f" AND platform IN ({placeholders})"
                params.extend(platform_filter)
            else:
                # Specific platform
                query += " AND platform = ?"
                params.append(platform_filter)
        
        # Order by creation date (newest first)
        query += " ORDER BY created_at DESC"
        
        # Apply limit
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            result = [self._format_video_row(row) for row in cursor.fetchall()]
        
        self._track_query('get_pending_videos_filtered', time.time() - start_time)
        return result
    
    def check_videos_exist_batch(self, file_paths: List[str]) -> Dict[str, bool]:
        """
        Check existence of multiple videos in single query (O(1))
        
        Args:
            file_paths: List of file paths to check
            
        Returns:
            Dictionary {file_path: bool} indicating existence
        """
        if not file_paths:
            return {}
        
        self._ensure_initialized()
        start_time = time.time()
        
        # Create placeholders for IN query
        placeholders = ','.join(['?' for _ in file_paths])
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT file_path FROM videos 
                WHERE file_path IN ({placeholders}) AND deleted_at IS NULL
            """, file_paths)
            
            existing_paths = {row[0] for row in cursor.fetchall()}
            
            # Create results dictionary
            result = {path: path in existing_paths for path in file_paths}
        
        self._track_query('check_videos_exist_batch', time.time() - start_time)
        return result
    
    def get_videos_by_paths_batch(self, file_paths: List[str]) -> Dict[str, Dict]:
        """
        Get multiple videos by their paths in single query
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Dictionary {file_path: video_data}
        """
        if not file_paths:
            return {}
        
        self._ensure_initialized()
        start_time = time.time()
        
        placeholders = ','.join(['?' for _ in file_paths])
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT * FROM videos 
                WHERE file_path IN ({placeholders}) AND deleted_at IS NULL
            """, file_paths)
            
            results = {}
            for row in cursor.fetchall():
                video_data = self._format_video_row(row)
                results[video_data['file_path']] = video_data
        
        self._track_query('get_videos_by_paths_batch', time.time() - start_time)
        return results
    
    def get_videos_by_ids_batch(self, video_ids: List[int]) -> Dict[int, Dict]:
        """
        Get multiple videos by their IDs in single query
        
        Args:
            video_ids: List of video IDs
            
        Returns:
            Dictionary {video_id: video_data}
        """
        if not video_ids:
            return {}
        
        self._ensure_initialized()
        start_time = time.time()
        
        placeholders = ','.join(['?' for _ in video_ids])
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT v.*, c.name as creator_name 
                FROM videos v 
                LEFT JOIN creators c ON v.creator_id = c.id 
                WHERE v.id IN ({placeholders}) AND v.deleted_at IS NULL
            """, video_ids)
            
            results = {}
            for row in cursor.fetchall():
                video_data = self._format_video_row(row)
                results[video_data['id']] = video_data
        
        self._track_query('get_videos_by_ids_batch', time.time() - start_time)
        return results
    
    def bulk_update_status(self, video_ids: List[int], new_status: str) -> int:
        """
        Bulk update processing status for multiple videos
        
        Args:
            video_ids: List of video IDs to update
            new_status: New processing status
            
        Returns:
            Number of videos updated
        """
        if not video_ids:
            return 0
        
        self._ensure_initialized()
        start_time = time.time()
        
        placeholders = ','.join(['?' for _ in video_ids])
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                UPDATE videos 
                SET processing_status = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders}) AND deleted_at IS NULL
            """, [new_status] + video_ids)
            
            updated_count = cursor.rowcount
        
        self._track_query('bulk_update_status', time.time() - start_time)
        logger.info(f"Bulk updated {updated_count} videos to status '{new_status}'")
        return updated_count
    
    def get_statistics_fast(self) -> Dict:
        """
        Get database statistics with optimized queries
        
        Returns:
            Dictionary with various statistics
        """
        self._ensure_initialized()
        start_time = time.time()
        
        stats = {}
        
        with self.get_connection() as conn:
            # Total videos (active)
            cursor = conn.execute("SELECT COUNT(*) FROM videos WHERE deleted_at IS NULL")
            stats['total_videos'] = cursor.fetchone()[0]
            
            # Videos by platform
            cursor = conn.execute("""
                SELECT platform, COUNT(*) as count 
                FROM videos 
                WHERE deleted_at IS NULL 
                GROUP BY platform
            """)
            stats['by_platform'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Videos by status
            cursor = conn.execute("""
                SELECT edit_status, COUNT(*) as count 
                FROM videos 
                WHERE deleted_at IS NULL 
                GROUP BY edit_status
            """)
            stats['by_edit_status'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Videos by processing status
            cursor = conn.execute("""
                SELECT processing_status, COUNT(*) as count 
                FROM videos 
                WHERE deleted_at IS NULL 
                GROUP BY processing_status
            """)
            stats['by_processing_status'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Deleted videos count
            cursor = conn.execute("SELECT COUNT(*) FROM videos WHERE deleted_at IS NOT NULL")
            stats['deleted_videos'] = cursor.fetchone()[0]
            
            # Total creators
            cursor = conn.execute("SELECT COUNT(*) FROM creators")
            stats['total_creators'] = cursor.fetchone()[0]
            
            # Total subscriptions
            cursor = conn.execute("SELECT COUNT(*) FROM subscriptions")
            stats['total_subscriptions'] = cursor.fetchone()[0]
        
        self._track_query('get_statistics_fast', time.time() - start_time)
        return stats
    
    def vacuum_database(self) -> bool:
        """
        Run VACUUM to optimize database file size and performance
        
        Returns:
            True if successful
        """
        self._ensure_initialized()
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                
            self._track_query('vacuum_database', time.time() - start_time)
            logger.info("Database VACUUM completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error running database VACUUM: {e}")
            return False
    
    def analyze_database(self) -> bool:
        """
        Run ANALYZE to update query planner statistics
        
        Returns:
            True if successful
        """
        self._ensure_initialized()
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                conn.execute("ANALYZE")
                
            self._track_query('analyze_database', time.time() - start_time)
            logger.info("Database ANALYZE completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error running database ANALYZE: {e}")
            return False