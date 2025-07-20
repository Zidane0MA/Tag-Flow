#!/usr/bin/env python3
"""
🔧 Tag-Flow V2 - Maintenance System Dispatcher
Sistema de mantenimiento modular refactorizado
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# Agregar src al path
sys.path.append(str(Path(__file__).parent / 'src'))

# Los módulos se importarán dinámicamente para evitar logs innecesarios en --help

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def show_help():
    """Muestra ayuda personalizada sin inicializar el sistema"""
    help_text = """
🔧 Tag-Flow V2 - Sistema de Mantenimiento Modular

USO:
    python maintenance.py <COMANDO> [OPCIONES]

📦 OPERACIONES DE BACKUP:
    backup                   Crear backup completo del sistema
    restore                  Restaurar desde backup
    list-backups            Listar backups disponibles
    cleanup-backups         Limpiar backups antiguos

🔍 OPERACIONES DE INTEGRIDAD:
    verify                   Verificación completa del sistema
    verify-files            Verificar archivos de video únicamente
    integrity-report        Generar reporte de salud del sistema

🖼️ OPERACIONES DE THUMBNAILS:
    regenerate-thumbnails   Regenerar thumbnails faltantes/corruptos
    populate-thumbnails     Generar thumbnails masivamente
    clean-thumbnails        Eliminar thumbnails huérfanos
    thumbnail-stats         Estadísticas de thumbnails

🗃️ OPERACIONES DE BASE DE DATOS:
    populate-db             Importar videos desde fuentes externas
    optimize-db             Optimizar y defragmentar base de datos
    clear-db                Limpiar registros de base de datos
    db-stats                Estadísticas de base de datos

👤 OPERACIONES DE PERSONAJES:
    character-stats         Estadísticas del sistema de IA
    add-character           Añadir personaje personalizado
    clean-false-positives   Limpiar detecciones incorrectas
    update-creator-mappings Actualizar mapeos creador→personaje
    analyze-titles          Analizar patrones en títulos
    download-character-images Descargar imágenes de referencia
    character-detection-report Reporte de detección de personajes

🔧 OPCIONES COMUNES:
    --help, -h              Mostrar esta ayuda
    --force                 Forzar acción sin confirmación
    --limit N               Límite de elementos a procesar
    --verbose, -v           Información detallada
    --platform PLATAFORMA   youtube|tiktok|instagram|other|all-platforms

📚 EJEMPLOS RÁPIDOS:
    python maintenance.py character-stats
    python maintenance.py verify --fix-issues
    python maintenance.py backup --compress
    python maintenance.py populate-db --platform tiktok --limit 50
    python maintenance.py populate-thumbnails --platform youtube

