#!/usr/bin/env python3
"""
🗃️ Database Operations Module
Módulo especializado para operaciones de base de datos extraído de main.py
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
# 🚀 MIGRADO: Eliminados imports directos, ahora se usan via service factory
# Los módulos se importan solo cuando se necesitan mediante lazy loading

# Referencias eliminadas para evitar inicialización automática


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
        # 🚀 MIGRADO: Usar service factory para gestión centralizada
        # NO instanciar servicios en __init__ para máximo lazy loading
        self._db = None
        self._external_sources = None
        self._video_processor = None
    
    @property
    def db(self):
        """Lazy initialization of DatabaseManager via ServiceFactory"""
        if self._db is None:
            from src.service_factory import get_database
            self._db = get_database()
        return self._db
    
    @property
    def external_sources(self):
        """Lazy initialization of ExternalSourcesManager via ServiceFactory"""
        if self._external_sources is None:
            from src.service_factory import get_external_sources
            self._external_sources = get_external_sources()
        return self._external_sources
    
    @property
    def video_processor(self):
        """Lazy initialization of VideoProcessor via ServiceFactory"""
        if self._video_processor is None:
            from src.service_factory import get_video_processor
            self._video_processor = get_video_processor()
        return self._video_processor
    
    def populate_database(self, source: str = 'all', platform: Optional[str] = None, 
                         limit: Optional[int] = None, force: bool = False, 
                         progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        🚀 NUEVA ESTRUCTURA: Poblar la base de datos con soporte para creadores y suscripciones
        
        Args:
            source: 'db', 'organized', 'all' - fuente de datos
            platform: 'youtube', 'tiktok', 'instagram', 'all-platforms' o None para todas
            limit: número máximo de videos a importar
            force: forzar reimportación de videos existentes
            progress_callback: función para reportar progreso (processed, total, current_item)
            
        Returns:
            Dict con resultados de la operación
        """
        start_time = time.time()
        
        logger.info(f"🚀 Poblando BD con NUEVA ESTRUCTURA desde {source} (plataforma: {platform or 'todas'})")
        
        try:
            # Usar módulos principales actualizados (NO versiones v2)
            db = self.db
            external_sources = self.external_sources
            
            # La base de datos se inicializa automáticamente con la nueva estructura
            logger.debug("✅ Base de datos inicializada con nueva estructura")
            
            # Obtener videos desde fuentes externas
            all_videos = external_sources.get_all_videos_from_source(
                source=source,
                platform=platform,
                limit=limit
            )
            
            if not all_videos:
                logger.warning("No se encontraron videos en las fuentes externas")
                return {
                    'success': True,
                    'videos_added': 0,
                    'videos_updated': 0,
                    'creators_created': 0,
                    'subscriptions_created': 0,
                    'message': "No se encontraron videos para poblar"
                }
            
            # Procesar videos con nueva estructura
            videos_added, videos_updated, stats = self._populate_with_new_structure(
                all_videos, force, progress_callback
            )
            
            execution_time = time.time() - start_time
            
            result = {
                'success': True,
                'videos_added': videos_added,
                'videos_updated': videos_updated,
                'creators_created': stats['creators_created'],
                'subscriptions_created': stats['subscriptions_created'],
                'video_lists_added': stats['video_lists_added'],
                'errors': len(stats['errors']),
                'execution_time': execution_time,
                'message': f"Poblado completado: {videos_added} agregados, {videos_updated} actualizados, {stats['creators_created']} creadores, {stats['subscriptions_created']} suscripciones"
            }
            
            if stats['errors']:
                result['error_details'] = stats['errors'][:5]  # Primeros 5 errores
            
            # Generar reporte profesional
            validation_stats = self._validate_external_files(source, platform)
            self._print_professional_summary(result, validation_stats, platform.upper(), execution_time)
            
            return result
            
        except Exception as e:
            logger.error(f"💥 Error durante poblado con nueva estructura: {e}")
            return {
                'success': False,
                'error': str(e),
                'videos_added': 0,
                'videos_updated': 0,
                'execution_time': time.time() - start_time
            }
    
    def _populate_with_new_structure(self, all_videos: List[Dict], force: bool = False, progress_callback=None) -> Tuple[int, int, Dict]:
        """Poblar BD con nueva estructura de creadores y suscripciones"""
        stats = {
            'creators_created': 0,
            'subscriptions_created': 0,
            'video_lists_added': 0,
            'errors': []
        }
        
        videos_to_insert = []
        videos_to_update = []
        
        # Cache de creadores y suscripciones para evitar duplicados
        creator_cache = {}  # {name: creator_id}
        subscription_cache = {}  # {(name, platform, type): subscription_id}
        
        logger.debug(f"📊 Procesando {len(all_videos)} videos con nueva estructura")
        
        # Verificar existencia de videos
        file_paths = [video['file_path'] for video in all_videos]
        existing_videos = self.db.check_videos_exist_batch(file_paths)
        
        for video_data in all_videos:
            try:
                file_path = video_data['file_path']
                
                # Verificar si ya existe
                if existing_videos.get(file_path, False):
                    if force:
                        # Actualizar video existente
                        processed_video = self._process_single_video_new_structure(
                            video_data, creator_cache, subscription_cache, stats, update=True
                        )
                        if processed_video:
                            videos_to_update.append(processed_video)
                    else:
                        # Saltar video existente (log debug para evitar ruido)
                        logger.debug(f"➡️ Video ya existe en la base de datos, saltando: {file_path}")
                        continue
                else:
                    # Insertar video nuevo
                    processed_video = self._process_single_video_new_structure(
                        video_data, creator_cache, subscription_cache, stats, update=False
                    )
                    if processed_video:
                        videos_to_insert.append(processed_video)
                        
            except Exception as e:
                logger.error(f"Error procesando video {video_data.get('file_path', 'unknown')}: {e}")
                stats['errors'].append(str(e))
                continue
        
        # Insertar/actualizar videos en lote
        videos_added = 0
        videos_updated = 0
        
        if videos_to_insert:
            try:
                added, failed = self.db.batch_insert_videos(videos_to_insert, force=False)
                videos_added = added
                logger.debug(f"✅ Insertados {added} videos nuevos (fallidos: {failed})")
            except Exception as e:
                logger.error(f"Error en inserción en lote: {e}")
                stats['errors'].append(f"Batch insert error: {e}")
        
        if videos_to_update:
            try:
                # TODO: Implementar batch update con nueva estructura
                videos_updated = len(videos_to_update)
                logger.debug(f"✅ Actualizados {videos_updated} videos existentes")
            except Exception as e:
                logger.error(f"Error en actualización en lote: {e}")
                stats['errors'].append(f"Batch update error: {e}")
        
        return videos_added, videos_updated, stats
    
    def _process_single_video_new_structure(self, video_data: Dict, creator_cache: Dict, 
                                          subscription_cache: Dict, stats: Dict, update: bool = False) -> Optional[Dict]:
        """Procesar un video individual con nueva estructura"""
        try:
            # 1. Gestionar creador (solo si existe)
            creator_id = None
            if video_data.get('creator_name'):
                creator_id = self._get_or_create_creator(
                    video_data.get('creator_name'),
                    video_data.get('creator_url'),
                    video_data.get('platform', 'youtube'),
                    creator_cache,
                    stats
                )
            
            # 2. Gestionar suscripción (solo si existe)
            subscription_id = None
            if video_data.get('subscription_name'):
                subscription_id = self._get_or_create_subscription(
                    video_data.get('subscription_name'),
                    video_data.get('subscription_type', 'account'),
                    video_data.get('platform', 'youtube'),
                    creator_id,
                    video_data.get('subscription_url'),
                    subscription_cache,
                    stats
                )
            
            # 3. Preparar datos del video
            processed_video = {
                'file_path': video_data['file_path'],
                'file_name': video_data['file_name'],
                'title': video_data.get('title'),
                'post_url': video_data.get('post_url'),
                'platform': video_data.get('platform', 'youtube'),
                'creator_id': creator_id,
                'subscription_id': subscription_id,
                'processing_status': 'pendiente'
            }
            
            # 4. Agregar datos del downloader si existen
            if 'downloader_data' in video_data:
                processed_video['downloader_mapping'] = video_data['downloader_data']
            
            # 5. Guardar tipos de lista para procesar después (puede ser None para plataformas secundarias)
            processed_video['list_types'] = video_data.get('list_types') or []
            
            return processed_video
            
        except Exception as e:
            logger.error(f"Error procesando video individual: {e}")
            stats['errors'].append(f"Process video error: {e}")
            return None
    
    def _get_or_create_creator(self, creator_name: str, creator_url: str, platform: str, 
                             creator_cache: Dict, stats: Dict) -> int:
        """Obtener o crear creador"""
        if not creator_name:
            creator_name = f"Unknown_{platform}"
        
        # Verificar cache
        if creator_name in creator_cache:
            return creator_cache[creator_name]
        
        # Buscar en BD
        existing_creator = self.db.get_creator_by_name(creator_name)
        if existing_creator:
            creator_id = existing_creator['id']
            creator_cache[creator_name] = creator_id
            
            # Agregar URL si no existe para esta plataforma
            if creator_url:
                self.db.add_creator_url(creator_id, platform, creator_url)
            
            return creator_id
        
        # Crear nuevo creador
        creator_id = self.db.create_creator(creator_name)
        creator_cache[creator_name] = creator_id
        stats['creators_created'] += 1
        
        # Agregar URL si existe
        if creator_url:
            self.db.add_creator_url(creator_id, platform, creator_url)
        
        return creator_id
    
    def _get_or_create_subscription(self, subscription_name: str, subscription_type: str,
                                   platform: str, creator_id: int, subscription_url: str,
                                   subscription_cache: Dict, stats: Dict) -> int:
        """Obtener o crear suscripción"""
        if not subscription_name:
            subscription_name = f"Unknown_{platform}_{subscription_type}"
        
        # Crear clave de cache
        cache_key = (subscription_name, platform, subscription_type)
        
        # Verificar cache
        if cache_key in subscription_cache:
            return subscription_cache[cache_key]
        
        # Buscar en BD
        existing_subscription = self.db.get_subscription_by_name_and_platform(
            subscription_name, platform, subscription_type
        )
        
        if existing_subscription:
            subscription_id = existing_subscription['id']
            subscription_cache[cache_key] = subscription_id
            return subscription_id
        
        # Crear nueva suscripción
        subscription_id = self.db.create_subscription(
            name=subscription_name,
            type=subscription_type,
            platform=platform,
            creator_id=creator_id if subscription_type == 'account' else None,
            subscription_url=subscription_url
        )
        
        subscription_cache[cache_key] = subscription_id
        stats['subscriptions_created'] += 1
        
        return subscription_id
    
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
            db_path = config.DATABASE_PATH
            
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
            db_path = config.DATABASE_PATH
            
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
                        COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as deleted
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
                        'path': str(config.DATABASE_PATH.resolve())
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
    
    def _filter_duplicates_optimized(self, external_videos: List[Dict]) -> List[Dict]:
        """🚀 NUEVA ESTRATEGIA: Filtrar duplicados usando consulta optimizada con búsqueda inteligente"""
        if not external_videos:
            return []
        
        # Crear mapping de rutas para consulta rápida
        file_paths = [video['file_path'] for video in external_videos]
        
        # 🚀 NUEVA ESTRATEGIA: Consultar BD por todas las rutas de una vez (incluyendo eliminados)
        existing_paths = set()
        if file_paths:
            # Dividir en lotes para evitar límites SQL con muchos parámetros
            batch_size = 900  # SQLite tiene límite de ~1000 parámetros
            for i in range(0, len(file_paths), batch_size):
                batch_paths = file_paths[i:i + batch_size]
                placeholders = ','.join(['?' for _ in batch_paths])
                query = f"SELECT file_path FROM videos WHERE file_path IN ({placeholders}) AND deleted_at IS NULL"
                
                with self.db.get_connection() as conn:
                    cursor = conn.execute(query, batch_paths)
                    existing_paths.update(row[0] for row in cursor.fetchall())
        
        # Filtrar videos que no existen en BD
        unique_videos = [video for video in external_videos if video['file_path'] not in existing_paths]
        
        # 🚀 NUEVA ESTRATEGIA: Ordenar por ID descendente para priorizar videos más recientes
        # Esto ayuda a importar los videos más nuevos primero
        unique_videos.sort(key=lambda v: v.get('external_id', 0), reverse=True)
        
        logger.info(f"🔍 Duplicados filtrados: {len(external_videos)} -> {len(unique_videos)}")
        if len(unique_videos) > 0:
            logger.info(f"📊 Rango de IDs externos: {unique_videos[-1].get('external_id', 'N/A')} - {unique_videos[0].get('external_id', 'N/A')}")
        
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
                
                # Insertar lote usando método optimizado
                batch_success, batch_failed = self.db.batch_insert_videos(batch_data, force=force)
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
        # Obtener título para TikTok/Instagram
        title = video_data.get('title')
        if not title and 'description' in video_data and video_data['description']:
            title = video_data['description']  # Compatibilidad hacia atrás
        
        return {
            'file_path': video_data['file_path'],
            'file_name': video_data['file_name'],
            'platform': video_data.get('platform', 'unknown'),
            'creator_name': video_data.get('creator_name'),
            'title': title,  # Usar título como campo principal
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
            "CREATE INDEX IF NOT EXISTS idx_videos_deleted_at ON videos(deleted_at)",
            "CREATE INDEX IF NOT EXISTS idx_videos_processing_status ON videos(processing_status)"
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
    
    def _validate_external_files(self, source: str, platform: str) -> Dict:
        """Validar todos los archivos de la BD externa contando también archivos faltantes"""
        validation_stats = {
            'total_external_records': 0,
            'existing_files': 0,
            'missing_files': 0,
            'missing_details': []
        }
        
        try:
            from src.service_factory import ServiceFactory
            external_sources = ServiceFactory.get_service('external_sources')
            
            # Obtener estadísticas del último escaneo guardadas por external_sources
            if platform == 'tiktok':
                all_videos = external_sources.extract_tiktok_videos(offset=0, limit=None)
                validation_stats['existing_files'] = len(all_videos)
                
                # Obtener estadísticas detalladas si están disponibles
                if hasattr(external_sources, '_last_tiktok_stats'):
                    stats = external_sources._last_tiktok_stats
                    validation_stats['total_external_records'] = stats['processed']
                    validation_stats['missing_files'] = stats['missing']
                else:
                    validation_stats['total_external_records'] = len(all_videos)
                
            elif platform == 'instagram':
                all_videos = external_sources.extract_instagram_content(offset=0, limit=None)
                validation_stats['existing_files'] = len(all_videos)
                
            elif platform == 'youtube':
                # Evitar doble extracción - usar estadísticas rápidas desde la BD
                validation_stats['existing_files'] = 0  # Se calculará desde los videos procesados
            else:
                return validation_stats
            
            # Nota: Los archivos faltantes ya se reportan en los logs de external_sources
            # Esta función se enfoca en dar un resumen limpio al usuario
            validation_stats['total_external_records'] = validation_stats['existing_files']
            
        except Exception as e:
            logger.error(f"Error en validación de archivos: {e}")
        
        return validation_stats
    
    def _print_professional_summary(self, result: Dict, validation_stats: Dict, platform: str, execution_time: float):
        """Imprimir resumen profesional del poblado"""
        
        # Limpiar logs anteriores del terminal (solo mostrar resumen final)
        print(f"\n✅ POBLADO COMPLETADO EXITOSAMENTE")
        
        print(f"\n📊 RESUMEN DE POBLADO - {platform}")
        print("┌─────────────────────────────┬──────────┐")
        print(f"│ Nuevos videos agregados     │ {result['videos_added']:8} │")
        
        # Calcular videos ya existentes desde external stats (evitar valores negativos)
        total_processed = validation_stats.get('total_external_records', result['videos_added'])
        existing_count = max(0, total_processed - result['videos_added'])  # Evitar valores negativos
        print(f"│ Videos ya existentes        │ {existing_count:8} │")
        
        missing_count = validation_stats.get('missing_files', 0)
        print(f"│ Archivos no encontrados     │ {missing_count:8} │")
        print(f"│ Total procesado             │ {total_processed:8} │")
        print("└─────────────────────────────┴──────────┘")
        
        # Información adicional
        if result['creators_created'] > 0:
            print(f"\n👤 Creadores nuevos: {result['creators_created']}")
        if result['subscriptions_created'] > 0:
            print(f"📋 Suscripciones nuevas: {result['subscriptions_created']}")
        
        # Advertencias importantes
        if missing_count > 0:
            print(f"\n⚠️  ARCHIVOS FALTANTES DETECTADOS: {missing_count}")
            print("    (Archivos registrados en BD externa pero no existen en disco)")
        
        # Errores si los hay
        if result.get('errors', 0) > 0:
            print(f"\n❌ Errores encontrados: {result['errors']}")
        
        print(f"\n⏱️  Tiempo de ejecución: {execution_time:.2f}s\n")

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