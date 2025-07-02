"""
Tag-Flow V2 - Gestión de Base de Datos
Manejo de SQLite para videos TikTok/MMD
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor principal de la base de datos SQLite"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Crear conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
        return conn
    
    def init_database(self):
        """Inicializar base de datos con todas las tablas"""
        with self.get_connection() as conn:
            # Tabla principal de videos
            conn.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Archivos
                    file_path TEXT NOT NULL UNIQUE,
                    file_name TEXT NOT NULL,
                    thumbnail_path TEXT,
                    file_size INTEGER,
                    duration_seconds INTEGER,
                    
                    -- Información del contenido
                    description TEXT,  -- Título/descripción del video
                    title TEXT,        -- Título alternativo
                    
                    -- Creador (desde 4K Downloader + manual)
                    creator_name TEXT NOT NULL,
                    platform TEXT DEFAULT 'tiktok' CHECK(platform IN ('tiktok', 'instagram', 'youtube', 'iwara', 'other')),
                    
                    -- Reconocimiento Automático
                    detected_music TEXT,
                    detected_music_artist TEXT,
                    detected_music_confidence REAL,
                    detected_characters TEXT, -- JSON array
                    music_source TEXT CHECK(music_source IN ('youtube', 'spotify', 'acrcloud', 'manual')),
                    
                    -- Edición Manual (Frontend)
                    final_music TEXT,
                    final_music_artist TEXT,
                    final_characters TEXT, -- JSON array
                    difficulty_level TEXT CHECK(difficulty_level IN ('bajo', 'medio', 'alto')),
                    
                    -- Estados del Proyecto
                    edit_status TEXT DEFAULT 'nulo' CHECK(edit_status IN ('nulo', 'en_proceso', 'hecho')),
                    edited_video_path TEXT,
                    notes TEXT,
                    
                    -- Metadatos
                    processing_status TEXT DEFAULT 'pendiente' CHECK(processing_status IN ('pendiente', 'procesando', 'completado', 'error')),
                    error_message TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de mapeo con 4K Downloader
            conn.execute('''
                CREATE TABLE IF NOT EXISTS downloader_mapping (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER,
                    download_item_id INTEGER,
                    original_filename TEXT,
                    creator_from_downloader TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
                )
            ''')
            
            # Índices para rendimiento
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_creator ON videos(creator_name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(edit_status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_platform ON videos(platform)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_file_path ON videos(file_path)')
            
            conn.commit()
            logger.info("Base de datos inicializada correctamente")
    
    def add_video(self, video_data: Dict) -> int:
        """Agregar nuevo video a la base de datos"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO videos (
                    file_path, file_name, creator_name, platform, file_size, duration_seconds,
                    detected_music, detected_music_artist, detected_music_confidence,
                    detected_characters, music_source, processing_status, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_data['file_path'],
                video_data['file_name'], 
                video_data['creator_name'],
                video_data.get('platform', 'tiktok'),
                video_data.get('file_size'),
                video_data.get('duration_seconds'),
                video_data.get('detected_music'),
                video_data.get('detected_music_artist'),
                video_data.get('detected_music_confidence'),
                json.dumps(video_data.get('detected_characters', [])),
                video_data.get('music_source'),
                video_data.get('processing_status', 'pendiente'),
                video_data.get('description')  # Nueva línea para descripción
            ))
            video_id = cursor.lastrowid
            logger.info(f"Video agregado con ID {video_id}: {video_data['file_name']}")
            return video_id
    
    def get_video(self, video_id: int) -> Optional[Dict]:
        """Obtener un video por ID"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_video_by_path(self, file_path: str) -> Optional[Dict]:
        """Obtener un video por su file_path (ruta absoluta)"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM videos WHERE file_path = ?', (file_path,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_videos(self, filters: Dict = None, limit: int = None, offset: int = 0) -> List[Dict]:
        """Obtener lista de videos con filtros opcionales"""
        query = "SELECT * FROM videos WHERE 1=1"
        params = []
        
        # Aplicar filtros
        if filters:
            if filters.get('creator_name'):
                query += " AND creator_name LIKE ?"
                params.append(f"%{filters['creator_name']}%")
            
            if filters.get('platform'):
                query += " AND platform = ?"
                params.append(filters['platform'])
                
            if filters.get('edit_status'):
                query += " AND edit_status = ?"
                params.append(filters['edit_status'])
            
            if filters.get('processing_status'):
                query += " AND processing_status = ?"
                params.append(filters['processing_status'])
                
            if filters.get('difficulty_level'):
                query += " AND difficulty_level = ?"
                params.append(filters['difficulty_level'])
                
            if filters.get('has_music'):
                if filters['has_music']:
                    query += " AND (detected_music IS NOT NULL OR final_music IS NOT NULL)"
                else:
                    query += " AND detected_music IS NULL AND final_music IS NULL"
            
            # Búsqueda de texto libre en múltiples campos
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query += """ AND (
                    creator_name LIKE ? OR
                    file_name LIKE ? OR
                    detected_music LIKE ? OR
                    final_music LIKE ? OR
                    detected_music_artist LIKE ? OR
                    final_music_artist LIKE ? OR
                    detected_characters LIKE ? OR
                    final_characters LIKE ? OR
                    notes LIKE ?
                )"""
                # Agregar el término de búsqueda para cada campo
                params.extend([search_term] * 9)
        
        # Ordenar por fecha de creación (más recientes primero)
        query += " ORDER BY created_at DESC"
        
        # Aplicar límite y offset
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            if offset:
                query += " OFFSET ?"
                params.append(offset)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def count_videos(self, filters: Dict = None) -> int:
        """Contar videos que coinciden con los filtros"""
        query = "SELECT COUNT(*) FROM videos WHERE 1=1"
        params = []
        
        # Aplicar los mismos filtros que get_videos
        if filters:
            if filters.get('creator_name'):
                query += " AND creator_name LIKE ?"
                params.append(f"%{filters['creator_name']}%")
            
            if filters.get('platform'):
                query += " AND platform = ?"
                params.append(filters['platform'])
                
            if filters.get('edit_status'):
                query += " AND edit_status = ?"
                params.append(filters['edit_status'])
            
            if filters.get('processing_status'):
                query += " AND processing_status = ?"
                params.append(filters['processing_status'])
                
            if filters.get('difficulty_level'):
                query += " AND difficulty_level = ?"
                params.append(filters['difficulty_level'])
                
            if filters.get('has_music'):
                if filters['has_music']:
                    query += " AND (detected_music IS NOT NULL OR final_music IS NOT NULL)"
                else:
                    query += " AND detected_music IS NULL AND final_music IS NULL"
            
            # Búsqueda de texto libre en múltiples campos
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query += """ AND (
                    creator_name LIKE ? OR
                    file_name LIKE ? OR
                    detected_music LIKE ? OR
                    final_music LIKE ? OR
                    detected_music_artist LIKE ? OR
                    final_music_artist LIKE ? OR
                    detected_characters LIKE ? OR
                    final_characters LIKE ? OR
                    notes LIKE ?
                )"""
                # Agregar el término de búsqueda para cada campo
                params.extend([search_term] * 9)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]
    
    def update_video(self, video_id: int, updates: Dict) -> bool:
        """Actualizar un video con nuevos datos"""
        if not updates:
            return False
        
        # Construir query de actualización dinámica
        set_clauses = []
        params = []
        
        allowed_fields = [
            'final_music', 'final_music_artist', 'final_characters', 'difficulty_level',
            'edit_status', 'edited_video_path', 'notes', 'processing_status', 'error_message',
            'thumbnail_path', 'description',  # Agregar description
            'detected_music', 'detected_music_artist', 'detected_music_confidence', 'music_source', 'detected_characters'
        ]
        
        for field, value in updates.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = ?")
                # Convertir listas a JSON para campos de personajes
                if field in ['final_characters', 'detected_characters'] and isinstance(value, list):
                    value = json.dumps(value)
                params.append(value)
        
        if not set_clauses:
            return False
        
        # Agregar timestamp de actualización
        set_clauses.append("last_updated = CURRENT_TIMESTAMP")
        params.append(video_id)
        
        query = f"UPDATE videos SET {', '.join(set_clauses)} WHERE id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Video {video_id} actualizado exitosamente")
            return success
    
    def update_video_characters(self, video_id: int, characters_json: str = None) -> bool:
        """Actualizar solo los personajes detectados de un video"""
        return self.update_video(video_id, {'detected_characters': characters_json})
    
    def delete_video(self, video_id: int) -> bool:
        """Eliminar un video de la base de datos"""
        with self.get_connection() as conn:
            cursor = conn.execute('DELETE FROM videos WHERE id = ?', (video_id,))
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Video {video_id} eliminado")
            return success
    
    def get_unique_creators(self) -> List[str]:
        """Obtener lista de creadores únicos"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT DISTINCT creator_name FROM videos ORDER BY creator_name')
            return [row[0] for row in cursor.fetchall()]
    
    def get_unique_music(self) -> List[str]:
        """Obtener lista de música única"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT DISTINCT 
                    COALESCE(final_music, detected_music) as music
                FROM videos 
                WHERE COALESCE(final_music, detected_music) IS NOT NULL
                ORDER BY music
            ''')
            return [row[0] for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas generales"""
        with self.get_connection() as conn:
            stats = {}
            
            # Total de videos
            cursor = conn.execute('SELECT COUNT(*) FROM videos')
            stats['total_videos'] = cursor.fetchone()[0]
            
            # Videos por estado
            cursor = conn.execute('SELECT edit_status, COUNT(*) FROM videos GROUP BY edit_status')
            stats['by_status'] = dict(cursor.fetchall())
            
            # Videos por plataforma
            cursor = conn.execute('SELECT platform, COUNT(*) FROM videos GROUP BY platform')
            stats['by_platform'] = dict(cursor.fetchall())
            
            # Videos con música detectada
            cursor = conn.execute('''
                SELECT COUNT(*) FROM videos 
                WHERE detected_music IS NOT NULL OR final_music IS NOT NULL
            ''')
            stats['with_music'] = cursor.fetchone()[0]
            
            # Videos con personajes detectados
            cursor = conn.execute('''
                SELECT COUNT(*) FROM videos 
                WHERE detected_characters IS NOT NULL AND detected_characters != '[]'
            ''')
            stats['with_characters'] = cursor.fetchone()[0]
            
            return stats

# Instancia global del gestor de base de datos
db = DatabaseManager()