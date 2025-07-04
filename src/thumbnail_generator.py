"""
Tag-Flow V2 - Generador de Thumbnails
Creación optimizada de miniaturas para videos
"""

import cv2
import numpy as np
import time
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
        self.add_watermark = False
        self.watermark_text = "Tag-Flow"
        
    def generate_thumbnail(self, video_path: Path, timestamp: float = 3.0, 
                          force_regenerate: bool = False) -> Optional[Path]:
        """
        🚀 OPTIMIZADO: Generar thumbnail optimizado de un video con caché y validación
        
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
            
            # Si ya existe y no forzamos regeneración, validar thumbnail
            if thumbnail_path.exists() and not force_regenerate:
                if self._is_thumbnail_valid(thumbnail_path):
                    return thumbnail_path
                else:
                    # Thumbnail corrupto, eliminarlo y regenerar
                    logger.debug(f"Thumbnail corrupto detectado, eliminando: {thumbnail_path}")
                    try:
                        thumbnail_path.unlink()
                    except Exception as e:
                        logger.warning(f"Error eliminando thumbnail corrupto: {e}")
            
            # Extraer frame del video con optimizaciones
            frame = self._extract_frame_optimized(video_path, timestamp)
            if frame is None:
                logger.error(f"No se pudo extraer frame de {video_path}")
                return None
            
            # Procesar imagen con optimizaciones
            processed_image = self._process_frame_optimized(frame)
            
            # Añadir watermark si está habilitado
            if self.add_watermark:
                processed_image = self._add_watermark(processed_image)
            
            # Guardar thumbnail con optimizaciones
            self._save_thumbnail_optimized(processed_image, thumbnail_path)
            
            logger.debug(f"Thumbnail generado: {thumbnail_path}")
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error generando thumbnail para {video_path}: {e}")
            return None
    
    def _is_thumbnail_valid(self, thumbnail_path: Path) -> bool:
        """Verificar si un thumbnail es válido"""
        try:
            # Verificar que el archivo existe
            if not thumbnail_path.exists():
                return False
            
            # Verificar tamaño mínimo (thumbnails muy pequeños probablemente corruptos)
            if thumbnail_path.stat().st_size < 1024:  # Menos de 1KB
                return False
            
            # Intentar abrir la imagen para verificar validez
            with Image.open(thumbnail_path) as img:
                # Verificar que tiene dimensiones válidas
                if img.width < 50 or img.height < 50:
                    return False
                
                # Verificar que tiene el tamaño esperado
                expected_width, expected_height = self.thumbnail_size
                if abs(img.width - expected_width) > 10 or abs(img.height - expected_height) > 10:
                    return False
                
                # Verificar que no está completamente negro
                if hasattr(img, 'getextrema'):
                    extrema = img.getextrema()
                    if isinstance(extrema, tuple) and len(extrema) == 2 and extrema[0] == extrema[1] == 0:
                        return False
                        
            return True
            
        except Exception:
            return False
    
    def _extract_frame_optimized(self, video_path: Path, timestamp: float) -> Optional[np.ndarray]:
        """🚀 OPTIMIZADO: Extraer frame específico del video con mejor manejo de errores"""
        cap = None
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                logger.warning(f"No se pudo abrir video: {video_path}")
                return None
            
            # Obtener información del video
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Validar FPS
            if fps <= 0:
                logger.warning(f"FPS inválido ({fps}) para {video_path}")
                fps = 30  # Asumir 30 FPS por defecto
            
            # Calcular duración
            duration = total_frames / fps if fps > 0 else 0
            
            # Ajustar timestamp si es mayor que la duración
            if timestamp > duration:
                timestamp = duration * 0.5  # Usar punto medio
            
            # Si el timestamp es muy pequeño, usar un segundo
            if timestamp < 1.0:
                timestamp = min(1.0, duration * 0.3)
            
            # Calcular frame objetivo
            target_frame = min(int(timestamp * fps), total_frames - 1)
            target_frame = max(0, target_frame)  # Asegurar que sea positivo
            
            # Posicionarse en el frame con manejo de errores
            success = cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            if not success:
                logger.warning(f"No se pudo posicionar en frame {target_frame}")
                # Intentar con frame 0
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # Leer frame
            ret, frame = cap.read()
            
            if ret and frame is not None:
                # Verificar que el frame tiene contenido válido
                if frame.size > 0:
                    # Convertir de BGR a RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    return frame_rgb
                else:
                    logger.warning(f"Frame vacío en {video_path}")
            
            # Si falló, intentar con frame 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            
            if ret and frame is not None and frame.size > 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return frame_rgb
            
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo frame de {video_path}: {e}")
            return None
        finally:
            if cap is not None:
                cap.release()
    
    def _process_frame_optimized(self, frame: np.ndarray) -> Image.Image:
        """🚀 OPTIMIZADO: Procesar frame para thumbnail con mejor calidad"""
        # Convertir a PIL Image
        pil_image = Image.fromarray(frame)
        
        # Redimensionar manteniendo aspecto con algoritmo de alta calidad
        pil_image = self._resize_with_aspect_ratio_optimized(pil_image)
        
        # Mejorar imagen con filtros básicos
        pil_image = self._enhance_image_optimized(pil_image)
        
        return pil_image
    
    def _resize_with_aspect_ratio_optimized(self, image: Image.Image) -> Image.Image:
        """🚀 OPTIMIZADO: Redimensionar imagen con mejor calidad y manejo de aspectos"""
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
        
        # Redimensionar con algoritmo de alta calidad
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crear imagen con padding si es necesario
        if new_width != target_width or new_height != target_height:
            # Usar color de padding inteligente basado en bordes
            padding_color = self._get_intelligent_padding_color(image)
            padded_image = Image.new('RGB', (target_width, target_height), padding_color)
            
            # Centrar imagen
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            
            padded_image.paste(image, (x_offset, y_offset))
            return padded_image
        
        return image
    
    def _get_intelligent_padding_color(self, image: Image.Image) -> tuple:
        """Obtener color de padding inteligente basado en los bordes de la imagen"""
        try:
            # Obtener píxeles de los bordes
            width, height = image.size
            
            # Muestrear píxeles de los bordes
            border_pixels = []
            
            # Borde superior e inferior
            for x in range(0, width, max(1, width // 10)):
                border_pixels.append(image.getpixel((x, 0)))
                border_pixels.append(image.getpixel((x, height - 1)))
            
            # Borde izquierdo y derecho
            for y in range(0, height, max(1, height // 10)):
                border_pixels.append(image.getpixel((0, y)))
                border_pixels.append(image.getpixel((width - 1, y)))
            
            # Calcular color promedio
            if border_pixels:
                avg_r = sum(p[0] for p in border_pixels) // len(border_pixels)
                avg_g = sum(p[1] for p in border_pixels) // len(border_pixels)
                avg_b = sum(p[2] for p in border_pixels) // len(border_pixels)
                
                # Oscurecer ligeramente para mejor contraste
                return (max(0, avg_r - 20), max(0, avg_g - 20), max(0, avg_b - 20))
            
        except Exception:
            pass
        
        # Fallback a negro
        return (0, 0, 0)
    
    def _enhance_image_optimized(self, image: Image.Image) -> Image.Image:
        """🚀 OPTIMIZADO: Mejorar calidad visual del thumbnail con filtros básicos"""
        try:
            from PIL import ImageEnhance
            
            # Mejorar contraste ligeramente
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
            
            # Mejorar saturación ligeramente
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.05)
            
            # Mejorar nitidez ligeramente
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            return image
            
        except Exception as e:
            logger.debug(f"Error aplicando mejoras de imagen: {e}")
            return image
    
    def _save_thumbnail_optimized(self, image: Image.Image, thumbnail_path: Path):
        """🚀 OPTIMIZADO: Guardar thumbnail con configuración optimizada"""
        try:
            # Asegurar directorio
            thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Configuración optimizada para JPEG
            save_kwargs = {
                'format': 'JPEG',
                'quality': self.quality,
                'optimize': True,
                'progressive': True,  # JPEG progresivo para mejor carga
                'subsampling': 2,     # Subsampling para mejor compresión
            }
            
            # Guardar con configuración optimizada
            image.save(thumbnail_path, **save_kwargs)
            
        except Exception as e:
            logger.error(f"Error guardando thumbnail en {thumbnail_path}: {e}")
            raise
    
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
    
    def generate_batch_thumbnails_optimized(self, video_data_list: list, 
                                          timestamp: float = 1.0, 
                                          force_regenerate: bool = False) -> dict:
        """
        🚀 OPTIMIZADO: Generar thumbnails para múltiples videos con procesamiento paralelo
        
        Args:
            video_data_list: Lista de diccionarios con información de videos
            timestamp: Momento del video para captura (segundos)
            force_regenerate: Forzar regeneración si ya existe
            
        Returns:
            Dict con estadísticas de la operación
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        start_time = time.time()
        
        results = {
            'successful': 0,
            'failed': 0,
            'thumbnails': [],
            'errors': [],
            'skipped': 0
        }
        
        if not video_data_list:
            return results
        
        # Filtrar videos que realmente necesitan thumbnails
        videos_to_process = []
        for video_data in video_data_list:
            video_path = Path(video_data['file_path'])
            
            # Verificar que el archivo existe
            if not video_path.exists():
                results['errors'].append(f"Archivo no existe: {video_path}")
                results['failed'] += 1
                continue
            
            # Verificar si necesita thumbnail
            thumbnail_name = f"{video_path.stem}_thumb.jpg"
            thumbnail_path = self.output_path / thumbnail_name
            
            if thumbnail_path.exists() and not force_regenerate:
                if self._is_thumbnail_valid(thumbnail_path):
                    results['skipped'] += 1
                    continue
            
            videos_to_process.append(video_data)
        
        if not videos_to_process:
            logger.info("No hay videos que procesar para thumbnails")
            return results
        
        # Función para procesar un video individual
        def process_single_video(video_data):
            try:
                video_path = Path(video_data['file_path'])
                
                # Generar thumbnail
                thumbnail_path = self.generate_thumbnail(
                    video_path, 
                    timestamp=timestamp, 
                    force_regenerate=force_regenerate
                )
                
                if thumbnail_path:
                    return {
                        'success': True,
                        'video_path': str(video_path),
                        'thumbnail_path': str(thumbnail_path),
                        'video_name': video_path.name
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Falló generación para {video_path.name}",
                        'video_path': str(video_path)
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Error procesando {video_data.get('file_name', 'unknown')}: {e}",
                    'video_path': video_data.get('file_path', 'unknown')
                }
        
        # Procesamiento en paralelo
        max_workers = min(4, len(videos_to_process))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas
            futures = [executor.submit(process_single_video, video_data) 
                      for video_data in videos_to_process]
            
            # Recopilar resultados
            for i, future in enumerate(as_completed(futures), 1):
                try:
                    result = future.result()
                    
                    if result['success']:
                        results['successful'] += 1
                        results['thumbnails'].append(result['thumbnail_path'])
                        logger.debug(f"✓ Thumbnail: {result['video_name']}")
                    else:
                        results['failed'] += 1
                        results['errors'].append(result['error'])
                        logger.debug(f"✗ Error: {result['error']}")
                    
                    # Progreso cada 10 videos
                    if i % 10 == 0 or i == len(videos_to_process):
                        progress = i / len(videos_to_process) * 100
                        logger.info(f"Progreso thumbnails: {i}/{len(videos_to_process)} ({progress:.1f}%)")
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Error en future: {e}")
        
        # Métricas finales
        end_time = time.time()
        duration = end_time - start_time
        
        results['processing_time'] = duration
        results['throughput'] = results['successful'] / duration if duration > 0 else 0
        
        logger.info(f"Batch thumbnail generation completado:")
        logger.info(f"  Exitosos: {results['successful']}")
        logger.info(f"  Fallidos: {results['failed']}")
        logger.info(f"  Omitidos: {results['skipped']}")
        logger.info(f"  Tiempo: {duration:.2f}s")
        if results['successful'] > 0:
            logger.info(f"  Throughput: {results['throughput']:.1f} thumbnails/segundo")
        
        return results

    def generate_batch_thumbnails(self, video_paths: list[Path], 
                                 timestamp: float = 1.0) -> dict:
        """
        LEGACY: Generar thumbnails para múltiples videos (mantenido para compatibilidad)
        
        Args:
            video_paths: Lista de rutas de videos
            timestamp: Momento del video para captura (segundos)
            
        Returns:
            Dict con estadísticas de la operación
        """
        # Convertir a formato esperado por el método optimizado
        video_data_list = [
            {'file_path': str(path), 'file_name': path.name}
            for path in video_paths
        ]
        
        return self.generate_batch_thumbnails_optimized(
            video_data_list, 
            timestamp=timestamp, 
            force_regenerate=False
        )

# Instancia global
thumbnail_generator = ThumbnailGenerator()