📖 Para documentación completa: MAINTENANCE.md
    """
    print(help_text)


class MaintenanceDispatcher:
    """
    🔧 Dispatcher para operaciones de mantenimiento
    
    Actúa como punto de entrada unificado para todas las operaciones de mantenimiento,
    delegando a los módulos especializados según corresponda.
    """
    
    def __init__(self):
        # Inicializar módulos especializados
        self.backup_ops = BackupOperations()
        self.character_ops = CharacterOperations()
        self.integrity_ops = IntegrityOperations()
        self.thumbnail_ops = ThumbnailOperations()
        self.database_ops = DatabaseOperations()
    
    # Métodos de backup
    def create_backup(self, include_thumbnails: bool = True, 
                     thumbnail_limit: int = 100, compress: bool = True):
        """Crear backup completo del sistema"""
        logger.info("💾 Creando backup del sistema...")
        result = self.backup_ops.create_backup(include_thumbnails, thumbnail_limit, compress)
        
        if result['success']:
            logger.info(f"✅ Backup creado exitosamente: {result['backup_path']}")
            logger.info(f"   📁 Tamaño: {result['backup_size_mb']:.1f} MB")
            logger.info(f"   ⏱️ Duración: {TimeUtils.format_duration(result['duration'])}")
        else:
            logger.error(f"❌ Error creando backup: {result.get('error', 'Unknown error')}")
        
        return result
    
    def restore_backup(self, backup_path: str, components: Optional[List[str]] = None,
                      force: bool = False):
        """Restaurar desde backup"""
        logger.info(f"🔄 Restaurando desde backup: {backup_path}")
        result = self.backup_ops.restore_backup(backup_path, components, force)
        
        if result['success']:
            logger.info(f"✅ Restauración completada exitosamente")
            logger.info(f"   📋 Componentes restaurados: {result['components_restored']}")
        else:
            logger.error(f"❌ Error restaurando: {result.get('error', 'Unknown error')}")
        
        return result
    
    def list_backups(self, limit: Optional[int] = None):
        """Listar backups disponibles"""
        logger.info("📋 Listando backups disponibles...")
        result = self.backup_ops.list_backups(limit)
        
        if result['success']:
            backups = result['backups']
            logger.info(f"📊 {len(backups)} backups encontrados:")
            for backup in backups:
                logger.info(f"   📁 {backup['name']} ({backup['size_mb']:.1f} MB)")
        else:
            logger.error(f"❌ Error listando backups: {result.get('error', 'Unknown error')}")
        
        return result
    
    def cleanup_old_backups(self, keep_count: int = 5, max_age_days: int = 30):
        """Limpiar backups antiguos"""
        logger.info("🧹 Limpiando backups antiguos...")
        result = self.backup_ops.cleanup_old_backups(keep_count, max_age_days)
        
        if result['success']:
            logger.info(f"✅ Limpieza completada: {result['deleted_count']} backups eliminados")
        else:
            logger.error(f"❌ Error limpiando backups: {result.get('error', 'Unknown error')}")
        
        return result
    
    # Métodos de integridad
    def verify_integrity(self, fix_issues: bool = False):
        """Verificar integridad del sistema"""
        logger.info("🔍 Verificando integridad del sistema...")
        result = self.integrity_ops.verify_database_integrity(fix_issues)
        
        if result['success']:
            score = result['integrity_score']
            issues = result['total_issues']
            logger.info(f"✅ Verificación completada:")
            logger.info(f"   🎯 Puntuación de integridad: {score:.1f}/100")
            logger.info(f"   ⚠️ {issues} problemas encontrados")
            if result.get('issues_fixed', 0) > 0:
                logger.info(f"   ✅ {result['issues_fixed']} problemas corregidos")
        else:
            logger.error(f"❌ Error verificando integridad: {result.get('error', 'Unknown error')}")
        
        return result
    
    def verify_video_files(self, video_ids: Optional[List[int]] = None):
        """Verificar archivos de video"""
        logger.info("📹 Verificando archivos de video...")
        result = self.integrity_ops.verify_video_files(video_ids)
        
        if result['success']:
            verification = result['verification_results']
            logger.info(f"✅ Verificación completada:")
            logger.info(f"   📊 {verification['accessible_files']}/{verification['total_videos']} archivos accesibles")
            logger.info(f"   ❌ {verification['missing_files']} archivos faltantes")
        else:
            logger.error(f"❌ Error verificando archivos: {result.get('error', 'Unknown error')}")
        
        return result
    
    def generate_integrity_report(self, include_details: bool = False):
        """Generar reporte de integridad"""
        logger.info("📊 Generando reporte de integridad...")
        result = self.integrity_ops.generate_integrity_report(include_details)
        
        if result['success']:
            report = result['integrity_report']
            logger.info(f"✅ Reporte generado:")
            logger.info(f"   🎯 Puntuación general: {report['overall_score']:.1f}/100")
            logger.info(f"   📈 Estado: {report['overall_status']}")
            logger.info(f"   💡 {result['recommendations_count']} recomendaciones")
        else:
            logger.error(f"❌ Error generando reporte: {result.get('error', 'Unknown error')}")
        
        return result
    
    # Métodos de thumbnails
    def regenerate_thumbnails(self, force: bool = False):
        """Regenerar thumbnails"""
        logger.info("🖼️ Regenerando thumbnails...")
        result = self.thumbnail_ops.regenerate_thumbnails(force)
        
        if result['success']:
            logger.info(f"✅ Thumbnails regenerados exitosamente")
            logger.info(f"   📊 Exitosos: {result['successful']}, Fallidos: {result['failed']}")
            if result.get('duration'):
                logger.info(f"   ⏱️ Duración: {TimeUtils.format_duration(result['duration'])}")
        else:
            logger.error(f"❌ Error regenerando thumbnails: {result.get('error', 'Unknown error')}")
        
        return result
    
    def populate_thumbnails(self, platform: Optional[str] = None,
                          limit: Optional[int] = None, force: bool = False):
        """Poblar thumbnails"""
        logger.info("📊 Poblando thumbnails...")
        result = self.thumbnail_ops.populate_thumbnails(platform, limit, force)
        
        if result['success']:
            logger.info(f"✅ Thumbnails poblados exitosamente")
            logger.info(f"   📊 Exitosos: {result['successful']}, Fallidos: {result['failed']}")
        else:
            logger.error(f"❌ Error poblando thumbnails: {result.get('error', 'Unknown error')}")
        
        return result
    
    def clean_thumbnails(self, force: bool = False):
        """Limpiar thumbnails huérfanos"""
        logger.info("🧹 Limpiando thumbnails huérfanos...")
        
        # Si no es force, obtener estadísticas primero
        if not force:
            result = self.thumbnail_ops.clean_thumbnails(force=False)
            if result['success'] and result['orphaned_count'] > 0:
                logger.info(f"Encontrados {result['orphaned_count']} thumbnails huérfanos ({result['total_size_mb']:.1f} MB)")
                response = input("¿Eliminar thumbnails huérfanos? [y/N]: ")
                if response.lower() == 'y':
                    result = self.thumbnail_ops.clean_thumbnails(force=True)
                else:
                    logger.info("Operación cancelada")
                    return result
        else:
            result = self.thumbnail_ops.clean_thumbnails(force=True)
        
        if result['success']:
            logger.info(f"✅ {result['message']}")
            if result['deleted_count'] > 0:
                logger.info(f"   🗑️ Eliminados: {result['deleted_count']} thumbnails")
        else:
            logger.error(f"❌ Error limpiando thumbnails: {result.get('error', 'Unknown error')}")
        
        return result
    
    def get_thumbnail_stats(self):
        """Obtener estadísticas de thumbnails"""
        logger.info("📊 Obteniendo estadísticas de thumbnails...")
        result = self.thumbnail_ops.get_thumbnail_stats()
        
        if result['success']:
            stats = result['stats']
            logger.info(f"✅ Estadísticas de thumbnails:")
            logger.info(f"   📁 Total archivos: {stats['total_files']}")
            logger.info(f"   💾 Tamaño total: {format_bytes(stats['total_size'])}")
            logger.info(f"   📊 Videos con thumbnails: {stats['videos_with_thumbnails']}")
        else:
            logger.error(f"❌ Error obteniendo estadísticas: {result.get('error', 'Unknown error')}")
        
        return result
    
    # Métodos de base de datos
    def populate_database(self, source: str = 'all', platform: Optional[str] = None,
                         limit: Optional[int] = None, force: bool = False,
                         file_path: Optional[str] = None):
        """Poblar base de datos"""
        logger.info("🗃️ Poblando base de datos...")
        result = self.database_ops.populate_database(source, platform, limit, force, file_path)
        
        if result['success']:
            logger.info(f"✅ Base de datos poblada exitosamente")
            logger.info(f"   📊 Importados: {result['imported']}, Errores: {result['errors']}")
        else:
            logger.error(f"❌ Error poblando BD: {result.get('error', 'Unknown error')}")
        
        return result
    
    def optimize_database(self):
        """Optimizar base de datos"""
        logger.info("🔧 Optimizando base de datos...")
        result = self.database_ops.optimize_database()
        
        if result['success']:
            logger.info(f"✅ Base de datos optimizada exitosamente")
            if result.get('size_reduction_mb'):
                logger.info(f"   📉 Reducción de tamaño: {result['size_reduction_mb']:.1f} MB")
        else:
            logger.error(f"❌ Error optimizando BD: {result.get('error', 'Unknown error')}")
        
        return result
    
    def clear_database(self, platform: Optional[str] = None, force: bool = False):
        """Limpiar base de datos"""
        logger.info("🗑️ Limpiando base de datos...")
        result = self.database_ops.clear_database(platform, force)
        
        if result['success']:
            logger.info(f"✅ Base de datos limpiada exitosamente")
            logger.info(f"   🗑️ Eliminados: {result['deleted']} registros")
        else:
            logger.error(f"❌ Error limpiando BD: {result.get('error', 'Unknown error')}")
        
        return result
    
    def get_database_stats(self):
        """Obtener estadísticas de base de datos"""
        logger.info("📊 Obteniendo estadísticas de base de datos...")
        result = self.database_ops.get_database_stats()
        
        if result['success']:
            stats = result['stats']
            logger.info(f"✅ Estadísticas de base de datos:")
            logger.info(f"   📊 Total videos: {stats['total_videos']}")
            logger.info(f"   📁 Por plataforma: {stats['platform_distribution']}")
            logger.info(f"   💾 Tamaño BD: {format_bytes(stats['database_size'])}")
        else:
            logger.error(f"❌ Error obteniendo estadísticas: {result.get('error', 'Unknown error')}")
        
        return result
    
    # Métodos de personajes
    def show_character_stats(self):
        """Mostrar estadísticas de personajes"""
        logger.info("📊 Obteniendo estadísticas de personajes...")
        result = self.character_ops.show_character_stats()
        
        if result['success']:
            stats = result['basic_stats']
            logger.info(f"✅ Estadísticas de personajes:")
            logger.info(f"   👥 Total personajes: {format_number(stats['total_characters'])}")
            logger.info(f"   🎮 Total juegos: {format_number(stats['total_games'])}")
            logger.info(f"   🔧 Detector: {stats['detector_type']}")
            logger.info(f"   🗂️ Mapeos creadores: {format_number(stats['creator_mappings'])}")
            
            if 'optimized_stats' in result:
                opt_stats = result['optimized_stats']
                if opt_stats.get('cache_hit_rate'):
                    logger.info(f"   🎯 Cache hit rate: {opt_stats['cache_hit_rate']}")
        else:
            logger.error(f"❌ Error obteniendo estadísticas: {result.get('error', 'Unknown error')}")
        
        return result
    
    def add_custom_character(self, character_name: str, game: str, aliases: List[str] = None):
        """Agregar personaje personalizado"""
        logger.info(f"👤 Agregando personaje: {character_name} ({game})")
        result = self.character_ops.add_custom_character(character_name, game, aliases)
        
        if result['success']:
            logger.info(f"✅ Personaje agregado exitosamente")
            logger.info(f"   👤 Nombre: {result['character_name']}")
            logger.info(f"   🎮 Juego: {result['game']}")
            logger.info(f"   📝 Patrones: {len(result['patterns'])}")
        else:
            logger.error(f"❌ Error agregando personaje: {result.get('error', 'Unknown error')}")
        
        return result
    
    def clean_false_positives(self, force: bool = False):
        """Limpiar falsos positivos"""
        logger.info("🧹 Limpiando falsos positivos...")
        result = self.character_ops.clean_false_positives(force)
        
        if result['success']:
            logger.info(f"✅ Falsos positivos limpiados exitosamente")
            logger.info(f"   🗑️ Eliminados: {result['total_cleaned']} falsos positivos")
            logger.info(f"   📊 Videos procesados: {result['videos_processed']}")
        else:
            logger.error(f"❌ Error limpiando falsos positivos: {result.get('error', 'Unknown error')}")
        
        return result
    
    def update_creator_mappings(self, auto_detect: bool = True):
        """Actualizar mapeos de creadores"""
        logger.info("🔄 Actualizando mapeos de creadores...")
        result = self.character_ops.update_creator_mappings(auto_detect)
        
        if result['success']:
            logger.info(f"✅ Mapeos actualizados exitosamente")
            logger.info(f"   🔍 Creadores analizados: {result['analyzed_creators']}")
            logger.info(f"   📊 Mapeos sugeridos: {result['suggested_mappings']}")
            logger.info(f"   ✅ Mapeos actualizados: {result['updated_mappings']}")
        else:
            logger.error(f"❌ Error actualizando mapeos: {result.get('error', 'Unknown error')}")
        
        return result
    
    def analyze_titles(self, limit: Optional[int] = None):
        """Analizar títulos de videos"""
        logger.info("📋 Analizando títulos de videos...")
        result = self.character_ops.analyze_titles(limit)
        
        if result['success']:
            logger.info(f"✅ Análisis de títulos completado")
            logger.info(f"   📊 Videos analizados: {result['analyzed_videos']}")
            logger.info(f"   📝 Palabras únicas: {result['unique_words']}")
            logger.info(f"   👥 Personajes mencionados: {result['characters_mentioned']}")
        else:
            logger.error(f"❌ Error analizando títulos: {result.get('error', 'Unknown error')}")
        
        return result
    
    def download_character_images(self, character_name: Optional[str] = None,
                                 game: Optional[str] = None, limit: int = 10):
        """Descargar imágenes de personajes"""
        logger.info("🖼️ Descargando imágenes de personajes...")
        result = self.character_ops.download_character_images(character_name, game, limit)
        
        if result['success']:
            logger.info(f"✅ Imágenes descargadas exitosamente")
            logger.info(f"   📥 Total descargadas: {result['total_downloaded']}")
            logger.info(f"   👥 Personajes procesados: {result['characters_processed']}")
        else:
            logger.error(f"❌ Error descargando imágenes: {result.get('error', 'Unknown error')}")
        
        return result
    
    def get_character_detection_report(self, video_ids: Optional[List[int]] = None):
        """Generar reporte de detección de personajes"""
        logger.info("📊 Generando reporte de detección de personajes...")
        result = self.character_ops.get_character_detection_report(video_ids)
        
        if result['success']:
            summary = result['summary']
            logger.info(f"✅ Reporte generado exitosamente")
            logger.info(f"   📊 Total videos: {summary['total_videos']}")
            logger.info(f"   📈 Tasa de detección: {summary['detection_rate']:.1f}%")
            logger.info(f"   👥 Personajes únicos: {summary['unique_characters']}")
        else:
            logger.error(f"❌ Error generando reporte: {result.get('error', 'Unknown error')}")
        
        return result


def lazy_import_modules():
    """Importar módulos solo cuando se necesiten (evita logs en --help)"""
    global BackupOperations, CharacterOperations, IntegrityOperations
    global ThumbnailOperations, DatabaseOperations, format_bytes, format_number, TimeUtils
    
    from src.maintenance.backup_ops import BackupOperations
    from src.maintenance.character_ops import CharacterOperations
    from src.maintenance.integrity_ops import IntegrityOperations
    from src.maintenance.thumbnail_ops import ThumbnailOperations
    from src.maintenance.database_ops import DatabaseOperations
    from src.maintenance.utils import format_bytes, format_number, TimeUtils

def main():
    """Función principal con CLI"""
    # Verificar si solo se solicita ayuda (evitar inicialización innecesaria)
    if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help']:
        show_help()
        return 0
    
    # Si no hay argumentos, mostrar ayuda personalizada también
    if len(sys.argv) == 1:
        show_help()
        return 0
    
    parser = argparse.ArgumentParser(
        description='🔧 Tag-Flow V2 - Sistema de Mantenimiento Modular',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 Para documentación completa: MAINTENANCE.md

🔥 Ejemplos rápidos:
  python maintenance.py backup --compress
  python maintenance.py character-stats
  python maintenance.py verify --fix-issues
  python maintenance.py populate-thumbnails --platform youtube --limit 50
  python maintenance.py populate-db --source all --platform tiktok
        """
    )
    
    parser.add_argument('action', choices=[
        # Backup operations
        'backup', 'restore', 'list-backups', 'cleanup-backups',
        # Integrity operations
        'verify', 'verify-files', 'integrity-report',
        # Thumbnail operations
        'regenerate-thumbnails', 'populate-thumbnails', 'clean-thumbnails', 'thumbnail-stats',
        # Database operations
        'populate-db', 'optimize-db', 'clear-db', 'db-stats',
        # Character operations
        'character-stats', 'add-character', 'clean-false-positives', 
        'update-creator-mappings', 'analyze-titles', 'download-character-images',
        'character-detection-report'
    ], help='Acción a realizar')
    
    # Argumentos generales
    parser.add_argument('--force', action='store_true', help='Forzar acción sin confirmación')
    parser.add_argument('--limit', type=int, help='Número máximo de elementos a procesar')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada')
    
    # Argumentos específicos para backup
    parser.add_argument('--compress', action='store_true', help='Comprimir backup')
    parser.add_argument('--no-thumbnails', action='store_true', help='Excluir thumbnails del backup')
    parser.add_argument('--thumbnail-limit', type=int, default=100, help='Límite de thumbnails en backup')
    parser.add_argument('--backup-path', help='Ruta del backup para restaurar')
    parser.add_argument('--components', nargs='+', help='Componentes específicos a restaurar')
    
    # Argumentos específicos para integridad
    parser.add_argument('--fix-issues', action='store_true', help='Intentar corregir problemas encontrados')
    parser.add_argument('--include-details', action='store_true', help='Incluir detalles en reportes')
    parser.add_argument('--video-ids', nargs='+', type=int, help='IDs específicos de videos')
    
    # Argumentos específicos para base de datos
    parser.add_argument('--source', choices=['db', 'organized', 'all'], default='all',
                        help='Fuente de datos para populate-db')
    parser.add_argument('--platform', help='Plataforma específica')
    parser.add_argument('--file-path', help='Ruta específica de archivo')
    
    # Argumentos específicos para personajes
    parser.add_argument('--character', help='Nombre del personaje')
    parser.add_argument('--game', help='Juego o serie del personaje')
    parser.add_argument('--aliases', nargs='*', help='Alias del personaje')
    parser.add_argument('--no-auto-detect', action='store_true', help='Desactivar detección automática')
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Importar módulos ahora que sabemos que no es --help
    lazy_import_modules()
    
    # Inicializar dispatcher
    dispatcher = MaintenanceDispatcher()
    
    try:
        # Ejecutar acción
        if args.action == 'backup':
            dispatcher.create_backup(
                include_thumbnails=not args.no_thumbnails,
                thumbnail_limit=args.thumbnail_limit,
                compress=args.compress
            )
        elif args.action == 'restore':
            if not args.backup_path:
                logger.error("❌ Se requiere --backup-path para restaurar")
                return 1
            dispatcher.restore_backup(args.backup_path, args.components, args.force)
        elif args.action == 'list-backups':
            dispatcher.list_backups(args.limit)
        elif args.action == 'cleanup-backups':
            dispatcher.cleanup_old_backups()
        elif args.action == 'verify':
            dispatcher.verify_integrity(args.fix_issues)
        elif args.action == 'verify-files':
            dispatcher.verify_video_files(args.video_ids)
        elif args.action == 'integrity-report':
            dispatcher.generate_integrity_report(args.include_details)
        elif args.action == 'regenerate-thumbnails':
            dispatcher.regenerate_thumbnails(args.force)
        elif args.action == 'populate-thumbnails':
            dispatcher.populate_thumbnails(args.platform, args.limit, args.force)
        elif args.action == 'clean-thumbnails':
            dispatcher.clean_thumbnails(args.force)
        elif args.action == 'thumbnail-stats':
            dispatcher.get_thumbnail_stats()
        elif args.action == 'populate-db':
            dispatcher.populate_database(args.source, args.platform, args.limit, args.force, args.file_path)
        elif args.action == 'optimize-db':
            dispatcher.optimize_database()
        elif args.action == 'clear-db':
            dispatcher.clear_database(args.platform, args.force)
        elif args.action == 'db-stats':
            dispatcher.get_database_stats()
        elif args.action == 'character-stats':
            dispatcher.show_character_stats()
        elif args.action == 'add-character':
            if not args.character or not args.game:
                logger.error("❌ Se requiere --character y --game")
                return 1
            dispatcher.add_custom_character(args.character, args.game, args.aliases)
        elif args.action == 'clean-false-positives':
            dispatcher.clean_false_positives(args.force)
        elif args.action == 'update-creator-mappings':
            dispatcher.update_creator_mappings(not args.no_auto_detect)
        elif args.action == 'analyze-titles':
            dispatcher.analyze_titles(args.limit)
        elif args.action == 'download-character-images':
            dispatcher.download_character_images(args.character, args.game, args.limit or 10)
        elif args.action == 'character-detection-report':
            dispatcher.get_character_detection_report(args.video_ids)
        else:
            logger.error(f"❌ Acción no implementada: {args.action}")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n❌ Operación cancelada por el usuario")
        return 130
    except Exception as e:
        logger.error(f"❌ Error ejecutando operación: {e}")
        return 1


if __name__ == "__main__":
    exit(main())