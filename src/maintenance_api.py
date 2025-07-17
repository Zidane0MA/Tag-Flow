#!/usr/bin/env python3
"""
🔧 Maintenance API - Fase 2
API programática especializada para operaciones de mantenimiento desde la app web

Características:
- Operaciones asíncronas con tracking de progreso
- Cancelación de operaciones en curso
- Sistema de salud del sistema
- Reporting en tiempo real
- Timeout y manejo de errores granular
"""

import os
import time
import uuid
import threading
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from concurrent.futures import ThreadPoolExecutor, Future
import psutil

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos del proyecto
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from src.database import Database
from src.maintenance.thumbnail_ops import ThumbnailOperations
from src.maintenance.database_ops import DatabaseOperations


class OperationStatus(Enum):
    """Estados de operación"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OperationType(Enum):
    """Tipos de operación"""
    REGENERATE_THUMBNAILS = "regenerate_thumbnails"
    POPULATE_THUMBNAILS = "populate_thumbnails"
    CLEAN_THUMBNAILS = "clean_thumbnails"
    POPULATE_DATABASE = "populate_database"
    OPTIMIZE_DATABASE = "optimize_database"
    CLEAR_DATABASE = "clear_database"
    BACKUP_DATABASE = "backup_database"
    RESTORE_DATABASE = "restore_database"


@dataclass
class OperationProgress:
    """Progreso de operación"""
    operation_id: str
    operation_type: OperationType
    status: OperationStatus
    progress_percentage: float = 0.0
    current_step: str = ""
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    cancellation_requested: bool = False
    
    @property
    def duration(self) -> float:
        """Duración de la operación en segundos"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def is_active(self) -> bool:
        """Verificar si la operación está activa"""
        return self.status in [OperationStatus.PENDING, OperationStatus.RUNNING]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para JSON"""
        return {
            'operation_id': self.operation_id,
            'operation_type': self.operation_type.value,
            'status': self.status.value,
            'progress_percentage': self.progress_percentage,
            'current_step': self.current_step,
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'successful_items': self.successful_items,
            'failed_items': self.failed_items,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'error_message': self.error_message,
            'result': self.result,
            'cancellation_requested': self.cancellation_requested
        }


class MaintenanceAPI:
    """
    🔧 API programática para operaciones de mantenimiento desde la app web
    
    Características:
    - Operaciones asíncronas con tracking de progreso
    - Cancelación de operaciones en curso
    - Sistema de salud del sistema
    - Reporting en tiempo real
    """
    
    def __init__(self):
        self.db = Database()
        self.thumbnail_ops = ThumbnailOperations()
        self.database_ops = DatabaseOperations()
        self.operations: Dict[str, OperationProgress] = {}
        self.active_futures: Dict[str, Future] = {}
        self.executor = ThreadPoolExecutor(max_workers=2)  # Limitar concurrencia
        self.lock = threading.Lock()
        
        # Limpiar operaciones antiguas al inicializar
        self._cleanup_old_operations()
    
    def regenerate_thumbnails_bulk(self, video_ids: List[int], force: bool = False) -> str:
        """
        🖼️ Regenerar thumbnails para videos específicos de forma asíncrona
        
        Args:
            video_ids: Lista de IDs de videos
            force: regenerar thumbnails existentes también
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = str(uuid.uuid4())
        
        operation = OperationProgress(
            operation_id=operation_id,
            operation_type=OperationType.REGENERATE_THUMBNAILS,
            status=OperationStatus.PENDING,
            total_items=len(video_ids),
            current_step="Iniciando regeneración de thumbnails..."
        )
        
        with self.lock:
            self.operations[operation_id] = operation
        
        # Ejecutar operación asíncrona
        future = self.executor.submit(self._regenerate_thumbnails_async, operation_id, video_ids, force)
        self.active_futures[operation_id] = future
        
        logger.info(f"🖼️ Operación de regeneración de thumbnails iniciada: {operation_id}")
        return operation_id
    
    def populate_thumbnails_bulk(self, platform: Optional[str] = None, limit: Optional[int] = None, force: bool = False) -> str:
        """
        📊 Poblar thumbnails de forma asíncrona
        
        Args:
            platform: plataforma específica o None para todas
            limit: número máximo de thumbnails a generar
            force: regenerar thumbnails existentes
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = str(uuid.uuid4())
        
        operation = OperationProgress(
            operation_id=operation_id,
            operation_type=OperationType.POPULATE_THUMBNAILS,
            status=OperationStatus.PENDING,
            current_step="Iniciando población de thumbnails..."
        )
        
        with self.lock:
            self.operations[operation_id] = operation
        
        # Ejecutar operación asíncrona
        future = self.executor.submit(self._populate_thumbnails_async, operation_id, platform, limit, force)
        self.active_futures[operation_id] = future
        
        logger.info(f"📊 Operación de población de thumbnails iniciada: {operation_id}")
        return operation_id
    
    def clean_thumbnails_bulk(self, force: bool = False) -> str:
        """
        🧹 Limpiar thumbnails huérfanos de forma asíncrona
        
        Args:
            force: eliminar sin confirmación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = str(uuid.uuid4())
        
        operation = OperationProgress(
            operation_id=operation_id,
            operation_type=OperationType.CLEAN_THUMBNAILS,
            status=OperationStatus.PENDING,
            current_step="Iniciando limpieza de thumbnails..."
        )
        
        with self.lock:
            self.operations[operation_id] = operation
        
        # Ejecutar operación asíncrona
        future = self.executor.submit(self._clean_thumbnails_async, operation_id, force)
        self.active_futures[operation_id] = future
        
        logger.info(f"🧹 Operación de limpieza de thumbnails iniciada: {operation_id}")
        return operation_id
    
    def populate_database_bulk(self, source: str = 'all', platform: Optional[str] = None, 
                              limit: Optional[int] = None, force: bool = False) -> str:
        """
        🗃️ Poblar base de datos de forma asíncrona
        
        Args:
            source: 'db', 'organized', 'all' - fuente de datos
            platform: plataforma específica o None para todas
            limit: número máximo de videos a importar
            force: forzar reimportación de videos existentes
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = str(uuid.uuid4())
        
        operation = OperationProgress(
            operation_id=operation_id,
            operation_type=OperationType.POPULATE_DATABASE,
            status=OperationStatus.PENDING,
            current_step="Iniciando población de base de datos..."
        )
        
        with self.lock:
            self.operations[operation_id] = operation
        
        # Ejecutar operación asíncrona
        future = self.executor.submit(self._populate_database_async, operation_id, source, platform, limit, force)
        self.active_futures[operation_id] = future
        
        logger.info(f"🗃️ Operación de población de BD iniciada: {operation_id}")
        return operation_id
    
    def optimize_database_bulk(self) -> str:
        """
        🔧 Optimizar base de datos de forma asíncrona
        
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = str(uuid.uuid4())
        
        operation = OperationProgress(
            operation_id=operation_id,
            operation_type=OperationType.OPTIMIZE_DATABASE,
            status=OperationStatus.PENDING,
            current_step="Iniciando optimización de base de datos..."
        )
        
        with self.lock:
            self.operations[operation_id] = operation
        
        # Ejecutar operación asíncrona
        future = self.executor.submit(self._optimize_database_async, operation_id)
        self.active_futures[operation_id] = future
        
        logger.info(f"🔧 Operación de optimización de BD iniciada: {operation_id}")
        return operation_id
    
    def clear_database_bulk(self, platform: Optional[str] = None, force: bool = False) -> str:
        """
        🗑️ Limpiar base de datos de forma asíncrona
        
        Args:
            platform: plataforma específica o None para todas
            force: forzar eliminación sin confirmación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = str(uuid.uuid4())
        
        operation = OperationProgress(
            operation_id=operation_id,
            operation_type=OperationType.CLEAR_DATABASE,
            status=OperationStatus.PENDING,
            current_step="Iniciando limpieza de base de datos..."
        )
        
        with self.lock:
            self.operations[operation_id] = operation
        
        # Ejecutar operación asíncrona
        future = self.executor.submit(self._clear_database_async, operation_id, platform, force)
        self.active_futures[operation_id] = future
        
        logger.info(f"🗑️ Operación de limpieza de BD iniciada: {operation_id}")
        return operation_id
    
    def backup_database_bulk(self, backup_path: Optional[str] = None) -> str:
        """
        💾 Crear backup de base de datos de forma asíncrona
        
        Args:
            backup_path: ruta específica del backup o None para automática
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = str(uuid.uuid4())
        
        operation = OperationProgress(
            operation_id=operation_id,
            operation_type=OperationType.BACKUP_DATABASE,
            status=OperationStatus.PENDING,
            current_step="Iniciando backup de base de datos..."
        )
        
        with self.lock:
            self.operations[operation_id] = operation
        
        # Ejecutar operación asíncrona
        future = self.executor.submit(self._backup_database_async, operation_id, backup_path)
        self.active_futures[operation_id] = future
        
        logger.info(f"💾 Operación de backup de BD iniciada: {operation_id}")
        return operation_id
    
    def get_operation_progress(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        📊 Obtener progreso de operación en curso
        
        Args:
            operation_id: ID de la operación
            
        Returns:
            Dict con progreso de la operación o None si no existe
        """
        with self.lock:
            operation = self.operations.get(operation_id)
            if operation:
                return operation.to_dict()
        return None
    
    def cancel_operation(self, operation_id: str) -> bool:
        """
        ❌ Cancelar operación en curso
        
        Args:
            operation_id: ID de la operación
            
        Returns:
            True si se pudo cancelar, False en caso contrario
        """
        with self.lock:
            operation = self.operations.get(operation_id)
            if operation and operation.is_active:
                operation.cancellation_requested = True
                operation.current_step = "Cancelación solicitada..."
                logger.info(f"❌ Cancelación solicitada para operación: {operation_id}")
                
                # Intentar cancelar el Future si existe
                future = self.active_futures.get(operation_id)
                if future and not future.done():
                    future.cancel()
                    
                return True
        return False
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        💚 Estado general del sistema
        
        Returns:
            Dict con información de salud del sistema
        """
        try:
            # Información del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Información de la base de datos
            db_stats = self._get_database_stats()
            
            # Información de thumbnails
            thumbnail_stats = self.thumbnail_ops.get_thumbnail_stats()
            
            # Operaciones activas
            active_operations = len([op for op in self.operations.values() if op.is_active])
            
            # Información de archivos
            config_path = Path(config.config.BASE_PATH if hasattr(config.config, 'BASE_PATH') else '.')
            total_videos = len(list(config_path.glob('**/*.mp4'))) if config_path.exists() else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_total_gb': memory.total / (1024**3),
                    'memory_used_gb': memory.used / (1024**3),
                    'memory_percent': memory.percent,
                    'disk_total_gb': disk.total / (1024**3),
                    'disk_used_gb': disk.used / (1024**3),
                    'disk_percent': (disk.used / disk.total) * 100
                },
                'database': db_stats,
                'thumbnails': thumbnail_stats,
                'operations': {
                    'active_operations': active_operations,
                    'total_operations': len(self.operations),
                    'executor_workers': self.executor._max_workers,
                    'executor_active': len(self.active_futures)
                },
                'files': {
                    'total_videos': total_videos,
                    'config_path': str(config_path)
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo salud del sistema: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'status': 'error'
            }
    
    def get_all_operations(self) -> List[Dict[str, Any]]:
        """
        📋 Obtener todas las operaciones
        
        Returns:
            Lista de todas las operaciones
        """
        with self.lock:
            return [op.to_dict() for op in self.operations.values()]
    
    def cleanup_completed_operations(self, max_age_hours: int = 24) -> int:
        """
        🧹 Limpiar operaciones completadas antiguas
        
        Args:
            max_age_hours: máximo tiempo en horas para mantener operaciones
            
        Returns:
            Número de operaciones limpiadas
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned = 0
        
        with self.lock:
            operations_to_remove = []
            for op_id, operation in self.operations.items():
                if not operation.is_active and operation.start_time < cutoff_time:
                    operations_to_remove.append(op_id)
            
            for op_id in operations_to_remove:
                del self.operations[op_id]
                if op_id in self.active_futures:
                    del self.active_futures[op_id]
                cleaned += 1
        
        if cleaned > 0:
            logger.info(f"🧹 Limpiadas {cleaned} operaciones antiguas")
        
        return cleaned
    
    # Métodos privados
    
    def _regenerate_thumbnails_async(self, operation_id: str, video_ids: List[int], force: bool):
        """Regenerar thumbnails de forma asíncrona"""
        operation = self.operations[operation_id]
        
        try:
            operation.status = OperationStatus.RUNNING
            operation.current_step = "Obteniendo información de videos..."
            
            # Crear callback para progreso
            def progress_callback(processed: int, total: int, current_item: str):
                if operation.cancellation_requested:
                    raise Exception("Operación cancelada por el usuario")
                
                operation.processed_items = processed
                operation.total_items = total
                operation.progress_percentage = (processed / total) * 100 if total > 0 else 0
                operation.current_step = f"Procesando: {current_item}"
            
            # Ejecutar regeneración con callback de progreso
            result = self.thumbnail_ops.regenerate_thumbnails_by_ids(video_ids, force)
            
            # Actualizar operación con resultado
            operation.successful_items = result.get('successful', 0)
            operation.failed_items = result.get('failed', 0)
            operation.result = result
            
            if result['success']:
                operation.status = OperationStatus.COMPLETED
                operation.current_step = "Regeneración completada exitosamente"
                operation.progress_percentage = 100.0
            else:
                operation.status = OperationStatus.FAILED
                operation.error_message = result.get('error', 'Error desconocido')
                operation.current_step = "Regeneración falló"
            
        except Exception as e:
            operation.status = OperationStatus.FAILED if not operation.cancellation_requested else OperationStatus.CANCELLED
            operation.error_message = str(e)
            operation.current_step = "Error en regeneración" if not operation.cancellation_requested else "Operación cancelada"
            logger.error(f"Error en regeneración de thumbnails {operation_id}: {e}")
        
        finally:
            operation.end_time = datetime.now()
            # Limpiar Future
            if operation_id in self.active_futures:
                del self.active_futures[operation_id]
    
    def _populate_thumbnails_async(self, operation_id: str, platform: Optional[str], limit: Optional[int], force: bool):
        """Poblar thumbnails de forma asíncrona"""
        operation = self.operations[operation_id]
        
        try:
            operation.status = OperationStatus.RUNNING
            operation.current_step = "Iniciando población de thumbnails..."
            
            # Ejecutar población
            result = self.thumbnail_ops.populate_thumbnails(platform, limit, force)
            
            # Actualizar operación con resultado
            operation.successful_items = result.get('successful', 0)
            operation.failed_items = result.get('failed', 0)
            operation.total_items = result.get('total_videos', 0)
            operation.processed_items = operation.successful_items + operation.failed_items
            operation.result = result
            
            if result['success']:
                operation.status = OperationStatus.COMPLETED
                operation.current_step = "Población completada exitosamente"
                operation.progress_percentage = 100.0
            else:
                operation.status = OperationStatus.FAILED
                operation.error_message = result.get('error', 'Error desconocido')
                operation.current_step = "Población falló"
            
        except Exception as e:
            operation.status = OperationStatus.FAILED if not operation.cancellation_requested else OperationStatus.CANCELLED
            operation.error_message = str(e)
            operation.current_step = "Error en población" if not operation.cancellation_requested else "Operación cancelada"
            logger.error(f"Error en población de thumbnails {operation_id}: {e}")
        
        finally:
            operation.end_time = datetime.now()
            if operation_id in self.active_futures:
                del self.active_futures[operation_id]
    
    def _clean_thumbnails_async(self, operation_id: str, force: bool):
        """Limpiar thumbnails de forma asíncrona"""
        operation = self.operations[operation_id]
        
        try:
            operation.status = OperationStatus.RUNNING
            operation.current_step = "Analizando thumbnails huérfanos..."
            
            # Ejecutar limpieza
            result = self.thumbnail_ops.clean_thumbnails(force)
            
            # Actualizar operación con resultado
            operation.successful_items = result.get('deleted_count', 0)
            operation.total_items = result.get('orphaned_count', 0)
            operation.processed_items = operation.total_items
            operation.result = result
            
            if result['success']:
                operation.status = OperationStatus.COMPLETED
                operation.current_step = "Limpieza completada exitosamente"
                operation.progress_percentage = 100.0
            else:
                operation.status = OperationStatus.FAILED
                operation.error_message = result.get('error', 'Error desconocido')
                operation.current_step = "Limpieza falló"
            
        except Exception as e:
            operation.status = OperationStatus.FAILED if not operation.cancellation_requested else OperationStatus.CANCELLED
            operation.error_message = str(e)
            operation.current_step = "Error en limpieza" if not operation.cancellation_requested else "Operación cancelada"
            logger.error(f"Error en limpieza de thumbnails {operation_id}: {e}")
        
        finally:
            operation.end_time = datetime.now()
            if operation_id in self.active_futures:
                del self.active_futures[operation_id]
    
    def _populate_database_async(self, operation_id: str, source: str, platform: Optional[str], 
                                limit: Optional[int], force: bool):
        """Poblar base de datos de forma asíncrona"""
        operation = self.operations[operation_id]
        
        try:
            operation.status = OperationStatus.RUNNING
            operation.current_step = "Iniciando población de base de datos..."
            
            # Crear callback para progreso
            def progress_callback(processed: int, total: int, current_item: str):
                if operation.cancellation_requested:
                    raise Exception("Operación cancelada por el usuario")
                
                operation.processed_items = processed
                operation.total_items = total
                operation.progress_percentage = (processed / total) * 100 if total > 0 else 0
                operation.current_step = f"Procesando: {current_item}"
            
            # Ejecutar población con callback de progreso
            result = self.database_ops.populate_database(source, platform, limit, force, progress_callback=progress_callback)
            
            # Actualizar operación con resultado
            operation.successful_items = result.get('imported', 0)
            operation.failed_items = result.get('errors', 0)
            operation.total_items = result.get('total_found', 0)
            operation.processed_items = operation.successful_items + operation.failed_items
            operation.result = result
            
            if result['success']:
                operation.status = OperationStatus.COMPLETED
                operation.current_step = "Población completada exitosamente"
                operation.progress_percentage = 100.0
            else:
                operation.status = OperationStatus.FAILED
                operation.error_message = result.get('error', 'Error desconocido')
                operation.current_step = "Población falló"
            
        except Exception as e:
            operation.status = OperationStatus.FAILED if not operation.cancellation_requested else OperationStatus.CANCELLED
            operation.error_message = str(e)
            operation.current_step = "Error en población" if not operation.cancellation_requested else "Operación cancelada"
            logger.error(f"Error en población de BD {operation_id}: {e}")
        
        finally:
            operation.end_time = datetime.now()
            if operation_id in self.active_futures:
                del self.active_futures[operation_id]
    
    def _optimize_database_async(self, operation_id: str):
        """Optimizar base de datos de forma asíncrona"""
        operation = self.operations[operation_id]
        
        try:
            operation.status = OperationStatus.RUNNING
            operation.current_step = "Optimizando base de datos..."
            operation.progress_percentage = 50.0
            
            # Ejecutar optimización
            result = self.database_ops.optimize_database()
            
            # Actualizar operación con resultado
            operation.result = result
            operation.total_items = 1
            operation.processed_items = 1
            
            if result['success']:
                operation.status = OperationStatus.COMPLETED
                operation.current_step = "Optimización completada exitosamente"
                operation.progress_percentage = 100.0
                operation.successful_items = 1
            else:
                operation.status = OperationStatus.FAILED
                operation.error_message = result.get('error', 'Error desconocido')
                operation.current_step = "Optimización falló"
                operation.failed_items = 1
            
        except Exception as e:
            operation.status = OperationStatus.FAILED if not operation.cancellation_requested else OperationStatus.CANCELLED
            operation.error_message = str(e)
            operation.current_step = "Error en optimización" if not operation.cancellation_requested else "Operación cancelada"
            logger.error(f"Error en optimización de BD {operation_id}: {e}")
        
        finally:
            operation.end_time = datetime.now()
            if operation_id in self.active_futures:
                del self.active_futures[operation_id]
    
    def _clear_database_async(self, operation_id: str, platform: Optional[str], force: bool):
        """Limpiar base de datos de forma asíncrona"""
        operation = self.operations[operation_id]
        
        try:
            operation.status = OperationStatus.RUNNING
            operation.current_step = "Analizando videos a eliminar..."
            
            # Ejecutar limpieza
            result = self.database_ops.clear_database(platform, force)
            
            # Actualizar operación con resultado
            operation.successful_items = result.get('deleted', 0)
            operation.total_items = result.get('videos_found', 0)
            operation.processed_items = operation.total_items
            operation.result = result
            
            if result['success']:
                operation.status = OperationStatus.COMPLETED
                operation.current_step = "Limpieza completada exitosamente"
                operation.progress_percentage = 100.0
            else:
                operation.status = OperationStatus.FAILED
                operation.error_message = result.get('error', 'Error desconocido')
                operation.current_step = "Limpieza falló"
            
        except Exception as e:
            operation.status = OperationStatus.FAILED if not operation.cancellation_requested else OperationStatus.CANCELLED
            operation.error_message = str(e)
            operation.current_step = "Error en limpieza" if not operation.cancellation_requested else "Operación cancelada"
            logger.error(f"Error en limpieza de BD {operation_id}: {e}")
        
        finally:
            operation.end_time = datetime.now()
            if operation_id in self.active_futures:
                del self.active_futures[operation_id]
    
    def _backup_database_async(self, operation_id: str, backup_path: Optional[str]):
        """Crear backup de base de datos de forma asíncrona"""
        operation = self.operations[operation_id]
        
        try:
            operation.status = OperationStatus.RUNNING
            operation.current_step = "Creando backup de base de datos..."
            operation.progress_percentage = 50.0
            
            # Ejecutar backup
            result = self.database_ops.backup_database(backup_path)
            
            # Actualizar operación con resultado
            operation.result = result
            operation.total_items = 1
            operation.processed_items = 1
            
            if result['success']:
                operation.status = OperationStatus.COMPLETED
                operation.current_step = "Backup completado exitosamente"
                operation.progress_percentage = 100.0
                operation.successful_items = 1
            else:
                operation.status = OperationStatus.FAILED
                operation.error_message = result.get('error', 'Error desconocido')
                operation.current_step = "Backup falló"
                operation.failed_items = 1
            
        except Exception as e:
            operation.status = OperationStatus.FAILED if not operation.cancellation_requested else OperationStatus.CANCELLED
            operation.error_message = str(e)
            operation.current_step = "Error en backup" if not operation.cancellation_requested else "Operación cancelada"
            logger.error(f"Error en backup de BD {operation_id}: {e}")
        
        finally:
            operation.end_time = datetime.now()
            if operation_id in self.active_futures:
                del self.active_futures[operation_id]
    
    def _get_database_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la base de datos"""
        try:
            with self.db.get_connection() as conn:
                # Contar videos por plataforma
                cursor = conn.execute("""
                    SELECT platform, COUNT(*) as count 
                    FROM videos 
                    GROUP BY platform
                """)
                platform_counts = dict(cursor.fetchall())
                
                # Contar videos con thumbnails
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(thumbnail_path) as with_thumbnails
                    FROM videos
                """)
                thumbnail_stats = dict(cursor.fetchone())
                
                # Tamaño de la base de datos
                cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                return {
                    'total_videos': sum(platform_counts.values()),
                    'platform_counts': platform_counts,
                    'videos_with_thumbnails': thumbnail_stats['with_thumbnails'],
                    'videos_without_thumbnails': thumbnail_stats['total'] - thumbnail_stats['with_thumbnails'],
                    'database_size_mb': db_size / (1024 * 1024),
                    'status': 'healthy'
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de BD: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _cleanup_old_operations(self):
        """Limpiar operaciones antiguas al inicializar"""
        try:
            self.cleanup_completed_operations(max_age_hours=24)
        except Exception as e:
            logger.warning(f"Error limpiando operaciones antiguas: {e}")
    
    def __del__(self):
        """Limpiar recursos al destruir"""
        try:
            self.executor.shutdown(wait=True, timeout=30)
        except Exception as e:
            logger.warning(f"Error cerrando executor: {e}")


# Instancia global (singleton)
_maintenance_api_instance = None

def get_maintenance_api() -> MaintenanceAPI:
    """Obtener instancia singleton de MaintenanceAPI"""
    global _maintenance_api_instance
    if _maintenance_api_instance is None:
        _maintenance_api_instance = MaintenanceAPI()
    return _maintenance_api_instance


# Funciones de conveniencia
def start_regenerate_thumbnails(video_ids: List[int], force: bool = False) -> str:
    """Iniciar regeneración de thumbnails asíncrona"""
    return get_maintenance_api().regenerate_thumbnails_bulk(video_ids, force)

def start_populate_thumbnails(platform: Optional[str] = None, limit: Optional[int] = None, force: bool = False) -> str:
    """Iniciar población de thumbnails asíncrona"""
    return get_maintenance_api().populate_thumbnails_bulk(platform, limit, force)

def start_clean_thumbnails(force: bool = False) -> str:
    """Iniciar limpieza de thumbnails asíncrona"""
    return get_maintenance_api().clean_thumbnails_bulk(force)

def get_operation_status(operation_id: str) -> Optional[Dict[str, Any]]:
    """Obtener estado de operación"""
    return get_maintenance_api().get_operation_progress(operation_id)

def cancel_operation(operation_id: str) -> bool:
    """Cancelar operación"""
    return get_maintenance_api().cancel_operation(operation_id)

def get_system_health() -> Dict[str, Any]:
    """Obtener salud del sistema"""
    return get_maintenance_api().get_system_health()