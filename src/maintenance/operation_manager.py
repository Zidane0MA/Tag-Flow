#!/usr/bin/env python3
"""
⚙️ Operation Manager - Fase 5
Middleware para manejo de operaciones de larga duración con notificaciones en tiempo real
"""

import time
import uuid
import json
import asyncio
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from pathlib import Path
import psutil

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos del proyecto
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.maintenance.websocket_manager import get_websocket_manager, send_operation_progress, send_operation_complete, send_notification


class OperationStatus(Enum):
    """Estados de operación"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class OperationPriority(Enum):
    """Prioridades de operación"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class OperationProgress:
    """Progreso de operación con notificaciones en tiempo real"""
    operation_id: str
    operation_type: str
    status: OperationStatus
    priority: OperationPriority = OperationPriority.NORMAL
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
    pause_requested: bool = False
    
    # Métricas de rendimiento
    items_per_second: float = 0.0
    estimated_completion: Optional[datetime] = None
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    # Notificaciones
    last_notification_time: datetime = field(default_factory=datetime.now)
    notification_interval: float = 1.0  # segundos
    
    @property
    def duration(self) -> float:
        """Duración de la operación en segundos"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def is_active(self) -> bool:
        """Verificar si la operación está activa"""
        return self.status in [OperationStatus.PENDING, OperationStatus.RUNNING, OperationStatus.PAUSED]
    
    @property
    def is_completed(self) -> bool:
        """Verificar si la operación está completada"""
        return self.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]
    
    def update_metrics(self):
        """Actualizar métricas de rendimiento"""
        try:
            # Calcular items por segundo
            if self.duration > 0:
                self.items_per_second = self.processed_items / self.duration
            
            # Estimar tiempo de finalización
            if self.items_per_second > 0 and self.total_items > 0:
                remaining_items = self.total_items - self.processed_items
                remaining_seconds = remaining_items / self.items_per_second
                self.estimated_completion = datetime.now() + timedelta(seconds=remaining_seconds)
            
            # Obtener uso de memoria y CPU del proceso actual
            try:
                process = psutil.Process()
                self.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                self.cpu_usage_percent = process.cpu_percent()
            except:
                pass
                
        except Exception as e:
            logger.debug(f"Error actualizando métricas: {e}")
    
    def should_notify(self) -> bool:
        """Verificar si debe enviar notificación"""
        now = datetime.now()
        return (now - self.last_notification_time).total_seconds() >= self.notification_interval
    
    def mark_notified(self):
        """Marcar como notificado"""
        self.last_notification_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para JSON"""
        return {
            'operation_id': self.operation_id,
            'operation_type': self.operation_type,
            'status': self.status.value,
            'priority': self.priority.value,
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
            'cancellation_requested': self.cancellation_requested,
            'pause_requested': self.pause_requested,
            'items_per_second': self.items_per_second,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent
        }


