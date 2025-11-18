"""
Tag-Flow V2 - Video Streaming and Playback API
API endpoints for video streaming, playback, and file system operations
"""

import mimetypes
import platform
import subprocess
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify, Response, send_file

logger = logging.getLogger(__name__)

videos_streaming_bp = Blueprint('videos_streaming', __name__, url_prefix='/api')

@videos_streaming_bp.route('/video/<int:video_id>/open-folder', methods=['POST'])
def api_open_folder(video_id):
    """API para mostrar y seleccionar el archivo de video en el explorador"""
    try:
        from src.service_factory import get_database
        db = get_database()

        # Consultar usando el nuevo esquema (media table)
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.file_path
                FROM media m
                JOIN posts p ON m.post_id = p.id
                WHERE m.id = ? AND p.deleted_at IS NULL
            """, (video_id,))

            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Video not found'}), 404

            video = {'file_path': row[0]}

        video_path = Path(video['file_path'])
        if not video_path.exists():
            return jsonify({'success': False, 'error': 'Video file not found'}), 404
        
        folder_path = video_path.parent
        
        # Mostrar archivo específico según el sistema operativo
        system = platform.system()
        
        if system == "Windows":
            # En Windows, usar método directo y simple que funcione correctamente
            windows_path = str(video_path).replace('/', '\\')
            
            try:
                # Abrir el explorador con el archivo seleccionado y traer al frente
                powershell_cmd = f'''
                # Abrir explorer con el archivo seleccionado
                Start-Process "explorer.exe" -ArgumentList "/select,`"{windows_path}`""
                
                # Esperar un momento para que se abra
                Start-Sleep -Milliseconds 1000
                
                # Traer la ventana del explorador al frente
                Add-Type @"
                    using System;
                    using System.Runtime.InteropServices;
                    public class Win32 {{
                        [DllImport("user32.dll")]
                        public static extern bool SetForegroundWindow(IntPtr hWnd);
                        [DllImport("user32.dll")]
                        public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
                        [DllImport("user32.dll")]
                        public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                    }}
"@
                
                # Buscar y activar la ventana del explorador
                $shell = New-Object -ComObject Shell.Application
                $windows = $shell.Windows()
                foreach ($window in $windows) {{
                    if ($window.Name -eq "Windows Explorer") {{
                        $hwnd = $window.HWND
                        [Win32]::ShowWindow([IntPtr]$hwnd, 9)  # SW_RESTORE
                        [Win32]::SetForegroundWindow([IntPtr]$hwnd)
                        break
                    }}
                }}
                '''
                
                # Ejecutar PowerShell con el comando completo
                result = subprocess.run([
                    'powershell', '-ExecutionPolicy', 'Bypass', '-Command', powershell_cmd
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    return jsonify({
                        'success': True,
                        'message': f'Archivo mostrado en el explorador: {video_path.name}',
                        'folder_path': str(folder_path),
                        'video_path': str(video_path)
                    })
                else:
                    # Fallback a método simple si PowerShell falla
                    subprocess.run(['explorer', '/select,', str(video_path)], check=True)
                    return jsonify({
                        'success': True,
                        'message': f'Archivo mostrado en el explorador (fallback): {video_path.name}',
                        'folder_path': str(folder_path),
                        'video_path': str(video_path)
                    })
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"Timeout abriendo explorador para video {video_id}")
                return jsonify({'success': False, 'error': 'Timeout opening file explorer'}), 500
            except Exception as e:
                logger.warning(f"Error con PowerShell para video {video_id}: {e}")
                # Fallback a método simple
                try:
                    subprocess.run(['explorer', '/select,', str(video_path)], check=True)
                    return jsonify({
                        'success': True,
                        'message': f'Archivo mostrado en el explorador: {video_path.name}',
                        'folder_path': str(folder_path),
                        'video_path': str(video_path)
                    })
                except Exception as fallback_error:
                    logger.error(f"Error con fallback explorer para video {video_id}: {fallback_error}")
                    return jsonify({'success': False, 'error': str(fallback_error)}), 500
                    
        elif system == "Darwin":  # macOS
            try:
                subprocess.run(['open', '-R', str(video_path)], check=True)
                return jsonify({
                    'success': True,
                    'message': f'Archivo mostrado en Finder: {video_path.name}',
                    'folder_path': str(folder_path),
                    'video_path': str(video_path)
                })
            except Exception as e:
                logger.error(f"Error abriendo Finder para video {video_id}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
                
        elif system == "Linux":
            try:
                # Intentar con xdg-open para abrir el directorio
                subprocess.run(['xdg-open', str(folder_path)], check=True)
                return jsonify({
                    'success': True,
                    'message': f'Carpeta abierta: {folder_path}',
                    'folder_path': str(folder_path),
                    'video_path': str(video_path)
                })
            except Exception as e:
                logger.error(f"Error abriendo directorio en Linux para video {video_id}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        else:
            return jsonify({'success': False, 'error': f'Sistema operativo no soportado: {system}'}), 400
            
    except Exception as e:
        logger.error(f"Error abriendo carpeta para video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@videos_streaming_bp.route('/video-stream/<int:video_id>')
def api_stream_video(video_id):
    """Stream video file directly using new schema"""
    try:
        from src.service_factory import get_database
        import os

        db = get_database()

        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.file_path, m.media_type, m.file_name
                FROM media m
                JOIN posts p ON m.post_id = p.id
                WHERE m.id = ? AND p.deleted_at IS NULL
            """, (video_id,))

            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Video not found'}), 404

            file_path = row[0]
            media_type = row[1]
            file_name = row[2]

            if not os.path.exists(file_path):
                return jsonify({'error': 'File not found on disk'}), 404

            # Determinar content type
            content_type = 'video/mp4'
            if media_type == 'image':
                if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                    content_type = 'image/jpeg'
                elif file_path.lower().endswith('.png'):
                    content_type = 'image/png'
                elif file_path.lower().endswith('.gif'):
                    content_type = 'image/gif'
            elif media_type == 'video':
                if file_path.lower().endswith('.mp4'):
                    content_type = 'video/mp4'
                elif file_path.lower().endswith('.webm'):
                    content_type = 'video/webm'
                elif file_path.lower().endswith('.mov'):
                    content_type = 'video/quicktime'

            # Usar send_file para streaming eficiente
            return send_file(
                file_path,
                mimetype=content_type,
                as_attachment=False,
                download_name=file_name
            )

    except Exception as e:
        logger.error(f"Error streaming video {video_id}: {e}")
        return jsonify({'error': str(e)}), 500