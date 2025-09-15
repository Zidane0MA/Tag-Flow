"""
Tag-Flow V2 - External Sources Manager  
Updated for new posts → media database structure
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

from ..database.core import DatabaseCore
from .youtube import YouTube4KHandler
from .tiktok import TikTokTokkitHandler  
from .instagram import InstagramStogramHandler
from .organized import OrganizedFoldersHandler

logger = logging.getLogger(__name__)


class ExternalSourcesManager:
    """New external sources manager for posts → media structure"""
    
    def __init__(self, db_core: DatabaseCore = None, config=None):
        """Initialize with database core"""
        self.db_core = db_core or DatabaseCore()
        self.config = config or {}
        self.logger = logger
        
        # Initialize handlers
        self._init_handlers()
        
        # Category mapping logic
        self._category_mapping = {
            'youtube': self._categorize_youtube_content,
            'tiktok': self._categorize_tiktok_content,
            'instagram': self._categorize_instagram_content,
            'bilibili': self._categorize_bilibili_content,
            'facebook': self._categorize_facebook_content,
            'twitter': self._categorize_twitter_content
        }
    
    def _init_handlers(self):
        """Initialize all platform handlers"""
        try:
            # Get paths from config or environment
            youtube_db = os.getenv('EXTERNAL_YOUTUBE_DB') or self.config.get('youtube_db')
            tiktok_db = os.getenv('EXTERNAL_TIKTOK_DB') or self.config.get('tiktok_db')
            instagram_db = os.getenv('EXTERNAL_INSTAGRAM_DB') or self.config.get('instagram_db')
            organized_path = os.getenv('ORGANIZED_BASE_PATH') or self.config.get('organized_path')
            
            # Initialize handlers (convert strings to Path objects)
            self.youtube_handler = YouTube4KHandler(Path(youtube_db)) if youtube_db else None
            self.tiktok_handler = TikTokTokkitHandler(Path(tiktok_db)) if tiktok_db else None
            self.instagram_handler = InstagramStogramHandler(Path(instagram_db)) if instagram_db else None
            self.organized_handler = OrganizedFoldersHandler(Path(organized_path)) if organized_path else None
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            raise

    def populate_from_4k_youtube(self, platform_filter=None, limit=None):
        """Populate from 4K Video Downloader using new structure"""
        if not self.youtube_handler or not self.youtube_handler.is_available():
            logger.warning("4K Video Downloader not available")
            return 0
        
        logger.info(f"Populating from 4K Video Downloader (platform: {platform_filter}, limit: {limit})")
        
        # Extract videos from 4K BD
        videos = self.youtube_handler.extract_videos(platform_filter=platform_filter, limit=limit)
        
        populated_count = 0
        
        for video_data in videos:
            try:
                # Process video through new structure
                self._process_4k_youtube_video(video_data)
                populated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process YouTube video {video_data.get('title', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Populated {populated_count} videos from 4K Video Downloader")
        return populated_count

    def _process_4k_youtube_video(self, video_data):
        """Process single video from 4K Video Downloader into new structure"""
        
        # Use database core's new methods
        from ..database.posts import PostOperations
        from ..database.creators import CreatorOperations
        from ..database.subscriptions import SubscriptionOperations
        
        post_ops = PostOperations()
        creator_ops = CreatorOperations()
        subscription_ops = SubscriptionOperations()
        
        # 1. Create or get creator
        creator_id = None
        if video_data.get('creator_name'):
            # Extract platform_creator_id from profile URL if available
            # Decode creator URL (4K Video Downloader provides encoded URLs)
            raw_creator_url = video_data.get('creator_url')
            decoded_creator_url = None
            if raw_creator_url:
                import urllib.parse
                decoded_creator_url = urllib.parse.unquote(raw_creator_url)
            
            platform_creator_id = self._extract_platform_creator_id(
                raw_creator_url, 
                video_data['platform']
            )
            
            creator_id = creator_ops.create_or_get_creator(
                name=video_data['creator_name'],
                platform_name=video_data['platform'],
                creator_name_source='db',
                profile_url=decoded_creator_url,
                platform_creator_id=platform_creator_id
            )
        
        # 2. Create or get subscription
        subscription_id = None
        subscription_type, is_account = self._determine_subscription_type_4k_youtube(video_data)
        
        if subscription_type:
            subscription_name = video_data.get('playlist_name') or video_data.get('creator_name', 'Unknown')
            
            # Normalize playlist names for consistency
            if subscription_type == 'playlist':
                subscription_name = self._normalize_youtube_playlist_name(subscription_name)
            
            # For account type, use creator name if no playlist name
            if subscription_type == 'account' and not video_data.get('playlist_name'):
                subscription_name = video_data.get('creator_name', 'Unknown')
            
            # Determine subscription URL based on type
            subscription_url = None
            subscription_creator_id = None
            
            if subscription_type == 'account':
                # For account subscriptions, use creator_url (channel URL)
                raw_subscription_url = video_data.get('creator_url') or video_data.get('channel_url')
                subscription_url = None
                if raw_subscription_url:
                    import urllib.parse
                    subscription_url = urllib.parse.unquote(raw_subscription_url)
                subscription_creator_id = creator_id  # Account always belongs to the creator
            elif subscription_type == 'playlist':
                # For playlist subscriptions, use playlist_url
                raw_subscription_url = video_data.get('playlist_url')
                subscription_url = None
                if raw_subscription_url:
                    import urllib.parse
                    subscription_url = urllib.parse.unquote(raw_subscription_url)
                # ALWAYS NULL for playlists - cannot reliably identify playlist owner from external DB data
                subscription_creator_id = None
            
            subscription_id = subscription_ops.create_or_get_subscription(
                name=subscription_name,
                platform_name=video_data['platform'],
                subscription_type=subscription_type,
                is_account=is_account,
                creator_id=subscription_creator_id,
                subscription_url=subscription_url,
                external_uuid=video_data.get('downloader_subscription_uuid')
            )
        
        # 3. Prepare post data
        post_data = {
            'platform_id': subscription_ops.get_platform_id(video_data['platform']),
            'platform_post_id': video_data.get('video_id'),
            'post_url': video_data.get('url'),
            'title_post': video_data.get('title'),
            'use_filename': False,  # YouTube doesn't need filename-based titles
            'creator_id': creator_id,
            'subscription_id': subscription_id,
            'download_date': int(video_data.get('timestampNs', 0) / 1_000_000_000) if video_data.get('timestampNs') else None
        }
        
        # 4. Prepare media data
        media_data = [{
            'file_path': video_data['file_path'],
            'file_name': video_data['file_name'],
            'thumbnail_path': video_data.get('thumbnail_path'),
            'file_size': video_data.get('file_size'),
            'duration_seconds': video_data.get('duration_seconds'),
            'media_type': 'video',
            'resolution_width': video_data.get('resolution_width'),
            'resolution_height': video_data.get('resolution_height'),
            'fps': video_data.get('fps')
        }]
        
        # 5. Determine categories
        category_types = self._categorize_youtube_content(video_data)
        
        # 6. Create post with media
        post_id, media_ids = post_ops.create_post_with_media(post_data, media_data, category_types)
        
        # 7. Create downloader mapping
        if media_ids:
            post_ops.create_downloader_mapping(media_ids[0], video_data.get('download_item_id'), '4k_youtube')
        
        return post_id

    def _normalize_youtube_playlist_name(self, playlist_name):
        """Normalize YouTube playlist names for consistency"""
        if not playlist_name:
            return playlist_name
            
        # Normalize common playlist names
        name_lower = playlist_name.lower().strip()
        
        # Liked videos variations
        if name_lower in ['liked videos', 'videos que me gustan', 'me gusta']:
            return 'Liked videos'
        
        # Watch later variations  
        elif name_lower in ['watch later', 'ver más tarde', 'ver mas tarde', 'watch later list']:
            return 'Watch Later'
            
        # Return original name if no normalization needed
        return playlist_name

    def _extract_platform_creator_id(self, profile_url, platform):
        """Extract platform-specific creator ID from profile URL
        
        Examples:
        - YouTube: http://www.youtube.com/@Frozen_mmd -> @Frozen_mmd
        - TikTok: https://www.tiktok.com/@username -> @username
        - Instagram: https://www.instagram.com/username -> username
        """
        if not profile_url:
            return None
            
        try:
            # Decode URL-encoded characters (4K Video Downloader provides encoded URLs)
            import urllib.parse
            decoded_url = urllib.parse.unquote(profile_url)
            profile_url = decoded_url
            if platform.lower() == 'youtube':
                # Extract from YouTube URLs: @username format
                if '@' in profile_url:
                    # Extract everything after the last @
                    parts = profile_url.split('@')
                    if len(parts) > 1:
                        username = parts[-1].split('/')[0].split('?')[0]  # Remove trailing path/params
                        return f"@{username}"
                        
            elif platform.lower() == 'tiktok':
                # Extract from TikTok URLs: @username format
                if '@' in profile_url:
                    parts = profile_url.split('@')
                    if len(parts) > 1:
                        username = parts[-1].split('/')[0].split('?')[0]
                        return f"@{username}"
                        
            elif platform.lower() == 'instagram':
                # Extract from Instagram URLs: username format (no @ prefix)
                if 'instagram.com/' in profile_url:
                    parts = profile_url.split('instagram.com/')
                    if len(parts) > 1:
                        username = parts[-1].split('/')[0].split('?')[0]
                        return username
                        
            # For other platforms or if extraction fails, return None
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting platform creator ID from {profile_url}: {e}")
            return None

    def _determine_subscription_type_4k_youtube(self, video_data):
        """Determine subscription type from 4K Video Downloader metadata
        
        Mapping based on 4K Apps to Subscriptions table:
        - type=5: account, is_account=TRUE (Creator's own content)
        - type=3: playlist, is_account=TRUE (Creator's playlists like Liked videos)
        """
        metadata_types = video_data.get('metadata_types', {})
        
        # Check for subscription indicators according to the mapping table
        if 5 in metadata_types:
            # Account subscription (type=5) - Creator's own content
            return 'account', True
        elif 3 in metadata_types:
            # Playlist subscription (type=3) - Creator's playlists (Liked videos, etc.)
            return 'playlist', True  # Changed to TRUE according to mapping table
        else:
            # Individual video - no subscription
            return None, False

    def populate_from_4k_tokkit(self, limit=None):
        """Populate from 4K Tokkit using new structure"""
        if not self.tiktok_handler or not self.tiktok_handler.is_available():
            logger.warning("4K Tokkit not available")
            return 0
        
        logger.info(f"Populating from 4K Tokkit (limit: {limit})")
        
        # Extract videos from 4K Tokkit
        videos = self.tiktok_handler.extract_videos(limit=limit)
        
        populated_count = 0
        
        for video_data in videos:
            try:
                self._process_4k_tokkit_video(video_data)
                populated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process TikTok video {video_data.get('description', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Populated {populated_count} videos from 4K Tokkit")
        return populated_count

    def populate_from_4k_stogram(self, limit=None):
        """Populate from 4K Stogram using new structure"""
        if not self.instagram_handler or not self.instagram_handler.is_available():
            logger.warning("4K Stogram not available")
            return 0
        
        logger.info(f"Populating from 4K Stogram (limit: {limit})")
        
        # Extract videos from 4K Stogram
        videos = self.instagram_handler.extract_videos(limit=limit)
        
        populated_count = 0
        
        for video_data in videos:
            try:
                self._process_4k_stogram_video(video_data)
                populated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process Instagram video {video_data.get('title', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Populated {populated_count} videos from 4K Stogram")
        return populated_count

    def get_all_videos_from_source(self, source: str, platform: str = None, limit: int = None, min_download_item_id: int = 0) -> List[Dict]:
        """Get all videos from specified source for database population"""
        all_videos = []
        
        if source == 'db':
            # From external databases (4K Apps)
            if platform is None:
                # All platforms
                if self.youtube_handler and self.youtube_handler.is_available():
                    videos = self.youtube_handler.extract_videos(limit=limit)
                    all_videos.extend(videos)
                if self.tiktok_handler and self.tiktok_handler.is_available():
                    videos = self.tiktok_handler.extract_videos(limit=limit)
                    all_videos.extend(videos)
                if self.instagram_handler and self.instagram_handler.is_available():
                    videos = self.instagram_handler.extract_videos(limit=limit)
                    all_videos.extend(videos)
            elif platform in ['youtube', 'bilibili', 'facebook', 'twitter']:
                # Platforms handled by YouTube handler (4K Video Downloader)
                if self.youtube_handler and self.youtube_handler.is_available():
                    videos = self.youtube_handler.extract_by_platform(platform, limit=limit, min_download_item_id=min_download_item_id)
                    all_videos.extend(videos)
            elif platform == 'tiktok':
                if self.tiktok_handler and self.tiktok_handler.is_available():
                    videos = self.tiktok_handler.extract_videos(limit=limit, min_download_item_id=min_download_item_id)
                    all_videos.extend(videos)
            elif platform == 'instagram':
                if self.instagram_handler and self.instagram_handler.is_available():
                    videos = self.instagram_handler.extract_videos(limit=limit)
                    all_videos.extend(videos)
                    
        elif source == 'organized':
            # From organized folder structure
            if self.organized_handler and self.organized_handler.is_available():
                videos = self.organized_handler.extract_videos(
                    platform_filter=platform, limit=limit
                )
                all_videos.extend(videos)
                
        return all_videos

    def _process_4k_tokkit_video(self, video_data):
        """Process single video from 4K Tokkit into new structure"""
        
        from ..database.posts import PostOperations
        from ..database.creators import CreatorOperations
        from ..database.subscriptions import SubscriptionOperations
        
        post_ops = PostOperations()
        creator_ops = CreatorOperations()
        subscription_ops = SubscriptionOperations()
        
        # 1. Create or get creator
        creator_name = video_data.get('creator_name') or video_data.get('authorName') or 'unknown_creator'
        creator_id = creator_ops.create_or_get_creator(
            name=creator_name,
            platform_name='tiktok',
            creator_name_source='db',
            profile_url=video_data.get('creator_url') or f"https://www.tiktok.com/@{creator_name}",
            platform_creator_id=f"@{creator_name}" if creator_name != 'unknown_creator' else None
        )
        
        # 2. Create or get subscription
        subscription_id = None
        subscription_name = video_data.get('subscription_name')
        subscription_type = video_data.get('subscription_type')
        
        if subscription_name and subscription_type:
            # Map subscription type according to 4K Apps mapping specification
            # TRUE: account, liked, saved (all belong to accounts)
            # FALSE: hashtag, music (not associated with accounts)
            is_account = subscription_type in ['account', 'liked', 'saved']
            
            # For liked/saved subscriptions, create the account owner creator
            subscription_creator_id = None
            if is_account:
                if subscription_type in ['liked', 'saved']:
                    # For liked/saved, subscription_name is the account name (without suffix)
                    # Create creator for the account that owns the liked/saved list
                    subscription_creator_id = creator_ops.create_or_get_creator(
                        name=subscription_name,
                        platform_name='tiktok',
                        creator_name_source='db',
                        profile_url=f"https://www.tiktok.com/@{subscription_name}",
                        platform_creator_id=f"@{subscription_name}"
                    )
                else:
                    # For account subscriptions, use the video's creator
                    subscription_creator_id = creator_id
            
            subscription_id = subscription_ops.create_or_get_subscription(
                name=subscription_name,
                platform_name='tiktok',
                subscription_type=subscription_type,
                is_account=is_account,
                creator_id=subscription_creator_id,
                subscription_url=video_data.get('subscription_url'),
                external_uuid=str(video_data.get('subscription_database_id')) if video_data.get('subscription_database_id') else None
            )
        
        # 3. Prepare post data with proper mapping
        title_from_content = video_data.get('title') or video_data.get('description')
        
        # Check if filename was used as title (either from handler or fallback logic)
        use_filename = video_data.get('title_is_filename', False)
        
        # Fallback logic for handlers that don't provide title_is_filename
        if not use_filename and (not title_from_content or title_from_content.strip() == ''):
            title_from_content = video_data.get('file_name', '').replace('.mp4', '').replace('.jpg', '').replace('.png', '')
            use_filename = True
        
        post_data = {
            'platform_id': subscription_ops.get_platform_id('tiktok'),
            'platform_post_id': str(video_data.get('id')),
            'post_url': video_data.get('post_url'),
            'title_post': title_from_content,
            'use_filename': use_filename,  # New field to track filename usage
            'creator_id': creator_id,
            'subscription_id': subscription_id,
            'publication_date': video_data.get('postingDate'),  # Already Unix timestamp
            'publication_date_source': '4k_bd' if video_data.get('postingDate') else None,
            'publication_date_confidence': None,  # Remove hardcoded 95, use NULL as requested
            'download_date': video_data.get('recordingDate')  # Already Unix timestamp
        }
        
        # 4. Prepare media data - handle carousel properly
        media_data = []
        
        if video_data.get('is_carousel') and video_data.get('carousel_items'):
            # This is a carousel post with multiple media items
            for carousel_item in video_data['carousel_items']:
                media_item = {
                    'file_path': carousel_item['file_path'],
                    'file_name': carousel_item['file_name'],
                    'media_type': carousel_item.get('content_type', 'video'),
                    'file_size': carousel_item.get('file_size', 0),
                    'duration_seconds': carousel_item.get('duration_seconds'),
                    'resolution_width': carousel_item.get('width'),
                    'resolution_height': carousel_item.get('height'),
                    'fps': None  # Not available in TikTok data
                }
                media_data.append(media_item)
        else:
            # Single media item
            media_item = {
                'file_path': video_data['file_path'],
                'file_name': video_data['file_name'],
                'media_type': video_data.get('content_type', 'video'),
                'file_size': video_data.get('file_size', 0),
                'duration_seconds': video_data.get('duration_seconds'),
                'resolution_width': video_data.get('width'),
                'resolution_height': video_data.get('height'),
                'fps': None  # Not available in TikTok data
            }
            media_data.append(media_item)
        
        # 5. Determine categories for TikTok (always 'videos' according to specification)
        category_types = ['videos']  # TikTok only has 'videos' category type
        
        # 6. Create post with media
        post_id, media_ids = post_ops.create_post_with_media(post_data, media_data, category_types)
        
        # 7. Create downloader mapping for each media
        if media_ids:
            if video_data.get('is_carousel') and video_data.get('carousel_items'):
                # For carousel, map each media to its corresponding carousel item
                for i, media_id in enumerate(media_ids):
                    if i < len(video_data['carousel_items']):
                        carousel_item = video_data['carousel_items'][i]
                        item_mapping = carousel_item.get('downloader_mapping', {})
                        download_item_id = item_mapping.get('download_item_id')
                        if download_item_id:
                            self._create_downloader_mapping(media_id, download_item_id, '4k_tokkit')
            else:
                # Single media item
                downloader_mapping = video_data.get('downloader_mapping', {})
                download_item_id = downloader_mapping.get('download_item_id')
                if download_item_id:
                    for media_id in media_ids:
                        self._create_downloader_mapping(media_id, download_item_id, '4k_tokkit')
        
        return post_id
    
    def _create_downloader_mapping(self, media_id: int, download_item_id: int, external_db_source: str):
        """Create downloader mapping entry"""
        try:
            from src.service_factory import get_database
            db = get_database()
            with db.get_connection() as conn:
                conn.execute('''
                    INSERT INTO downloader_mapping (media_id, download_item_id, external_db_source)
                    VALUES (?, ?, ?)
                ''', (media_id, download_item_id, external_db_source))
        except Exception as e:
            logger.error(f"Error creating downloader mapping: {e}")

    def _process_4k_stogram_video(self, video_data):
        """Process single video from 4K Stogram (Instagram) using correct data mapping"""
        
        from ..database.posts import PostOperations
        from ..database.creators import CreatorOperations
        from ..database.subscriptions import SubscriptionOperations
        
        post_ops = PostOperations()
        creator_ops = CreatorOperations()
        subscription_ops = SubscriptionOperations()
        
        # 1. Create or get creator - use data from Instagram handler
        creator_name = video_data.get('creator_name')
        creator_url = video_data.get('creator_url')
        creator_id = None
        
        if creator_name:
            creator_id = creator_ops.create_or_get_creator(
                name=creator_name,
                platform_name='instagram',
                creator_name_source='db',
                profile_url=creator_url,
                platform_creator_id=creator_name  # Instagram username
            )
        
        # 2. Create or get subscription - use proper Instagram data
        subscription_id = None
        subscription_creator_id = creator_id if video_data.get('subscription_type') in ['account', 'saved'] else None
        
        if video_data.get('subscription_name'):
            subscription_id = subscription_ops.create_or_get_subscription(
                name=video_data.get('subscription_name'),
                platform_name='instagram',
                subscription_type=video_data.get('subscription_type', 'account'),
                is_account=video_data.get('subscription_type') in ['account', 'saved'],
                creator_id=subscription_creator_id,
                subscription_url=video_data.get('subscription_url'),
                external_uuid=str(video_data.get('subscription_database_id')) if video_data.get('subscription_database_id') else None
            )
        
        # 3. Prepare post data - use correct Instagram field mapping
        title_from_content = video_data.get('title')
        use_filename = video_data.get('title_is_filename', False)
        
        # Fallback logic for empty titles
        if not title_from_content or title_from_content.strip() == '':
            title_from_content = video_data.get('file_name', '').replace('.mp4', '').replace('.jpg', '').replace('.png', '')
            use_filename = True
        
        post_data = {
            'platform_id': subscription_ops.get_platform_id('instagram'),
            'platform_post_id': str(video_data.get('id')),  # Use 'id' field from handler
            'post_url': video_data.get('post_url'),  # Use 'post_url' field from handler
            'title_post': title_from_content,
            'use_filename': use_filename,
            'creator_id': creator_id,
            'subscription_id': subscription_id,
            'publication_date': None,  # Instagram doesn't provide publication_date
            'publication_date_source': None,
            'publication_date_confidence': None,
            'download_date': video_data.get('created_time')  # Use 'created_time' field from handler
        }
        
        
        # 4. Prepare media data - use correct content_type
        media_data = []
        if video_data.get('is_carousel'):
            # Multiple media items
            for item in video_data.get('carousel_items', []):
                media_data.append({
                    'file_path': item['file_path'],
                    'file_name': item['file_name'],
                    'media_type': item.get('content_type', 'image'),  # Use content_type from handler
                    'file_size': item.get('file_size', 0),
                    'duration_seconds': item.get('duration_seconds'),
                    'resolution_width': item.get('resolution_width'),
                    'resolution_height': item.get('resolution_height'),
                    'fps': None
                })
        else:
            # Single media item
            media_data.append({
                'file_path': video_data['file_path'],
                'file_name': video_data['file_name'],
                'media_type': video_data.get('content_type', 'image'),  # Use content_type from handler
                'file_size': video_data.get('file_size', 0),
                'duration_seconds': video_data.get('duration_seconds'),
                'resolution_width': video_data.get('resolution_width'),
                'resolution_height': video_data.get('resolution_height'),
                'fps': None
            })
        
        # 5. Determine categories - use list_types from Instagram handler
        list_types = video_data.get('list_types', ['feed'])
        category_types = list_types
        
        # 6. Create post with media
        post_id, media_ids = post_ops.create_post_with_media(post_data, media_data, category_types)
        
        # 7. Create downloader mapping - use dynamic external_db_source
        if media_ids:
            downloader_mapping = video_data.get('downloader_mapping', {})
            download_item_id = downloader_mapping.get('download_item_id')
            external_db_source = downloader_mapping.get('external_db_source', '4k_stogram')
            
            if download_item_id:
                for media_id in media_ids:
                    self._create_downloader_mapping(media_id, download_item_id, external_db_source)
        
        return post_id

    def _determine_subscription_type_4k_tokkit(self, subscription_data):
        """Determine subscription type from 4K Tokkit data"""
        sub_type = subscription_data.get('type')
        download_settings = subscription_data.get('download_settings', {})
        
        if sub_type == 1:  # Account
            # Determine specific type based on download settings
            if download_settings.get('downloadLiked'):
                return 'liked', False
            elif download_settings.get('downloadFavorites'):
                return 'saved', False
            else:
                return 'account', True
        elif sub_type == 2:  # Hashtag
            return 'hashtag', False
        elif sub_type == 3:  # Music
            return 'music', False
        else:
            return 'account', True

    def _build_tiktok_subscription_url(self, subscription_data):
        """Build TikTok subscription URL"""
        sub_type = subscription_data.get('type')
        name = subscription_data.get('name', '')
        sub_id = subscription_data.get('id')
        
        if sub_type == 1:  # Account
            return f"https://www.tiktok.com/@{name}"
        elif sub_type == 2:  # Hashtag
            return f"https://www.tiktok.com/tag/{name}"
        elif sub_type == 3:  # Music
            return f"https://www.tiktok.com/music/{name.replace(' ', '-')}-{sub_id}"
        else:
            return None

    # Category determination methods
    def _categorize_youtube_content(self, video_data):
        """Categorize YouTube content"""
        categories = ['videos']  # Default
        
        # Check for shorts based on dimensions and duration
        width = video_data.get('resolution_width', 0)
        height = video_data.get('resolution_height', 0)
        duration = video_data.get('duration_seconds', 0)
        
        if height > width and duration <= 60:  # Vertical and short
            categories = ['shorts']
        
        return categories

    def _categorize_tiktok_content(self, video_data, subscription_data=None):
        """Categorize TikTok content"""
        categories = ['videos']  # Default for TikTok
        
        # Add subscription-specific categories
        if subscription_data:
            download_settings = subscription_data.get('download_settings', {})
            if download_settings.get('downloadLiked'):
                categories.append('liked')
            elif download_settings.get('downloadFavorites'):
                categories.append('favorites')
        
        return categories

    def _categorize_instagram_content(self, video_data):
        """Categorize Instagram content based on file path"""
        file_path = video_data.get('file_path', '')
        categories = ['feed']  # Default
        
        if '/reels/' in file_path:
            categories = ['reels']
        elif '/stories/' in file_path:
            categories = ['stories']
        elif '/highlights/' in file_path:
            categories = ['highlights']
        elif '/tagged/' in file_path:
            categories = ['tagged']
        
        return categories

    def _categorize_bilibili_content(self, video_data):
        """Categorize Bilibili content"""
        return self._categorize_youtube_content(video_data)  # Similar logic

    def _categorize_facebook_content(self, video_data):
        """Categorize Facebook content"""
        return ['videos']  # Simple for now

    def _categorize_twitter_content(self, video_data):
        """Categorize Twitter content"""
        return ['videos']  # Simple for now

    def get_population_stats(self):
        """Get statistics about populated content"""
        from ..database.posts import PostOperations
        post_ops = PostOperations()
        return post_ops.get_platform_statistics()