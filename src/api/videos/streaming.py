"""
Tag-Flow V2 - Video Streaming and Playback API
API endpoints for video streaming, playback, and file system operations
"""

import mimetypes
import platform
import subprocess
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

videos_streaming_bp = Blueprint('videos_streaming', __name__, url_prefix='/api')


@videos_streaming_bp.route('/video/<int:video_id>/play')
def api_play_video(video_id):
    """API para obtener información de reproducción del video"""
    try:
        from src.service_factory import get_database
        db = get_database()
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        video_path = Path(video['file_path'])
        if not video_path.exists():
            return jsonify({'success': False, 'error': 'Video file not found'}), 404
        
        # Verificar que el archivo sea accesible
        mime_type, _ = mimetypes.guess_type(str(video_path))
        
        return jsonify({
            'success': True,
            'video_path': str(video_path),
            'file_name': video['file_name'],
            'mime_type': mime_type,
            'file_size': video.get('file_size', 0),
            'duration': video.get('duration_seconds', 0)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo info de reproducción para video {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@videos_streaming_bp.route('/video/<int:video_id>/open-folder', methods=['POST'])
def api_open_folder(video_id):
    """API para mostrar y seleccionar el archivo de video en el explorador"""
    try:
        from src.service_factory import get_database
        db = get_database()
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
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