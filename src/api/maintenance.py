"""
Tag-Flow V2 - Maintenance API Blueprint
API endpoints para sistema de mantenimiento avanzado
"""

import json
from flask import Blueprint, request, jsonify, render_template
import logging

logger = logging.getLogger(__name__)

# Import del sistema de mantenimiento
try:
    from src.maintenance_api import get_maintenance_api
    from src.maintenance.operation_manager import OperationPriority
    MAINTENANCE_AVAILABLE = True
except ImportError:
    # logger.warning("Sistema de mantenimiento no disponible")
    MAINTENANCE_AVAILABLE = False
    
    # Crear clase mock para OperationPriority si no está disponible
    class OperationPriority:
        LOW = 'low'
        MEDIUM = 'medium'
        HIGH = 'high'

from src.database import db

maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/api/maintenance')

@maintenance_bp.route('/operations', methods=['GET'])
def api_get_operations():
    """API para obtener todas las operaciones de mantenimiento"""
    try:
        if not MAINTENANCE_AVAILABLE:
            return jsonify({'success': False, 'error': 'Maintenance system not available'}), 503
        
        api = get_maintenance_api()
        operations = api.get_all_operations()
        
        return jsonify({
            'success': True,
            'operations': operations
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo operaciones: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/operation/<operation_id>', methods=['GET'])
def api_get_operation(operation_id):
    """API para obtener una operación específica"""
    try:
        if not MAINTENANCE_AVAILABLE:
            return jsonify({'success': False, 'error': 'Maintenance system not available'}), 503
        
        api = get_maintenance_api()
        operation = api.get_operation_status(operation_id)
        
        if operation:
            return jsonify({
                'success': True,
                'operation': operation
            })
        else:
            return jsonify({'success': False, 'error': 'Operation not found'}), 404
        
    except Exception as e:
        logger.error(f"Error obteniendo operación {operation_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/operation/<operation_id>/cancel', methods=['POST'])
def api_cancel_operation(operation_id):
    """API para cancelar una operación"""
    try:
        if not MAINTENANCE_AVAILABLE:
            return jsonify({'success': False, 'error': 'Maintenance system not available'}), 503
        
        api = get_maintenance_api()
        success = api.cancel_operation(operation_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Operation {operation_id} cancelled'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to cancel operation'}), 500
        
    except Exception as e:
        logger.error(f"Error cancelando operación {operation_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/thumbnails/regenerate', methods=['POST'])
def api_regenerate_thumbnails():
    """API para regenerar thumbnails"""
    try:
        if not MAINTENANCE_AVAILABLE:
            return jsonify({'success': False, 'error': 'Maintenance system not available'}), 503
        
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        force = data.get('force', False)
        priority = data.get('priority', 'medium')
        
        # Convertir string priority a enum
        priority_enum = getattr(OperationPriority, priority.upper(), OperationPriority.MEDIUM)
        
        api = get_maintenance_api()
        operation_id = api.regenerate_thumbnails_bulk(
            video_ids=video_ids,
            force=force,
            priority=priority_enum
        )
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': f'Thumbnail regeneration started for {len(video_ids)} videos'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando regeneración de thumbnails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/thumbnails/populate', methods=['POST'])
def api_populate_thumbnails():
    """API para poblar thumbnails faltantes"""
    try:
        if not MAINTENANCE_AVAILABLE:
            return jsonify({'success': False, 'error': 'Maintenance system not available'}), 503
        
        data = request.get_json() or {}
        limit = data.get('limit', 100)
        priority = data.get('priority', 'medium')
        
        priority_enum = getattr(OperationPriority, priority.upper(), OperationPriority.MEDIUM)
        
        api = get_maintenance_api()
        operation_id = api.populate_missing_thumbnails(
            limit=limit,
            priority=priority_enum
        )
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': f'Thumbnail population started (limit: {limit})'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando población de thumbnails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/thumbnails/clean', methods=['POST'])
def api_clean_thumbnails():
    """API para limpiar thumbnails huérfanos"""
    try:
        if not MAINTENANCE_AVAILABLE:
            return jsonify({'success': False, 'error': 'Maintenance system not available'}), 503
        
        data = request.get_json() or {}
        priority = data.get('priority', 'low')
        
        priority_enum = getattr(OperationPriority, priority.upper(), OperationPriority.LOW)
        
        api = get_maintenance_api()
        operation_id = api.cleanup_orphaned_thumbnails(priority=priority_enum)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': 'Thumbnail cleanup started'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando limpieza de thumbnails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/system/health', methods=['GET'])
