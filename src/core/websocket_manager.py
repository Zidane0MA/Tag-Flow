#!/usr/bin/env python3
"""
🔗 WebSocket Manager - Fase 5
Sistema de comunicación en tiempo real para operaciones de mantenimiento
"""

import json
import time
import uuid
import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from queue import Queue
# Imports opcionales para WebSocket
try:
    import websockets
    import websockets.server
    from websockets.exceptions import ConnectionClosed
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None
    ConnectionClosed = Exception

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Tipos de mensajes WebSocket"""
    OPERATION_PROGRESS = "operation_progress"
    OPERATION_COMPLETE = "operation_complete"
    OPERATION_FAILED = "operation_failed"
    OPERATION_CANCELLED = "operation_cancelled"
    SYSTEM_STATUS = "system_status"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"


@dataclass
class WebSocketMessage:
    """Mensaje WebSocket estandarizado"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime = None
    message_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
    
    def to_json(self) -> str:
        """Convertir a JSON para envío"""
        return json.dumps({
            'type': self.type.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'message_id': self.message_id
        })


class WebSocketManager:
    """
    🔗 Gestor de WebSockets para comunicación en tiempo real
    
    Características:
    - Conexiones múltiples simultáneas
    - Broadcast de mensajes
    - Filtrado por suscripciones
    - Heartbeat automático
    - Reconexión automática
    """
    
    def __init__(self, host: str = None, port: int = None):
        import os
        
        # Leer configuración desde variables de entorno
        self.host = host or os.getenv('WEBSOCKET_HOST', 'localhost')
        self.port = port or int(os.getenv('WEBSOCKET_PORT', '8766'))
        self.clients: Dict[str, Any] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of operation_ids
        self.message_queue: Queue = Queue()
        self.running = False
        self.server = None
        self.broadcast_task = None
        self.heartbeat_task = None
        
        # Verificar si WebSockets está disponible
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("⚠️ WebSockets no disponible. Funcionalidades limitadas.")
        
        # Estadísticas
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'messages_failed': 0,
            'start_time': None,
            'websockets_available': WEBSOCKETS_AVAILABLE
        }
    
    async def start_server(self):
        """Iniciar servidor WebSocket"""
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("⚠️ WebSockets no disponible. Servidor no iniciado.")
            return

        try:
            # Usar wrapper para compatibilidad de versiones
            async def handler(websocket, path=None):
                await self.handle_client(websocket, path or "/")

            self.server = await websockets.serve(
                handler,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10
            )
            
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            # Iniciar tareas de background
            self.broadcast_task = asyncio.create_task(self.broadcast_messages())
            self.heartbeat_task = asyncio.create_task(self.send_heartbeat())
            
            logger.info(f"🔗 WebSocket server iniciado en ws://{self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Error iniciando servidor WebSocket: {e}")
            raise
    
    async def stop_server(self):
        """Detener servidor WebSocket"""
        try:
            self.running = False
            
            # Cancelar tareas
            if self.broadcast_task:
                self.broadcast_task.cancel()
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            
            # Cerrar conexiones
            if self.clients:
                close_tasks = []
                for client_id, websocket in self.clients.items():
                    close_tasks.append(self._close_connection(client_id, websocket))
                
                if close_tasks:
                    await asyncio.gather(*close_tasks, return_exceptions=True)
            
            # Cerrar servidor
            if self.server:
                self.server.close()
                await self.server.wait_closed()
            
            logger.info("🔗 WebSocket server detenido")
            
        except Exception as e:
            logger.error(f"Error deteniendo servidor WebSocket: {e}")
    
    async def handle_client(self, websocket, path):
        """Manejar conexión de cliente"""
        client_id = str(uuid.uuid4())

        try:
            # Registrar cliente
            self.clients[client_id] = websocket
            self.subscriptions[client_id] = set()
            self.stats['total_connections'] += 1
            self.stats['active_connections'] += 1

            logger.info(f"🔗 Cliente conectado: {client_id} desde {websocket.remote_address}")

            # Enviar mensaje de bienvenida
            welcome_message = WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={
                    'client_id': client_id,
                    'message': 'Conectado al servidor de mantenimiento',
                    'server_time': datetime.now().isoformat()
                }
            )

            try:
                await websocket.send(welcome_message.to_json())
                logger.debug(f"🔗 Mensaje de bienvenida enviado a {client_id}")
            except Exception as e:
                logger.error(f"🔗 Error enviando bienvenida a {client_id}: {e}")
                return

            # Escuchar mensajes del cliente
            async for message in websocket:
                logger.debug(f"🔗 Mensaje recibido de {client_id}: {message}")
                await self._handle_client_message(client_id, message)

        except ConnectionClosed as e:
            logger.info(f"🔗 Cliente desconectado: {client_id} - Código: {e.code}, Razón: {e.reason}")
        except Exception as e:
            logger.error(f"🔗 Error manejando cliente {client_id}: {e}")
            import traceback
            logger.error(f"🔗 Traceback: {traceback.format_exc()}")
        finally:
            # Limpiar cliente
            await self._cleanup_client(client_id)
    
    async def _handle_client_message(self, client_id: str, message: str):
        """Manejar mensaje del cliente"""
        try:
            data = json.loads(message)
            action = data.get('action')
            
            if action == 'subscribe':
                # Suscribir a operación específica
                operation_id = data.get('operation_id')
                if operation_id:
                    self.subscriptions[client_id].add(operation_id)
                    logger.debug(f"Cliente {client_id} suscrito a operación {operation_id}")
            
            elif action == 'unsubscribe':
                # Desuscribir de operación
                operation_id = data.get('operation_id')
                if operation_id:
                    self.subscriptions[client_id].discard(operation_id)
                    logger.debug(f"Cliente {client_id} desuscrito de operación {operation_id}")
            
            elif action == 'get_status':
                # Enviar estado del servidor
                await self._send_server_status(client_id)
            
            elif action == 'ping':
                # Responder pong
                pong_message = WebSocketMessage(
                    type=MessageType.HEARTBEAT,
                    data={'type': 'pong', 'timestamp': datetime.now().isoformat()}
                )
                await self.clients[client_id].send(pong_message.to_json())
            
        except json.JSONDecodeError:
            logger.warning(f"Mensaje JSON inválido de cliente {client_id}")
        except Exception as e:
            logger.error(f"Error procesando mensaje de cliente {client_id}: {e}")
    
    async def _cleanup_client(self, client_id: str):
        """Limpiar datos del cliente"""
        try:
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.subscriptions:
                del self.subscriptions[client_id]
            
            self.stats['active_connections'] -= 1
            
        except Exception as e:
            logger.error(f"Error limpiando cliente {client_id}: {e}")
    
    async def _close_connection(self, client_id: str, websocket):
        """Cerrar conexión específica"""
        try:
            await websocket.close()
        except Exception as e:
            logger.warning(f"Error cerrando conexión {client_id}: {e}")
    
    async def _send_server_status(self, client_id: str):
        """Enviar estado del servidor a cliente específico"""
        try:
            server_stats = self.get_stats()
            status_message = WebSocketMessage(
                type=MessageType.SYSTEM_STATUS,
                data={
                    'server_stats': server_stats,
                    'active_clients': server_stats['active_connections'],
                    'total_subscriptions': server_stats['total_subscriptions']
                }
            )
            
            await self.clients[client_id].send(status_message.to_json())
            
        except Exception as e:
            logger.error(f"Error enviando estado a cliente {client_id}: {e}")
    
    def send_operation_progress(self, operation_id: str, progress_data: Dict[str, Any]):
        """Enviar progreso de operación (thread-safe)"""
        if not WEBSOCKETS_AVAILABLE:
            return
        
        message = WebSocketMessage(
            type=MessageType.OPERATION_PROGRESS,
            data={
                'operation_id': operation_id,
                'progress': progress_data
            }
        )
        self.message_queue.put(message)
    
    def send_operation_complete(self, operation_id: str, result_data: Dict[str, Any]):
        """Enviar completado de operación (thread-safe)"""
        message = WebSocketMessage(
            type=MessageType.OPERATION_COMPLETE,
            data={
                'operation_id': operation_id,
                'result': result_data
            }
        )
        self.message_queue.put(message)
    
    def send_operation_failed(self, operation_id: str, error_data: Dict[str, Any]):
        """Enviar error de operación (thread-safe)"""
        message = WebSocketMessage(
            type=MessageType.OPERATION_FAILED,
            data={
                'operation_id': operation_id,
                'error': error_data
            }
        )
        self.message_queue.put(message)
    
    def send_notification(self, message: str, level: str = "info", data: Dict[str, Any] = None):
        """Enviar notificación general (thread-safe)"""
        if not WEBSOCKETS_AVAILABLE:
            return
        notification = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                'message': message,
                'level': level,
                'data': data or {}
            }
        )
        self.message_queue.put(notification)
    
    async def broadcast_messages(self):
        """Procesar cola de mensajes y enviar broadcasts"""
        while self.running:
            try:
                # Procesar mensajes en cola
                messages_to_process = []
                
                # Obtener todos los mensajes disponibles
                while not self.message_queue.empty():
                    try:
                        message = self.message_queue.get_nowait()
                        messages_to_process.append(message)
                    except:
                        break
                
                # Enviar mensajes
                for message in messages_to_process:
                    await self._broadcast_message(message)
                
                # Pequeña pausa para evitar busy-waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error en broadcast de mensajes: {e}")
                await asyncio.sleep(1)
    
    async def _broadcast_message(self, message: WebSocketMessage):
        """Enviar mensaje a clientes relevantes"""
        try:
            message_json = message.to_json()
            
            # Determinar destinatarios
            target_clients = []
            
            if message.type in [MessageType.OPERATION_PROGRESS, MessageType.OPERATION_COMPLETE, 
                               MessageType.OPERATION_FAILED, MessageType.OPERATION_CANCELLED]:
                # Mensajes de operación - solo a clientes suscritos
                operation_id = message.data.get('operation_id')
                if operation_id:
                    for client_id, subscriptions in self.subscriptions.items():
                        if operation_id in subscriptions:
                            target_clients.append(client_id)
            else:
                # Mensajes generales - a todos los clientes
                target_clients = list(self.clients.keys())
            
            # Enviar a clientes objetivo
            send_tasks = []
            for client_id in target_clients:
                if client_id in self.clients:
                    send_tasks.append(self._send_to_client(client_id, message_json))
            
            # Ejecutar envíos en paralelo
            if send_tasks:
                results = await asyncio.gather(*send_tasks, return_exceptions=True)
                
                # Contar estadísticas
                for result in results:
                    if isinstance(result, Exception):
                        self.stats['messages_failed'] += 1
                    else:
                        self.stats['messages_sent'] += 1
            
        except Exception as e:
            logger.error(f"Error enviando mensaje broadcast: {e}")
    
    async def _send_to_client(self, client_id: str, message_json: str):
        """Enviar mensaje a cliente específico"""
        try:
            websocket = self.clients.get(client_id)
            if websocket:
                await websocket.send(message_json)
                return True
            return False
            
        except ConnectionClosed:
            # Cliente desconectado - limpiar
            await self._cleanup_client(client_id)
            return False
        except Exception as e:
            logger.warning(f"Error enviando mensaje a cliente {client_id}: {e}")
            return False
    
    async def send_heartbeat(self):
        """Enviar heartbeat periódico"""
        while self.running:
            try:
                heartbeat_message = WebSocketMessage(
                    type=MessageType.HEARTBEAT,
                    data={
                        'type': 'ping',
                        'timestamp': datetime.now().isoformat(),
                        'server_stats': {
                            'active_connections': len(self.clients),
                            'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0
                        }
                    }
                )
                
                self.message_queue.put(heartbeat_message)
                
                # Esperar 30 segundos antes del próximo heartbeat
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error enviando heartbeat: {e}")
                await asyncio.sleep(5)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del servidor en un formato serializable."""
        stats_copy = self.stats.copy()
        if isinstance(stats_copy.get('start_time'), datetime):
            stats_copy['start_time'] = stats_copy['start_time'].isoformat()

        uptime_seconds = 0
        if self.stats.get('start_time'):
            uptime_seconds = (datetime.now() - self.stats['start_time']).total_seconds()

        return {
            **stats_copy,
            'active_connections': len(self.clients),
            'total_subscriptions': sum(len(subs) for subs in self.subscriptions.values()),
            'uptime_seconds': uptime_seconds
        }


class WebSocketClient:
    """
    🔗 Cliente WebSocket para testing y uso programático
    """
    
    def __init__(self, uri: str = "ws://localhost:8766"):
        self.uri = uri
        self.websocket = None
        self.connected = False
        self.message_handlers = {}
        self.client_id = None
    
    async def connect(self):
        """Conectar al servidor WebSocket"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            logger.info(f"🔗 Conectado a {self.uri}")
            
            # Procesar mensajes
            asyncio.create_task(self._message_handler())
            
        except Exception as e:
            logger.error(f"Error conectando a WebSocket: {e}")
            raise
    
    async def disconnect(self):
        """Desconectar del servidor"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("🔗 Desconectado del servidor")
    
    async def subscribe_to_operation(self, operation_id: str):
        """Suscribirse a una operación específica"""
        if self.connected:
            message = {
                'action': 'subscribe',
                'operation_id': operation_id
            }
            await self.websocket.send(json.dumps(message))
    
    async def unsubscribe_from_operation(self, operation_id: str):
        """Desuscribirse de una operación"""
        if self.connected:
            message = {
                'action': 'unsubscribe',
                'operation_id': operation_id
            }
            await self.websocket.send(json.dumps(message))
    
    async def get_server_status(self):
        """Solicitar estado del servidor"""
        if self.connected:
            message = {
                'action': 'get_status'
            }
            await self.websocket.send(json.dumps(message))
    
    async def _message_handler(self):
        """Manejar mensajes entrantes"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                message_type = data.get('type')
                
                if message_type == 'notification':
                    # Extraer client_id del mensaje de bienvenida
                    if 'client_id' in data.get('data', {}):
                        self.client_id = data['data']['client_id']
                
                # Llamar handlers registrados
                if message_type in self.message_handlers:
                    await self.message_handlers[message_type](data)
                
        except ConnectionClosed:
            self.connected = False
            logger.info("🔗 Conexión cerrada por servidor")
        except Exception as e:
            logger.error(f"Error manejando mensaje: {e}")
    
    def on_message(self, message_type: str, handler):
        """Registrar handler para tipo de mensaje"""
        self.message_handlers[message_type] = handler


# Instancia global del manager
_websocket_manager = None

def get_websocket_manager() -> WebSocketManager:
    """Obtener instancia singleton del WebSocket manager"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


# Funciones de conveniencia
def start_websocket_server(host: str = "localhost", port: int = 8765):
    """Iniciar servidor WebSocket en thread separado"""
    def run_server():
        asyncio.run(get_websocket_manager().start_server())
    
    import threading
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    return server_thread


def send_operation_progress(operation_id: str, progress_data: Dict[str, Any]):
    """Enviar progreso de operación"""
    manager = get_websocket_manager()
    manager.send_operation_progress(operation_id, progress_data)


def send_operation_complete(operation_id: str, result_data: Dict[str, Any]):
    """Enviar completado de operación"""
    manager = get_websocket_manager()
    manager.send_operation_complete(operation_id, result_data)


def send_notification(message: str, level: str = "info", data: Dict[str, Any] = None):
    """Enviar notificación general"""
    if not WEBSOCKETS_AVAILABLE:
        return
    manager = get_websocket_manager()
    manager.send_notification(message, level, data)