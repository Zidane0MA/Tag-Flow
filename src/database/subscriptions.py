"""
Tag-Flow V2 - Subscription Management
Subscription and video list operations
"""

import time
from typing import Dict, List, Optional
from .base import DatabaseBase
import logging

logger = logging.getLogger(__name__)


class SubscriptionOperations(DatabaseBase):
    """Subscription and video list management"""
    
    def create_subscription(self, name: str, platform_id: int, subscription_type: str, 
                          have_account: bool = False, creator_id: int = None, 
                          subscription_url: str = None, external_uuid: str = None) -> int:
        """Create new subscription"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO subscriptions (name, platform_id, subscription_type, have_account, 
                                         creator_id, subscription_url, external_uuid)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, platform_id, subscription_type, have_account, creator_id, subscription_url, external_uuid))
            subscription_id = cursor.lastrowid
            
            self._track_query('create_subscription', time.time() - start_time)
            logger.debug(f"Subscription created with ID {subscription_id}: {name} ({subscription_type})")
            return subscription_id
    
    def get_subscription_by_name_and_platform(self, name: str, platform: str, type: str = None) -> Optional[Dict]:
        """Get subscription by name and platform"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            if type:
                cursor = conn.execute('''
                    SELECT * FROM subscriptions 
                    WHERE name = ? AND platform = ? AND type = ?
                ''', (name, platform, type))
            else:
                cursor = conn.execute('''
                    SELECT * FROM subscriptions 
                    WHERE name = ? AND platform = ?
                ''', (name, platform))
            
            row = cursor.fetchone()
            
            self._track_query('get_subscription_by_name_and_platform', time.time() - start_time)
            return self._format_subscription_row(row) if row else None
    
    def get_subscriptions_by_creator(self, creator_id: int) -> List[Dict]:
        """Get all subscriptions for a creator"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM subscriptions 
                WHERE creator_id = ?
                ORDER BY platform, type, name
            ''', (creator_id,))
            
            subscriptions = [self._format_subscription_row(row) for row in cursor.fetchall()]
            
            self._track_query('get_subscriptions_by_creator', time.time() - start_time)
            return subscriptions
    
    def get_subscriptions_by_platform_and_type(self, platform: str, type: str) -> List[Dict]:
        """Get subscriptions by platform and type"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM subscriptions 
                WHERE platform = ? AND type = ?
                ORDER BY name
            ''', (platform, type))
            
            subscriptions = [self._format_subscription_row(row) for row in cursor.fetchall()]
            
            self._track_query('get_subscriptions_by_platform_and_type', time.time() - start_time)
            return subscriptions
    
    # --- VIDEO LIST MANAGEMENT ---
    
    def add_video_to_list(self, video_id: int, list_type: str) -> bool:
        """Add video to specific list"""
        self._ensure_initialized()
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO video_lists (video_id, list_type)
                    VALUES (?, ?)
                ''', (video_id, list_type))
                
                self._track_query('add_video_to_list', time.time() - start_time)
                return True
                
        except Exception as e:
            logger.error(f"Error adding video {video_id} to list {list_type}: {e}")
            return False
    
    def get_video_lists(self, video_id: int) -> List[str]:
        """Get all lists that a video belongs to"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT list_type FROM video_lists 
                WHERE video_id = ?
            ''', (video_id,))
            
            lists = [row[0] for row in cursor.fetchall()]
            
            self._track_query('get_video_lists', time.time() - start_time)
            return lists
    
    def get_videos_by_list_type(self, list_type: str, platform: str = None, limit: int = None) -> List[Dict]:
        """Get videos by list type"""
        self._ensure_initialized()
        start_time = time.time()
        
        query = '''
            SELECT v.*, vl.list_type, c.name as creator_name
            FROM videos v
            JOIN video_lists vl ON v.id = vl.video_id
            LEFT JOIN creators c ON v.creator_id = c.id
            WHERE vl.list_type = ? AND v.deleted_at IS NULL
        '''
        params = [list_type]
        
        if platform:
            query += ' AND v.platform = ?'
            params.append(platform)
        
        query += ' ORDER BY v.created_at DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            videos = [self._format_video_row(row) for row in cursor.fetchall()]
            
            self._track_query('get_videos_by_list_type', time.time() - start_time)
            return videos
    
    def get_videos_by_creator_with_metadata(self, creator_id: int, platform: str = None, limit: int = None) -> List[Dict]:
        """Get videos by creator with subscription metadata"""
        self._ensure_initialized()
        start_time = time.time()
        
        query = '''
            SELECT v.*, c.name as creator_name, s.name as subscription_name, s.type as subscription_type
            FROM videos v
            LEFT JOIN creators c ON v.creator_id = c.id
            LEFT JOIN subscriptions s ON v.subscription_id = s.id
            WHERE v.creator_id = ? AND v.deleted_at IS NULL
        '''
        params = [creator_id]
        
        if platform:
            query += ' AND v.platform = ?'
            params.append(platform)
        
        query += ' ORDER BY v.created_at DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            videos = [self._format_video_row(row) for row in cursor.fetchall()]
            
            self._track_query('get_videos_by_creator_with_metadata', time.time() - start_time)
            return videos
    
    def get_videos_by_subscription_with_metadata(self, subscription_id: int, limit: int = None) -> List[Dict]:
        """Get videos by subscription with metadata"""
        self._ensure_initialized()
        start_time = time.time()
        
        query = '''
            SELECT v.*, c.name as creator_name, s.name as subscription_name, s.type as subscription_type
            FROM videos v
            LEFT JOIN creators c ON v.creator_id = c.id
            LEFT JOIN subscriptions s ON v.subscription_id = s.id
            WHERE v.subscription_id = ? AND v.deleted_at IS NULL
            ORDER BY v.created_at DESC
        '''
        params = [subscription_id]
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            videos = [self._format_video_row(row) for row in cursor.fetchall()]
            
            self._track_query('get_videos_by_subscription_with_metadata', time.time() - start_time)
            return videos
    
    def remove_video_from_list(self, video_id: int, list_type: str) -> bool:
        """Remove video from specific list"""
        self._ensure_initialized()
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    DELETE FROM video_lists 
                    WHERE video_id = ? AND list_type = ?
                ''', (video_id, list_type))
                
                success = cursor.rowcount > 0
                
                self._track_query('remove_video_from_list', time.time() - start_time)
                
                if success:
                    logger.debug(f"Video {video_id} removed from list {list_type}")
                
                return success
                
        except Exception as e:
            logger.error(f"Error removing video {video_id} from list {list_type}: {e}")
            return False
    
    def get_list_statistics(self) -> Dict:
        """Get statistics about video lists"""
        self._ensure_initialized()
        start_time = time.time()
        
        stats = {}
        
        with self.get_connection() as conn:
            # Count videos per list type
            cursor = conn.execute('''
                SELECT vl.list_type, COUNT(*) as count
                FROM video_lists vl
                JOIN videos v ON vl.video_id = v.id
                WHERE v.deleted_at IS NULL
                GROUP BY vl.list_type
                ORDER BY count DESC
            ''')
            
            stats['videos_per_list'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Count videos per subscription type
            cursor = conn.execute('''
                SELECT s.type, COUNT(*) as count
                FROM videos v
                JOIN subscriptions s ON v.subscription_id = s.id
                WHERE v.deleted_at IS NULL
                GROUP BY s.type
                ORDER BY count DESC
            ''')
            
            stats['videos_per_subscription_type'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Count videos per platform-subscription combination
            cursor = conn.execute('''
                SELECT v.platform, s.type, COUNT(*) as count
                FROM videos v
                JOIN subscriptions s ON v.subscription_id = s.id
                WHERE v.deleted_at IS NULL
                GROUP BY v.platform, s.type
                ORDER BY count DESC
            ''')
            
            platform_subscription_stats = {}
            for row in cursor.fetchall():
                platform = row[0]
                sub_type = row[1]
                count = row[2]
                
                if platform not in platform_subscription_stats:
                    platform_subscription_stats[platform] = {}
                platform_subscription_stats[platform][sub_type] = count
            
            stats['platform_subscription_distribution'] = platform_subscription_stats
        
        self._track_query('get_list_statistics', time.time() - start_time)
        return stats
    
    def get_subscription_statistics(self) -> Dict:
        """Get detailed subscription statistics"""
        self._ensure_initialized()
        start_time = time.time()
        
        stats = {}
        
        with self.get_connection() as conn:
            # Total subscriptions
            cursor = conn.execute('SELECT COUNT(*) FROM subscriptions')
            stats['total_subscriptions'] = cursor.fetchone()[0]
            
            # Subscriptions by platform
            cursor = conn.execute('''
                SELECT platform, COUNT(*) as count
                FROM subscriptions
                GROUP BY platform
                ORDER BY count DESC
            ''')
            stats['by_platform'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Subscriptions by type
            cursor = conn.execute('''
                SELECT type, COUNT(*) as count
                FROM subscriptions
                GROUP BY type
                ORDER BY count DESC
            ''')
            stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Subscriptions with most videos
            cursor = conn.execute('''
                SELECT s.name, s.platform, s.type, COUNT(v.id) as video_count
                FROM subscriptions s
                LEFT JOIN videos v ON s.id = v.subscription_id AND v.deleted_at IS NULL
                GROUP BY s.id
                ORDER BY video_count DESC
                LIMIT 20
            ''')
            
            top_subscriptions = []
            for row in cursor.fetchall():
                top_subscriptions.append({
                    'name': row[0],
                    'platform': row[1],
                    'type': row[2],
                    'video_count': row[3]
                })
            
            stats['top_subscriptions'] = top_subscriptions
        
        self._track_query('get_subscription_statistics', time.time() - start_time)
        return stats

    # === NEW DATABASE STRUCTURE METHODS ===
    
    def get_platform_id(self, platform_name):
        """Get platform ID by name"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT id FROM platforms WHERE name = ?', (platform_name,))
            result = cursor.fetchone()
            return result[0] if result else None

    def create_or_get_subscription(self, name: str, platform_name: str, subscription_type: str, **kwargs) -> int:
        """Create or get subscription with platform (new structure)"""
        platform_id = self.get_platform_id(platform_name)
        if not platform_id:
            raise ValueError(f"Unknown platform: {platform_name}")
        
        with self.get_connection() as conn:
            # Check if subscription exists
            cursor = conn.execute('''
                SELECT id FROM subscriptions 
                WHERE name = ? AND platform_id = ? AND subscription_type = ?
            ''', (name, platform_id, subscription_type))
            
            result = cursor.fetchone()
            if result:
                return result[0]
            
            # Create new subscription using existing method
            return self.create_subscription(
                name=name,
                platform_id=platform_id,
                subscription_type=subscription_type,
                have_account=kwargs.get('have_account', False),
                creator_id=kwargs.get('creator_id'),
                subscription_url=kwargs.get('subscription_url'),
                external_uuid=kwargs.get('external_uuid')
            )