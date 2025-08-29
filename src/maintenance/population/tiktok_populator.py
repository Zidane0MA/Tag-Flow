"""
TikTok Populator - Platform-Specific Population Logic for TikTok
==============================================================

Handles all TikTok-specific population logic including:
- BLOB ID handling for incremental population
- Carousel post processing
- Download settings integration (liked, favorites, feed)
- Subscription type mapping
"""

from typing import Dict, List, Optional, Any, Callable
import logging
from .base_populator import BasePopulator

logger = logging.getLogger(__name__)


class TikTokPopulator(BasePopulator):
    """TikTok-specific population implementation"""
    
    @property
    def platform_name(self) -> str:
        return "tiktok"
    
    @property
    def supported_sources(self) -> List[str]:
        return ['db', 'organized']
    
    def get_last_processed_id(self, source: str, specific_platform: str = None) -> tuple[Any, List[str]]:
        """
        Get last processed TikTok ID (BLOB type) for incremental population.
        
        TikTok uses BLOB (UUID) IDs instead of integers, so we need special handling.
        """
        missing_files = []
        
        try:
            if source != 'db':
                return None, missing_files
            
            # Get last processed BLOB ID from downloader_mapping
            with self.db.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT dm.download_item_id 
                    FROM downloader_mapping dm
                    WHERE dm.external_db_source = '4k_tokkit'
                    ORDER BY dm.id DESC
                    LIMIT 1
                ''')
                
                row = cursor.fetchone()
                if row:
                    last_id = row[0]
                    logger.info(f"🔍 Found last processed TikTok ID: {last_id}")
                    return last_id, missing_files
                else:
                    logger.info(f"🆕 No previous TikTok records found, starting fresh")
                    return None, missing_files
        
        except Exception as e:
            logger.error(f"Error getting last processed TikTok ID: {e}")
            return None, missing_files
    
    def extract_videos(self, source: str, limit: Optional[int], last_processed_id: Any, specific_platform: str = None) -> List[Dict]:
        """Extract TikTok videos from 4K Tokkit database"""
        
        if source == 'db':
            # Extract from 4K Tokkit database
            if not self.external_sources.tiktok_handler or not self.external_sources.tiktok_handler.is_available():
                logger.error("TikTok handler not available")
                return []
            
            return self.external_sources.tiktok_handler.extract_videos(
                limit=limit,
                min_download_item_id=last_processed_id
            )
            
        elif source == 'organized':
            # Extract from organized folder structure  
            if not self.external_sources.organized_handler or not self.external_sources.organized_handler.is_available():
                logger.error("Organized handler not available")
                return []
            
            return self.external_sources.organized_handler.extract_videos(
                platform_filter='tiktok',
                limit=limit
            )
        
        else:
            logger.error(f"Unsupported source for TikTok: {source}")
            return []
    
    def process_videos(self, videos: List[Dict], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Process TikTok videos with platform-specific logic.
        
        Handles:
        - Carousel posts (multiple media items per post)
        - BLOB ID mapping for downloader_mapping
        - TikTok-specific subscription types
        """
        
        posts_created = 0
        media_created = 0
        creators_created = 0
        subscriptions_created = 0
        errors = []
        
        # Track unique entities to count new ones
        processed_creators = set()
        processed_subscriptions = set()
        
        # Filter out videos that already exist (by file_path) to avoid duplicates
        from src.database.posts import PostOperations
        post_ops = PostOperations()
        
        new_videos = post_ops.filter_existing_posts_by_file_path(videos)
        posts_skipped = len(videos) - len(new_videos)
        
        logger.info(f"📱 Processing {len(videos)} TikTok videos: {len(new_videos)} new, {posts_skipped} already exist")
        
        for i, video_data in enumerate(new_videos):
            try:
                # Process single TikTok video
                post_id = self.external_sources._process_4k_tokkit_video(video_data)
                
                if post_id:
                    # Post was created successfully
                    posts_created += 1
                    
                    # Count media items (handle carousels)
                    if video_data.get('is_carousel') and video_data.get('carousel_items'):
                        media_created += len(video_data['carousel_items'])
                    else:
                        media_created += 1
                    
                    # Track creators and subscriptions (only for successfully created posts)
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
                        progress_callback(f"Created TikTok post {post_id}")
                        
                elif post_id is None:
                    # This should not happen with new filtering, but handle just in case
                    logger.debug(f"Post creation returned None for: {video_data.get('file_path', 'unknown')}")
                
            except Exception as e:
                error_msg = f"Error processing TikTok video {video_data.get('file_path', 'unknown')}: {e}"
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
            'error_details': errors[:5] if errors else [],  # First 5 errors
            'message': (
                f"TikTok population completed: {posts_created} posts, "
                f"{media_created} media, {creators_created} creators, "
                f"{subscriptions_created} subscriptions"
                + (f", {posts_skipped} duplicates skipped" if posts_skipped > 0 else "")
                + (f", {len(errors)} errors" if errors else "")
            )
        }
        
        return result
    
    def _handle_tiktok_carousel(self, video_data: Dict) -> int:
        """
        Handle TikTok carousel post creation.
        
        TikTok carousels are grouped by base_id and contain multiple media items.
        This method ensures proper media ordering and primary media designation.
        """
        # This logic is already handled in the external_sources manager
        # via the _process_4k_tokkit_video method, but we could add
        # additional TikTok-specific processing here if needed
        
        return self.external_sources._process_4k_tokkit_video(video_data)
    
    def _validate_tiktok_data(self, video_data: Dict) -> bool:
        """Validate TikTok-specific data requirements"""
        required_fields = ['file_path', 'platform', 'creator_name']
        
        for field in required_fields:
            if not video_data.get(field):
                logger.warning(f"Missing required TikTok field: {field}")
                return False
        
        if video_data.get('platform') != 'tiktok':
            logger.warning(f"Invalid platform for TikTok populator: {video_data.get('platform')}")
            return False
        
        return True