"""
Tag-Flow V2 - Database Core
Final optimized schema implementation with posts → media structure
"""

import sqlite3
from .base import DatabaseBase
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseCore(DatabaseBase):
    """New optimized database core with posts → media structure"""
    
    def init_database(self):
        """Initialize database with new optimized schema"""
        with self.get_connection() as conn:
            # Enable foreign key constraints
            conn.execute('PRAGMA foreign_keys = ON')
            
            # 1. Platforms table
            self._create_platforms_table(conn)
            
            # 2. Creators table  
            self._create_creators_table(conn)
            
            # 3. Subscriptions table
            self._create_subscriptions_table(conn)
            
            # 4. Posts table (main content)
            self._create_posts_table(conn)
            
            # 5. Media table (technical files)
            self._create_media_table(conn)
            
            # 6. Post categories table
            self._create_post_categories_table(conn)
            
            # 7. Downloader mapping table
            self._create_downloader_mapping_table(conn)
            
            # Insert initial platform data
            self._insert_initial_platforms(conn)
            
            logger.info("New database schema initialized successfully")

    def _create_platforms_table(self, conn):
        """Create platforms table with initial data"""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS platforms (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                base_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index
        conn.execute('CREATE INDEX IF NOT EXISTS idx_platforms_name ON platforms(name)')

    def _create_creators_table(self, conn):
        """Create creators table with hierarchy support"""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS creators (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                platform_id INTEGER REFERENCES platforms(id),
                
                -- Hierarchy for aliases
                parent_creator_id INTEGER REFERENCES creators(id),
                is_primary BOOLEAN DEFAULT FALSE,
                alias_type TEXT CHECK(alias_type IN ('main', 'alias', 'variation')),
                
                -- External IDs (conserved)
                platform_creator_id TEXT,
                profile_url TEXT,
                
                -- Metadata
                creator_name_source TEXT CHECK(creator_name_source IN ('db', 'folder', 'api', 'scraping', 'manual')),
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indices
        conn.execute('CREATE INDEX IF NOT EXISTS idx_creators_platform ON creators(platform_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_creators_parent ON creators(parent_creator_id)')
        conn.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_creators_platform_unique 
                        ON creators(platform_id, platform_creator_id) 
                        WHERE platform_creator_id IS NOT NULL''')

    def _create_subscriptions_table(self, conn):
        """Create subscriptions table for 4K Apps mapping"""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                platform_id INTEGER REFERENCES platforms(id),
                
                -- Subscription types
                subscription_type TEXT CHECK(subscription_type IN (
                    'account', 'playlist', 'hashtag', 'location', 'music', 
                    'search', 'liked', 'saved', 'folder'
                )) NOT NULL,
                is_account BOOLEAN DEFAULT FALSE,
                
                -- References
                creator_id INTEGER REFERENCES creators(id),
                subscription_url TEXT,
                external_uuid TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indices
        conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_platform ON subscriptions(platform_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_creator ON subscriptions(creator_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_type ON subscriptions(subscription_type)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_account ON subscriptions(is_account)')

    def _create_posts_table(self, conn):
        """Create posts table - main content concept"""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                
                -- Identification
                platform_id INTEGER REFERENCES platforms(id) NOT NULL,
                platform_post_id TEXT,
                post_url TEXT,
                
                -- Content
                title_post TEXT,
                use_filename BOOLEAN DEFAULT FALSE,  -- Indicates if title_post was populated using filename
                
                -- Creator and subscription
                creator_id INTEGER REFERENCES creators(id),
                subscription_id INTEGER REFERENCES subscriptions(id),
                
                -- Dates
                publication_date INTEGER,
                publication_date_source TEXT CHECK(publication_date_source IN (
                    '4k_bd', 'api', 'scraping', 'parsing', 'fallback'
                )),
                publication_date_confidence INTEGER CHECK(publication_date_confidence BETWEEN 0 AND 100),
                
                download_date INTEGER,
                
                -- Carousel handling
                is_carousel BOOLEAN DEFAULT FALSE,
                carousel_count INTEGER DEFAULT 1,
                
                -- System
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP NULL,
                deleted_by TEXT,
                deletion_reason TEXT
            )
        ''')
        
        # Create indices
        conn.execute('CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_posts_creator ON posts(creator_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_posts_subscription ON posts(subscription_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_posts_publication_date ON posts(publication_date)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_posts_download_date ON posts(download_date)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_posts_deleted ON posts(deleted_at)')
        # REMOVED: Unique constraint on platform_post_id to allow same video in multiple lists/downloads
        # conn.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_platform_unique 
        #                 ON posts(platform_id, platform_post_id) 
        #                 WHERE platform_post_id IS NOT NULL''')

    def _create_media_table(self, conn):
        """Create media table - technical file data"""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY,
                post_id INTEGER REFERENCES posts(id) NOT NULL,
                
                -- Files
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                thumbnail_path TEXT,
                file_size INTEGER,
                duration_seconds INTEGER,
                
                -- Media specific
                media_type TEXT CHECK(media_type IN ('video', 'image', 'audio')) NOT NULL,
                resolution_width INTEGER,
                resolution_height INTEGER,
                fps INTEGER,
                
                -- Carousel
                carousel_order INTEGER DEFAULT 0,
                is_primary BOOLEAN DEFAULT TRUE,
                
                -- AI Recognition
                detected_music TEXT,
                detected_music_artist TEXT,
                detected_music_confidence REAL,
                detected_characters TEXT,
                music_source TEXT CHECK(music_source IN ('youtube', 'spotify', 'acrcloud', 'manual')),
                
                -- Manual editing
                final_music TEXT,
                final_music_artist TEXT,
                final_characters TEXT,
                difficulty_level TEXT CHECK(difficulty_level IN ('low', 'medium', 'high')),
                edit_status TEXT CHECK(edit_status IN ('pendiente', 'en_proceso', 'completado', 'descartado')) DEFAULT 'pendiente',
                edited_video_path TEXT,
                notes TEXT,
                processing_status TEXT CHECK(processing_status IN ('pending', 'processing', 'completed', 'failed', 'skipped')) DEFAULT 'pending',
                
                -- System
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indices
        conn.execute('CREATE INDEX IF NOT EXISTS idx_media_post ON media(post_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_media_type ON media(media_type)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_media_carousel ON media(post_id, carousel_order)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_media_primary ON media(is_primary)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_media_edit_status ON media(edit_status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_media_processing_status ON media(processing_status)')

    def _create_post_categories_table(self, conn):
        """Create post categories table"""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS post_categories (
                id INTEGER PRIMARY KEY,
                post_id INTEGER REFERENCES posts(id) NOT NULL,
                category_type TEXT CHECK(category_type IN (
                    'videos', 'shorts', 'feed', 'reels', 'stories', 'highlights', 'tagged'
                )) NOT NULL,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indices
        conn.execute('CREATE INDEX IF NOT EXISTS idx_post_categories_post ON post_categories(post_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_post_categories_type ON post_categories(category_type)')
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_post_categories_unique ON post_categories(post_id, category_type)')

    def _create_downloader_mapping_table(self, conn):
        """Create downloader mapping table"""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS downloader_mapping (
                id INTEGER PRIMARY KEY,
                media_id INTEGER REFERENCES media(id) NOT NULL,
                
                -- Mapping to external DB
                download_item_id INTEGER,
                external_db_source TEXT NOT NULL CHECK(external_db_source IN ('4k_youtube', '4k_tokkit', '4k_stogram')),
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indices
        conn.execute('CREATE INDEX IF NOT EXISTS idx_downloader_mapping_media ON downloader_mapping(media_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_downloader_mapping_source ON downloader_mapping(external_db_source)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_downloader_mapping_download_item ON downloader_mapping(download_item_id, external_db_source)')

    def _insert_initial_platforms(self, conn):
        """Insert initial platform data"""
        platforms = [
            ('youtube', 'YouTube', 'https://www.youtube.com'),
            ('tiktok', 'TikTok', 'https://www.tiktok.com'),
            ('instagram', 'Instagram', 'https://www.instagram.com'),
            ('bilibili', 'Bilibili', 'https://www.bilibili.com'),
            ('bilibili', 'Bilibili.tv', 'https://www.bilibili.tv'),
            ('facebook', 'Facebook', 'https://www.facebook.com'),
            ('twitter', 'Twitter/X', 'https://x.com'),
            ('vimeo', 'Vimeo', 'https://www.vimeo.com'),
            ('dailymotion', 'Dailymotion', 'https://www.dailymotion.com'),
            ('pinterest', 'Pinterest', 'https://www.pinterest.com'),
            ('flickr', 'Flickr', 'https://www.flickr.com'),
            ('soundcloud', 'SoundCloud', 'https://www.soundcloud.com'),
            ('newgrounds', 'Newgrounds', 'https://www.newgrounds.com'),
            ('bitchute', 'BitChute', 'https://www.bitchute.com'),
            ('peertube', 'PeerTube', 'https://peertube.com'),
            ('spotify', 'Spotify', 'https://www.spotify.com'),
            ('twitch', 'Twitch', 'https://www.twitch.tv'),
            ('iwara', 'Iwara', 'https://www.iwara.tv'),
            ('patreon', 'Patreon', 'https://www.patreon.com'),
            ('onlyfans', 'OnlyFans', 'https://www.onlyfans.com'),
            ('substack', 'Substack', 'https://www.substack.com'),
            ('discord', 'Discord', 'https://www.discord.com'),
            ('mastodon', 'Mastodon', 'https://mastodon.social'),
            ('telegram', 'Telegram', 'https://www.telegram.org'),
            ('reddit', 'Reddit', 'https://www.reddit.com'),
            ('tumblr', 'Tumblr', 'https://www.tumblr.com'),
            ('odnoklassniki', 'Odnoklassniki', 'https://ok.ru'),
            ('vk', 'VK', 'https://vk.com'),
            ('telegram', 'Telegram Channels', 'https://www.telegram.org'),
            ('whatsapp', 'WhatsApp', 'https://www.whatsapp.com'),
            ('snapchat', 'Snapchat', 'https://www.snapchat.com'),
            ('quora', 'Quora', 'https://www.quora.com'),
            ('rule34', 'Rule34', 'https://rule34.xxx'),
            ('kemono', 'Kemono', 'https://kemono.cr'),
            ('coomer', 'Coomer', 'https://coomer.st')
        ]
        
        conn.executemany('''
            INSERT OR IGNORE INTO platforms (name, display_name, base_url) 
            VALUES (?, ?, ?)
        ''', platforms)