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
        """🆕 NUEVA ESTRUCTURA: Extraer videos de 4K Video Downloader con soporte completo"""
        self.logger.info("Extrayendo videos de 4K Video Downloader con nueva estructura...")
        videos = []
        
        if not self.is_available():
            return videos
        
        try:
            # Query completa para obtener todos los metadatos necesarios
            query = """
            SELECT 
                di.id as download_id,
                di.filename as file_path,
                mid.title as video_title,
                ud.service_name as platform,
                ud.url as video_url,
                
                -- Metadatos del creador y playlist
                GROUP_CONCAT(
                    CASE 
                        WHEN mim.type = 0 THEN 'creator_name:' || mim.value
                        WHEN mim.type = 1 THEN 'creator_url:' || mim.value  
                        WHEN mim.type = 3 THEN 'playlist_name:' || mim.value
                        WHEN mim.type = 4 THEN 'playlist_url:' || mim.value
                        WHEN mim.type = 5 THEN 'channel_name:' || mim.value
                        WHEN mim.type = 6 THEN 'channel_url:' || mim.value
                        WHEN mim.type = 7 THEN 'subscription_info:' || mim.value
                    END, '|||'
                ) as metadata_concat
                
            FROM download_item di
            LEFT JOIN media_item_description mid ON di.id = mid.download_item_id
            LEFT JOIN url_description ud ON mid.id = ud.media_item_description_id
            LEFT JOIN media_item_metadata mim ON di.id = mim.download_item_id
            WHERE di.filename IS NOT NULL
            GROUP BY di.id, di.filename, mid.title, ud.service_name, ud.url
            ORDER BY di.id
            """
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            rows = self._execute_query(query)
            
            for row in rows:
                video_data = self._process_4k_video_row(row)
                if video_data:
                    videos.append(video_data)
            
            self.logger.info(f"Extraídos {len(videos)} videos de 4K Video Downloader")
            return videos
            
        except Exception as e:
            self.logger.error(f"Error extrayendo videos de 4K Video Downloader: {e}")
            return videos
    
    def extract_by_platform(self, platform_filter: str, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """Extraer videos filtrados por plataforma específica"""
        self.logger.info(f"Extrayendo videos de 4K Video Downloader - Plataforma: {platform_filter}")
        videos = []
        
        if not self.is_available():
            return videos
        
        try:
            # Build platform filter condition based on platform_filter
            platform_condition, platform_params = self._build_platform_condition(platform_filter)
            
            # Query similar pero con filtro de plataforma mejorado
            query = f"""
            SELECT 
                di.id as download_id,
                di.filename as file_path,
                mid.title as video_title,
                ud.service_name as platform,
                ud.url as video_url,
                
                GROUP_CONCAT(
                    CASE 
                        WHEN mim.type = 0 THEN 'creator_name:' || mim.value
                        WHEN mim.type = 1 THEN 'creator_url:' || mim.value  
                        WHEN mim.type = 3 THEN 'playlist_name:' || mim.value
                        WHEN mim.type = 4 THEN 'playlist_url:' || mim.value
                        WHEN mim.type = 5 THEN 'channel_name:' || mim.value
                        WHEN mim.type = 6 THEN 'channel_url:' || mim.value
                        WHEN mim.type = 7 THEN 'subscription_info:' || mim.value
                    END, '|||'
                ) as metadata_concat
                
            FROM download_item di
            LEFT JOIN media_item_description mid ON di.id = mid.download_item_id
            LEFT JOIN url_description ud ON mid.id = ud.media_item_description_id
            LEFT JOIN media_item_metadata mim ON di.id = mim.download_item_id
            WHERE di.filename IS NOT NULL 
            AND {platform_condition}
            GROUP BY di.id, di.filename, mid.title, ud.service_name, ud.url
            ORDER BY di.id
            """
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            rows = self._execute_query(query, platform_params)
            
            for row in rows:
                video_data = self._process_4k_video_row(row)
                if video_data:
                    videos.append(video_data)
            
            self.logger.info(f"Extraídos {len(videos)} videos de {platform_filter}")
            return videos
            
        except Exception as e:
            self.logger.error(f"Error extrayendo videos de {platform_filter}: {e}")
            return videos
    
    def _process_4k_video_row(self, row) -> Optional[Dict]:
        """Procesar una fila de video de 4K Video Downloader"""
        try:
            file_path_str = self._safe_str(row['file_path'])
            if not file_path_str:
                return None
            
            file_path = Path(file_path_str)
            if not file_path.exists():
                return None
            
            # Parsear metadatos
            metadata_concat = self._safe_str(row['metadata_concat'])
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
                'title': self._safe_str(row['video_title']) or file_path.stem,
                'platform': self._normalize_platform_name(self._safe_str(row['platform'])),
                'post_url': self._safe_str(row['video_url']),  # Cambiar video_url -> post_url para consistencia
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
                    'download_item_id': row['download_id'],
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
                
                # Información de archivo
                'file_size': file_path.stat().st_size if file_path.exists() else 0,
                
                # 🚀 OPTIMIZACIÓN: Obtener duración directamente de 4K DB (100x más rápido)
                'duration_seconds': self._get_duration_from_db(row['download_id']),
                'video_dimensions': self._get_dimensions_from_db(row['download_id']),
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