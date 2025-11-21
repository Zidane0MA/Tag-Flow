#!/usr/bin/env python3
"""
🔗 WebSocket API - Sistema de actualizaciones en tiempo real
Integración de WebSockets con Flask para cursor pagination
"""

from flask import Blueprint, request, jsonify
from src.core.websocket_manager import get_websocket_manager, send_notification, MessageType
import asyncio
import threading
import logging

logger = logging.getLogger(__name__)

# Blueprint para WebSocket endpoints
websocket_bp = Blueprint('websocket', __name__, url_prefix='/api/websocket')

# Global para el servidor WebSocket
_websocket_server_started = False
_websocket_server_thread = None

def start_websocket_server_if_needed():
    """Iniciar servidor WebSocket si no está corriendo"""
    global _websocket_server_started, _websocket_server_thread

    # Evitar start en Flask reloader
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        # Solo iniciar en el proceso principal del reloader
        if not _websocket_server_started:
            try:
                def run_websocket_server():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    manager = get_websocket_manager()
                    loop.run_until_complete(manager.start_server())
                    loop.run_forever()

                _websocket_server_thread = threading.Thread(
                    target=run_websocket_server,
                    daemon=True,
                    name="WebSocketServer"
                )
                _websocket_server_thread.start()
                _websocket_server_started = True

                logger.info("🔗 WebSocket server iniciado en thread separado")

            except Exception as e:
                logger.error(f"Error iniciando WebSocket server: {e}")
                # No raise para evitar bloquear Flask
                logger.warning("🔗 Continuando sin WebSocket server")
    else:
        logger.info("🔗 Esperando proceso principal de Flask para iniciar WebSocket")

@websocket_bp.route('/status', methods=['GET'])
def websocket_status():
    """Obtener estado del servidor WebSocket"""
    try:
        manager = get_websocket_manager()
        stats = manager.get_stats()

        return jsonify({
            'success': True,
            'websocket_enabled': stats.get('websockets_available', False),
            'server_running': _websocket_server_started,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error obteniendo estado WebSocket: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'websocket_enabled': False,
            'server_running': False
        }), 500

@websocket_bp.route('/start', methods=['POST'])
def start_websocket_server():
    """Iniciar servidor WebSocket manualmente"""
    try:
        start_websocket_server_if_needed()

        # Obtener configuración desde variables de entorno
        ws_host = os.getenv('WEBSOCKET_HOST', 'localhost')
        ws_port = os.getenv('WEBSOCKET_PORT', '8766')
        
        return jsonify({
            'success': True,
            'message': 'WebSocket server iniciado',
            'websocket_url': f'ws://{ws_host}:{ws_port}'
        })

    except Exception as e:
        logger.error(f"Error iniciando WebSocket server: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@websocket_bp.route('/notify', methods=['POST'])
def send_websocket_notification():
    """Enviar notificación via WebSocket"""
    try:
        data = request.get_json()

        message = data.get('message', '')
        level = data.get('level', 'info')
        notification_data = data.get('data', {})

        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400

        # Enviar notificación
        send_notification(message, level, notification_data)

        return jsonify({
            'success': True,
            'message': 'Notification sent'
        })

    except Exception as e:
        logger.error(f"Error enviando notificación WebSocket: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@websocket_bp.route('/broadcast/video-update', methods=['POST'])
def broadcast_video_update():
    """Broadcast actualización de video para invalidar caches cursor"""
    try:
        data = request.get_json()

        video_id = data.get('video_id')
        action = data.get('action')  # 'update', 'delete', 'restore', 'move_to_trash'
        changes = data.get('changes', {})

        if not video_id or not action:
            return jsonify({
                'success': False,
                'error': 'video_id and action are required'
            }), 400

        # Preparar datos del broadcast
        broadcast_data = {
            'video_id': str(video_id),
            'action': action,
            'changes': changes,
            'timestamp': str(asyncio.get_event_loop().time() if hasattr(asyncio, 'get_event_loop') else 0)
        }

        # Enviar notificación especializada para cursor invalidation
        send_notification(
            message=f"Video {action}: {video_id}",
            level="cursor_invalidation",
            data={
                'type': 'video_update',
                'video_update': broadcast_data
            }
        )

        return jsonify({
            'success': True,
            'message': f'Video {action} broadcast sent',
            'data': broadcast_data
        })

    except Exception as e:
        logger.error(f"Error broadcasting video update: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@websocket_bp.route('/broadcast/cache-invalidate', methods=['POST'])
def broadcast_cache_invalidation():
    """Broadcast invalidación de cache para componentes específicos"""
    try:
        data = request.get_json()

        cache_keys = data.get('cache_keys', [])
        reason = data.get('reason', 'manual_invalidation')

        if not cache_keys:
            return jsonify({
                'success': False,
                'error': 'cache_keys array is required'
            }), 400

        # Preparar datos del broadcast
        broadcast_data = {
            'cache_keys': cache_keys,
            'reason': reason,
            'timestamp': str(asyncio.get_event_loop().time() if hasattr(asyncio, 'get_event_loop') else 0)
        }

        # Enviar notificación de invalidación
        send_notification(
            message=f"Cache invalidation: {len(cache_keys)} keys",
            level="cache_invalidation",
            data={
                'type': 'cache_invalidation',
                'cache_invalidation': broadcast_data
            }
        )

        return jsonify({
            'success': True,
            'message': f'Cache invalidation broadcast sent for {len(cache_keys)} keys',
            'data': broadcast_data
        })

    except Exception as e:
        logger.error(f"Error broadcasting cache invalidation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Auto-start del servidor WebSocket cuando se carga el módulo
try:
    start_websocket_server_if_needed()
except Exception as e:
    logger.warning(f"No se pudo auto-iniciar WebSocket server: {e}")