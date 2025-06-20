"""
Tag-Flow V2 - Procesador de Videos
Análisis y extracción de metadatos de videos TikTok/MMD
"""

import cv2
import subprocess
from moviepy.editor import VideoFileClip
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
import os
import tempfile

from config import config

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Procesador principal de videos para extracción de metadatos"""
    
    def __init__(self):
        self.thumbnail_size = config.THUMBNAIL_SIZE
        self.thumbnails_path = config.THUMBNAILS_PATH
        self.thumbnails_path.mkdir(parents=True, exist_ok=True)
    
    def extract_metadata(self, video_path: Path) -> Dict:
        """Extraer metadatos completos del video"""
        try:
            metadata = {
                'file_path': str(video_path),
                'file_name': video_path.name,
                'file_size': video_path.stat().st_size,
                'duration_seconds': None,
                'width': None,
                'height': None,
                'fps': None,
                'has_audio': False
            }
            
            # Usar OpenCV para datos básicos
            cap = cv2.VideoCapture(str(video_path))
            if cap.isOpened():
                # Dimensiones
                metadata['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                metadata['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))                
                # FPS
                metadata['fps'] = cap.get(cv2.CAP_PROP_FPS)
                
                # Duración (frames / fps)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if metadata['fps'] > 0:
                    metadata['duration_seconds'] = total_frames / metadata['fps']
                
                cap.release()
            
            # Usar MoviePy para verificar audio
            try:
                with VideoFileClip(str(video_path)) as clip:
                    metadata['has_audio'] = clip.audio is not None
                    if not metadata['duration_seconds']:
                        metadata['duration_seconds'] = clip.duration
            except Exception as e:
                logger.warning(f"Error con MoviePy para {video_path}: {e}")
            
            logger.info(f"Metadatos extraídos de {video_path.name}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo metadatos de {video_path}: {e}")
            return {'file_path': str(video_path), 'file_name': video_path.name, 'error': str(e)}
    
    def generate_thumbnail(self, video_path: Path, timestamp: float = 1.0) -> Optional[Path]:
        """Generar thumbnail del video en el timestamp especificado"""
        try:
            # Nombre del thumbnail
            thumbnail_name = f"{video_path.stem}_thumb.jpg"
            thumbnail_path = self.thumbnails_path / thumbnail_name
            
            # Si ya existe, no regenerar
            if thumbnail_path.exists():
                return thumbnail_path            
            # Abrir video
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                logger.error(f"No se pudo abrir el video: {video_path}")
                return None
            
            # Calcular frame del timestamp
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            target_frame = min(int(timestamp * fps), total_frames - 1)
            
            # Ir al frame objetivo
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                logger.error(f"No se pudo extraer frame de {video_path}")
                return None
            
            # Redimensionar manteniendo aspecto
            height, width = frame.shape[:2]
            target_width, target_height = self.thumbnail_size
            
            # Calcular dimensiones manteniendo aspecto
            aspect_ratio = width / height
            if aspect_ratio > target_width / target_height:
                new_width = target_width
                new_height = int(target_width / aspect_ratio)
            else:
                new_height = target_height
                new_width = int(target_height * aspect_ratio)
            
            # Redimensionar
            resized = cv2.resize(frame, (new_width, new_height))
            
            # Guardar thumbnail
            success = cv2.imwrite(str(thumbnail_path), resized)
            
            if success:
                logger.info(f"Thumbnail generado: {thumbnail_path}")
                return thumbnail_path
            else:
                logger.error(f"Error guardando thumbnail: {thumbnail_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error generando thumbnail para {video_path}: {e}")
            return None
    
    def extract_audio(self, video_path: Path, duration: int = 30) -> Optional[Path]:
        """Extraer audio del video para análisis musical"""
        try:
            # Crear archivo temporal para audio
            audio_temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            audio_path = Path(audio_temp.name)
            audio_temp.close()
            
            # Extraer audio con ffmpeg (más rápido que MoviePy)
            cmd = [
                'ffmpeg', '-i', str(video_path),
                '-t', str(duration),  # Primeros N segundos
                '-vn',  # Sin video
                '-acodec', 'pcm_s16le',  # Codec de audio
                '-ar', '44100',  # Sample rate
                '-ac', '2',  # Stereo
                '-y',  # Sobrescribir
                str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and audio_path.exists():
                logger.info(f"Audio extraído: {audio_path}")
                return audio_path
            else:
                logger.error(f"Error extrayendo audio: {result.stderr}")
                return None                
        except Exception as e:
            logger.error(f"Error extrayendo audio de {video_path}: {e}")
            return None
    
    def is_valid_video(self, file_path: Path) -> bool:
        """Verificar si el archivo es un video válido"""
        if not file_path.exists():
            return False
            
        # Extensiones de video soportadas
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        if file_path.suffix.lower() not in video_extensions:
            return False
        
        # Verificar que se puede abrir con OpenCV
        try:
            cap = cv2.VideoCapture(str(file_path))
            is_valid = cap.isOpened()
            cap.release()
            return is_valid
        except:
            return False
    
    def get_video_frame(self, video_path: Path, timestamp: float) -> Optional[bytes]:
        """Obtener frame específico como bytes para análisis de caras"""
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return None
            
            # Ir al timestamp específico
            fps = cap.get(cv2.CAP_PROP_FPS)
            target_frame = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Convertir a bytes (JPEG)
                _, buffer = cv2.imencode('.jpg', frame)
                return buffer.tobytes()
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo frame de {video_path}: {e}")
            return None

# Instancia global del procesador
video_processor = VideoProcessor()