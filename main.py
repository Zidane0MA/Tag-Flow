#!/usr/bin/env python3
"""
🎬 Tag-Flow V2 - Unified CLI System
Sistema unificado de procesamiento y mantenimiento
"""

import os
# Ocultar logs de TensorFlow y Keras antes de cualquier import relacionado
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Agregar src al path
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TagFlowCLI:
    """CLI unificado para Tag-Flow V2"""
    
    def __init__(self):
        self.config = config
        config.ensure_directories()
        
    def create_parser(self):
        """Crear parser de argumentos unificado"""
        parser = argparse.ArgumentParser(
            description='🎬 Tag-Flow V2 - Sistema Unificado de Gestión de Videos',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Ejemplos de uso:

📹 PROCESAMIENTO Y ANÁLISIS:
  python main.py process                                    # Procesar todos los videos nuevos
  python main.py process --limit 10                        # Procesar solo 10 videos
  python main.py process --platform youtube --limit 5      # Procesar 5 videos de YouTube
  python main.py process --platform tiktok --source db     # Procesar TikTok solo desde BD externa
  python main.py process --source organized --limit 20     # Procesar 20 videos de carpetas organizadas

🔄 REANÁLISIS:
  python main.py process --reanalyze-video 123             # Reanalizar video específico
  python main.py process --reanalyze-video 1,2,3           # Reanalizar múltiples videos
  python main.py process --reanalyze-video 123 --force     # Forzar reanálisis sobrescribiendo datos

🔧 MANTENIMIENTO:
  python main.py backup                     # Crear backup completo del sistema
  python main.py restore --backup-path ruta # Restaurar desde backup
  python main.py populate-db --source all   # Poblar desde fuentes externas
  python main.py optimize-db                # Optimizar base de datos
  python main.py clear-db --platform youtube # Limpiar base de datos
  python main.py verify                     # Verificar integridad del sistema
  python main.py integrity-report           # Reporte detallado de integridad

🖼️ THUMBNAILS:
  python main.py regenerate-thumbnails      # Regenerar thumbnails
  python main.py populate-thumbnails        # Generar thumbnails faltantes
  python main.py clean-thumbnails           # Limpiar thumbnails huérfanos

👤 PERSONAJES:
  python main.py add-character --character "Nahida" --game "Genshin Impact" --aliases "Kusanali" "Dendro Archon"
  python main.py clean-false-positives      # Limpiar falsos positivos
  python main.py update-creator-mappings    # Actualizar mapeos creador→personaje
  python main.py analyze-titles --limit 100 # Analizar patrones en títulos
  python main.py download-character-images  # Descargar imágenes de referencia

📊 ESTADÍSTICAS:
  python main.py show-stats                 # Mostrar estadísticas del sistema
  python main.py db-stats                   # Estadísticas de base de datos
  python main.py thumbnail-stats            # Estadísticas de thumbnails
  python main.py character-stats            # Estadísticas de personajes
  python main.py character-detection-report # Reporte de detección
  python main.py list-backups               # Listar backups disponibles
  python main.py cleanup-backups            # Limpiar backups antiguos
            """
        )
        
        # Comando principal
        subparsers = parser.add_subparsers(dest='command', help='Comando a ejecutar')
        
        # === SUBCOMANDO: PROCESS ===
        process_parser = subparsers.add_parser('process', help='Procesamiento y análisis de videos')
        
        # Opciones de análisis
        process_parser.add_argument('--limit', type=int, help='Límite de videos a procesar')
        process_parser.add_argument('--platform', 
                                  help='Filtrar por plataforma específica (youtube, tiktok, instagram, other, all-platforms) o usar autodetección')
        process_parser.add_argument('--source', choices=['db', 'organized', 'all'], default='all',
                                  help='Fuente de videos: db (bases externas), organized (carpetas), all (ambas)')
        
        # Opciones de reanálisis
        process_parser.add_argument('--reanalyze-video', type=str,
                                  help='ID de video(s) a reanalizar (separados por coma)')
        process_parser.add_argument('--force', action='store_true',
                                  help='Forzar análisis incluso de videos ya completados')
        
        # === SUBCOMANDOS: MANTENIMIENTO ===
        # Backup y restore
        backup_parser = subparsers.add_parser('backup', help='Crear backup completo del sistema')
        backup_parser.add_argument('--compress', action='store_true', help='Comprimir backup en ZIP')
        backup_parser.add_argument('--no-thumbnails', action='store_true', help='Excluir thumbnails del backup')
        backup_parser.add_argument('--thumbnail-limit', type=int, default=100, help='Límite de thumbnails en backup')
        
        restore_parser = subparsers.add_parser('restore', help='Restaurar desde backup')
        restore_parser.add_argument('--backup-path', required=True, help='Ruta del backup a restaurar')
        restore_parser.add_argument('--components', nargs='+', help='Componentes específicos a restaurar')
        restore_parser.add_argument('--force', action='store_true', help='Forzar restauración sin confirmación')
        
        subparsers.add_parser('list-backups', help='Listar backups disponibles')
        cleanup_parser = subparsers.add_parser('cleanup-backups', help='Limpiar backups antiguos')
        cleanup_parser.add_argument('--force', action='store_true', help='Eliminar todos los backups sin confirmación')
        
        # Base de datos
        populate_parser = subparsers.add_parser('populate-db', help='Poblar BD desde fuentes externas')
        populate_parser.add_argument('--source', choices=['db', 'organized', 'all'], 
                                   default='all', help='Fuente de datos: db (bases externas), organized (carpetas), all (ambas)')
        populate_parser.add_argument('--platform', help='Plataforma específica (youtube, tiktok, instagram, other, all-platforms)')
        populate_parser.add_argument('--limit', type=int, help='Límite de videos a importar')
        populate_parser.add_argument('--force', action='store_true', help='Forzar importación y sobrescribir videos existentes')
        
        subparsers.add_parser('optimize-db', help='Optimizar y defragmentar base de datos')
        
        clear_db_parser = subparsers.add_parser('clear-db', help='Limpiar base de datos')
        clear_db_parser.add_argument('--platform', help='Plataforma específica a limpiar (youtube, tiktok, instagram, other, all-platforms)')
        clear_db_parser.add_argument('--force', action='store_true', help='Forzar limpieza sin confirmación')
        
        subparsers.add_parser('db-stats', help='Estadísticas detalladas de base de datos')
        
        # Thumbnails
        thumb_parser = subparsers.add_parser('regenerate-thumbnails', help='Regenerar thumbnails')
        thumb_parser.add_argument('--force', action='store_true', help='Forzar regeneración')
        
        populate_thumbs_parser = subparsers.add_parser('populate-thumbnails', help='Generar thumbnails faltantes')
        populate_thumbs_parser.add_argument('--platform', help='Plataforma específica (youtube, tiktok, instagram, other, all-platforms)')
        populate_thumbs_parser.add_argument('--limit', type=int, help='Límite de thumbnails a generar')
        populate_thumbs_parser.add_argument('--force', action='store_true', help='Generar thumbnails incluso para videos que ya los tienen')
        
        clean_thumbs_parser = subparsers.add_parser('clean-thumbnails', help='Limpiar thumbnails huérfanos')
        clean_thumbs_parser.add_argument('--force', action='store_true', help='Ejecutar eliminación directamente sin confirmación')
        
        subparsers.add_parser('thumbnail-stats', help='Estadísticas de thumbnails')
        
        # Verificación e integridad
        verify_parser = subparsers.add_parser('verify', help='Verificación completa del sistema')
        verify_parser.add_argument('--fix-issues', action='store_true', help='Intentar corregir problemas automáticamente')
        
        verify_files_parser = subparsers.add_parser('verify-files', help='Verificar solo archivos de video')
        verify_files_parser.add_argument('--video-id', nargs='+', type=int, help='IDs específicos de videos a verificar')
        
        integrity_parser = subparsers.add_parser('integrity-report', help='Generar reporte detallado de integridad')
        integrity_parser.add_argument('--include-details', action='store_true', help='Incluir detalles completos en formato JSON')
        
        # Personajes
        add_char_parser = subparsers.add_parser('add-character', help='Agregar personaje personalizado')
        add_char_parser.add_argument('--character', required=True, help='Nombre del personaje (usar comillas si contiene espacios)')
        add_char_parser.add_argument('--game', required=True, help='Juego o serie del personaje (usar comillas si contiene espacios)')
        add_char_parser.add_argument('--aliases', nargs='*', default=[], help='Alias del personaje separados por espacios (usar comillas para alias con espacios)')
        
        clean_fp_parser = subparsers.add_parser('clean-false-positives', help='Limpiar falsos positivos de personajes')
        clean_fp_parser.add_argument('--force', action='store_true', help='Ejecutar limpieza sin confirmación')
        subparsers.add_parser('update-creator-mappings', help='Actualizar mapeos creador→personaje')
        
        analyze_titles_parser = subparsers.add_parser('analyze-titles', help='Analizar patrones en títulos')
        analyze_titles_parser.add_argument('--limit', type=int, help='Límite de títulos a analizar')
        
        download_images_parser = subparsers.add_parser('download-character-images', help='Descargar imágenes de referencia')
        download_images_parser.add_argument('--character', help='Personaje específico')
        download_images_parser.add_argument('--game', help='Juego específico')
        download_images_parser.add_argument('--limit', type=int, default=10, help='Límite de imágenes')
        
        char_report_parser = subparsers.add_parser('character-detection-report', help='Reporte de detección de personajes')
        char_report_parser.add_argument('--video-ids', nargs='+', type=int, help='IDs específicos de videos')
        
        # Estadísticas
        subparsers.add_parser('show-stats', help='Mostrar estadísticas del sistema')
        subparsers.add_parser('character-stats', help='Estadísticas de personajes')
        
        return parser
    
    def execute_process_command(self, args):
        """Ejecutar comando de procesamiento"""
        logger.info("🎬 Iniciando procesamiento de videos...")
        
        # 🚀 MIGRADO: Usar service factory para lazy loading
        from src.service_factory import get_video_processor, get_music_recognizer, get_face_recognizer
        
        video_processor = get_video_processor()
        music_recognizer = get_music_recognizer()
        face_recognizer = get_face_recognizer()
        
        # Reanálisis vs análisis normal
        if args.reanalyze_video:
            self._execute_reanalysis(args)
        else:
            self._execute_analysis(args)
    
    def _execute_analysis(self, args):
        """Ejecutar análisis de videos usando src/core/video_analyzer.py"""
        from src.core.video_analyzer import VideoAnalyzer
        
        analyzer = VideoAnalyzer()
        result = analyzer.run(
            limit=args.limit,
            platform=args.platform,
            source=args.source,
            force=args.force
        )
        
        # El VideoAnalyzer ya muestra el resultado final compacto
        pass
    
    def _execute_reanalysis(self, args):
        """Ejecutar reanálisis de videos específicos"""
        from src.core import ReanalysisEngine
        
        engine = ReanalysisEngine()
        
        # Ejecutar reanálisis
        result = engine.reanalyze_videos(args.reanalyze_video, force=args.force)
        
        if result['success']:
            logger.info("✅ Reanálisis completado exitosamente")
        else:
            logger.error("❌ Reanálisis completado con errores")
    
    def execute_populate_db(self, params):
        """Ejecutar población de base de datos"""
        logger.info("📥 Poblando base de datos desde fuentes externas...")
        
        # Importar operaciones de mantenimiento refactorizadas
        from src.maintenance.database_ops import DatabaseOperations
        
        db_ops = DatabaseOperations()
        
        # Usar la funcionalidad ya refactorizada
        result = db_ops.populate_database(
            source=params.get('source', 'all'),
            platform=params.get('platform'),
            limit=params.get('limit'),
            force=params.get('force', False)
        )
        
        if result['success']:
            # El reporte profesional ya se mostró, no necesitamos log adicional
            logger.debug(f"✅ Base de datos poblada exitosamente: {result.get('message', 'Completado')}")
        else:
            logger.error(f"❌ Error poblando base de datos: {result.get('error', 'Error desconocido')}")
    
    def execute_maintenance_command(self, args):
        """Ejecutar comandos de mantenimiento"""
        command = args.command
        
        # Importar operaciones según el comando
        if command == 'backup':
            from src.maintenance.backup_ops import BackupOperations
            ops = BackupOperations()
            result = ops.create_backup(
                include_thumbnails=not getattr(args, 'no_thumbnails', False),
                thumbnail_limit=getattr(args, 'thumbnail_limit', 100),
                compress=getattr(args, 'compress', True)
            )
            
        elif command == 'restore':
            from src.maintenance.backup_ops import BackupOperations
            ops = BackupOperations()
            result = ops.restore_backup(
                backup_path=args.backup_path,
                components=getattr(args, 'components', None),
                force=getattr(args, 'force', False)
            )
            
        elif command == 'list-backups':
            from src.maintenance.backup_ops import BackupOperations
            ops = BackupOperations()
            result = ops.list_backups()
            
        elif command == 'cleanup-backups':
            from src.maintenance.backup_ops import BackupOperations
            ops = BackupOperations()
            result = ops.cleanup_old_backups(force=getattr(args, 'force', False))
            
        elif command == 'populate-db':
            self.execute_populate_db({
                'source': args.source,
                'platform': getattr(args, 'platform', None),
                'limit': getattr(args, 'limit', None),
                'force': getattr(args, 'force', False)
            })
            return
            
        elif command == 'optimize-db':
            from src.maintenance.database_ops import DatabaseOperations
            ops = DatabaseOperations()
            result = ops.optimize_database()
            
        elif command == 'clear-db':
            from src.maintenance.database_ops import DatabaseOperations
            ops = DatabaseOperations()
            result = ops.clear_database(
                platform=getattr(args, 'platform', None),
                force=getattr(args, 'force', False)
            )
            
        elif command == 'db-stats':
            # 🚀 OPTIMIZADO: Usar operaciones ligeras sin dependencias pesadas
            from src.maintenance.stats_ops import StatsOperations
            ops = StatsOperations()
            result = ops.get_database_stats()
            
            # Mostrar estadísticas formateadas
            if result['success']:
                stats = result['stats']
                print("\n" + "="*60)
                print("📊 ESTADÍSTICAS DE BASE DE DATOS")
                print("="*60)
                print(f"Base de datos: {stats['database_file']}")
                print(f"Tamaño: {stats['database_size_mb']} MB")
                print(f"Total videos: {stats['total_records'].get('videos', 0)}")
                
                if 'platform_breakdown' in stats:
                    print(f"\n🌐 POR PLATAFORMA:")
                    for platform, count in stats['platform_breakdown'].items():
                        print(f"  {platform}: {count} videos")
                
                if 'new_structure' in stats:
                    ns = stats['new_structure']
                    print(f"\n🆕 NUEVA ESTRUCTURA:")
                    print(f"  Creadores: {ns.get('total_creators', 0)}")
                    print(f"  Suscripciones: {ns.get('total_subscriptions', 0)}")
                    print(f"  Videos con creator_id: {ns.get('videos_with_creator_id', 0)}")
                    print(f"  Videos con subscription_id: {ns.get('videos_with_subscription_id', 0)}")
                
                if 'external_sources' in stats:
                    ext = stats['external_sources']
                    print(f"\n🔗 FUENTES EXTERNAS:")
                    print(f"  Total videos disponibles: {ext.get('total_external_videos', 0)}")
                    print(f"  Fuentes encontradas: {ext.get('sources_found', 0)}")
                    
                    # Mostrar desglose detallado por plataforma de 4K Video Downloader
                    if ext.get('platform_breakdown') and '4k_video_downloader' in ext['platform_breakdown']:
                        print(f"\n  📺 4K Video Downloader - Por plataforma:")
                        platform_stats = ext['platform_breakdown']['4k_video_downloader']
                        total_4k = sum(platform_stats.values())
                        
                        for platform, count in sorted(platform_stats.items(), key=lambda x: x[1], reverse=True):
                            percentage = (count / total_4k * 100) if total_4k > 0 else 0
                            print(f"    {platform.capitalize()}: {count} videos ({percentage:.1f}%)")
                        print(f"    Total: {total_4k} videos")
                    
                    # Mostrar otros sources
                    if ext.get('available_sources'):
                        print(f"\n  🎬 Otras fuentes:")
                        for source, count in ext['available_sources'].items():
                            if 'tokkit' in source or 'stogram' in source:
                                source_name = source.replace('4k_', '').replace('_', ' ').title()
                                print(f"    {source_name}: {count} videos")
                    
                    # Mostrar información de carpetas organizadas
                    if ext.get('organized_folders'):
                        org = ext['organized_folders']
                        print(f"\n📁 CARPETAS ORGANIZADAS:")
                        print(f"  Carpeta base: {org.get('base_path', 'No configurada')}")
                        
                        if org.get('base_path_exists'):
                            print(f"  Estado: ✅ Carpeta base existe")
                            
                            if org.get('platforms'):
                                print(f"\n  📊 Por plataforma:")
                                for platform, info in org['platforms'].items():
                                    if isinstance(info, dict) and info.get('exists', True):
                                        creators = info.get('creators', 0)
                                        videos = info.get('videos', 0)
                                        print(f"    {platform.capitalize()}: {creators} creadores, {videos} videos")
                                    else:
                                        print(f"    {platform.capitalize()}: ❌ No existe")
                            
                            total_creators = org.get('total_creators', 0)
                            total_videos = org.get('total_videos', 0)
                            print(f"\n  📈 Totales: {total_creators} creadores, {total_videos} videos")
                            
                            if org.get('other_platforms'):
                                other_count = org.get('other_platforms_count', 0)
                                print(f"  🌐 Otras plataformas: {other_count} adicionales")
                        else:
                            print(f"  Estado: ❌ Carpeta base no existe")
                        
                        if org.get('error'):
                            print(f"  ⚠️  Error: {org['error']}")
                
                print("="*60)
            else:
                print(f"❌ Error: {result.get('error', 'Error desconocido')}")
            return
            
        elif command in ['regenerate-thumbnails', 'populate-thumbnails', 'clean-thumbnails', 'thumbnail-stats']:
            from src.maintenance.thumbnail_ops import ThumbnailOperations
            ops = ThumbnailOperations()
            
            if command == 'regenerate-thumbnails':
                result = ops.regenerate_thumbnails(force=getattr(args, 'force', False))
            elif command == 'populate-thumbnails':
                result = ops.populate_thumbnails(
                    platform=getattr(args, 'platform', None),
                    limit=getattr(args, 'limit', None),
                    force=getattr(args, 'force', False)
                )
            elif command == 'clean-thumbnails':
                result = ops.clean_thumbnails(force=getattr(args, 'force', False))
            elif command == 'thumbnail-stats':
                result = ops.get_thumbnail_stats()
                
        elif command in ['verify', 'verify-files', 'integrity-report']:
            from src.maintenance.integrity_ops import IntegrityOperations
            ops = IntegrityOperations()
            
            if command == 'verify':
                result = ops.verify_database_integrity(fix_issues=getattr(args, 'fix_issues', False))
            elif command == 'verify-files':
                result = ops.verify_video_files(video_ids=getattr(args, 'video_id', None))
            elif command == 'integrity-report':
                result = ops.generate_integrity_report(include_details=getattr(args, 'include_details', False))
                
        elif command in ['add-character', 'clean-false-positives', 'update-creator-mappings', 
                        'analyze-titles', 'download-character-images', 'character-detection-report']:
            from src.maintenance.character_ops import CharacterOperations
            ops = CharacterOperations()
            
            if command == 'add-character':
                result = ops.add_custom_character(
                    character_name=args.character,
                    game=args.game,
                    aliases=getattr(args, 'aliases', None) or []
                )
            elif command == 'clean-false-positives':
                result = ops.clean_false_positives(force=getattr(args, 'force', False))
            elif command == 'update-creator-mappings':
                result = ops.update_creator_mappings()
            elif command == 'analyze-titles':
                result = ops.analyze_titles(limit=getattr(args, 'limit', None))
            elif command == 'download-character-images':
                result = ops.download_character_images(
                    character_name=getattr(args, 'character', None),
                    game=getattr(args, 'game', None),
                    limit=getattr(args, 'limit', 10)
                )
            elif command == 'character-detection-report':
                result = ops.get_character_detection_report(
                    video_ids=getattr(args, 'video_ids', None)
                )
                
        elif command in ['show-stats', 'character-stats']:
            from src.utils import format_bytes, format_number
            # 🚀 MIGRADO: Usar service factory para lazy loading
            from src.service_factory import get_database
            db = get_database()
            
            if command == 'show-stats':
                stats = db.get_stats()
                logger.info("📊 Estadísticas del sistema:")
                for key, value in stats.items():
                    logger.info(f"  {key}: {value}")
                return
            else:
                # 🚀 MIGRADO: Character stats usando service factory
                from src.service_factory import get_character_intelligence
                ci = get_character_intelligence()
                stats = ci.get_performance_report()
                logger.info("🎭 Estadísticas de personajes:")
                for key, value in stats.items():
                    logger.info(f"  {key}: {value}")
                return
                
        else:
            logger.error(f"❌ Comando no reconocido: {command}")
            return
        
        # Mostrar resultado
        if result.get('success'):
            logger.info(f"✅ {command}: {result.get('message', 'Completado exitosamente')}")
            
            # Mostrar información adicional para ciertos comandos
            if command == 'character-detection-report':
                self._display_character_detection_report(result)
            elif command == 'character-stats':
                self._display_character_stats(result)
            elif command == 'analyze-titles':
                self._display_analyze_titles_result(result)
            elif command == 'list-backups':
                self._display_backup_list(result)
            elif command in ['backup', 'restore']:
                if 'backup_path' in result:
                    logger.info(f"📁 Ubicación: {result['backup_path']}")
        else:
            logger.error(f"❌ {command}: {result.get('error', 'Error desconocido')}")
    
    def _display_backup_list(self, result):
        """Mostrar lista de backups disponibles"""
        if not result.get('success'):
            return
            
        backups = result.get('backups', [])
        if not backups:
            logger.info("📋 No se encontraron backups")
            return
            
        logger.info(f"📋 Backups disponibles ({len(backups)}):")        
        for i, backup in enumerate(backups, 1):
            size_mb = backup.get('size_mb', 0)
            created = backup.get('created', 'Desconocido')
            # Formatear fecha de YYYYMMDD_HHMMSS a formato legible
            try:
                from datetime import datetime
                if '_' in created:
                    date_part, time_part = created.split('_')
                    dt = datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
                    formatted_date = dt.strftime("%d/%m/%Y %H:%M:%S")
                else:
                    formatted_date = created
            except:
                formatted_date = created
                
            components = backup.get('components', {})
            comp_count = len([k for k, v in components.items() if v])
            
            logger.info(f"  {i}. {backup.get('name', 'Sin nombre')}")
            logger.info(f"     📅 Fecha: {formatted_date}")
            logger.info(f"     📊 Tamaño: {size_mb:.1f} MB")
            logger.info(f"     🧩 Componentes: {comp_count}")
            logger.info(f"     📁 Ruta: {backup.get('path', '')}")
            if i < len(backups):
                logger.info("")
    
    def _display_character_detection_report(self, result):
        """Mostrar reporte de detección de personajes"""
        if not result.get('success'):
            return
            
        summary = result.get('summary', {})
        top_characters = result.get('top_characters', [])
        top_creators = result.get('top_creators', [])
        
        logger.info("📊 REPORTE DE DETECCIÓN DE PERSONAJES")
        logger.info("=" * 50)
        
        # Resumen
        logger.info(f"📈 Videos totales: {summary.get('total_videos', 0)}")
        logger.info(f"🎭 Tasa de detección: {summary.get('detection_rate', 0):.1f}%")
        logger.info(f"👥 Personajes únicos: {summary.get('unique_characters', 0)}")
        logger.info(f"🎨 Creadores activos: {summary.get('active_creators', 0)}")
        logger.info("")
        
        # Top personajes
        if top_characters:
            logger.info("🏆 TOP 10 PERSONAJES MÁS DETECTADOS:")
            for i, (char_name, count) in enumerate(top_characters[:10], 1):
                logger.info(f"  {i:2d}. {char_name}: {count} videos")
            logger.info("")
        
        # Top creadores
        if top_creators:
            logger.info("👨‍🎨 TOP 10 CREADORES CON MÁS DETECCIONES:")
            for i, (creator, count) in enumerate(top_creators[:10], 1):
                logger.info(f"  {i:2d}. {creator}: {count} videos")
    
    def _display_character_stats(self, result):
        """Mostrar estadísticas de personajes"""
        if not result.get('success'):
            return
            
        basic_stats = result.get('basic_stats', {})
        optimized_stats = result.get('optimized_stats', {})
        
        logger.info("🎭 ESTADÍSTICAS DEL SISTEMA DE PERSONAJES")
        logger.info("=" * 50)
        
        logger.info(f"👥 Total personajes: {basic_stats.get('total_characters', 0)}")
        logger.info(f"🎮 Total juegos: {basic_stats.get('total_games', 0)}")
        logger.info(f"🔧 Tipo detector: {basic_stats.get('detector_type', 'N/A')}")
        
        if optimized_stats and basic_stats.get('detector_type') == 'optimized':
            logger.info(f"⚡ Patrones optimizados: {optimized_stats.get('optimized_patterns', 'N/A')}")
            logger.info(f"📈 Cache hit rate: {optimized_stats.get('cache_hit_rate', 'N/A')}")
            logger.info(f"⏱️  Tiempo promedio: {optimized_stats.get('avg_detection_time_ms', 'N/A')} ms")
    
    def _display_analyze_titles_result(self, result):
        """Mostrar resultados del análisis de títulos"""
        if not result.get('success'):
            return
            
        logger.info("📋 ANÁLISIS DE TÍTULOS DE VIDEOS")
        logger.info("=" * 50)
        
        # Estadísticas generales
        logger.info(f"📈 Videos analizados: {result.get('analyzed_videos', 0)}")
        logger.info(f"📝 Palabras únicas: {result.get('unique_words', 0)}")
        logger.info(f"🎭 Personajes mencionados: {result.get('characters_mentioned', 0)}")
        logger.info("")
        
        # Estadísticas de títulos
        title_stats = result.get('title_stats', {})
        if title_stats:
            logger.info("📏 ESTADÍSTICAS DE LONGITUD:")
            logger.info(f"  📊 Promedio: {title_stats.get('avg_length', 0):.1f} caracteres")
            logger.info(f"  📉 Mínima: {title_stats.get('min_length', 0)} caracteres")
            logger.info(f"  📈 Máxima: {title_stats.get('max_length', 0)} caracteres")
            logger.info("")
        
        # Top palabras
        top_words = result.get('top_words', [])
        if top_words:
            logger.info("🔤 TOP 10 PALABRAS MÁS FRECUENTES:")
            for i, (word, count) in enumerate(top_words[:10], 1):
                logger.info(f"  {i:2d}. {word}: {count} veces")
            logger.info("")
        
        # Top personajes
        top_characters = result.get('top_characters', [])
        if top_characters:
            logger.info("🎭 TOP 10 PERSONAJES MÁS MENCIONADOS:")
            for i, (char_name, count) in enumerate(top_characters[:10], 1):
                logger.info(f"  {i:2d}. {char_name}: {count} menciones")
    
    def run(self):
        """Ejecutar CLI"""
        parser = self.create_parser()
        
        # Si no hay argumentos, mostrar ayuda
        if len(sys.argv) == 1:
            parser.print_help()
            return
        
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        try:
            logger.info(f"🚀 Tag-Flow V2 - Ejecutando comando: {args.command}")
            
            if args.command == 'process':
                self.execute_process_command(args)
            else:
                self.execute_maintenance_command(args)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Operación cancelada por el usuario")
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Función principal"""
    cli = TagFlowCLI()
    cli.run()

if __name__ == '__main__':
    main()