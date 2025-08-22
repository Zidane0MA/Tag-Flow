"""
Tag-Flow V2 - Admin API Blueprint
API endpoints para administración: backup, populate DB, análisis, etc.
"""

import json
import subprocess
import threading
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template
import logging

# Database will be imported lazily within functions

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin_page():
    """Página de administración"""
    try:
        from src.service_factory import get_database
        db = get_database()
        stats = db.get_stats()
        return render_template('admin.html', stats=stats)
    except Exception as e:
        logger.error(f"Error en página de admin: {e}")
        return render_template('error.html', 
                             error="Error al cargar la administración",
                             details=str(e)), 500

@admin_bp.route('/api/admin/analyze-videos', methods=['POST'])
def api_analyze_videos():
    """API para analizar videos nuevos usando AsyncOperationsAPI"""
    try:
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        force = data.get('force', False)
        priority = data.get('priority', 'medium')
        
        if not video_ids:
            return jsonify({
                'success': False, 
                'error': 'video_ids es requerido'
            }), 400
        
        # Usar la nueva API asíncrona
        from src.async_operations_api import get_async_operations_api
        from src.core.operation_manager import OperationPriority
        
        priority_enum = getattr(OperationPriority, priority.upper(), OperationPriority.MEDIUM)
        api = get_async_operations_api()
        operation_id = api.analyze_videos_async(
            video_ids=video_ids,
            force=force,
            priority=priority_enum
        )
        
        return jsonify({
            'success': True, 
            'operation_id': operation_id,
            'message': f'Reanálisis iniciado para {len(video_ids)} videos',
            'status': 'running'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando análisis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/process-videos', methods=['POST'])
def api_process_videos():
    """API para procesamiento de videos usando AsyncOperationsAPI"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', None)
        platform = data.get('platform', None)
        source = data.get('source', 'all')
        priority = data.get('priority', 'high')
        
        # Usar la nueva API asíncrona
        from src.async_operations_api import get_async_operations_api
        from src.core.operation_manager import OperationPriority
        
        priority_enum = getattr(OperationPriority, priority.upper(), OperationPriority.HIGH)
        api = get_async_operations_api()
        operation_id = api.process_videos_async(
            limit=limit,
            platform=platform,
            source=source,
            priority=priority_enum
        )
        
        return jsonify({
            'success': True, 
            'operation_id': operation_id,
            'message': f'Procesamiento iniciado (limit: {limit}, platform: {platform}, source: {source})',
            'status': 'running'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando procesamiento: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/generate-thumbnails', methods=['POST'])
def api_generate_thumbnails():
    """API para generar thumbnails"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 50)
        force = data.get('force', False)
        
        def run_thumbnail_generation():
            try:
                logger.info(f"Iniciando generación de thumbnails - Limit: {limit}, Force: {force}")
                
                cmd = ['python', 'main.py', 'populate-thumbnails', '--limit', str(limit)]
                if force:
                    cmd.append('--force')
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
                
                if result.returncode == 0:
                    logger.info("Generación de thumbnails completada exitosamente")
                else:
                    logger.error(f"Error en generación de thumbnails: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error ejecutando generación de thumbnails: {e}")
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=run_thumbnail_generation)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': f'Generación de thumbnails iniciada (limit: {limit}, force: {force})',
            'status': 'running'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando generación de thumbnails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/optimize-db', methods=['POST'])
def api_optimize_db():
    """API para optimizar la base de datos"""
    try:
        def run_optimization():
            try:
                logger.info("Iniciando optimización de BD")
                
                cmd = ['python', 'main.py', 'optimize-db']
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
                
                if result.returncode == 0:
                    logger.info("Optimización de BD completada exitosamente")
                else:
                    logger.error(f"Error en optimización de BD: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error ejecutando optimización de BD: {e}")
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=run_optimization)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': 'Optimización de BD iniciada',
            'status': 'running'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando optimización: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/verify', methods=['POST'])
def api_verify():
    """API para verificar integridad del sistema"""
    try:
        def run_verification():
            try:
                logger.info("Iniciando verificación de integridad")
                
                cmd = ['python', 'main.py', 'verify']
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
                
                if result.returncode == 0:
                    logger.info("Verificación de integridad completada exitosamente")
                else:
                    logger.error(f"Error en verificación de integridad: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error ejecutando verificación: {e}")
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=run_verification)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': 'Verificación de integridad iniciada',
            'status': 'running'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando verificación: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/empty-trash', methods=['POST'])
def api_empty_trash():
    """API para vaciar la papelera (eliminación permanente)"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Contar videos en papelera antes de eliminar
        trash_count = db.count_videos({'is_deleted': True})
        
        if trash_count == 0:
            return jsonify({
                'success': True, 
                'message': 'La papelera ya está vacía',
                'deleted_count': 0
            })
        
        # Eliminar permanentemente todos los videos en papelera
        success = db.empty_trash()
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'{trash_count} videos eliminados permanentemente',
                'deleted_count': trash_count
            })
        else:
            return jsonify({'success': False, 'error': 'Error vaciando papelera'}), 500
        
    except Exception as e:
        logger.error(f"Error vaciando papelera: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

        logger.error(f"Error reinicializando BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/platforms', methods=['GET'])
def api_get_platforms():
    """API para obtener plataformas disponibles"""
    try:
        from src.service_factory import get_database
        db = get_database()
        platforms = db.get_unique_platforms()
        return jsonify({
            'success': True, 
            'platforms': platforms
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo plataformas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500