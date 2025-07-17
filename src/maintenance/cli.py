#!/usr/bin/env python3
"""
🖥️ Maintenance CLI Module
Módulo CLI wrapper para operaciones de mantenimiento
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.maintenance.backup_ops import BackupOperations
from src.maintenance.character_ops import CharacterOperations
from src.maintenance.integrity_ops import IntegrityOperations
from src.maintenance.thumbnail_ops import ThumbnailOperations
from src.maintenance.database_ops import DatabaseOperations
from src.maintenance.utils import format_bytes, format_number, TimeUtils, SystemUtils


class MaintenanceCLI:
    """
    🖥️ Interfaz de línea de comandos para operaciones de mantenimiento
    
    Proporciona una interfaz unificada para todas las operaciones de mantenimiento
    del sistema Tag-Flow V2.
    """
    
    def __init__(self):
        self.backup_ops = BackupOperations()
        self.character_ops = CharacterOperations()
        self.integrity_ops = IntegrityOperations()
        self.thumbnail_ops = ThumbnailOperations()
        self.database_ops = DatabaseOperations()
        
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Crear parser de argumentos"""
        parser = argparse.ArgumentParser(
            description='🔧 Tag-Flow V2 Maintenance System',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Ejemplos de uso:
  python -m src.maintenance.cli backup --compress
  python -m src.maintenance.cli character-stats
  python -m src.maintenance.cli verify --fix-issues
  python -m src.maintenance.cli thumbnails --platform youtube --limit 50
  python -m src.maintenance.cli database --populate --source all
            """
        )
        
        # Argumentos globales
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Mostrar información detallada'
        )
        
        parser.add_argument(
            '--json',
            action='store_true',
            help='Salida en formato JSON'
        )
        
        parser.add_argument(
            '--no-color',
            action='store_true',
            help='Desactivar colores en la salida'
        )
        
        # Subcomandos
        subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
        
        # Backup commands
        self._add_backup_commands(subparsers)
        
        # Character commands
        self._add_character_commands(subparsers)
        
        # Integrity commands
        self._add_integrity_commands(subparsers)
        
        # Thumbnail commands
        self._add_thumbnail_commands(subparsers)
        
        # Database commands
        self._add_database_commands(subparsers)
        
        # System commands
        self._add_system_commands(subparsers)
        
        return parser
    
    def _add_backup_commands(self, subparsers):
        """Agregar comandos de backup"""
        # Backup create
        backup_parser = subparsers.add_parser('backup', help='Crear backup del sistema')
        backup_parser.add_argument('--compress', action='store_true', help='Comprimir backup')
        backup_parser.add_argument('--no-thumbnails', action='store_true', help='Excluir thumbnails')
        backup_parser.add_argument('--thumbnail-limit', type=int, default=100, help='Límite de thumbnails')
        
        # Backup restore
        restore_parser = subparsers.add_parser('restore', help='Restaurar desde backup')
        restore_parser.add_argument('backup_path', help='Ruta del backup')
        restore_parser.add_argument('--components', nargs='+', help='Componentes a restaurar')
        restore_parser.add_argument('--force', action='store_true', help='Forzar restauración')
        
        # Backup list
        list_parser = subparsers.add_parser('list-backups', help='Listar backups disponibles')
        list_parser.add_argument('--limit', type=int, help='Límite de backups a mostrar')
        
        # Backup verify
        verify_parser = subparsers.add_parser('verify-backup', help='Verificar integridad de backup')
        verify_parser.add_argument('backup_path', help='Ruta del backup')
        
        # Backup cleanup
        cleanup_parser = subparsers.add_parser('cleanup-backups', help='Limpiar backups antiguos')
        cleanup_parser.add_argument('--keep', type=int, default=5, help='Número de backups a mantener')
        cleanup_parser.add_argument('--max-age', type=int, default=30, help='Edad máxima en días')
    
    def _add_character_commands(self, subparsers):
        """Agregar comandos de personajes"""
        # Character stats
        subparsers.add_parser('character-stats', help='Mostrar estadísticas de personajes')
        
        # Add character
        add_char_parser = subparsers.add_parser('add-character', help='Agregar personaje personalizado')
        add_char_parser.add_argument('--character', required=True, help='Nombre del personaje')
        add_char_parser.add_argument('--game', required=True, help='Juego/serie')
        add_char_parser.add_argument('--aliases', nargs='+', help='Alias del personaje')
        
        # Clean false positives
        clean_parser = subparsers.add_parser('clean-false-positives', help='Limpiar falsos positivos')
        clean_parser.add_argument('--force', action='store_true', help='Forzar limpieza')
        
        # Update creator mappings
        mapping_parser = subparsers.add_parser('update-creator-mappings', help='Actualizar mapeos de creadores')
        mapping_parser.add_argument('--no-auto-detect', action='store_true', help='Desactivar detección automática')
        
        # Analyze titles
        analyze_parser = subparsers.add_parser('analyze-titles', help='Analizar títulos de videos')
        analyze_parser.add_argument('--limit', type=int, help='Límite de videos a analizar')
        
        # Download character images
        download_parser = subparsers.add_parser('download-character-images', help='Descargar imágenes de personajes')
        download_parser.add_argument('--character', help='Personaje específico')
        download_parser.add_argument('--game', help='Juego específico')
        download_parser.add_argument('--limit', type=int, default=10, help='Límite de imágenes')
        
        # Character detection report
        report_parser = subparsers.add_parser('character-detection-report', help='Generar reporte de detección')
        report_parser.add_argument('--video-ids', nargs='+', type=int, help='IDs específicos de videos')
    
    def _add_integrity_commands(self, subparsers):
        """Agregar comandos de integridad"""
        # Verify system
        verify_parser = subparsers.add_parser('verify', help='Verificar integridad del sistema')
        verify_parser.add_argument('--fix-issues', action='store_true', help='Intentar corregir problemas')
        
        # Verify files
        verify_files_parser = subparsers.add_parser('verify-files', help='Verificar archivos de video')
        verify_files_parser.add_argument('--video-ids', nargs='+', type=int, help='IDs específicos de videos')
        
        # Verify thumbnails
        verify_thumb_parser = subparsers.add_parser('verify-thumbnails', help='Verificar thumbnails')
        verify_thumb_parser.add_argument('--regenerate-missing', action='store_true', help='Regenerar thumbnails faltantes')
        
        # Verify configuration
        subparsers.add_parser('verify-config', help='Verificar configuración del sistema')
        
        # Generate integrity report
        report_parser = subparsers.add_parser('integrity-report', help='Generar reporte de integridad')
        report_parser.add_argument('--include-details', action='store_true', help='Incluir detalles extensos')
    
    def _add_thumbnail_commands(self, subparsers):
        """Agregar comandos de thumbnails"""
        # Populate thumbnails
        populate_parser = subparsers.add_parser('populate-thumbnails', help='Poblar thumbnails')
        populate_parser.add_argument('--platform', help='Plataforma específica')
        populate_parser.add_argument('--limit', type=int, help='Límite de thumbnails')
        populate_parser.add_argument('--force', action='store_true', help='Regenerar existentes')
        
        # Regenerate thumbnails
        regen_parser = subparsers.add_parser('regenerate-thumbnails', help='Regenerar thumbnails')
        regen_parser.add_argument('--video-ids', nargs='+', type=int, help='IDs específicos de videos')
        regen_parser.add_argument('--force', action='store_true', help='Regenerar existentes')
        
        # Clean thumbnails
        clean_parser = subparsers.add_parser('clean-thumbnails', help='Limpiar thumbnails huérfanos')
        clean_parser.add_argument('--force', action='store_true', help='Forzar limpieza')
        
        # Thumbnail stats
        subparsers.add_parser('thumbnail-stats', help='Mostrar estadísticas de thumbnails')
    
    def _add_database_commands(self, subparsers):
        """Agregar comandos de base de datos"""
        # Populate database
        populate_parser = subparsers.add_parser('populate-db', help='Poblar base de datos')
        populate_parser.add_argument('--source', choices=['db', 'organized', 'all'], default='all', help='Fuente de datos')
        populate_parser.add_argument('--platform', help='Plataforma específica')
        populate_parser.add_argument('--limit', type=int, help='Límite de videos')
        populate_parser.add_argument('--force', action='store_true', help='Forzar reimportación')
        
        # Optimize database
        subparsers.add_parser('optimize-db', help='Optimizar base de datos')
        
        # Clear database
        clear_parser = subparsers.add_parser('clear-db', help='Limpiar base de datos')
        clear_parser.add_argument('--platform', help='Plataforma específica')
        clear_parser.add_argument('--force', action='store_true', help='Forzar eliminación')
        
        # Database stats
        subparsers.add_parser('db-stats', help='Mostrar estadísticas de base de datos')
    
    def _add_system_commands(self, subparsers):
        """Agregar comandos del sistema"""
        # System stats
        subparsers.add_parser('system-stats', help='Mostrar estadísticas del sistema')
        
        # System health
        subparsers.add_parser('health', help='Verificar salud del sistema')
        
        # Show version
        subparsers.add_parser('version', help='Mostrar versión del sistema')
    
    def run(self, args: List[str] = None) -> int:
        """Ejecutar CLI"""
        try:
            parsed_args = self.parser.parse_args(args)
            
            # Configurar logging
            if parsed_args.verbose:
                logging.getLogger().setLevel(logging.DEBUG)
            
            # Ejecutar comando
            if not parsed_args.command:
                self.parser.print_help()
                return 1
            
            result = self._execute_command(parsed_args)
            
            # Mostrar resultado
            if parsed_args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                self._print_result(result, parsed_args)
            
            return 0 if result.get('success', False) else 1
            
        except KeyboardInterrupt:
            print("\n❌ Operación cancelada por el usuario")
            return 130
        except Exception as e:
            logger.error(f"Error ejecutando comando: {e}")
            return 1
    
    def _execute_command(self, args) -> Dict[str, Any]:
        """Ejecutar comando específico"""
        command = args.command
        
        # Backup commands
        if command == 'backup':
            return self.backup_ops.create_backup(
                include_thumbnails=not args.no_thumbnails,
                thumbnail_limit=args.thumbnail_limit,
                compress=args.compress
            )
        
        elif command == 'restore':
            return self.backup_ops.restore_backup(
                backup_path=args.backup_path,
                components=args.components,
                force=args.force
            )
        
        elif command == 'list-backups':
            return self.backup_ops.list_backups(limit=args.limit)
        
        elif command == 'verify-backup':
            return self.backup_ops.verify_backup(args.backup_path)
        
        elif command == 'cleanup-backups':
            return self.backup_ops.cleanup_old_backups(
                keep_count=args.keep,
                max_age_days=args.max_age
            )
        
        # Character commands
        elif command == 'character-stats':
            return self.character_ops.show_character_stats()
        
        elif command == 'add-character':
            return self.character_ops.add_custom_character(
                character_name=args.character,
                game=args.game,
                aliases=args.aliases
            )
        
        elif command == 'clean-false-positives':
            return self.character_ops.clean_false_positives(force=args.force)
        
        elif command == 'update-creator-mappings':
            return self.character_ops.update_creator_mappings(
                auto_detect=not args.no_auto_detect
            )
        
        elif command == 'analyze-titles':
            return self.character_ops.analyze_titles(limit=args.limit)
        
        elif command == 'download-character-images':
            return self.character_ops.download_character_images(
                character_name=args.character,
                game=args.game,
                limit=args.limit
            )
        
        elif command == 'character-detection-report':
            return self.character_ops.get_character_detection_report(
                video_ids=args.video_ids
            )
        
        # Integrity commands
        elif command == 'verify':
            return self.integrity_ops.verify_database_integrity(
                fix_issues=args.fix_issues
            )
        
        elif command == 'verify-files':
            return self.integrity_ops.verify_video_files(
                video_ids=args.video_ids
            )
        
        elif command == 'verify-thumbnails':
            return self.integrity_ops.verify_thumbnails(
                regenerate_missing=args.regenerate_missing
            )
        
        elif command == 'verify-config':
            return self.integrity_ops.verify_configuration()
        
        elif command == 'integrity-report':
            return self.integrity_ops.generate_integrity_report(
                include_details=args.include_details
            )
        
        # Thumbnail commands
        elif command == 'populate-thumbnails':
            return self.thumbnail_ops.populate_thumbnails(
                platform=args.platform,
                limit=args.limit,
                force=args.force
            )
        
        elif command == 'regenerate-thumbnails':
            return self.thumbnail_ops.regenerate_thumbnails_by_ids(
                video_ids=args.video_ids,
                force=args.force
            )
        
        elif command == 'clean-thumbnails':
            return self.thumbnail_ops.clean_thumbnails(force=args.force)
        
        elif command == 'thumbnail-stats':
            return self.thumbnail_ops.get_thumbnail_stats()
        
        # Database commands
        elif command == 'populate-db':
            return self.database_ops.populate_database(
                source=args.source,
                platform=args.platform,
                limit=args.limit,
                force=args.force
            )
        
        elif command == 'optimize-db':
            return self.database_ops.optimize_database()
        
        elif command == 'clear-db':
            return self.database_ops.clear_database(
                platform=args.platform,
                force=args.force
            )
        
        elif command == 'db-stats':
            return self.database_ops.get_database_stats()
        
        # System commands
        elif command == 'system-stats':
            return self._get_system_stats()
        
        elif command == 'health':
            return self._get_system_health()
        
        elif command == 'version':
            return self._get_version_info()
        
        else:
            return {'success': False, 'error': f'Comando desconocido: {command}'}
    
    def _print_result(self, result: Dict[str, Any], args):
        """Imprimir resultado formateado"""
        if not result.get('success', False):
            print(f"❌ Error: {result.get('error', 'Operación falló')}")
            return
        
        command = args.command
        
        # Mensajes específicos por comando
        if command == 'backup':
            print(f"✅ {result.get('message', 'Backup creado exitosamente')}")
            if 'backup_size_mb' in result:
                print(f"   📁 Tamaño: {result['backup_size_mb']:.1f} MB")
            if 'duration' in result:
                print(f"   ⏱️ Duración: {TimeUtils.format_duration(result['duration'])}")
        
        elif command == 'character-stats':
            stats = result.get('basic_stats', {})
            print(f"📊 Estadísticas de Personajes:")
            print(f"   👥 Total personajes: {format_number(stats.get('total_characters', 0))}")
            print(f"   🎮 Total juegos: {format_number(stats.get('total_games', 0))}")
            print(f"   🔧 Detector: {stats.get('detector_type', 'unknown')}")
            print(f"   🗂️ Mapeos creadores: {format_number(stats.get('creator_mappings', 0))}")
            
            if 'optimized_stats' in result:
                opt_stats = result['optimized_stats']
                if opt_stats.get('cache_hit_rate'):
                    print(f"   🎯 Cache hit rate: {opt_stats['cache_hit_rate']}")
                if opt_stats.get('avg_detection_time_ms'):
                    print(f"   ⚡ Tiempo detección: {opt_stats['avg_detection_time_ms']}ms")
        
        elif command == 'verify':
            score = result.get('integrity_score', 0)
            issues = result.get('total_issues', 0)
            print(f"🔍 Verificación de Integridad:")
            print(f"   🎯 Puntuación: {score:.1f}/100")
            print(f"   ⚠️ Problemas encontrados: {issues}")
            if result.get('issues_fixed', 0) > 0:
                print(f"   ✅ Problemas corregidos: {result['issues_fixed']}")
        
        elif command == 'system-stats':
            stats = result.get('system_stats', {})
            print(f"💻 Estadísticas del Sistema:")
            print(f"   🖥️ CPU: {stats.get('cpu_percent', 0):.1f}%")
            print(f"   💾 Memoria: {stats.get('memory_percent', 0):.1f}%")
            print(f"   💿 Disco: {stats.get('disk_percent', 0):.1f}%")
            print(f"   ⏱️ Uptime: {TimeUtils.format_duration(stats.get('uptime_hours', 0) * 3600)}")
        
        elif command == 'integrity-report':
            report = result.get('integrity_report', {})
            print(f"📊 Reporte de Integridad:")
            print(f"   🎯 Puntuación general: {report.get('overall_score', 0):.1f}/100")
            print(f"   📈 Estado: {report.get('overall_status', 'unknown')}")
            
            components = report.get('components', {})
            for comp_name, comp_data in components.items():
                print(f"   {comp_name}: {comp_data.get('score', 0):.1f}/100")
            
            recommendations = report.get('recommendations', [])
            if recommendations:
                print(f"   💡 Recomendaciones: {len(recommendations)}")
        
        else:
            # Mensaje genérico
            print(f"✅ {result.get('message', 'Operación completada exitosamente')}")
    
    def _get_system_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema"""
        try:
            stats = SystemUtils.get_system_stats()
            return {
                'success': True,
                'system_stats': stats.to_dict(),
                'message': 'Estadísticas del sistema obtenidas'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Obtener salud del sistema"""
        try:
            stats = SystemUtils.get_system_stats()
            
            # Determinar estado de salud
            health_issues = []
            
            if stats.cpu_percent > 80:
                health_issues.append('CPU usage high')
            if stats.memory_percent > 90:
                health_issues.append('Memory usage high')
            if stats.disk_percent > 95:
                health_issues.append('Disk usage critical')
            
            if not health_issues:
                health_status = 'healthy'
            elif len(health_issues) == 1:
                health_status = 'warning'
            else:
                health_status = 'critical'
            
            return {
                'success': True,
                'health_status': health_status,
                'health_issues': health_issues,
                'system_stats': stats.to_dict(),
                'message': f'Sistema {health_status}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_version_info(self) -> Dict[str, Any]:
        """Obtener información de versión"""
        return {
            'success': True,
            'version': '2.0.0',
            'name': 'Tag-Flow V2',
            'description': 'Sistema inteligente de gestión de videos',
            'python_version': sys.version,
            'message': 'Tag-Flow V2 versión 2.0.0'
        }


def main():
    """Función principal para ejecutar CLI"""
    cli = MaintenanceCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()