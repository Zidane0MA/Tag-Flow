"""
Tag-Flow V2 - Generador de Thumbnails
Creación optimizada de miniaturas para videos
"""

import cv2
import numpy as np
import time
import os
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import logging
from typing import Optional, Tuple

from config import config

logger = logging.getLogger(__name__)

# Instancia global para evitar múltiples inicializaciones
_thumbnail_generator_instance = None

class ThumbnailGenerator:
    """Generador avanzado de thumbnails para videos"""
    
    def __new__(cls):
        global _thumbnail_generator_instance
        if _thumbnail_generator_instance is None:
            _thumbnail_generator_instance = super().__new__(cls)
        return _thumbnail_generator_instance
    
    def __init__(self):
        # Evitar reinicialización si ya se ha inicializado
        if hasattr(self, '_initialized'):
            return
            
        self.output_path = config.THUMBNAILS_PATH
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        self.thumbnail_size = config.THUMBNAIL_SIZE
        # Leer calidad desde configuración del entorno
        self.quality = int(os.getenv('THUMBNAIL_QUALITY', '85'))
        
        # Configuración de watermark (opcional)
        self.add_watermark = False
        self.watermark_text = "Tag-Flow"
        
        # Configuración de optimización para velocidad
        self.enable_image_enhancement = False  # Deshabilitado por defecto para mayor velocidad
        self.fast_mode = True  # Modo rápido activado
        self.enable_validation = os.getenv('ENABLE_THUMBNAIL_VALIDATION', 'true').lower() == 'true'
        self.use_ffmpeg_direct = True  # Usar FFmpeg directo cuando sea posible
        self._last_used_ffmpeg = False  # Flag para tracking
        
        # Cache para intercambiar CPU por RAM
        self.frame_cache = {}  # Cache de frames extraídos
        self.max_cache_size = int(os.getenv('THUMBNAIL_CACHE_SIZE', '50'))  # Máximo frames en cache
        self.use_ram_optimization = True  # Activar optimizaciones de RAM
        self.preload_cache = {}  # Cache para pre-cargar datos de video en RAM
        
        # 🎯 OPTIMIZACIÓN: Tamaño dinámico según modo
        self.adaptive_sizing = os.getenv('ADAPTIVE_THUMBNAIL_SIZE', 'true').lower() == 'true'
        
        # 🎯 CONFIGURACIÓN AUTOMÁTICA: Aplicar modo desde configuración
        thumbnail_mode = config.THUMBNAIL_MODE.lower().strip().replace('"', '').split('#')[0].strip()
        if thumbnail_mode == 'auto':
            self.auto_configure_best_mode()
        else:
            self.configure_thumbnail_mode(thumbnail_mode)
        
    def enable_ultra_fast_mode(self):
        """🚀 Activar modo ultra-rápido GPU para máximo rendimiento"""
        self.fast_mode = True
        self.enable_image_enhancement = False
        self.add_watermark = False
        # Usar calidad mínima para velocidad
        self.quality = min(self.quality, 60)
        # 🎮 GPU: Configuración ultra-rápida
        self._enable_gpu_acceleration = True
        self._gpu_decoder = self._detect_gpu_support()
        self._gpu_mode = 'ultra_fast'  # Modo GPU específico
        
        # 🚀 OPTIMIZACIÓN: Reducir tamaño 5% para ultra velocidad
        if self.adaptive_sizing:
            original_size = self.thumbnail_size
            self.thumbnail_size = (
                int(original_size[0] * 0.95),  # 5% menor
                int(original_size[1] * 0.95)
            )
            logger.info(f"⚡ Tamaño adaptativo: {original_size} → {self.thumbnail_size}")
        
        logger.info(f"⚡ Modo ultra-rápido GPU activado - Máximo rendimiento ({self.thumbnail_size[0]}x{self.thumbnail_size[1]}, calidad {self.quality}, GPU: {self._gpu_decoder or 'CPU fallback'})")
        
    def enable_balanced_mode(self):
        """⚖️ Activar modo balanceado GPU para buena calidad con buen rendimiento"""
        self.fast_mode = True
        self.enable_image_enhancement = True  # Activar mejoras básicas
        self.add_watermark = False
        # Mantener calidad del .env (no sobrescribir)
        # 🎮 GPU: Configuración balanceada
        self._enable_gpu_acceleration = True
        self._gpu_decoder = self._detect_gpu_support()
        self._gpu_mode = 'balanced'  # Modo GPU específico
        self.use_ffmpeg_direct = False  # Forzar post-procesamiento para mejoras
        logger.info(f"⚖️ Modo balanceado GPU activado - Buena calidad + buen rendimiento (calidad {self.quality}, GPU: {self._gpu_decoder or 'CPU fallback'})")
        
    def enable_gpu_mode(self):
        """🎮 Activar modo GPU para máxima calidad con aceleración hardware"""
        self.fast_mode = False
        self.enable_image_enhancement = True
        # Incrementar calidad solo si es menor a 80
        if self.quality < 80:
            self.quality = min(90, self.quality + 15)  # Aumentar más para modo GPU
        # 🎮 GPU: Configuración máxima calidad
        self._enable_gpu_acceleration = True
        self._gpu_decoder = self._detect_gpu_support()
        self._gpu_mode = 'quality'  # Modo GPU de máxima calidad
        logger.info(f"🎮 Modo GPU activado - Máxima calidad con aceleración hardware (calidad {self.quality}, GPU: {self._gpu_decoder or 'CPU fallback'})")
        
    def _detect_gpu_support(self) -> Optional[str]:
        """🎮 Detectar soporte GPU disponible para FFmpeg"""
        try:
            # Probar NVIDIA GPU (NVENC/NVDEC)
            result = subprocess.run(['ffmpeg', '-hwaccels'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'cuda' in output:
                    logger.info("🎮 GPU NVIDIA CUDA detectada")
                    return 'cuda'
                elif 'dxva2' in output:
                    logger.info("🎮 GPU Intel/AMD DirectX Video Acceleration detectada")
                    return 'dxva2'
                elif 'qsv' in output:
                    logger.info("🎮 GPU Intel Quick Sync Video detectada")
                    return 'qsv'
            return None
        except Exception as e:
            logger.debug(f"Error detectando GPU: {e}")
            return None
        
    def _generate_thumbnail_ffmpeg_direct(self, video_path: Path, thumbnail_path: Path, timestamp: float = 3.0) -> bool:
        """🚀 MEJORADO: Generar thumbnail con FFmpeg GPU optimizado por modo"""
        try:
            # Usar timestamp fijo para máximo rendimiento
            fixed_timestamp = min(timestamp, 3.0)
            target_width, target_height = self.thumbnail_size
            
            # 🎮 CONFIGURACIÓN GPU ESPECÍFICA POR MODO
            cmd = ['ffmpeg', '-y']
            gpu_mode = getattr(self, '_gpu_mode', 'balanced')
            
            # Configurar GPU según modo
            if hasattr(self, '_enable_gpu_acceleration') and self._enable_gpu_acceleration and hasattr(self, '_gpu_decoder'):
                if self._gpu_decoder == 'cuda':
                    if gpu_mode == 'ultra_fast':
                        # Modo ultra rápido: decodificación GPU básica
                        cmd.extend(['-hwaccel', 'cuda'])
                    else:
                        # Otros modos: decodificación GPU completa
                        cmd.extend(['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda'])
                elif self._gpu_decoder == 'qsv':
                    cmd.extend(['-hwaccel', 'qsv'])
                elif self._gpu_decoder == 'dxva2':
                    cmd.extend(['-hwaccel', 'dxva2'])
            
            cmd.extend(['-ss', str(fixed_timestamp), '-i', str(video_path)])
            
            # 🎨 FILTROS OPTIMIZADOS POR MODO GPU
            vf_filters = []
            
            # 🚀 OPTIMIZACIÓN: Mantener más trabajo en GPU para reducir carga CPU
            gpu_transfer_needed = False
            if gpu_mode in ['quality', 'max_quality'] and self.enable_image_enhancement:
                # Solo transferir si necesitamos filtros complejos que requieren CPU
                gpu_transfer_needed = True
            
            if hasattr(self, '_gpu_decoder') and self._gpu_decoder == 'cuda' and gpu_transfer_needed:
                vf_filters.append('hwdownload,format=nv12,format=yuv420p')
            
            # 1. Redimensionar (optimizado por modo)
            if gpu_mode == 'ultra_fast':
                # Ultra rápido: algoritmo más básico
                vf_filters.append(f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease:flags=fast_bilinear')
            else:
                # Otros modos: algoritmo de mejor calidad
                vf_filters.append(f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease:flags=lanczos')
            
            # 2. Padding
            vf_filters.append(f'pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black')
            
            # 3. Mejoras de imagen según modo
            if gpu_mode == 'ultra_fast':
                # Sin mejoras para máxima velocidad
                pass
            elif gpu_mode == 'balanced':
                # Mejoras básicas
                if self.quality >= 70:
                    vf_filters.append('eq=contrast=1.05:saturation=1.02')
            elif gpu_mode in ['quality', 'max_quality']:
                # Mejoras completas
                if self.quality >= 70:
                    vf_filters.append('eq=contrast=1.1:saturation=1.05:brightness=0.02')
                    vf_filters.append('unsharp=5:5:1.0:5:5:0.0')
            
            # Unir filtros
            vf_filter = ','.join(vf_filters)
            
            # 🎯 CONFIGURACIÓN DE CALIDAD POR MODO
            if gpu_mode == 'ultra_fast':
                q_value = 8  # Calidad básica para velocidad
            elif gpu_mode == 'balanced':
                q_value = max(3, min(7, 9 - int(self.quality/15)))
            else:  # quality/max_quality
                q_value = max(2, min(5, 7 - int(self.quality/20)))
            
            # 🚀 TIMEOUT OPTIMIZADO POR MODO
            timeout = 8 if gpu_mode == 'ultra_fast' else 15
            
            cmd.extend([
                '-vframes', '1',
                '-vf', vf_filter,
                '-q:v', str(q_value),
                '-loglevel', 'quiet',
                str(thumbnail_path)
            ])
            
            result = subprocess.run(cmd, capture_output=True, timeout=timeout)
            if result.returncode == 0 and thumbnail_path.exists():
                return True
            return False
        except Exception as e:
            logger.debug(f"Error con FFmpeg GPU (modo {getattr(self, '_gpu_mode', 'unknown')}): {e}")
            return False
    
    def _extract_frame_with_cache(self, video_path: Path, timestamp: float, cache_key: str) -> Optional[np.ndarray]:
        """🧠 OPTIMIZACIÓN RAM: Extraer frame con cache inteligente"""
        # Extraer frame usando método rápido
        if self.fast_mode:
            frame = self._extract_frame_ffmpeg(video_path, timestamp)
            if frame is None:
                frame = self._extract_frame_ultra_fast(video_path, timestamp)
        else:
            frame = self._extract_frame_optimized(video_path, timestamp)
        
        # Añadir al cache si se extrajo exitosamente
        if frame is not None and self.use_ram_optimization:
            self._add_to_cache(cache_key, frame)
        
        return frame
    
    def _add_to_cache(self, cache_key: str, frame: np.ndarray):
        """Añadir frame al cache con gestión de memoria"""
        # Si el cache está lleno, eliminar el más antiguo (FIFO)
        if len(self.frame_cache) >= self.max_cache_size:
            # Eliminar la primera entrada (más antigua)
            oldest_key = next(iter(self.frame_cache))
            del self.frame_cache[oldest_key]
            logger.debug(f"Cache lleno, eliminando frame antiguo: {oldest_key}")
        
        # Añadir nuevo frame al cache
        self.frame_cache[cache_key] = frame.copy()  # Copia para evitar modificaciones
        logger.debug(f"Frame añadido al cache: {cache_key} (total: {len(self.frame_cache)})")
    
    def clear_frame_cache(self):
        """Limpiar cache de frames para liberar RAM"""
        cache_size = len(self.frame_cache)
        self.frame_cache.clear()
        logger.info(f"Cache de frames limpiado: {cache_size} frames eliminados")
        
    def enable_quality_mode(self):
        """🎨 Activar modo de calidad GPU para mejor imagen"""
        self.fast_mode = False
        self.enable_image_enhancement = True
        # Solo aumentar calidad si es menor a la configurada
        if self.quality < 85:
            self.quality = 90  # Calidad máxima para modo quality
        # 🎮 GPU: Configuración de máxima calidad
        self._enable_gpu_acceleration = True
        self._gpu_decoder = self._detect_gpu_support()
        self._gpu_mode = 'max_quality'  # Modo GPU de máxima calidad
        logger.info(f"🎨 Modo de calidad GPU activado - Mejor imagen (calidad {self.quality}, GPU: {self._gpu_decoder or 'CPU fallback'})")
        
        self._initialized = True
        
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
                if self.fast_mode or not self.enable_validation:
                    # En modo ultra-rápido o con validación deshabilitada, asumir que thumbnails existentes son válidos
                    return thumbnail_path
                elif self._is_thumbnail_valid(thumbnail_path):
                    return thumbnail_path
                else:
                    # Thumbnail corrupto, eliminarlo y regenerar
                    logger.debug(f"Thumbnail corrupto detectado, eliminando: {thumbnail_path}")
                    try:
                        thumbnail_path.unlink()
                    except Exception as e:
                        logger.warning(f"Error eliminando thumbnail corrupto: {e}")
            
            # ULTRA OPTIMIZACIÓN: Usar FFmpeg directo en modo ultra-rápido para extracción, pero siempre procesar visualmente
            frame = None
            used_ffmpeg_direct = False
            if self.fast_mode and self.use_ffmpeg_direct and not self.add_watermark:
                # Extraer frame con FFmpeg directo a archivo temporal
                if self._generate_thumbnail_ffmpeg_direct(video_path, thumbnail_path, timestamp):
                    # Cargar el thumbnail generado por FFmpeg para reprocesar visualmente
                    try:
                        frame = np.array(Image.open(thumbnail_path))
                        used_ffmpeg_direct = True
                        # Eliminar el thumbnail temporal, lo vamos a sobrescribir
                        thumbnail_path.unlink()
                    except Exception as e:
                        logger.debug(f"No se pudo cargar thumbnail FFmpeg directo para reprocesar: {e}")
                        frame = None
                else:
                    logger.debug(f"FFmpeg directo falló, usando método tradicional")
            
            if frame is None:
                # 🧠 OPTIMIZACIÓN RAM: Verificar cache de frames primero
                cache_key = f"{video_path}_{timestamp}"
                if self.use_ram_optimization and cache_key in self.frame_cache:
                    logger.debug(f"Frame encontrado en cache: {video_path}")
                    frame = self.frame_cache[cache_key]
                else:
                    # Extraer frame y añadir al cache
                    frame = self._extract_frame_with_cache(video_path, timestamp, cache_key)
            
            if frame is None:
                logger.error(f"No se pudo extraer frame de {video_path}")
                return None
            
            # Procesar imagen SIEMPRE con resize con aspecto y mejoras visuales
            # Forzar siempre el resize con padding y mejoras visuales, incluso en modo rápido
            # 1. Redimensionar manteniendo aspecto y padding a tamaño destino
            processed_image = self._resize_with_aspect_ratio_optimized(Image.fromarray(frame))

            # 2. Aplicar mejoras visuales SIEMPRE (no solo si enable_image_enhancement)
            try:
                from PIL import ImageEnhance
                # Contraste
                enhancer = ImageEnhance.Contrast(processed_image)
                processed_image = enhancer.enhance(1.1)
                # Saturación
                enhancer = ImageEnhance.Color(processed_image)
                processed_image = enhancer.enhance(1.05)
                # Nitidez
                enhancer = ImageEnhance.Sharpness(processed_image)
                processed_image = enhancer.enhance(1.1)
            except Exception as e:
                logger.debug(f"Error aplicando mejoras visuales forzadas: {e}")

            # Añadir watermark si está habilitado
            if self.add_watermark:
                processed_image = self._add_watermark(processed_image)

            # Guardar thumbnail con optimizaciones
            if self.fast_mode:
                self._save_thumbnail_ultra_fast(processed_image, thumbnail_path)
            else:
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
    
    def _extract_frame_ffmpeg(self, video_path: Path, timestamp: float) -> Optional[np.ndarray]:
        """🚀 ULTRA OPTIMIZADO: Extraer frame usando FFmpeg (mucho más rápido que OpenCV), SIN distorsionar aspecto"""
        try:
            fixed_timestamp = min(timestamp, 3.0)
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_path = temp_file.name
            try:
                target_width, target_height = self.thumbnail_size
                vf_filter = f'scale={target_width}:-1'
                cmd = [
                    'ffmpeg',
                    '-y',
                    '-ss', str(fixed_timestamp),
                    '-i', str(video_path),
                    '-vframes', '1',
                    '-vf', vf_filter,
                    '-q:v', '5',
                    '-loglevel', 'quiet',
                    temp_path
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                if result.returncode == 0 and os.path.exists(temp_path):
                    image = Image.open(temp_path)
                    frame_array = np.array(image)
                    if len(frame_array.shape) == 2:
                        frame_array = np.stack([frame_array] * 3, axis=-1)
                    self._last_used_ffmpeg = True
                    return frame_array
                return None
            finally:
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except:
                    pass
        except Exception as e:
            logger.debug(f"Error con FFmpeg: {e}")
            return None
    
    def _extract_frame_ultra_fast(self, video_path: Path, timestamp: float) -> Optional[np.ndarray]:
        """🚀 ULTRA OPTIMIZADO: Extraer frame con mínimo procesamiento"""
        cap = None
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return None
            
            # Configuraciones agresivas para máximo rendimiento
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)   # Reducir resolución temporalmente
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)  # Reducir resolución temporalmente
            
            # Usar timestamp fijo para evitar cálculos
            # La mayoría de videos tienen contenido interesante en los primeros 3-5 segundos
            fixed_timestamp = min(timestamp, 3.0)  # Máximo 3 segundos
            
            # 🧠 OPTIMIZACIÓN RAM: Usar metadatos pre-cargados si están disponibles
            video_path_str = str(video_path)
            if self.use_ram_optimization and video_path_str in self.preload_cache:
                metadata = self.preload_cache[video_path_str]
                fps = metadata['fps']
                logger.debug(f"Usando metadatos pre-cargados para {video_path.name}")
            else:
                # Obtener FPS rápido (sin verificaciones)
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps <= 0 or fps > 120:  # Valores irreales
                    fps = 30  # Asumir 30fps
            
            # Calcular frame objetivo (simplificado)
            target_frame = int(fixed_timestamp * fps)
            target_frame = max(0, min(target_frame, 300))  # Límite de 300 frames (10s @ 30fps)
            
            # Posicionarse y leer frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            
            if ret and frame is not None:
                # Conversión directa sin verificaciones extras
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Fallback ultra-rápido a frame 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            
            if ret and frame is not None:
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            return None
            
        except Exception:
            return None
        finally:
            if cap is not None:
                cap.release()
    
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
        
        # Mejorar imagen con filtros básicos (solo si está habilitado)
        if getattr(self, 'enable_image_enhancement', False):
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
        
        # Redimensionar con algoritmo mejorado
        if self.fast_mode:
            # 🎨 MEJORADO: En modo rápido, usar BILINEAR (mejor que NEAREST, aún rápido)
            image = image.resize((new_width, new_height), Image.Resampling.BILINEAR)
        else:
            # Modo normal, usar LANCZOS para máxima calidad
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crear imagen con padding si es necesario
        if new_width != target_width or new_height != target_height:
            # 🎨 MEJORADO: Usar padding inteligente siempre para mejor resultado visual
            if hasattr(self, '_enable_gpu_acceleration') and self._enable_gpu_acceleration:
                # Modo GPU: usar padding más sofisticado
                padding_color = self._get_intelligent_padding_color(image)
            else:
                # Modo normal/rápido: padding inteligente básico 
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
    
    def _save_thumbnail_ultra_fast(self, image: Image.Image, thumbnail_path: Path):
        """🚀 ULTRA OPTIMIZADO: Guardar thumbnail con configuración ultra-rápida"""
        try:
            # Asegurar directorio
            thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Configuración ultra-rápida para JPEG
            save_kwargs = {
                'format': 'JPEG',
                'quality': self.quality,  # Usar calidad dinámica
                'optimize': False,  # Sin optimización para velocidad
                'progressive': False,  # Sin JPEG progresivo
            }
            
            # Guardar directo sin optimizaciones
            image.save(thumbnail_path, **save_kwargs)
            
        except Exception as e:
            logger.error(f"Error guardando thumbnail ultra-rápido en {thumbnail_path}: {e}")
            raise
    
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
        
        # 🧠 OPTIMIZACIÓN RAM: Pre-cargar metadatos si está habilitado
        if self.use_ram_optimization:
            video_paths = [v['file_path'] for v in video_data_list]
            self.preload_video_metadata(video_paths)
        
        # Filtrar videos que realmente necesitan thumbnails (validación en lotes)
        videos_to_process = self._batch_validate_videos(video_data_list, force_regenerate, results)
        
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
        
        # Procesamiento en paralelo optimizado para I/O bound
        import os
        cpu_count = os.cpu_count() or 4
        # Para thumbnail generation (I/O bound), usar 2-4 workers max
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
    
    def preload_video_metadata(self, video_paths: list) -> dict:
        """🧠 OPTIMIZACIÓN RAM: Pre-cargar metadatos de videos en RAM"""
        preload_results = {'loaded': 0, 'failed': 0}
        
        for video_path in video_paths[:20]:  # Limitar a 20 videos para no saturar RAM
            try:
                path_obj = Path(video_path)
                if not path_obj.exists():
                    continue
                
                # Pre-cargar información básica del video
                cap = cv2.VideoCapture(str(path_obj))
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS) or 30
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    duration = total_frames / fps if fps > 0 else 0
                    
                    # Guardar metadatos en cache
                    self.preload_cache[str(path_obj)] = {
                        'fps': fps,
                        'total_frames': total_frames,
                        'duration': duration,
                        'loaded_at': time.time()
                    }
                    
                    preload_results['loaded'] += 1
                    cap.release()
                else:
                    preload_results['failed'] += 1
                    
            except Exception as e:
                logger.debug(f"Error pre-cargando {video_path}: {e}")
                preload_results['failed'] += 1
        
        if preload_results['loaded'] > 0:
            logger.info(f"🧠 Pre-cargados {preload_results['loaded']} metadatos en RAM")
        
        return preload_results
    
    def _batch_validate_videos(self, video_data_list: list, force_regenerate: bool, results: dict) -> list:
        """🚀 OPTIMIZADO: Validar videos en lotes para mejor rendimiento"""
        videos_to_process = []
        
        # Procesar en lotes de 100 para optimizar acceso a disco
        batch_size = 100
        for i in range(0, len(video_data_list), batch_size):
            batch = video_data_list[i:i+batch_size]
            
            for video_data in batch:
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
        
        return videos_to_process

    def configure_thumbnail_mode(self, mode: str = 'balanced'):
        """🎯 Configurar modo de thumbnail según necesidades"""
        if mode == 'ultra_fast':
            self.enable_ultra_fast_mode()
        elif mode == 'balanced':
            self.enable_balanced_mode()
        elif mode == 'quality':
            self.enable_quality_mode()
        elif mode == 'gpu':
            self.enable_gpu_mode()
        else:
            logger.warning(f"Modo desconocido: {mode}. Usando 'balanced'")
            self.enable_balanced_mode()
    
    def auto_configure_best_mode(self):
        """🧠 Configurar automáticamente el mejor modo según el hardware"""
        # Detectar GPU primero
        gpu_support = self._detect_gpu_support()
        
        if gpu_support:
            logger.info("🎮 GPU detectada, configurando modo GPU para máxima calidad")
            self.enable_gpu_mode()
        else:
            # Estimar capacidad del sistema basado en CPU cores
            import os
            cpu_count = os.cpu_count() or 4
            
            if cpu_count >= 8:
                logger.info("💪 CPU potente detectada, configurando modo calidad")
                self.enable_quality_mode()
            elif cpu_count >= 4:
                logger.info("⚖️ CPU moderada detectada, configurando modo balanceado")
                self.enable_balanced_mode()
            else:
                logger.info("⚡ CPU limitada detectada, configurando modo ultra-rápido")
                self.enable_ultra_fast_mode()

# ⚠️ DEPRECATED: Instancia global removida para eliminar dependencias circulares
# Usar ServiceFactory.get_service('thumbnail_generator') o get_thumbnail_generator() desde service_factory