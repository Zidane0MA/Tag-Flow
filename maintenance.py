"""
Tag-Flow V2 - Utilidades de Mantenimiento
Scripts para backup, limpieza y mantenimiento del sistema
"""

import sys
import argparse
import shutil
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple  # 🚀 Añadido Tuple para optimizaciones
import sqlite3
import logging

# Agregar src al path
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config
from src.database import db
from src.external_sources import external_sources
from src.thumbnail_generator import thumbnail_generator
from src.character_intelligence import character_intelligence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaintenanceUtils:
    """Utilidades de mantenimiento para Tag-Flow V2"""
    
    def __init__(self):
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self):
        """Crear backup completo del sistema"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"tag_flow_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"Creando backup: {backup_path}")
        
        try:
            # Backup de la base de datos
            if config.DATABASE_PATH.exists():
                shutil.copy2(config.DATABASE_PATH, backup_path / 'videos.db')
                logger.info("✓ Base de datos respaldada")
            
            # Backup de thumbnails (solo los primeros 100 para no ocupar mucho espacio)
            thumbnails_backup = backup_path / 'thumbnails'
            thumbnails_backup.mkdir(exist_ok=True)
            
            thumbnail_count = 0
            for thumb in config.THUMBNAILS_PATH.glob('*.jpg'):
                if thumbnail_count < 100:  # Límite para ahorrar espacio
                    shutil.copy2(thumb, thumbnails_backup)
                    thumbnail_count += 1
            
            logger.info(f"✓ {thumbnail_count} thumbnails respaldados")
            
            # Backup de configuración
            if Path('.env').exists():
                shutil.copy2('.env', backup_path / '.env')
                logger.info("✓ Configuración respaldada")
            
            # Backup de caras conocidas
            if config.KNOWN_FACES_PATH.exists():
                shutil.copytree(config.KNOWN_FACES_PATH, backup_path / 'caras_conocidas')
                logger.info("✓ Caras conocidas respaldadas")
            
            # Crear manifiesto del backup
            manifest = {
                'created': timestamp,
                'version': '2.0.0',
                'database_size': config.DATABASE_PATH.stat().st_size if config.DATABASE_PATH.exists() else 0,
                'thumbnails_count': thumbnail_count,
                'has_config': Path('.env').exists(),
                'has_faces': config.KNOWN_FACES_PATH.exists()
            }
            
            with open(backup_path / 'manifest.json', 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Comprimir backup
            shutil.make_archive(str(backup_path), 'zip', str(backup_path))
            shutil.rmtree(backup_path)  # Eliminar carpeta temporal
            
            backup_zip = f"{backup_path}.zip"
            logger.info(f"✅ Backup creado: {backup_zip}")
            
            return backup_zip
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return None
    
    def clean_thumbnails(self, force=False):
        """Limpiar thumbnails huérfanos (sin video asociado)"""
        logger.info("Limpiando thumbnails huérfanos...")
        
        # Obtener videos en BD
        videos = db.get_videos()
        valid_thumbnails = set()
        
        for video in videos:
            if video.get('thumbnail_path'):
                thumb_name = Path(video['thumbnail_path']).name
                valid_thumbnails.add(thumb_name)
        
        # Encontrar thumbnails huérfanos
        orphaned = []
        total_size = 0
        
        for thumb_path in config.THUMBNAILS_PATH.glob('*.jpg'):
            if thumb_path.name not in valid_thumbnails:
                orphaned.append(thumb_path)
                total_size += thumb_path.stat().st_size
        
        if not orphaned:
            logger.info("✅ No se encontraron thumbnails huérfanos")
            return
        
        logger.info(f"Encontrados {len(orphaned)} thumbnails huérfanos ({total_size / 1024 / 1024:.1f} MB)")
        
        if not force:
            response = input("¿Eliminar thumbnails huérfanos? [y/N]: ")
            if response.lower() != 'y':
                logger.info("Operación cancelada")
                return
        
        # Eliminar thumbnails
        deleted = 0
        for thumb_path in orphaned:
            try:
                thumb_path.unlink()
                deleted += 1
            except Exception as e:
                logger.error(f"Error eliminando {thumb_path}: {e}")
        
        logger.info(f"✅ Eliminados {deleted} thumbnails huérfanos")
    
    def verify_integrity(self):
        """Verificar integridad de la base de datos y archivos"""
        logger.info("Verificando integridad del sistema...")
        
        issues = []
        
        # Verificar base de datos
        try:
            videos = db.get_videos()
            logger.info(f"✓ Base de datos accesible ({len(videos)} videos)")
        except Exception as e:
            issues.append(f"Error accediendo base de datos: {e}")
        
        # Verificar archivos de video
        missing_videos = []
        missing_thumbnails = []
        
        for video in videos:
            # Verificar archivo de video
            video_path = Path(video['file_path'])
            if not video_path.exists():
                missing_videos.append(video_path)
            
            # Verificar thumbnail
            if video.get('thumbnail_path'):
                thumb_path = Path(video['thumbnail_path'])
                if not thumb_path.exists():
                    missing_thumbnails.append(thumb_path)
        
        if missing_videos:
            issues.append(f"{len(missing_videos)} videos faltantes")
            for vid in missing_videos[:5]:  # Mostrar solo los primeros 5
                logger.warning(f"  Faltante: {vid}")
            if len(missing_videos) > 5:
                logger.warning(f"  ... y {len(missing_videos) - 5} más")
        
        if missing_thumbnails:
            issues.append(f"{len(missing_thumbnails)} thumbnails faltantes")
        
        # Verificar configuración
        config_issues = config.validate_config()
        if config_issues:
            issues.extend(config_issues)
        
        # Resumen
        if issues:
            logger.warning(f"❌ Encontrados {len(issues)} problemas:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("✅ Integridad verificada - Sin problemas")
        
        return issues
    
    def regenerate_thumbnails(self, force=False):
        """
        🚀 OPTIMIZADO: Regeneración selectiva de thumbnails con procesamiento paralelo
        
        Args:
            force: regenerar thumbnails existentes también
        """
        start_time = time.time()
        logger.info("🚀 Regenerando thumbnails OPTIMIZADO...")
        
        # 🔧 CORREGIDO: Usar configuración del .env en lugar de forzar ultra_fast
        logger.info(f"🎯 Configuración aplicada: Tamaño {thumbnail_generator.thumbnail_size}, Calidad {thumbnail_generator.quality}%, Validación: {thumbnail_generator.enable_validation}")
        
        # 🔍 PASO 1: Obtener videos que necesitan regeneración (consulta optimizada)
        logger.info("📊 Identificando videos que necesitan regeneración...")
        videos_to_regenerate = self._get_videos_for_regeneration_optimized(force)
        
        if not videos_to_regenerate:
            logger.info("✅ Todos los videos tienen thumbnails válidos")
            return
        
        logger.info(f"Videos para regenerar: {len(videos_to_regenerate)}")
        
        # 🎯 PASO 2: Priorizar videos con personajes detectados
        prioritized_videos = self._prioritize_videos_with_characters(videos_to_regenerate)
        logger.info(f"📈 Videos priorizados: {len(prioritized_videos['priority'])} con personajes, {len(prioritized_videos['normal'])} normales")
        
        # Combinar videos priorizados
        ordered_videos = prioritized_videos['priority'] + prioritized_videos['normal']
        
        # 🧹 PASO 3: Limpiar thumbnails corruptos/inválidos
        logger.info("🧹 Limpiando thumbnails corruptos...")
        cleaned_count = self._clean_corrupt_thumbnails(ordered_videos)
        if cleaned_count > 0:
            logger.info(f"✅ Thumbnails corruptos eliminados: {cleaned_count}")
        
        # ⚡ PASO 4: Regeneración en paralelo con ThreadPoolExecutor
        logger.info("⚡ Regenerando thumbnails en paralelo...")
        success, failed = self._regenerate_thumbnails_parallel(ordered_videos, force)
        
        # 📊 PASO 5: Métricas finales
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ Thumbnails regenerados OPTIMIZADO en {duration:.2f}s")
        logger.info(f"   📊 Resultados: {success} exitosos, {failed} fallidos")
        if cleaned_count > 0:
            logger.info(f"   🧹 Limpiezas: {cleaned_count} thumbnails corruptos eliminados")
        if success > 0:
            logger.info(f"   ⚡ Throughput: {success/duration:.1f} thumbnails/segundo")
        
        # 🔧 PASO 6: Optimización automática de BD si fue procesamiento masivo
        if success > 20:
            logger.info("🔧 Optimizando base de datos...")
            try:
                self.optimize_database()
                logger.info("✅ Base de datos optimizada")
            except Exception as e:
                logger.warning(f"Advertencia optimizando BD: {e}")
    
    def _get_videos_for_regeneration_optimized(self, force=False):
        """🚀 OPTIMIZADO: Obtener videos que necesitan regeneración con consulta SQL eficiente"""
        # Construir consulta SQL optimizada
        if force:
            # Si force=True, regenerar todos los videos
            query = """
            SELECT id, file_path, file_name, thumbnail_path, detected_characters, platform
            FROM videos 
            WHERE file_path IS NOT NULL
            ORDER BY 
                CASE 
                    WHEN detected_characters IS NOT NULL AND detected_characters != '[]' 
                    THEN 0 ELSE 1 
                END,
                id
            """
            params = []
        else:
            # Solo videos sin thumbnails o con thumbnails inválidos
            query = """
            SELECT id, file_path, file_name, thumbnail_path, detected_characters, platform
            FROM videos 
            WHERE file_path IS NOT NULL 
            AND (thumbnail_path IS NULL OR thumbnail_path = '')
            ORDER BY 
                CASE 
                    WHEN detected_characters IS NOT NULL AND detected_characters != '[]' 
                    THEN 0 ELSE 1 
                END,
                id
            """
            params = []
        
        # Ejecutar consulta
        with db.get_connection() as conn:
            cursor = conn.execute(query, params)
            videos = [dict(row) for row in cursor.fetchall()]
        
        # Filtrar videos por existencia de archivo y validez de thumbnail
        valid_videos = []
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        
        for video in videos:
            file_path = Path(video['file_path'])
            
            # Verificar que el archivo de video existe
            if not file_path.exists():
                logger.debug(f"Archivo de video no existe: {file_path}")
                continue
            
            # Verificar que es un video (no imagen)
            if file_path.suffix.lower() not in video_extensions:
                continue
            
            # Verificar si necesita regeneración de thumbnail
            needs_regeneration = force
            
            if not needs_regeneration:
                thumbnail_path = video.get('thumbnail_path')
                if not thumbnail_path:
                    needs_regeneration = True
                else:
                    thumb_path = Path(thumbnail_path)
                    if not thumb_path.exists():
                        needs_regeneration = True
                    elif self._is_thumbnail_corrupt(thumb_path):
                        needs_regeneration = True
            
            if needs_regeneration:
                valid_videos.append(video)
        
        return valid_videos
    
    def _is_thumbnail_corrupt(self, thumbnail_path):
        """Verificar si un thumbnail está corrupto"""
        try:
            thumb_path = Path(thumbnail_path)
            
            # Verificar que el archivo existe
            if not thumb_path.exists():
                return True
            
            # Verificar tamaño mínimo (thumbnails muy pequeños probablemente corruptos)
            if thumb_path.stat().st_size < 1024:  # Menos de 1KB
                return True
            
            # Intentar abrir la imagen para verificar validez
            from PIL import Image
            try:
                with Image.open(thumb_path) as img:
                    # Verificar que tiene dimensiones válidas
                    if img.width < 50 or img.height < 50:
                        return True
                    # Verificar que no está completamente negro
                    if hasattr(img, 'getextrema'):
                        extrema = img.getextrema()
                        if isinstance(extrema, tuple) and len(extrema) == 2 and extrema[0] == extrema[1] == 0:
                            return True
                return False
            except Exception:
                return True
                
        except Exception:
            return True
    
    def _clean_corrupt_thumbnails(self, videos):
        """🧹 Limpiar thumbnails corruptos identificados"""
        cleaned_count = 0
        
        for video in videos:
            thumbnail_path = video.get('thumbnail_path')
            if not thumbnail_path:
                continue
            
            thumb_path = Path(thumbnail_path)
            if thumb_path.exists() and self._is_thumbnail_corrupt(thumb_path):
                try:
                    thumb_path.unlink()
                    cleaned_count += 1
                    logger.debug(f"Thumbnail corrupto eliminado: {thumb_path}")
                except Exception as e:
                    logger.warning(f"Error eliminando thumbnail corrupto {thumb_path}: {e}")
        
        return cleaned_count
    
    def _regenerate_thumbnails_parallel(self, videos, force=False):
        """⚡ Regenerar thumbnails en paralelo con ThreadPoolExecutor"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        success = 0
        failed = 0
        # Optimizar workers para I/O bound (thumbnail generation)
        import os
        cpu_count = os.cpu_count() or 4
        # Para thumbnail generation, usar menos workers para evitar thrashing
        max_workers = min(4, len(videos))
        
        def regenerate_single_thumbnail(video_data):
            """Regenerar thumbnail para un video individual (sin actualizar BD)"""
            try:
                video_path = Path(video_data['file_path'])
                
                # Verificar que el archivo existe
                if not video_path.exists():
                    return {'success': False, 'error': f"Video no existe: {video_path}", 'video_id': video_data['id']}
                
                # Generar thumbnail (siempre con force=True para regeneración)
                thumbnail_path = thumbnail_generator.generate_thumbnail(video_path, force_regenerate=True)
                
                if thumbnail_path:
                    # NO actualizar BD aquí - acumular para batch update
                    return {
                        'success': True, 
                        'path': str(thumbnail_path), 
                        'video_name': video_path.name,
                        'video_id': video_data['id'],
                        'thumbnail_path': str(thumbnail_path)
                    }
                else:
                    return {'success': False, 'error': f"Falló regeneración para {video_path.name}", 'video_id': video_data['id']}
                    
            except Exception as e:
                return {'success': False, 'error': f"Error con {video_data.get('file_name', 'unknown')}: {e}", 'video_id': video_data['id']}
        
        # Procesamiento en paralelo con batch updates
        batch_updates = []  # Acumular updates para BD
        batch_size = 25  # Actualizar BD cada 25 thumbnails
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas
            future_to_video = {
                executor.submit(regenerate_single_thumbnail, video): video 
                for video in videos
            }
            
            # Recopilar resultados conforme se completan
            for i, future in enumerate(as_completed(future_to_video), 1):
                try:
                    result = future.result()
                    
                    if result['success']:
                        success += 1
                        logger.info(f"✓ {result['video_name']}")
                        
                        # Acumular update para batch
                        batch_updates.append({
                            'video_id': result['video_id'],
                            'updates': {'thumbnail_path': result['thumbnail_path']}
                        })
                        
                    else:
                        failed += 1
                        logger.warning(f"✗ {result['error']}")
                    
                    # Batch update cada 25 thumbnails o al final
                    if len(batch_updates) >= batch_size or i == len(videos):
                        if batch_updates:
                            try:
                                batch_success, batch_failed = db.batch_update_videos(batch_updates)
                                logger.debug(f"🔄 Batch update: {batch_success} exitosos, {batch_failed} fallidos")
                                batch_updates = []  # Limpiar batch
                            except Exception as e:
                                logger.warning(f"Error en batch update: {e}")
                    
                    # Mostrar progreso cada 10 thumbnails
                    if i % 10 == 0 or i == len(videos):
                        logger.info(f"⚡ Progreso: {i}/{len(videos)} ({i/len(videos)*100:.1f}%) - {success} exitosos, {failed} fallidos")
                        
                except Exception as e:
                    failed += 1
                    video = future_to_video[future]
                    logger.error(f"Error procesando {video.get('file_name', 'unknown')}: {e}")
        
        # Procesar cualquier update restante
        if batch_updates:
            try:
                batch_success, batch_failed = db.batch_update_videos(batch_updates)
                logger.info(f"🔄 Batch update final: {batch_success} exitosos, {batch_failed} fallidos")
            except Exception as e:
                logger.warning(f"Error en batch update final: {e}")
        
        return success, failed
    
    def optimize_database(self):
        """Optimizar base de datos SQLite"""
        logger.info("Optimizando base de datos...")
        
        try:
            with db.get_connection() as conn:
                # VACUUM para compactar BD
                conn.execute('VACUUM')
                
                # ANALYZE para optimizar consultas
                conn.execute('ANALYZE')
                
                # Obtener estadísticas
                cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM videos")
                video_count = cursor.fetchone()[0]
            
            logger.info(f"✅ Base de datos optimizada")
            logger.info(f"   Tamaño: {db_size / 1024 / 1024:.1f} MB")
            logger.info(f"   Videos: {video_count}")
            
        except Exception as e:
            logger.error(f"Error optimizando base de datos: {e}")
    
    def populate_database(self, source='all', platform=None, limit=None, force=False, file_path=None):
        """
        🚀 OPTIMIZADO: Poblar la base de datos desde fuentes externas o un archivo específico
        
        Args:
            source: 'db', 'organized', 'all' - fuente de datos
            platform: 'youtube', 'tiktok', 'instagram' o None para todas
            limit: número máximo de videos a importar
            force: forzar reimportación de videos existentes
            file_path: 🆕 ruta específica de un video para importar
        """
        start_time = time.time()
        
        # 🆕 NUEVA FUNCIONALIDAD: Importar archivo específico
        if file_path:
            return self._populate_single_file(file_path, force)
        
        # 🚀 FUNCIONALIDAD OPTIMIZADA: Importar desde fuentes múltiples
        logger.info(f"🚀 Poblando base de datos OPTIMIZADO desde {source} (plataforma: {platform or 'todas'})")
        
        if limit:
            logger.info(f"Límite establecido: {limit} videos")
        
        # 🚀 PASO 1: Obtener videos de fuentes externas (sin cambios)
        logger.info("📥 Obteniendo videos de fuentes externas...")
        external_videos = external_sources.get_all_videos_from_source(source, platform, limit)
        
        if not external_videos:
            logger.info("No se encontraron videos para importar")
            return
        
        logger.info(f"Videos encontrados para procesar: {len(external_videos)}")
        
        # 🚀 PASO 2: Verificación optimizada de duplicados
        if not force:
            logger.info("🔍 Verificando duplicados (optimizado)...")
            external_videos = self._filter_duplicates_optimized(external_videos)
        
        if not external_videos:
            logger.info("✅ Todos los videos ya están en la base de datos")
            return
        
        logger.info(f"Videos únicos para importar: {len(external_videos)}")
        
        # 🚀 PASO 3: Extracción de metadatos en paralelo
        logger.info("⚡ Extrayendo metadatos en paralelo...")
        processed_videos = self._extract_metadata_parallel(external_videos, force)
        
        # 🚀 PASO 4: Inserción por lotes optimizada
        logger.info("💾 Insertando videos por lotes...")
        imported, errors = self._insert_videos_batch(processed_videos, force)
        
        # 📊 Métricas finales
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ Importación OPTIMIZADA completada en {duration:.2f}s")
        logger.info(f"   📊 Resultados: {imported} exitosos, {errors} errores")
        logger.info(f"   ⚡ Throughput: {imported/duration:.1f} videos/segundo")
        
        # 🚀 PASO 5: Optimizar BD después de inserción masiva
        if imported > 50:  # Solo optimizar si se insertaron muchos videos
            logger.info("🔧 Optimizando base de datos...")
            try:
                self.optimize_database()
                logger.info("✅ Base de datos optimizada")
            except Exception as e:
                logger.warning(f"Advertencia optimizando BD: {e}")
    
    def _populate_single_file(self, file_path: str, force: bool = False) -> None:
        """🆕 Importar un archivo específico (funcionalidad existente mantenida)"""
        logger.info(f"Importando archivo específico: {file_path}")
        
        # Extraer información del video específico
        video_data = external_sources.extract_single_video_info(file_path)
        
        if not video_data:
            logger.error("No se pudo extraer información del archivo")
            return
        
        # Verificar si ya existe en la BD
        existing = db.get_video_by_path(video_data['file_path'])
        if existing and not force:
            logger.info(f"El video ya existe en la BD (ID: {existing['id']})")
            logger.info(f"Usa --force para forzar actualización")
            return
        
        # Preparar datos para la BD
        db_data = self._prepare_db_data(video_data)
        
        # Obtener metadatos del archivo
        db_data.update(self._extract_file_metadata(video_data))
        
        # Agregar o actualizar en la BD
        try:
            if existing and force:
                # Actualizar registro existente
                db.update_video(existing['id'], db_data)
                logger.info(f"✅ Video actualizado: {video_data['file_name']}")
            else:
                # Agregar nuevo registro
                db.add_video(db_data)
                logger.info(f"✅ Video importado: {video_data['file_name']}")
            
            logger.info(f"   Plataforma: {video_data['platform']}")
            logger.info(f"   Creador: {video_data['creator_name']}")
            logger.info(f"   Fuente: {video_data['source']}")
            
        except Exception as e:
            logger.error(f"Error importando archivo específico: {e}")
    
    def _filter_duplicates_optimized(self, external_videos: List[Dict]) -> List[Dict]:
        """🚀 OPTIMIZADO: Filtrar duplicados usando consulta SQL directa"""
        if not external_videos:
            return []
        
        # Extraer rutas de archivos para verificar
        file_paths = [video['file_path'] for video in external_videos]
        
        # 🚀 Consulta SQL optimizada con WHERE IN
        placeholders = ','.join(['?' for _ in file_paths])
        query = f"SELECT file_path FROM videos WHERE file_path IN ({placeholders})"
        
        with db.get_connection() as conn:
            cursor = conn.execute(query, file_paths)
            existing_paths = {row[0] for row in cursor.fetchall()}
        
        # Filtrar videos nuevos usando set lookup O(1)
        new_videos = [v for v in external_videos if v['file_path'] not in existing_paths]
        skipped = len(external_videos) - len(new_videos)
        
        if skipped > 0:
            logger.info(f"⏭️  Videos ya existentes omitidos: {skipped}")
        
        return new_videos
    
    def _extract_metadata_parallel(self, external_videos: List[Dict], force: bool = False) -> List[Dict]:
        """🚀 OPTIMIZADO: Extraer metadatos en paralelo con cache"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Cache temporal para evitar recálculos
        metadata_cache = {}
        
        def extract_single_metadata(video_data: Dict) -> Dict:
            """Extraer metadatos de un video individual"""
            try:
                file_path = video_data['file_path']
                
                # Verificar cache primero
                if file_path in metadata_cache:
                    cached_metadata = metadata_cache[file_path]
                    video_data.update(cached_metadata)
                    return video_data
                
                # Preparar datos base
                processed_data = self._prepare_db_data(video_data)
                
                # Extraer metadatos del archivo
                file_metadata = self._extract_file_metadata(video_data)
                processed_data.update(file_metadata)
                
                # Guardar en cache
                metadata_cache[file_path] = file_metadata
                
                return processed_data
                
            except Exception as e:
                logger.error(f"Error extrayendo metadatos de {video_data.get('file_name', 'unknown')}: {e}")
                # Retornar datos básicos si falla la extracción de metadatos
                return self._prepare_db_data(video_data)
        
        # 🚀 Procesamiento en paralelo
        processed_videos = []
        max_workers = min(4, len(external_videos))  # Máximo 4 threads para evitar sobrecarga
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas
            future_to_video = {
                executor.submit(extract_single_metadata, video): video 
                for video in external_videos
            }
            
            # Recopilar resultados conforme se completan
            for i, future in enumerate(as_completed(future_to_video), 1):
                try:
                    processed_video = future.result()
                    processed_videos.append(processed_video)
                    
                    # Mostrar progreso cada 10 videos
                    if i % 10 == 0 or i == len(external_videos):
                        logger.info(f"⚡ Metadatos extraídos: {i}/{len(external_videos)} ({i/len(external_videos)*100:.1f}%)")
                        
                except Exception as e:
                    video = future_to_video[future]
                    logger.error(f"Error procesando {video.get('file_name', 'unknown')}: {e}")
        
        logger.info(f"✅ Metadatos extraídos para {len(processed_videos)} videos")
        return processed_videos
    
    def _insert_videos_batch(self, processed_videos: List[Dict], force: bool = False) -> Tuple[int, int]:
        """🚀 OPTIMIZADO: Inserción por lotes con transacciones"""
        if not processed_videos:
            return 0, 0
        
        batch_size = 50  # Insertar en lotes de 50
        imported = 0
        errors = 0
        
        # Separar videos para insertar vs actualizar si force=True
        videos_to_insert = []
        videos_to_update = []
        
        if force:
            # Si force=True, necesitamos verificar cuáles existen para actualizar
            file_paths = [v['file_path'] for v in processed_videos]
            placeholders = ','.join(['?' for _ in file_paths])
            query = f"SELECT id, file_path FROM videos WHERE file_path IN ({placeholders})"
            
            with db.get_connection() as conn:
                cursor = conn.execute(query, file_paths)
                existing_videos = {row[1]: row[0] for row in cursor.fetchall()}  # path -> id
            
            for video in processed_videos:
                if video['file_path'] in existing_videos:
                    video['existing_id'] = existing_videos[video['file_path']]
                    videos_to_update.append(video)
                else:
                    videos_to_insert.append(video)
        else:
            videos_to_insert = processed_videos
        
        # 🚀 Inserción por lotes para videos nuevos
        if videos_to_insert:
            logger.info(f"💾 Insertando {len(videos_to_insert)} videos nuevos en lotes...")
            
            for i in range(0, len(videos_to_insert), batch_size):
                batch = videos_to_insert[i:i + batch_size]
                
                try:
                    with db.get_connection() as conn:
                        # Preparar datos para executemany
                        insert_data = []
                        for video in batch:
                            insert_row = (
                                video['file_path'],
                                video['file_name'], 
                                video['creator_name'],
                                video.get('platform', 'tiktok'),
                                video.get('file_size'),
                                video.get('duration_seconds'),
                                video.get('detected_music'),
                                video.get('detected_music_artist'),
                                video.get('detected_music_confidence'),
                                json.dumps(video.get('detected_characters', [])),
                                video.get('music_source'),
                                video.get('processing_status', 'pendiente'),
                                video.get('description')
                            )
                            insert_data.append(insert_row)
                        
                        # 🚀 Inserción por lotes usando executemany
                        conn.executemany('''
                            INSERT INTO videos (
                                file_path, file_name, creator_name, platform, file_size, duration_seconds,
                                detected_music, detected_music_artist, detected_music_confidence,
                                detected_characters, music_source, processing_status, description
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', insert_data)
                        
                        imported += len(batch)
                        logger.info(f"✅ Lote insertado: {len(batch)} videos (total: {imported})")
                        
                except Exception as e:
                    logger.error(f"Error insertando lote {i//batch_size + 1}: {e}")
                    errors += len(batch)
        
        # 🚀 Actualización por lotes para videos existentes (si force=True)
        if videos_to_update:
            logger.info(f"🔄 Actualizando {len(videos_to_update)} videos existentes...")
            
            for video in videos_to_update:
                try:
                    # Remover 'existing_id' antes de actualizar
                    existing_id = video.pop('existing_id')
                    db.update_video(existing_id, video)
                    imported += 1
                    
                    if imported % 20 == 0:  # Progreso cada 20 actualizaciones
                        logger.info(f"🔄 Actualizados: {imported - len(videos_to_insert)}")
                        
                except Exception as e:
                    logger.error(f"Error actualizando video {video.get('file_name', 'unknown')}: {e}")
                    errors += 1
        
        return imported, errors
    
    def _prepare_db_data(self, video_data: Dict) -> Dict:
        """🔧 Preparar datos básicos para la BD"""
        db_data = {
            'file_path': video_data['file_path'],
            'file_name': video_data['file_name'],
            'creator_name': video_data['creator_name'],
            'platform': video_data['platform'],
            'processing_status': 'pendiente'
        }
        
        # Agregar información adicional si está disponible
        if 'title' in video_data:
            db_data['description'] = video_data['title']
        
        return db_data
    
    def _extract_file_metadata(self, video_data: Dict) -> Dict:
        """🔧 Extraer metadatos del archivo (tamaño, duración)"""
        metadata = {}
        
        file_path = Path(video_data['file_path'])
        if not file_path.exists():
            return metadata
        
        try:
            # Tamaño del archivo
            metadata['file_size'] = file_path.stat().st_size
            
            # Duración si es video
            if video_data.get('content_type', 'video') == 'video':
                try:
                    from src.video_processor import video_processor
                    file_metadata = video_processor.extract_metadata(file_path)
                    if 'duration_seconds' in file_metadata:
                        metadata['duration_seconds'] = file_metadata['duration_seconds']
                except Exception as e:
                    logger.debug(f"No se pudo obtener duración de {file_path.name}: {e}")
            
        except Exception as e:
            logger.warning(f"Error extrayendo metadatos de {file_path.name}: {e}")
        
        return metadata
        
    def clear_database(self, platform=None, force=False):
        """
        Limpiar la base de datos (eliminar todos los videos o de una plataforma específica)
        
        Args:
            platform: plataforma específica a limpiar o None para todas
            force: forzar eliminación sin confirmación
        """
        if platform:
            logger.info(f"Limpiando videos de la plataforma: {platform}")
        else:
            logger.info("Limpiando TODA la base de datos")
        
        # Contar videos a eliminar
        filters = {'platform': platform} if platform else {}
        videos_to_delete = db.get_videos(filters)
        
        if not videos_to_delete:
            logger.info("No hay videos para eliminar")
            return
        
        logger.info(f"Videos a eliminar: {len(videos_to_delete)}")
        
        if not force:
            response = input(f"¿Confirmar eliminación de {len(videos_to_delete)} videos? [y/N]: ")
            if response.lower() != 'y':
                logger.info("Operación cancelada")
                return
        
        # Eliminar videos
        deleted = 0
        for video in videos_to_delete:
            try:
                if db.delete_video(video['id']):
                    deleted += 1
            except Exception as e:
                logger.error(f"Error eliminando video {video['id']}: {e}")
        
        # Resetear secuencia AUTOINCREMENT si se eliminaron todos los videos
        if not platform:  # Solo si se limpió toda la BD
            try:
                with db.get_connection() as conn:
                    # Verificar si quedan videos
                    cursor = conn.execute("SELECT COUNT(*) FROM videos")
                    remaining_videos = cursor.fetchone()[0]
                    
                    # Si no quedan videos, resetear la secuencia
                    if remaining_videos == 0:
                        conn.execute("DELETE FROM sqlite_sequence WHERE name='videos'")
                        logger.info("✓ Secuencia AUTOINCREMENT reseteada")
            except Exception as e:
                logger.error(f"Error reseteando secuencia: {e}")
        
        logger.info(f"✅ Eliminados {deleted} videos de la base de datos")
    
    def populate_thumbnails(self, platform=None, limit=None, force=False):
        """
        🚀 OPTIMIZADO: Generación ultra-rápida de thumbnails con procesamiento paralelo
        
        Args:
            platform: plataforma específica o None para todas
            limit: número máximo de thumbnails a generar
            force: regenerar thumbnails existentes
        """
        start_time = time.time()
        logger.info("🚀 Generando thumbnails OPTIMIZADO...")
        
        # 🔧 CORREGIDO: Usar configuración del .env en lugar de forzar ultra_fast
        logger.info(f"🎯 Configuración aplicada: Tamaño {thumbnail_generator.thumbnail_size}, Calidad {thumbnail_generator.quality}%, Validación: {thumbnail_generator.enable_validation}")
        logger.info(f"🧠 Optimización RAM: Cache {thumbnail_generator.max_cache_size} frames, Pre-carga habilitada: {thumbnail_generator.use_ram_optimization}")
        
        # 🔍 PASO 1: Obtener videos que necesitan thumbnails (consulta optimizada)
        logger.info("📊 Obteniendo videos que necesitan thumbnails...")
        videos_needing_thumbs = self._get_videos_needing_thumbnails_optimized(platform, limit, force)
        
        if not videos_needing_thumbs:
            logger.info("✅ Todos los videos ya tienen thumbnails")
            return
        
        logger.info(f"Videos que necesitan thumbnails: {len(videos_needing_thumbs)}")
        
        # 🎯 PASO 2: Priorizar videos con personajes detectados
        prioritized_videos = self._prioritize_videos_with_characters(videos_needing_thumbs)
        logger.info(f"📈 Videos priorizados: {len(prioritized_videos['priority'])} con personajes, {len(prioritized_videos['normal'])} normales")
        
        # Combinar videos priorizados
        ordered_videos = prioritized_videos['priority'] + prioritized_videos['normal']
        
        # ⚡ PASO 3: Generación en paralelo con ThreadPoolExecutor
        logger.info("⚡ Generando thumbnails en paralelo...")
        success, failed = self._generate_thumbnails_parallel(ordered_videos, force)
        
        # 📊 PASO 4: Métricas finales
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ Thumbnails generados OPTIMIZADO en {duration:.2f}s")
        logger.info(f"   📊 Resultados: {success} exitosos, {failed} fallidos")
        if success > 0:
            logger.info(f"   ⚡ Throughput: {success/duration:.1f} thumbnails/segundo")
        
        # 🔧 PASO 5: Optimización automática de BD si fue procesamiento masivo
        if success > 20:
            logger.info("🔧 Optimizando base de datos...")
            try:
                self.optimize_database()
                logger.info("✅ Base de datos optimizada")
            except Exception as e:
                logger.warning(f"Advertencia optimizando BD: {e}")
    
    def _get_videos_needing_thumbnails_optimized(self, platform=None, limit=None, force=False):
        """🚀 OPTIMIZADO: Obtener videos que necesitan thumbnails con consulta SQL eficiente"""
        # Construir consulta SQL optimizada
        query = """
        SELECT id, file_path, file_name, thumbnail_path, detected_characters, platform
        FROM videos 
        WHERE 1=1
        """
        params = []
        
        # Filtrar por plataforma si se especifica
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        
        # Filtrar por videos que necesitan thumbnails
        if not force:
            query += " AND (thumbnail_path IS NULL OR thumbnail_path = '')"
        
        # Aplicar límite
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        # Ejecutar consulta
        with db.get_connection() as conn:
            cursor = conn.execute(query, params)
            videos = [dict(row) for row in cursor.fetchall()]
        
        # Filtrar videos por existencia de archivo y extensión
        valid_videos = []
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        
        for video in videos:
            file_path = Path(video['file_path'])
            
            # Verificar que el archivo existe
            if not file_path.exists():
                logger.debug(f"Archivo no existe: {file_path}")
                continue
            
            # Verificar que es un video (no imagen)
            if file_path.suffix.lower() not in video_extensions:
                continue
            
            # Verificar si necesita thumbnail (para force=True)
            if force or not video.get('thumbnail_path') or not Path(str(video['thumbnail_path'])).exists():
                valid_videos.append(video)
        
        return valid_videos
    
    def _prioritize_videos_with_characters(self, videos):
        """🎯 Priorizar videos con personajes detectados para thumbnails"""
        priority_videos = []
        normal_videos = []
        
        for video in videos:
            detected_characters = video.get('detected_characters')
            
            # Verificar si tiene personajes detectados
            has_characters = False
            if detected_characters:
                try:
                    import json
                    characters = json.loads(detected_characters) if isinstance(detected_characters, str) else detected_characters
                    has_characters = len(characters) > 0
                except:
                    has_characters = False
            
            if has_characters:
                priority_videos.append(video)
            else:
                normal_videos.append(video)
        
        return {'priority': priority_videos, 'normal': normal_videos}
    
    def _generate_thumbnails_parallel(self, videos, force=False):
        """⚡ Generar thumbnails en paralelo con ThreadPoolExecutor"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        success = 0
        failed = 0
        # Optimizar workers para I/O bound (thumbnail generation)
        import os
        cpu_count = os.cpu_count() or 4
        # Para thumbnail generation, usar menos workers para evitar thrashing
        max_workers = min(4, len(videos))
        
        def generate_single_thumbnail(video_data):
            """Generar thumbnail para un video individual (sin actualizar BD)"""
            try:
                video_path = Path(video_data['file_path'])
                
                # Verificar que el archivo existe
                if not video_path.exists():
                    return {'success': False, 'error': f"Archivo no existe: {video_path}", 'video_id': video_data['id']}
                
                # Generar thumbnail
                thumbnail_path = thumbnail_generator.generate_thumbnail(video_path, force_regenerate=force)
                
                if thumbnail_path:
                    # NO actualizar BD aquí - acumular para batch update
                    return {
                        'success': True, 
                        'path': str(thumbnail_path), 
                        'video_name': video_path.name,
                        'video_id': video_data['id'],
                        'thumbnail_path': str(thumbnail_path)
                    }
                else:
                    return {'success': False, 'error': f"Falló generación para {video_path.name}", 'video_id': video_data['id']}
                    
            except Exception as e:
                return {'success': False, 'error': f"Error con {video_data.get('file_name', 'unknown')}: {e}", 'video_id': video_data['id']}
        
        # Procesamiento en paralelo con batch updates
        batch_updates = []  # Acumular updates para BD
        batch_size = 25  # Actualizar BD cada 25 thumbnails
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas
            future_to_video = {
                executor.submit(generate_single_thumbnail, video): video 
                for video in videos
            }
            
            # Recopilar resultados conforme se completan
            for i, future in enumerate(as_completed(future_to_video), 1):
                try:
                    result = future.result()
                    
                    if result['success']:
                        success += 1
                        logger.info(f"✓ {result['video_name']}")
                        
                        # Acumular update para batch
                        batch_updates.append({
                            'video_id': result['video_id'],
                            'updates': {'thumbnail_path': result['thumbnail_path']}
                        })
                        
                    else:
                        failed += 1
                        logger.warning(f"✗ {result['error']}")
                    
                    # Batch update cada 25 thumbnails o al final
                    if len(batch_updates) >= batch_size or i == len(videos):
                        if batch_updates:
                            try:
                                batch_success, batch_failed = db.batch_update_videos(batch_updates)
                                logger.debug(f"🔄 Batch update: {batch_success} exitosos, {batch_failed} fallidos")
                                batch_updates = []  # Limpiar batch
                            except Exception as e:
                                logger.warning(f"Error en batch update: {e}")
                    
                    # Mostrar progreso cada 10 thumbnails
                    if i % 10 == 0 or i == len(videos):
                        logger.info(f"⚡ Progreso: {i}/{len(videos)} ({i/len(videos)*100:.1f}%) - {success} exitosos, {failed} fallidos")
                        
                except Exception as e:
                    failed += 1
                    video = future_to_video[future]
                    logger.error(f"Error procesando {video.get('file_name', 'unknown')}: {e}")
        
        # Procesar cualquier update restante
        if batch_updates:
            try:
                batch_success, batch_failed = db.batch_update_videos(batch_updates)
                logger.info(f"🔄 Batch update final: {batch_success} exitosos, {batch_failed} fallidos")
            except Exception as e:
                logger.warning(f"Error en batch update final: {e}")
        
        return success, failed
        
    def clear_thumbnails(self, platform=None, force=False):
        """
        Eliminar thumbnails de la carpeta de thumbnails
        
        Args:
            platform: plataforma específica o None para todas
            force: forzar eliminación sin confirmación
        """
        logger.info("Limpiando thumbnails...")
        
        # Obtener thumbnails a eliminar
        thumbnails_to_delete = []
        
        if platform:
            # Solo thumbnails de una plataforma específica
            videos = db.get_videos({'platform': platform})
            platform_thumbs = set()
            for video in videos:
                if video.get('thumbnail_path'):
                    thumb_path = Path(video['thumbnail_path'])
                    if thumb_path.exists():
                        platform_thumbs.add(thumb_path)
            thumbnails_to_delete = list(platform_thumbs)
        else:
            # Todos los thumbnails
            thumbnails_to_delete = list(config.THUMBNAILS_PATH.glob('*.jpg'))
        
        if not thumbnails_to_delete:
            logger.info("No hay thumbnails para eliminar")
            return
        
        total_size = sum(thumb.stat().st_size for thumb in thumbnails_to_delete)
        logger.info(f"Thumbnails a eliminar: {len(thumbnails_to_delete)} ({total_size / 1024 / 1024:.1f} MB)")
        
        if not force:
            response = input(f"¿Confirmar eliminación de {len(thumbnails_to_delete)} thumbnails? [y/N]: ")
            if response.lower() != 'y':
                logger.info("Operación cancelada")
                return
        
        # Eliminar thumbnails
        deleted = 0
        for thumb_path in thumbnails_to_delete:
            try:
                thumb_path.unlink()
                deleted += 1
            except Exception as e:
                logger.error(f"Error eliminando {thumb_path}: {e}")
        
        # Limpiar referencias en la BD si se eliminaron todos
        if not platform:
            try:
                with db.get_connection() as conn:
                    conn.execute("UPDATE videos SET thumbnail_path = NULL")
                logger.info("✓ Referencias de thumbnails limpiadas en la BD")
            except Exception as e:
                logger.error(f"Error limpiando referencias en BD: {e}")
        
        logger.info(f"✅ Eliminados {deleted} thumbnails")
    
    def show_sources_stats(self):
        """Mostrar estadísticas de todas las fuentes de datos (incluyendo plataformas adicionales)"""
        logger.info("Obteniendo estadísticas de fuentes externas...")
        
        # Usar stats extendidas que incluyen plataformas adicionales
        stats = external_sources.get_platform_stats_extended()
        
        print("\nESTADISTICAS DE FUENTES EXTERNAS")
        print("=" * 50)
        
        total_db = 0
        total_organized = 0
        
        # Mostrar plataformas principales
        for platform, counts in stats['main'].items():
            db_count = counts['db']
            org_count = counts['organized']
            total_db += db_count
            total_organized += org_count
            
            print(f"{platform.upper()}:")
            print(f"  [BD]: {db_count}")
            print(f"  [Carpetas]: {org_count}")
            print(f"  [Total]: {db_count + org_count}")
            print()
        
        # Mostrar plataformas adicionales si existen
        if stats['additional']:
            print("PLATAFORMAS ADICIONALES:")
            print("-" * 30)
            for platform, count in stats['additional'].items():
                total_organized += count
                print(f"{platform.upper()}:")
                print(f"  [BD]: 0")
                print(f"  [Carpetas]: {count}")
                print(f"  [Total]: {count}")
                print()
        
        print(f"TOTALES:")
        print(f"  [BD]: {total_db}")
        print(f"  [Carpetas]: {total_organized}")
        print(f"  [Gran total]: {total_db + total_organized}")
        
        # Stats de la BD de Tag-Flow
        try:
            tagflow_stats = db.get_stats()
            print(f"\nTAG-FLOW DATABASE")
            print("=" * 30)
            print(f"Videos en BD: {tagflow_stats['total_videos']}")
            print(f"Con musica: {tagflow_stats['with_music']}")
            print(f"Con personajes: {tagflow_stats['with_characters']}")
            
            if tagflow_stats['by_platform']:
                print("\nPor plataforma:")
                for platform, count in tagflow_stats['by_platform'].items():
                    print(f"  {platform}: {count}")
            
        except Exception as e:
            logger.error(f"Error obteniendo stats de Tag-Flow: {e}")
        
        return stats
        """Generar reporte del estado del sistema"""
        logger.info("Generando reporte del sistema...")
        
        try:
            stats = db.get_stats()
            creators = db.get_unique_creators()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'database': {
                    'total_videos': stats['total_videos'],
                    'by_status': stats['by_status'],
                    'by_platform': stats['by_platform'],
                    'with_music': stats['with_music'],
                    'with_characters': stats['with_characters'],
                    'unique_creators': len(creators)
                },
                'files': {
                    'thumbnails_count': len(list(config.THUMBNAILS_PATH.glob('*.jpg'))),
                    'database_size_mb': config.DATABASE_PATH.stat().st_size / 1024 / 1024 if config.DATABASE_PATH.exists() else 0
                },
                'configuration': {
                    'apis_configured': len(config.validate_config()) == 0,
                    'deepface_enabled': config.USE_GPU_DEEPFACE,
                    'thumbnail_size': config.THUMBNAIL_SIZE
                }
            }
            
            # Guardar reporte
            report_path = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"✅ Reporte generado: {report_path}")
            
            # Mostrar resumen
            print("\n📊 RESUMEN DEL SISTEMA")
            print("=" * 40)
            print(f"Videos totales: {stats['total_videos']}")
            print(f"Con música: {stats['with_music']}")
            print(f"Con personajes: {stats['with_characters']}")
            print(f"Creadores únicos: {len(creators)}")
            print(f"Thumbnails: {report['files']['thumbnails_count']}")
            print(f"Tamaño BD: {report['files']['database_size_mb']:.1f} MB")
            
            return report_path
            
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return None

    def show_character_stats(self):
        """FINAL: Mostrar estadísticas completas del sistema optimizado"""
        logger.info("Obteniendo estadísticas de Character Intelligence...")
        
        stats = character_intelligence.get_stats()
        
        print("\nINTELIGENCIA DE PERSONAJES - SISTEMA OPTIMIZADO")
        print("=" * 60)
        print(f"Personajes conocidos: {stats['total_characters']}")
        print(f"Juegos/Series: {stats['total_games']}")
        print(f"Detector: {stats['detector_type'].upper()}")
        print(f"Mapeos creador->personaje: {stats['creator_mappings']}")
        print(f"Auto-detectados: {stats['auto_detected_mappings']}")
        print(f"BD Personajes: {stats['database_file']}")
        print(f"BD Mapeos: {stats['mapping_file']}")
        
        # Estadísticas específicas del detector optimizado
        if stats['detector_type'] == 'optimized':
            print(f"\nRENDIMIENTO OPTIMIZADO:")
            print(f"  Patrones jerárquicos: {stats.get('optimized_patterns', 'N/A')}")
            print(f"  Cache hit rate: {stats.get('cache_hit_rate', 'N/A')}%")
            print(f"  Tiempo promedio detección: {stats.get('avg_detection_time_ms', 'N/A')}ms")
            
            # Distribución de patrones por categoría
            pattern_dist = stats.get('pattern_distribution', {})
            if pattern_dist:
                print(f"  Distribución de patrones:")
                for category, count in pattern_dist.items():
                    print(f"    {category}: {count}")
        
        # Mostrar personajes por juego usando métodos públicos
        print(f"\nPersonajes por juego:")
        for game, game_data in character_intelligence.character_db.items():
            if isinstance(game_data.get('characters'), dict):
                count = len(game_data['characters'])
                print(f"  {game.replace('_', ' ').title()}: {count}")
                
                # Mostrar algunos ejemplos
                examples = list(game_data['characters'].keys())[:3]
                print(f"    Ejemplos: {', '.join(examples)}")
                if count > 3:
                    print(f"    ... y {count - 3} mas")
        
        # Mostrar mapeos de TikToker Personas
        auto_detected = character_intelligence.creator_mapping.get('auto_detected', {})
        if auto_detected:
            print(f"\nTikToker Personas configurados:")
            for creator, data in auto_detected.items():
                character = data.get('character', 'N/A')
                confidence = data.get('confidence', 'N/A')
                platform = data.get('platform', 'N/A')
                print(f"  {creator} -> {character} (confidence: {confidence}, platform: {platform})")
        else:
            print(f"\nTikToker Personas: Ninguno configurado")
            print("    Usa 'python maintenance.py add-tiktoker --creator NOMBRE' para agregar")
        
        # Reporte de rendimiento si está disponible
        if stats['detector_type'] == 'optimized':
            try:
                performance = character_intelligence.get_performance_report()
                if performance and 'total_patterns' in performance:
                    print(f"\nESTADISTICAS DETALLADAS DE RENDIMIENTO:")
                    print(f"  Total consultas: {performance.get('cache_size', 0)} en cache")
                    
                    # Mostrar métricas de eficiencia si están disponibles
                    for category, count in performance.get('pattern_distribution', {}).items():
                        efficiency = count / performance.get('total_patterns', 1) * 100
                        print(f"  {category.title()}: {count} patrones ({efficiency:.1f}%)")
            except Exception as e:
                logger.debug(f"Error obteniendo estadísticas detalladas: {e}")
        
        print(f"\nSistema listo para procesamiento optimizado de videos!")
        print(f"Usa 'python main.py 10' para procesar videos con detector optimizado")
    
    def clean_false_positives(self, force: bool = False):
        """Limpiar falsos positivos del sistema de reconocimiento de personajes"""
        logger.info("Iniciando limpieza de falsos positivos...")
        
        # Lista de falsos positivos conocidos
        false_positives = {
            'animegamey', 'zenlesszonezero', 'forte', 'mamama', 'batte',
            'genshin', 'honkai', 'impact', 'zenless', 'zone', 'zero', 'star', 'rail',
            'hsr', 'hi3', 'zzz', 'genshinimpact', 'honkaiimpact', 'honkaistarrail',
            'wuthering', 'waves', 'anime', 'game', 'gaming', 'mmd', 'dance',
            'cosplay', 'cos', 'shorts', 'tiktok', 'video', 'compilation'
        }
        
        # Confirmar acción si no es force
        if not force:
            print(f"\n⚠️  Esta operación limpiará falsos positivos conocidos:")
            print(f"   {', '.join(sorted(false_positives))}")
            confirm = input("¿Continuar? (y/N): ").lower().strip()
            if confirm != 'y':
                logger.info("Operación cancelada")
                return
        
        try:
            # Obtener videos con personajes detectados
            videos = db.get_videos()
            updates_made = 0
            total_false_positives_removed = 0
            
            for video in videos:
                if not video.get('detected_characters'):
                    continue
                
                try:
                    # Parsear personajes detectados
                    characters = json.loads(video['detected_characters'])
                    original_count = len(characters)
                    
                    # Filtrar falsos positivos
                    cleaned_characters = [
                        char for char in characters 
                        if char.lower().strip() not in false_positives
                    ]
                    
                    # Si hay cambios, actualizar
                    if len(cleaned_characters) != original_count:
                        new_characters_json = json.dumps(cleaned_characters) if cleaned_characters else None
                        
                        # Actualizar en la base de datos
                        db.update_video_characters(video['id'], new_characters_json)
                        
                        updates_made += 1
                        removed_count = original_count - len(cleaned_characters)
                        total_false_positives_removed += removed_count
                        
                        logger.info(f"Video {video['id']}: {removed_count} falsos positivos removidos")
                        
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Error parseando personajes en video {video.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Limpieza completada:")
            logger.info(f"   - Videos actualizados: {updates_made}")
            logger.info(f"   - Falsos positivos removidos: {total_false_positives_removed}")
            
            # Mostrar estadísticas post-limpieza
            total_videos = len(videos)
            videos_with_chars = len([v for v in videos if v.get('detected_characters')])
            
            logger.info(f"📊 Estadísticas post-limpieza:")
            logger.info(f"   - Total videos: {total_videos}")
            logger.info(f"   - Videos con personajes: {videos_with_chars}")
            if total_videos > 0:
                logger.info(f"   - Tasa de detección: {videos_with_chars/total_videos*100:.1f}%")
            
        except Exception as e:
            logger.error(f"Error durante la limpieza: {e}")

    def add_custom_character(self, character_name: str, game: str, aliases: list = None):
        """Agregar un personaje personalizado con estructura jerárquica optimizada"""
        logger.info(f"Agregando personaje personalizado: {character_name} ({game})")
        
        success = character_intelligence.add_custom_character(character_name, game, aliases)
        
        if success:
            # Obtener la entrada creada para mostrar detalles
            if game in character_intelligence.character_db:
                game_data = character_intelligence.character_db[game]
                if isinstance(game_data.get('characters'), dict) and character_name in game_data['characters']:
                    char_info = game_data['characters'][character_name]
                    
                    print(f"[OK] Personaje agregado: {character_name}")
                    print(f"   Juego: {game}")
                    if aliases:
                        print(f"   Aliases: {', '.join(aliases)}")
                    
                    # Manejar context_hints de forma segura para evitar problemas de codificación
                    try:
                        context_hints = char_info.get('context_hints', [])
                        print(f"   Context hints: {context_hints}")
                    except UnicodeEncodeError:
                        print(f"   Context hints: [hintsdetected]")
                    
                    # Manejar variants de forma segura
                    try:
                        exact_variants = char_info['variants'].get('exact', [])
                        # Filtrar caracteres no imprimibles para Windows
                        safe_exact = [v for v in exact_variants if all(ord(c) < 127 or c.isalnum() for c in v)]
                        if safe_exact:
                            print(f"   Exact: {safe_exact}")
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        print(f"   Exact: [variants detected]")
                    
                    try:
                        common_variants = char_info['variants'].get('common', [])
                        # Filtrar caracteres seguros para Windows
                        safe_common = [v for v in common_variants if all(ord(c) < 127 or c.isalnum() for c in v)]
                        if safe_common:
                            print(f"   Common: {safe_common}")
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        print(f"   Common: [variants detected]")
                    
                    if 'joined' in char_info['variants']:
                        try:
                            joined = char_info['variants']['joined']
                            print(f"   Joined: {joined}")
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            print(f"   Joined: [variants detected]")
                    
                    if 'abbreviations' in char_info['variants']:
                        try:
                            abbrev = char_info['variants']['abbreviations']
                            print(f"   Abbreviations: {abbrev}")
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            print(f"   Abbreviations: [variants detected]")
                else:
                    print(f"[OK] Personaje agregado: {character_name}")
                    if aliases:
                        print(f"   Aliases: {', '.join(aliases)}")
            else:
                print(f"[OK] Personaje agregado: {character_name}")
                if aliases:
                    print(f"   Aliases: {', '.join(aliases)}")
        else:
            print(f"[ERROR] Error agregando personaje: {character_name}")
    
    def add_tiktoker_persona(self, creator_name: str, persona_name: str = None, confidence: float = 0.9):
        """Agregar un TikToker como personaje con estructura jerárquica optimizada"""
        logger.info(f"Agregando TikToker como personaje: {creator_name}")
        
        # Si no se especifica persona_name, usar el nombre del creador limpio
        if not persona_name:
            # Limpiar nombre del creador (remover .cos, @, etc.)
            persona_name = creator_name.replace('.cos', '').replace('@', '').replace('_', ' ').title()
        
        try:
            # Asegurar que existe tiktoker_personas con estructura jerárquica
            if 'tiktoker_personas' not in character_intelligence.character_db:
                character_intelligence.character_db['tiktoker_personas'] = {
                    'characters': {}  # Nueva estructura jerárquica
                }
            
            tiktoker_game = character_intelligence.character_db['tiktoker_personas']
            
            # Migrar a estructura jerárquica si es necesario
            if not isinstance(tiktoker_game.get('characters'), dict):
                # Convertir de lista legacy a estructura jerárquica
                legacy_chars = tiktoker_game.get('characters', [])
                legacy_aliases = tiktoker_game.get('aliases', {})
                
                tiktoker_game['characters'] = {}
                for char in legacy_chars:
                    tiktoker_game['characters'][char] = {
                        'canonical_name': char,
                        'priority': 2,  # Prioridad media para TikTokers
                        'variants': {
                            'exact': [char],
                            'common': [char]
                        },
                        'detection_weight': 0.9,
                        'context_hints': ['cosplay', 'tiktok', 'dance'],
                        'platform_specific': 'tiktok'
                    }
                    
                    # Migrar aliases
                    if char in legacy_aliases:
                        tiktoker_game['characters'][char]['variants']['exact'].extend(legacy_aliases[char])
                
                # Limpiar estructura legacy
                if 'aliases' in tiktoker_game:
                    del tiktoker_game['aliases']
            
            # Agregar nuevo TikToker con estructura jerárquica completa
            if persona_name not in tiktoker_game['characters']:
                # Crear entrada jerárquica optimizada para TikToker
                tiktoker_entry = {
                    'canonical_name': persona_name,
                    'priority': 2,  # Prioridad media para TikTokers
                    'variants': {
                        'exact': [persona_name],  # Solo el nombre canónico en exact
                        'common': [persona_name, f"{persona_name} Cosplay"],  # CORREGIDO: Aliases en common
                        'usernames': [creator_name]  # Nueva categoría para usernames
                    },
                    'detection_weight': 0.95,
                    'context_hints': ['cosplay', 'tiktok', 'dance', 'cos', 'tiktoker', 'creator'],  # MEJORADO: Más context hints
                    'auto_detect_for_creator': creator_name,  # Mapeo automático
                    'confidence': confidence,
                    'platform_specific': 'tiktok',
                    'added_timestamp': time.time(),
                    'tiktoker_persona': True  # Marcar como TikToker persona
                }
                
                # Agregar variantes adicionales inteligentemente
                if creator_name != persona_name and creator_name not in tiktoker_entry['variants']['common']:
                    tiktoker_entry['variants']['common'].append(creator_name)
                
                # Si el creator tiene .cos, agregar también la versión base
                if '.cos' in creator_name:
                    base_name = creator_name.replace('.cos', '')
                    if base_name not in tiktoker_entry['variants']['common']:
                        tiktoker_entry['variants']['common'].append(base_name)
                
                tiktoker_game['characters'][persona_name] = tiktoker_entry
                
                logger.info(f"Nueva entrada TikToker creada: {persona_name}")
                logger.info(f"Variantes generadas: {tiktoker_entry['variants']}")
            else:
                # Actualizar entrada existente con lógica mejorada
                existing_entry = tiktoker_game['characters'][persona_name]
                
                # Actualizar auto_detect_for_creator si no existe
                if 'auto_detect_for_creator' not in existing_entry:
                    existing_entry['auto_detect_for_creator'] = creator_name
                
                # Asegurar que tiene la estructura de variants correcta
                if 'variants' not in existing_entry:
                    existing_entry['variants'] = {'exact': [persona_name], 'common': [persona_name]}
                
                # Agregar creator_name a variantes si no está (MEJORADO: common en lugar de exact)
                if 'common' not in existing_entry['variants']:
                    existing_entry['variants']['common'] = [persona_name]
                
                if creator_name not in existing_entry['variants']['common']:
                    existing_entry['variants']['common'].append(creator_name)
                
                # Agregar a usernames si no está
                if 'usernames' not in existing_entry['variants']:
                    existing_entry['variants']['usernames'] = []
                if creator_name not in existing_entry['variants']['usernames']:
                    existing_entry['variants']['usernames'].append(creator_name)
                
                # Mejorar context_hints si no existen o están limitados
                if not existing_entry.get('context_hints') or len(existing_entry['context_hints']) < 3:
                    existing_entry['context_hints'] = ['cosplay', 'tiktok', 'dance', 'cos', 'tiktoker', 'creator']
                
                logger.info(f"Entrada TikToker actualizada: {persona_name}")
            
            # Regenerar patrones en el detector optimizado
            if character_intelligence.optimized_detector:
                try:
                    character_intelligence.optimized_detector.reload_patterns(character_intelligence.character_db)
                    logger.info("Patrones del detector optimizado actualizados")
                except Exception as e:
                    logger.warning(f"Error recargando patrones optimizados: {e}")
            
            # Actualizar patrones legacy para compatibilidad
            character_intelligence.character_patterns = character_intelligence._init_character_patterns()
            
            # Guardar cambios
            character_intelligence._save_character_database()
            
            print(f"[OK] TikToker agregado como personaje:")
            print(f"   Creador: {creator_name}")
            print(f"   Personaje: {persona_name}")
            print(f"   Confianza: {confidence}")
            print(f"   Context hints: {tiktoker_game['characters'][persona_name]['context_hints']}")
            print(f"   Estructura: Jerarquica optimizada")
            print(f"   Exact: {tiktoker_game['characters'][persona_name]['variants']['exact']}")
            print(f"   Common: {tiktoker_game['characters'][persona_name]['variants']['common']}")
            print(f"   Auto-deteccion: Habilitada para videos de {creator_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error agregando TikToker como personaje: {e}")
            print(f"[ERROR] Error agregando TikToker: {e}")
            return False
    
    def list_available_platforms(self):
        """
        🆕 Listar todas las plataformas disponibles (principales + adicionales)
        """
        logger.info("Obteniendo plataformas disponibles...")
        
        try:
            # Obtener plataformas disponibles
            platforms = external_sources.get_available_platforms()
            stats = external_sources.get_platform_stats_extended()
            
            print("\n" + "="*60)
            print("PLATAFORMAS DISPONIBLES EN TAG-FLOW V2")
            print("="*60)
            
            # Plataformas principales
            print("\nPLATAFORMAS PRINCIPALES (con integración de BD):")
            print("-" * 50)
            
            for platform_key, platform_info in platforms['main'].items():
                print(f"\n{platform_key.upper()} ({platform_info['folder_name']})")
                
                # Estado de fuentes
                db_status = "Disponible" if platform_info['has_db'] else "No encontrada"
                folder_status = "Disponible" if platform_info['has_organized'] else "No encontrada"
                
                print(f"  Base de datos externa: {db_status}")
                print(f"  Carpeta organizada:    {folder_status}")
                
                # Estadísticas
                if platform_key in stats['main']:
                    platform_stats = stats['main'][platform_key]
                    print(f"  Videos en BD externa:  {platform_stats['db']}")
                    print(f"  Videos en carpeta:     {platform_stats['organized']}")
                    total = platform_stats['db'] + platform_stats['organized']
                    print(f"  TOTAL DISPONIBLE:      {total}")
            
            # Plataformas adicionales
            if platforms['additional']:
                print("\nPLATAFORMAS ADICIONALES (solo carpetas):")
                print("-" * 50)
                
                for platform_key, platform_info in platforms['additional'].items():
                    print(f"\n{platform_key.upper()} ({platform_info['folder_name']})")
                    print(f"  Ruta: {platform_info['folder_path']}")
                    
                    # Estadísticas
                    if platform_key in stats['additional']:
                        count = stats['additional'][platform_key]
                        print(f"  Videos disponibles: {count}")
                    else:
                        print(f"  Videos disponibles: 0 (no escaneado)")
            else:
                print("\nPLATAFORMAS ADICIONALES:")
                print("-" * 50)
                print("  No se encontraron plataformas adicionales")
                print("  Agrega carpetas en D:\\4K All\\ para nuevas plataformas")
            
            print("\n" + "="*60)
            print("OPCIONES DE USO:")
            print("="*60)
            print("  --platform youtube        -> Solo YouTube")
            print("  --platform tiktok         -> Solo TikTok") 
            print("  --platform instagram      -> Solo Instagram")
            if platforms['additional']:
                for platform_key in platforms['additional'].keys():
                    print(f"  --platform {platform_key:<14} -> Solo {platform_key.title()}")
            print("  --platform other          -> Solo plataformas adicionales")
            print("  --platform all-platforms  -> Todas las plataformas")
            print("  (sin --platform)          -> Solo principales (YT+TT+IG)")
            
            print("\nEJEMPLOS DE COMANDOS:")
            print("="*60)
            print("  python maintenance.py populate-db --platform other")
            print("  python maintenance.py populate-db --platform iwara --limit 50")
            print("  python maintenance.py populate-db --platform all-platforms")
            if platforms['additional']:
                first_additional = list(platforms['additional'].keys())[0]
                print(f"  python maintenance.py populate-db --platform {first_additional}")
            
            print("\nListado completado!")
            
        except Exception as e:
            logger.error(f"Error listando plataformas: {e}")

    def show_optimization_stats(self):
        """
        Mostrar estadísticas de optimizaciones de BD para main.py
        """
        print("\n" + "="*60)
        print("ESTADISTICAS DE OPTIMIZACION - TAG-FLOW V2")
        print("="*60)
        
        # Verificar configuración
        print(f"Estado de optimizaciones: {'ACTIVAS' if config.USE_OPTIMIZED_DATABASE else 'DESACTIVADAS'}")
        print(f"Cache TTL configurado: {config.DATABASE_CACHE_TTL} segundos")
        print(f"Cache size maximo: {config.DATABASE_CACHE_SIZE} entradas")
        print(f"Metricas habilitadas: {'SI' if config.ENABLE_PERFORMANCE_METRICS else 'NO'}")
        
        if not config.USE_OPTIMIZED_DATABASE:
            print("\nOPTIMIZACIONES DESACTIVADAS")
            print("Para activar, configura USE_OPTIMIZED_DATABASE=true en .env")
            print("\nBeneficios de las optimizaciones:")
            print("  - 10-20x mejora en verificacion de duplicados")
            print("  - 5-10x mejora en busqueda de videos pendientes")
            print("  - 70% reduccion en I/O de base de datos")
            print("  - Cache inteligente con 80-95% hit rate")
            return
        
        # Intentar mostrar estadísticas de optimización
        try:
            # Importar OptimizedDatabaseManager
            sys.path.append(str(Path(__file__).parent / 'src'))
            from src.optimized_database import OptimizedDatabaseManager
            from src.pattern_cache import get_global_cache
            
            # Crear instancia optimizada
            optimized_db = OptimizedDatabaseManager()
            cache = get_global_cache()
            
            print("\nESTADO ACTUAL:")
            print("-" * 40)
            
            # Estadísticas del cache
            cache_stats = cache.get_cache_stats()
            memory_usage = cache.get_memory_usage()
            
            print(f"Total consultas realizadas: {cache_stats['total_queries']}")
            print(f"Cache hits: {cache_stats['cache_hits']}")
            print(f"Cache misses: {cache_stats['cache_misses']}")
            print(f"Hit rate: {cache_stats['hit_rate_percentage']}%")
            print(f"Eficiencia: {cache_stats['cache_efficiency']}")
            
            print(f"\nUSO DE MEMORIA:")
            print("-" * 40)
            print(f"Cache de paths: {memory_usage['paths_cache_mb']} MB")
            print(f"Cache de pendientes: {memory_usage['pending_cache_mb']} MB")
            print(f"Total cache: {memory_usage['total_cache_mb']} MB")
            
            # Performance report si está disponible
            try:
                performance_report = optimized_db.get_performance_report()
                
                print(f"\nRENDIMIENTO:")
                print("-" * 40)
                print(f"Runtime total: {performance_report['total_runtime_seconds']:.2f}s")
                print(f"Queries ejecutadas: {performance_report['total_db_queries']}")
                print(f"Queries/segundo: {performance_report['queries_per_second']:.1f}")
                print(f"Performance grade: {performance_report['performance_grade']}")
                
                if performance_report.get('avg_query_times'):
                    print(f"\nTIEMPOS PROMEDIO POR QUERY:")
                    print("-" * 40)
                    for query_type, avg_time in performance_report['avg_query_times'].items():
                        print(f"  {query_type}: {avg_time:.3f}s")
                        
            except Exception as e:
                logger.debug(f"Error obteniendo performance report: {e}")
            
            # Recomendaciones
            hit_rate = cache_stats['hit_rate_percentage']
            print(f"\nRECOMENDACIONES:")
            print("-" * 40)
            
            if hit_rate >= 90:
                print("EXCELENTE - sistema optimizado funcionando perfectamente")
            elif hit_rate >= 70:
                print("BUENA performance - considera aumentar DATABASE_CACHE_SIZE")
            else:
                print("Performance mejorable - revisa configuracion del cache")
                print("   - Aumenta DATABASE_CACHE_TTL para datos mas estables")
                print("   - Aumenta DATABASE_CACHE_SIZE para mejor hit rate")
            
            print(f"\nACCIONES DISPONIBLES:")
            print("-" * 40)
            print("  python maintenance.py optimization-stats  -> Ver estas estadisticas")
            print("  python main.py --limit 10  -> Test con optimizaciones")
            
        except ImportError as e:
            print(f"\nERROR: No se pudieron cargar las optimizaciones")
            print(f"Detalles: {e}")
            print(f"\nSolucion:")
            print(f"1. Verifica que src/optimized_database.py existe")
            print(f"2. Verifica que src/pattern_cache.py existe") 
            print(f"3. Ejecuta: python verify_config.py")
            
        except Exception as e:
            print(f"\nERROR obteniendo estadisticas de optimizacion: {e}")
            logger.error(f"Error en show_optimization_stats: {e}")
        
        print("="*60)

    def download_character_images(self, character_name: str = None, game: str = None, limit: int = None):
        """Descargar imágenes de referencia para personajes"""
        if character_name:
            # Descargar para un personaje específico
            logger.info(f"Descargando imagen para {character_name}...")
            image_path = character_intelligence.download_character_reference_image(character_name, game)
            if image_path:
                print(f"[OK] Imagen descargada: {image_path}")
            else:
                print(f"[ERROR] No se pudo descargar imagen para {character_name}")
        else:
            # Descargar para personajes sin imagen
            logger.info("Descargando imágenes para personajes sin referencia...")
            
            # Encontrar personajes sin imagen en caras_conocidas
            missing_count = 0
            processed = 0
            
            for game, game_data in character_intelligence.character_db.items():
                if limit and processed >= limit:
                    break
                
                # ARREGLADO: Usar wrapper de compatibilidad
                characters = character_intelligence._get_characters_compatible(game_data)
                for character in characters:
                    if limit and processed >= limit:
                        break
                    
                    # Verificar si ya tiene imagen
                    game_dir = character_intelligence.known_faces_path / game.replace('_', ' ').title()
                    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
                    has_image = any((game_dir / f"{character}{ext}").exists() for ext in image_extensions)
                    
                    if not has_image:
                        logger.info(f"Descargando imagen para {character}...")
                        image_path = character_intelligence.download_character_reference_image(character, game)
                        if image_path:
                            print(f"[OK] {character}")
                        else:
                            print(f"[ERROR] {character}")
                        missing_count += 1
                    
                    processed += 1
            
            print(f"\nProcesados: {processed}, Sin imagen: {missing_count}")
            print("Nota: La descarga automatica requiere configurar APIs de busqueda de imagenes")
    
    def analyze_existing_titles(self, limit: int = None):
        """Analizar títulos existentes para detectar personajes"""
        logger.info("Analizando títulos existentes para detectar personajes...")
        
        # Obtener videos sin personajes detectados
        videos = db.get_videos({'no_characters': True}, limit=limit)
        
        if not videos:
            print("No hay videos sin personajes para analizar")
            return
        
        analyzed = 0
        detected = 0
        
        for video in videos:
            title = video.get('title', '')
            if not title:
                continue
            
            # Analizar título
            suggestions = character_intelligence.analyze_video_title(title)
            
            if suggestions:
                # Actualizar base de datos con sugerencias
                detected_chars = [s['name'] for s in suggestions]
                db.update_video(video['id'], {'detected_characters': detected_chars})
                
                print(f"[OK] {video['file_name'][:50]}... -> {', '.join(detected_chars)}")
                detected += 1
            
            analyzed += 1
        
        print(f"\nAnalizados: {analyzed}, Con personajes detectados: {detected}")
    
    def _generate_persona_name(self, creator_name: str) -> str:
        """Generar nombre de personaje basado en el nombre del creador"""
        
        # Limpiar el nombre del creador
        # Remover extensiones comunes
        clean_name = creator_name.replace('.cos', '').replace('.cosplay', '')
        clean_name = clean_name.replace('@', '').replace('_', ' ')
        
        # Si tiene punto, tomar solo la parte antes del punto
        if '.' in clean_name and not clean_name.endswith('.cos'):
            clean_name = clean_name.split('.')[0]
        
        # Capitalizar palabras
        words = clean_name.split()
        capitalized_words = []
        
        for word in words:
            if len(word) > 0:
                # Capitalizar primera letra y mantener el resto como está
                capitalized_word = word[0].upper() + word[1:] if len(word) > 1 else word.upper()
                capitalized_words.append(capitalized_word)
        
        persona_name = ' '.join(capitalized_words)
        
        # Si el resultado es muy corto o tiene caracteres extraños, usar nombre base
        if len(persona_name) < 3 or not any(c.isalpha() for c in persona_name):
            # Fallback: usar una versión más básica
            basic_clean = ''.join(c for c in creator_name if c.isalnum())
            if len(basic_clean) >= 3:
                persona_name = basic_clean.capitalize()
            else:
                persona_name = creator_name.capitalize()
        
        return persona_name
    
    def update_creator_mappings(self, limit: int = None):
        """Analizar creadores para detectar cosplayers/performers que deberían ser personajes de sí mismos
        🆕 MEJORADO: Prioridad especial para TikTok e Instagram"""
        logger.info("Analizando creadores para detectar cosplayers/performers...")
        
        # 🆕 CONFIGURACIÓN DE PLATAFORMAS CON PRIORIDAD
        platform_weights = {
            'tiktok': 2.5,      # 🔥 Prioridad ALTA - TikTok es principalmente cosplayers/performers
            'instagram': 2.0,   # 🔥 Prioridad ALTA - Instagram es principalmente cosplayers/performers  
            'youtube': 1.0,     # Prioridad NORMAL - YouTube tiene mix de contenido
            'other': 1.2,       # Prioridad MEDIA - Otras plataformas tienden a ser cosplayers
            'unknown': 0.8      # Prioridad BAJA - Plataforma desconocida
        }
        
        # 🆕 BOOST DE CONFIANZA POR PLATAFORMA
        platform_confidence_boost = {
            'tiktok': 0.25,     # +25% confianza para TikTok
            'instagram': 0.20,  # +20% confianza para Instagram
            'youtube': 0.0,     # Sin boost para YouTube
            'other': 0.10,      # +10% para otras plataformas
            'unknown': -0.05    # -5% para plataformas desconocidas
        }
        
        # Obtener todos los videos para análisis
        videos = db.get_videos(limit=limit)
        creator_stats = {}
        
        # Palabras clave que indican que es un cosplayer/performer (no creador de MMD)
        cosplayer_keywords = {
            'cosplay', 'cos', 'dance', 'dancing', 'trend', 'trending', 'challenge', 
            'outfit', 'ootd', 'makeup', 'tutorial', 'transformation', 'acting',
            'performance', 'cover', 'choreo', 'choreography', 'viral', 'fyp',
            'tiktok', 'instagram', 'reel', 'short', 'shorts', 'live', 'stream',
            'photoshoot', 'modeling', 'pose', 'poses', 'selfie', 'me as', 'as me',
            'wearing', 'dressed', 'costume', 'wig', 'makeup', 'cosplaying', 'shorts'
        }
        
        # Palabras que indican contenido MMD/no-cosplayer (a evitar)
        mmd_keywords = {
            'mmd', 'model', 'animation', 'render', 'blender', '3d', 'motion',
            'camera', 'edit', 'editing', 'effects', 'compilation', 'pmx',
            'vmd', 'stage', 'background', 'lighting', 'shader', 'texture'
        }
        
        # 🆕 PALABRAS CLAVE ESPECÍFICAS PARA YOUTUBE (con hashtags)
        # Los hashtags son más comunes en contenido de personas reales en YouTube
        youtube_hashtag_keywords = {
            '#cosplay', '#shorts', '#dance', '#dancing', '#trend', '#trending', 
            '#challenge', '#outfit', '#ootd', '#makeup', '#tutorial', '#transformation',
            '#acting', '#performance', '#cover', '#choreo', '#choreography', '#viral',
            '#short', '#live', '#stream', '#photoshoot', '#modeling', '#pose', '#poses',
            '#selfie', '#costume', '#wig', '#cosplaying', '#dancer', '#performer'
        }
        
        # Analizar cada creador
        for video in videos:
            creator = video.get('creator_name', '')
            if not creator:
                continue
            
            if creator not in creator_stats:
                creator_stats[creator] = {
                    'total_videos': 0,
                    'cosplayer_indicators': 0,  # Videos que sugieren que es cosplayer
                    'mmd_indicators': 0,        # Videos que sugieren que es creador MMD
                    'platforms': set(),
                    'video_titles': [],
                    'characters_detected': {},
                    'recent_videos': [],
                    # 🆕 NUEVAS MÉTRICAS POR PLATAFORMA
                    'platform_videos': {},      # Conteo de videos por plataforma
                    'platform_cosplayer_score': {},  # Score de cosplayer por plataforma
                    'primary_platform': None,   # Plataforma principal del creador
                    'weighted_cosplayer_score': 0.0,  # Score ponderado total
                    'youtube_hashtag_bonus': 0  # 🆕 Bonus específico por hashtags de YouTube
                }
            
            creator_stats[creator]['total_videos'] += 1
            
            # 🆕 TRACKING POR PLATAFORMA
            platform = video.get('platform', 'unknown')
            creator_stats[creator]['platforms'].add(platform)
            
            if platform not in creator_stats[creator]['platform_videos']:
                creator_stats[creator]['platform_videos'][platform] = 0
                creator_stats[creator]['platform_cosplayer_score'][platform] = 0
            
            creator_stats[creator]['platform_videos'][platform] += 1
            
            # Analizar título del video de forma segura
            title = video.get('title') or ''
            description = video.get('description') or ''  # 🆕 INCLUIR DESCRIPTIONS
            filename = video.get('file_name') or ''
            combined_text = f"{title.lower()} {description.lower()} {filename.lower()}"  # 🆕 INCLUIR DESCRIPTIONS
            
            creator_stats[creator]['video_titles'].append(title or '[sin titulo]')
            creator_stats[creator]['recent_videos'].append({
                'title': title or '[sin titulo]',
                'filename': filename or '[sin nombre]',
                'characters': video.get('detected_characters', []),
                'platform': platform
            })
            
            # Detectar indicadores de cosplayer CON PESO POR PLATAFORMA
            cosplayer_score = 0
            for keyword in cosplayer_keywords:
                if keyword in combined_text:
                    cosplayer_score += 1
            
            # 🆕 LÓGICA ESPECIAL PARA YOUTUBE: Boost por hashtags
            youtube_hashtag_bonus = 0
            if platform == 'youtube':
                for hashtag_keyword in youtube_hashtag_keywords:
                    if hashtag_keyword in combined_text:
                        youtube_hashtag_bonus += 2  # Bonus extra por hashtag en YouTube
                        # Los hashtags en YouTube son MUY indicativos de personas reales
                
                # Agregar el bonus al score de cosplayer
                cosplayer_score += youtube_hashtag_bonus
            
            # 🆕 APLICAR PESO DE PLATAFORMA AL SCORE
            platform_weight = platform_weights.get(platform, 1.0)
            weighted_cosplayer_score = cosplayer_score * platform_weight
            
            if cosplayer_score > 0:
                creator_stats[creator]['cosplayer_indicators'] += cosplayer_score
                creator_stats[creator]['platform_cosplayer_score'][platform] += cosplayer_score
                creator_stats[creator]['weighted_cosplayer_score'] += weighted_cosplayer_score
                
                # 🆕 Guardar bonus de hashtags de YouTube
                if platform == 'youtube' and youtube_hashtag_bonus > 0:
                    creator_stats[creator]['youtube_hashtag_bonus'] += youtube_hashtag_bonus
            
            # Detectar indicadores de MMD (sin cambio, pero con menos peso para TikTok/Instagram)
            mmd_score = 0
            for keyword in mmd_keywords:
                if keyword in combined_text:
                    mmd_score += 1
            
            if mmd_score > 0:
                creator_stats[creator]['mmd_indicators'] += mmd_score
            
            # Contar personajes detectados (para contexto)
            detected_chars = video.get('detected_characters', [])
            if isinstance(detected_chars, str):
                try:
                    detected_chars = json.loads(detected_chars)
                except:
                    detected_chars = []
            
            for char in detected_chars:
                if char not in creator_stats[creator]['characters_detected']:
                    creator_stats[creator]['characters_detected'][char] = 0
                creator_stats[creator]['characters_detected'][char] += 1
        
        # 🆕 CALCULAR PLATAFORMA PRINCIPAL PARA CADA CREADOR
        for creator, stats in creator_stats.items():
            if stats['platform_videos']:
                # Encontrar la plataforma con más videos
                primary_platform = max(stats['platform_videos'].items(), key=lambda x: x[1])[0]
                stats['primary_platform'] = primary_platform
        
        # Analizar y generar sugerencias para cosplayers/performers
        cosplayer_suggestions = []
        mmd_creators_filtered = []
        
        print("\nANALISIS DE COSPLAYERS/PERFORMERS")
        print("=" * 50)
        
        for creator, stats in creator_stats.items():
            if stats['total_videos'] < 2:  # Mínimo 2 videos
                continue
            
            # Verificar si ya tiene mapeo
            existing_mapping = character_intelligence.analyze_creator_name(creator)
            if existing_mapping and existing_mapping.get('source') in ['creator_mapping', 'tiktoker_persona']:
                continue  # Ya tiene mapeo
            
            total_videos = stats['total_videos']
            cosplayer_indicators = stats['cosplayer_indicators']
            mmd_indicators = stats['mmd_indicators']
            primary_platform = stats['primary_platform']
            weighted_score = stats['weighted_cosplayer_score']
            
            # 🆕 CALCULAR RATIOS CON PESO POR PLATAFORMA
            cosplayer_ratio = cosplayer_indicators / total_videos if total_videos > 0 else 0
            weighted_cosplayer_ratio = weighted_score / total_videos if total_videos > 0 else 0
            mmd_ratio = mmd_indicators / total_videos if total_videos > 0 else 0
            
            # 🆕 AJUSTE ESPECIAL PARA MMD: Reducir threshold para TikTok/Instagram
            # (En TikTok/Instagram es menos probable que sean verdaderos creadores MMD)
            mmd_threshold = 0.3  # Threshold base
            if primary_platform in ['tiktok', 'instagram']:
                mmd_threshold = 0.5  # Más tolerante con "mmd" en TikTok/Instagram
            
            # Determinar si es cosplayer o creador MMD
            if mmd_ratio > mmd_threshold:
                mmd_creators_filtered.append({
                    'creator': creator,
                    'mmd_ratio': mmd_ratio,
                    'cosplayer_ratio': cosplayer_ratio,
                    'videos': total_videos,
                    'primary_platform': primary_platform,
                    'reason': f'Alto contenido MMD ({mmd_ratio:.1%}) - No es cosplayer'
                })
                continue
            
            # 🆕 NUEVOS THRESHOLDS DIFERENCIADOS POR PLATAFORMA
            cosplayer_threshold = 0.2  # Threshold base (20%)
            if primary_platform == 'tiktok':
                cosplayer_threshold = 0.1  # 🔥 Solo 10% para TikTok (más sensible)
            elif primary_platform == 'instagram':
                cosplayer_threshold = 0.15  # 🔥 Solo 15% para Instagram
            elif primary_platform == 'youtube':
                cosplayer_threshold = 0.25  # 25% para YouTube (más estricto)
            
            # Usar el ratio ponderado para la decisión final
            effective_ratio = max(cosplayer_ratio, weighted_cosplayer_ratio)
            
            if effective_ratio >= cosplayer_threshold:
                # Generar nombre de personaje basado en el creador
                persona_name = self._generate_persona_name(creator)
                
                # 🆕 CALCULAR CONFIANZA CON BOOST POR PLATAFORMA
                base_confidence = min(0.85, 0.5 + effective_ratio * 0.35)
                
                # Aplicar boost por plataforma
                platform_boost = platform_confidence_boost.get(primary_platform, 0.0)
                confidence = min(0.98, base_confidence + platform_boost)
                
                # 🆕 CATEGORIZACIÓN AJUSTADA CON PLATAFORMA
                if primary_platform in ['tiktok', 'instagram']:
                    # Para TikTok/Instagram, ser más agresivo en la categorización
                    if effective_ratio >= 0.3 or cosplayer_indicators >= 2:
                        suggestion_type = 'high_confidence'
                    elif effective_ratio >= 0.15 or cosplayer_indicators >= 1:
                        suggestion_type = 'medium_confidence'
                    else:
                        suggestion_type = 'low_confidence'
                else:
                    # Para YouTube y otras, usar thresholds más conservadores
                    if effective_ratio >= 0.5 and cosplayer_indicators >= 3:
                        suggestion_type = 'high_confidence'
                    elif effective_ratio >= 0.3 and cosplayer_indicators >= 2:
                        suggestion_type = 'medium_confidence'
                    else:
                        suggestion_type = 'low_confidence'
                
                suggestion = {
                    'creator': creator,
                    'persona_name': persona_name,
                    'confidence': confidence,
                    'videos': total_videos,
                    'cosplayer_indicators': cosplayer_indicators,
                    'cosplayer_ratio': cosplayer_ratio,
                    'weighted_ratio': weighted_cosplayer_ratio,  # 🆕 Nuevo campo
                    'effective_ratio': effective_ratio,  # 🆕 Ratio usado para decisión
                    'primary_platform': primary_platform,  # 🆕 Plataforma principal
                    'platform_boost': platform_boost,  # 🆕 Boost aplicado
                    'platforms': list(stats['platforms']),
                    'suggestion_type': suggestion_type,
                    'sample_titles': stats['video_titles'][:3],  # Primeros 3 títulos como muestra
                    'youtube_hashtag_bonus': stats.get('youtube_hashtag_bonus', 0)  # 🆕 Bonus de hashtags de YouTube
                }
                cosplayer_suggestions.append(suggestion)
        
        # Mostrar sugerencias categorizadas
        high_conf = [s for s in cosplayer_suggestions if s['suggestion_type'] == 'high_confidence']
        medium_conf = [s for s in cosplayer_suggestions if s['suggestion_type'] == 'medium_confidence']
        low_conf = [s for s in cosplayer_suggestions if s['suggestion_type'] == 'low_confidence']
        
        if high_conf:
            print(f"\n[COSPLAYERS - ALTA CONFIANZA] {len(high_conf)} sugerencias:")
            print("-" * 60)
            for suggestion in sorted(high_conf, key=lambda x: x['confidence'], reverse=True):
                platform_indicator = "[PRIORIDAD ALTA]" if suggestion['primary_platform'] in ['tiktok', 'instagram'] else "[NORMAL]"
                # Filtrar caracteres no ASCII para evitar errores de codificación en Windows
                safe_creator = ''.join(c if ord(c) < 128 else '?' for c in suggestion['creator'])
                safe_persona = ''.join(c if ord(c) < 128 else '?' for c in suggestion['persona_name'])
                
                print(f"[COSPLAYER] {safe_creator} -> {safe_persona} {platform_indicator}")
                print(f"   Confianza: {suggestion['confidence']:.1%} (base: {suggestion['confidence'] - suggestion['platform_boost']:.1%} + boost: +{suggestion['platform_boost']:.1%})")
                print(f"   Indicadores cosplay: {suggestion['cosplayer_indicators']} en {suggestion['videos']} videos")
                print(f"   Ratio efectivo: {suggestion['effective_ratio']:.1%} (normal: {suggestion['cosplayer_ratio']:.1%}, ponderado: {suggestion['weighted_ratio']:.1%})")
                print(f"   Plataforma principal: {suggestion['primary_platform'].upper()} ({', '.join(suggestion['platforms'])})")
                
                # 🆕 Mostrar bonus de hashtags de YouTube si existe
                if suggestion['youtube_hashtag_bonus'] > 0:
                    print(f"   *** BONUS YOUTUBE: +{suggestion['youtube_hashtag_bonus']} puntos por hashtags (#cosplay, #shorts, etc.)")
                
                # Filtrar títulos de ejemplo
                safe_titles = []
                for title in suggestion['sample_titles']:
                    safe_title = ''.join(c if ord(c) < 128 else '?' for c in title)
                    safe_titles.append(safe_title)
                
                print(f"   Ejemplos: {', '.join(safe_titles)}")
                print(f"   Comando: python maintenance.py add-tiktoker --creator \"{suggestion['creator']}\" --persona \"{suggestion['persona_name']}\" --confidence {suggestion['confidence']:.2f}")
                print()
        
        if medium_conf:
            print(f"\n[COSPLAYERS - CONFIANZA MEDIA] {len(medium_conf)} sugerencias:")
            print("-" * 60)
            for suggestion in sorted(medium_conf, key=lambda x: x['confidence'], reverse=True):
                platform_indicator = "[PRIORIDAD ALTA]" if suggestion['primary_platform'] in ['tiktok', 'instagram'] else "[NORMAL]"
                safe_creator = ''.join(c if ord(c) < 128 else '?' for c in suggestion['creator'])
                safe_persona = ''.join(c if ord(c) < 128 else '?' for c in suggestion['persona_name'])
                
                print(f"[POSIBLE COSPLAYER] {safe_creator} -> {safe_persona} {platform_indicator}")
                print(f"   Confianza: {suggestion['confidence']:.1%} (base: {suggestion['confidence'] - suggestion['platform_boost']:.1%} + boost: +{suggestion['platform_boost']:.1%})")
                print(f"   Indicadores cosplay: {suggestion['cosplayer_indicators']} en {suggestion['videos']} videos")
                print(f"   Plataforma principal: {suggestion['primary_platform'].upper()}")
                
                # 🆕 Mostrar bonus de hashtags de YouTube si existe
                if suggestion['youtube_hashtag_bonus'] > 0:
                    print(f"   *** BONUS YOUTUBE: +{suggestion['youtube_hashtag_bonus']} puntos por hashtags (#cosplay, #shorts, etc.)")
                
                safe_titles = []
                for title in suggestion['sample_titles']:
                    safe_title = ''.join(c if ord(c) < 128 else '?' for c in title)
                    safe_titles.append(safe_title)
                
                print(f"   Ejemplos: {', '.join(safe_titles)}")
                print(f"   Comando (revisar manualmente): python maintenance.py add-tiktoker --creator \"{suggestion['creator']}\" --persona \"{suggestion['persona_name']}\" --confidence {suggestion['confidence']:.2f}")
                print()
        
        if low_conf:
            print(f"\n[COSPLAYERS - REVISION MANUAL] {len(low_conf)} sugerencias:")
            print("-" * 60)
            for suggestion in sorted(low_conf, key=lambda x: x['confidence'], reverse=True):
                platform_indicator = "[PRIORIDAD ALTA]" if suggestion['primary_platform'] in ['tiktok', 'instagram'] else "[NORMAL]"
                safe_creator = ''.join(c if ord(c) < 128 else '?' for c in suggestion['creator'])
                safe_persona = ''.join(c if ord(c) < 128 else '?' for c in suggestion['persona_name'])
                
                print(f"[REVISAR] {safe_creator} -> {safe_persona} {platform_indicator}")
                print(f"   Indicadores limitados: {suggestion['cosplayer_indicators']} en {suggestion['videos']} videos ({suggestion['effective_ratio']:.1%})")
                print(f"   Plataforma principal: {suggestion['primary_platform'].upper()}")
                
                # 🆕 Mostrar bonus de hashtags de YouTube si existe
                if suggestion['youtube_hashtag_bonus'] > 0:
                    print(f"   *** BONUS YOUTUBE: +{suggestion['youtube_hashtag_bonus']} puntos por hashtags (#cosplay, #shorts, etc.)")
                
                print(f"   Requiere revision manual de contenido")
                print()
        
        # Mostrar creadores MMD filtrados
        if mmd_creators_filtered:
            print(f"\n[CREADORES MMD - FILTRADOS] {len(mmd_creators_filtered)} creadores:")
            print("-" * 60)
            for filtered in sorted(mmd_creators_filtered, key=lambda x: x['mmd_ratio'], reverse=True):
                # Filtrar caracteres no ASCII para evitar errores de codificación en Windows
                safe_creator = ''.join(c if ord(c) < 128 else '?' for c in filtered['creator'])
                safe_reason = ''.join(c if ord(c) < 128 else '?' for c in filtered['reason'])
                
                print(f"[MMD] {safe_creator} - {safe_reason}")
                print(f"   MMD ratio: {filtered['mmd_ratio']:.1%}, Cosplay ratio: {filtered['cosplayer_ratio']:.1%}")
                print(f"   Plataforma: {filtered.get('primary_platform', 'unknown').upper()}")
                print()
        
        # Resumen final
        total_analyzed = len([c for c, s in creator_stats.items() if s['total_videos'] >= 2])
        total_cosplayer_suggestions = len(cosplayer_suggestions)
        total_filtered = len(mmd_creators_filtered)
        
        # 🆕 ESTADÍSTICAS POR PLATAFORMA
        tiktok_suggestions = len([s for s in cosplayer_suggestions if s['primary_platform'] == 'tiktok'])
        instagram_suggestions = len([s for s in cosplayer_suggestions if s['primary_platform'] == 'instagram'])
        youtube_suggestions = len([s for s in cosplayer_suggestions if s['primary_platform'] == 'youtube'])
        other_suggestions = len([s for s in cosplayer_suggestions if s['primary_platform'] not in ['tiktok', 'instagram', 'youtube']])
        
        print(f"\nRESUMEN DEL ANALISIS:")
        print(f"   Creadores analizados: {total_analyzed}")
        print(f"   Cosplayers detectados: {total_cosplayer_suggestions}")
        print(f"   - Alta confianza: {len(high_conf)} (aplicar automaticamente)")
        print(f"   - Confianza media: {len(medium_conf)} (revisar manualmente)")
        print(f"   - Revision manual: {len(low_conf)} (analizar contenido)")
        print(f"   Creadores MMD filtrados: {total_filtered}")
        
        print(f"\n*** DISTRIBUCION POR PLATAFORMA:")
        print(f"   [ALTA PRIORIDAD] TikTok: {tiktok_suggestions} cosplayers (boost +25%)")
        print(f"   [ALTA PRIORIDAD] Instagram: {instagram_suggestions} cosplayers (boost +20%)")
        print(f"   [PRIORIDAD NORMAL] YouTube: {youtube_suggestions} cosplayers (sin boost)")
        print(f"   [PRIORIDAD MEDIA] Otras: {other_suggestions} cosplayers (boost +10%)")
        
        if high_conf:
            # Mostrar estadísticas de boost aplicado
            tiktok_high = len([s for s in high_conf if s['primary_platform'] == 'tiktok'])
            instagram_high = len([s for s in high_conf if s['primary_platform'] == 'instagram'])
            avg_boost_tiktok = sum([s['platform_boost'] for s in high_conf if s['primary_platform'] == 'tiktok']) / max(1, tiktok_high)
            avg_boost_instagram = sum([s['platform_boost'] for s in high_conf if s['primary_platform'] == 'instagram']) / max(1, instagram_high)
            
            print(f"\nRECOMENDACION:")
            print(f"   Aplica automaticamente las {len(high_conf)} sugerencias de alta confianza")
            if tiktok_high > 0:
                print(f"   [ALTA PRIORIDAD] {tiktok_high} de TikTok (boost promedio: +{avg_boost_tiktok:.1%})")
            if instagram_high > 0:
                print(f"   [ALTA PRIORIDAD] {instagram_high} de Instagram (boost promedio: +{avg_boost_instagram:.1%})")
            print(f"   Ejemplo: python maintenance.py add-tiktoker --creator \"{high_conf[0]['creator']}\" --persona \"{high_conf[0]['persona_name']}\"")
        
        print(f"\nNOTA:")
        print(f"   - *** SISTEMA MEJORADO: TikTok/Instagram tienen +25%/+20% boost de confianza")
        print(f"   - *** Thresholds ajustados: TikTok 10%, Instagram 15%, YouTube 25%")
        print(f"   - *** NUEVO: YouTube hashtags (#cosplay, #shorts) dan +2 puntos extra por hashtag")
        print(f"   - Los hashtags son mas indicativos de personas reales vs creadores MMD en YouTube")
        print(f"   - Este analisis se enfoca en detectar COSPLAYERS/PERFORMERS reales")
        print(f"   - Los creadores de MMD son filtrados automaticamente")
        print(f"   - El objetivo es agregar personas como personajes de si mismos")
        
        return {
            'cosplayer_suggestions': cosplayer_suggestions,
            'mmd_creators_filtered': mmd_creators_filtered,
            'total_analyzed': total_analyzed
        }
    
    def configure_thumbnail_mode(self, mode=None):
        """🎯 Configurar modo de thumbnail para mejorar calidad/rendimiento"""
        print("🎯 CONFIGURADOR DE MODO THUMBNAIL")
        print("=" * 50)
        
        # Mostrar configuración actual
        current_mode = getattr(config, 'THUMBNAIL_MODE', 'no configurado')
        print(f"Modo actual: {current_mode}")
        print(f"Tamaño actual: {config.THUMBNAIL_SIZE}")
        print(f"Calidad desde .env: {thumbnail_generator.quality}")
        print()
        
        # Mostrar opciones disponibles
        modes = {
            'ultra_fast': '⚡ Ultra Rápido - Velocidad máxima, calidad básica',
            'balanced': '⚖️ Balanceado - Buena calidad + buen rendimiento (RECOMENDADO)',
            'quality': '🎨 Calidad - Mejor imagen, más tiempo de procesamiento',
            'gpu': '🎮 GPU - Máxima calidad con aceleración hardware',
            'auto': '🧠 Automático - Detecta el mejor modo según tu hardware'
        }
        
        if not mode:
            print("Modos disponibles:")
            for key, desc in modes.items():
                print(f"  {key}: {desc}")
            print()
            
            mode = input("Selecciona un modo [balanced]: ").strip().lower()
            if not mode:
                mode = 'balanced'
        
        if mode not in modes:
            print(f"❌ Modo inválido: {mode}")
            return
        
        print(f"\n🔧 Configurando modo: {mode}")
        print("-" * 30)
        
        # Probar configuración
        from src.thumbnail_generator import ThumbnailGenerator
        test_generator = ThumbnailGenerator()
        
        if mode == 'auto':
            test_generator.auto_configure_best_mode()
        else:
            test_generator.configure_thumbnail_mode(mode)
        
        # Mostrar resultados
        print("✅ Configuración aplicada:")
        print(f"   Modo rápido: {test_generator.fast_mode}")
        print(f"   Mejoras de imagen: {test_generator.enable_image_enhancement}")
        print(f"   Calidad JPEG: {test_generator.quality}")
        print(f"   GPU habilitada: {hasattr(test_generator, '_enable_gpu_acceleration') and test_generator._enable_gpu_acceleration}")
        
        # Detectar GPU si está en modo GPU
        if hasattr(test_generator, '_gpu_decoder'):
            gpu_info = test_generator._gpu_decoder or 'No detectada'
            print(f"   GPU detectada: {gpu_info}")
        
        print()
        print("💡 Para hacer este cambio permanente:")
        print(f'   Agrega en tu .env: THUMBNAIL_MODE="{mode}"')
        print()
        print("🔍 Para probar la calidad:")
        print("   python test_thumbnail_quality.py")
    
    def test_thumbnail_quality(self, video_path=None):
        """🧪 Probar calidad de thumbnails con diferentes modos"""
        print("🧪 PRUEBA DE CALIDAD DE THUMBNAILS")
        print("=" * 50)
        
        if video_path:
            test_video = Path(video_path)
        else:
            # Buscar video de prueba
            test_video = None
            test_locations = [
                Path("tests"),
                Path("data"),
                config.THUMBNAILS_PATH.parent
            ]
            
            for location in test_locations:
                if location.exists():
                    for ext in ['.mp4', '.avi', '.mkv', '.mov']:
                        videos = list(location.glob(f"*{ext}"))
                        if videos:
                            test_video = videos[0]
                            break
                if test_video:
                    break
        
        if not test_video or not test_video.exists():
            print("❌ No se encontró video de prueba.")
            print("   Uso: python maintenance.py test-thumbnail-quality --file /ruta/al/video.mp4")
            return
        
        print(f"🎬 Video de prueba: {test_video}")
        
        # Crear directorio de salida
        output_dir = Path("thumbnail_test_results")
        output_dir.mkdir(exist_ok=True)
        
        modes = ['ultra_fast', 'balanced', 'quality', 'gpu']
        mode_names = {
            'ultra_fast': '⚡ Ultra Rápido',
            'balanced': '⚖️ Balanceado', 
            'quality': '🎨 Calidad',
            'gpu': '🎮 GPU'
        }
        
        for mode in modes:
            print(f"\n{mode_names.get(mode, mode)}")
            from src.thumbnail_generator import ThumbnailGenerator
            generator = ThumbnailGenerator()
            generator.configure_thumbnail_mode(mode)
            generator.output_path = output_dir / mode
            generator.output_path.mkdir(exist_ok=True)
            
            start_time = time.time()
            result = generator.generate_thumbnail(test_video, force_regenerate=True)
            duration = time.time() - start_time
            
            if result:
                size = result.stat().st_size
                print(f"  ✅ {duration:.2f}s, {size/1024:.1f} KB")
            else:
                print(f"  ❌ Error")
        
        print(f"\n📁 Resultados guardados en: {output_dir.absolute()}")

def main():
    """Función principal con CLI"""
    parser = argparse.ArgumentParser(description='Tag-Flow V2 - Utilidades de Mantenimiento')
    parser.add_argument('action', choices=[
        'backup', 'clean-thumbnails', 'verify', 'regenerate-thumbnails', 
        'optimize-db', 'report', 'populate-db', 'clear-db', 'populate-thumbnails',
        'clear-thumbnails', 'show-stats', 'character-stats', 'add-character',
        'download-character-images', 'analyze-titles', 'update-creator-mappings',
        'clean-false-positives', 'add-tiktoker', 'list-platforms', 'optimization-stats',
        'configure-thumbnails', 'test-thumbnail-quality'
    ], help='Acción a realizar')
    
    # Argumentos generales
    parser.add_argument('--force', action='store_true', help='Forzar acción sin confirmación')
    parser.add_argument('--limit', type=int, help='Número máximo de elementos a procesar')
    
    # Argumentos específicos para poblado de BD
    parser.add_argument('--source', choices=['db', 'organized', 'all'], default='all',
                        help='Fuente de datos (db=bases datos externas, organized=carpetas organizadas, all=ambas)')
    parser.add_argument('--platform', 
                        help='Plataforma específica: youtube|tiktok|instagram (principales), other (adicionales), all-platforms (todas), o nombre específico como "iwara"')
    parser.add_argument('--file', type=str, 
                        help='Ruta específica de un video para importar (ej: "D:/videos/video.mp4")')
    
    # Argumentos específicos para gestión de personajes
    parser.add_argument('--character', type=str, help='Nombre del personaje')
    parser.add_argument('--game', type=str, help='Juego o serie del personaje')
    parser.add_argument('--aliases', nargs='*', help='Nombres alternativos del personaje')
    
    # Argumentos específicos para TikTokers como personajes
    parser.add_argument('--creator', type=str, help='Nombre del creador/TikToker')
    parser.add_argument('--persona', type=str, help='Nombre del personaje/persona (opcional)')
    parser.add_argument('--confidence', type=float, default=0.9, help='Nivel de confianza (0.0-1.0)')
    
    # Argumentos específicos para thumbnails
    parser.add_argument('--mode', type=str, choices=['ultra_fast', 'balanced', 'quality', 'gpu', 'auto'],
                        help='Modo de thumbnail para configurar')
    
    args = parser.parse_args()
    
    utils = MaintenanceUtils()
    
    if args.action == 'backup':
        utils.create_backup()
    elif args.action == 'clean-thumbnails':
        utils.clean_thumbnails(force=args.force)
    elif args.action == 'verify':
        utils.verify_integrity()
    elif args.action == 'regenerate-thumbnails':
        utils.regenerate_thumbnails(force=args.force)
    elif args.action == 'optimize-db':
        utils.optimize_database()
    elif args.action == 'report':
        utils.generate_report()
    elif args.action == 'populate-db':
        utils.populate_database(
            source=args.source, 
            platform=args.platform, 
            limit=args.limit, 
            force=args.force,
            file_path=args.file
        )
    elif args.action == 'clear-db':
        utils.clear_database(platform=args.platform, force=args.force)
    elif args.action == 'populate-thumbnails':
        utils.populate_thumbnails(
            platform=args.platform, 
            limit=args.limit, 
            force=args.force
        )
    elif args.action == 'clear-thumbnails':
        utils.clear_thumbnails(platform=args.platform, force=args.force)
    elif args.action == 'show-stats':
        utils.show_sources_stats()
    elif args.action == 'character-stats':
        utils.show_character_stats()
    elif args.action == 'add-character':
        if not args.character or not args.game:
            logger.error("Se requiere --character y --game para agregar personaje")
            return
        utils.add_custom_character(args.character, args.game, args.aliases)
    elif args.action == 'download-character-images':
        utils.download_character_images(args.character, args.game, args.limit)
    elif args.action == 'analyze-titles':
        utils.analyze_existing_titles(args.limit)
    elif args.action == 'update-creator-mappings':
        utils.update_creator_mappings(args.limit)
    elif args.action == 'clean-false-positives':
        utils.clean_false_positives(force=args.force)
    elif args.action == 'add-tiktoker':
        if not args.creator:
            logger.error("Se requiere --creator para agregar TikToker como personaje")
            return
        utils.add_tiktoker_persona(args.creator, args.persona, args.confidence)
    elif args.action == 'list-platforms':
        utils.list_available_platforms()
    elif args.action == 'optimization-stats':
        utils.show_optimization_stats()
    elif args.action == 'configure-thumbnails':
        utils.configure_thumbnail_mode(args.mode)
    elif args.action == 'test-thumbnail-quality':
        utils.test_thumbnail_quality(args.file)

if __name__ == '__main__':
    main()