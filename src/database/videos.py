"""
Tag-Flow V2 - Video Database Operations
CRUD operations for videos with optimizations
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from .base import DatabaseBase
import logging

logger = logging.getLogger(__name__)


class VideoOperations(DatabaseBase):
    """Video CRUD operations with performance optimizations"""
    
    def add_video(self, video_data: Dict) -> int:
        """Add new video to database (with automatic creator_id resolution)"""
        self._ensure_initialized()
        
        start_time = time.time()
        
        # Resolve creator_name to creator_id
        creator_id = None
        if video_data.get('creator_name'):
            from .creators import CreatorOperations
            creator_ops = CreatorOperations(self.db_path)
            creator = creator_ops.get_creator_by_name(video_data['creator_name'])
            if creator:
                creator_id = creator['id']
            else:
                # Create creator if doesn't exist
                creator_id = creator_ops.create_creator(video_data['creator_name'])
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO videos (
                    file_path, file_name, creator_id, platform, file_size, duration_seconds,
                    detected_music, detected_music_artist, detected_music_confidence,
                    detected_characters, music_source, processing_status, title
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_data['file_path'],
                video_data['file_name'], 
                creator_id,
                video_data.get('platform', 'tiktok'),
                video_data.get('file_size'),
                video_data.get('duration_seconds'),
                video_data.get('detected_music'),
                video_data.get('detected_music_artist'),
                video_data.get('detected_music_confidence'),
                self._safe_json_dumps(video_data.get('detected_characters', [])),
                video_data.get('music_source'),
                video_data.get('processing_status', 'pendiente'),
                video_data.get('title')
            ))
            video_id = cursor.lastrowid
            
            self._track_query('add_video', time.time() - start_time)
            logger.info(f"Video added with ID {video_id}: {video_data['file_name']} (creator_id: {creator_id})")
            return video_id
    
    def batch_insert_videos(self, videos_data: List[Dict], force: bool = False) -> Tuple[int, int]:
        """Insert multiple videos in single transaction (optimized)"""
        if not videos_data:
            return 0, 0
            
        self._ensure_initialized()
        start_time = time.time()
        
        successful = 0
        failed = 0
        
        with self.get_connection() as conn:
            try:
                if force:
                    # Force mode: use INSERT OR REPLACE to update existing
                    insert_data = []
                    for video_data in videos_data:
                        insert_row = (
                            video_data['file_path'],
                            video_data['file_name'],
                            video_data.get('thumbnail_path'),  # Campo que faltaba
                            video_data.get('file_size'),
                            video_data.get('duration_seconds'),
                            video_data.get('title'),
                            video_data.get('post_url'),
                            video_data.get('platform', 'tiktok'),
                            video_data.get('detected_music'),
                            video_data.get('detected_music_artist'),
                            video_data.get('detected_music_confidence'),
                            self._safe_json_dumps(video_data.get('detected_characters', [])),
                            video_data.get('music_source'),
                            video_data.get('processing_status', 'pendiente'),
                            video_data.get('creator_id'),
                            video_data.get('subscription_id')
                        )
                        insert_data.append(insert_row)
                    
                    conn.executemany('''
                        INSERT OR REPLACE INTO videos (
                            file_path, file_name, thumbnail_path,
                            file_size, duration_seconds, title, post_url, platform,
                            detected_music, detected_music_artist, detected_music_confidence,
                            detected_characters, music_source, processing_status,
                            creator_id, subscription_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', insert_data)
                    
                    successful = len(insert_data)
                    logger.info(f"Batch insert with FORCE successful: {successful} videos")
                else:
                    # Normal mode: insert only new videos
                    video_ids = []
                    for video_data in videos_data:
                        insert_row = (
                            video_data['file_path'],
                            video_data['file_name'],
                            video_data.get('thumbnail_path'),  # Campo que faltaba
                            video_data.get('file_size'),
                            video_data.get('duration_seconds'),
                            video_data.get('title'),
                            video_data.get('post_url'),
                            video_data.get('platform', 'tiktok'),
                            video_data.get('detected_music'),
                            video_data.get('detected_music_artist'),
                            video_data.get('detected_music_confidence'),
                            self._safe_json_dumps(video_data.get('detected_characters', [])),
                            video_data.get('music_source'),
                            video_data.get('processing_status', 'pendiente'),
                            video_data.get('creator_id'),
                            video_data.get('subscription_id')
                        )
                        
                        cursor = conn.execute('''
                            INSERT INTO videos (
                                file_path, file_name, thumbnail_path,
                                file_size, duration_seconds, title, post_url, platform,
                                detected_music, detected_music_artist, detected_music_confidence, 
                                detected_characters, music_source, processing_status,
                                creator_id, subscription_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', insert_row)
                        
                        video_id = cursor.lastrowid
                        video_ids.append(video_id)
                        
                        # Insert downloader mapping if exists
                        if 'downloader_mapping' in video_data and video_data['downloader_mapping']:
                            self._insert_downloader_mapping(conn, video_id, video_data)
                        
                        # Insert video lists if exists
                        if 'list_types' in video_data and video_data['list_types']:
                            self._insert_video_lists(conn, video_id, video_data['list_types'])
                    
                    successful = len(video_ids)
                    logger.debug(f"Batch insert successful: {successful} videos")
                
                conn.commit()
                
            except Exception as e:
                logger.error(f"Error in batch insert: {e}")
                conn.rollback()
                failed = len(videos_data)
        
        self._track_query('batch_insert_videos', time.time() - start_time)
        return successful, failed
    
    def _insert_downloader_mapping(self, conn, video_id: int, video_data: Dict):
        """Insert downloader mapping data"""
        dm_data = video_data['downloader_mapping']
        
        # Get carousel information from dm_data
        is_carousel_item = dm_data.get('is_carousel_item', False)
        carousel_order = dm_data.get('carousel_order')
        carousel_base_id = dm_data.get('carousel_base_id')
        
        logger.debug(f"🎠 CAROUSEL DEBUG - File: {video_data.get('file_name')}, "
                    f"is_carousel: {is_carousel_item}, order: {carousel_order}, base_id: {carousel_base_id}")
        
        if is_carousel_item:
            logger.debug(f"✅ CAROUSEL DETECTED - File: {video_data.get('file_name')}, "
                        f"order: {carousel_order}, base_id: {carousel_base_id}")
        
        conn.execute('''
            INSERT INTO downloader_mapping (
                video_id, download_item_id, external_db_source, 
                original_filename, creator_from_downloader,
                is_carousel_item, carousel_order, carousel_base_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            video_id,
            dm_data.get('download_item_id'),
            dm_data.get('external_db_source'),
            video_data.get('file_name'),
            dm_data.get('creator_from_downloader', video_data.get('creator_name')),
            is_carousel_item,
            carousel_order,
            carousel_base_id
        ))
    
    def _insert_video_lists(self, conn, video_id: int, list_types: List[str]):
        """Insert video list associations"""
        for list_type in list_types:
            conn.execute('''
                INSERT OR IGNORE INTO video_lists (video_id, list_type)
                VALUES (?, ?)
            ''', (video_id, list_type))
    
    def get_video(self, video_id: int, include_deleted: bool = False) -> Optional[Dict]:
        """Get video by ID"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            if include_deleted:
                cursor = conn.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
            else:
                cursor = conn.execute('SELECT * FROM videos WHERE id = ? AND deleted_at IS NULL', (video_id,))
            row = cursor.fetchone()
            
            self._track_query('get_video', time.time() - start_time)
            return self._format_video_row(row) if row else None
    
    def get_video_by_path(self, file_path: str, include_deleted: bool = False) -> Optional[Dict]:
        """Get video by file path (absolute path)"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            if include_deleted:
                cursor = conn.execute('SELECT * FROM videos WHERE file_path = ?', (file_path,))
            else:
                cursor = conn.execute('SELECT * FROM videos WHERE file_path = ? AND deleted_at IS NULL', (file_path,))
            row = cursor.fetchone()
            
            self._track_query('get_video_by_path', time.time() - start_time)
            return self._format_video_row(row) if row else None

    def get_videos(self, filters: Dict = None, limit: int = None, offset: int = 0, include_deleted: bool = False) -> List[Dict]:
        """Get list of videos with optional filters (with JOIN to creators)"""
        self._ensure_initialized()
        start_time = time.time()
        
        if include_deleted:
            query = "SELECT v.*, c.name as creator_name FROM videos v LEFT JOIN creators c ON v.creator_id = c.id WHERE 1=1"
        else:
            query = "SELECT v.*, c.name as creator_name FROM videos v LEFT JOIN creators c ON v.creator_id = c.id WHERE v.deleted_at IS NULL"
        params = []
        
        # Apply filters
        where_clause, filter_params = self._build_where_clause(filters or {})
        if where_clause:
            query += f" AND {where_clause}"
            params.extend(filter_params)
        
        # Add ordering and pagination
        query += " ORDER BY v.created_at DESC"
        if limit:
            query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            self._track_query('get_videos', time.time() - start_time)
            return [self._format_video_row(row) for row in rows]

    def count_videos(self, filters: Dict = None, include_deleted: bool = False) -> int:
        """Count videos with optional filters"""
        self._ensure_initialized()
        start_time = time.time()
        
        if include_deleted:
            query = "SELECT COUNT(*) FROM videos WHERE 1=1"
        else:
            query = "SELECT COUNT(*) FROM videos WHERE deleted_at IS NULL"
        params = []
        
        # Apply filters
        where_clause, filter_params = self._build_where_clause(filters or {})
        if where_clause:
            query += f" AND {where_clause}"
            params.extend(filter_params)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            count = cursor.fetchone()[0]
            
            self._track_query('count_videos', time.time() - start_time)
            return count

    def update_video(self, video_id: int, updates: Dict) -> bool:
        """Update video with provided data - NUEVO ESQUEMA"""
        if not updates:
            return False

        self._ensure_initialized()
        start_time = time.time()

        # Build dynamic update query
        set_clauses = []
        params = []

        for field, value in updates.items():
            if field in ['detected_characters', 'final_characters']:
                # JSON fields need special handling
                set_clauses.append(f"{field} = ?")
                params.append(self._safe_json_dumps(value))
            elif field not in ['id', 'created_at']:  # Don't allow updating these fields
                set_clauses.append(f"{field} = ?")
                params.append(value)

        if not set_clauses:
            return False

        # Add last_updated
        set_clauses.append("last_updated = CURRENT_TIMESTAMP")
        params.append(video_id)

        query = f"UPDATE media SET {', '.join(set_clauses)} WHERE id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            success = cursor.rowcount > 0
            
            self._track_query('update_video', time.time() - start_time)
            if success:
                logger.debug(f"Video {video_id} updated successfully")
            
            return success

    def batch_update_videos(self, video_updates: List[Dict]) -> Tuple[int, int]:
        """Update multiple videos in batch"""
        if not video_updates:
            return 0, 0
            
        self._ensure_initialized()
        start_time = time.time()
        
        successful = 0
        failed = 0
        
        with self.get_connection() as conn:
            try:
                for update_data in video_updates:
                    video_id = update_data.get('id')
                    if not video_id:
                        failed += 1
                        continue
                    
                    updates = {k: v for k, v in update_data.items() if k != 'id'}
                    if self._update_single_video(conn, video_id, updates):
                        successful += 1
                    else:
                        failed += 1
                
                conn.commit()
                
            except Exception as e:
                logger.error(f"Error in batch update: {e}")
                conn.rollback()
                failed = len(video_updates)
        
        self._track_query('batch_update_videos', time.time() - start_time)
        logger.info(f"Batch update completed: {successful} successful, {failed} failed")
        return successful, failed
    
    def _update_single_video(self, conn, video_id: int, updates: Dict) -> bool:
        """Update single video within existing transaction - NUEVO ESQUEMA"""
        if not updates:
            return False

        set_clauses = []
        params = []

        for field, value in updates.items():
            if field in ['detected_characters', 'final_characters']:
                set_clauses.append(f"{field} = ?")
                params.append(self._safe_json_dumps(value))
            elif field not in ['id', 'created_at']:
                set_clauses.append(f"{field} = ?")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("last_updated = CURRENT_TIMESTAMP")
        params.append(video_id)

        query = f"UPDATE media SET {', '.join(set_clauses)} WHERE id = ?"
        cursor = conn.execute(query, params)
        return cursor.rowcount > 0

    def update_video_characters(self, video_id: int, characters_json: str = None) -> bool:
        """Update video characters specifically"""
        return self.update_video(video_id, {'final_characters': characters_json})

    def delete_video(self, video_id: int) -> bool:
        """Hard delete video (permanent removal)"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('DELETE FROM videos WHERE id = ?', (video_id,))
            success = cursor.rowcount > 0
            
            self._track_query('delete_video', time.time() - start_time)
            if success:
                logger.info(f"Video {video_id} permanently deleted")
            
            return success