#!/usr/bin/env python3
"""
💾 Backup Operations Module
Módulo especializado para operaciones de backup y restore extraído de maintenance.py
"""

import os
import json
import shutil
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import zipfile
import tempfile

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos del proyecto
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from src.database import DatabaseManager


class BackupOperations:
    """
    💾 Operaciones especializadas de backup y restore
    
    Funcionalidades:
    - Backup completo del sistema
    - Restore desde backup
    - Verificación de integridad
    - Limpieza de backups antiguos
    - Backup incremental
    """
    
    def __init__(self, backup_dir: Optional[Path] = None):
        self.db = DatabaseManager()
        self.backup_dir = backup_dir or Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, include_thumbnails: bool = True, 
                     thumbnail_limit: int = 100,
                     compress: bool = True) -> Dict[str, Any]:
        """
        💾 Crear backup completo del sistema
        
        Args:
            include_thumbnails: incluir thumbnails en el backup
            thumbnail_limit: límite de thumbnails para ahorrar espacio
            compress: comprimir el backup en ZIP
            
        Returns:
            Dict con resultados del backup
        """
        start_time = time.time()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"tag_flow_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        logger.info(f"💾 Creando backup: {backup_path}")
        
        try:
            backup_path.mkdir(exist_ok=True)
            
            backup_info = {
                'created': timestamp,
                'version': '2.0.0',
                'components': {},
                'stats': {}
            }
            
            # 1. Backup de la base de datos
            db_backed_up = self._backup_database(backup_path, backup_info)
            
            # 2. Backup de thumbnails (opcional)
            if include_thumbnails:
                thumbnails_backed_up = self._backup_thumbnails(backup_path, thumbnail_limit, backup_info)
            else:
                thumbnails_backed_up = 0
                backup_info['components']['thumbnails'] = False
            
            # 3. Backup de configuración
            config_backed_up = self._backup_configuration(backup_path, backup_info)
            
            # 4. Backup de caras conocidas
            faces_backed_up = self._backup_known_faces(backup_path, backup_info)
            
            # 5. Backup de archivos adicionales
            additional_files = self._backup_additional_files(backup_path, backup_info)
            
            # 6. Crear manifiesto del backup
            backup_info['stats'] = {
                'database_backed_up': db_backed_up,
                'thumbnails_count': thumbnails_backed_up,
                'config_backed_up': config_backed_up,
                'faces_backed_up': faces_backed_up,
                'additional_files': additional_files
            }
            
            manifest_path = backup_path / 'manifest.json'
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            # 7. Comprimir backup si se solicita
            final_path = backup_path
            if compress:
                final_path = self._compress_backup(backup_path)
            
            duration = time.time() - start_time
            backup_size = self._get_backup_size(final_path)
            
            logger.info(f"✅ Backup creado en {duration:.2f}s")
            logger.info(f"   📁 Ruta: {final_path}")
            logger.info(f"   📊 Tamaño: {backup_size / 1024 / 1024:.1f} MB")
            logger.info(f"   📋 Componentes: BD={db_backed_up}, Thumbnails={thumbnails_backed_up}, Config={config_backed_up}")
            
            return {
                'success': True,
                'backup_path': str(final_path),
                'backup_size_mb': backup_size / 1024 / 1024,
                'duration': duration,
                'components': backup_info['components'],
                'stats': backup_info['stats'],
                'compressed': compress,
                'message': f'Backup creado exitosamente: {final_path.name}'
            }
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            # Limpiar en caso de error
            if backup_path.exists():
                shutil.rmtree(backup_path, ignore_errors=True)
            
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    def restore_backup(self, backup_path: str, 
                      components: Optional[List[str]] = None,
                      force: bool = False) -> Dict[str, Any]:
        """
        🔄 Restaurar desde backup
        
        Args:
            backup_path: ruta del backup
            components: lista de componentes a restaurar o None para todos
            force: forzar restauración sin confirmación
            
        Returns:
            Dict con resultados de la restauración
        """
        start_time = time.time()
        backup_path = Path(backup_path)
        
        logger.info(f"🔄 Restaurando desde backup: {backup_path}")
        
        try:
            # Verificar que el backup existe
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': f'Backup no encontrado: {backup_path}',
                    'duration': time.time() - start_time
                }
            
            # Extraer backup si es un ZIP
            temp_dir = None
            if backup_path.suffix == '.zip':
                temp_dir = Path(tempfile.mkdtemp())
                with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                restore_path = temp_dir
            else:
                restore_path = backup_path
            
            # Leer manifiesto
            manifest_path = restore_path / 'manifest.json'
            if not manifest_path.exists():
                return {
                    'success': False,
                    'error': 'Backup inválido: falta manifest.json',
                    'duration': time.time() - start_time
                }
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Determinar componentes a restaurar
            if components is None:
                components = list(manifest.get('components', {}).keys())
            
            logger.info(f"📋 Componentes a restaurar: {components}")
            
            if not force:
                # Crear backup de seguridad antes de restaurar
                safety_backup = self.create_backup(include_thumbnails=False, compress=True)
                if safety_backup['success']:
                    logger.info(f"💾 Backup de seguridad creado: {safety_backup['backup_path']}")
            
            # Restaurar componentes
            restored_components = {}
            
            if 'database' in components:
                restored_components['database'] = self._restore_database(restore_path, manifest)
            
            if 'thumbnails' in components:
                restored_components['thumbnails'] = self._restore_thumbnails(restore_path, manifest)
            
            if 'configuration' in components:
                restored_components['configuration'] = self._restore_configuration(restore_path, manifest)
            
            if 'known_faces' in components:
                restored_components['known_faces'] = self._restore_known_faces(restore_path, manifest)
            
            # Limpiar directorio temporal
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            
            duration = time.time() - start_time
            successful_components = [k for k, v in restored_components.items() if v]
            
            logger.info(f"✅ Restauración completada en {duration:.2f}s")
            logger.info(f"   📋 Componentes restaurados: {successful_components}")
            
            return {
                'success': True,
                'duration': duration,
                'components_restored': successful_components,
                'components_failed': [k for k, v in restored_components.items() if not v],
                'backup_version': manifest.get('version', 'unknown'),
                'backup_created': manifest.get('created', 'unknown'),
                'message': f'Restauración completada: {len(successful_components)} componentes'
            }
            
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    def list_backups(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        📋 Listar backups disponibles
        
        Args:
            limit: número máximo de backups a mostrar
            
        Returns:
            Dict con lista de backups
        """
        try:
            backups = []
            
            # Buscar backups en el directorio
            for backup_file in self.backup_dir.glob('tag_flow_backup_*.zip'):
                try:
                    backup_info = self._get_backup_info(backup_file)
                    if backup_info:
                        backups.append(backup_info)
                except Exception as e:
                    logger.warning(f"Error leyendo backup {backup_file}: {e}")
            
            # Ordenar por fecha (más reciente primero)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            # Aplicar límite si se especifica
            if limit:
                backups = backups[:limit]
            
            return {
                'success': True,
                'backups': backups,
                'total_backups': len(backups),
                'backup_dir': str(self.backup_dir)
            }
            
        except Exception as e:
            logger.error(f"Error listando backups: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_old_backups(self, keep_count: int = 5, 
                           max_age_days: int = 30) -> Dict[str, Any]:
        """
        🧹 Limpiar backups antiguos
        
        Args:
            keep_count: número de backups recientes a mantener
            max_age_days: edad máxima en días
            
        Returns:
            Dict con resultados de la limpieza
        """
        try:
            backups_info = self.list_backups()
            if not backups_info['success']:
                return backups_info
            
            backups = backups_info['backups']
            
            # Determinar backups a eliminar
            to_delete = []
            
            # Por edad
            cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 3600)
            for backup in backups:
                backup_date = datetime.fromisoformat(backup['created']).timestamp()
                if backup_date < cutoff_date:
                    to_delete.append(backup)
            
            # Por cantidad (mantener los más recientes)
            if len(backups) > keep_count:
                to_delete.extend(backups[keep_count:])
            
            # Eliminar duplicados
            to_delete = list({backup['path']: backup for backup in to_delete}.values())
            
            # Eliminar backups
            deleted_count = 0
            deleted_size = 0
            
            for backup in to_delete:
                try:
                    backup_path = Path(backup['path'])
                    if backup_path.exists():
                        deleted_size += backup_path.stat().st_size
                        backup_path.unlink()
                        deleted_count += 1
                        logger.info(f"🗑️  Eliminado backup: {backup_path.name}")
                except Exception as e:
                    logger.warning(f"Error eliminando backup {backup['path']}: {e}")
            
            logger.info(f"✅ Limpieza completada: {deleted_count} backups eliminados ({deleted_size / 1024 / 1024:.1f} MB)")
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'deleted_size_mb': deleted_size / 1024 / 1024,
                'remaining_backups': len(backups) - deleted_count,
                'message': f'Eliminados {deleted_count} backups antiguos'
            }
            
        except Exception as e:
            logger.error(f"Error limpiando backups: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_backup(self, backup_path: str) -> Dict[str, Any]:
        """
        🔍 Verificar integridad de backup
        
        Args:
            backup_path: ruta del backup a verificar
            
        Returns:
            Dict con resultados de la verificación
        """
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': f'Backup no encontrado: {backup_path}'
                }
            
            verification_results = {
                'file_exists': True,
                'can_extract': False,
                'has_manifest': False,
                'manifest_valid': False,
                'components_exist': {},
                'database_valid': False
            }
            
            # Verificar si es ZIP válido
            if backup_path.suffix == '.zip':
                try:
                    with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                        zip_ref.testzip()
                        verification_results['can_extract'] = True
                        
                        # Verificar archivos en el ZIP
                        file_list = zip_ref.namelist()
                        verification_results['has_manifest'] = any('manifest.json' in f for f in file_list)
                        
                except zipfile.BadZipFile:
                    verification_results['can_extract'] = False
            
            # Leer manifiesto si existe
            if verification_results['has_manifest']:
                try:
                    temp_dir = Path(tempfile.mkdtemp())
                    with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    manifest_path = temp_dir / 'manifest.json'
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    
                    verification_results['manifest_valid'] = True
                    
                    # Verificar componentes
                    components = manifest.get('components', {})
                    for component, exists in components.items():
                        if exists:
                            component_path = temp_dir / self._get_component_path(component)
                            verification_results['components_exist'][component] = component_path.exists()
                    
                    # Verificar BD si existe
                    if verification_results['components_exist'].get('database', False):
                        db_path = temp_dir / 'videos.db'
                        verification_results['database_valid'] = self._verify_database(db_path)
                    
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
                except Exception as e:
                    logger.warning(f"Error verificando manifiesto: {e}")
            
            # Determinar resultado final
            is_valid = (
                verification_results['file_exists'] and
                verification_results['can_extract'] and
                verification_results['has_manifest'] and
                verification_results['manifest_valid']
            )
            
            return {
                'success': True,
                'is_valid': is_valid,
                'verification_results': verification_results,
                'backup_path': str(backup_path),
                'message': 'Backup válido' if is_valid else 'Backup inválido o corrupto'
            }
            
        except Exception as e:
            logger.error(f"Error verificando backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Métodos privados auxiliares
    
    def _backup_database(self, backup_path: Path, backup_info: Dict) -> bool:
        """Backup de la base de datos"""
        try:
            db_source = Path(config.DATABASE_PATH if hasattr(config, 'DATABASE_PATH') else 'data/videos.db')
            if db_source.exists():
                shutil.copy2(db_source, backup_path / 'videos.db')
                backup_info['components']['database'] = True
                backup_info['database_size'] = db_source.stat().st_size
                logger.info("✓ Base de datos respaldada")
                return True
            else:
                backup_info['components']['database'] = False
                logger.warning("Base de datos no encontrada")
                return False
        except Exception as e:
            logger.error(f"Error respaldando BD: {e}")
            backup_info['components']['database'] = False
            return False
    
    def _backup_thumbnails(self, backup_path: Path, limit: int, backup_info: Dict) -> int:
        """Backup de thumbnails"""
        try:
            thumbnails_source = Path(config.THUMBNAILS_PATH if hasattr(config, 'THUMBNAILS_PATH') else 'data/thumbnails')
            if not thumbnails_source.exists():
                backup_info['components']['thumbnails'] = False
                return 0
            
            thumbnails_backup = backup_path / 'thumbnails'
            thumbnails_backup.mkdir(exist_ok=True)
            
            thumbnail_count = 0
            for thumb in thumbnails_source.glob('*.jpg'):
                if thumbnail_count < limit:
                    shutil.copy2(thumb, thumbnails_backup)
                    thumbnail_count += 1
                else:
                    break
            
            backup_info['components']['thumbnails'] = thumbnail_count > 0
            logger.info(f"✓ {thumbnail_count} thumbnails respaldados")
            return thumbnail_count
            
        except Exception as e:
            logger.error(f"Error respaldando thumbnails: {e}")
            backup_info['components']['thumbnails'] = False
            return 0
    
    def _backup_configuration(self, backup_path: Path, backup_info: Dict) -> bool:
        """Backup de configuración"""
        try:
            config_files = ['.env', 'config.py', 'CLAUDE.md']
            config_backed_up = False
            
            for config_file in config_files:
                source = Path(config_file)
                if source.exists():
                    shutil.copy2(source, backup_path / config_file)
                    config_backed_up = True
            
            backup_info['components']['configuration'] = config_backed_up
            if config_backed_up:
                logger.info("✓ Configuración respaldada")
            return config_backed_up
            
        except Exception as e:
            logger.error(f"Error respaldando configuración: {e}")
            backup_info['components']['configuration'] = False
            return False
    
    def _backup_known_faces(self, backup_path: Path, backup_info: Dict) -> bool:
        """Backup de caras conocidas"""
        try:
            faces_source = Path(config.KNOWN_FACES_PATH if hasattr(config, 'KNOWN_FACES_PATH') else 'caras_conocidas')
            if faces_source.exists():
                shutil.copytree(faces_source, backup_path / 'caras_conocidas')
                backup_info['components']['known_faces'] = True
                logger.info("✓ Caras conocidas respaldadas")
                return True
            else:
                backup_info['components']['known_faces'] = False
                return False
        except Exception as e:
            logger.error(f"Error respaldando caras conocidas: {e}")
            backup_info['components']['known_faces'] = False
            return False
    
    def _backup_additional_files(self, backup_path: Path, backup_info: Dict) -> int:
        """Backup de archivos adicionales"""
        try:
            additional_files = ['requirements.txt', 'README.md', 'PROYECTO_ESTADO.md']
            files_backed_up = 0
            
            for file_name in additional_files:
                source = Path(file_name)
                if source.exists():
                    shutil.copy2(source, backup_path / file_name)
                    files_backed_up += 1
            
            backup_info['components']['additional_files'] = files_backed_up
            if files_backed_up > 0:
                logger.info(f"✓ {files_backed_up} archivos adicionales respaldados")
            return files_backed_up
            
        except Exception as e:
            logger.error(f"Error respaldando archivos adicionales: {e}")
            backup_info['components']['additional_files'] = 0
            return 0
    
    def _compress_backup(self, backup_path: Path) -> Path:
        """Comprimir backup en ZIP"""
        try:
            zip_path = backup_path.with_suffix('.zip')
            shutil.make_archive(str(backup_path), 'zip', str(backup_path))
            shutil.rmtree(backup_path)  # Eliminar carpeta temporal
            return zip_path
        except Exception as e:
            logger.error(f"Error comprimiendo backup: {e}")
            return backup_path
    
    def _get_backup_size(self, backup_path: Path) -> int:
        """Obtener tamaño del backup"""
        try:
            if backup_path.is_file():
                return backup_path.stat().st_size
            elif backup_path.is_dir():
                return sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            return 0
        except Exception:
            return 0
    
    def _get_backup_info(self, backup_path: Path) -> Optional[Dict]:
        """Obtener información de un backup"""
        try:
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                    if 'manifest.json' in zip_ref.namelist():
                        with zip_ref.open('manifest.json') as f:
                            manifest = json.load(f)
                        
                        return {
                            'path': str(backup_path),
                            'name': backup_path.name,
                            'size_mb': backup_path.stat().st_size / 1024 / 1024,
                            'created': manifest.get('created', 'unknown'),
                            'version': manifest.get('version', 'unknown'),
                            'components': manifest.get('components', {}),
                            'compressed': True
                        }
            return None
        except Exception:
            return None
    
    def _get_component_path(self, component: str) -> str:
        """Obtener ruta del componente en el backup"""
        paths = {
            'database': 'videos.db',
            'thumbnails': 'thumbnails',
            'configuration': '.env',
            'known_faces': 'caras_conocidas'
        }
        return paths.get(component, component)
    
    def _verify_database(self, db_path: Path) -> bool:
        """Verificar que la base de datos es válida"""
        try:
            import sqlite3
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                return len(tables) > 0
        except Exception:
            return False
    
    def _restore_database(self, restore_path: Path, manifest: Dict) -> bool:
        """Restaurar base de datos"""
        try:
            if not manifest.get('components', {}).get('database', False):
                return False
            
            source = restore_path / 'videos.db'
            target = Path(config.DATABASE_PATH if hasattr(config, 'DATABASE_PATH') else 'data/videos.db')
            
            if source.exists():
                # Crear backup del actual
                if target.exists():
                    backup_current = target.with_suffix('.db.backup')
                    shutil.copy2(target, backup_current)
                
                # Restaurar
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                logger.info("✓ Base de datos restaurada")
                return True
            return False
        except Exception as e:
            logger.error(f"Error restaurando BD: {e}")
            return False
    
    def _restore_thumbnails(self, restore_path: Path, manifest: Dict) -> bool:
        """Restaurar thumbnails"""
        try:
            if not manifest.get('components', {}).get('thumbnails', False):
                return False
            
            source = restore_path / 'thumbnails'
            target = Path(config.THUMBNAILS_PATH if hasattr(config, 'THUMBNAILS_PATH') else 'data/thumbnails')
            
            if source.exists():
                target.mkdir(parents=True, exist_ok=True)
                for thumb in source.glob('*.jpg'):
                    shutil.copy2(thumb, target)
                logger.info("✓ Thumbnails restaurados")
                return True
            return False
        except Exception as e:
            logger.error(f"Error restaurando thumbnails: {e}")
            return False
    
    def _restore_configuration(self, restore_path: Path, manifest: Dict) -> bool:
        """Restaurar configuración"""
        try:
            if not manifest.get('components', {}).get('configuration', False):
                return False
            
            config_files = ['.env', 'config.py', 'CLAUDE.md']
            restored = False
            
            for config_file in config_files:
                source = restore_path / config_file
                if source.exists():
                    shutil.copy2(source, config_file)
                    restored = True
            
            if restored:
                logger.info("✓ Configuración restaurada")
            return restored
        except Exception as e:
            logger.error(f"Error restaurando configuración: {e}")
            return False
    
    def _restore_known_faces(self, restore_path: Path, manifest: Dict) -> bool:
        """Restaurar caras conocidas"""
        try:
            if not manifest.get('components', {}).get('known_faces', False):
                return False
            
            source = restore_path / 'caras_conocidas'
            target = Path(config.KNOWN_FACES_PATH if hasattr(config, 'KNOWN_FACES_PATH') else 'caras_conocidas')
            
            if source.exists():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(source, target)
                logger.info("✓ Caras conocidas restauradas")
                return True
            return False
        except Exception as e:
            logger.error(f"Error restaurando caras conocidas: {e}")
            return False


# Funciones de conveniencia para compatibilidad
def create_backup(include_thumbnails: bool = True, thumbnail_limit: int = 100, compress: bool = True) -> Dict[str, Any]:
    """Función de conveniencia para crear backup"""
    ops = BackupOperations()
    return ops.create_backup(include_thumbnails, thumbnail_limit, compress)

def restore_backup(backup_path: str, components: Optional[List[str]] = None, force: bool = False) -> Dict[str, Any]:
    """Función de conveniencia para restaurar backup"""
    ops = BackupOperations()
    return ops.restore_backup(backup_path, components, force)

def list_backups(limit: Optional[int] = None) -> Dict[str, Any]:
    """Función de conveniencia para listar backups"""
    ops = BackupOperations()
    return ops.list_backups(limit)

def cleanup_old_backups(keep_count: int = 5, max_age_days: int = 30) -> Dict[str, Any]:
    """Función de conveniencia para limpiar backups antiguos"""
    ops = BackupOperations()
    return ops.cleanup_old_backups(keep_count, max_age_days)

def verify_backup(backup_path: str) -> Dict[str, Any]:
    """Función de conveniencia para verificar backup"""
    ops = BackupOperations()
    return ops.verify_backup(backup_path)