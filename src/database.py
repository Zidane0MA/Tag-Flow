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
                    deletion_reason TEXT
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
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_deleted ON videos(deleted_at)')
            
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
                            video_data.get('description')
                        )
                        insert_data.append(insert_row)
                    
                    # Inserción con reemplazo para forzar actualización
                    conn.executemany('''
                        INSERT OR REPLACE INTO videos (
                            file_path, file_name, creator_name, platform,
                            file_size, duration_seconds, detected_music, detected_music_artist,
                            detected_music_confidence, detected_characters, music_source,
                            processing_status, description
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', insert_data)
                    
                    successful = len(insert_data)
                    logger.info(f"Inserción por lotes con FORCE exitosa: {successful} videos")
                else:
                    # Modo normal: insertar solo videos nuevos
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
                            video_data.get('description')
                        )
                        insert_data.append(insert_row)
                    
                    # Inserción normal
                    conn.executemany('''
                        INSERT INTO videos (
                            file_path, file_name, creator_name, platform,
                            file_size, duration_seconds, detected_music, detected_music_artist,
                            detected_music_confidence, detected_characters, music_source,
                            processing_status, description
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', insert_data)
                    
                    successful = len(insert_data)
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
            'thumbnail_path', 'description',
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