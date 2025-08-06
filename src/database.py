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
        
        # 🚀 MIGRADO: Sistema de métricas de performance de optimized_database.py
        self.query_times = {}  # {query_name: [times]}
        self.total_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
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
                    title TEXT,  -- Título/descripción del video
                    post_url TEXT,              -- URL del post original
                    external_video_id TEXT,     -- ID del video en plataforma externa
                    
                    -- Creador (desde 4K Downloader + manual)
                    creator_name TEXT NOT NULL,
                    platform TEXT DEFAULT 'tiktok',
                    
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
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Sistema de eliminación (soft delete)
                    deleted_at TIMESTAMP NULL,
                    deleted_by TEXT,
                    deletion_reason TEXT,
                    
                    -- Relaciones con nuevas tablas
                    creator_id INTEGER REFERENCES creators(id),
                    subscription_id INTEGER REFERENCES subscriptions(id)
                )
            ''')
            
            # Nuevas tablas del sistema
            
            # Tabla de creadores
            conn.execute('''
                CREATE TABLE IF NOT EXISTS creators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,              -- Nombre unificado del creador
                    display_name TEXT,               -- Nombre para mostrar en UI
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de URLs de creadores por plataforma
            conn.execute('''
                CREATE TABLE IF NOT EXISTS creator_urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER NOT NULL REFERENCES creators(id),
                    platform TEXT NOT NULL,         -- 'youtube', 'tiktok', 'instagram', 'facebook'
                    url TEXT NOT NULL,              -- URL completa del perfil
                    username TEXT,                  -- @username sin la URL base
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(creator_id, platform)
                )
            ''')
            
            # Tabla de suscripciones
            conn.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,             -- "Canal X", "Mi Playlist", "#hashtag"
                    type TEXT NOT NULL,             -- 'account', 'playlist', 'music', 'hashtag', 'location', 'saved', 'personal'
                    platform TEXT NOT NULL,        -- 'youtube', 'tiktok', 'instagram', 'facebook'
                    creator_id INTEGER REFERENCES creators(id), -- NULL para listas sin creador específico
                    
                    -- URLs y metadata
                    subscription_url TEXT,          -- URL de la lista/subscription
                    external_id TEXT,              -- ID en la plataforma externa
                    metadata TEXT,                 -- JSON con datos específicos por tipo
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de listas por video
            conn.execute('''
                CREATE TABLE IF NOT EXISTS video_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL REFERENCES videos(id),
                    list_type TEXT NOT NULL,       -- 'feed', 'liked', 'reels', 'stories', 'highlights', 'saved', 'favorites'
                    source_path TEXT,              -- Ruta que indica la lista (ej: "\\\\name\\\\Liked\\\\")
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(video_id, list_type)
                )
            ''')
            
            # Tabla de mapeo con 4K Downloader (actualizada)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS downloader_mapping (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL REFERENCES videos(id),
                    download_item_id INTEGER,       -- ID en BD externa
                    external_db_source TEXT,        -- '4k_video', '4k_tokkit', '4k_stogram'
                    original_filename TEXT,
                    creator_from_downloader TEXT,
                    external_metadata TEXT,         -- JSON con metadata específica del downloader
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
                )
            ''')
            
            # Índices para rendimiento - Tabla videos
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_creator ON videos(creator_name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(edit_status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_platform ON videos(platform)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_file_path ON videos(file_path)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_deleted ON videos(deleted_at)')
            
            # Índices para nuevos campos en videos
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_creator_id ON videos(creator_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_subscription_id ON videos(subscription_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_external_video_id ON videos(external_video_id)')
            
            # 🚀 MIGRADOS: Índices optimizados de optimized_database.py
            # Índice compuesto para búsqueda por path y nombre combinada (10x más rápido)
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_videos_file_path_name 
                ON videos(file_path, file_name)
            ''')
            
            # Índice para filtros frecuentes en procesamiento (5x más rápido)
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_videos_platform_status 
                ON videos(platform, processing_status)
            ''')
            
            # Índice para consultas de videos pendientes optimizadas
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_videos_status_platform 
                ON videos(processing_status, platform)
            ''')
            
            # Índice compuesto para filtering avanzado con fecha
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_videos_status_platform_created 
                ON videos(processing_status, platform, created_at)
            ''')
            
            # Índice para ordenamiento por fecha de agregado
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_videos_created_at 
                ON videos(created_at)
            ''')
            
            # Índices compuestos para queries del frontend
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_videos_creator_platform 
                ON videos(creator_id, platform)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_videos_subscription_platform 
                ON videos(subscription_id, platform)
            ''')
            
            # Índices para creators
            conn.execute('CREATE INDEX IF NOT EXISTS idx_creators_name ON creators(name)')
            
            # Índices para creator_urls
            conn.execute('CREATE INDEX IF NOT EXISTS idx_creator_urls_creator_id ON creator_urls(creator_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_creator_urls_platform ON creator_urls(platform)')
            
            # Índices para subscriptions
            conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_creator_id ON subscriptions(creator_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_platform ON subscriptions(platform)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_type ON subscriptions(type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_platform_type ON subscriptions(platform, type)')
            
            # Índices para video_lists
            conn.execute('CREATE INDEX IF NOT EXISTS idx_video_lists_video_id ON video_lists(video_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_video_lists_list_type ON video_lists(list_type)')
            
            # Índices para downloader_mapping
            conn.execute('CREATE INDEX IF NOT EXISTS idx_downloader_mapping_external_db ON downloader_mapping(external_db_source)')
            
            conn.commit()
            logger.info("Base de datos inicializada correctamente")
    
    def add_video(self, video_data: Dict) -> int:
        """Agregar nuevo video a la base de datos"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO videos (
                    file_path, file_name, creator_name, platform, file_size, duration_seconds,
                    detected_music, detected_music_artist, detected_music_confidence,
                    detected_characters, music_source, processing_status, title
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
                video_data.get('title')  # Nueva línea para título
            ))
            video_id = cursor.lastrowid
            logger.info(f"Video agregado con ID {video_id}: {video_data['file_name']}")
            return video_id
    
    def batch_insert_videos(self, videos_data: List[Dict], force: bool = False) -> Tuple[int, int]:
        """Insertar múltiples videos en una sola transacción (optimizado)"""
        if not videos_data:
            return 0, 0
            
        successful = 0
        failed = 0
        
        with self.get_connection() as conn:
            try:
                if force:
                    # Modo force: usar INSERT OR REPLACE para actualizar existentes
                    insert_data = []
                    for video_data in videos_data:
                        insert_row = (
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
                            video_data.get('title'),
                            video_data.get('post_url'),
                            video_data.get('external_video_id'),
                            video_data.get('creator_id'),          # Nueva estructura
                            video_data.get('subscription_id')      # Nueva estructura
                        )
                        insert_data.append(insert_row)
                    
                    # Inserción con reemplazo para forzar actualización
                    conn.executemany('''
                        INSERT OR REPLACE INTO videos (
                            file_path, file_name, creator_name, platform,
                            file_size, duration_seconds, detected_music, detected_music_artist,
                            detected_music_confidence, detected_characters, music_source,
                            processing_status, title, post_url, external_video_id,
                            creator_id, subscription_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', insert_data)
                    
                    successful = len(insert_data)
                    logger.info(f"Inserción por lotes con FORCE exitosa: {successful} videos")
                else:
                    # Modo normal: insertar solo videos nuevos
                    # Inserción uno por uno para obtener IDs correctos
                    video_ids = []
                    for video_data in videos_data:
                        insert_row = (
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
                            video_data.get('title'),
                            video_data.get('post_url'),
                            video_data.get('external_video_id'),
                            video_data.get('creator_id'),          # Nueva estructura
                            video_data.get('subscription_id')      # Nueva estructura
                        )
                        
                        cursor = conn.execute('''
                            INSERT INTO videos (
                                file_path, file_name, creator_name, platform,
                                file_size, duration_seconds, detected_music, detected_music_artist,
                                detected_music_confidence, detected_characters, music_source,
                                processing_status, title, post_url, external_video_id,
                                creator_id, subscription_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', insert_row)
                        
                        video_id = cursor.lastrowid
                        video_ids.append(video_id)
                        
                        # Insertar en downloader_mapping si hay datos
                        if 'downloader_mapping' in video_data and video_data['downloader_mapping']:
                            dm_data = video_data['downloader_mapping']
                            conn.execute('''
                                INSERT INTO downloader_mapping (
                                    video_id, download_item_id, external_db_source, 
                                    original_filename, creator_from_downloader, external_metadata
                                ) VALUES (?, ?, ?, ?, ?, ?)
                            ''', (
                                video_id,
                                dm_data.get('download_item_id'),
                                dm_data.get('external_db_source'),
                                video_data.get('file_name'),
                                video_data.get('creator_name'),
                                dm_data.get('external_metadata', '{}')
                            ))
                        
                        # Insertar en video_lists si hay tipos de lista
                        if 'list_types' in video_data and video_data['list_types']:
                            for list_type in video_data['list_types']:
                                conn.execute('''
                                    INSERT OR IGNORE INTO video_lists (video_id, list_type)
                                    VALUES (?, ?)
                                ''', (video_id, list_type))
                    
                    successful = len(video_ids)
                    logger.info(f"Inserción por lotes exitosa: {successful} videos")
                
                conn.commit()
                
            except Exception as e:
                logger.error(f"Error en inserción por lotes: {e}")
                conn.rollback()
                failed = len(videos_data)
                
        return successful, failed
    
    def get_video(self, video_id: int, include_deleted: bool = False) -> Optional[Dict]:
        """Obtener un video por ID"""
        with self.get_connection() as conn:
            if include_deleted:
                cursor = conn.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
            else:
                cursor = conn.execute('SELECT * FROM videos WHERE id = ? AND deleted_at IS NULL', (video_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_video_by_path(self, file_path: str, include_deleted: bool = False) -> Optional[Dict]:
        """Obtener un video por su file_path (ruta absoluta)"""
        with self.get_connection() as conn:
            if include_deleted:
                cursor = conn.execute('SELECT * FROM videos WHERE file_path = ?', (file_path,))
            else:
                cursor = conn.execute('SELECT * FROM videos WHERE file_path = ? AND deleted_at IS NULL', (file_path,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_videos(self, filters: Dict = None, limit: int = None, offset: int = 0, include_deleted: bool = False) -> List[Dict]:
        """Obtener lista de videos con filtros opcionales"""
        if include_deleted:
            query = "SELECT * FROM videos WHERE 1=1"
        else:
            query = "SELECT * FROM videos WHERE deleted_at IS NULL"
        params = []
        
        # Aplicar filtros
        if filters:
            if filters.get('creator_name'):
                query += " AND creator_name LIKE ?"
                params.append(f"%{filters['creator_name']}%")
            
            if filters.get('creator_name_exact'):
                query += " AND creator_name = ?"
                params.append(filters['creator_name_exact'])
            
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
        if limit and limit > 0:
            query += " LIMIT ?"
            params.append(limit)
            if offset:
                query += " OFFSET ?"
                params.append(offset)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def count_videos(self, filters: Dict = None, include_deleted: bool = False) -> int:
        """Contar videos que coinciden con los filtros"""
        if include_deleted:
            query = "SELECT COUNT(*) FROM videos WHERE 1=1"
        else:
            query = "SELECT COUNT(*) FROM videos WHERE deleted_at IS NULL"
        params = []
        
        # Aplicar los mismos filtros que get_videos
        if filters:
            if filters.get('creator_name'):
                query += " AND creator_name LIKE ?"
                params.append(f"%{filters['creator_name']}%")
            
            if filters.get('creator_name_exact'):
                query += " AND creator_name = ?"
                params.append(filters['creator_name_exact'])
            
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
            'thumbnail_path', 'title', 'post_url', 'external_video_id',  # Campos de contenido
            'creator_id', 'subscription_id',  # Relaciones
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
            else:
                logger.warning(f"⚠️ Video {video_id} no encontrado o no se actualizó (rowcount: {cursor.rowcount})")
            return success
    
    def batch_update_videos(self, video_updates: List[Dict]) -> Tuple[int, int]:
        """
        🚀 OPTIMIZADO: Actualizar múltiples videos en una sola transacción
        
        Args:
            video_updates: Lista de diccionarios con formato:
                          [{'video_id': int, 'updates': dict}, ...]
        
        Returns:
            Tuple (exitosos, fallidos)
        """
        if not video_updates:
            return 0, 0
        
        successful = 0
        failed = 0
        
        allowed_fields = [
            'final_music', 'final_music_artist', 'final_characters', 'difficulty_level',
            'edit_status', 'edited_video_path', 'notes', 'processing_status', 'error_message',
            'thumbnail_path', 'title', 'post_url', 'external_video_id',  # Campos de contenido
            'creator_id', 'subscription_id',  # Relaciones
            'detected_music', 'detected_music_artist', 'detected_music_confidence', 'music_source', 'detected_characters'
        ]
        
        # Usar una sola transacción para todas las actualizaciones
        with self.get_connection() as conn:
            try:
                for video_update in video_updates:
                    video_id = video_update.get('video_id')
                    updates = video_update.get('updates', {})
                    
                    if not video_id or not updates:
                        failed += 1
                        continue
                    
                    # Construir query de actualización dinámica
                    set_clauses = []
                    params = []
                    
                    for field, value in updates.items():
                        if field in allowed_fields:
                            set_clauses.append(f"{field} = ?")
                            # Convertir listas a JSON para campos de personajes
                            if field in ['final_characters', 'detected_characters'] and isinstance(value, list):
                                value = json.dumps(value)
                            params.append(value)
                    
                    if not set_clauses:
                        failed += 1
                        continue
                    
                    # Agregar timestamp de actualización
                    set_clauses.append("last_updated = CURRENT_TIMESTAMP")
                    params.append(video_id)
                    
                    query = f"UPDATE videos SET {', '.join(set_clauses)} WHERE id = ?"
                    
                    try:
                        cursor = conn.execute(query, params)
                        if cursor.rowcount > 0:
                            successful += 1
                        else:
                            failed += 1
                    except Exception as e:
                        logger.debug(f"Error actualizando video {video_id}: {e}")
                        failed += 1
                
                # Commit de toda la transacción al final
                conn.commit()
                logger.info(f"Batch update completado: {successful} exitosos, {failed} fallidos")
                
            except Exception as e:
                # Si hay error general, rollback
                conn.rollback()
                logger.error(f"Error en batch update, rollback realizado: {e}")
                return 0, len(video_updates)
        
        return successful, failed
    
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
            
            # Total de videos (excluyendo eliminados)
            cursor = conn.execute('SELECT COUNT(*) FROM videos WHERE deleted_at IS NULL')
            stats['total_videos'] = cursor.fetchone()[0]
            
            # Videos por estado (excluyendo eliminados)
            cursor = conn.execute('SELECT edit_status, COUNT(*) FROM videos WHERE deleted_at IS NULL GROUP BY edit_status')
            stats['by_status'] = dict(cursor.fetchall())
            
            # Videos por plataforma (excluyendo eliminados)
            cursor = conn.execute('SELECT platform, COUNT(*) FROM videos WHERE deleted_at IS NULL GROUP BY platform')
            stats['by_platform'] = dict(cursor.fetchall())
            
            # Videos con música detectada (excluyendo eliminados)
            cursor = conn.execute('''
                SELECT COUNT(*) FROM videos 
                WHERE deleted_at IS NULL AND (detected_music IS NOT NULL OR final_music IS NOT NULL)
            ''')
            stats['with_music'] = cursor.fetchone()[0]
            
            # Videos con personajes detectados (excluyendo eliminados)
            cursor = conn.execute('''
                SELECT COUNT(*) FROM videos 
                WHERE deleted_at IS NULL AND detected_characters IS NOT NULL AND detected_characters != '[]'
            ''')
            stats['with_characters'] = cursor.fetchone()[0]
            
            return stats
    
    def soft_delete_video(self, video_id: int, deleted_by: str = "user", deletion_reason: str = "") -> bool:
        """
        Marcar un video como eliminado (soft delete)
        
        Args:
            video_id: ID del video a eliminar
            deleted_by: Usuario que realiza la eliminación
            deletion_reason: Razón de la eliminación
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    UPDATE videos 
                    SET deleted_at = CURRENT_TIMESTAMP,
                        deleted_by = ?,
                        deletion_reason = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ? AND deleted_at IS NULL
                ''', (deleted_by, deletion_reason, video_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Video {video_id} marcado como eliminado por {deleted_by}")
                    return True
                else:
                    logger.warning(f"Video {video_id} no encontrado o ya estaba eliminado")
                    return False
                    
        except Exception as e:
            logger.error(f"Error eliminando video {video_id}: {e}")
            return False
    
    def restore_video(self, video_id: int) -> bool:
        """
        Restaurar un video eliminado
        
        Args:
            video_id: ID del video a restaurar
            
        Returns:
            bool: True si se restauró exitosamente
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    UPDATE videos 
                    SET deleted_at = NULL,
                        deleted_by = NULL,
                        deletion_reason = NULL,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ? AND deleted_at IS NOT NULL
                ''', (video_id,))
                
                if cursor.rowcount > 0:
                    logger.info(f"Video {video_id} restaurado exitosamente")
                    return True
                else:
                    logger.warning(f"Video {video_id} no encontrado o no estaba eliminado")
                    return False
                    
        except Exception as e:
            logger.error(f"Error restaurando video {video_id}: {e}")
            return False
    
    def permanent_delete_video(self, video_id: int) -> bool:
        """
        Eliminar permanentemente un video de la base de datos
        ⚠️ PELIGROSO: Esta acción no se puede deshacer
        
        Args:
            video_id: ID del video a eliminar permanentemente
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            with self.get_connection() as conn:
                # Eliminar referencias en downloader_mapping primero
                conn.execute('DELETE FROM downloader_mapping WHERE video_id = ?', (video_id,))
                
                # Eliminar el video
                cursor = conn.execute('DELETE FROM videos WHERE id = ?', (video_id,))
                
                if cursor.rowcount > 0:
                    logger.warning(f"Video {video_id} ELIMINADO PERMANENTEMENTE")
                    return True
                else:
                    logger.warning(f"Video {video_id} no encontrado para eliminación permanente")
                    return False
                    
        except Exception as e:
            logger.error(f"Error eliminando permanentemente video {video_id}: {e}")
            return False
    
    def get_deleted_videos(self, limit: int = None, offset: int = 0) -> List[Dict]:
        """
        Obtener videos eliminados (papelera)
        
        Args:
            limit: Límite de resultados
            offset: Offset para paginación
            
        Returns:
            Lista de videos eliminados
        """
        query = "SELECT * FROM videos WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC"
        params = []
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def count_deleted_videos(self) -> int:
        """Contar videos en papelera"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM videos WHERE deleted_at IS NOT NULL')
            return cursor.fetchone()[0]
    
    def bulk_delete_videos(self, video_ids: List[int], deleted_by: str = "user", deletion_reason: str = "") -> Tuple[int, int]:
        """
        Eliminar múltiples videos (soft delete)
        
        Args:
            video_ids: Lista de IDs de videos a eliminar
            deleted_by: Usuario que realiza la eliminación
            deletion_reason: Razón de la eliminación
            
        Returns:
            Tuple (exitosos, fallidos)
        """
        if not video_ids:
            return 0, 0
            
        successful = 0
        failed = 0
        
        for video_id in video_ids:
            if self.soft_delete_video(video_id, deleted_by, deletion_reason):
                successful += 1
            else:
                failed += 1
        
        logger.info(f"Eliminación masiva: {successful} exitosos, {failed} fallidos")
        return successful, failed
    
    def bulk_restore_videos(self, video_ids: List[int]) -> Tuple[int, int]:
        """
        Restaurar múltiples videos
        
        Args:
            video_ids: Lista de IDs de videos a restaurar
            
        Returns:
            Tuple (exitosos, fallidos)
        """
        if not video_ids:
            return 0, 0
            
        successful = 0
        failed = 0
        
        for video_id in video_ids:
            if self.restore_video(video_id):
                successful += 1
            else:
                failed += 1
        
        logger.info(f"Restauración masiva: {successful} exitosos, {failed} fallidos")
        return successful, failed
    
    # 🚀 MIGRADOS: Métodos optimizados de optimized_database.py
    
    def get_existing_paths_only(self) -> set:
        """
        🚀 OPTIMIZADO: Solo obtener file_paths para verificación de duplicados (10x más rápido)
        
        Returns:
            Set de file_paths existentes para verificación O(1)
        """
        import time
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT file_path FROM videos WHERE deleted_at IS NULL")
            result = {row[0] for row in cursor.fetchall()}
        
        # Track performance
        execution_time = time.time() - start_time
        self._track_query('get_existing_paths_only', execution_time)
        
        return result
    
    def get_video_by_path_or_name(self, file_path: str, file_name: str) -> Optional[Dict]:
        """
        🚀 OPTIMIZADO: Buscar por ruta O nombre en una sola consulta SQL optimizada
        
        Args:
            file_path: Ruta completa del archivo
            file_name: Nombre del archivo
            
        Returns:
            Diccionario con datos del video o None si no se encuentra
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM videos 
                WHERE (file_path = ? OR file_name = ?) AND deleted_at IS NULL
                LIMIT 1
            """, (file_path, file_name))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_pending_videos_filtered(self, platform_filter: str = None, 
                                   source_filter: str = 'all', limit: int = None) -> List[Dict]:
        """
        🚀 OPTIMIZADO: Obtener videos pendientes con filtros SQL nativos (5x más rápido)
        
        Args:
            platform_filter: Filtro de plataforma ('youtube', 'tiktok', 'instagram', 'all', etc.)
            source_filter: Filtro de fuente ('db', 'organized', 'all')
            limit: Límite de resultados
            
        Returns:
            Lista de videos pendientes filtrados
        """
        import time
        start_time = time.time()
        
        query = "SELECT * FROM videos WHERE processing_status = 'pendiente' AND deleted_at IS NULL"
        params = []
        
        # Aplicar filtros de plataforma en SQL
        if platform_filter and platform_filter != 'all-platforms':
            if platform_filter == 'other':
                # Filtrar plataformas adicionales (no principales)
                query += " AND platform NOT IN ('youtube', 'tiktok', 'instagram')"
            elif isinstance(platform_filter, list):
                # Lista de plataformas
                placeholders = ','.join(['?' for _ in platform_filter])
                query += f" AND platform IN ({placeholders})"
                params.extend(platform_filter)
            else:
                # Plataforma específica
                query += " AND platform = ?"
                params.append(platform_filter)
        
        # Ordenar por fecha de agregado (más recientes primero)
        query += " ORDER BY created_at DESC"
        
        # Aplicar límite
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            result = [dict(row) for row in cursor.fetchall()]
        
        # Track performance  
        execution_time = time.time() - start_time
        self._track_query('get_pending_videos_filtered', execution_time)
        
        return result
    
    def check_videos_exist_batch(self, file_paths: List[str]) -> Dict[str, bool]:
        """
        🚀 OPTIMIZADO: Verificar existencia de múltiples videos en una sola query (O(1))
        
        Args:
            file_paths: Lista de rutas de archivos a verificar
            
        Returns:
            Diccionario {file_path: bool} indicando existencia
        """
        if not file_paths:
            return {}
        
        # Crear placeholders para la consulta IN
        placeholders = ','.join(['?' for _ in file_paths])
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT file_path FROM videos 
                WHERE file_path IN ({placeholders}) AND deleted_at IS NULL
            """, file_paths)
            
            existing_paths = {row[0] for row in cursor.fetchall()}
            
            # Crear diccionario de resultados
            return {path: path in existing_paths for path in file_paths}
    
    def get_videos_by_paths_batch(self, file_paths: List[str]) -> Dict[str, Dict]:
        """
        🚀 OPTIMIZADO: Obtener múltiples videos por sus rutas en una sola query
        
        Args:
            file_paths: Lista de rutas de archivos
            
        Returns:
            Diccionario {file_path: video_data}
        """
        if not file_paths:
            return {}
        
        placeholders = ','.join(['?' for _ in file_paths])
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT * FROM videos 
                WHERE file_path IN ({placeholders}) AND deleted_at IS NULL
            """, file_paths)
            
            results = {}
            for row in cursor.fetchall():
                video_data = dict(row)
                results[video_data['file_path']] = video_data
            
            return results
    
    # ========================================
    # 🆕 NUEVAS FUNCIONES PARA SISTEMA REESTRUCTURADO
    # ========================================
    
    # --- GESTIÓN DE CREADORES ---
    
    def create_creator(self, name: str, display_name: str = None) -> int:
        """Crear un nuevo creador"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO creators (name, display_name)
                VALUES (?, ?)
            ''', (name, display_name or name))
            creator_id = cursor.lastrowid
            logger.info(f"Creador creado con ID {creator_id}: {name}")
            return creator_id
    
    def get_creator_by_name(self, name: str) -> Optional[Dict]:
        """Obtener creador por nombre"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM creators WHERE name = ?', (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_creator_with_urls(self, creator_id: int) -> Optional[Dict]:
        """Obtener creador con sus URLs por plataforma"""
        with self.get_connection() as conn:
            # Obtener datos del creador
            cursor = conn.execute('SELECT * FROM creators WHERE id = ?', (creator_id,))
            creator_row = cursor.fetchone()
            if not creator_row:
                return None
                
            creator = dict(creator_row)
            
            # Obtener URLs por plataforma
            cursor = conn.execute('''
                SELECT platform, url, username 
                FROM creator_urls 
                WHERE creator_id = ?
            ''', (creator_id,))
            
            creator['urls'] = {}
            for row in cursor.fetchall():
                creator['urls'][row[0]] = {
                    'url': row[1],
                    'username': row[2]
                }
            
            return creator
    
    def add_creator_url(self, creator_id: int, platform: str, url: str, username: str = None) -> bool:
        """Agregar URL de creador para una plataforma"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO creator_urls (creator_id, platform, url, username)
                    VALUES (?, ?, ?, ?)
                ''', (creator_id, platform, url, username))
                logger.info(f"URL agregada para creador {creator_id} en {platform}: {url}")
                return True
        except Exception as e:
            logger.error(f"Error agregando URL de creador: {e}")
            return False
    
    # --- GESTIÓN DE SUSCRIPCIONES ---
    
    def create_subscription(self, name: str, type: str, platform: str, 
                          creator_id: int = None, subscription_url: str = None,
                          external_id: str = None, metadata: str = None) -> int:
        """Crear una nueva suscripción"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO subscriptions (name, type, platform, creator_id, subscription_url, external_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, type, platform, creator_id, subscription_url, external_id, metadata))
            subscription_id = cursor.lastrowid
            logger.info(f"Suscripción creada con ID {subscription_id}: {name} ({type})")
            return subscription_id
    
    def get_subscription_by_name_and_platform(self, name: str, platform: str, type: str = None) -> Optional[Dict]:
        """Obtener suscripción por nombre y plataforma"""
        with self.get_connection() as conn:
            if type:
                cursor = conn.execute('''
                    SELECT * FROM subscriptions 
                    WHERE name = ? AND platform = ? AND type = ?
                ''', (name, platform, type))
            else:
                cursor = conn.execute('''
                    SELECT * FROM subscriptions 
                    WHERE name = ? AND platform = ?
                ''', (name, platform))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_subscriptions_by_creator(self, creator_id: int) -> List[Dict]:
        """Obtener todas las suscripciones de un creador"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM subscriptions 
                WHERE creator_id = ?
                ORDER BY platform, type, name
            ''', (creator_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_subscriptions_by_platform_and_type(self, platform: str, type: str) -> List[Dict]:
        """Obtener suscripciones por plataforma y tipo"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM subscriptions 
                WHERE platform = ? AND type = ?
                ORDER BY name
            ''', (platform, type))
            return [dict(row) for row in cursor.fetchall()]
    
    # --- GESTIÓN DE LISTAS DE VIDEOS ---
    
    def add_video_to_list(self, video_id: int, list_type: str, source_path: str = None) -> bool:
        """Agregar video a una lista específica"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO video_lists (video_id, list_type, source_path)
                    VALUES (?, ?, ?)
                ''', (video_id, list_type, source_path))
                return True
        except Exception as e:
            logger.error(f"Error agregando video {video_id} a lista {list_type}: {e}")
            return False
    
    def get_video_lists(self, video_id: int) -> List[str]:
        """Obtener todas las listas a las que pertenece un video"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT list_type FROM video_lists 
                WHERE video_id = ?
            ''', (video_id,))
            return [row[0] for row in cursor.fetchall()]
    
    def get_videos_by_list_type(self, list_type: str, platform: str = None, limit: int = None) -> List[Dict]:
        """Obtener videos por tipo de lista"""
        query = '''
            SELECT v.*, vl.list_type, vl.source_path
            FROM videos v
            JOIN video_lists vl ON v.id = vl.video_id
            WHERE vl.list_type = ? AND v.deleted_at IS NULL
        '''
        params = [list_type]
        
        if platform:
            query += ' AND v.platform = ?'
            params.append(platform)
            
        query += ' ORDER BY v.created_at DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # --- QUERIES COMPLEJAS PARA FRONTEND ---
    
    def get_videos_by_creator_with_metadata(self, creator_id: int, platform: str = None, limit: int = None) -> List[Dict]:
        """Obtener videos de un creador con metadata completa"""
        query = '''
            SELECT 
                v.*,
                c.name as creator_name,
                c.display_name as creator_display_name,
                s.name as subscription_name,
                s.type as subscription_type,
                s.subscription_url,
                GROUP_CONCAT(vl.list_type) as list_types
            FROM videos v
            LEFT JOIN creators c ON v.creator_id = c.id
            LEFT JOIN subscriptions s ON v.subscription_id = s.id
            LEFT JOIN video_lists vl ON v.id = vl.video_id
            WHERE v.creator_id = ? AND v.deleted_at IS NULL
        '''
        params = [creator_id]
        
        if platform:
            query += ' AND v.platform = ?'
            params.append(platform)
            
        query += ' GROUP BY v.id ORDER BY v.created_at DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_videos_by_subscription_with_metadata(self, subscription_id: int, limit: int = None) -> List[Dict]:
        """Obtener videos de una suscripción con metadata completa"""
        query = '''
            SELECT 
                v.*,
                c.name as creator_name,
                c.display_name as creator_display_name,
                s.name as subscription_name,
                s.type as subscription_type,
                s.subscription_url,
                GROUP_CONCAT(vl.list_type) as list_types
            FROM videos v
            LEFT JOIN creators c ON v.creator_id = c.id
            LEFT JOIN subscriptions s ON v.subscription_id = s.id
            LEFT JOIN video_lists vl ON v.id = vl.video_id
            WHERE v.subscription_id = ? AND v.deleted_at IS NULL
            GROUP BY v.id
            ORDER BY v.created_at DESC
        '''
        params = [subscription_id]
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_creator_stats(self, creator_id: int) -> Dict:
        """Obtener estadísticas de un creador"""
        with self.get_connection() as conn:
            stats = {}
            
            # Total de videos
            cursor = conn.execute('''
                SELECT COUNT(*) FROM videos 
                WHERE creator_id = ? AND deleted_at IS NULL
            ''', (creator_id,))
            stats['total_videos'] = cursor.fetchone()[0]
            
            # Videos por plataforma
            cursor = conn.execute('''
                SELECT platform, COUNT(*) FROM videos 
                WHERE creator_id = ? AND deleted_at IS NULL
                GROUP BY platform
            ''', (creator_id,))
            stats['by_platform'] = dict(cursor.fetchall())
            
            # Videos por suscripción
            cursor = conn.execute('''
                SELECT s.name, s.type, COUNT(v.id) FROM videos v
                JOIN subscriptions s ON v.subscription_id = s.id
                WHERE v.creator_id = ? AND v.deleted_at IS NULL
                GROUP BY s.id, s.name, s.type
            ''', (creator_id,))
            stats['by_subscription'] = [{'name': row[0], 'type': row[1], 'count': row[2]} for row in cursor.fetchall()]
            
            return stats
    
    def get_platform_stats_external_sources(self) -> Dict:
        """Obtener estadísticas de plataformas desde fuentes externas"""
        with self.get_connection() as conn:
            stats = {}
            
            # Estadísticas por fuente externa
            cursor = conn.execute('''
                SELECT dm.external_db_source, v.platform, COUNT(v.id) as video_count
                FROM videos v
                JOIN downloader_mapping dm ON v.id = dm.video_id
                WHERE v.deleted_at IS NULL
                GROUP BY dm.external_db_source, v.platform
            ''')
            
            for row in cursor.fetchall():
                source = row[0] or 'unknown'
                platform = row[1]
                count = row[2]
                
                if source not in stats:
                    stats[source] = {}
                stats[source][platform] = count
            
            return stats
    
    # 🚀 MIGRADO: Sistema de métricas de performance de optimized_database.py
    
    def _track_query(self, query_name: str, execution_time: float):
        """Registrar tiempo de ejecución de una consulta para métricas"""
        if query_name not in self.query_times:
            self.query_times[query_name] = []
        
        self.query_times[query_name].append(execution_time)
        self.total_queries += 1
        
        # Mantener solo las últimas 100 mediciones por query
        if len(self.query_times[query_name]) > 100:
            self.query_times[query_name] = self.query_times[query_name][-100:]
    
    def get_performance_report(self) -> Dict:
        """
        🚀 OPTIMIZADO: Obtener reporte completo de performance de la base de datos
        
        Returns:
            Diccionario con métricas detalladas de performance
        """
        import statistics
        
        report = {
            'total_queries': self.total_queries,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': 0.0,
            'queries_by_type': {},
            'database_size_mb': 0.0,
            'performance_grade': 'UNKNOWN'
        }
        
        # Calcular hit rate si hay datos de cache
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests > 0:
            report['cache_hit_rate'] = round((self.cache_hits / total_cache_requests) * 100, 1)
        
        # Estadísticas por tipo de query
        for query_name, times in self.query_times.items():
            if times:
                report['queries_by_type'][query_name] = {
                    'count': len(times),
                    'avg_time_ms': round(statistics.mean(times) * 1000, 2),
                    'min_time_ms': round(min(times) * 1000, 2),
                    'max_time_ms': round(max(times) * 1000, 2),
                    'total_time_s': round(sum(times), 2)
                }
        
        # Tamaño de base de datos
        try:
            db_size_bytes = self.db_path.stat().st_size
            report['database_size_mb'] = round(db_size_bytes / (1024 * 1024), 2)
        except:
            pass
        
        # Calcular grade de performance
        report['performance_grade'] = self._calculate_performance_grade(report)
        
        return report
    
    def _calculate_performance_grade(self, report: Dict) -> str:
        """Calcular calificación de performance basada en métricas"""
        score = 100
        
        # Penalizar hit rate bajo
        if report['cache_hit_rate'] < 70:
            score -= 20
        elif report['cache_hit_rate'] < 85:
            score -= 10
        
        # Penalizar queries lentas
        for query_data in report['queries_by_type'].values():
            avg_time = query_data['avg_time_ms']
            if avg_time > 100:  # > 100ms
                score -= 15
            elif avg_time > 50:  # > 50ms
                score -= 5
        
        # Calificación final
        if score >= 90:
            return 'EXCELLENT'
        elif score >= 75:
            return 'GOOD'
        elif score >= 60:
            return 'AVERAGE'
        else:
            return 'NEEDS_IMPROVEMENT'
    
    def log_performance_summary(self):
        """Mostrar resumen de performance en logs"""
        report = self.get_performance_report()
        
        logger.info("="*50)
        logger.info("📊 DATABASE PERFORMANCE REPORT")
        logger.info("="*50)
        logger.info(f"Total Queries: {report['total_queries']}")
        logger.info(f"Cache Hit Rate: {report['cache_hit_rate']}%")
        logger.info(f"Database Size: {report['database_size_mb']} MB")
        logger.info(f"Performance Grade: {report['performance_grade']}")
        
        if report['queries_by_type']:
            logger.info("\nQuery Performance:")
            for query_name, stats in report['queries_by_type'].items():
                logger.info(f"  {query_name}: {stats['avg_time_ms']}ms avg ({stats['count']} calls)")
        
        logger.info("="*50)

# ⚠️ DEPRECATED: Instancia global removida para eliminar dependencias circulares
# Usar ServiceFactory.get_service('database') o get_database() desde service_factory
# 
# Funciones de compatibilidad temporal (serán removidas en futuras versiones)
def get_database_manager():
    """
    🔄 MIGRACIÓN: Función de compatibilidad temporal
    TODO: Reemplazar todos los usos con ServiceFactory.get_service('database')
    """
    from src.service_factory import get_database
    return get_database()

# Variable global para compatibilidad temporal
db = None

def _ensure_global_db():
    """Asegurar que db global esté inicializado (solo para compatibilidad)"""
    global db
    if db is None:
        db = get_database_manager()
    return db

# Monkey-patch para compatibilidad temporal
import sys
current_module = sys.modules[__name__]

class DatabaseProxy:
    """Proxy para mantener compatibilidad con uso de db.método()"""
    
    def __getattr__(self, name):
        # Asegurar que ServiceFactory registre el servicio como cargado
        from src.service_factory import get_database
        db_instance = get_database()
        return getattr(db_instance, name)

# Reemplazar la variable db con el proxy
db = DatabaseProxy()