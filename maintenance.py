"""
Tag-Flow V2 - Utilidades de Mantenimiento
Scripts para backup, limpieza y mantenimiento del sistema
"""

import sys
import argparse
import shutil
import json
from pathlib import Path
from datetime import datetime
import sqlite3
import logging

# Agregar src al path
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config
from src.database import db

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
    
    def generate_report(self):
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

def main():
    """Función principal con CLI"""
    parser = argparse.ArgumentParser(description='Tag-Flow V2 - Utilidades de Mantenimiento')
    parser.add_argument('action', choices=[
        'backup', 'clean-thumbnails', 'verify', 'regenerate-thumbnails', 
        'optimize-db', 'report'
    ], help='Acción a realizar')
    parser.add_argument('--force', action='store_true', help='Forzar acción sin confirmación')
    
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

if __name__ == '__main__':
    main()