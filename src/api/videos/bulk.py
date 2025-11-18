"""
Tag-Flow V2 - Videos Bulk Operations API
API endpoints for bulk video operations: reanalyze, delete, restore, update, edit
"""

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

videos_bulk_bp = Blueprint('videos_bulk', __name__, url_prefix='/api')

@videos_bulk_bp.route('/videos/reanalyze', methods=['POST'])
def api_bulk_reanalyze_videos():
    """API para reanalizar múltiples videos"""
    try:
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        force = data.get('force', False)
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No se proporcionaron IDs de videos'}), 400
        
        # Validar que todos los IDs sean números enteros
        try:
            video_ids = [int(vid) for vid in video_ids]
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Todos los IDs deben ser números enteros'}), 400
        
        from src.service_factory import get_database
        db = get_database()
        
        # Verificar que todos los videos existen
        missing_videos = []
        for video_id in video_ids:
            video = db.get_video(video_id)
            if not video:
                missing_videos.append(video_id)
        
        if missing_videos:
            return jsonify({
                'success': False, 
                'error': f'Videos no encontrados: {", ".join(map(str, missing_videos))}'
            }), 404
        
        # Marcar todos los videos como procesando
        for video_id in video_ids:
            db.update_video(video_id, {
                'processing_status': 'procesando',
                'error_message': None
            })
        
        def run_bulk_reanalysis():
            try:
                cmd = [sys.executable, 'main.py', '--reanalyze-video', ','.join(map(str, video_ids))]
                if force:
                    cmd.append('--force')
                
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                env['PYTHONUNBUFFERED'] = '1'
                
                result = subprocess.run(
                    cmd,
                    cwd=Path.cwd(),
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    env=env,
                    timeout=600
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr or 'Error desconocido en el reanálisis masivo'
                    for video_id in video_ids:
                        db.update_video(video_id, {
                            'processing_status': 'error',
                            'error_message': error_msg
                        })
                    logger.error(f"Error en reanálisis masivo: {error_msg}")
                
            except subprocess.TimeoutExpired:
                error_msg = 'Timeout: El reanálisis masivo tomó demasiado tiempo'
                for video_id in video_ids:
                    db.update_video(video_id, {
                        'processing_status': 'error',
                        'error_message': error_msg
                    })
                logger.error(f"Timeout en reanálisis masivo: {error_msg}")
            except Exception as e:
                for video_id in video_ids:
                    db.update_video(video_id, {
                        'processing_status': 'error',
                        'error_message': f'Error iniciando reanálisis masivo: {str(e)}'
                    })
                logger.error(f"Error ejecutando reanálisis masivo: {e}")
        
        # Ejecutar en thread separado
        import threading
        thread = threading.Thread(target=run_bulk_reanalysis)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Reanálisis masivo iniciado para {len(video_ids)} videos',
            'video_ids': video_ids,
            'total_videos': len(video_ids)
        })
        
    except Exception as e:
        logger.error(f"Error en reanálisis masivo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bulk_bp.route('/videos/delete-bulk', methods=['POST'])
def api_bulk_delete_videos():
    """API para eliminar múltiples videos (soft delete)"""
    try:
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No video IDs provided'}), 400
        
        from src.service_factory import get_database
        db = get_database()
        
        success_count = 0
        for video_id in video_ids:
            if db.soft_delete_video(video_id):
                success_count += 1
        
        return jsonify({
            'success': True,
            'message': f'{success_count} videos moved to trash',
            'deleted_count': success_count
        })
        
    except Exception as e:
        logger.error(f"Error en eliminación masiva: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@videos_bulk_bp.route('/videos/restore-bulk', methods=['POST'])
def api_bulk_restore_videos():
    """API para restaurar múltiples videos desde papelera"""
    try:
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No video IDs provided'}), 400
        
        from src.service_factory import get_database
        db = get_database()
        
        success_count = 0
        for video_id in video_ids:
            if db.restore_video(video_id):
                success_count += 1
        
        return jsonify({
            'success': True,
            'message': f'{success_count} videos restored from trash',
            'restored_count': success_count
        })
        
    except Exception as e:
        logger.error(f"Error en restauración masiva: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



