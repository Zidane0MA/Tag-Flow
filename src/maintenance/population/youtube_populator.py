"""
YouTube Populator - Platform-Specific Population Logic for YouTube & Similar Platforms
=====================================================================================

Handles YouTube and similar platforms (Bilibili, Facebook, Twitter) that use:
- Integer ID handling for incremental population  
- 4K Video Downloader database structure
- Playlist vs Account subscription types
"""

from typing import Dict, List, Optional, Any, Callable
import logging
from .base_populator import BasePopulator

logger = logging.getLogger(__name__)


class YouTubePopulator(BasePopulator):
    """YouTube-specific population implementation (also handles Bilibili, Facebook, Twitter)"""
    
    @property
    def platform_name(self) -> str:
        return "youtube"  # Base name, actual platform determined by data
    
    @property  
    def supported_sources(self) -> List[str]:
        return ['db', 'organized']
    
    def get_last_processed_id(self, source: str) -> tuple[Any, List[str]]:
        """
        Get last processed YouTube ID (integer type) for incremental population.
        
        YouTube platforms use integer download_item_id values.
        """
        missing_files = []
        
        try:
            if source != 'db':
                return 0, missing_files
            
            # Get last processed integer ID from downloader_mapping
            with self.db.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT MAX(dm.download_item_id) 
                    FROM downloader_mapping dm
                    WHERE dm.external_db_source = '4k_youtube'
                ''')
                
                row = cursor.fetchone()
                if row and row[0]:
                    last_id = int(row[0])
                    logger.info(f"🔍 Found last processed YouTube ID: {last_id}")
                    return last_id, missing_files
                else:
                    logger.info(f"🆕 No previous YouTube records found, starting from 0")
                    return 0, missing_files
        
        except Exception as e:
            logger.error(f"Error getting last processed YouTube ID: {e}")
            return 0, missing_files
    
    def extract_videos(self, source: str, limit: Optional[int], last_processed_id: Any) -> List[Dict]:
        """Extract YouTube videos from 4K Video Downloader database"""
        
        if source == 'db':
            # Extract from 4K Video Downloader database
            if not self.external_sources.youtube_handler or not self.external_sources.youtube_handler.is_available():
                logger.error("YouTube handler not available")
                return []
            
            # Extract from all YouTube-compatible platforms
            all_videos = []
            platforms = ['youtube', 'bilibili', 'facebook', 'twitter']
            
            for platform in platforms:
                platform_videos = self.external_sources.youtube_handler.extract_by_platform(
                    platform=platform,
                    limit=limit,
                    min_download_item_id=last_processed_id
                )
                all_videos.extend(platform_videos)
                
                if limit and len(all_videos) >= limit:
                    all_videos = all_videos[:limit]
                    break
            
            return all_videos
            
        elif source == 'organized':
            # Extract from organized folder structure
            if not self.external_sources.organized_handler or not self.external_sources.organized_handler.is_available():
                logger.error("Organized handler not available")
                return []
            
            # Extract from all YouTube-compatible platforms
            all_videos = []
            platforms = ['youtube', 'bilibili', 'facebook', 'twitter']
            
            for platform in platforms:
                platform_videos = self.external_sources.organized_handler.extract_videos(
                    platform_filter=platform,
                    limit=limit
                )
                all_videos.extend(platform_videos)
                
                if limit and len(all_videos) >= limit:
                    all_videos = all_videos[:limit]
                    break
            
            return all_videos
        
        else:
            logger.error(f"Unsupported source for YouTube: {source}")
            return []
    
    def process_videos(self, videos: List[Dict], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Process YouTube videos with platform-specific logic.
        
        Handles:
        - Multiple platforms (YouTube, Bilibili, Facebook, Twitter)
        - Integer ID mapping for downloader_mapping
        - Account vs Playlist subscription types
        """
        
        posts_created = 0
        posts_skipped = 0
        media_created = 0
        creators_created = 0
        subscriptions_created = 0
        errors = []
        
        # Track unique entities to count new ones
        processed_creators = set()
        processed_subscriptions = set()
        
        # Group videos by platform for processing
        platform_groups = {}
        for video in videos:
            platform = video.get('platform', 'youtube')
            if platform not in platform_groups:
                platform_groups[platform] = []
            platform_groups[platform].append(video)
        
        logger.info(f"🎬 Processing YouTube-family videos: {dict((k, len(v)) for k, v in platform_groups.items())}")
        
        for platform, platform_videos in platform_groups.items():
            logger.info(f"📺 Processing {len(platform_videos)} {platform} videos...")
            
            for video_data in platform_videos:
                try:
                    # Process single YouTube-family video
                    post_id = self.external_sources._process_4k_youtube_video(video_data)
                    
                    if post_id:
                        # Post was created successfully
                        posts_created += 1
                        media_created += 1  # YouTube typically has 1 media per post
                        
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
                            progress_callback(f"Created {platform} post {post_id}")
                            
                    elif post_id is None:
                        # Post was skipped (duplicate)
                        posts_skipped += 1
                        logger.debug(f"Skipped duplicate {platform} post: {video_data.get('file_path', 'unknown')}")
                    
                except Exception as e:
                    error_msg = f"Error processing {platform} video {video_data.get('file_path', 'unknown')}: {e}"
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
            'platforms_processed': list(platform_groups.keys()),
            'message': (
                f"YouTube-family population completed: {posts_created} posts, "
                f"{media_created} media, {creators_created} creators, "
                f"{subscriptions_created} subscriptions across {len(platform_groups)} platforms"
                + (f", {posts_skipped} duplicates skipped" if posts_skipped > 0 else "")
                + (f", {len(errors)} errors" if errors else "")
            )
        }
        
        return result