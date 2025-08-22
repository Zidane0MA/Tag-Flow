"""
Tag-Flow V2 - Deletion Management
Soft delete, restore, and permanent deletion operations
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from .base import DatabaseBase
import logging

logger = logging.getLogger(__name__)


class DeletionOperations(DatabaseBase):
    """Video deletion management with soft delete support"""
    
    def soft_delete_video(self, video_id: int, deleted_by: str = "user", deletion_reason: str = "") -> bool:
        """Soft delete video (mark as deleted without removing)"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE videos 
                SET deleted_at = CURRENT_TIMESTAMP, 
                    deleted_by = ?, 
                    deletion_reason = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
            ''', (deleted_by, deletion_reason, video_id))
            
            success = cursor.rowcount > 0
            
            self._track_query('soft_delete_video', time.time() - start_time)
            if success:
                logger.info(f"Video {video_id} soft deleted by {deleted_by}. Reason: {deletion_reason}")
            else:
                logger.warning(f"Video {video_id} not found or already deleted")
            
            return success
    
    def restore_video(self, video_id: int) -> bool:
        """Restore soft deleted video"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE videos 
                SET deleted_at = NULL, 
                    deleted_by = NULL, 
                    deletion_reason = NULL,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NOT NULL
            ''', (video_id,))
            
            success = cursor.rowcount > 0
            
            self._track_query('restore_video', time.time() - start_time)
            if success:
                logger.info(f"Video {video_id} restored successfully")
            else:
                logger.warning(f"Video {video_id} not found in deleted videos")
            
            return success
    
    def permanent_delete_video(self, video_id: int) -> bool:
        """Permanently delete video and all related data"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            try:
                # Delete related data first (CASCADE will handle some)
                conn.execute('DELETE FROM video_lists WHERE video_id = ?', (video_id,))
                conn.execute('DELETE FROM downloader_mapping WHERE video_id = ?', (video_id,))
                
                # Delete the video itself
                cursor = conn.execute('DELETE FROM videos WHERE id = ?', (video_id,))
                success = cursor.rowcount > 0
                
                conn.commit()
                
                self._track_query('permanent_delete_video', time.time() - start_time)
                if success:
                    logger.info(f"Video {video_id} permanently deleted with all related data")
                else:
                    logger.warning(f"Video {video_id} not found for permanent deletion")
                
                return success
                
            except Exception as e:
                logger.error(f"Error permanently deleting video {video_id}: {e}")
                conn.rollback()
                return False
    
    def get_deleted_videos(self, limit: int = None, offset: int = 0) -> List[Dict]:
        """Get list of soft deleted videos"""
        self._ensure_initialized()
        start_time = time.time()
        
        query = '''
            SELECT v.*, c.name as creator_name 
            FROM videos v 
            LEFT JOIN creators c ON v.creator_id = c.id 
            WHERE v.deleted_at IS NOT NULL 
            ORDER BY v.deleted_at DESC
        '''
        params = []
        
        if limit:
            query += f' LIMIT {limit}'
            if offset:
                query += f' OFFSET {offset}'
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            self._track_query('get_deleted_videos', time.time() - start_time)
            return [self._format_video_row(row) for row in rows]
    
    def count_deleted_videos(self) -> int:
        """Count soft deleted videos"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM videos WHERE deleted_at IS NOT NULL')
            count = cursor.fetchone()[0]
            
            self._track_query('count_deleted_videos', time.time() - start_time)
            return count
    
    def bulk_delete_videos(self, video_ids: List[int], deleted_by: str = "user", deletion_reason: str = "") -> Tuple[int, int]:
        """Soft delete multiple videos in batch"""
        if not video_ids:
            return 0, 0
            
        self._ensure_initialized()
        start_time = time.time()
        
        successful = 0
        failed = 0
        
        with self.get_connection() as conn:
            try:
                for video_id in video_ids:
                    cursor = conn.execute('''
                        UPDATE videos 
                        SET deleted_at = CURRENT_TIMESTAMP, 
                            deleted_by = ?, 
                            deletion_reason = ?,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE id = ? AND deleted_at IS NULL
                    ''', (deleted_by, deletion_reason, video_id))
                    
                    if cursor.rowcount > 0:
                        successful += 1
                    else:
                        failed += 1
                
                conn.commit()
                
            except Exception as e:
                logger.error(f"Error in bulk delete: {e}")
                conn.rollback()
                failed = len(video_ids)
        
        self._track_query('bulk_delete_videos', time.time() - start_time)
        logger.info(f"Bulk delete completed: {successful} deleted, {failed} failed")
        return successful, failed
    
    def bulk_restore_videos(self, video_ids: List[int]) -> Tuple[int, int]:
        """Restore multiple videos in batch"""
        if not video_ids:
            return 0, 0
            
        self._ensure_initialized()
        start_time = time.time()
        
        successful = 0
        failed = 0
        
        with self.get_connection() as conn:
            try:
                for video_id in video_ids:
                    cursor = conn.execute('''
                        UPDATE videos 
                        SET deleted_at = NULL, 
                            deleted_by = NULL, 
                            deletion_reason = NULL,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE id = ? AND deleted_at IS NOT NULL
                    ''', (video_id,))
                    
                    if cursor.rowcount > 0:
                        successful += 1
                    else:
                        failed += 1
                
                conn.commit()
                
            except Exception as e:
                logger.error(f"Error in bulk restore: {e}")
                conn.rollback()
                failed = len(video_ids)
        
        self._track_query('bulk_restore_videos', time.time() - start_time)
        logger.info(f"Bulk restore completed: {successful} restored, {failed} failed")
        return successful, failed
    
    def cleanup_old_deleted_videos(self, days_old: int = 30) -> int:
        """Permanently delete videos that have been soft deleted for more than specified days"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            # Get videos to delete
            cursor = conn.execute('''
                SELECT id FROM videos 
                WHERE deleted_at IS NOT NULL 
                AND deleted_at < datetime('now', '-{} days')
            '''.format(days_old))
            
            video_ids = [row[0] for row in cursor.fetchall()]
            
            if not video_ids:
                return 0
            
            deleted_count = 0
            try:
                for video_id in video_ids:
                    # Delete related data
                    conn.execute('DELETE FROM video_lists WHERE video_id = ?', (video_id,))
                    conn.execute('DELETE FROM downloader_mapping WHERE video_id = ?', (video_id,))
                    
                    # Delete the video
                    cursor = conn.execute('DELETE FROM videos WHERE id = ?', (video_id,))
                    if cursor.rowcount > 0:
                        deleted_count += 1
                
                conn.commit()
                
                self._track_query('cleanup_old_deleted_videos', time.time() - start_time)
                logger.info(f"Cleaned up {deleted_count} old deleted videos (older than {days_old} days)")
                return deleted_count
                
            except Exception as e:
                logger.error(f"Error cleaning up old deleted videos: {e}")
                conn.rollback()
                return 0