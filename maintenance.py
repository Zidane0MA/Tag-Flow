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
        """Regenerar todos los thumbnails"""
        logger.info("Regenerando thumbnails...")
        
        from src.thumbnail_generator import thumbnail_generator
        
        videos = db.get_videos()
        videos_without_thumbs = [v for v in videos if not v.get('thumbnail_path') or not Path(v['thumbnail_path']).exists()]
        
        if not videos_without_thumbs:
            logger.info("✅ Todos los videos tienen thumbnails")
            return
        
        logger.info(f"Regenerando thumbnails para {len(videos_without_thumbs)} videos...")
        
        success = 0
        failed = 0
        
        for video in videos_without_thumbs:
            try:
                video_path = Path(video['file_path'])
                if not video_path.exists():
                    logger.warning(f"Video no existe: {video_path}")
                    failed += 1
                    continue
                
                thumbnail_path = thumbnail_generator.generate_thumbnail(video_path, force_regenerate=force)
                
                if thumbnail_path:
                    # Actualizar BD
                    db.update_video(video['id'], {'thumbnail_path': str(thumbnail_path)})
                    success += 1
                    logger.info(f"✓ {video_path.name}")
                else:
                    failed += 1
                    logger.warning(f"✗ {video_path.name}")
                    
            except Exception as e:
                failed += 1
                logger.error(f"Error con {video.get('file_name', 'unknown')}: {e}")
        
        logger.info(f"✅ Thumbnails regenerados: {success} exitosos, {failed} fallidos")
    
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
        Poblar la base de datos desde fuentes externas o un archivo específico
        
        Args:
            source: 'db', 'organized', 'all' - fuente de datos
            platform: 'youtube', 'tiktok', 'instagram' o None para todas
            limit: número máximo de videos a importar
            force: forzar reimportación de videos existentes
            file_path: 🆕 ruta específica de un video para importar
        """
        
        # 🆕 NUEVA FUNCIONALIDAD: Importar archivo específico
        if file_path:
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
            db_data = {
                'file_path': video_data['file_path'],
                'file_name': video_data['file_name'],
                'creator_name': video_data['creator_name'],
                'platform': video_data['platform'],
                'processing_status': 'pendiente'
            }
            
            # Agregar información adicional si está disponible
            if 'title' in video_data:
                # Solo mapear a description, que es el campo principal para títulos
                db_data['description'] = video_data['title']
            
            # Obtener tamaño del archivo y duración si es video
            file_path_obj = Path(video_data['file_path'])
            if file_path_obj.exists():
                db_data['file_size'] = file_path_obj.stat().st_size
                
                # Si es video, intentar obtener duración
                if video_data.get('content_type', 'video') == 'video':
                    try:
                        from src.video_processor import video_processor
                        metadata = video_processor.extract_metadata(file_path_obj)
                        if 'duration_seconds' in metadata:
                            db_data['duration_seconds'] = metadata['duration_seconds']
                    except Exception as e:
                        logger.warning(f"No se pudo obtener duración de {file_path_obj.name}: {e}")
            
            # Agregar o actualizar en la BD
            try:
                if existing and force:
                    # Actualizar registro existente
                    db.update_video(existing['id'], db_data)
                    logger.info(f"✅ Video actualizado: {video_data['file_name']}")
                    logger.info(f"   Plataforma: {video_data['platform']}")
                    logger.info(f"   Creador: {video_data['creator_name']}")
                    logger.info(f"   Fuente: {video_data['source']}")
                else:
                    # Agregar nuevo registro
                    db.add_video(db_data)
                    logger.info(f"✅ Video importado: {video_data['file_name']}")
                    logger.info(f"   Plataforma: {video_data['platform']}")
                    logger.info(f"   Creador: {video_data['creator_name']}")
                    logger.info(f"   Fuente: {video_data['source']}")
                
                return
                
            except Exception as e:
                logger.error(f"Error importando archivo específico: {e}")
                return
        
        # FUNCIONALIDAD EXISTENTE: Importar desde fuentes múltiples
        logger.info(f"Poblando base de datos desde {source} (plataforma: {platform or 'todas'})")
        
        if limit:
            logger.info(f"Límite establecido: {limit} videos")
        
        # Obtener videos de fuentes externas
        external_videos = external_sources.get_all_videos_from_source(source, platform, limit)
        
        if not external_videos:
            logger.info("No se encontraron videos para importar")
            return
        
        logger.info(f"Videos encontrados para importar: {len(external_videos)}")
        
        # Verificar duplicados si no se fuerza
        if not force:
            existing_paths = {video['file_path'] for video in db.get_videos()}
            new_videos = [v for v in external_videos if v['file_path'] not in existing_paths]
            skipped = len(external_videos) - len(new_videos)
            if skipped > 0:
                logger.info(f"Videos ya existentes omitidos: {skipped}")
            external_videos = new_videos
        
        if not external_videos:
            logger.info("Todos los videos ya están en la base de datos")
            return
        
        # Importar videos
        imported = 0
        errors = 0
        
        for video_data in external_videos:
            try:
                # Preparar datos para la BD
                db_data = {
                    'file_path': video_data['file_path'],
                    'file_name': video_data['file_name'],
                    'creator_name': video_data['creator_name'],
                    'platform': video_data['platform'],
                    'processing_status': 'pendiente'
                }
                
                # Agregar información adicional si está disponible
                if 'title' in video_data:
                    # Solo mapear a description, que es el campo principal para títulos
                    db_data['description'] = video_data['title']
                
                # Obtener tamaño del archivo y duración si es video
                file_path = Path(video_data['file_path'])
                if file_path.exists():
                    db_data['file_size'] = file_path.stat().st_size
                    
                    # Si es video, intentar obtener duración
                    if video_data.get('content_type', 'video') == 'video':
                        try:
                            from src.video_processor import video_processor
                            metadata = video_processor.extract_metadata(file_path)
                            if 'duration_seconds' in metadata:
                                db_data['duration_seconds'] = metadata['duration_seconds']
                        except Exception as e:
                            logger.warning(f"No se pudo obtener duración de {file_path.name}: {e}")
                
                # Agregar a la BD
                if force:
                    # Si forzamos, verificar si existe y actualizar o insertar
                    existing = db.get_video_by_path(video_data['file_path'])
                    if existing:
                        db.update_video(existing['id'], db_data)
                        logger.debug(f"Actualizado: {video_data['file_name']}")
                    else:
                        db.add_video(db_data)
                        logger.debug(f"Agregado: {video_data['file_name']}")
                else:
                    db.add_video(db_data)
                    logger.debug(f"Importado: {video_data['file_name']}")
                
                imported += 1
                
            except Exception as e:
                logger.error(f"Error importando {video_data['file_name']}: {e}")
                errors += 1
        
        logger.info(f"✅ Importación completada: {imported} exitosos, {errors} errores")
        
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
        Generar thumbnails para videos en la base de datos
        
        Args:
            platform: plataforma específica o None para todas
            limit: número máximo de thumbnails a generar
            force: regenerar thumbnails existentes
        """
        logger.info("Generando thumbnails para videos en la base de datos...")
        
        # Obtener videos de la BD
        filters = {'platform': platform} if platform else {}
        videos = db.get_videos(filters, limit=limit)
        
        if not videos:
            logger.info("No hay videos en la base de datos")
            return
        
        # Filtrar videos que necesitan thumbnails
        videos_needing_thumbs = []
        for video in videos:
            file_path = Path(video['file_path'])
            
            # Verificar que el archivo existe
            if not file_path.exists():
                logger.warning(f"Archivo no existe: {file_path}")
                continue
            
            # Verificar que es un video (no imagen)
            video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
            if file_path.suffix.lower() not in video_extensions:
                continue
            
            # Verificar si necesita thumbnail
            needs_thumb = force or not video.get('thumbnail_path') or not Path(video['thumbnail_path']).exists()
            
            if needs_thumb:
                videos_needing_thumbs.append(video)
        
        if not videos_needing_thumbs:
            logger.info("✅ Todos los videos ya tienen thumbnails")
            return
        
        logger.info(f"Generando thumbnails para {len(videos_needing_thumbs)} videos...")
        
        success = 0
        failed = 0
        
        for video in videos_needing_thumbs:
            try:
                video_path = Path(video['file_path'])
                thumbnail_path = thumbnail_generator.generate_thumbnail(video_path, force_regenerate=force)
                
                if thumbnail_path:
                    # Actualizar BD con la ruta del thumbnail
                    db.update_video(video['id'], {'thumbnail_path': str(thumbnail_path)})
                    success += 1
                    logger.info(f"✓ {video_path.name}")
                else:
                    failed += 1
                    logger.warning(f"✗ {video_path.name}")
                    
            except Exception as e:
                failed += 1
                logger.error(f"Error generando thumbnail para {video.get('file_name', 'unknown')}: {e}")
        
        logger.info(f"✅ Thumbnails generados: {success} exitosos, {failed} fallidos")
        
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
    
    def update_creator_mappings(self, limit: int = None):
        """Analizar creadores y sugerir mapeos automáticos con estructura jerárquica"""
        logger.info("Analizando creadores para mapeos automáticos...")
        
        # Obtener todos los videos con personajes detectados
        videos = db.get_videos(limit=limit)
        creator_stats = {}
        
        # Analizar patrones de detección por creador
        for video in videos:
            creator = video.get('creator_name', '')
            if not creator:
                continue
            
            if creator not in creator_stats:
                creator_stats[creator] = {
                    'total_videos': 0,
                    'characters_detected': {},  # Cambio: usar dict para contar frecuencia
                    'platforms': set(),
                    'recent_videos': []
                }
            
            creator_stats[creator]['total_videos'] += 1
            creator_stats[creator]['platforms'].add(video.get('platform', 'unknown'))
            
            # Guardar info de videos recientes para análisis
            creator_stats[creator]['recent_videos'].append({
                'title': video.get('title', ''),
                'filename': video.get('file_name', ''),
                'characters': video.get('detected_characters', [])
            })
            
            # Contar frecuencia de personajes detectados
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
        
        # Analizar patrones y generar sugerencias inteligentes
        high_confidence_suggestions = []
        medium_confidence_suggestions = []
        low_confidence_suggestions = []
        
        print("\nANALISIS AVANZADO DE CREADORES")
        print("=" * 50)
        
        for creator, stats in creator_stats.items():
            if stats['total_videos'] < 2:  # Mínimo 2 videos para análisis
                continue
            
            # Verificar si ya tiene mapeo automático
            existing_mapping = character_intelligence.analyze_creator_name(creator)
            if existing_mapping and existing_mapping.get('source') in ['creator_mapping', 'tiktoker_persona']:
                continue  # Ya tiene mapeo, saltear
            
            chars_detected = stats['characters_detected']
            total_videos = stats['total_videos']
            
            # Análisis de consistencia
            if chars_detected:
                # Encontrar el personaje más frecuente
                most_frequent_char = max(chars_detected.items(), key=lambda x: x[1])
                char_name, char_frequency = most_frequent_char
                
                # Calcular ratio de consistencia
                consistency_ratio = char_frequency / total_videos
                
                # Categorizar sugerencias por confianza
                if consistency_ratio >= 0.8 and char_frequency >= 3:
                    # Alta confianza: 80%+ de consistencia, mínimo 3 videos
                    suggestion = {
                        'creator': creator,
                        'character': char_name,
                        'confidence': min(0.95, 0.7 + consistency_ratio * 0.3),
                        'videos': total_videos,
                        'frequency': char_frequency,
                        'ratio': consistency_ratio,
                        'platforms': list(stats['platforms']),
                        'suggestion_type': 'high_confidence'
                    }
                    high_confidence_suggestions.append(suggestion)
                    
                elif consistency_ratio >= 0.6 and char_frequency >= 2:
                    # Confianza media: 60%+ de consistencia, mínimo 2 videos
                    suggestion = {
                        'creator': creator,
                        'character': char_name,
                        'confidence': min(0.8, 0.5 + consistency_ratio * 0.3),
                        'videos': total_videos,
                        'frequency': char_frequency,
                        'ratio': consistency_ratio,
                        'platforms': list(stats['platforms']),
                        'suggestion_type': 'medium_confidence'
                    }
                    medium_confidence_suggestions.append(suggestion)
                    
                elif consistency_ratio >= 0.4:
                    # Baja confianza: 40%+ de consistencia para revisión manual
                    suggestion = {
                        'creator': creator,
                        'character': char_name,
                        'confidence': min(0.6, 0.3 + consistency_ratio * 0.3),
                        'videos': total_videos,
                        'frequency': char_frequency,
                        'ratio': consistency_ratio,
                        'platforms': list(stats['platforms']),
                        'suggestion_type': 'low_confidence',
                        'other_characters': {k: v for k, v in chars_detected.items() if k != char_name}
                    }
                    low_confidence_suggestions.append(suggestion)
        
        # Mostrar sugerencias por categoría
        if high_confidence_suggestions:
            print(f"\n[ALTA CONFIANZA] {len(high_confidence_suggestions)} sugerencias:")
            print("-" * 60)
            for suggestion in sorted(high_confidence_suggestions, key=lambda x: x['confidence'], reverse=True):
                print(f"[OK] {suggestion['creator']} -> {suggestion['character']}")
                print(f"   Confianza: {suggestion['confidence']:.1%}")
                print(f"   Consistencia: {suggestion['frequency']}/{suggestion['videos']} videos ({suggestion['ratio']:.1%})")
                print(f"   Plataformas: {', '.join(suggestion['platforms'])}")
                print(f"   Comando: python maintenance.py add-tiktoker --creator \"{suggestion['creator']}\" --persona \"{suggestion['character']}\" --confidence {suggestion['confidence']:.2f}")
                print()
        
        if medium_confidence_suggestions:
            print(f"\n[CONFIANZA MEDIA] {len(medium_confidence_suggestions)} sugerencias:")
            print("-" * 60)
            for suggestion in sorted(medium_confidence_suggestions, key=lambda x: x['confidence'], reverse=True):
                print(f"[?] {suggestion['creator']} -> {suggestion['character']}")
                print(f"   Confianza: {suggestion['confidence']:.1%}")
                print(f"   Consistencia: {suggestion['frequency']}/{suggestion['videos']} videos ({suggestion['ratio']:.1%})")
                print(f"   Comando (revisar manualmente): python maintenance.py add-tiktoker --creator \"{suggestion['creator']}\" --persona \"{suggestion['character']}\" --confidence {suggestion['confidence']:.2f}")
                print()
        
        if low_confidence_suggestions:
            print(f"\n[REVISION MANUAL] {len(low_confidence_suggestions)} sugerencias:")
            print("-" * 60)
            for suggestion in sorted(low_confidence_suggestions, key=lambda x: x['confidence'], reverse=True):
                print(f"[!] {suggestion['creator']} -> {suggestion['character']} (pero tambien: {list(suggestion['other_characters'].keys())})")
                print(f"   Consistencia baja: {suggestion['frequency']}/{suggestion['videos']} videos ({suggestion['ratio']:.1%})")
                print(f"   Requiere revision manual de videos")
                print()
        
        # Resumen y recomendaciones
        total_suggestions = len(high_confidence_suggestions) + len(medium_confidence_suggestions) + len(low_confidence_suggestions)
        
        print(f"\nRESUMEN DEL ANALISIS:")
        print(f"   Creadores analizados: {len([c for c, s in creator_stats.items() if s['total_videos'] >= 2])}")
        print(f"   Total sugerencias: {total_suggestions}")
        print(f"   Alta confianza: {len(high_confidence_suggestions)} (aplicar automaticamente)")
        print(f"   Confianza media: {len(medium_confidence_suggestions)} (revisar antes de aplicar)")
        print(f"   Revision manual: {len(low_confidence_suggestions)} (analizar videos individuales)")
        
        if high_confidence_suggestions:
            print(f"\nRECOMENDACION:")
            print(f"   Puedes aplicar automaticamente las {len(high_confidence_suggestions)} sugerencias de alta confianza")
            print(f"   Ejemplo: python maintenance.py add-tiktoker --creator \"{high_confidence_suggestions[0]['creator']}\" --persona \"{high_confidence_suggestions[0]['character']}\"")
        
        print(f"\nPara aplicar mapeos, usa:")
        print(f"   python maintenance.py add-tiktoker --creator \"NOMBRE_CREADOR\" --persona \"NOMBRE_PERSONAJE\"")
        
        return {
            'high_confidence': high_confidence_suggestions,
            'medium_confidence': medium_confidence_suggestions,
            'low_confidence': low_confidence_suggestions,
            'total_analyzed': len([c for c, s in creator_stats.items() if s['total_videos'] >= 2])
        }

def main():
    """Función principal con CLI"""
    parser = argparse.ArgumentParser(description='Tag-Flow V2 - Utilidades de Mantenimiento')
    parser.add_argument('action', choices=[
        'backup', 'clean-thumbnails', 'verify', 'regenerate-thumbnails', 
        'optimize-db', 'report', 'populate-db', 'clear-db', 'populate-thumbnails',
        'clear-thumbnails', 'show-stats', 'character-stats', 'add-character',
        'download-character-images', 'analyze-titles', 'update-creator-mappings',
        'clean-false-positives', 'add-tiktoker', 'list-platforms'
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

if __name__ == '__main__':
    main()