"""
Tag-Flow V2 - Database Core
Database initialization and schema management
"""

import sqlite3
from .base import DatabaseBase
import logging

logger = logging.getLogger(__name__)


class DatabaseCore(DatabaseBase):
    """Core database functionality including schema initialization"""
    
    def init_database(self):
        """Initialize database with all tables and indices"""
        with self.get_connection() as conn:
            # Main videos table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Files
                    file_path TEXT NOT NULL UNIQUE,
                    file_name TEXT NOT NULL,
                    thumbnail_path TEXT,
                    file_size INTEGER,
                    duration_seconds INTEGER,
                    
                    -- Content information
                    title TEXT,  -- Video title/description
                    post_url TEXT,              -- Original post URL
                    
                    -- Platform
                    platform TEXT DEFAULT 'tiktok',
                    
                    -- Automatic Recognition
                    detected_music TEXT,
                    detected_music_artist TEXT,
                    detected_music_confidence REAL,
                    detected_characters TEXT, -- JSON array
                    music_source TEXT CHECK(music_source IN ('youtube', 'spotify', 'acrcloud', 'manual')),
                    
                    -- Manual Editing (Frontend)
                    final_music TEXT,
                    final_music_artist TEXT,
                    final_characters TEXT, -- JSON array
                    difficulty_level TEXT CHECK(difficulty_level IN ('bajo', 'medio', 'alto')),
                    
                    -- Project States
                    edit_status TEXT DEFAULT 'nulo' CHECK(edit_status IN ('nulo', 'en_proceso', 'hecho')),
                    edited_video_path TEXT,
                    notes TEXT,
                    
                    -- Metadata
                    processing_status TEXT DEFAULT 'pendiente' CHECK(processing_status IN ('pendiente', 'procesando', 'completado', 'error')),
                    error_message TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Deletion system (soft delete)
                    deleted_at TIMESTAMP NULL,
                    deleted_by TEXT,
                    deletion_reason TEXT,
                    
                    -- Normalized relationships (creator_id now required)
                    creator_id INTEGER NOT NULL REFERENCES creators(id),
                    subscription_id INTEGER REFERENCES subscriptions(id),
                    
                    FOREIGN KEY (creator_id) REFERENCES creators(id)
                )
            ''')
            
            # Creators table (with hierarchy support)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS creators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,              -- Unified creator name
                    parent_creator_id INTEGER REFERENCES creators(id),  -- For secondary accounts
                    is_primary BOOLEAN DEFAULT TRUE, -- Main vs secondary account
                    alias_type TEXT DEFAULT 'main' CHECK(alias_type IN ('main', 'secondary', 'collaboration', 'alias')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_creator_id) REFERENCES creators(id)
                )
            ''')
            
            # Creator URLs by platform
            conn.execute('''
                CREATE TABLE IF NOT EXISTS creator_urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER NOT NULL REFERENCES creators(id),
                    platform TEXT NOT NULL,         -- 'youtube', 'tiktok', 'instagram', 'facebook'
                    url TEXT NOT NULL,              -- Complete profile URL
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(creator_id, platform)
                )
            ''')
            
            # Subscriptions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,             -- "Channel X", "My Playlist", "#hashtag"
                    type TEXT NOT NULL,             -- 'account', 'playlist', 'music', 'hashtag', 'location', 'saved', 'personal'
                    platform TEXT NOT NULL,        -- 'youtube', 'tiktok', 'instagram', 'facebook'
                    creator_id INTEGER REFERENCES creators(id), -- NULL for lists without specific creator
                    subscription_url TEXT,          -- List/subscription URL
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Video lists table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS video_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL REFERENCES videos(id),
                    list_type TEXT NOT NULL,       -- 'feed', 'liked', 'reels', 'stories', 'highlights', 'saved', 'favorites'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(video_id, list_type)
                )
            ''')
            
            # 4K Downloader mapping table (optimized)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS downloader_mapping (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL REFERENCES videos(id),
                    download_item_id INTEGER,       -- ID in external DB
                    external_db_source TEXT,        -- '4k_video', '4k_tokkit', '4k_stogram'
                    original_filename TEXT,
                    creator_from_downloader TEXT,
                    is_carousel_item BOOLEAN DEFAULT FALSE,  -- New: Instagram carousel item
                    carousel_order INTEGER,                  -- New: Order in carousel
                    carousel_base_id TEXT,                   -- New: Carousel base ID
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
                )
            ''')
            
            # Create all performance indices
            self._create_performance_indices(conn)
            
            conn.commit()
            logger.debug("Database initialized successfully")
    
    def _create_performance_indices(self, conn):
        """Create all performance indices for optimal query speed"""
        
        # Basic indices for videos table
        conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(edit_status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_platform ON videos(platform)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_file_path ON videos(file_path)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_deleted ON videos(deleted_at)')
        
        # Foreign key indices
        conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_creator_id ON videos(creator_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_subscription_id ON videos(subscription_id)')
        
        # Composite indices for performance (10x faster queries)
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_videos_file_path_name 
            ON videos(file_path, file_name)
        ''')
        
        # Platform and status filters (5x faster)
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_videos_platform_status 
            ON videos(platform, processing_status)
        ''')
        
        # Pending videos optimization
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_videos_status_platform 
            ON videos(processing_status, platform)
        ''')
        
        # Advanced filtering with date
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_videos_status_platform_created 
            ON videos(processing_status, platform, created_at)
        ''')
        
        # Date ordering
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_videos_created_at 
            ON videos(created_at)
        ''')
        
        # Frontend composite queries
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_videos_creator_platform 
            ON videos(creator_id, platform)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_videos_subscription_platform 
            ON videos(subscription_id, platform)
        ''')
        
        # Creators indices (including hierarchy fields)
        conn.execute('CREATE INDEX IF NOT EXISTS idx_creators_name ON creators(name)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_creators_parent ON creators(parent_creator_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_creators_is_primary ON creators(is_primary)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_creators_alias_type ON creators(alias_type)')
        
        # Creator URLs indices
        conn.execute('CREATE INDEX IF NOT EXISTS idx_creator_urls_creator_id ON creator_urls(creator_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_creator_urls_platform ON creator_urls(platform)')
        
        # Subscriptions indices
        conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_creator_id ON subscriptions(creator_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_platform ON subscriptions(platform)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_type ON subscriptions(type)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_platform_type ON subscriptions(platform, type)')
        
        # Video lists indices
        conn.execute('CREATE INDEX IF NOT EXISTS idx_video_lists_video_id ON video_lists(video_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_video_lists_list_type ON video_lists(list_type)')
        
        # Downloader mapping indices (including carousel fields)
        conn.execute('CREATE INDEX IF NOT EXISTS idx_downloader_mapping_external_db ON downloader_mapping(external_db_source)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_downloader_mapping_carousel ON downloader_mapping(is_carousel_item)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_downloader_mapping_carousel_base ON downloader_mapping(carousel_base_id)')
        
        logger.debug("Performance indices created successfully")