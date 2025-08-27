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
    
    def _normalize_platform_name(self, platform: str) -> str:
        """Override base method to use YouTube-specific mapping"""
        platform_lower = platform.lower().strip()
        return self.platform_mapping.get(platform_lower, platform_lower)
    
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
            query_key = 'main_query_v2'  # Changed key to invalidate cache
            if self._prepared_statements_cache.get(query_key) is None:
                # Preparar query una sola vez con estructura correcta y metadatos completos
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
                        ) as metadata_concat,
                        GROUP_CONCAT(DISTINCT mim.type) as metadata_types_concat
                    FROM download_item di
                    LEFT JOIN media_item_description mid ON di.id = mid.download_item_id
                    LEFT JOIN url_description ud ON mid.id = ud.media_item_description_id
                    LEFT JOIN media_item_metadata mim ON di.id = mim.download_item_id
                    LEFT JOIN media_info mi ON di.id = mi.download_item_id
                    LEFT JOIN video_info vi ON mi.id = vi.media_info_id
                    WHERE di.filename IS NOT NULL
                    GROUP BY di.id, di.filename, mid.title, ud.service_name, ud.url, mid.duration, vi.dimension, vi.resolution, vi.fps
                    ORDER BY di.id ASC
                '''
            
            main_query = self._prepared_statements_cache[query_key]
            
            # Añadir paginación (SQLite requiere LIMIT antes de OFFSET)
            if limit or offset > 0:
                if limit:
                    main_query += f' LIMIT {limit}'
                    if offset > 0:
                        main_query += f' OFFSET {offset}'
                else:
                    # Si solo hay offset sin limit, usar un limit muy grande
                    main_query += f' LIMIT 999999 OFFSET {offset}'
            
            return self._process_videos_ultra_fast(main_query, [])
        except Exception as e:
            self.logger.error(f"Error en extract_videos optimized: {e}")
            return []
    
    def extract_by_platform(self, platform: str, offset: int = 0, limit: Optional[int] = None, min_download_item_id: int = 0) -> List[Dict]:
        """🚀 Extract videos by platform ultra-fast con todas las optimizaciones"""
        if not self.is_available() or not platform:
            return []
        
        try:
            # 🚀 Construir condición de plataforma
            platform_condition, platform_params = self._build_platform_condition(platform)
            
            # 🚀 USAR PREPARED STATEMENT CACHEADO para plataforma
            query_key = f'platform_{platform.lower()}_v2'  # Changed to invalidate cache
            if query_key not in self._prepared_statements_cache:
                # Preparar query específica para esta plataforma con metadatos completos
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
                        ) as metadata_concat,
                        GROUP_CONCAT(DISTINCT mim.type) as metadata_types_concat
                    FROM download_item di
                    LEFT JOIN media_item_description mid ON di.id = mid.download_item_id
                    LEFT JOIN url_description ud ON mid.id = ud.media_item_description_id
                    LEFT JOIN media_item_metadata mim ON di.id = mim.download_item_id
                    LEFT JOIN media_info mi ON di.id = mi.download_item_id
                    LEFT JOIN video_info vi ON mi.id = vi.media_info_id
                    WHERE di.filename IS NOT NULL
                        AND {platform_condition}
                        AND di.id > ?
                    GROUP BY di.id, di.filename, mid.title, ud.service_name, ud.url, mid.duration, vi.dimension, vi.resolution, vi.fps
                    ORDER BY di.id ASC
                '''
            
            main_query = self._prepared_statements_cache[query_key]
            
            # Añadir paginación (SQLite requiere LIMIT antes de OFFSET)  
            if limit or offset > 0:
                if limit:
                    main_query += f' LIMIT {limit}'
                    if offset > 0:
                        main_query += f' OFFSET {offset}'
                else:
                    # Si solo hay offset sin limit, usar un limit muy grande
                    main_query += f' LIMIT 999999 OFFSET {offset}'
            
            # Add min_download_item_id parameter
            params = platform_params + [min_download_item_id]
            return self._process_videos_ultra_fast(main_query, params)
            
        except Exception as e:
            self.logger.error(f"Error en extract_by_platform {platform}: {e}")
            return []
    
    
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
                
                # 🚀 STAGE 5: Process rows con optimizaciones extremas + lógica completa
                for i, row in enumerate(rows):
                    file_path_str = file_paths[i]
                    
                    # Skip si el archivo no existe (verificación ultra-rápida)
                    if not file_path_str or not file_existence_cache.get(file_path_str, False):
                        continue
                    
                    # 🚀 ULTRA-FAST: Acceso directo por índice (sin nombres de columna)
                    # Nueva estructura: 0=download_id, 1=file_path, 2=video_title, 3=platform, 4=video_url,
                    #                  5=duration_ms, 6=dimension_code, 7=resolution_code, 8=fps, 9=metadata_concat, 10=metadata_types_concat
                    
                    try:
                        file_path = Path(file_path_str)
                        service_name = row[3]  # platform
                        platform = self._normalize_platform_name(service_name or "")
                        
                        # 🚀 Parse metadata ultra-fast (solo si existe)
                        metadata_concat = row[9] if len(row) > 9 else ""
                        metadata_types_concat = row[10] if len(row) > 10 else ""
                        metadata = {}
                        creator_name = None
                        creator_url = None
                        subscription_name = None
                        subscription_type = None
                        subscription_url = None
                        
                        # Extract metadata types for subscription logic
                        metadata_types = set()
                        if metadata_types_concat:
                            metadata_types = set(int(t) for t in metadata_types_concat.split(',') if t.strip().isdigit())
                        
                        # 🚀 ULTRA-FAST: Parseo directo sin funciones adicionales cuando es posible
                        if metadata_concat:
                            metadata = self._parse_4k_metadata(metadata_concat)
                            # Extraer directamente los valores más comunes
                            creator_name = metadata.get('creator_name')
                            creator_url = metadata.get('creator_url')
                            playlist_name = metadata.get('playlist_name')
                            playlist_url = metadata.get('playlist_url')
                            channel_name = metadata.get('channel_name')
                            channel_url = metadata.get('channel_url')
                            subscription_info = metadata.get('subscription_info')
                            
                            # 🚀 Lógica de suscripción corregida según estructura real de 4K Video Downloader
                            if playlist_name:
                                # ✅ PLAYLIST SUBSCRIPTION: Solo cuando hay playlist_name (type=3)
                                subscription_name = playlist_name.strip()
                                if subscription_name in ['Liked videos', 'Videos que me gustan']:
                                    subscription_name = 'Liked videos'
                                subscription_type = 'playlist'
                                subscription_url = playlist_url
                                creator_name = creator_name or channel_name
                                creator_url = creator_url or channel_url
                            elif channel_name and subscription_info:
                                # ✅ ACCOUNT SUBSCRIPTION: Solo cuando hay channel_name (type=5) + subscription_info (type=7)
                                # Esto indica una verdadera suscripción de canal, no un video individual
                                subscription_name = channel_name
                                subscription_type = 'account'
                                subscription_url = channel_url
                                creator_name = creator_name or channel_name
                                creator_url = creator_url or channel_url
                            else:
                                # ✅ VIDEO INDIVIDUAL: Solo asignar creador, NO crear suscripción
                                creator_name = creator_name or channel_name
                                creator_url = creator_url or channel_url
                                # subscription_name, subscription_type, subscription_url quedan None
                        
                        # Fallback ultra-rápido si no hay creador
                        if not creator_name:
                            creator_name = self._extract_creator_from_path(file_path) or "undefined"
                        
                        # 🚀 Procesar duración usando acceso directo
                        duration_ms = row[5] if len(row) > 5 else None
                        
                        # 🚀 Procesar dimensiones usando cache pre-computado
                        resolution_code = row[7] if len(row) > 7 else None
                        dimensions = None
                        video_dimensions = None
                        if resolution_code is not None:
                            dimensions = self._resolution_cache.get(resolution_code)
                            if dimensions:
                                video_dimensions = {
                                    'width': dimensions['width'],
                                    'height': dimensions['height'], 
                                    'aspect_ratio': dimensions['aspect_ratio'],
                                    'is_vertical': dimensions['is_vertical'],
                                    'fps': row[8] if len(row) > 8 else None,
                                    'resolution_code': resolution_code,
                                    'dimension_code': row[6] if len(row) > 6 else None
                                }
                        
                        # 🚀 Detectar tipo de video ultra-rápido (Shorts vs Videos)
                        video_type = "video"  # default
                        is_short = False
                        
                        if platform == "youtube" and duration_ms is not None and dimensions:
                            duration_seconds = duration_ms / 1000
                            is_vertical = dimensions['is_vertical']  # Pre-computado
                            # Ultra-fast detection: solo verificar criterios básicos
                            if duration_seconds <= 60 and is_vertical:
                                video_type = "shorts"
                                is_short = True
                        
                        # 🚀 File size usando cache de existencia
                        file_size = self._get_file_size_cached(file_path_str, file_existence_cache)
                        
                        # 🚀 Build video dict optimizado con lógica directa
                        file_name = file_path.name
                        list_types = [video_type]  # Lista directa basada en video_type
                        
                        # 🎯 CRÍTICO: Asegurar downloader_mapping primero
                        downloader_mapping = {
                            'download_item_id': row[0],  # download_id
                            'external_db_source': 'youtube_4k',
                            'creator_from_downloader': creator_name,
                            'is_carousel_item': False,  # YouTube no tiene carruseles típicamente
                            'carousel_order': None,
                            'carousel_base_id': None
                        }
                        
                        video = {
                            'file_path': file_path_str,
                            'file_name': file_name,
                            'title': row[2] or file_path.stem,  # video_title
                            'platform': platform,
                            'url': row[4],   # video_url (renombrado para el manager)
                            'post_url': row[4],   # mantener compatibilidad
                            'source': 'db',
                            'file_size': file_size,
                            'duration_seconds': duration_ms // 1000 if duration_ms else None,
                            'video_type': video_type,
                            'is_short': is_short,
                            
                            # 🎯 Campos requeridos por manager
                            'video_id': str(row[0]),  # download_id como video_id
                            'download_item_id': row[0],  # para mapping
                            'publishing_timestamp': None,  # 4K BD no tiene este dato
                            'timestampNs': None,  # 4K BD no tiene este dato preciso
                            'downloader_subscription_uuid': metadata.get('subscription_info'),
                            'metadata_types': metadata_types,  # Para lógica de suscripciones
                            
                            # 🎯 CRÍTICO: Downloader mapping debe estar presente
                            'downloader_mapping': downloader_mapping,
                            
                            # 🎯 Información del creador y suscripción (directo, sin funciones)
                            'creator_name': creator_name,
                            'creator_url': creator_url,
                            'subscription_name': subscription_name,
                            'subscription_type': subscription_type,
                            'subscription_url': subscription_url,
                            'list_types': list_types,
                            
                            # 🎯 Metadatos adicionales (directos del metadata ya parseado)
                            'channel_name': metadata.get('channel_name'),
                            'channel_url': metadata.get('channel_url'),
                            'playlist_name': metadata.get('playlist_name'),
                            'playlist_url': metadata.get('playlist_url'),
                            
                            # 🚀 Video dimensions si están disponibles
                            'video_dimensions': video_dimensions,
                        }
                        
                        # Añadir dimensiones directamente si están disponibles (compatibilidad)
                        if dimensions:
                            video.update({
                                'width': dimensions['width'],
                                'height': dimensions['height'],
                                'resolution_width': dimensions['width'],  # para manager
                                'resolution_height': dimensions['height'],  # para manager
                                'fps': row[8] if len(row) > 8 else None
                            })
                        
                        videos.append(video)
                        
                    except Exception as e:
                        self.logger.error(f"Error procesando video individual ultra-fast: {e}")
                        import traceback
                        self.logger.error(traceback.format_exc())
                        continue
                
                self.logger.debug(f"🚀 ULTRA-FAST: Processed {len(videos)} videos from {len(rows)} rows")
                return videos
                
        except Exception as e:
            self.logger.error(f"Error en _process_videos_ultra_fast: {e}")
            return []