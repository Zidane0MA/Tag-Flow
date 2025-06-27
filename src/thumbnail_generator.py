"""
Tag-Flow V2 - Generador de Thumbnails
Creación optimizada de miniaturas para videos
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import logging
from typing import Optional, Tuple

from config import config

logger = logging.getLogger(__name__)

class ThumbnailGenerator:
    """Generador avanzado de thumbnails para videos"""
    
    def __init__(self):
        self.output_path = config.THUMBNAILS_PATH
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        self.thumbnail_size = config.THUMBNAIL_SIZE
        self.quality = 85  # Calidad JPEG
        
        # Configuración de watermark (opcional)
        self.add_watermark = True
        self.watermark_text = "Tag-Flow"
        
    def generate_thumbnail(self, video_path: Path, timestamp: float = 3.0, 
                          force_regenerate: bool = False) -> Optional[Path]:
        """
        Generar thumbnail optimizado de un video
        
        Args:
            video_path: Ruta al video
            timestamp: Momento del video para captura (segundos)
            force_regenerate: Forzar regeneración si ya existe
            
        Returns:
            Path al thumbnail generado o None si falla
        """
        try:
            # Generar nombre del thumbnail
            thumbnail_name = f"{video_path.stem}_thumb.jpg"
            thumbnail_path = self.output_path / thumbnail_name
            
            # Si ya existe y no forzamos regeneración
            if thumbnail_path.exists() and not force_regenerate:
                return thumbnail_path
            
            # Extraer frame del video
            frame = self._extract_frame(video_path, timestamp)
            if frame is None:
                logger.error(f"No se pudo extraer frame de {video_path}")
                return None
            
            # Procesar imagen
            processed_image = self._process_frame(frame)
            
            # Añadir watermark si está habilitado
            if self.add_watermark:
                processed_image = self._add_watermark(processed_image)
            
            # Guardar thumbnail
            processed_image.save(
                thumbnail_path, 
                'JPEG', 
                quality=self.quality,
                optimize=True
            )
            
            logger.info(f"Thumbnail generado: {thumbnail_path}")
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error generando thumbnail para {video_path}: {e}")
            return None
    
    def _extract_frame(self, video_path: Path, timestamp: float) -> Optional[np.ndarray]:
        """Extraer frame específico del video"""
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return None
            
            # Obtener información del video
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            # Ajustar timestamp si es mayor que la duración
            if timestamp > duration:
                timestamp = duration * 0.5  # Usar punto medio
            
            # Calcular frame objetivo
            target_frame = min(int(timestamp * fps), total_frames - 1)
            
            # Posicionarse en el frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Convertir de BGR a RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return frame_rgb
            
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo frame: {e}")
            return None
    
    def _process_frame(self, frame: np.ndarray) -> Image.Image:
        """Procesar frame para thumbnail optimizado"""
        # Convertir a PIL Image
        pil_image = Image.fromarray(frame)
        
        # Redimensionar manteniendo aspecto
        pil_image = self._resize_with_aspect_ratio(pil_image)
        
        # Mejorar imagen
        pil_image = self._enhance_image(pil_image)
        
        return pil_image
    
    def _resize_with_aspect_ratio(self, image: Image.Image) -> Image.Image:
        """Redimensionar imagen manteniendo aspecto y añadiendo padding si necesario"""
        target_width, target_height = self.thumbnail_size
        
        # Calcular dimensiones para mantener aspecto
        img_width, img_height = image.size
        aspect_ratio = img_width / img_height
        target_aspect = target_width / target_height
        
        if aspect_ratio > target_aspect:
            # Imagen más ancha - ajustar por ancho
            new_width = target_width
            new_height = int(target_width / aspect_ratio)
        else:
            # Imagen más alta - ajustar por altura
            new_height = target_height
            new_width = int(target_height * aspect_ratio)
        
        # Redimensionar
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crear imagen con padding si es necesario
        if new_width != target_width or new_height != target_height:
            padded_image = Image.new('RGB', (target_width, target_height), (0, 0, 0))
            
            # Centrar imagen
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            
            padded_image.paste(image, (x_offset, y_offset))
            return padded_image
        
        return image
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Mejorar calidad visual del thumbnail"""
        # Aquí se pueden añadir mejoras como:
        # - Ajuste de contraste
        # - Saturación
        # - Nitidez
        
        # Por simplicidad, retornamos la imagen sin modificar
        # En el futuro se pueden añadir filtros con PIL o OpenCV
        return image
    
    def _add_watermark(self, image: Image.Image) -> Image.Image:
        """Añadir watermark discreto al thumbnail"""
        try:
            # Crear copia para no modificar original
            watermarked = image.copy()
            draw = ImageDraw.Draw(watermarked)
            
            # Configuración del watermark
            font_size = max(12, min(image.size) // 30)
            
            try:
                # Intentar usar fuente del sistema
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                # Fallback a fuente por defecto
                font = ImageFont.load_default()
            
            # Posición (esquina inferior derecha)
            text_bbox = draw.textbbox((0, 0), self.watermark_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = image.width - text_width - 10
            y = image.height - text_height - 10
            
            # Dibujar texto con sombra
            shadow_offset = 1
            draw.text((x + shadow_offset, y + shadow_offset), self.watermark_text, 
                     fill=(0, 0, 0, 128), font=font)  # Sombra
            draw.text((x, y), self.watermark_text, 
                     fill=(255, 255, 255, 180), font=font)  # Texto
            
            return watermarked
            
        except Exception as e:
            logger.warning(f"Error añadiendo watermark: {e}")
            return image
    
    def generate_batch_thumbnails(self, video_paths: list[Path], 
                                 timestamp: float = 1.0) -> dict:
        """Generar thumbnails para múltiples videos"""
        results = {
            'successful': 0,
            'failed': 0,
            'thumbnails': [],
            'errors': []
        }
        
        for video_path in video_paths:
            try:
                thumbnail_path = self.generate_thumbnail(video_path, timestamp)
                if thumbnail_path:
                    results['successful'] += 1
                    results['thumbnails'].append(str(thumbnail_path))
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to generate thumbnail for {video_path}")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error with {video_path}: {e}")
        
        logger.info(f"Batch thumbnail generation: {results['successful']} successful, {results['failed']} failed")
        return results

# Instancia global
thumbnail_generator = ThumbnailGenerator()