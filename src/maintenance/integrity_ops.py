#!/usr/bin/env python3
"""
🔍 Integrity Operations Module
Módulo especializado para verificaciones de integridad extraído de main.py
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import hashlib
import sqlite3

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


class IntegrityOperations:
    """
    🔍 Operaciones especializadas de verificación de integridad
    
    Funcionalidades:
    - Verificación de consistencia de BD
    - Validación de archivos de video
    - Verificación de thumbnails
    - Análisis de referencias rotas
    - Validación de configuración
    - Reporte de integridad del sistema
    """
    
    def __init__(self):
        # 🚀 MIGRADO: Usar service factory para gestión centralizada
        # NO instanciar servicios en __init__ para máximo lazy loading
        self._db = None
        self._character_intelligence = None
    
    @property
    def db(self):
        """Lazy initialization of DatabaseManager via ServiceFactory"""
        if self._db is None:
            from src.service_factory import get_database
            self._db = get_database()
        return self._db
    
    @property
    def character_intelligence(self):
        """Lazy initialization of CharacterIntelligence via ServiceFactory"""
        if self._character_intelligence is None:
            from src.service_factory import get_character_intelligence
            self._character_intelligence = get_character_intelligence()
        return self._character_intelligence
    
    def verify_database_integrity(self, fix_issues: bool = False) -> Dict[str, Any]:
        """
        🔍 Verificar integridad de la base de datos
        
        Args:
            fix_issues: intentar corregir problemas encontrados
            
        Returns:
            Dict con resultados de la verificación
        """
        logger.info("🔍 Verificando integridad de la base de datos...")
        
        try:
            integrity_report = {
                'database_file': {
                    'exists': False,
                    'accessible': False,
                    'size_mb': 0,
                    'tables_count': 0
                },
                'video_records': {
                    'total_videos': 0,
                    'missing_files': 0,
                    'duplicate_paths': 0,
                    'invalid_metadata': 0
                },
                'thumbnails': {
                    'total_thumbnails': 0,
                    'missing_thumbnails': 0,
                    'orphaned_thumbnails': 0,
                    'invalid_paths': 0
                },
                'references': {
                    'broken_file_paths': 0,
                    'broken_thumbnail_paths': 0,
                    'missing_creators': 0
                },
                'fixed_issues': 0,
                'issues_found': []
            }
            
            # 1. Verificar archivo de base de datos
            db_path = config.DATABASE_PATH
            if db_path.exists():
                integrity_report['database_file']['exists'] = True
                integrity_report['database_file']['size_mb'] = db_path.stat().st_size / (1024 * 1024)
                
                try:
                    with sqlite3.connect(db_path) as conn:
                        integrity_report['database_file']['accessible'] = True
                        
                        # Verificar tablas
                        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()
                        integrity_report['database_file']['tables_count'] = len(tables)
                        
                        # Verificar integridad SQLite
                        cursor = conn.execute("PRAGMA integrity_check")
                        integrity_check = cursor.fetchone()
                        if integrity_check[0] != 'ok':
                            integrity_report['issues_found'].append({
                                'type': 'database_corruption',
                                'description': f'SQLite integrity check failed: {integrity_check[0]}',
                                'severity': 'high'
                            })
                        
                except sqlite3.Error as e:
                    integrity_report['issues_found'].append({
                        'type': 'database_access',
                        'description': f'Cannot access database: {e}',
                        'severity': 'critical'
                    })
            else:
                integrity_report['issues_found'].append({
                    'type': 'database_missing',
                    'description': f'Database file not found: {db_path}',
                    'severity': 'critical'
                })
            
            # 2. Verificar registros de video
            videos = self.db.get_videos()
            integrity_report['video_records']['total_videos'] = len(videos)
            
            file_paths = {}
            for video in videos:
                file_path = video.get('file_path')
                if file_path:
                    # Verificar archivos duplicados
                    if file_path in file_paths:
                        integrity_report['video_records']['duplicate_paths'] += 1
                        integrity_report['issues_found'].append({
                            'type': 'duplicate_path',
                            'description': f'Duplicate file path: {file_path}',
                            'severity': 'medium',
                            'video_ids': [file_paths[file_path], video['id']]
                        })
                    else:
                        file_paths[file_path] = video['id']
                    
                    # Verificar que el archivo existe
                    if not Path(file_path).exists():
                        integrity_report['video_records']['missing_files'] += 1
                        integrity_report['references']['broken_file_paths'] += 1
                        integrity_report['issues_found'].append({
                            'type': 'missing_file',
                            'description': f'Video file not found: {file_path}',
                            'severity': 'high',
                            'video_id': video['id']
                        })
                
                # Verificar metadatos requeridos
                required_fields = ['platform', 'creator_name']
                for field in required_fields:
                    if not video.get(field):
                        integrity_report['video_records']['invalid_metadata'] += 1
                        integrity_report['issues_found'].append({
                            'type': 'missing_metadata',
                            'description': f'Missing {field} for video {video["id"]}',
                            'severity': 'low',
                            'video_id': video['id']
                        })
                
                # Verificar descripciones específicas para TikTok/Instagram
                platform = video.get('platform', '').lower()
                if platform in ['tiktok', 'instagram']:
                    if not video.get('description'):
                        integrity_report['video_records']['invalid_metadata'] += 1
                        integrity_report['issues_found'].append({
                            'type': 'missing_description_tiktok_instagram',
                            'description': f'Missing description for {platform} video {video["id"]} - can extract from external DB',
                            'severity': 'medium',
                            'video_id': video['id'],
                            'platform': platform,
                            'file_path': video.get('file_path')
                        })
            
            # 3. Verificar thumbnails
            thumbnails_dir = config.THUMBNAILS_PATH
            if thumbnails_dir.exists():
                thumbnail_files = set(f.name for f in thumbnails_dir.glob('*.jpg'))
                integrity_report['thumbnails']['total_thumbnails'] = len(thumbnail_files)
                
                # Verificar thumbnails en BD
                videos_with_thumbnails = [v for v in videos if v.get('thumbnail_path')]
                for video in videos_with_thumbnails:
                    thumbnail_path = video.get('thumbnail_path')
                    if thumbnail_path:
                        thumbnail_name = Path(thumbnail_path).name
                        if thumbnail_name not in thumbnail_files:
                            integrity_report['thumbnails']['missing_thumbnails'] += 1
                            integrity_report['references']['broken_thumbnail_paths'] += 1
                            integrity_report['issues_found'].append({
                                'type': 'missing_thumbnail',
                                'description': f'Thumbnail not found: {thumbnail_path}',
                                'severity': 'medium',
                                'video_id': video['id']
                            })
                
                # Verificar thumbnails huérfanos
                video_thumbnail_names = set()
                for video in videos_with_thumbnails:
                    thumbnail_path = video.get('thumbnail_path')
                    if thumbnail_path:
                        video_thumbnail_names.add(Path(thumbnail_path).name)
                
                orphaned_thumbnails = thumbnail_files - video_thumbnail_names
                integrity_report['thumbnails']['orphaned_thumbnails'] = len(orphaned_thumbnails)
                
                for orphaned in orphaned_thumbnails:
                    integrity_report['issues_found'].append({
                        'type': 'orphaned_thumbnail',
                        'description': f'Orphaned thumbnail: {orphaned}',
                        'severity': 'low',
                        'file_name': orphaned
                    })
            
            # 4. Intentar corregir problemas si se solicita
            if fix_issues:
                integrity_report['fixed_issues'] = self._fix_integrity_issues(integrity_report['issues_found'])
            
            # 5. Calcular puntuación de integridad
            total_issues = len(integrity_report['issues_found'])
            critical_issues = len([i for i in integrity_report['issues_found'] if i['severity'] == 'critical'])
            high_issues = len([i for i in integrity_report['issues_found'] if i['severity'] == 'high'])
            
            # Puntuación de 0-100
            if critical_issues > 0:
                integrity_score = 0
            elif high_issues > 0:
                integrity_score = max(0, 50 - (high_issues * 10))
            else:
                integrity_score = max(0, 100 - (total_issues * 5))
            
            integrity_report['integrity_score'] = integrity_score
            integrity_report['total_issues'] = total_issues
            
            # Mostrar detalles de los problemas encontrados
            if total_issues > 0:
                self._display_verification_details(integrity_report['issues_found'], fix_issues)
            
            # Mostrar resumen final
            if fix_issues and integrity_report.get('fixed_issues', 0) > 0:
                logger.info(f"✅ Verificación completada: {integrity_report['fixed_issues']} problemas corregidos, {total_issues - integrity_report['fixed_issues']} restantes")
            else:
                logger.info(f"✅ Verificación completada: {total_issues} problemas encontrados")
            
            logger.info(f"   🎯 Puntuación de integridad: {integrity_score}/100")
            
            return {
                'success': True,
                'integrity_report': integrity_report,
                'integrity_score': integrity_score,
                'total_issues': total_issues,
                'issues_fixed': integrity_report['fixed_issues'],
                'message': f'Verificación completada: {integrity_report.get("fixed_issues", 0)} problemas corregidos' if fix_issues and integrity_report.get('fixed_issues', 0) > 0 else f'Verificación completada: {total_issues} problemas encontrados'
            }
            
        except Exception as e:
            logger.error(f"Error verificando integridad: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_video_files(self, video_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        📹 Verificar archivos de video específicos
        
        Args:
            video_ids: lista de IDs de videos o None para todos
            
        Returns:
            Dict con resultados de la verificación
        """
        logger.info("📹 Verificando archivos de video...")
        
        try:
            # Obtener videos
            if video_ids:
                videos = []
                for video_id in video_ids:
                    video = self.db.get_video(video_id)
                    if video:
                        videos.append(video)
            else:
                videos = self.db.get_videos()
            
            verification_results = {
                'total_videos': len(videos),
                'existing_files': 0,
                'missing_files': 0,
                'accessible_files': 0,
                'corrupted_files': 0,
                'file_details': []
            }
            
            for video in videos:
                file_path = video.get('file_path')
                if not file_path:
                    continue
                
                file_info = {
                    'video_id': video['id'],
                    'file_path': file_path,
                    'exists': False,
                    'accessible': False,
                    'size_mb': 0,
                    'corrupted': False,
                    'last_modified': None
                }
                
                try:
                    file_path_obj = Path(file_path)
                    
                    # Verificar existencia
                    if file_path_obj.exists():
                        file_info['exists'] = True
                        verification_results['existing_files'] += 1
                        
                        # Verificar accesibilidad
                        if file_path_obj.is_file():
                            file_info['accessible'] = True
                            verification_results['accessible_files'] += 1
                            
                            # Obtener información del archivo
                            stat = file_path_obj.stat()
                            file_info['size_mb'] = stat.st_size / (1024 * 1024)
                            file_info['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                            
                            # Verificación básica de corrupción (tamaño muy pequeño)
                            if stat.st_size < 1024:  # Menor a 1KB es sospechoso
                                file_info['corrupted'] = True
                                verification_results['corrupted_files'] += 1
                    else:
                        verification_results['missing_files'] += 1
                        
                except Exception as e:
                    logger.warning(f"Error verificando archivo {file_path}: {e}")
                    file_info['error'] = str(e)
                
                verification_results['file_details'].append(file_info)
            
            # Calcular estadísticas
            success_rate = (verification_results['accessible_files'] / verification_results['total_videos'] * 100) if verification_results['total_videos'] > 0 else 0
            
            logger.info(f"✅ Verificación de archivos completada:")
            logger.info(f"   📊 {verification_results['accessible_files']}/{verification_results['total_videos']} archivos accesibles ({success_rate:.1f}%)")
            logger.info(f"   ❌ {verification_results['missing_files']} archivos faltantes")
            logger.info(f"   🔥 {verification_results['corrupted_files']} archivos posiblemente corruptos")
            
            return {
                'success': True,
                'verification_results': verification_results,
                'success_rate': success_rate,
                'message': f'Verificados {verification_results["total_videos"]} videos'
            }
            
        except Exception as e:
            logger.error(f"Error verificando archivos de video: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_thumbnails(self, regenerate_missing: bool = False) -> Dict[str, Any]:
        """
        🖼️ Verificar thumbnails del sistema
        
        Args:
            regenerate_missing: regenerar thumbnails faltantes
            
        Returns:
            Dict con resultados de la verificación
        """
        logger.info("🖼️ Verificando thumbnails...")
        
        try:
            thumbnails_dir = config.THUMBNAILS_PATH
            
            verification_results = {
                'thumbnails_directory': {
                    'exists': thumbnails_dir.exists(),
                    'path': str(thumbnails_dir),
                    'total_files': 0,
                    'size_mb': 0
                },
                'video_thumbnails': {
                    'total_videos': 0,
                    'with_thumbnails': 0,
                    'missing_thumbnails': 0,
                    'broken_thumbnails': 0
                },
                'orphaned_thumbnails': [],
                'missing_thumbnails': [],
                'regenerated_count': 0
            }
            
            # Verificar directorio de thumbnails
            if thumbnails_dir.exists():
                thumbnail_files = list(thumbnails_dir.glob('*.jpg'))
                verification_results['thumbnails_directory']['total_files'] = len(thumbnail_files)
                
                # Calcular tamaño total
                total_size = sum(f.stat().st_size for f in thumbnail_files)
                verification_results['thumbnails_directory']['size_mb'] = total_size / (1024 * 1024)
                
                # Crear set de thumbnails existentes
                existing_thumbnails = {f.name for f in thumbnail_files}
            else:
                existing_thumbnails = set()
                thumbnails_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"📁 Creado directorio de thumbnails: {thumbnails_dir}")
            
            # Verificar thumbnails de videos
            videos = self.db.get_videos()
            verification_results['video_thumbnails']['total_videos'] = len(videos)
            
            video_thumbnail_names = set()
            
            for video in videos:
                thumbnail_path = video.get('thumbnail_path')
                
                if thumbnail_path:
                    verification_results['video_thumbnails']['with_thumbnails'] += 1
                    thumbnail_name = Path(thumbnail_path).name
                    video_thumbnail_names.add(thumbnail_name)
                    
                    # Verificar si el thumbnail existe
                    if thumbnail_name not in existing_thumbnails:
                        verification_results['video_thumbnails']['broken_thumbnails'] += 1
                        verification_results['missing_thumbnails'].append({
                            'video_id': video['id'],
                            'video_path': video.get('file_path', 'Unknown'),
                            'thumbnail_path': thumbnail_path,
                            'thumbnail_name': thumbnail_name
                        })
                else:
                    verification_results['video_thumbnails']['missing_thumbnails'] += 1
                    verification_results['missing_thumbnails'].append({
                        'video_id': video['id'],
                        'video_path': video.get('file_path', 'Unknown'),
                        'thumbnail_path': None,
                        'thumbnail_name': None
                    })
            
            # Identificar thumbnails huérfanos
            orphaned_thumbnails = existing_thumbnails - video_thumbnail_names
            verification_results['orphaned_thumbnails'] = [
                {
                    'file_name': thumb,
                    'file_path': str(thumbnails_dir / thumb),
                    'size_kb': (thumbnails_dir / thumb).stat().st_size / 1024
                }
                for thumb in orphaned_thumbnails
            ]
            
            # Regenerar thumbnails faltantes si se solicita
            if regenerate_missing and verification_results['missing_thumbnails']:
                logger.info("🔄 Regenerando thumbnails faltantes...")
                
                try:
                    from src.service_factory import get_thumbnail_generator
                    thumbnail_generator = get_thumbnail_generator()
                    
                    for missing in verification_results['missing_thumbnails']:
                        video_id = missing['video_id']
                        video_path = missing['video_path']
                        
                        if video_path and Path(video_path).exists():
                            try:
                                thumbnail_path = thumbnail_generator.generate_thumbnail(video_path, video_id)
                                if thumbnail_path:
                                    # Actualizar BD
                                    self.db.update_video(video_id, {'thumbnail_path': thumbnail_path})
                                    verification_results['regenerated_count'] += 1
                                    logger.info(f"✅ Regenerado thumbnail para video {video_id}")
                            except Exception as e:
                                logger.warning(f"Error regenerando thumbnail para video {video_id}: {e}")
                                
                except ImportError:
                    logger.warning("ThumbnailGenerator no disponible para regeneración")
            
            # Calcular estadísticas
            thumbnail_coverage = (verification_results['video_thumbnails']['with_thumbnails'] / verification_results['video_thumbnails']['total_videos'] * 100) if verification_results['video_thumbnails']['total_videos'] > 0 else 0
            
            logger.info(f"✅ Verificación de thumbnails completada:")
            logger.info(f"   📊 {verification_results['video_thumbnails']['with_thumbnails']}/{verification_results['video_thumbnails']['total_videos']} videos con thumbnails ({thumbnail_coverage:.1f}%)")
            logger.info(f"   ❌ {len(verification_results['missing_thumbnails'])} thumbnails faltantes")
            logger.info(f"   🗑️ {len(verification_results['orphaned_thumbnails'])} thumbnails huérfanos")
            if regenerate_missing:
                logger.info(f"   🔄 {verification_results['regenerated_count']} thumbnails regenerados")
            
            return {
                'success': True,
                'verification_results': verification_results,
                'thumbnail_coverage': thumbnail_coverage,
                'regenerated_count': verification_results['regenerated_count'],
                'message': f'Verificación completada: {thumbnail_coverage:.1f}% cobertura de thumbnails'
            }
            
        except Exception as e:
            logger.error(f"Error verificando thumbnails: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_configuration(self) -> Dict[str, Any]:
        """
        ⚙️ Verificar configuración del sistema
        
        Returns:
            Dict con resultados de la verificación
        """
        logger.info("⚙️ Verificando configuración del sistema...")
        
        try:
            config_verification = {
                'environment_file': {
                    'exists': False,
                    'readable': False,
                    'variables_count': 0,
                    'missing_variables': []
                },
                'config_module': {
                    'accessible': False,
                    'attributes_count': 0,
                    'missing_attributes': []
                },
                'directories': {
                    'data_dir': {'exists': False, 'writable': False, 'path': ''},
                    'thumbnails_dir': {'exists': False, 'writable': False, 'path': ''},
                    'known_faces_dir': {'exists': False, 'writable': False, 'path': ''}
                },
                'database_files': {
                    'character_database': {'exists': False, 'readable': False, 'path': ''},
                    'creator_mapping': {'exists': False, 'readable': False, 'path': ''}
                },
                'issues_found': []
            }
            
            # 1. Verificar archivo .env
            env_file = Path('.env')
            if env_file.exists():
                config_verification['environment_file']['exists'] = True
                try:
                    with open(env_file, 'r') as f:
                        env_content = f.read()
                    config_verification['environment_file']['readable'] = True
                    
                    # Contar variables
                    env_lines = [line for line in env_content.split('\n') if line.strip() and not line.startswith('#')]
                    config_verification['environment_file']['variables_count'] = len(env_lines)
                    
                    # Verificar variables críticas
                    critical_vars = ['YOUTUBE_API_KEY', 'SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET']
                    for var in critical_vars:
                        if var not in env_content:
                            config_verification['environment_file']['missing_variables'].append(var)
                            config_verification['issues_found'].append({
                                'type': 'missing_env_variable',
                                'description': f'Missing environment variable: {var}',
                                'severity': 'medium'
                            })
                            
                except Exception as e:
                    config_verification['issues_found'].append({
                        'type': 'env_file_error',
                        'description': f'Cannot read .env file: {e}',
                        'severity': 'high'
                    })
            else:
                config_verification['issues_found'].append({
                    'type': 'env_file_missing',
                    'description': '.env file not found',
                    'severity': 'medium'
                })
            
            # 2. Verificar módulo config
            try:
                import config
                config_verification['config_module']['accessible'] = True
                config_verification['config_module']['attributes_count'] = len(dir(config))
                
                # Verificar atributos críticos
                critical_attrs = ['DATABASE_PATH', 'THUMBNAILS_PATH', 'KNOWN_FACES_PATH']
                for attr in critical_attrs:
                    if not hasattr(config, attr):
                        config_verification['config_module']['missing_attributes'].append(attr)
                        config_verification['issues_found'].append({
                            'type': 'missing_config_attribute',
                            'description': f'Missing config attribute: {attr}',
                            'severity': 'low'
                        })
                        
            except ImportError as e:
                config_verification['issues_found'].append({
                    'type': 'config_module_error',
                    'description': f'Cannot import config module: {e}',
                    'severity': 'high'
                })
            
            # 3. Verificar directorios
            directories = {
                'data_dir': config.DATA_DIR,
                'thumbnails_dir': config.THUMBNAILS_PATH,
                'known_faces_dir': config.KNOWN_FACES_PATH
            }
            
            for dir_name, dir_path in directories.items():
                config_verification['directories'][dir_name]['path'] = str(dir_path)
                
                if dir_path.exists():
                    config_verification['directories'][dir_name]['exists'] = True
                    
                    # Verificar permisos de escritura
                    try:
                        test_file = dir_path / '.write_test'
                        test_file.write_text('test')
                        test_file.unlink()
                        config_verification['directories'][dir_name]['writable'] = True
                    except Exception:
                        config_verification['issues_found'].append({
                            'type': 'directory_not_writable',
                            'description': f'Directory not writable: {dir_path}',
                            'severity': 'medium'
                        })
                else:
                    config_verification['issues_found'].append({
                        'type': 'directory_missing',
                        'description': f'Directory missing: {dir_path}',
                        'severity': 'medium'
                    })
            
            # 4. Verificar archivos de base de datos
            db_files = {
                'character_database': Path('data/character_database.json'),
                'creator_mapping': Path('data/creator_character_mapping.json')
            }
            
            for db_name, db_path in db_files.items():
                config_verification['database_files'][db_name]['path'] = str(db_path)
                
                if db_path.exists():
                    config_verification['database_files'][db_name]['exists'] = True
                    try:
                        with open(db_path, 'r') as f:
                            json.load(f)
                        config_verification['database_files'][db_name]['readable'] = True
                    except Exception as e:
                        config_verification['issues_found'].append({
                            'type': 'database_file_corrupt',
                            'description': f'Database file corrupt: {db_path} - {e}',
                            'severity': 'high'
                        })
                else:
                    config_verification['issues_found'].append({
                        'type': 'database_file_missing',
                        'description': f'Database file missing: {db_path}',
                        'severity': 'medium'
                    })
            
            # Calcular puntuación de configuración
            total_issues = len(config_verification['issues_found'])
            high_issues = len([i for i in config_verification['issues_found'] if i['severity'] == 'high'])
            config_score = max(0, 100 - (high_issues * 20) - (total_issues * 5))
            
            logger.info(f"✅ Verificación de configuración completada:")
            logger.info(f"   🎯 Puntuación de configuración: {config_score}/100")
            logger.info(f"   ⚠️ {total_issues} problemas encontrados")
            
            return {
                'success': True,
                'config_verification': config_verification,
                'config_score': config_score,
                'total_issues': total_issues,
                'message': f'Verificación completada: {config_score}/100 puntos'
            }
            
        except Exception as e:
            logger.error(f"Error verificando configuración: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_integrity_report(self, include_details: bool = False) -> Dict[str, Any]:
        """
        📊 Generar reporte completo de integridad del sistema
        
        Args:
            include_details: incluir detalles extensos en el reporte
            
        Returns:
            Dict con reporte completo de integridad
        """
        logger.info("📊 Generando reporte completo de integridad...")
        
        try:
            start_time = time.time()
            
            # Ejecutar todas las verificaciones
            database_result = self.verify_database_integrity()
            video_files_result = self.verify_video_files()
            thumbnails_result = self.verify_thumbnails()
            config_result = self.verify_configuration()
            
            # Compilar reporte
            integrity_report = {
                'generated_at': datetime.now().isoformat(),
                'generation_time': time.time() - start_time,
                'overall_score': 0,
                'components': {
                    'database': {
                        'score': database_result.get('integrity_score', 0),
                        'status': 'healthy' if database_result.get('success', False) else 'error',
                        'issues': database_result.get('total_issues', 0),
                        'summary': database_result.get('message', '')
                    },
                    'video_files': {
                        'score': video_files_result.get('success_rate', 0),
                        'status': 'healthy' if video_files_result.get('success', False) else 'error',
                        'total_files': video_files_result.get('verification_results', {}).get('total_videos', 0),
                        'missing_files': video_files_result.get('verification_results', {}).get('missing_files', 0),
                        'summary': video_files_result.get('message', '')
                    },
                    'thumbnails': {
                        'score': thumbnails_result.get('thumbnail_coverage', 0),
                        'status': 'healthy' if thumbnails_result.get('success', False) else 'error',
                        'coverage': thumbnails_result.get('thumbnail_coverage', 0),
                        'summary': thumbnails_result.get('message', '')
                    },
                    'configuration': {
                        'score': config_result.get('config_score', 0),
                        'status': 'healthy' if config_result.get('success', False) else 'error',
                        'issues': config_result.get('total_issues', 0),
                        'summary': config_result.get('message', '')
                    }
                },
                'recommendations': []
            }
            
            # Calcular puntuación general
            scores = [
                integrity_report['components']['database']['score'],
                integrity_report['components']['video_files']['score'],
                integrity_report['components']['thumbnails']['score'],
                integrity_report['components']['configuration']['score']
            ]
            integrity_report['overall_score'] = sum(scores) / len(scores)
            
            # Generar recomendaciones
            if integrity_report['components']['database']['score'] < 80:
                integrity_report['recommendations'].append({
                    'priority': 'high',
                    'component': 'database',
                    'action': 'Ejecutar verificación de integridad con corrección automática',
                    'command': 'python main.py verify --fix-issues'
                })
            
            if integrity_report['components']['video_files']['score'] < 90:
                integrity_report['recommendations'].append({
                    'priority': 'medium',
                    'component': 'video_files',
                    'action': 'Revisar archivos de video faltantes y actualizar rutas',
                    'command': 'python main.py verify-files'
                })
            
            if integrity_report['components']['thumbnails']['score'] < 70:
                integrity_report['recommendations'].append({
                    'priority': 'medium',
                    'component': 'thumbnails',
                    'action': 'Regenerar thumbnails faltantes',
                    'command': 'python main.py populate-thumbnails --force'
                })
            
            if integrity_report['components']['configuration']['score'] < 80:
                integrity_report['recommendations'].append({
                    'priority': 'low',
                    'component': 'configuration',
                    'action': 'Revisar configuración del sistema',
                    'command': 'python verify_config.py'
                })
            
            # Incluir detalles si se solicita
            if include_details:
                integrity_report['detailed_results'] = {
                    'database': database_result,
                    'video_files': video_files_result,
                    'thumbnails': thumbnails_result,
                    'configuration': config_result
                }
            
            # Determinar estado general
            if integrity_report['overall_score'] >= 90:
                overall_status = 'excellent'
            elif integrity_report['overall_score'] >= 80:
                overall_status = 'good'
            elif integrity_report['overall_score'] >= 60:
                overall_status = 'fair'
            else:
                overall_status = 'poor'
            
            integrity_report['overall_status'] = overall_status
            
            # Mostrar reporte en consola
            logger.info(f"✅ Reporte de integridad generado:")
            logger.info(f"   🎯 Puntuación general: {integrity_report['overall_score']:.1f}/100 ({overall_status})")
            logger.info(f"   📊 BD: {integrity_report['components']['database']['score']:.1f}, Archivos: {integrity_report['components']['video_files']['score']:.1f}, Thumbnails: {integrity_report['components']['thumbnails']['score']:.1f}, Config: {integrity_report['components']['configuration']['score']:.1f}")
            
            # Mostrar recomendaciones
            if integrity_report['recommendations']:
                logger.info(f"\n💡 Recomendaciones ({len(integrity_report['recommendations'])}):") 
                for i, rec in enumerate(integrity_report['recommendations'], 1):
                    priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🔵'}.get(rec['priority'], '🟡')
                    logger.info(f"  {i}. {priority_icon} {rec['action']}")
                    logger.info(f"     Comando: {rec['command']}")
            else:
                logger.info("   🎉 No hay recomendaciones - Sistema en buen estado")
            
            # Exportar a JSON si se solicita
            if include_details:
                json_path = Path('integrity_report.json')
                try:
                    import json
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(integrity_report, f, indent=2, ensure_ascii=False)
                    logger.info(f"\n📄 Reporte detallado exportado: {json_path}")
                except Exception as e:
                    logger.warning(f"Error exportando reporte JSON: {e}")
            
            return {
                'success': True,
                'integrity_report': integrity_report,
                'overall_score': integrity_report['overall_score'],
                'overall_status': overall_status,
                'recommendations_count': len(integrity_report['recommendations']),
                'message': f'Reporte generado: {overall_status} ({integrity_report["overall_score"]:.1f}/100)' + (f', exportado a integrity_report.json' if include_details else '')
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte de integridad: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Métodos privados auxiliares
    
    def _fix_integrity_issues(self, issues: List[Dict[str, Any]]) -> int:
        """Intentar corregir problemas de integridad"""
        fixed_count = 0
        
        for issue in issues:
            try:
                issue_type = issue['type']
                
                if issue_type == 'missing_metadata':
                    # Intentar completar metadatos faltantes
                    video_id = issue.get('video_id')
                    if video_id:
                        video = self.db.get_video(video_id)
                        if video:
                            updates = {}
                            
                            # Completar título si falta
                            if not video.get('title'):
                                file_name = Path(video.get('file_path', '')).stem
                                updates['title'] = file_name
                            
                            # Completar creador si falta
                            if not video.get('creator_name'):
                                updates['creator_name'] = 'Unknown'
                            
                            # Completar plataforma si falta
                            if not video.get('platform'):
                                updates['platform'] = 'unknown'
                            
                            if updates:
                                self.db.update_video(video_id, updates)
                                fixed_count += 1
                                logger.info(f"✅ Corregido metadatos para video {video_id}")
                
                elif issue_type == 'missing_description_tiktok_instagram':
                    # Extraer descripción de bases de datos externas
                    video_id = issue.get('video_id')
                    platform = issue.get('platform')
                    file_path = issue.get('file_path')
                    
                    if video_id and platform and file_path:
                        description = self._extract_description_from_external_db(file_path, platform)
                        if description:
                            self.db.update_video(video_id, {'description': description})
                            fixed_count += 1
                            logger.info(f"✅ Corregida descripción para video {platform} {video_id}: {description[:50]}...")
                        else:
                            logger.warning(f"⚠️ No se pudo extraer descripción para video {video_id}")
                
                elif issue_type == 'orphaned_thumbnail':
                    # Eliminar thumbnails huérfanos
                    file_name = issue.get('file_name')
                    if file_name:
                        thumbnails_dir = config.THUMBNAILS_PATH
                        orphaned_file = thumbnails_dir / file_name
                        if orphaned_file.exists():
                            orphaned_file.unlink()
                            fixed_count += 1
                            logger.info(f"✅ Eliminado thumbnail huérfano: {file_name}")
                
                elif issue_type == 'duplicate_path':
                    # Marcar duplicados para revisión manual
                    video_ids = issue.get('video_ids', [])
                    if len(video_ids) > 1:
                        # Mantener el más reciente, marcar otros como duplicados
                        for video_id in video_ids[1:]:
                            self.db.update_video(video_id, {'edit_status': 'duplicate'})
                            fixed_count += 1
                            logger.info(f"✅ Marcado video {video_id} como duplicado")
                
            except Exception as e:
                logger.warning(f"Error corrigiendo problema {issue_type}: {e}")
                continue
        
        return fixed_count
    
    def _extract_description_from_external_db(self, file_path: str, platform: str) -> Optional[str]:
        """Extraer descripción desde bases de datos externas de 4K Apps"""
        try:
            from src.service_factory import get_external_sources
            
            # Usar ExternalSourcesManager para acceder a las BDs externas
            external_manager = get_external_sources()
            
            if platform == 'tiktok':
                # Buscar en BD de TikTok
                if not external_manager.tiktok_db_path or not external_manager.tiktok_db_path.exists():
                    return None
                
                conn = external_manager._get_connection(external_manager.tiktok_db_path)
                if not conn:
                    return None
                
                # Extraer nombre del archivo desde la ruta completa
                file_name = Path(file_path).name
                
                # Buscar por nombre de archivo en la BD de TikTok
                cursor = conn.execute("""
                    SELECT description 
                    FROM MediaItems 
                    WHERE relativePath LIKE ? 
                    LIMIT 1
                """, (f'%{file_name}',))
                
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0]:
                    return result[0].strip()
                    
            elif platform == 'instagram':
                # Buscar en BD de Instagram
                if not external_manager.instagram_db_path or not external_manager.instagram_db_path.exists():
                    return None
                
                conn = external_manager._get_connection(external_manager.instagram_db_path)
                if not conn:
                    return None
                
                # Extraer nombre del archivo desde la ruta completa
                file_name = Path(file_path).name
                
                # Buscar por nombre de archivo en la BD de Instagram
                cursor = conn.execute("""
                    SELECT title 
                    FROM photos 
                    WHERE file LIKE ? 
                    LIMIT 1
                """, (f'%{file_name}',))
                
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0]:
                    return result[0].strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo descripción desde BD externa para {platform}: {e}")
            return None
    
    def _display_verification_details(self, issues: List[Dict[str, Any]], fix_issues: bool = False) -> None:
        """Mostrar detalles de los problemas encontrados en verificación"""
        if not issues:
            return
            
        # Agrupar problemas por tipo
        issues_by_type = {}
        for issue in issues:
            issue_type = issue.get('type', 'unknown')
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        logger.info("\n🔍 Detalles de problemas encontrados:")
        
        # Mostrar cada tipo de problema
        for issue_type, type_issues in issues_by_type.items():
            count = len(type_issues)
            severity_icon = {
                'critical': '🔴',
                'high': '🟠', 
                'medium': '🟡',
                'low': '🔵'
            }.get(type_issues[0].get('severity', 'medium'), '🟡')
            
            type_name = {
                'missing_file': 'Archivos faltantes',
                'missing_thumbnail': 'Thumbnails faltantes',
                'orphaned_thumbnail': 'Thumbnails huérfanos',
                'missing_metadata': 'Metadatos faltantes',
                'duplicate_paths': 'Rutas duplicadas',
                'corrupted_file': 'Archivos corruptos'
            }.get(issue_type, issue_type.replace('_', ' ').title())
            
            logger.info(f"  {severity_icon} {type_name}: {count} problemas")
            
            # Mostrar algunos ejemplos (máximo 3 por tipo para no saturar)
            for i, issue in enumerate(type_issues[:3]):
                description = issue.get('description', 'Sin descripción')
                if 'video_id' in issue:
                    logger.info(f"    - Video ID {issue['video_id']}: {description}")
                else:
                    logger.info(f"    - {description}")
            
            # Si hay más, indicar el número
            if len(type_issues) > 3:
                logger.info(f"    ... y {len(type_issues) - 3} más")
        
        if not fix_issues:
            logger.info("\n💡 Para intentar corregir automáticamente, usa --fix-issues")


# Funciones de conveniencia para compatibilidad
def verify_database_integrity(fix_issues: bool = False) -> Dict[str, Any]:
    """Función de conveniencia para verificar integridad de BD"""
    ops = IntegrityOperations()
    return ops.verify_database_integrity(fix_issues)

def verify_video_files(video_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """Función de conveniencia para verificar archivos de video"""
    ops = IntegrityOperations()
    return ops.verify_video_files(video_ids)

def verify_thumbnails(regenerate_missing: bool = False) -> Dict[str, Any]:
    """Función de conveniencia para verificar thumbnails"""
    ops = IntegrityOperations()
    return ops.verify_thumbnails(regenerate_missing)

def verify_configuration() -> Dict[str, Any]:
    """Función de conveniencia para verificar configuración"""
    ops = IntegrityOperations()
    return ops.verify_configuration()

def generate_integrity_report(include_details: bool = False) -> Dict[str, Any]:
    """Función de conveniencia para generar reporte de integridad"""
    ops = IntegrityOperations()
    return ops.generate_integrity_report(include_details)