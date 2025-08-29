"""
Tag-Flow V2 - Posts Database Operations
CRUD operations for posts and media with new structure
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from .base import DatabaseBase
import logging

logger = logging.getLogger(__name__)


class PostOperations(DatabaseBase):
    """Posts and Media operations for new database structure"""

    def post_exists(self, platform_id: int, platform_post_id: str) -> bool:
        """Check if post already exists - LEGACY: kept for compatibility"""
        if not platform_post_id:
            return False
            
        self._ensure_initialized()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT id FROM posts 
                WHERE platform_id = ? AND platform_post_id = ?
            ''', (platform_id, platform_post_id))
            
            return cursor.fetchone() is not None
            
    def post_exists_by_file_path(self, file_path: str) -> bool:
        """Check if post already exists by file_path (new uniqueness logic)"""
        if not file_path:
            return False
            
        self._ensure_initialized()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT p.id FROM posts p
                JOIN media m ON p.id = m.post_id
                WHERE m.file_path = ?
            ''', (file_path,))
            
            return cursor.fetchone() is not None
    
    def filter_existing_posts(self, video_data_list: list) -> list:
        """Filter out videos that already exist as posts - LEGACY: uses platform_post_id"""
        if not video_data_list:
            return []
            
        self._ensure_initialized()
        
        # Get platform mapping from database
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT id, name FROM platforms')
            platform_mapping = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Build list of (platform_id, platform_post_id) for batch check
        check_pairs = []
        video_index_map = {}  # Map to track original video position
        
        for i, video_data in enumerate(video_data_list):
            platform_name = video_data.get('platform')
            platform_post_id = video_data.get('platform_post_id') or video_data.get('id')
            
            if platform_name and platform_post_id:
                platform_id = platform_mapping.get(platform_name)
                if platform_id:
                    check_pairs.append((platform_id, platform_post_id))
                    video_index_map[(platform_id, platform_post_id)] = i
        
        if not check_pairs:
            return video_data_list  # No valid pairs to check
        
        # Batch query for existing posts
        with self.get_connection() as conn:
            # Create placeholders for IN clause
            placeholders = ','.join(['(?,?)'] * len(check_pairs))
            query = f'''
                SELECT platform_id, platform_post_id FROM posts 
                WHERE (platform_id, platform_post_id) IN ({placeholders})
            '''
            
            # Flatten pairs for query parameters
            params = []
            for pair in check_pairs:
                params.extend(pair)
            
            cursor = conn.execute(query, params)
            existing_pairs = set((row[0], row[1]) for row in cursor.fetchall())
        
        # Filter out existing videos
        new_videos = []
        for i, video_data in enumerate(video_data_list):
            platform_name = video_data.get('platform')
            platform_post_id = video_data.get('platform_post_id') or video_data.get('id')
            
            if platform_name and platform_post_id:
                platform_id = platform_mapping.get(platform_name)
                if platform_id and (platform_id, platform_post_id) not in existing_pairs:
                    new_videos.append(video_data)
            else:
                # Include videos without proper identification (for manual review)
                new_videos.append(video_data)
        
        return new_videos
        
    def filter_existing_posts_by_file_path(self, video_data_list: list) -> list:
        """Filter out videos that already exist as posts - NEW: uses file_path for uniqueness"""
        if not video_data_list:
            return []
            
        self._ensure_initialized()
        
        # Extract file paths for batch checking
        file_paths = []
        video_path_map = {}  # Map file_path to video data index
        
        for i, video_data in enumerate(video_data_list):
            file_path = video_data.get('file_path')
            if file_path:
                file_paths.append(file_path)
                video_path_map[file_path] = i
        
        if not file_paths:
            return video_data_list  # No file paths to check
        
        # Batch query for existing posts by file_path
        with self.get_connection() as conn:
            # Create placeholders for IN clause
            placeholders = ','.join(['?'] * len(file_paths))
            query = f'''
                SELECT DISTINCT m.file_path FROM posts p
                JOIN media m ON p.id = m.post_id
                WHERE m.file_path IN ({placeholders})
            '''
            
            cursor = conn.execute(query, file_paths)
            existing_file_paths = set(row[0] for row in cursor.fetchall())
        
        # Filter out existing videos based on file_path
        new_videos = []
        for video_data in video_data_list:
            file_path = video_data.get('file_path')
            if not file_path or file_path not in existing_file_paths:
                new_videos.append(video_data)
        
        return new_videos

    def create_post_with_media(self, post_data: Dict, media_data: List[Dict], category_types: List[str] = None) -> Tuple[int, List[int]]:
        """Create post with associated media and categories"""
        self._ensure_initialized()
        start_time = time.time()
        
        # Check if post already exists - NEW: Use file_path for uniqueness instead of platform_post_id
        # This allows the same video (same platform_post_id) to exist multiple times if downloaded to different paths
        if media_data and len(media_data) > 0:
            primary_file_path = media_data[0].get('file_path')
            if primary_file_path and self.post_exists_by_file_path(primary_file_path):
                logger.debug(f"Post already exists for file_path: {primary_file_path}")
                return None, []  # Return None to indicate duplicate
        
        with self.get_connection() as conn:
            # Create post
            cursor = conn.execute('''
                INSERT INTO posts (
                    platform_id, platform_post_id, post_url, title_post, use_filename,
                    creator_id, subscription_id, download_date, is_carousel, carousel_count,
                    publication_date, publication_date_source, publication_date_confidence
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post_data['platform_id'],
                post_data.get('platform_post_id'),
                post_data.get('post_url'),
                post_data.get('title_post'),
                post_data.get('use_filename', False),
                post_data.get('creator_id'),
                post_data.get('subscription_id'),
                post_data.get('download_date'),
                len(media_data) > 1,  # is_carousel
                len(media_data),  # carousel_count
                post_data.get('publication_date'),
                post_data.get('publication_date_source'),
                post_data.get('publication_date_confidence')
            ))
            
            post_id = cursor.lastrowid
            
            # Create media items
            media_ids = []
            for i, media_item in enumerate(media_data):
                cursor = conn.execute('''
                    INSERT INTO media (
                        post_id, file_path, file_name, thumbnail_path, file_size,
                        duration_seconds, media_type, resolution_width, resolution_height,
                        fps, carousel_order, is_primary
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post_id,
                    media_item['file_path'],
                    media_item['file_name'],
                    media_item.get('thumbnail_path'),
                    media_item.get('file_size'),
                    media_item.get('duration_seconds'),
                    media_item.get('media_type', 'video'),
                    media_item.get('resolution_width'),
                    media_item.get('resolution_height'),
                    media_item.get('fps'),
                    i,  # carousel_order
                    i == 0  # is_primary (first item)
                ))
                media_ids.append(cursor.lastrowid)
            
            # Create categories
            if category_types:
                for category_type in category_types:
                    conn.execute('''
                        INSERT OR IGNORE INTO post_categories (post_id, category_type)
                        VALUES (?, ?)
                    ''', (post_id, category_type))
            
            self._track_query('create_post_with_media', time.time() - start_time)
            logger.debug(f"✅ Created post {post_id} with {len(media_ids)} media items")
            
            return post_id, media_ids

    def get_posts_with_media(self, creator_id: int = None, subscription_id: int = None, 
                            category_type: str = None, platform_id: int = None, limit: int = 50) -> List[Dict]:
        """Get posts with their media items and metadata"""
        self._ensure_initialized()
        start_time = time.time()
        
        query = '''
            SELECT 
                p.*, 
                pl.name as platform_name,
                pl.display_name as platform_display_name,
                c.name as creator_name,
                s.name as subscription_name,
                s.subscription_type,
                s.is_account,
                m.id as media_id,
                m.file_path,
                m.file_name,
                m.thumbnail_path,
                m.media_type,
                m.duration_seconds,
                m.resolution_width,
                m.resolution_height,
                m.fps,
                m.carousel_order,
                m.is_primary,
                pc.category_type
            FROM posts p
            LEFT JOIN platforms pl ON p.platform_id = pl.id
            LEFT JOIN creators c ON p.creator_id = c.id
            LEFT JOIN subscriptions s ON p.subscription_id = s.id
            LEFT JOIN media m ON p.id = m.post_id
            LEFT JOIN post_categories pc ON p.id = pc.post_id
            WHERE 1=1
        '''
        
        params = []
        
        if creator_id:
            query += ' AND p.creator_id = ?'
            params.append(creator_id)
            
        if subscription_id:
            query += ' AND p.subscription_id = ?'
            params.append(subscription_id)
            
        if category_type:
            query += ' AND pc.category_type = ?'
            params.append(category_type)
            
        if platform_id:
            query += ' AND p.platform_id = ?'
            params.append(platform_id)
        
        query += ' ORDER BY p.publication_date DESC, p.created_at DESC, m.carousel_order ASC'
        query += f' LIMIT {limit * 10}'  # Allow for multiple media per post
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            # Group by post_id
            posts_dict = {}
            for row in rows:
                post_id = row[0]  # p.id
                
                if post_id not in posts_dict:
                    posts_dict[post_id] = {
                        'id': row[0],
                        'platform_id': row[1],
                        'platform_post_id': row[2],
                        'post_url': row[3],
                        'title_post': row[4],
                        'creator_id': row[5],
                        'subscription_id': row[6],
                        'publication_date': row[7],
                        'publication_date_source': row[8],
                        'publication_date_confidence': row[9],
                        'download_date': row[10],
                        'is_carousel': row[11],
                        'carousel_count': row[12],
                        'created_at': row[13],
                        'updated_at': row[14],
                        'deleted_at': row[15],
                        'platform_name': row[17],
                        'platform_display_name': row[18],
                        'creator_name': row[19],
                        'subscription_name': row[20],
                        'subscription_type': row[21],
                        'is_account': row[22],
                        'media': [],
                        'categories': set()
                    }
                
                # Add media if exists
                if row[23]:  # media_id
                    posts_dict[post_id]['media'].append({
                        'id': row[23],
                        'file_path': row[24],
                        'file_name': row[25],
                        'thumbnail_path': row[26],
                        'media_type': row[27],
                        'duration_seconds': row[28],
                        'resolution_width': row[29],
                        'resolution_height': row[30],
                        'fps': row[31],
                        'carousel_order': row[32],
                        'is_primary': row[33]
                    })
                
                # Add category
                if row[34]:  # category_type
                    posts_dict[post_id]['categories'].add(row[34])
            
            # Convert to list and clean up
            posts = []
            for post_data in posts_dict.values():
                post_data['categories'] = list(post_data['categories'])
                posts.append(post_data)
                
                if len(posts) >= limit:
                    break
            
            self._track_query('get_posts_with_media', time.time() - start_time)
            return posts

    def get_post_by_id(self, post_id: int) -> Optional[Dict]:
        """Get single post with media by ID"""
        posts = self.get_posts_with_media(limit=1)
        
        for post in posts:
            if post['id'] == post_id:
                return post
        return None

    def update_post(self, post_id: int, update_data: Dict) -> bool:
        """Update post data"""
        self._ensure_initialized()
        start_time = time.time()
        
        # Build dynamic update query
        update_fields = []
        params = []
        
        allowed_fields = ['title_post', 'post_url', 'publication_date', 'publication_date_source', 
                         'publication_date_confidence', 'download_date']
        
        for field in allowed_fields:
            if field in update_data:
                update_fields.append(f"{field} = ?")
                params.append(update_data[field])
        
        if not update_fields:
            logger.warning("No valid fields to update")
            return False
        
        # Add updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(post_id)
        
        query = f"UPDATE posts SET {', '.join(update_fields)} WHERE id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            success = cursor.rowcount > 0
            
        self._track_query('update_post', time.time() - start_time)
        
        if success:
            logger.debug(f"✅ Updated post {post_id}")
        else:
            logger.warning(f"Post {post_id} not found for update")
            
        return success

    def delete_post(self, post_id: int, deleted_by: str = None, deletion_reason: str = None) -> bool:
        """Soft delete post"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE posts 
                SET deleted_at = CURRENT_TIMESTAMP, deleted_by = ?, deletion_reason = ?
                WHERE id = ? AND deleted_at IS NULL
            ''', (deleted_by, deletion_reason, post_id))
            
            success = cursor.rowcount > 0
            
        self._track_query('delete_post', time.time() - start_time)
        
        if success:
            logger.debug(f"✅ Soft deleted post {post_id}")
        else:
            logger.warning(f"Post {post_id} not found or already deleted")
            
        return success

    def restore_post(self, post_id: int) -> bool:
        """Restore soft deleted post"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE posts 
                SET deleted_at = NULL, deleted_by = NULL, deletion_reason = NULL
                WHERE id = ? AND deleted_at IS NOT NULL
            ''', (post_id,))
            
            success = cursor.rowcount > 0
            
        self._track_query('restore_post', time.time() - start_time)
        
        if success:
            logger.debug(f"✅ Restored post {post_id}")
        else:
            logger.warning(f"Post {post_id} not found or not deleted")
            
        return success

    def add_category_to_post(self, post_id: int, category_type: str) -> bool:
        """Add category to post"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT OR IGNORE INTO post_categories (post_id, category_type)
                VALUES (?, ?)
            ''', (post_id, category_type))
            
            success = cursor.rowcount > 0
            
        self._track_query('add_category_to_post', time.time() - start_time)
        return success

    def remove_category_from_post(self, post_id: int, category_type: str) -> bool:
        """Remove category from post"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM post_categories 
                WHERE post_id = ? AND category_type = ?
            ''', (post_id, category_type))
            
            success = cursor.rowcount > 0
            
        self._track_query('remove_category_from_post', time.time() - start_time)
        return success

    def get_posts_by_platform(self, platform_name: str, limit: int = 50) -> List[Dict]:
        """Get posts by platform name"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT id FROM platforms WHERE name = ?', (platform_name,))
            result = cursor.fetchone()
            if not result:
                return []
            
            platform_id = result[0]
            return self.get_posts_with_media(platform_id=platform_id, limit=limit)

    def get_platform_statistics(self) -> Dict:
        """Get posts statistics by platform"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    pl.display_name,
                    COUNT(p.id) as post_count,
                    COUNT(m.id) as media_count,
                    COUNT(CASE WHEN p.is_carousel THEN 1 END) as carousel_count
                FROM platforms pl
                LEFT JOIN posts p ON pl.id = p.platform_id AND p.deleted_at IS NULL
                LEFT JOIN media m ON p.id = m.post_id
                GROUP BY pl.id, pl.display_name
                HAVING post_count > 0
                ORDER BY post_count DESC
            ''')
            
            stats = {}
            for row in cursor.fetchall():
                stats[row[0]] = {
                    'posts': row[1],
                    'media_files': row[2],
                    'carousels': row[3]
                }
            
        self._track_query('get_platform_statistics', time.time() - start_time)
        return stats

    def create_downloader_mapping(self, media_id: int, download_item_id: int, external_db_source: str) -> bool:
        """Create mapping between media and external downloader"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT OR IGNORE INTO downloader_mapping (media_id, download_item_id, external_db_source)
                VALUES (?, ?, ?)
            ''', (media_id, download_item_id, external_db_source))
            
            success = cursor.rowcount > 0
            
        self._track_query('create_downloader_mapping', time.time() - start_time)
        return success