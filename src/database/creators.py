"""
Tag-Flow V2 - Creator Management
Creator operations with hierarchy support
"""

import time
from typing import Dict, List, Optional
from .base import DatabaseBase
import logging

logger = logging.getLogger(__name__)


class CreatorOperations(DatabaseBase):
    """Creator management with hierarchy and URL support"""
    
    def create_creator(self, name: str, parent_creator_id: int = None, 
                      is_primary: bool = True, alias_type: str = 'main') -> int:
        """Create new creator (with hierarchy support)"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO creators (name, parent_creator_id, is_primary, alias_type)
                VALUES (?, ?, ?, ?)
            ''', (name, parent_creator_id, is_primary, alias_type))
            creator_id = cursor.lastrowid
            
            self._track_query('create_creator', time.time() - start_time)
            
            if parent_creator_id:
                logger.debug(f"Secondary creator created with ID {creator_id}: {name} "
                           f"(parent: {parent_creator_id}, type: {alias_type})")
            else:
                logger.debug(f"Primary creator created with ID {creator_id}: {name}")
            return creator_id
    
    def get_creator_by_name(self, name: str) -> Optional[Dict]:
        """Get creator by name"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM creators WHERE name = ?', (name,))
            row = cursor.fetchone()
            
            self._track_query('get_creator_by_name', time.time() - start_time)
            return self._format_creator_row(row) if row else None
    
    def get_creator_with_urls(self, creator_id: int) -> Optional[Dict]:
        """Get creator with URLs by platform"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            # Get creator data
            cursor = conn.execute('SELECT * FROM creators WHERE id = ?', (creator_id,))
            creator_row = cursor.fetchone()
            if not creator_row:
                return None
                
            creator = self._format_creator_row(creator_row)
            
            # Get URLs by platform
            cursor = conn.execute('''
                SELECT platform, url 
                FROM creator_urls 
                WHERE creator_id = ?
            ''', (creator_id,))
            
            creator['urls'] = {}
            for row in cursor.fetchall():
                creator['urls'][row[0]] = {
                    'url': row[1]
                }
            
            self._track_query('get_creator_with_urls', time.time() - start_time)
            return creator
    
    def add_creator_url(self, creator_id: int, platform: str, url: str) -> bool:
        """Add creator URL for platform"""
        self._ensure_initialized()
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO creator_urls (creator_id, platform, url)
                    VALUES (?, ?, ?)
                ''', (creator_id, platform, url))
                
                self._track_query('add_creator_url', time.time() - start_time)
                logger.debug(f"URL added for creator {creator_id} on {platform}: {url}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding creator URL: {e}")
            return False
    
    # --- CREATOR HIERARCHY MANAGEMENT (SECONDARY ACCOUNTS) ---
    
    def link_creator_as_secondary(self, secondary_creator_id: int, primary_creator_id: int, 
                                 alias_type: str = 'secondary') -> bool:
        """Link creator as secondary account of another"""
        self._ensure_initialized()
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                # Verify primary creator exists and is actually primary
                cursor = conn.execute('''
                    SELECT id, is_primary, parent_creator_id FROM creators WHERE id = ?
                ''', (primary_creator_id,))
                primary_creator = cursor.fetchone()
                
                if not primary_creator:
                    logger.error(f"Primary creator {primary_creator_id} not found")
                    return False
                
                # If "primary" creator is actually secondary, use its parent
                if not primary_creator[1] and primary_creator[2]:  # is_primary=False and has parent
                    actual_primary_id = primary_creator[2]
                    logger.info(f"Redirecting link: {primary_creator_id} is secondary, using parent {actual_primary_id}")
                    primary_creator_id = actual_primary_id
                
                # Update secondary creator
                cursor = conn.execute('''
                    UPDATE creators 
                    SET parent_creator_id = ?, is_primary = FALSE, alias_type = ?
                    WHERE id = ?
                ''', (primary_creator_id, alias_type, secondary_creator_id))
                
                success = cursor.rowcount > 0
                
                self._track_query('link_creator_as_secondary', time.time() - start_time)
                
                if success:
                    logger.info(f"Creator {secondary_creator_id} linked as {alias_type} of {primary_creator_id}")
                else:
                    logger.error(f"Could not link creator {secondary_creator_id}")
                
                return success
                
        except Exception as e:
            logger.error(f"Error linking creator as secondary: {e}")
            return False
    
    def unlink_secondary_creator(self, secondary_creator_id: int) -> bool:
        """Unlink secondary creator (make it primary)"""
        self._ensure_initialized()
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    UPDATE creators 
                    SET parent_creator_id = NULL, is_primary = TRUE, alias_type = 'main'
                    WHERE id = ? AND is_primary = FALSE
                ''', (secondary_creator_id,))
                
                success = cursor.rowcount > 0
                
                self._track_query('unlink_secondary_creator', time.time() - start_time)
                
                if success:
                    logger.info(f"Creator {secondary_creator_id} unlinked and made primary")
                else:
                    logger.warning(f"Creator {secondary_creator_id} not found or already primary")
                
                return success
                
        except Exception as e:
            logger.error(f"Error unlinking secondary creator: {e}")
            return False
    
    def get_creator_with_secondaries(self, creator_id: int) -> Optional[Dict]:
        """Get creator with all secondary accounts"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            # Get main creator
            cursor = conn.execute('SELECT * FROM creators WHERE id = ?', (creator_id,))
            creator_row = cursor.fetchone()
            if not creator_row:
                return None
            
            creator = self._format_creator_row(creator_row)
            
            # If this is a secondary creator, get the primary one instead
            if not creator['is_primary'] and creator['parent_creator_id']:
                return self.get_creator_with_secondaries(creator['parent_creator_id'])
            
            # Get secondary accounts
            cursor = conn.execute('''
                SELECT * FROM creators 
                WHERE parent_creator_id = ? AND is_primary = FALSE
                ORDER BY alias_type, name
            ''', (creator_id,))
            
            secondary_accounts = []
            for row in cursor.fetchall():
                secondary = self._format_creator_row(row)
                secondary_accounts.append(secondary)
            
            creator['secondary_accounts'] = secondary_accounts
            creator['total_accounts'] = 1 + len(secondary_accounts)
            
            self._track_query('get_creator_with_secondaries', time.time() - start_time)
            return creator
    
    def get_primary_creator_for_video(self, video_id: int) -> Optional[Dict]:
        """Get primary creator for a video (resolving hierarchy)"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT c.*, v.creator_id as original_creator_id
                FROM videos v
                JOIN creators c ON v.creator_id = c.id
                WHERE v.id = ?
            ''', (video_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            creator = self._format_creator_row(row)
            
            # If this is a secondary creator, get the primary one
            if not creator['is_primary'] and creator['parent_creator_id']:
                cursor = conn.execute('SELECT * FROM creators WHERE id = ?', (creator['parent_creator_id'],))
                primary_row = cursor.fetchone()
                if primary_row:
                    primary_creator = self._format_creator_row(primary_row)
                    primary_creator['resolved_from_secondary'] = True
                    primary_creator['secondary_creator_id'] = creator['id']
                    primary_creator['secondary_creator_name'] = creator['name']
                    
                    self._track_query('get_primary_creator_for_video', time.time() - start_time)
                    return primary_creator
            
            creator['resolved_from_secondary'] = False
            
            self._track_query('get_primary_creator_for_video', time.time() - start_time)
            return creator
    
    def search_creators_with_hierarchy(self, search_term: str) -> List[Dict]:
        """Search creators including hierarchy information"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT c.*, 
                       p.name as parent_name,
                       (SELECT COUNT(*) FROM creators WHERE parent_creator_id = c.id) as secondary_count
                FROM creators c
                LEFT JOIN creators p ON c.parent_creator_id = p.id
                WHERE c.name LIKE ?
                ORDER BY c.is_primary DESC, c.name
            ''', (f'%{search_term}%',))
            
            results = []
            for row in cursor.fetchall():
                creator = self._format_creator_row(row)
                creator['parent_name'] = row['parent_name']
                creator['secondary_count'] = row['secondary_count']
                results.append(creator)
            
            self._track_query('search_creators_with_hierarchy', time.time() - start_time)
            return results
    
    def get_creator_hierarchy_stats(self, creator_id: int) -> Dict:
        """Get hierarchy statistics for creator"""
        self._ensure_initialized()
        start_time = time.time()
        
        stats = {
            'video_count': 0,
            'platform_distribution': {},
            'secondary_accounts': [],
            'total_videos_including_secondaries': 0
        }
        
        with self.get_connection() as conn:
            # Get creator info
            creator = self.get_creator_with_secondaries(creator_id)
            if not creator:
                return stats
            
            # Video count for primary creator
            cursor = conn.execute('''
                SELECT COUNT(*) FROM videos 
                WHERE creator_id = ? AND deleted_at IS NULL
            ''', (creator_id,))
            stats['video_count'] = cursor.fetchone()[0]
            
            # Platform distribution for primary creator
            cursor = conn.execute('''
                SELECT platform, COUNT(*) as count
                FROM videos 
                WHERE creator_id = ? AND deleted_at IS NULL
                GROUP BY platform
            ''', (creator_id,))
            stats['platform_distribution'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Secondary accounts stats
            secondary_ids = [creator_id]  # Include primary
            for secondary in creator.get('secondary_accounts', []):
                secondary_info = {
                    'id': secondary['id'],
                    'name': secondary['name'],
                    'alias_type': secondary['alias_type'],
                    'video_count': 0
                }
                
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM videos 
                    WHERE creator_id = ? AND deleted_at IS NULL
                ''', (secondary['id'],))
                secondary_info['video_count'] = cursor.fetchone()[0]
                
                stats['secondary_accounts'].append(secondary_info)
                secondary_ids.append(secondary['id'])
            
            # Total videos including all secondaries
            if len(secondary_ids) > 1:
                placeholders = ','.join(['?' for _ in secondary_ids])
                cursor = conn.execute(f'''
                    SELECT COUNT(*) FROM videos 
                    WHERE creator_id IN ({placeholders}) AND deleted_at IS NULL
                ''', secondary_ids)
                stats['total_videos_including_secondaries'] = cursor.fetchone()[0]
            else:
                stats['total_videos_including_secondaries'] = stats['video_count']
        
        self._track_query('get_creator_hierarchy_stats', time.time() - start_time)
        return stats
    
    def get_unique_creators(self) -> List[str]:
        """Get list of unique creator names"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT DISTINCT name 
                FROM creators 
                WHERE is_primary = TRUE
                ORDER BY name
            ''')
            creators = [row[0] for row in cursor.fetchall()]
        
        self._track_query('get_unique_creators', time.time() - start_time)
        return creators