class OperationManager:
    """
    ⚙️ Gestor de operaciones con notificaciones en tiempo real
    
    Características:
    - Operaciones asíncronas con WebSockets
    - Progreso en tiempo real
    - Cancelación y pausa
    - Métricas de rendimiento
    - Priorización de operaciones
    - Persistencia de estado
    """
    
    def __init__(self, max_concurrent_operations: int = 3):
        self.operations: Dict[str, OperationProgress] = {}
        self.active_futures: Dict[str, Future] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_operations)
        self.lock = threading.Lock()
        self.notification_thread = None
        self.running = False
        
        # Configuración
        self.max_concurrent_operations = max_concurrent_operations
        self.operation_timeout = 3600  # 1 hora por defecto
        self.cleanup_interval = 300  # 5 minutos
        
        # Estadísticas
        self.stats = {
            'total_operations': 0,
            'completed_operations': 0,
            'failed_operations': 0,
            'cancelled_operations': 0,
            'average_duration': 0.0,
            'start_time': datetime.now()
        }
        
        # Iniciar sistema de notificaciones
        self.start_notification_system()
    
    def start_notification_system(self):
        """Iniciar sistema de notificaciones en tiempo real"""
        self.running = True
        self.notification_thread = threading.Thread(target=self._notification_worker, daemon=True)
        self.notification_thread.start()
        logger.info("⚙️ Sistema de notificaciones iniciado")
    
    def stop_notification_system(self):
        """Detener sistema de notificaciones"""
        self.running = False
        if self.notification_thread:
            self.notification_thread.join(timeout=5)
        logger.info("⚙️ Sistema de notificaciones detenido")
    
    def _notification_worker(self):
        """Worker para enviar notificaciones periódicas"""
        while self.running:
            try:
                with self.lock:
                    for operation in self.operations.values():
                        if operation.is_active and operation.should_notify():
                            operation.update_metrics()
                            
                            # Enviar notificación de progreso
                            send_operation_progress(
                                operation.operation_id,
                                operation.to_dict()
                            )
                            
                            operation.mark_notified()
                
                # Limpiar operaciones antiguas
                self._cleanup_old_operations()
                
                time.sleep(0.5)  # Verificar cada 500ms
                
            except Exception as e:
                logger.error(f"Error en notification worker: {e}")
                time.sleep(1)
    
    def create_operation(self, operation_type: str, 
                        priority: OperationPriority = OperationPriority.NORMAL,
                        total_items: int = 0,
                        notification_interval: float = 1.0) -> str:
        """
        Crear nueva operación
        
        Args:
            operation_type: Tipo de operación
            priority: Prioridad de la operación
            total_items: Número total de items a procesar
            notification_interval: Intervalo de notificación en segundos
            
        Returns:
            operation_id: ID único de la operación
        """
        operation_id = str(uuid.uuid4())
        
        operation = OperationProgress(
            operation_id=operation_id,
            operation_type=operation_type,
            status=OperationStatus.PENDING,
            priority=priority,
            total_items=total_items,
            notification_interval=notification_interval
        )
        
        with self.lock:
            self.operations[operation_id] = operation
            self.stats['total_operations'] += 1
        
        # Notificar creación
        send_notification(
            f"Nueva operación creada: {operation_type}",
            "info",
            {'operation_id': operation_id, 'type': operation_type}
        )
        
        logger.info(f"⚙️ Operación creada: {operation_id} ({operation_type})")
        return operation_id
    
    def start_operation(self, operation_id: str, 
                       operation_func: Callable,
                       *args, **kwargs) -> bool:
        """
        Iniciar operación
        
        Args:
            operation_id: ID de la operación
            operation_func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
            
        Returns:
            bool: True si se pudo iniciar, False si no
        """
        with self.lock:
            operation = self.operations.get(operation_id)
            if not operation or operation.status != OperationStatus.PENDING:
                return False
            
            # Verificar límite de operaciones concurrentes
            active_operations = len([op for op in self.operations.values() 
                                   if op.status == OperationStatus.RUNNING])
            
            if active_operations >= self.max_concurrent_operations:
                logger.warning(f"Límite de operaciones concurrentes alcanzado: {active_operations}")
                return False
            
            # Cambiar estado
            operation.status = OperationStatus.RUNNING
            operation.current_step = "Iniciando operación..."
            
            # Crear wrapper para la función
            def operation_wrapper():
                return self._execute_operation(operation_id, operation_func, *args, **kwargs)
            
            # Ejecutar en thread pool
            future = self.executor.submit(operation_wrapper)
            self.active_futures[operation_id] = future
            
            logger.info(f"⚙️ Operación iniciada: {operation_id}")
            return True
    
    def _execute_operation(self, operation_id: str, operation_func: Callable, *args, **kwargs):
        """Ejecutar operación con manejo de errores"""
        operation = self.operations[operation_id]
        
        try:
            # Crear callback de progreso
            def progress_callback(processed: int, total: int = None, current_item: str = "", 
                                successful: int = None, failed: int = None):
                with self.lock:
                    if operation.cancellation_requested:
                        raise InterruptedError("Operación cancelada por el usuario")
                    
                    if operation.pause_requested:
                        operation.status = OperationStatus.PAUSED
                        while operation.pause_requested and not operation.cancellation_requested:
                            time.sleep(0.1)
                        operation.status = OperationStatus.RUNNING
                    
                    # Actualizar progreso
                    operation.processed_items = processed
                    if total is not None:
                        operation.total_items = total
                    if current_item:
                        operation.current_step = current_item
                    if successful is not None:
                        operation.successful_items = successful
                    if failed is not None:
                        operation.failed_items = failed
                    
                    # Calcular porcentaje
                    if operation.total_items > 0:
                        operation.progress_percentage = (processed / operation.total_items) * 100
            
            # Ejecutar función con callback
            if 'progress_callback' in kwargs:
                kwargs['progress_callback'] = progress_callback
            else:
                # Intentar agregar callback como parámetro posicional
                result = operation_func(*args, progress_callback=progress_callback, **kwargs)
            
            # Operación completada exitosamente
            with self.lock:
                operation.status = OperationStatus.COMPLETED
                operation.end_time = datetime.now()
                operation.progress_percentage = 100.0
                operation.current_step = "Operación completada"
                operation.result = result if isinstance(result, dict) else {'result': result}
                
                self.stats['completed_operations'] += 1
                self._update_average_duration()
            
            # Notificar completación
            send_operation_complete(operation_id, operation.to_dict())
            send_notification(
                f"Operación completada: {operation.operation_type}",
                "success",
                {'operation_id': operation_id, 'duration': operation.duration}
            )
            
            logger.info(f"✅ Operación completada: {operation_id} ({operation.duration:.2f}s)")
            return result
            
        except InterruptedError as e:
            # Operación cancelada
            with self.lock:
                operation.status = OperationStatus.CANCELLED
                operation.end_time = datetime.now()
                operation.error_message = str(e)
                operation.current_step = "Operación cancelada"
                
                self.stats['cancelled_operations'] += 1
            
            send_notification(
                f"Operación cancelada: {operation.operation_type}",
                "warning",
                {'operation_id': operation_id, 'reason': str(e)}
            )
            
            logger.info(f"❌ Operación cancelada: {operation_id}")
            return None
            
        except Exception as e:
            # Operación falló
            with self.lock:
                operation.status = OperationStatus.FAILED
                operation.end_time = datetime.now()
                operation.error_message = str(e)
                operation.current_step = "Operación falló"
                
                self.stats['failed_operations'] += 1
            
            send_notification(
                f"Operación falló: {operation.operation_type}",
                "error",
                {'operation_id': operation_id, 'error': str(e)}
            )
            
            logger.error(f"❌ Operación falló: {operation_id} - {e}")
            return None
            
        finally:
            # Limpiar future
            if operation_id in self.active_futures:
                del self.active_futures[operation_id]
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancelar operación"""
        with self.lock:
            operation = self.operations.get(operation_id)
            if not operation or not operation.is_active:
                return False
            
            operation.cancellation_requested = True
            operation.current_step = "Cancelación solicitada..."
            
            # Intentar cancelar Future
            future = self.active_futures.get(operation_id)
            if future and not future.done():
                future.cancel()
            
            logger.info(f"❌ Cancelación solicitada: {operation_id}")
            return True
    
    def pause_operation(self, operation_id: str) -> bool:
        """Pausar operación"""
        with self.lock:
            operation = self.operations.get(operation_id)
            if not operation or operation.status != OperationStatus.RUNNING:
                return False
            
            operation.pause_requested = True
            logger.info(f"⏸️ Pausa solicitada: {operation_id}")
            return True
    
    def resume_operation(self, operation_id: str) -> bool:
        """Reanudar operación"""
        with self.lock:
            operation = self.operations.get(operation_id)
            if not operation or operation.status != OperationStatus.PAUSED:
                return False
            
            operation.pause_requested = False
            logger.info(f"▶️ Operación reanudada: {operation_id}")
            return True
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de operación"""
        with self.lock:
            operation = self.operations.get(operation_id)
            if operation:
                operation.update_metrics()
                return operation.to_dict()
        return None
    
    def get_all_operations(self) -> List[Dict[str, Any]]:
        """Obtener todas las operaciones"""
        with self.lock:
            operations = []
            for operation in self.operations.values():
                operation.update_metrics()
                operations.append(operation.to_dict())
            return operations
    
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """Obtener operaciones activas"""
        with self.lock:
            operations = []
            for operation in self.operations.values():
                if operation.is_active:
                    operation.update_metrics()
                    operations.append(operation.to_dict())
            return operations
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del manager"""
        with self.lock:
            return {
                **self.stats,
                'active_operations': len([op for op in self.operations.values() if op.is_active]),
                'max_concurrent_operations': self.max_concurrent_operations,
                'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds()
            }
    
    def _update_average_duration(self):
        """Actualizar duración promedio"""
        completed_operations = [op for op in self.operations.values() if op.status == OperationStatus.COMPLETED]
        if completed_operations:
            total_duration = sum(op.duration for op in completed_operations)
            self.stats['average_duration'] = total_duration / len(completed_operations)
    
    def _cleanup_old_operations(self):
        """Limpiar operaciones antiguas"""
        try:
            cutoff_time = datetime.now() - timedelta(seconds=self.cleanup_interval)
            
            with self.lock:
                operations_to_remove = []
                for op_id, operation in self.operations.items():
                    if (operation.is_completed and 
                        operation.end_time and 
                        operation.end_time < cutoff_time):
                        operations_to_remove.append(op_id)
                
                for op_id in operations_to_remove:
                    del self.operations[op_id]
                    if op_id in self.active_futures:
                        del self.active_futures[op_id]
                
                if operations_to_remove:
                    logger.debug(f"🧹 Limpiadas {len(operations_to_remove)} operaciones antiguas")
                    
        except Exception as e:
            logger.error(f"Error limpiando operaciones antiguas: {e}")
    
    def shutdown(self):
        """Apagar el manager"""
        logger.info("⚙️ Apagando Operation Manager...")
        
        # Detener notificaciones
        self.stop_notification_system()
        
        # Cancelar operaciones activas
        with self.lock:
            for operation_id, operation in self.operations.items():
                if operation.is_active:
                    self.cancel_operation(operation_id)
        
        # Apagar executor
        self.executor.shutdown(wait=True, timeout=30)
        
        logger.info("⚙️ Operation Manager apagado")


# Instancia global
_operation_manager = None

def get_operation_manager() -> OperationManager:
    """Obtener instancia singleton del Operation Manager"""
    global _operation_manager
    if _operation_manager is None:
        _operation_manager = OperationManager()
    return _operation_manager


# Funciones de conveniencia
def create_operation(operation_type: str, 
                    priority: OperationPriority = OperationPriority.NORMAL,
                    total_items: int = 0,
                    notification_interval: float = 1.0) -> str:
    """Crear nueva operación"""
    return get_operation_manager().create_operation(
        operation_type, priority, total_items, notification_interval
    )


def start_operation(operation_id: str, operation_func: Callable, *args, **kwargs) -> bool:
    """Iniciar operación"""
    return get_operation_manager().start_operation(operation_id, operation_func, *args, **kwargs)


def cancel_operation(operation_id: str) -> bool:
    """Cancelar operación"""
    return get_operation_manager().cancel_operation(operation_id)


def get_operation_status(operation_id: str) -> Optional[Dict[str, Any]]:
    """Obtener estado de operación"""
    return get_operation_manager().get_operation_status(operation_id)