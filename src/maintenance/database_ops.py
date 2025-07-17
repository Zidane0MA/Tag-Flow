#!/usr/bin/env python3
"""
🗃️ Database Operations Module
Módulo especializado para operaciones de base de datos extraído de maintenance.py
"""

import os
import time
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import shutil

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos del proyecto
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from src.database import Database
from src.external_sources import ExternalSources
from src.video_processor import VideoProcessor

# Instancias globales
db = Database()
external_sources = ExternalSources()
video_processor = VideoProcessor()


class DatabaseOperations:
    """
    🗃️ Operaciones especializadas de base de datos
    
    Funcionalidades:
    - Población desde fuentes externas
    - Optimización de base de datos
    - Limpieza y migración de datos
    - Backup y restore
    - Operaciones por lotes optimizadas
    """
    
    def __init__(self):
        self.db = Database()
        self.external_sources = ExternalSources()
        self.video_processor = VideoProcessor()
    
    def populate_database(self, source: str = 'all', platform: Optional[str] = None, 
                         limit: Optional[int] = None, force: bool = False, 
                         file_path: Optional[str] = None, 
                         progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        🚀 OPTIMIZADO: Poblar la base de datos desde fuentes externas o un archivo específico
        
        Args:
            source: 'db', 'organized', 'all' - fuente de datos
            platform: 'youtube', 'tiktok', 'instagram' o None para todas
            limit: número máximo de videos a importar
            force: forzar reimportación de videos existentes
            file_path: ruta específica de un video para importar
            progress_callback: función para reportar progreso (processed, total, current_item)
            
        Returns:
            Dict con resultados de la operación
        """
        start_time = time.time()
        
        # NUEVA FUNCIONALIDAD: Importar archivo específico
        if file_path:
            return self._populate_single_file(file_path, force)
        
        # FUNCIONALIDAD OPTIMIZADA: Importar desde fuentes múltiples
        logger.info(f"🚀 Poblando base de datos OPTIMIZADO desde {source} (plataforma: {platform or 'todas'})")
        
        if limit:
            logger.info(f"Límite establecido: {limit} videos")
        
        try:
            # PASO 1: Obtener videos de fuentes externas
            logger.info("📥 Obteniendo videos de fuentes externas...")
            external_videos = self.external_sources.get_all_videos_from_source(source, platform, limit)
            
            if not external_videos:
                logger.info("No se encontraron videos para importar")
                return {
                    'success': True,
                    'imported': 0,
                    'errors': 0,
                    'duration': 0.0,
                    'message': 'No se encontraron videos para importar'
                }
            
            logger.info(f"Videos encontrados para procesar: {len(external_videos)}")
            
            # PASO 2: Verificación optimizada de duplicados
            if not force:
                logger.info("🔍 Verificando duplicados (optimizado)...")
                external_videos = self._filter_duplicates_optimized(external_videos)
            
            if not external_videos:
                logger.info("✅ Todos los videos ya están en la base de datos")
                return {
                    'success': True,
                    'imported': 0,
                    'errors': 0,
                    'duration': time.time() - start_time,
                    'message': 'Todos los videos ya están en la base de datos'
                }
            
            logger.info(f"Videos únicos para importar: {len(external_videos)}")
            
            # PASO 3: Extracción de metadatos en paralelo
            logger.info("⚡ Extrayendo metadatos en paralelo...")
            processed_videos = self._extract_metadata_parallel(external_videos, force, progress_callback)
            
            # PASO 4: Inserción por lotes optimizada
            logger.info("💾 Insertando videos por lotes...")
            imported, errors = self._insert_videos_batch(processed_videos, force, progress_callback)
            
            # Métricas finales
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"✅ Importación OPTIMIZADA completada en {duration:.2f}s")
            logger.info(f"   📊 Resultados: {imported} exitosos, {errors} errores")
            logger.info(f"   ⚡ Throughput: {imported/duration:.1f} videos/segundo")
            
            # PASO 5: Optimizar BD después de inserción masiva
            if imported > 50:  # Solo optimizar si se insertaron muchos videos
                logger.info("🔧 Optimizando base de datos...")
                try:
                    self.optimize_database()
                    logger.info("✅ Base de datos optimizada")
                except Exception as e:
                    logger.warning(f"Advertencia optimizando BD: {e}")
            
            return {
                'success': True,
                'imported': imported,
                'errors': errors,
                'duration': duration,
                'throughput': imported/duration if imported > 0 else 0,
                'total_found': len(external_videos) + imported,
                'message': f'Importados {imported} videos exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error en población de BD: {e}")
            return {
                'success': False,
                'error': str(e),
                'imported': 0,
                'errors': 1,
                'duration': time.time() - start_time
            }
    
    def optimize_database(self) -> Dict[str, Any]:
        """
        🔧 Optimizar base de datos SQLite
        
        Returns:
            Dict con resultados de la optimización
        """
        start_time = time.time()
        logger.info("🔧 Optimizando base de datos...")
        
        try:
            with self.db.get_connection() as conn:
                # VACUUM para compactar BD
                logger.info("🔄 Ejecutando VACUUM...")
                conn.execute('VACUUM')
                
                # ANALYZE para optimizar consultas
                logger.info("📊 Ejecutando ANALYZE...")
                conn.execute('ANALYZE')
                
                # Obtener estadísticas
                cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM videos")
                video_count = cursor.fetchone()[0]
                
                # Crear índices si no existen
                self._ensure_database_indexes(conn)
            
            duration = time.time() - start_time
            
            logger.info(f"✅ Base de datos optimizada en {duration:.2f}s")
            logger.info(f"   📊 Tamaño: {db_size / 1024 / 1024:.1f} MB")
            logger.info(f"   📹 Videos: {video_count}")
            
            return {
                'success': True,
                'duration': duration,
                'database_size_mb': db_size / 1024 / 1024,
                'video_count': video_count,
                'message': 'Base de datos optimizada exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error optimizando base de datos: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    def clear_database(self, platform: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """
        🗑️ Limpiar la base de datos (eliminar todos los videos o de una plataforma específica)
        
        Args:
            platform: plataforma específica a limpiar o None para todas
            force: forzar eliminación sin confirmación
            
        Returns:
            Dict con resultados de la limpieza
        """
        start_time = time.time()
        
        if platform:
            logger.info(f"🗑️ Limpiando videos de la plataforma: {platform}")
        else:
            logger.info("🗑️ Limpiando TODA la base de datos")
        
        try:
            # Contar videos a eliminar
            filters = {'platform': platform} if platform else {}
            videos_to_delete = self.db.get_videos(filters)
            
            if not videos_to_delete:
                logger.info("No hay videos para eliminar")
                return {
                    'success': True,
                    'deleted': 0,
                    'duration': 0.0,
                    'message': 'No hay videos para eliminar'
                }
            
            logger.info(f"Videos a eliminar: {len(videos_to_delete)}")
            
            if not force:
                # En modo no-force, solo reportar
                return {
                    'success': True,
                    'deleted': 0,
                    'videos_found': len(videos_to_delete),
                    'duration': time.time() - start_time,
                    'message': f'Encontrados {len(videos_to_delete)} videos, usar force=True para eliminar'
                }
            
            # Eliminar videos
            deleted = 0
            for video in videos_to_delete:
                try:
                    if self.db.delete_video(video['id']):
                        deleted += 1
                except Exception as e:
                    logger.error(f"Error eliminando video {video['id']}: {e}")
            
            # Resetear secuencia AUTOINCREMENT si se eliminaron todos los videos
            if not platform:  # Solo si se limpió toda la BD
                try:
                    with self.db.get_connection() as conn:
                        # Verificar si quedan videos
                        cursor = conn.execute("SELECT COUNT(*) FROM videos")
                        remaining_videos = cursor.fetchone()[0]
                        
                        # Si no quedan videos, resetear la secuencia
                        if remaining_videos == 0:
                            conn.execute("DELETE FROM sqlite_sequence WHERE name='videos'")
                            logger.info("✓ Secuencia AUTOINCREMENT reseteada")
                except Exception as e:
                    logger.error(f"Error reseteando secuencia: {e}")
            
            duration = time.time() - start_time
            
            logger.info(f"✅ Eliminados {deleted} videos en {duration:.2f}s")
            
            return {
                'success': True,
                'deleted': deleted,
                'videos_found': len(videos_to_delete),
                'duration': duration,
                'message': f'Eliminados {deleted} videos exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error limpiando base de datos: {e}")
            return {
                'success': False,
                'error': str(e),
                'deleted': 0,
                'duration': time.time() - start_time
            }
    
    def backup_database(self, backup_path: Optional[str] = None) -> Dict[str, Any]:
        """
        💾 Crear backup de la base de datos
        
        Args:
            backup_path: ruta específica del backup o None para automática
            
        Returns:
            Dict con resultados del backup
        """
        start_time = time.time()
        
        try:
            # Determinar ruta del backup
            if not backup_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"backup_database_{timestamp}.db"
            
            backup_path = Path(backup_path)
            
            # Obtener ruta de la BD actual
            db_path = Path(config.DATABASE_PATH if hasattr(config, 'DATABASE_PATH') else 'data/videos.db')
            
            if not db_path.exists():
                return {
                    'success': False,
                    'error': 'Base de datos no encontrada',
                    'duration': time.time() - start_time
                }
            
            logger.info(f"💾 Creando backup de {db_path} -> {backup_path}")
            
            # Crear directorio de backup si no existe
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copiar archivo de BD
            shutil.copy2(db_path, backup_path)
            
            # Verificar integridad del backup
            try:
                with sqlite3.connect(backup_path) as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM videos")
                    backup_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute("PRAGMA integrity_check")
                    integrity = cursor.fetchone()[0]
                    
                    if integrity != 'ok':
                        raise Exception(f"Integridad del backup fallida: {integrity}")
                        
            except Exception as e:
                # Eliminar backup corrupto
                if backup_path.exists():
                    backup_path.unlink()
                raise Exception(f"Backup corrupto: {e}")
            
            duration = time.time() - start_time
            backup_size = backup_path.stat().st_size
            
            logger.info(f"✅ Backup creado exitosamente en {duration:.2f}s")
            logger.info(f"   📁 Ruta: {backup_path}")
            logger.info(f"   📊 Tamaño: {backup_size / 1024 / 1024:.1f} MB")
            logger.info(f"   📹 Videos: {backup_count}")
            
            return {
                'success': True,
                'backup_path': str(backup_path),
                'backup_size_mb': backup_size / 1024 / 1024,
                'video_count': backup_count,
                'duration': duration,
                'message': f'Backup creado exitosamente: {backup_path}'
            }
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    def restore_database(self, backup_path: str, force: bool = False) -> Dict[str, Any]:
        """
        🔄 Restaurar base de datos desde backup
        
        Args:
            backup_path: ruta del backup
            force: forzar restauración sin confirmación
            
        Returns:
            Dict con resultados de la restauración
        """
        start_time = time.time()
        
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': f'Backup no encontrado: {backup_path}',
                    'duration': time.time() - start_time
                }
            
            # Verificar integridad del backup
            try:
                with sqlite3.connect(backup_path) as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM videos")
                    backup_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute("PRAGMA integrity_check")
                    integrity = cursor.fetchone()[0]
                    
                    if integrity != 'ok':
                        return {
                            'success': False,
                            'error': f'Backup corrupto: {integrity}',
                            'duration': time.time() - start_time
                        }
                        
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Error verificando backup: {e}',
                    'duration': time.time() - start_time
                }
            
            # Obtener ruta de la BD actual
            db_path = Path(config.DATABASE_PATH if hasattr(config, 'DATABASE_PATH') else 'data/videos.db')
            
            if not force and db_path.exists():
                # Contar videos actuales
                try:
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.execute("SELECT COUNT(*) FROM videos")
                        current_count = cursor.fetchone()[0]
                        
                    return {
                        'success': True,
                        'restored': False,
                        'current_count': current_count,
                        'backup_count': backup_count,
                        'duration': time.time() - start_time,
                        'message': f'BD actual tiene {current_count} videos, backup tiene {backup_count}. Usar force=True para restaurar'
                    }
                except Exception as e:
                    logger.warning(f"Error leyendo BD actual: {e}")
            
            logger.info(f"🔄 Restaurando BD desde {backup_path}")
            
            # Crear backup de la BD actual si existe
            if db_path.exists():
                backup_current = db_path.parent / f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(db_path, backup_current)
                logger.info(f"💾 BD actual respaldada en: {backup_current}")
            
            # Restaurar BD
            shutil.copy2(backup_path, db_path)
            
            duration = time.time() - start_time
            
            logger.info(f"✅ Base de datos restaurada en {duration:.2f}s")
            logger.info(f"   📹 Videos restaurados: {backup_count}")
            
            return {
                'success': True,
                'restored': True,
                'video_count': backup_count,
                'duration': duration,
                'message': f'Base de datos restaurada exitosamente: {backup_count} videos'
            }
            
        except Exception as e:
            logger.error(f"Error restaurando BD: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    def migrate_database(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """
        🔄 Migrar esquema de base de datos
        
        Args:
            target_version: versión objetivo o None para última
            
        Returns:
            Dict con resultados de la migración
        """
        start_time = time.time()
        
        try:
            logger.info("🔄 Iniciando migración de base de datos...")
            
            # Obtener versión actual
            current_version = self._get_database_version()
            logger.info(f"📊 Versión actual: {current_version}")
            
            # Determinar migraciones necesarias
            migrations = self._get_pending_migrations(current_version, target_version)
            
            if not migrations:
                logger.info("✅ Base de datos ya está actualizada")
                return {
                    'success': True,
                    'migrations_applied': 0,
                    'current_version': current_version,
                    'duration': time.time() - start_time,
                    'message': 'Base de datos ya está actualizada'
                }
            
            logger.info(f"🔄 Aplicando {len(migrations)} migraciones...")
            
            # Crear backup antes de migrar
            backup_result = self.backup_database()
            if not backup_result['success']:
                logger.warning(f"No se pudo crear backup: {backup_result['error']}")
            
            # Aplicar migraciones
            applied = 0
            for migration in migrations:
                try:
                    logger.info(f"🔄 Aplicando migración: {migration['name']}")
                    self._apply_migration(migration)
                    applied += 1
                except Exception as e:
                    logger.error(f"Error aplicando migración {migration['name']}: {e}")
                    raise
            
            # Actualizar versión
            new_version = target_version or self._get_latest_version()
            self._set_database_version(new_version)
            
            duration = time.time() - start_time
            
            logger.info(f"✅ Migración completada en {duration:.2f}s")
            logger.info(f"   📊 Versión: {current_version} -> {new_version}")
            logger.info(f"   🔄 Migraciones aplicadas: {applied}")
            
            return {
                'success': True,
                'migrations_applied': applied,
                'old_version': current_version,
                'new_version': new_version,
                'duration': duration,
                'message': f'Migración completada: {applied} migraciones aplicadas'
            }
            
        except Exception as e:
            logger.error(f"Error en migración: {e}")
            return {
                'success': False,
                'error': str(e),
                'migrations_applied': applied if 'applied' in locals() else 0,
                'duration': time.time() - start_time
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        📊 Obtener estadísticas detalladas de la base de datos
        
        Returns:
            Dict con estadísticas completas
        """
        try:
            with self.db.get_connection() as conn:
                # Estadísticas básicas
                cursor = conn.execute("SELECT COUNT(*) FROM videos")
                total_videos = cursor.fetchone()[0]
                
                # Videos por plataforma
                cursor = conn.execute("""
                    SELECT platform, COUNT(*) as count 
                    FROM videos 
                    GROUP BY platform
                    ORDER BY count DESC
                """)
                platform_stats = dict(cursor.fetchall())
                
                # Videos por estado
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN thumbnail_path IS NOT NULL THEN 1 END) as with_thumbnails,
                        COUNT(CASE WHEN detected_characters IS NOT NULL AND detected_characters != '[]' THEN 1 END) as with_characters,
                        COUNT(CASE WHEN detected_music IS NOT NULL THEN 1 END) as with_music,
                        COUNT(CASE WHEN is_deleted = 1 THEN 1 END) as deleted
                    FROM videos
                """)
                status_stats = dict(cursor.fetchone())
                
                # Estadísticas de archivos
                cursor = conn.execute("""
                    SELECT 
                        AVG(file_size) as avg_size,
                        MAX(file_size) as max_size,
                        MIN(file_size) as min_size,
                        SUM(file_size) as total_size
                    FROM videos
                    WHERE file_size IS NOT NULL
                """)
                file_stats = dict(cursor.fetchone())
                
                # Información de la BD
                cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                cursor = conn.execute("PRAGMA user_version")
                db_version = cursor.fetchone()[0]
                
                # Estadísticas de rendimiento
                cursor = conn.execute("""
                    SELECT 
                        MIN(created_at) as oldest_video,
                        MAX(created_at) as newest_video,
                        COUNT(CASE WHEN created_at >= datetime('now', '-1 day') THEN 1 END) as added_last_24h,
                        COUNT(CASE WHEN created_at >= datetime('now', '-7 days') THEN 1 END) as added_last_week
                    FROM videos
                    WHERE created_at IS NOT NULL
                """)
                time_stats = dict(cursor.fetchone())
                
                return {
                    'success': True,
                    'total_videos': total_videos,
                    'platform_stats': platform_stats,
                    'status_stats': status_stats,
                    'file_stats': {
                        'avg_size_mb': (file_stats['avg_size'] or 0) / 1024 / 1024,
                        'max_size_mb': (file_stats['max_size'] or 0) / 1024 / 1024,
                        'min_size_mb': (file_stats['min_size'] or 0) / 1024 / 1024,
                        'total_size_gb': (file_stats['total_size'] or 0) / 1024 / 1024 / 1024
                    },
                    'database_info': {
                        'size_mb': db_size / 1024 / 1024,
                        'version': db_version,
                        'path': str(Path(config.DATABASE_PATH if hasattr(config, 'DATABASE_PATH') else 'data/videos.db').resolve())
                    },
                    'time_stats': time_stats,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de BD: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Métodos privados auxiliares
    
    def _populate_single_file(self, file_path: str, force: bool = False) -> Dict[str, Any]:
        """Importar un archivo específico"""
        logger.info(f"📁 Importando archivo específico: {file_path}")
        
        try:
            # Extraer información del video específico
            video_data = self.external_sources.extract_single_video_info(file_path)
            
            if not video_data:
                return {
                    'success': False,
                    'error': 'No se pudo extraer información del archivo',
                    'imported': 0,
                    'errors': 1
                }
            
            # Verificar si ya existe en la BD
            existing = self.db.get_video_by_path(video_data['file_path'])
            if existing and not force:
                return {
                    'success': True,
                    'imported': 0,
                    'errors': 0,
                    'message': f'El video ya existe en la BD (ID: {existing["id"]}), usar force=True para actualizar'
                }
            
            # Preparar datos para la BD
            db_data = self._prepare_db_data(video_data)
            
            # Obtener metadatos del archivo
            db_data.update(self._extract_file_metadata(video_data))
            
            # Agregar o actualizar en la BD
            if existing and force:
                # Actualizar registro existente
                self.db.update_video(existing['id'], db_data)
                logger.info(f"✅ Video actualizado: {video_data['file_name']}")
            else:
                # Insertar nuevo registro
                video_id = self.db.add_video(db_data)
                logger.info(f"✅ Video agregado: {video_data['file_name']} (ID: {video_id})")
            
            return {
                'success': True,
                'imported': 1,
                'errors': 0,
                'message': f'Video importado exitosamente: {video_data["file_name"]}'
            }
            
        except Exception as e:
            logger.error(f"Error importando archivo: {e}")
            return {
                'success': False,
                'error': str(e),
                'imported': 0,
                'errors': 1
            }
    
    def _filter_duplicates_optimized(self, external_videos: List[Dict]) -> List[Dict]:
        """Filtrar duplicados usando consulta optimizada"""
        if not external_videos:
            return []
        
        # Crear mapping de rutas para consulta rápida
        file_paths = [video['file_path'] for video in external_videos]
        
        # Consultar BD por todas las rutas de una vez
        existing_paths = set()
        if file_paths:
            placeholders = ','.join(['?' for _ in file_paths])
            query = f"SELECT file_path FROM videos WHERE file_path IN ({placeholders})"
            
            with self.db.get_connection() as conn:
                cursor = conn.execute(query, file_paths)
                existing_paths = {row[0] for row in cursor.fetchall()}
        
        # Filtrar videos que no existen en BD
        unique_videos = [video for video in external_videos if video['file_path'] not in existing_paths]
        
        logger.info(f"🔍 Duplicados filtrados: {len(external_videos)} -> {len(unique_videos)}")
        return unique_videos
    
    def _extract_metadata_parallel(self, videos: List[Dict], force: bool = False, 
                                  progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Extraer metadatos en paralelo"""
        if not videos:
            return []
        
        processed_videos = []
        max_workers = min(3, len(videos))  # Limitar workers para evitar sobrecarga
        
        def process_video(video_data):
            try:
                # Preparar datos básicos
                db_data = self._prepare_db_data(video_data)
                
                # Extraer metadatos del archivo
                file_metadata = self._extract_file_metadata(video_data)
                db_data.update(file_metadata)
                
                return db_data
            except Exception as e:
                logger.error(f"Error procesando video {video_data.get('file_name', 'unknown')}: {e}")
                return None
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas
            future_to_video = {
                executor.submit(process_video, video): video 
                for video in videos
            }
            
            # Recopilar resultados
            for i, future in enumerate(as_completed(future_to_video), 1):
                try:
                    result = future.result()
                    if result:
                        processed_videos.append(result)
                    
                    # Callback de progreso
                    if progress_callback:
                        progress_callback(i, len(videos), result.get('file_name', 'unknown') if result else 'error')
                        
                except Exception as e:
                    logger.error(f"Error procesando video: {e}")
        
        return processed_videos
    
    def _insert_videos_batch(self, videos: List[Dict], force: bool = False, 
                            progress_callback: Optional[Callable] = None) -> Tuple[int, int]:
        """Insertar videos en lotes optimizados"""
        if not videos:
            return 0, 0
        
        imported = 0
        errors = 0
        batch_size = 50  # Tamaño del lote
        
        for i in range(0, len(videos), batch_size):
            batch = videos[i:i + batch_size]
            
            try:
                # Preparar datos para inserción por lotes
                batch_data = []
                for video in batch:
                    batch_data.append(video)
                
                # Insertar lote
                batch_success, batch_failed = self.db.batch_insert_videos(batch_data)
                imported += batch_success
                errors += batch_failed
                
                # Callback de progreso
                if progress_callback:
                    progress_callback(i + len(batch), len(videos), f"Lote {i//batch_size + 1}")
                
                logger.info(f"💾 Lote {i//batch_size + 1}: {batch_success} exitosos, {batch_failed} fallidos")
                
            except Exception as e:
                logger.error(f"Error insertando lote: {e}")
                errors += len(batch)
        
        return imported, errors
    
    def _prepare_db_data(self, video_data: Dict) -> Dict:
        """Preparar datos para inserción en BD"""
        return {
            'file_path': video_data['file_path'],
            'file_name': video_data['file_name'],
            'platform': video_data.get('platform', 'unknown'),
            'creator_name': video_data.get('creator_name'),
            'title': video_data.get('title'),
            'description': video_data.get('description'),
            'upload_date': video_data.get('upload_date'),
            'duration': video_data.get('duration'),
            'file_size': video_data.get('file_size'),
            'created_at': datetime.now().isoformat()
        }
    
    def _extract_file_metadata(self, video_data: Dict) -> Dict:
        """Extraer metadatos del archivo"""
        try:
            file_path = Path(video_data['file_path'])
            
            metadata = {
                'file_size': file_path.stat().st_size,
                'file_extension': file_path.suffix.lower(),
                'file_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            
            # Extraer metadatos adicionales con video_processor si está disponible
            if hasattr(self.video_processor, 'extract_metadata'):
                video_metadata = self.video_processor.extract_metadata(str(file_path))
                if video_metadata:
                    metadata.update(video_metadata)
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Error extrayendo metadatos de archivo: {e}")
            return {}
    
    def _ensure_database_indexes(self, conn):
        """Asegurar que existan índices optimizados"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_videos_platform ON videos(platform)",
            "CREATE INDEX IF NOT EXISTS idx_videos_creator ON videos(creator_name)",
            "CREATE INDEX IF NOT EXISTS idx_videos_file_path ON videos(file_path)",
            "CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_videos_is_deleted ON videos(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_videos_upload_date ON videos(upload_date)"
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Error creando índice: {e}")
    
    def _get_database_version(self) -> str:
        """Obtener versión actual de la BD"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("PRAGMA user_version")
                version = cursor.fetchone()[0]
                return str(version)
        except Exception:
            return "0"
    
    def _set_database_version(self, version: str):
        """Establecer versión de la BD"""
        try:
            with self.db.get_connection() as conn:
                conn.execute(f"PRAGMA user_version = {version}")
        except Exception as e:
            logger.error(f"Error estableciendo versión de BD: {e}")
    
    def _get_latest_version(self) -> str:
        """Obtener última versión disponible"""
        return "1"  # Implementar versionado según necesidades
    
    def _get_pending_migrations(self, current_version: str, target_version: Optional[str]) -> List[Dict]:
        """Obtener migraciones pendientes"""
        # Implementar lógica de migraciones según necesidades
        return []
    
    def _apply_migration(self, migration: Dict):
        """Aplicar migración específica"""
        # Implementar aplicación de migraciones
        pass


# Funciones de conveniencia para compatibilidad
def populate_database(source: str = 'all', platform: Optional[str] = None, 
                     limit: Optional[int] = None, force: bool = False, 
                     file_path: Optional[str] = None) -> Dict[str, Any]:
    """Función de conveniencia para poblar BD"""
    ops = DatabaseOperations()
    return ops.populate_database(source, platform, limit, force, file_path)

def optimize_database() -> Dict[str, Any]:
    """Función de conveniencia para optimizar BD"""
    ops = DatabaseOperations()
    return ops.optimize_database()

def clear_database(platform: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """Función de conveniencia para limpiar BD"""
    ops = DatabaseOperations()
    return ops.clear_database(platform, force)

def backup_database(backup_path: Optional[str] = None) -> Dict[str, Any]:
    """Función de conveniencia para backup"""
    ops = DatabaseOperations()
    return ops.backup_database(backup_path)

def restore_database(backup_path: str, force: bool = False) -> Dict[str, Any]:
    """Función de conveniencia para restore"""
    ops = DatabaseOperations()
    return ops.restore_database(backup_path, force)

def get_database_stats() -> Dict[str, Any]:
    """Función de conveniencia para estadísticas"""
    ops = DatabaseOperations()
    return ops.get_database_stats()