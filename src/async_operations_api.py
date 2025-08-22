#!/usr/bin/env python3
"""
🔄 Async Operations API
API unificada para operaciones asíncronas con WebSockets y notificaciones en tiempo real
"""

import os
import time
import uuid
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import json
# Imports opcionales
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos del proyecto
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from src.maintenance.thumbnail_ops import ThumbnailOperations
from src.maintenance.database_ops import DatabaseOperations
from src.maintenance.backup_ops import BackupOperations
from src.maintenance.character_ops import CharacterOperations
from src.maintenance.integrity_ops import IntegrityOperations
from src.core.operation_manager import get_operation_manager, OperationPriority
from src.core.websocket_manager import get_websocket_manager, send_notification

class AsyncOperationsAPI:
    """
    🔄 API unificada para operaciones asíncronas del sistema
    
    Características:
    - Procesamiento de videos con tracking en tiempo real
    - Operaciones de mantenimiento con WebSockets
    - Notificaciones en tiempo real
    - Progreso detallado con métricas
    - Cancelación y pausa de operaciones
    - Priorización de operaciones
    - Persistencia de estado
    """
    
    def __init__(self):
        self._db = None
        self.thumbnail_ops = ThumbnailOperations()
        self.database_ops = DatabaseOperations()
        self.backup_ops = BackupOperations()
        self.character_ops = CharacterOperations()
        self.integrity_ops = IntegrityOperations()
        
        # Managers
        self.operation_manager = get_operation_manager()
        self.websocket_manager = get_websocket_manager()
        
        logger.info("🔄 Async Operations API inicializada")
    
    @property
    def db(self):
        """Lazy initialization of Database via ServiceFactory"""
        if self._db is None:
            from src.service_factory import get_database
            self._db = get_database()
        return self._db
    
    # === PROCESAMIENTO DE VIDEOS ===
    def process_videos_async(self, limit: Optional[int] = None, 
                           platform: Optional[str] = None,
                           source: str = 'all',
                           priority: OperationPriority = OperationPriority.HIGH) -> str:
        """
        🎬 Procesamiento de videos con tracking en tiempo real
        
        Args:
            limit: Límite de videos a procesar
            platform: Plataforma específica (youtube, tiktok, etc.)
            source: Fuente de datos ('db', 'organized', 'all')
            priority: Prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="process_videos",
            priority=priority,
            total_items=limit or 100,  # Estimación inicial
            notification_interval=2.0  # Actualizar cada 2 segundos
        )
        
        def process_worker():
            try:
                # Notificar inicio
                self.websocket_manager.send_operation_update(
                    operation_id=operation_id,
                    status="running",
                    message="🎬 Iniciando procesamiento de videos...",
                    progress=0
                )
                
                # Importar video analyzer de forma lazy
                from src.core.video_analyzer import VideoAnalyzer
                analyzer = VideoAnalyzer()
                
                # Obtener videos a procesar
                videos_to_process = analyzer.get_videos_to_process(
                    limit=limit,
                    platform=platform,
                    source=source
                )
                
                # Actualizar total real
                total_videos = len(videos_to_process)
                self.operation_manager.update_operation(
                    operation_id, 
                    total_items=total_videos
                )
                
                # Procesar videos uno por uno
                for i, video_path in enumerate(videos_to_process):
                    if self.operation_manager.is_cancelled(operation_id):
                        break
                        
                    # Procesar video individual
                    try:
                        result = analyzer.process_single_video(video_path)
                        progress = ((i + 1) / total_videos) * 100
                        
                        self.websocket_manager.send_operation_update(
                            operation_id=operation_id,
                            status="running",
                            message=f"📹 Procesado: {video_path.name}",
                            progress=progress,
                            processed_count=i + 1
                        )
                        
                    except Exception as e:
                        logger.error(f"Error procesando {video_path}: {e}")
                        self.websocket_manager.send_operation_update(
                            operation_id=operation_id,
                            status="running", 
                            message=f"❌ Error en {video_path.name}: {str(e)}",
                            progress=((i + 1) / total_videos) * 100
                        )
                
                # Finalizar operación
                self.operation_manager.complete_operation(
                    operation_id,
                    result={"processed": total_videos, "success": True}
                )
                
                self.websocket_manager.send_operation_update(
                    operation_id=operation_id,
                    status="completed",
                    message=f"✅ Procesamiento completado: {total_videos} videos",
                    progress=100
                )
                
            except Exception as e:
                logger.error(f"Error en procesamiento de videos: {e}")
                self.operation_manager.fail_operation(operation_id, str(e))
                self.websocket_manager.send_operation_update(
                    operation_id=operation_id,
                    status="failed",
                    message=f"❌ Error: {str(e)}",
                    progress=0
                )
        
        # Ejecutar en thread separado
        import threading
        thread = threading.Thread(target=process_worker, daemon=True)
        thread.start()
        
        return operation_id

    def analyze_videos_async(self, video_ids: List[int],
                           force: bool = False,
                           priority: OperationPriority = OperationPriority.MEDIUM) -> str:
        """
        🔍 Reanálisis de videos específicos con tracking en tiempo real
        
        Args:
            video_ids: Lista de IDs de videos a reanalizar
            force: Forzar reanálisis sobrescribiendo datos existentes
            priority: Prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="analyze_videos",
            priority=priority,
            total_items=len(video_ids),
            notification_interval=1.0
        )
        
        def analyze_worker():
            try:
                self.websocket_manager.send_operation_update(
                    operation_id=operation_id,
                    status="running",
                    message="🔍 Iniciando reanálisis de videos...",
                    progress=0
                )
                
                from src.core.reanalysis_engine import ReanalysisEngine
                engine = ReanalysisEngine()
                
                for i, video_id in enumerate(video_ids):
                    if self.operation_manager.is_cancelled(operation_id):
                        break
                        
                    try:
                        result = engine.reanalyze_video(video_id, force=force)
                        progress = ((i + 1) / len(video_ids)) * 100
                        
                        self.websocket_manager.send_operation_update(
                            operation_id=operation_id,
                            status="running",
                            message=f"🔍 Reanalizado video ID: {video_id}",
                            progress=progress,
                            processed_count=i + 1
                        )
                        
                    except Exception as e:
                        logger.error(f"Error analizando video {video_id}: {e}")
                
                self.operation_manager.complete_operation(
                    operation_id,
                    result={"analyzed": len(video_ids), "success": True}
                )
                
                self.websocket_manager.send_operation_update(
                    operation_id=operation_id,
                    status="completed",
                    message=f"✅ Reanálisis completado: {len(video_ids)} videos",
                    progress=100
                )
                
            except Exception as e:
                logger.error(f"Error en reanálisis: {e}")
                self.operation_manager.fail_operation(operation_id, str(e))
                self.websocket_manager.send_operation_update(
                    operation_id=operation_id,
                    status="failed",
                    message=f"❌ Error: {str(e)}",
                    progress=0
                )
        
        import threading
        thread = threading.Thread(target=analyze_worker, daemon=True)
        thread.start()
        
        return operation_id

    # === OPERACIONES DE MANTENIMIENTO ===
    # Operaciones de thumbnails con WebSockets
    def regenerate_thumbnails_bulk(self, video_ids: List[int], 
                                  force: bool = False,
                                  priority: OperationPriority = OperationPriority.NORMAL) -> str:
        """
        🖼️ Regenerar thumbnails para videos específicos con notificaciones en tiempo real
        
        Args:
            video_ids: Lista de IDs de videos
            force: regenerar thumbnails existentes también
            priority: prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="regenerate_thumbnails",
            priority=priority,
            total_items=len(video_ids),
            notification_interval=0.5  # Actualizar cada 500ms
        )
        
        # Función wrapper para la operación
        def regenerate_operation(progress_callback=None):
            return self.thumbnail_ops.regenerate_thumbnails_by_ids(
                video_ids=video_ids,
                force=force,
                progress_callback=progress_callback
            )
        
        # Iniciar operación
        success = self.operation_manager.start_operation(
            operation_id,
            regenerate_operation
        )
        
        if success:
            send_notification(
                f"Regeneración de thumbnails iniciada: {len(video_ids)} videos",
                "info",
                {
                    'operation_id': operation_id,
                    'video_count': len(video_ids),
                    'force': force
                }
            )
        
        return operation_id
    
    def populate_thumbnails_bulk(self, platform: Optional[str] = None, 
                               limit: Optional[int] = None, 
                               force: bool = False,
                               priority: OperationPriority = OperationPriority.NORMAL) -> str:
        """
        📊 Poblar thumbnails de forma asíncrona con notificaciones
        
        Args:
            platform: plataforma específica o None para todas
            limit: número máximo de thumbnails a generar
            force: regenerar thumbnails existentes
            priority: prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="populate_thumbnails",
            priority=priority,
            total_items=limit or 0,
            notification_interval=1.0
        )
        
        def populate_operation(progress_callback=None):
            return self.thumbnail_ops.populate_thumbnails(
                platform=platform,
                limit=limit,
                force=force,
                progress_callback=progress_callback
            )
        
        success = self.operation_manager.start_operation(
            operation_id,
            populate_operation
        )
        
        if success:
            send_notification(
                f"Población de thumbnails iniciada: {platform or 'todas las plataformas'}",
                "info",
                {
                    'operation_id': operation_id,
                    'platform': platform,
                    'limit': limit
                }
            )
        
        return operation_id
    
    def clean_thumbnails_bulk(self, force: bool = False,
                             priority: OperationPriority = OperationPriority.LOW) -> str:
        """
        🧹 Limpiar thumbnails huérfanos de forma asíncrona
        
        Args:
            force: eliminar sin confirmación
            priority: prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="clean_thumbnails",
            priority=priority,
            notification_interval=2.0
        )
        
        def clean_operation(progress_callback=None):
            return self.thumbnail_ops.clean_thumbnails(
                force=force,
                progress_callback=progress_callback
            )
        
        success = self.operation_manager.start_operation(
            operation_id,
            clean_operation
        )
        
        if success:
            send_notification(
                "Limpieza de thumbnails iniciada",
                "info",
                {'operation_id': operation_id, 'force': force}
            )
        
        return operation_id
    
    # Operaciones de base de datos
    def populate_database_bulk(self, source: str = 'all', 
                             platform: Optional[str] = None,
                             limit: Optional[int] = None, 
                             force: bool = False,
                             priority: OperationPriority = OperationPriority.HIGH) -> str:
        """
        🗃️ Poblar base de datos de forma asíncrona
        
        Args:
            source: 'db', 'organized', 'all' - fuente de datos
            platform: plataforma específica o None para todas
            limit: número máximo de videos a importar
            force: forzar reimportación de videos existentes
            priority: prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="populate_database",
            priority=priority,
            total_items=limit or 0,
            notification_interval=1.0
        )
        
        def populate_operation(progress_callback=None):
            return self.database_ops.populate_database(
                source=source,
                platform=platform,
                limit=limit,
                force=force,
                progress_callback=progress_callback
            )
        
        success = self.operation_manager.start_operation(
            operation_id,
            populate_operation
        )
        
        if success:
            send_notification(
                f"Población de BD iniciada: {source} - {platform or 'todas las plataformas'}",
                "info",
                {
                    'operation_id': operation_id,
                    'source': source,
                    'platform': platform,
                    'limit': limit
                }
            )
        
        return operation_id
    
    def optimize_database_bulk(self, priority: OperationPriority = OperationPriority.LOW) -> str:
        """
        🔧 Optimizar base de datos de forma asíncrona
        
        Args:
            priority: prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="optimize_database",
            priority=priority,
            notification_interval=2.0
        )
        
        def optimize_operation(progress_callback=None):
            return self.database_ops.optimize_database(
                progress_callback=progress_callback
            )
        
        success = self.operation_manager.start_operation(
            operation_id,
            optimize_operation
        )
        
        if success:
            send_notification(
                "Optimización de BD iniciada",
                "info",
                {'operation_id': operation_id}
            )
        
        return operation_id
    
    # Operaciones de backup
    def create_backup_bulk(self, include_thumbnails: bool = True, 
                          thumbnail_limit: int = 100,
                          compress: bool = True,
                          priority: OperationPriority = OperationPriority.NORMAL) -> str:
        """
        💾 Crear backup del sistema de forma asíncrona
        
        Args:
            include_thumbnails: incluir thumbnails en el backup
            thumbnail_limit: límite de thumbnails para ahorrar espacio
            compress: comprimir el backup en ZIP
            priority: prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="create_backup",
            priority=priority,
            notification_interval=1.0
        )
        
        def backup_operation(progress_callback=None):
            return self.backup_ops.create_backup(
                include_thumbnails=include_thumbnails,
                thumbnail_limit=thumbnail_limit,
                compress=compress,
                progress_callback=progress_callback
            )
        
        success = self.operation_manager.start_operation(
            operation_id,
            backup_operation
        )
        
        if success:
            send_notification(
                "Backup del sistema iniciado",
                "info",
                {
                    'operation_id': operation_id,
                    'include_thumbnails': include_thumbnails,
                    'compress': compress
                }
            )
        
        return operation_id
    
    # Operaciones de personajes
    def analyze_characters_bulk(self, limit: Optional[int] = None,
                              priority: OperationPriority = OperationPriority.LOW) -> str:
        """
        👥 Analizar personajes de forma asíncrona
        
        Args:
            limit: límite de videos a analizar
            priority: prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="analyze_characters",
            priority=priority,
            total_items=limit or 0,
            notification_interval=1.0
        )
        
        def analyze_operation(progress_callback=None):
            return self.character_ops.analyze_titles(
                limit=limit,
                progress_callback=progress_callback
            )
        
        success = self.operation_manager.start_operation(
            operation_id,
            analyze_operation
        )
        
        if success:
            send_notification(
                "Análisis de personajes iniciado",
                "info",
                {'operation_id': operation_id, 'limit': limit}
            )
        
        return operation_id
    
    def clean_false_positives_bulk(self, force: bool = False,
                                  priority: OperationPriority = OperationPriority.LOW) -> str:
        """
        🧹 Limpiar falsos positivos de forma asíncrona
        
        Args:
            force: forzar limpieza sin confirmación
            priority: prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="clean_false_positives",
            priority=priority,
            notification_interval=1.0
        )
        
        def clean_operation(progress_callback=None):
            return self.character_ops.clean_false_positives(
                force=force,
                progress_callback=progress_callback
            )
        
        success = self.operation_manager.start_operation(
            operation_id,
            clean_operation
        )
        
        if success:
            send_notification(
                "Limpieza de falsos positivos iniciada",
                "info",
                {'operation_id': operation_id, 'force': force}
            )
        
        return operation_id
    
    # Operaciones de integridad
    def verify_integrity_bulk(self, fix_issues: bool = False,
                             priority: OperationPriority = OperationPriority.NORMAL) -> str:
        """
        🔍 Verificar integridad del sistema de forma asíncrona
        
        Args:
            fix_issues: intentar corregir problemas encontrados
            priority: prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="verify_integrity",
            priority=priority,
            notification_interval=1.0
        )
        
        def verify_operation(progress_callback=None):
            return self.integrity_ops.verify_database_integrity(
                fix_issues=fix_issues,
                progress_callback=progress_callback
            )
        
        success = self.operation_manager.start_operation(
            operation_id,
            verify_operation
        )
        
        if success:
            send_notification(
                "Verificación de integridad iniciada",
                "info",
                {'operation_id': operation_id, 'fix_issues': fix_issues}
            )
        
        return operation_id
    
    # Gestión de operaciones
    def get_operation_progress(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        📊 Obtener progreso de operación en curso
        
        Args:
            operation_id: ID de la operación
            
        Returns:
            Dict con progreso de la operación o None si no existe
        """
        return self.operation_manager.get_operation_status(operation_id)
    
    def cancel_operation(self, operation_id: str) -> bool:
        """
        ❌ Cancelar operación en curso
        
        Args:
            operation_id: ID de la operación
            
        Returns:
            True si se pudo cancelar, False en caso contrario
        """
        success = self.operation_manager.cancel_operation(operation_id)
        
        if success:
            send_notification(
                f"Operación cancelada: {operation_id}",
                "warning",
                {'operation_id': operation_id}
            )
        
        return success
    
    def pause_operation(self, operation_id: str) -> bool:
        """
        ⏸️ Pausar operación en curso
        
        Args:
            operation_id: ID de la operación
            
        Returns:
            True si se pudo pausar, False en caso contrario
        """
        success = self.operation_manager.pause_operation(operation_id)
        
        if success:
            send_notification(
                f"Operación pausada: {operation_id}",
                "info",
                {'operation_id': operation_id}
            )
        
        return success
    
    def resume_operation(self, operation_id: str) -> bool:
        """
        ▶️ Reanudar operación pausada
        
        Args:
            operation_id: ID de la operación
            
        Returns:
            True si se pudo reanudar, False en caso contrario
        """
        success = self.operation_manager.resume_operation(operation_id)
        
        if success:
            send_notification(
                f"Operación reanudada: {operation_id}",
                "info",
                {'operation_id': operation_id}
            )
        
        return success
    
    def get_all_operations(self) -> List[Dict[str, Any]]:
        """
        📋 Obtener todas las operaciones
        
        Returns:
            Lista de todas las operaciones
        """
        return self.operation_manager.get_all_operations()
    
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """
        🏃 Obtener operaciones activas
        
        Returns:
            Lista de operaciones activas
        """
        return self.operation_manager.get_active_operations()
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        💚 Estado general del sistema
        
        Returns:
            Dict con información de salud del sistema
        """
        try:
            # Información del sistema
            if PSUTIL_AVAILABLE:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                system_stats = {
                    'cpu_percent': cpu_percent,
                    'memory_total_gb': memory.total / (1024**3),
                    'memory_used_gb': memory.used / (1024**3),
                    'memory_percent': memory.percent,
                    'disk_total_gb': disk.total / (1024**3),
                    'disk_used_gb': disk.used / (1024**3),
                    'disk_percent': (disk.used / disk.total) * 100
                }
                
                health_score = self._calculate_health_score(
                    cpu_percent, memory.percent, disk.used / disk.total * 100
                )
            else:
                system_stats = {
                    'cpu_percent': 0,
                    'memory_total_gb': 0,
                    'memory_used_gb': 0,
                    'memory_percent': 0,
                    'disk_total_gb': 0,
                    'disk_used_gb': 0,
                    'disk_percent': 0
                }
                health_score = 50  # Score neutral cuando no hay info
            
            # Información de operaciones
            operation_stats = self.operation_manager.get_stats()
            
            # Información de WebSocket
            websocket_stats = self.websocket_manager.get_stats()
            
            # Información de la base de datos
            db_stats = self._get_database_stats()
            
            # Información de thumbnails
            thumbnail_stats = self.thumbnail_ops.get_thumbnail_stats()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'health_score': health_score,
                'system': system_stats,
                'operations': operation_stats,
                'websockets': websocket_stats,
                'database': db_stats,
                'thumbnails': thumbnail_stats,
                'psutil_available': PSUTIL_AVAILABLE
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo salud del sistema: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'status': 'error'
            }
    
    def _get_database_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la base de datos"""
        try:
            result = self.database_ops.get_database_stats()
            return result.get('stats', {}) if result.get('success') else {}
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de BD: {e}")
            return {'error': str(e)}
    
    def _calculate_health_score(self, cpu_percent: float, 
                               memory_percent: float, 
                               disk_percent: float) -> float:
        """Calcular puntuación de salud del sistema"""
        if not PSUTIL_AVAILABLE:
            return 50.0  # Score neutral cuando no hay datos
        
        # Puntuación basada en uso de recursos
        cpu_score = max(0, 100 - cpu_percent)
        memory_score = max(0, 100 - memory_percent)
        disk_score = max(0, 100 - disk_percent)
        
        # Peso promedio
        health_score = (cpu_score * 0.3 + memory_score * 0.4 + disk_score * 0.3)
        
        return round(health_score, 1)
    
    def send_custom_notification(self, message: str, 
                               level: str = "info", 
                               data: Dict[str, Any] = None):
        """
        📢 Enviar notificación personalizada
        
        Args:
            message: mensaje de la notificación
            level: nivel de la notificación (info, warning, error, success)
            data: datos adicionales
        """
        send_notification(message, level, data)
    
    def clear_database_bulk(self, platform: Optional[str] = None, 
                           force: bool = False,
                           priority: OperationPriority = OperationPriority.HIGH) -> str:
        """
        🧹 Limpiar base de datos de forma asíncrona
        
        Args:
            platform: plataforma específica o None para todas
            force: forzar limpieza sin confirmación
            priority: prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="clear_database",
            priority=priority,
            notification_interval=1.0
        )
        
        def clear_operation(progress_callback=None):
            return self.database_ops.clear_database(
                platform=platform,
                force=force,
                progress_callback=progress_callback
            )
        
        success = self.operation_manager.start_operation(
            operation_id,
            clear_operation
        )
        
        if success:
            send_notification(
                f"Limpieza de BD iniciada: {platform or 'todas las plataformas'}",
                "warning",
                {'operation_id': operation_id, 'platform': platform, 'force': force}
            )
        
        return operation_id

    def backup_database_bulk(self, backup_path: Optional[str] = None,
                            priority: OperationPriority = OperationPriority.NORMAL) -> str:
        """
        💾 Crear backup de base de datos de forma asíncrona
        
        Args:
            backup_path: ruta personalizada para el backup
            priority: prioridad de la operación
            
        Returns:
            operation_id: ID de la operación para tracking
        """
        operation_id = self.operation_manager.create_operation(
            operation_type="backup_database",
            priority=priority,
            notification_interval=1.0
        )
        
        def backup_operation(progress_callback=None):
            return self.backup_ops.backup_database(
                backup_path=backup_path,
                progress_callback=progress_callback
            )
        
        success = self.operation_manager.start_operation(
            operation_id,
            backup_operation
        )
        
        if success:
            send_notification(
                f"Backup de BD iniciado: {backup_path or 'ruta automática'}",
                "info",
                {'operation_id': operation_id, 'backup_path': backup_path}
            )
        
        return operation_id

    def cleanup_completed_operations(self, max_age_hours: int = 24) -> int:
        """
        🧹 Limpiar operaciones completadas antiguas
        
        Args:
            max_age_hours: edad máxima en horas para mantener operaciones
            
        Returns:
            Número de operaciones limpiadas
        """
        return self.operation_manager.cleanup_completed_operations(max_age_hours)

    def get_api_stats(self) -> Dict[str, Any]:
        """
        📊 Obtener estadísticas de la API
        
        Returns:
            Dict con estadísticas de la API
        """
        return {
            'api_version': '2.0',
            'features': [
                'websocket_support',
                'real_time_notifications',
                'operation_management',
                'priority_queuing',
                'progress_tracking',
                'cancellation_support',
                'pause_resume_support'
            ],
            'operation_manager': self.operation_manager.get_stats(),
            'websocket_manager': self.websocket_manager.get_stats()
        }

# Instancia global (singleton)
_async_operations_api_instance = None

def get_async_operations_api() -> AsyncOperationsAPI:
    """Obtener instancia singleton de AsyncOperationsAPI"""
    global _async_operations_api_instance
    if _async_operations_api_instance is None:
        _async_operations_api_instance = AsyncOperationsAPI()
    return _async_operations_api_instance

# Alias para compatibilidad hacia atrás
def get_maintenance_api() -> AsyncOperationsAPI:
    """Alias para compatibilidad - usar get_async_operations_api()"""
    return get_async_operations_api()

# Funciones de conveniencia
def start_regenerate_thumbnails(video_ids: List[int], 
                              force: bool = False,
                              priority: OperationPriority = OperationPriority.NORMAL) -> str:
    """Iniciar regeneración de thumbnails asíncrona"""
    return get_maintenance_api().regenerate_thumbnails_bulk(video_ids, force, priority)

def start_populate_database(source: str = 'all', 
                          platform: Optional[str] = None,
                          limit: Optional[int] = None, 
                          force: bool = False,
                          priority: OperationPriority = OperationPriority.HIGH) -> str:
    """Iniciar población de BD asíncrona"""
    return get_maintenance_api().populate_database_bulk(source, platform, limit, force, priority)

def get_operation_status(operation_id: str) -> Optional[Dict[str, Any]]:
    """Obtener estado de operación"""
    return get_maintenance_api().get_operation_progress(operation_id)

def cancel_operation(operation_id: str) -> bool:
    """Cancelar operación"""
    return get_maintenance_api().cancel_operation(operation_id)

def get_system_health() -> Dict[str, Any]:
    """Obtener salud del sistema"""
    return get_maintenance_api().get_system_health()

def send_notification(message: str, level: str = "info", data: Dict[str, Any] = None):
    """Enviar notificación"""
    return get_maintenance_api().send_custom_notification(message, level, data)

def start_populate_thumbnails(platform: Optional[str] = None,
                             limit: Optional[int] = None,
                             force: bool = False,
                             priority: OperationPriority = OperationPriority.NORMAL) -> str:
    """Iniciar población de thumbnails asíncrona"""
    return get_maintenance_api().populate_thumbnails_bulk(platform, limit, force, priority)

def start_clean_thumbnails(force: bool = False,
                          priority: OperationPriority = OperationPriority.NORMAL) -> str:
    """Iniciar limpieza de thumbnails asíncrona"""
    return get_maintenance_api().clean_thumbnails_bulk(force, priority)

def start_optimize_database(priority: OperationPriority = OperationPriority.LOW) -> str:
    """Iniciar optimización de BD asíncrona"""
    return get_maintenance_api().optimize_database_bulk(priority)

def start_clear_database(platform: Optional[str] = None,
                        force: bool = False,
                        priority: OperationPriority = OperationPriority.HIGH) -> str:
    """Iniciar limpieza de BD asíncrona"""
    return get_maintenance_api().clear_database_bulk(platform, force, priority)

def start_backup_database(backup_path: Optional[str] = None,
                         priority: OperationPriority = OperationPriority.NORMAL) -> str:
    """Iniciar backup de BD asíncrona"""
    return get_maintenance_api().backup_database_bulk(backup_path, priority)

def cleanup_operations(max_age_hours: int = 24) -> int:
    """Limpiar operaciones completadas antiguas"""
    return get_maintenance_api().cleanup_completed_operations(max_age_hours)