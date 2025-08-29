"""
Population Coordinator - Main Dispatcher for Platform-Specific Population
========================================================================

This class acts as the main entry point for database population operations,
dispatching to the appropriate platform-specific populator.
"""

from typing import Dict, List, Optional, Any, Callable
import logging

logger = logging.getLogger(__name__)


class PopulationCoordinator:
    """
    Main coordinator for database population operations.
    
    Dispatches population requests to appropriate platform-specific populators
    and provides a unified interface for the maintenance system.
    """
    
    def __init__(self):
        self._populators = {}
        self._initialize_populators()
    
    def _initialize_populators(self):
        """Initialize all platform-specific populators"""
        try:
            from .tiktok_populator import TikTokPopulator
            from .youtube_populator import YouTubePopulator
            from .instagram_populator import InstagramPopulator
            
            self._populators = {
                'tiktok': TikTokPopulator(),
                'youtube': YouTubePopulator(),
                'bilibili': YouTubePopulator(),  # Bilibili uses YouTube populator
                'facebook': YouTubePopulator(),  # Facebook uses YouTube populator  
                'twitter': YouTubePopulator(),   # Twitter uses YouTube populator
                'instagram': InstagramPopulator(),
            }
            
            logger.debug(f"Initialized populators for: {list(self._populators.keys())}")
            
        except ImportError as e:
            logger.error(f"Failed to initialize populators: {e}")
            self._populators = {}
    
    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms"""
        return list(self._populators.keys())
    
    def get_platform_info(self, platform: str) -> Dict[str, Any]:
        """Get information about a specific platform"""
        if platform not in self._populators:
            return {'supported': False, 'error': f'Platform {platform} not supported'}
        
        populator = self._populators[platform]
        return {
            'supported': True,
            'platform_name': populator.platform_name,
            'supported_sources': populator.supported_sources,
        }
    
    def populate(self, source: str, platform: Optional[str] = None, 
                limit: Optional[int] = None, force: bool = False, 
                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Main population method - coordinates platform-specific population.
        
        Args:
            source: Source type ('db', 'organized', etc.)
            platform: Target platform ('tiktok', 'youtube', etc.) or None for all
            limit: Maximum number of videos to process
            force: Force reprocessing of existing videos
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with population results
        """
        
        if platform is None:
            # Populate all platforms
            return self._populate_all_platforms(source, limit, force, progress_callback)
        
        # Populate specific platform
        if platform not in self._populators:
            error_msg = f"Platform '{platform}' not supported. Supported: {list(self._populators.keys())}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'supported_platforms': list(self._populators.keys())
            }
        
        populator = self._populators[platform]
        
        # Validate source for this platform
        if not populator._validate_source(source):
            return {
                'success': False,
                'platform': platform,
                'error': f"Source '{source}' not supported by {platform}",
                'supported_sources': populator.supported_sources
            }
        
        logger.info(f"🎯 Dispatching {platform} population to {populator.__class__.__name__}")
        
        # Execute population with specific platform filter
        result = populator.populate(source, limit, force, progress_callback, platform)
        
        # Log results
        populator._log_results(result)
        
        return result
    
    def _populate_all_platforms(self, source: str, limit: Optional[int] = None, 
                               force: bool = False, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Populate all supported platforms.
        
        This method coordinates population across all platforms and aggregates results.
        """
        logger.info(f"🌐 Starting multi-platform population from {source}")
        
        overall_results = {
            'success': True,
            'source': source,
            'platforms_processed': [],
            'total_videos_added': 0,
            'total_creators_created': 0,
            'total_subscriptions_created': 0,
            'platform_results': {},
            'errors': []
        }
        
        for platform_name, populator in self._populators.items():
            # Check if populator supports this source
            if source not in populator.supported_sources:
                logger.debug(f"⏭️ Skipping {platform_name} - source '{source}' not supported")
                continue
            
            logger.info(f"🔄 Processing {platform_name}...")
            
            try:
                # Execute platform-specific population
                platform_result = populator.populate(source, limit, force, progress_callback)
                
                # Track results
                overall_results['platform_results'][platform_name] = platform_result
                overall_results['platforms_processed'].append(platform_name)
                
                if platform_result.get('success'):
                    overall_results['total_videos_added'] += platform_result.get('videos_added', 0)
                    overall_results['total_creators_created'] += platform_result.get('creators_created', 0)
                    overall_results['total_subscriptions_created'] += platform_result.get('subscriptions_created', 0)
                else:
                    overall_results['errors'].append({
                        'platform': platform_name,
                        'error': platform_result.get('error', 'Unknown error')
                    })
                    overall_results['success'] = False
                
                # Log platform results
                populator._log_results(platform_result)
                
            except Exception as e:
                error_msg = f"Error processing {platform_name}: {e}"
                logger.error(error_msg)
                overall_results['errors'].append({
                    'platform': platform_name,
                    'error': str(e)
                })
                overall_results['success'] = False
        
        # Final summary
        if overall_results['success']:
            logger.info(
                f"✅ Multi-platform population completed: "
                f"{overall_results['total_videos_added']} videos, "
                f"{overall_results['total_creators_created']} creators, "
                f"{overall_results['total_subscriptions_created']} subscriptions "
                f"across {len(overall_results['platforms_processed'])} platforms"
            )
        else:
            logger.error(f"❌ Multi-platform population completed with {len(overall_results['errors'])} errors")
        
        return overall_results