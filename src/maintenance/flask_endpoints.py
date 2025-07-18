#!/usr/bin/env python3
"""
🌐 Flask Endpoints - Fase 5
Endpoints Flask para el dashboard de mantenimiento con WebSockets
"""

from flask import Blueprint, render_template, jsonify, request
import logging
from typing import Dict, List, Optional, Any
import json

# Importar módulos del proyecto
from src.maintenance_api import get_maintenance_api
from src.maintenance.websocket_manager import get_websocket_manager
from src.maintenance.operation_manager import get_operation_manager, OperationPriority

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Crear Blueprint
maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')


@maintenance_bp.route('/dashboard')
def dashboard():
    """
    🖥️ Página principal del dashboard
    """
    return render_template('maintenance_dashboard.html')


@maintenance_bp.route('/api/system/health')
def api_system_health():
    """
    💚 Obtener salud del sistema
    """
    try:
        api = get_maintenance_api()
        health = api.get_system_health()
        
        return jsonify({
            'success': True,
            'data': health
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo salud del sistema: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/operations')
def api_get_operations():
    """
    📋 Obtener todas las operaciones
    """
    try:
        manager = get_operation_manager()
        operations = manager.get_all_operations()
        
        return jsonify({
            'success': True,
            'data': operations
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo operaciones: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/operations/active')
def api_get_active_operations():
    """
    🏃 Obtener operaciones activas
    """
    try:
        manager = get_operation_manager()
        operations = manager.get_active_operations()
        
        return jsonify({
            'success': True,
            'data': operations
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo operaciones activas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/operations/<operation_id>')
def api_get_operation(operation_id: str):
    """
    📊 Obtener estado de operación específica
    """
    try:
        manager = get_operation_manager()
        operation = manager.get_operation_status(operation_id)
        
        if operation:
            return jsonify({
                'success': True,
                'data': operation
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Operación no encontrada'
            }), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo operación {operation_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/operations/<operation_id>/cancel', methods=['POST'])
def api_cancel_operation(operation_id: str):
    """
    ❌ Cancelar operación
    """
    try:
        manager = get_operation_manager()
        success = manager.cancel_operation(operation_id)
        
        return jsonify({
            'success': success,
            'message': 'Operación cancelada' if success else 'No se pudo cancelar la operación'
        })
        
    except Exception as e:
        logger.error(f"Error cancelando operación {operation_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/operations/<operation_id>/pause', methods=['POST'])
def api_pause_operation(operation_id: str):
    """
    ⏸️ Pausar operación
    """
    try:
        manager = get_operation_manager()
        success = manager.pause_operation(operation_id)
        
        return jsonify({
            'success': success,
            'message': 'Operación pausada' if success else 'No se pudo pausar la operación'
        })
        
    except Exception as e:
        logger.error(f"Error pausando operación {operation_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/operations/<operation_id>/resume', methods=['POST'])
def api_resume_operation(operation_id: str):
    """
    ▶️ Reanudar operación
    """
    try:
        manager = get_operation_manager()
        success = manager.resume_operation(operation_id)
        
        return jsonify({
            'success': success,
            'message': 'Operación reanudada' if success else 'No se pudo reanudar la operación'
        })
        
    except Exception as e:
        logger.error(f"Error reanudando operación {operation_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/operations/thumbnails/regenerate', methods=['POST'])
def api_regenerate_thumbnails():
    """
    🖼️ Iniciar regeneración de thumbnails
    """
    try:
        data = request.get_json()
        video_ids = data.get('video_ids', [])
        force = data.get('force', False)
        priority = data.get('priority', 'normal')
        
        if not video_ids:
            return jsonify({
                'success': False,
                'error': 'Se requieren video_ids'
            }), 400
        
        # Convertir prioridad string a enum
        priority_enum = OperationPriority.NORMAL
        if priority == 'high':
            priority_enum = OperationPriority.HIGH
        elif priority == 'low':
            priority_enum = OperationPriority.LOW
        elif priority == 'critical':
            priority_enum = OperationPriority.CRITICAL
        
        # Iniciar operación
        api = get_maintenance_api()
        operation_id = api.regenerate_thumbnails_bulk(video_ids, force, priority_enum)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': f'Regeneración de thumbnails iniciada para {len(video_ids)} videos'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando regeneración de thumbnails: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/operations/database/populate', methods=['POST'])
def api_populate_database():
    """
    🗃️ Iniciar población de base de datos
    """
    try:
        data = request.get_json()
        source = data.get('source', 'all')
        platform = data.get('platform')
        limit = data.get('limit')
        force = data.get('force', False)
        priority = data.get('priority', 'high')
        
        # Convertir prioridad
        priority_enum = OperationPriority.HIGH
        if priority == 'normal':
            priority_enum = OperationPriority.NORMAL
        elif priority == 'low':
            priority_enum = OperationPriority.LOW
        elif priority == 'critical':
            priority_enum = OperationPriority.CRITICAL
        
        # Iniciar operación
        api = get_maintenance_api()
        operation_id = api.populate_database_bulk(source, platform, limit, force, priority_enum)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': f'Población de BD iniciada: {source} - {platform or "todas las plataformas"}'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando población de BD: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/operations/backup/create', methods=['POST'])
def api_create_backup():
    """
    💾 Crear backup del sistema
    """
    try:
        data = request.get_json()
        include_thumbnails = data.get('include_thumbnails', True)
        thumbnail_limit = data.get('thumbnail_limit', 100)
        compress = data.get('compress', True)
        priority = data.get('priority', 'normal')
        
        # Convertir prioridad
        priority_enum = OperationPriority.NORMAL
        if priority == 'high':
            priority_enum = OperationPriority.HIGH
        elif priority == 'low':
            priority_enum = OperationPriority.LOW
        elif priority == 'critical':
            priority_enum = OperationPriority.CRITICAL
        
        # Iniciar operación
        api = get_maintenance_api()
        operation_id = api.create_backup_bulk(include_thumbnails, thumbnail_limit, compress, priority_enum)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': 'Backup del sistema iniciado'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando backup: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/operations/integrity/verify', methods=['POST'])
def api_verify_integrity():
    """
    🔍 Verificar integridad del sistema
    """
    try:
        data = request.get_json()
        fix_issues = data.get('fix_issues', False)
        priority = data.get('priority', 'normal')
        
        # Convertir prioridad
        priority_enum = OperationPriority.NORMAL
        if priority == 'high':
            priority_enum = OperationPriority.HIGH
        elif priority == 'low':
            priority_enum = OperationPriority.LOW
        elif priority == 'critical':
            priority_enum = OperationPriority.CRITICAL
        
        # Iniciar operación
        api = get_maintenance_api()
        operation_id = api.verify_integrity_bulk(fix_issues, priority_enum)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': 'Verificación de integridad iniciada'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando verificación: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/websocket/stats')
def api_websocket_stats():
    """
    📊 Obtener estadísticas de WebSocket
    """
    try:
        manager = get_websocket_manager()
        stats = manager.get_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas WebSocket: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/notifications/send', methods=['POST'])
def api_send_notification():
    """
    📢 Enviar notificación personalizada
    """
    try:
        data = request.get_json()
        message = data.get('message', '')
        level = data.get('level', 'info')
        notification_data = data.get('data', {})
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Se requiere mensaje'
            }), 400
        
        # Enviar notificación
        api = get_maintenance_api()
        api.send_custom_notification(message, level, notification_data)
        
        return jsonify({
            'success': True,
            'message': 'Notificación enviada'
        })
        
    except Exception as e:
        logger.error(f"Error enviando notificación: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/stats/overview')
def api_stats_overview():
    """
    📊 Obtener resumen de estadísticas
    """
    try:
        api = get_maintenance_api()
        operation_manager = get_operation_manager()
        websocket_manager = get_websocket_manager()
        
        # Obtener estadísticas
        system_health = api.get_system_health()
        operation_stats = operation_manager.get_stats()
        websocket_stats = websocket_manager.get_stats()
        api_stats = api.get_api_stats()
        
        overview = {
            'system_health': system_health,
            'operations': operation_stats,
            'websockets': websocket_stats,
            'api': api_stats
        }
        
        return jsonify({
            'success': True,
            'data': overview
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """
    ⚙️ Gestionar configuración del dashboard
    """
    if request.method == 'GET':
        try:
            # Obtener configuración actual
            settings = {
                'websocket_url': 'ws://localhost:8765',
                'update_interval': 1000,
                'max_log_entries': 100,
                'notification_levels': ['info', 'warning', 'error', 'success'],
                'operation_priorities': ['low', 'normal', 'high', 'critical']
            }
            
            return jsonify({
                'success': True,
                'data': settings
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo configuración: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validar configuración
            if 'update_interval' in data:
                interval = data['update_interval']
                if not isinstance(interval, int) or interval < 500:
                    return jsonify({
                        'success': False,
                        'error': 'Intervalo de actualización debe ser >= 500ms'
                    }), 400
            
            # Guardar configuración (en implementación real, usar BD o archivo)
            logger.info(f"Configuración actualizada: {data}")
            
            return jsonify({
                'success': True,
                'message': 'Configuración guardada exitosamente'
            })
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


# Rutas de conveniencia para desarrollo
@maintenance_bp.route('/test/websocket')
def test_websocket():
    """
    🧪 Página de prueba WebSocket
    """
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        <div id="messages"></div>
        <script>
            const ws = new WebSocket('ws://localhost:8765');
            const messages = document.getElementById('messages');
            
            ws.onopen = function() {
                messages.innerHTML += '<p>Connected to WebSocket</p>';
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                messages.innerHTML += '<p>' + JSON.stringify(data, null, 2) + '</p>';
            };
            
            ws.onclose = function() {
                messages.innerHTML += '<p>WebSocket connection closed</p>';
            };
            
            ws.onerror = function(error) {
                messages.innerHTML += '<p>WebSocket error: ' + error + '</p>';
            };
        </script>
    </body>
    </html>
    '''


@maintenance_bp.route('/test/operation')
def test_operation():
    """
    🧪 Crear operación de prueba
    """
    try:
        import time
        import threading
        
        def test_operation_func(progress_callback=None):
            """Operación de prueba que simula procesamiento"""
            total = 10
            for i in range(total):
                if progress_callback:
                    progress_callback(
                        processed=i + 1,
                        total=total,
                        current_item=f"Procesando item {i + 1}",
                        successful=i + 1,
                        failed=0
                    )
                time.sleep(1)
            return {'message': 'Operación de prueba completada', 'items_processed': total}
        
        # Crear y iniciar operación
        manager = get_operation_manager()
        operation_id = manager.create_operation(
            "test_operation",
            total_items=10,
            notification_interval=0.5
        )
        
        success = manager.start_operation(operation_id, test_operation_func)
        
        return jsonify({
            'success': success,
            'operation_id': operation_id,
            'message': 'Operación de prueba iniciada'
        })
        
    except Exception as e:
        logger.error(f"Error creando operación de prueba: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Funciones auxiliares
def register_maintenance_routes(app):
    """
    Registrar rutas de mantenimiento en la aplicación Flask
    """
    app.register_blueprint(maintenance_bp)
    logger.info("🌐 Rutas de mantenimiento registradas")


def start_websocket_server():
    """
    Iniciar servidor WebSocket en thread separado
    """
    import threading
    import asyncio
    
    def run_websocket():
        try:
            manager = get_websocket_manager()
            asyncio.run(manager.start_server())
        except Exception as e:
            logger.error(f"Error iniciando servidor WebSocket: {e}")
    
    thread = threading.Thread(target=run_websocket, daemon=True)
    thread.start()
    logger.info("🔗 Servidor WebSocket iniciado en thread separado")
    return thread