def api_system_health():
    """API para obtener estado de salud del sistema"""
    try:
        if not MAINTENANCE_AVAILABLE:
            return jsonify({'success': False, 'error': 'Maintenance system not available'}), 503
        
        api = get_maintenance_api()
        health = api.get_system_health()
        
        return jsonify({
            'success': True,
            'health': health
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo salud del sistema: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/operations/cleanup', methods=['POST'])
def api_cleanup_operations():
    """API para limpiar operaciones completadas"""
    try:
        if not MAINTENANCE_AVAILABLE:
            return jsonify({'success': False, 'error': 'Maintenance system not available'}), 503
        
        data = request.get_json() or {}
        max_age_hours = data.get('max_age_hours', 24)
        
        api = get_maintenance_api()
        cleaned_count = api.cleanup_completed_operations(max_age_hours=max_age_hours)
        
        return jsonify({
            'success': True,
            'cleaned_count': cleaned_count,
            'message': f'Cleaned {cleaned_count} old operations'
        })
        
    except Exception as e:
        logger.error(f"Error limpiando operaciones: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/database/populate', methods=['POST'])
def api_populate_database():
    """API para poblar base de datos"""
    try:
        if not MAINTENANCE_AVAILABLE:
            return jsonify({'success': False, 'error': 'Maintenance system not available'}), 503
        
        data = request.get_json() or {}
        source = data.get('source', 'all')
        limit = data.get('limit', None)
        priority = data.get('priority', 'high')
        
        priority_enum = getattr(OperationPriority, priority.upper(), OperationPriority.HIGH)
        
        api = get_maintenance_api()
        operation_id = api.populate_database(
            source=source,
            limit=limit,
            priority=priority_enum
        )
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': f'Database population started from {source}'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando población de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/database/optimize', methods=['POST'])
def api_optimize_database():
    """API para optimizar base de datos"""
    try:
        if not MAINTENANCE_AVAILABLE:
            return jsonify({'success': False, 'error': 'Maintenance system not available'}), 503
        
        data = request.get_json() or {}
        priority = data.get('priority', 'medium')
        
        priority_enum = getattr(OperationPriority, priority.upper(), OperationPriority.MEDIUM)
        
        api = get_maintenance_api()
        operation_id = api.optimize_database(priority=priority_enum)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': 'Database optimization started'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando optimización de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/database/clear', methods=['POST'])
def api_clear_database():
    """API para limpiar base de datos"""
    try:
        if not MAINTENANCE_AVAILABLE:
            return jsonify({'success': False, 'error': 'Maintenance system not available'}), 503
        
        data = request.get_json() or {}
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                'success': False,
                'error': 'Confirmation required for this dangerous operation'
            }), 400
        
        priority = data.get('priority', 'high')
        priority_enum = getattr(OperationPriority, priority.upper(), OperationPriority.HIGH)
        
        api = get_maintenance_api()
        operation_id = api.clear_database(priority=priority_enum)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': 'Database clearing started'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando limpieza de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/database/backup', methods=['POST'])
def api_backup_database():
    """API para hacer backup de base de datos"""
    try:
        if not MAINTENANCE_AVAILABLE:
            return jsonify({'success': False, 'error': 'Maintenance system not available'}), 503
        
        data = request.get_json() or {}
        priority = data.get('priority', 'medium')
        
        priority_enum = getattr(OperationPriority, priority.upper(), OperationPriority.MEDIUM)
        
        api = get_maintenance_api()
        operation_id = api.backup_database(priority=priority_enum)
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': 'Database backup started'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando backup de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/database/stats', methods=['GET'])
def api_database_stats():
    """API para obtener estadísticas de base de datos"""
    try:
        stats = db.get_detailed_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Ruta adicional para el monitor de mantenimiento
@maintenance_bp.route('/monitor')
def maintenance_monitor():
    """Página del monitor de mantenimiento"""
    try:
        return render_template('maintenance_dashboard.html')
    except Exception as e:
        logger.error(f"Error en página de monitor: {e}")
        return render_template('error.html', 
                             error="Error al cargar el monitor de mantenimiento",
                             details=str(e)), 500