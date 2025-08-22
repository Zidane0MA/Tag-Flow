"""
Tag-Flow V2 - Database Base Classes
Core database functionality and connection management
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from config import config

logger = logging.getLogger(__name__)


class DatabaseBase:
    """Base class for all database operations"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.query_times = {}  # {query_name: [times]}
        self.total_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Initialize database on first use
        self._initialized = False
    
    def get_connection(self) -> sqlite3.Connection:
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
        return conn
    
    def _ensure_initialized(self):
        """Ensure database is initialized (lazy initialization)"""
        if not self._initialized:
            # Only DatabaseCore should initialize the database
            # Other modules will be initialized by DatabaseManager
            self._initialized = True
    
    def init_database(self):
        """Initialize database with all tables - implemented by DatabaseCore"""
        # Default implementation for subclasses that don't need initialization
        pass
    
    def _track_query(self, query_name: str, execution_time: float):
        """Track query performance"""
        if query_name not in self.query_times:
            self.query_times[query_name] = []
        
        self.query_times[query_name].append(execution_time)
        self.total_queries += 1
    
    def _safe_json_loads(self, json_str: str, default=None):
        """Safely parse JSON string"""
        if not json_str:
            return default or []
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default or []
    
    def _safe_json_dumps(self, data) -> str:
        """Safely serialize to JSON string"""
        if not data:
            return ""
        try:
            return json.dumps(data, ensure_ascii=False)
        except (TypeError, ValueError):
            return ""
    
    def _format_video_row(self, row) -> Dict:
        """Format video database row to dictionary"""
        if not row:
            return None
        
        video = dict(row)
        
        # Parse JSON fields
        video['detected_characters'] = self._safe_json_loads(video.get('detected_characters'))
        video['final_characters'] = self._safe_json_loads(video.get('final_characters'))
        
        return video
    
    def _format_creator_row(self, row) -> Dict:
        """Format creator database row to dictionary"""
        if not row:
            return None
        
        creator = dict(row)
        
        # Parse JSON fields if any
        if 'urls' in creator:
            creator['urls'] = self._safe_json_loads(creator.get('urls'), {})
        
        return creator
    
    def _format_subscription_row(self, row) -> Dict:
        """Format subscription database row to dictionary"""
        if not row:
            return None
        
        subscription = dict(row)
        return subscription
    
    def _build_where_clause(self, filters: Dict) -> Tuple[str, List]:
        """Build WHERE clause from filters dictionary"""
        if not filters:
            return "", []
        
        conditions = []
        params = []
        
        for key, value in filters.items():
            if value is None:
                continue
                
            if key == 'platform' and value:
                conditions.append("platform = ?")
                params.append(value)
            elif key == 'edit_status' and value:
                conditions.append("edit_status = ?")
                params.append(value)
            elif key == 'processing_status' and value:
                conditions.append("processing_status = ?")
                params.append(value)
            elif key == 'creator_id' and value:
                conditions.append("creator_id = ?")
                params.append(value)
            elif key == 'subscription_id' and value:
                conditions.append("subscription_id = ?")
                params.append(value)
            elif key == 'has_music' and isinstance(value, bool):
                if value:
                    conditions.append("(detected_music IS NOT NULL OR final_music IS NOT NULL)")
                else:
                    conditions.append("(detected_music IS NULL AND final_music IS NULL)")
            elif key == 'has_characters' and isinstance(value, bool):
                if value:
                    conditions.append("(detected_characters IS NOT NULL OR final_characters IS NOT NULL)")
                else:
                    conditions.append("(detected_characters IS NULL AND final_characters IS NULL)")
        
        where_clause = " AND ".join(conditions) if conditions else ""
        return where_clause, params