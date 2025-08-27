"""
Instagram Populator - Platform-Specific Population Logic for Instagram  
======================================================================

Handles Instagram-specific population logic including:
- 4K Stogram database integration
- Instagram content types (feed, reels, stories, highlights)
- Saved content handling
"""

from typing import Dict, List, Optional, Any, Callable
import logging
from .base_populator import BasePopulator

logger = logging.getLogger(__name__)


class InstagramPopulator(BasePopulator):
    """Instagram-specific population implementation"""
    
    @property
    def platform_name(self) -> str:
        return "instagram"
    
    @property
    def supported_sources(self) -> List[str]:
        return ['db', 'organized']
    
    def get_last_processed_id(self, source: str) -> tuple[Any, List[str]]:
        """
        Get last processed Instagram ID for incremental population.
        
        Instagram uses 4K Stogram database structure.
        """
        missing_files = []
        
        try:
            if source != 'db':
                return None, missing_files
            
            # Get last processed ID from downloader_mapping  
            with self.db.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT MAX(dm.download_item_id) 
                    FROM downloader_mapping dm
                    WHERE dm.external_db_source = '4k_stogram'
                ''')
                
                row = cursor.fetchone()
                if row and row[0]:
                    last_id = row[0]
                    logger.info(f"🔍 Found last processed Instagram ID: {last_id}")
                    return last_id, missing_files
                else:
                    logger.info(f"🆕 No previous Instagram records found, starting fresh")
                    return None, missing_files
        
        except Exception as e:
            logger.error(f"Error getting last processed Instagram ID: {e}")
            return None, missing_files
    
    def extract_videos(self, source: str, limit: Optional[int], last_processed_id: Any) -> List[Dict]:
        """Extract Instagram content from 4K Stogram database"""
        
        if source == 'db':
            # Extract from 4K Stogram database
            if not self.external_sources.instagram_handler or not self.external_sources.instagram_handler.is_available():
                logger.error("Instagram handler not available") 
                return []
            
            return self.external_sources.instagram_handler.extract_videos(
                limit=limit
                # Note: Instagram handler may need updates for incremental support
            )
            
        elif source == 'organized':
            # Extract from organized folder structure
            if not self.external_sources.organized_handler or not self.external_sources.organized_handler.is_available():
                logger.error("Organized handler not available")
                return []
            
            return self.external_sources.organized_handler.extract_videos(
                platform_filter='instagram',
                limit=limit
            )
        
        else:
            logger.error(f"Unsupported source for Instagram: {source}")
            return []
    
    def process_videos(self, videos: List[Dict], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Process Instagram content with platform-specific logic.
        
        Handles:
        - Multiple content types (feed, reels, stories, highlights)
        - Saved content collections
        - Instagram-specific metadata
        """
        
        posts_created = 0
        posts_skipped = 0
        media_created = 0
        creators_created = 0
        subscriptions_created = 0
        errors = []
        
        # Track unique entities
        processed_creators = set()
        processed_subscriptions = set()
        
        logger.info(f"📸 Processing {len(videos)} Instagram items...")
        
        for video_data in videos:
            try:
                # Process single Instagram item
                post_id = self.external_sources._process_4k_stogram_video(video_data)
                
                if post_id:
                    # Post was created successfully
                    posts_created += 1
                    
                    # Count media (Instagram may have carousel posts)
                    if video_data.get('is_carousel') and video_data.get('carousel_items'):
                        media_created += len(video_data['carousel_items'])
                    else:
                        media_created += 1
                    
                    # Track creators and subscriptions
                    creator_name = video_data.get('creator_name')
                    subscription_name = video_data.get('subscription_name')
                    
                    if creator_name and creator_name not in processed_creators:
                        processed_creators.add(creator_name)
                        creators_created += 1
                    
                    if subscription_name and subscription_name not in processed_subscriptions:
                        processed_subscriptions.add(subscription_name)
                        subscriptions_created += 1
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(f"Created Instagram post {post_id}")
                        
                elif post_id is None:
                    # Post was skipped (duplicate)
                    posts_skipped += 1
                    logger.debug(f"Skipped duplicate Instagram post: {video_data.get('file_path', 'unknown')}")
                
            except Exception as e:
                error_msg = f"Error processing Instagram item {video_data.get('file_path', 'unknown')}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        # Build results
        result = {
            'videos_added': posts_created,
            'videos_updated': 0,
            'posts_created': posts_created,
            'posts_skipped': posts_skipped,
            'media_created': media_created,
            'creators_created': creators_created,
            'subscriptions_created': subscriptions_created,
            'errors': len(errors),
            'error_details': errors[:5] if errors else [],
            'message': (
                f"Instagram population completed: {posts_created} posts, "
                f"{media_created} media, {creators_created} creators, "
                f"{subscriptions_created} subscriptions"
                + (f", {posts_skipped} duplicates skipped" if posts_skipped > 0 else "")
                + (f", {len(errors)} errors" if errors else "")
            )
        }
        
        return result