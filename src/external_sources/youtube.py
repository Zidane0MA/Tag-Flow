"""
Tag-Flow V2 - YouTube 4K Video Downloader Handler
Specialized handler for YouTube videos from 4K Video Downloader database
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .base import DatabaseExtractor

import logging
logger = logging.getLogger(__name__)


class YouTube4KHandler(DatabaseExtractor):
    """Handler for YouTube videos from 4K Video Downloader"""
    
    def __init__(self, db_path: Optional[Path] = None):
        super().__init__(db_path)
        
        # 🚀 CACHE EN MEMORIA: Pre-computar mapeos para ultra-velocidad
        self._resolution_cache = self._build_resolution_cache()
        
        # 🚀 Cache de prepared statements para ultra-velocidad
        self._prepared_statements_cache = {
            'main_query': None,
            'platform_filter': None
        }
        
        self.platform_mapping = {
            'youtube': 'youtube',
            'facebook': 'facebook',
            'twitter': 'twitter',
            'x': 'twitter',  # X (antes Twitter)
            'vimeo': 'vimeo',
            'dailymotion': 'dailymotion',
            'twitch': 'twitch',
            'soundcloud': 'soundcloud',
            'bilibili': 'bilibili',
            'bilibili/video': 'bilibili',
            'bilibili/video/tv': 'bilibili',
        }
    
    def get_available_platforms(self) -> Dict[str, int]:
        """
        🔍 AUTODETECCIÓN: Descubrir automáticamente todas las plataformas disponibles en 4K Video Downloader
        
        Returns:
            Dict con plataforma normalizada y cantidad de videos disponibles
        """
        platforms = {}
        
        if not self.is_available():
            return platforms
        
        try:
            # Query para obtener todas las plataformas disponibles con conteo
            query = """
            SELECT 
                LOWER(ud.service_name) as platform_raw,
                COUNT(*) as count
            FROM download_item di
            LEFT JOIN media_item_description mid ON di.id = mid.download_item_id
            LEFT JOIN url_description ud ON mid.id = ud.media_item_description_id
            WHERE di.filename IS NOT NULL AND ud.service_name IS NOT NULL
            GROUP BY LOWER(ud.service_name)
            ORDER BY count DESC
            """
            
            rows = self._execute_query(query)
            
            for row in rows:
                platform_raw = row['platform_raw']
                count = row['count']
                
                # Normalizar nombre de plataforma
                platform_normalized = self.platform_mapping.get(platform_raw, platform_raw)
                
                if platform_normalized in platforms:
                    platforms[platform_normalized] += count
                else:
                    platforms[platform_normalized] = count
            
            return platforms
            
        except Exception as e:
            self.logger.error(f"Error autodescubriendo plataformas 4K Video Downloader: {e}")
            return platforms
    
    def extract_videos(self, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """🚀 Extract videos ultra-fast con todas las optimizaciones posibles"""
        if not self.is_available():
            return []
        
        try:
            # 🚀 USAR PREPARED STATEMENT CACHEADO
            query_key = 'main_query'
            if self._prepared_statements_cache[query_key] is None:
                # Preparar query una sola vez con estructura correcta de 4K Video Downloader
                self._prepared_statements_cache[query_key] = '''
                    SELECT 
                        di.id as download_id,
                        di.filename as file_path,
                        mid.title as video_title,
                        ud.service_name as platform,
                        ud.url as video_url,
                        mid.duration as duration_ms,
                        vi.dimension as dimension_code,
                        vi.resolution as resolution_code,
                        vi.fps as fps,
                        di.id as created_at
                    FROM download_item di
                    LEFT JOIN media_item_description mid ON di.id = mid.download_item_id
                    LEFT JOIN url_description ud ON mid.id = ud.media_item_description_id
                    LEFT JOIN media_info mi ON di.id = mi.download_item_id
                    LEFT JOIN video_info vi ON mi.id = vi.media_info_id
                    WHERE di.filename IS NOT NULL
                    ORDER BY di.id DESC
                '''
            
            main_query = self._prepared_statements_cache[query_key]
            
            # Añadir paginación
            if limit:
                main_query += f' LIMIT {limit}'
            if offset > 0:
                main_query += f' OFFSET {offset}'
            
            return self._process_videos_ultra_fast(main_query, [])
        except Exception as e:
            self.logger.error(f"Error en extract_videos optimized: {e}")
            return []
    
    def extract_by_platform(self, platform: str, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """🚀 Extract videos by platform ultra-fast con todas las optimizaciones"""
        if not self.is_available() or not platform:
            return []
        
        try:
            # 🚀 Construir condición de plataforma
            platform_condition, platform_params = self._build_platform_condition(platform)
            
            # 🚀 USAR PREPARED STATEMENT CACHEADO para plataforma
            query_key = f'platform_{platform.lower()}'
            if query_key not in self._prepared_statements_cache:
                # Preparar query específica para esta plataforma con estructura correcta
                self._prepared_statements_cache[query_key] = f'''
                    SELECT 
                        di.id as download_id,
                        di.filename as file_path,
                        mid.title as video_title,
                        ud.service_name as platform,
                        ud.url as video_url,
                        mid.duration as duration_ms,
                        vi.dimension as dimension_code,
                        vi.resolution as resolution_code,
                        vi.fps as fps,
                        di.id as created_at
                    FROM download_item di
                    LEFT JOIN media_item_description mid ON di.id = mid.download_item_id
                    LEFT JOIN url_description ud ON mid.id = ud.media_item_description_id
                    LEFT JOIN media_info mi ON di.id = mi.download_item_id
                    LEFT JOIN video_info vi ON mi.id = vi.media_info_id
                    WHERE di.filename IS NOT NULL
                        AND {platform_condition}
                    ORDER BY di.id DESC
                '''
            
            main_query = self._prepared_statements_cache[query_key]
            
            # Añadir paginación
            if limit:
                main_query += f' LIMIT {limit}'
            if offset > 0:
                main_query += f' OFFSET {offset}'
            
            return self._process_videos_ultra_fast(main_query, platform_params)
            
        except Exception as e:
            self.logger.error(f"Error en extract_by_platform {platform}: {e}")
            return []
    
    def _process_4k_video_row(self, row, file_existence_cache: Dict[str, bool] = None) -> Optional[Dict]:
        """🚀 Procesar una fila de video de 4K Video Downloader con cache de existencia"""
        try:
            file_path_str = self._safe_str(row[1])  # row[1] = file_path (acceso directo por índice)
            if not file_path_str:
                return None
            
            file_path = Path(file_path_str)
            if not file_path.exists():
                return None
            
            # 🚀 ULTRA-FAST: Acceso directo por índices
            metadata_concat = self._safe_str(row[9])  # row[9] = metadata_concat
            metadata = self._parse_4k_metadata(metadata_concat)
            
            # Determinar creador y suscripción
            creator_subscription_data = self._determine_4k_creator_and_subscription(metadata, file_path)
            
            # Si no hay creador, usar fallback
            if not creator_subscription_data.get('creator_name'):
                platform_name = self._normalize_platform_name(self._safe_str(row['platform']))
                creator_subscription_data = self._determine_4k_creator_fallback(metadata, file_path, platform_name)
            
            # Detectar tipo de contenido (Short vs Video)
            video_type = self._detect_video_type(file_path, creator_subscription_data.get('creator_name'))
            creator_subscription_data['list_types'] = [video_type]
            
            # Construir estructura completa del video
            video_data = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'title': self._safe_str(row[2]) or file_path.stem,  # row[2] = video_title
                'platform': self._normalize_platform_name(self._safe_str(row[3])),  # row[3] = platform
                'post_url': self._safe_str(row[4]),  # row[4] = video_url
                'source': 'db',
                
                # Información del creador y suscripción
                'creator_name': creator_subscription_data.get('creator_name'),
                'creator_url': creator_subscription_data.get('creator_url'),
                'subscription_name': creator_subscription_data.get('subscription_name'),
                'subscription_type': creator_subscription_data.get('subscription_type'),
                'subscription_url': creator_subscription_data.get('subscription_url'),
                'list_types': creator_subscription_data.get('list_types', ['feed']),
                
                # Datos del downloader - CRÍTICO para batch_insert_videos
                'downloader_data': {
                    'download_item_id': row[0],  # row[0] = download_id
                    'external_db_source': '4k_video',
                    'creator_from_downloader': creator_subscription_data.get('creator_name'),
                    'is_carousel_item': False,  # YouTube no tiene carruseles típicamente
                    'carousel_order': None,
                    'carousel_base_id': None
                },
                
                # Metadatos adicionales
                'channel_name': metadata.get('channel_name'),
                'channel_url': metadata.get('channel_url'),
                'playlist_name': metadata.get('playlist_name'),
                'playlist_url': metadata.get('playlist_url'),
                
                # 🚀 ULTRA-FAST: Usar cache de existencia pre-computado
                'file_size': self._get_file_size_cached(file_path_str, file_existence_cache),
                
                # 🚀 OPTIMIZACIÓN ULTRA: Usar datos que ya vienen en la query principal (0 queries adicionales)
                'duration_seconds': self._process_duration_optimized(row),
                'video_dimensions': self._process_dimensions_optimized(row),
            }
            
            return video_data
            
        except Exception as e:
            self.logger.error(f"Error procesando fila de 4K Video Downloader: {e}")
            return None
    
    def _parse_4k_metadata(self, metadata_concat: str) -> Dict:
        """Parsear metadatos concatenados de 4K Video Downloader"""
        metadata = {}
        
        if not metadata_concat:
            return metadata
        
        try:
            # Dividir por el separador personalizado
            metadata_parts = metadata_concat.split('|||')
            
            for part in metadata_parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    if value and value.strip():
                        metadata[key] = value.strip()
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error parseando metadatos 4K: {e}")
            return metadata
    
    def _determine_4k_creator_and_subscription(self, metadata: Dict, file_path: Path) -> Dict:
        """Determinar creador y suscripción para videos de 4K Video Downloader"""
        result = {
            'creator_name': None,
            'creator_url': None,
            'subscription_name': None,
            'subscription_type': None,
            'subscription_url': None,
            'list_types': ['feed']  # Por defecto
        }
        
        try:
            # Extraer información de metadatos
            creator_name = metadata.get('creator_name')
            creator_url = metadata.get('creator_url')
            channel_name = metadata.get('channel_name')
            channel_url = metadata.get('channel_url')
            playlist_name = metadata.get('playlist_name')
            playlist_url = metadata.get('playlist_url')
            
            # 🎯 LÓGICA CORREGIDA: Priorizar playlist sobre creator
            # PRIORIDAD: playlist_subscription > creator_subscription > individual_video
            
            if playlist_name:
                # 🎯 PLAYLIST SUBSCRIPTION: Videos que pertenecen a una playlist específica (likes, etc.)
                # Normalizar nombres equivalentes
                normalized_playlist = playlist_name.strip()
                if normalized_playlist in ['Liked videos', 'Videos que me gustan']:
                    normalized_playlist = 'Liked videos'  # Usar nombre en inglés como preferido
                
                result['subscription_name'] = normalized_playlist
                result['subscription_type'] = 'playlist'
                result['subscription_url'] = playlist_url
                # Para playlists, mantener 'playlist' pero también detectar tipo de contenido
                result['list_types'] = ['playlist']
                
                # ✅ IMPORTANTE: Para playlists, SÍ asignar creador individual del video
                # pero NO crear suscripción de creador (solo la de playlist)
                result['creator_name'] = creator_name or channel_name
                result['creator_url'] = creator_url or channel_url
                
            elif creator_name or channel_name:
                # Verificar si es una suscripción de canal o video individual
                # Según metadata: type(5=channel name, 6=channel url, 7=subscription_info) indica suscripción
                has_channel_subscription = bool(channel_name and metadata.get('subscription_info'))
                
                final_creator_name = creator_name or channel_name
                final_creator_url = creator_url or channel_url
                
                result['creator_name'] = final_creator_name
                result['creator_url'] = final_creator_url
                
                if has_channel_subscription:
                    # 🎯 CHANNEL SUBSCRIPTION: Videos de una suscripción de canal específico
                    result['subscription_name'] = final_creator_name
                    result['subscription_type'] = 'account'
                    result['subscription_url'] = final_creator_url
                    # Para suscripciones de canal, usar 'feed' - la detección de tipo se hará después
                    result['list_types'] = ['feed']
                else:
                    # 🎯 INDIVIDUAL VIDEO: Videos descargados individualmente
                    # Solo asignar creador, NO crear suscripción (como en legacy)
                    result['subscription_name'] = None
                    result['subscription_type'] = None
                    result['subscription_url'] = None
                    result['list_types'] = ['feed']
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error determinando creador/suscripción 4K: {e}")
            return result
    
    def _determine_4k_creator_fallback(self, metadata: Dict, file_path: Path, platform_name: str) -> Dict:
        """Determinar creador usando métodos de fallback"""
        result = {
            'creator_name': None,
            'creator_url': None,
            'subscription_name': None,
            'subscription_type': None,
            'subscription_url': None,
            'list_types': ['feed']  # Por defecto
        }
        
        try:
            # 🎯 IMPORTANTE: Para videos sin metadata (otras plataformas como Facebook, Bilibili)
            # NO crear creador ni suscripción automáticamente
            # El usuario puede editarlo desde el frontend
            
            # Solo intentar extraer de ruta si es un patrón reconocible
            creator_name = self._extract_creator_from_path_safe(file_path)
            
            if creator_name:
                result['creator_name'] = creator_name
            else:
                # 🎯 Usar "undefined" para indicar claramente que el creador no está definido
                # Esto es más claro que None y evita fragmentos de rutas confusos
                result['creator_name'] = "undefined"
            
            # 🚫 NO crear suscripciones para videos individuales de otras plataformas
            result['subscription_name'] = None
            result['subscription_type'] = None
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error en fallback de creador 4K: {e}")
            return result
    
    def _extract_creator_from_path_safe(self, file_path: Path) -> Optional[str]:
        """Extraer creador de ruta solo si es un patrón reconocible (no títulos de videos)"""
        try:
            # Solo extraer si está en una carpeta que parece nombre de creador
            # NO si está en carpeta root o con nombres genéricos
            parts = file_path.parts
            
            # Buscar carpetas que parezcan nombres de creadores (no títulos de videos)
            for part in reversed(parts[:-1]):  # Excluir el nombre del archivo
                part_clean = part.strip()
                
                # Skip carpetas obvias del sistema y fragmentos de rutas
                skip_folders = {
                    'downloads', 'videos', 'content', 'media', 'files',
                    'youtube', 'tiktok', 'instagram', 'facebook', 'bilibili',
                    '4k video downloader+', '4k video downloader', 'downloader'
                }
                
                # Skip fragmentos de rutas como "D:\", "C:\", etc.
                if ':' in part_clean or '\\' in part_clean or '/' in part_clean:
                    continue
                
                # Solo considerar si es un nombre válido de creador
                if (part_clean and 
                    part_clean.lower() not in skip_folders and
                    not part_clean.startswith('.') and
                    3 <= len(part_clean) <= 50 and  # Rango razonable para nombre de creador
                    not any(char in part_clean for char in ['【', '】', '[', ']', '#']) and  # No símbolos de títulos
                    not part_clean.isdigit()  # No números puros
                ):
                    return part_clean
            
            return None
            
        except Exception:
            return None
    
    def _get_video_duration(self, file_path: Path) -> Optional[int]:
        """Obtener duración del video en segundos usando FFprobe"""
        try:
            import subprocess
            if not file_path.exists():
                return None
                
            # Use FFprobe to get duration
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format',
                str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                duration = data.get('format', {}).get('duration')
                if duration:
                    return int(float(duration))
            return None
            
        except Exception as e:
            self.logger.debug(f"Error getting video duration: {e}")
            return None
    
    def _get_video_dimensions(self, file_path: Path) -> Optional[Dict]:
        """Obtener dimensiones del video usando FFprobe"""
        try:
            import subprocess
            if not file_path.exists():
                return None
                
            # Use FFprobe to get video dimensions
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams',
                '-select_streams', 'v:0', str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                streams = data.get('streams', [])
                if streams:
                    stream = streams[0]
                    width = stream.get('width')
                    height = stream.get('height')
                    if width and height:
                        aspect_ratio = width / height
                        return {
                            'width': width,
                            'height': height,
                            'aspect_ratio': aspect_ratio,
                            'is_vertical': aspect_ratio < 1.0  # Vertical if width < height
                        }
            return None
            
        except Exception as e:
            self.logger.debug(f"Error getting video dimensions: {e}")
            return None
    
    def _detect_video_type(self, file_path: Path, creator_name: str = None) -> str:
        """Detectar si es un Short, Video normal o Playlist basado en dimensiones y contexto"""
        try:
            # Obtener dimensiones y duración
            dimensions = self._get_video_dimensions(file_path)
            duration = self._get_video_duration(file_path)
            
            # Verificar si es parte de una playlist (ya se maneja en determine_creator_and_subscription)
            # Si llega aquí, es video individual o de canal
            
            if dimensions and duration:
                is_vertical = dimensions.get('is_vertical', False)
                aspect_ratio = dimensions.get('aspect_ratio', 1.0)
                
                # Detectar YouTube Short: vertical + corto
                if is_vertical and duration <= 60:
                    return 'shorts'
                # Detectar video vertical largo (también puede ser short si es ≤60s)
                elif is_vertical and duration <= 120:  # Up to 2 minutes vertical could be short
                    return 'shorts'
                # Video horizontal normal
                else:
                    return 'videos'
            
            # Fallback: usar nombre de archivo o título para detectar
            file_name_lower = file_path.name.lower()
            if 'short' in file_name_lower or '#short' in file_name_lower:
                return 'shorts'
            
            # Default: asumir video normal
            return 'videos'
            
        except Exception as e:
            self.logger.debug(f"Error detecting video type: {e}")
            return 'videos'  # Default fallback
    
    def _get_duration_from_db(self, download_id: int) -> Optional[int]:
        """🚀 Obtener duración directamente de la BD de 4K (sin convertir a segundos)"""
        try:
            if not self.is_available():
                return None

            query = """
                SELECT duration FROM media_item_description 
                WHERE download_item_id = ?
            """

            rows = self._execute_query(query, (download_id,))
            if rows:
                duration_ms = rows[0][0]  # Duración en milisegundos
                return duration_ms if duration_ms else None
            return None
            
        except Exception as e:
            self.logger.debug(f"Error getting duration from DB: {e}")
            return None
    
    def _get_dimensions_from_db(self, download_id: int) -> Optional[Dict]:
        """🚀 Obtener dimensiones estimadas de la BD de 4K basado en códigos de resolución"""
        try:
            if not self.is_available():
                return None
                
            query = """
                SELECT vi.dimension, vi.resolution, vi.fps
                FROM video_info vi
                JOIN media_info mi ON vi.media_info_id = mi.id
                WHERE mi.download_item_id = ?
            """
            
            rows = self._execute_query(query, (download_id,))
            if rows:
                dimension, resolution, fps = rows[0]
                
                # Decodificar códigos basado en patrones observados
                estimated_dims = self._decode_resolution_code(resolution)
                
                if estimated_dims:
                    return {
                        'width': estimated_dims['width'],
                        'height': estimated_dims['height'], 
                        'aspect_ratio': estimated_dims['width'] / estimated_dims['height'],
                        'is_vertical': estimated_dims['width'] < estimated_dims['height'],
                        'fps': fps,
                        'resolution_code': resolution,
                        'dimension_code': dimension
                    }
            return None
            
        except Exception as e:
            self.logger.debug(f"Error getting dimensions from DB: {e}")
            return None
    
    def _decode_resolution_code(self, resolution_code: int) -> Optional[Dict]:
        """Decodificar códigos de resolución de 4K Video Downloader"""
        # Mapeo basado en análisis de patrones observados
        resolution_map = {
            5: {'width': 640, 'height': 360},    # 360p
            6: {'width': 854, 'height': 480},    # 480p  
            7: {'width': 1280, 'height': 720},   # 720p (videos largos)
            8: {'width': 1080, 'height': 1920},  # 1080p vertical (Shorts)
            9: {'width': 1440, 'height': 1080},  # 1080p+ (some vertical)
            10: {'width': 1920, 'height': 1080}, # 1080p horizontal (Videos)
            11: {'width': 2560, 'height': 1440}, # 1440p
        }
        
        return resolution_map.get(resolution_code)
    
    def _build_resolution_cache(self) -> Dict[int, Dict]:
        """🚀 Pre-computar cache de resoluciones con dimensiones calculadas para ultra-velocidad"""
        cache = {}
        
        # Mapeo base + cálculos pre-computados
        resolution_map = {
            5: {'width': 640, 'height': 360},    # 360p
            6: {'width': 854, 'height': 480},    # 480p  
            7: {'width': 1280, 'height': 720},   # 720p (videos largos)
            8: {'width': 1080, 'height': 1920},  # 1080p vertical (Shorts)
            9: {'width': 1440, 'height': 1080},  # 1080p+ (some vertical)
            10: {'width': 1920, 'height': 1080}, # 1080p horizontal (Videos)
            11: {'width': 2560, 'height': 1440}, # 1440p
        }
        
        # Pre-computar todos los cálculos
        for code, dims in resolution_map.items():
            width, height = dims['width'], dims['height']
            aspect_ratio = width / height
            cache[code] = {
                'width': width,
                'height': height,
                'aspect_ratio': aspect_ratio,
                'is_vertical': width < height
            }
        
        return cache
    
    def _decode_resolution_code_ultra_fast(self, resolution_code: int) -> Optional[Dict]:
        """🚀 Decodificación ultra-rápida usando cache pre-computado"""
        return self._resolution_cache.get(resolution_code)
    
    def _batch_check_file_existence(self, file_paths: List[str]) -> Dict[str, bool]:
        """🚀 Verificar existencia de archivos en batch para ultra-velocidad"""
        try:
            from pathlib import Path
            import os
            
            existence_cache = {}
            
            # Batch check usando os.path.exists (más rápido que Path.exists())
            for file_path_str in file_paths:
                if file_path_str:
                    existence_cache[file_path_str] = os.path.exists(file_path_str)
                else:
                    existence_cache[file_path_str] = False
            
            return existence_cache
            
        except Exception as e:
            self.logger.debug(f"Error in batch file existence check: {e}")
            # Fallback: asumir que todos existen
            return {path: True for path in file_paths}
    
    def _get_file_size_cached(self, file_path_str: str, file_existence_cache: Dict[str, bool] = None) -> int:
        """🚀 Obtener file_size usando cache de existencia"""
        try:
            # Si tenemos cache de existencia, usarlo
            if file_existence_cache and file_path_str in file_existence_cache:
                if file_existence_cache[file_path_str]:
                    from pathlib import Path
                    return Path(file_path_str).stat().st_size
                else:
                    return 0
            
            # Fallback: verificación directa
            from pathlib import Path
            file_path = Path(file_path_str)
            return file_path.stat().st_size if file_path.exists() else 0
            
        except Exception:
            return 0
    
    def _process_duration_optimized(self, row) -> Optional[int]:
        """🚀 Procesar duración de datos que ya vienen en la query principal"""
        try:
            # Los datos ya vienen del JOIN en la query principal (sqlite3.Row)
            duration_ms = row[5] if len(row) > 5 else None  # duration_ms está en posición 5
            return duration_ms if duration_ms else None  # Mantener en ms según modificación previa
        except Exception as e:
            self.logger.debug(f"Error processing duration: {e}")
            return None
    
    def _process_dimensions_optimized(self, row) -> Optional[Dict]:
        """🚀 Procesar dimensiones de datos que ya vienen en la query principal"""
        try:
            # Los datos ya vienen del JOIN en la query principal (sqlite3.Row)
            # Posiciones: 5=duration_ms, 6=dimension_code, 7=resolution_code, 8=fps
            dimension_code = row[6] if len(row) > 6 else None
            resolution_code = row[7] if len(row) > 7 else None 
            fps = row[8] if len(row) > 8 else None
            
            if resolution_code is not None:
                # 🚀 ULTRA-FAST: Cache lookup sin cálculos adicionales
                cached_dims = self._decode_resolution_code_ultra_fast(resolution_code)
                
                if cached_dims:
                    return {
                        'width': cached_dims['width'],
                        'height': cached_dims['height'], 
                        'aspect_ratio': cached_dims['aspect_ratio'],  # Pre-computado
                        'is_vertical': cached_dims['is_vertical'],    # Pre-computado
                        'fps': fps,
                        'resolution_code': resolution_code,
                        'dimension_code': dimension_code
                    }
            return None
        except Exception as e:
            self.logger.debug(f"Error processing dimensions: {e}")
            return None
    
    def _build_platform_condition(self, platform_filter: str) -> Tuple[str, List[str]]:
        """Build SQL condition for platform filtering"""
        platform_lower = platform_filter.lower()
        
        # Special cases for platforms with multiple service names
        if platform_lower == 'bilibili':
            # Match both "bilibili/video" and "bilibili/video/tv"
            return "LOWER(ud.service_name) LIKE 'bilibili%'", []
        elif platform_lower == 'twitter' or platform_lower == 'x':
            # Match "twitter" (could be stored as either)
            return "LOWER(ud.service_name) IN ('twitter', 'x')", []
        else:
            # Exact match for other platforms
            return "LOWER(ud.service_name) = LOWER(?)", [platform_filter]
    
    def _process_videos_ultra_fast(self, query: str, params: List) -> List[Dict]:
        """🚀 Procesar videos con optimizaciones extremas para sub-1ms por video"""
        try:
            conn = self._get_connection(self.db_path)
            if not conn:
                return []
            
            with conn:
                # 🚀 ULTRA-OPTIMIZATION: Usar cursor con arraysize para mejor rendimiento
                cursor = conn.execute(query, params)
                cursor.arraysize = 1000  # Fetch en chunks grandes
                
                rows = cursor.fetchall()
                
                if not rows:
                    return []
                
                # 🚀 STAGE 1: Pre-allocate lists con tamaño conocido para evitar resize
                row_count = len(rows)
                file_paths = [None] * row_count
                
                # 🚀 STAGE 2: Build file paths con minimal string operations
                for i, row in enumerate(rows):
                    # Con la nueva estructura: row[1] = di.filename (que es el path completo)
                    file_path_str = row[1]  # di.filename ya es el path completo
                    if file_path_str:
                        file_paths[i] = file_path_str
                
                # 🚀 STAGE 3: Batch check file existence con filtrado de None
                valid_paths = [p for p in file_paths if p is not None]
                file_existence_cache = self._batch_check_file_existence(valid_paths)
                
                # 🚀 STAGE 4: Pre-allocate videos list con capacidad estimada
                videos = []
                videos_capacity = int(row_count * 0.8)  # Estimate 80% files exist
                
                # 🚀 STAGE 5: Process rows con optimizaciones extremas
                for i, row in enumerate(rows):
                    file_path_str = file_paths[i]
                    
                    # Skip si el archivo no existe (verificación ultra-rápida)
                    if not file_path_str or not file_existence_cache.get(file_path_str, False):
                        continue
                    
                    # 🚀 ULTRA-FAST: Acceso directo por índice (sin nombres de columna)
                    # Nueva estructura: 0=download_id, 1=file_path, 2=video_title, 3=platform, 4=video_url,
                    #                  5=duration_ms, 6=dimension_code, 7=resolution_code, 8=fps, 9=created_at
                    
                    service_name = row[3]  # platform
                    platform = self._normalize_platform_name(service_name or "")
                    
                    # 🚀 Procesar duración usando acceso directo
                    duration_ms = row[5] if len(row) > 5 else None
                    
                    # 🚀 Procesar dimensiones usando cache pre-computado
                    resolution_code = row[7] if len(row) > 7 else None
                    dimensions = None
                    if resolution_code is not None:
                        dimensions = self._resolution_cache.get(resolution_code)
                    
                    # 🚀 Detectar tipo de video (Shorts vs Videos) con mínima lógica
                    video_type = "video"  # default
                    is_short = False
                    
                    if platform == "youtube" and duration_ms is not None and dimensions:
                        # 🚀 ULTRA-FAST: Usar datos pre-computados del cache
                        duration_seconds = duration_ms / 1000
                        is_vertical = dimensions['is_vertical']  # Pre-computado
                        
                        # Lógica ultra-optimizada para Shorts
                        if duration_seconds <= 60 and is_vertical:
                            video_type = "shorts"
                            is_short = True
                    
                    # 🚀 File size usando cache de existencia
                    file_size = self._get_file_size_cached(file_path_str, file_existence_cache)
                    
                    # 🚀 Build video dict con mínimas operaciones (usar dict literal)
                    file_name = Path(file_path_str).name if file_path_str else "unknown"
                    video = {
                        'file_path': file_path_str,
                        'file_name': file_name,
                        'title': row[2] or file_name,  # video_title
                        'platform': platform,
                        'post_url': row[4],   # video_url 
                        'file_size': file_size,
                        'duration_seconds': duration_ms // 1000 if duration_ms else None,
                        'creator_name': self._extract_creator_from_path(Path(file_path_str)) or "undefined",
                        'video_type': video_type,
                        'is_short': is_short,
                        'downloader_mapping': {
                            'download_item_id': row[0],  # download_id
                            'external_db_source': 'youtube_4k',
                            'creator_from_downloader': service_name
                        }
                    }
                    
                    # Añadir dimensiones si están disponibles (optimización condicional)
                    if dimensions:
                        video.update({
                            'width': dimensions['width'],
                            'height': dimensions['height'],
                            'fps': row[8] if len(row) > 8 else None  # fps directo
                        })
                    
                    videos.append(video)
                
                self.logger.debug(f"🚀 ULTRA-FAST: Processed {len(videos)} videos from {len(rows)} rows")
                return videos
                
        except Exception as e:
            self.logger.error(f"Error en _process_videos_ultra_fast: {e}")
            return []