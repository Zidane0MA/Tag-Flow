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

@admin_bp.route('/api/admin/populate-db', methods=['POST'])
def api_populate_db():
    """API para poblar la base de datos desde fuentes externas"""
    try:
        data = request.get_json() or {}
        source = data.get('source', 'all')
        limit = data.get('limit', None)
        
        def run_populate():
            try:
                logger.info(f"Iniciando población de BD - Source: {source}, Limit: {limit}")
                
                # Ejecutar comando main.py
                cmd = ['python', 'main.py', 'populate-db', '--source', source]
                if limit:
                    cmd.extend(['--limit', str(limit)])
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
                
                if result.returncode == 0:
                    logger.info("Población de BD completada exitosamente")
                else:
                    logger.error(f"Error en población de BD: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error ejecutando población de BD: {e}")
        
        # Ejecutar en thread separado para no bloquear
        thread = threading.Thread(target=run_populate)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': f'Población de BD iniciada desde {source}' + (f' (limit: {limit})' if limit else ''),
            'status': 'running'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando población de BD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/analyze-videos', methods=['POST'])
def api_analyze_videos():
    """API para analizar videos nuevos"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 10)
        platform = data.get('platform', 'all')
        
        def run_analysis():
            try:
                logger.info(f"Iniciando análisis de videos - Platform: {platform}, Limit: {limit}")
                
                # Ejecutar main.py para análisis
                cmd = ['python', 'main.py', '--limit', str(limit)]
                if platform != 'all':
                    cmd.extend(['--platform', platform])
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
                
                if result.returncode == 0:
                    logger.info("Análisis de videos completado exitosamente")
                else:
                    logger.error(f"Error en análisis de videos: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error ejecutando análisis de videos: {e}")
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': f'Análisis iniciado para {limit} videos de {platform}',
            'status': 'running'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando análisis: {e}")
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

@admin_bp.route('/api/admin/backup', methods=['POST'])
def api_backup():
    """API para crear backup del sistema"""
    try:
        def run_backup():
            try:
                logger.info("Iniciando backup del sistema")
                
                cmd = ['python', 'main.py', 'backup']
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
                
                if result.returncode == 0:
                    logger.info("Backup completado exitosamente")
                else:
                    logger.error(f"Error en backup: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error ejecutando backup: {e}")
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=run_backup)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': 'Backup del sistema iniciado',
            'status': 'running'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando backup: {e}")
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

@admin_bp.route('/api/admin/reset-database', methods=['POST'])
def api_reset_database():
    """API para reinicializar la base de datos (PELIGROSO)"""
    try:
        data = request.get_json() or {}
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                'success': False, 
                'error': 'Confirmación requerida para esta operación'
            }), 400
        
        from src.service_factory import get_database
        db = get_database()
        
        # Reinicializar base de datos
        success = db.reset_database()
        
        if success:
            return jsonify({
                'success': True, 
                'message': 'Base de datos reinicializada exitosamente'
            })
        else:
            return jsonify({'success': False, 'error': 'Error reinicializando BD'}), 500
        
    except Exception as e:
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