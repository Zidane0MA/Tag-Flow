"""
Tag-Flow V2 - Manejo de Fuentes Externas con Nueva Estructura
Extracción de datos desde múltiples bases de datos y carpetas organizadas
CON SOPORTE COMPLETO PARA CREADORES, SUSCRIPCIONES Y LISTAS
"""

import sqlite3
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Usar config para las rutas
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import config

logger = logging.getLogger(__name__)

# Instancia global para evitar múltiples inicializaciones
_external_sources_instance = None

class ExternalSourcesManager:
    """Gestor para extraer datos de fuentes externas con nueva estructura BD completa"""
    
    def __new__(cls):
        global _external_sources_instance
        if _external_sources_instance is None:
            _external_sources_instance = super().__new__(cls)
        return _external_sources_instance
    
    def __init__(self):
        # Evitar reinicialización si ya se ha inicializado
        if hasattr(self, '_initialized'):
            return
            
        # Rutas de las bases de datos externas (desde config)
        self.external_youtube_db = config.EXTERNAL_YOUTUBE_DB
        self.tiktok_db_path = config.EXTERNAL_TIKTOK_DB  
        self.instagram_db_path = config.EXTERNAL_INSTAGRAM_DB
        
        # Debug: Verificar que la ruta esté limpia
        if self.external_youtube_db:
            path_str = str(self.external_youtube_db)
            # Detectar caracteres de control
            control_chars = [char for char in path_str if ord(char) < 32 and char not in '\t\n\r']
            if control_chars:
                logger.warning(f"Caracteres de control detectados en EXTERNAL_YOUTUBE_DB: {[hex(ord(c)) for c in control_chars]}")
            logger.debug(f"YouTube DB configurada: {self.external_youtube_db.exists()}")
            logger.debug(f"TikTok DB configurada: {self.tiktok_db_path.exists()}")
            logger.debug(f"Instagram DB configurada: {self.instagram_db_path.exists()}")
        
        # Rutas de las carpetas organizadas (desde config)
        self.organized_base_path = config.ORGANIZED_BASE_PATH
        self.organized_youtube_path = config.ORGANIZED_YOUTUBE_PATH
        self.organized_tiktok_path = config.ORGANIZED_TIKTOK_PATH
        self.organized_instagram_path = config.ORGANIZED_INSTAGRAM_PATH
        
        # Extensiones de video soportadas
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        
        self._initialized = True
    
    def _get_connection(self, db_path: Path) -> Optional[sqlite3.Connection]:
        """Crear conexión segura a una base de datos externa"""
        try:
            if not db_path.exists():
                logger.warning(f"Base de datos no existe: {db_path}")
                return None
            
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Error conectando a {db_path}: {e}")
            return None
    
    def get_available_4k_platforms(self) -> Dict[str, int]:
        """
        🔍 AUTODETECCIÓN: Descubrir automáticamente todas las plataformas disponibles en 4K Video Downloader
        
        Returns:
            Dict con plataforma normalizada y cantidad de videos disponibles
        """
        platforms = {}
        
        conn = self._get_connection(self.external_youtube_db)
        if not conn:
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
            
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
            # Mapeo para normalizar nombres de plataforma
            platform_mapping = {
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
            
            for row in rows:
                platform_raw = row['platform_raw']
                count = row['count']
                
                # Normalizar nombre de plataforma
                platform_normalized = platform_mapping.get(platform_raw, platform_raw)
                
                if platform_normalized in platforms:
                    platforms[platform_normalized] += count
                else:
                    platforms[platform_normalized] = count
            
            conn.close()
            
            return platforms
            
        except Exception as e:
            logger.error(f"Error autodescubriendo plataformas 4K Video Downloader: {e}")
            conn.close()
            return platforms
    
    def extract_youtube_videos(self, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """🆕 NUEVA ESTRUCTURA: Extraer videos de 4K Video Downloader con soporte completo"""
        logger.info("Extrayendo videos de 4K Video Downloader con nueva estructura...")
        videos = []
        
        conn = self._get_connection(self.external_youtube_db)
        if not conn:
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
            GROUP BY di.id 
            ORDER BY di.id DESC
            """
            
            # Aplicar límite y offset (SQLite requiere LIMIT con OFFSET)
            params = []
            if limit or offset > 0:
                # Si hay offset pero no limit, usar un límite muy alto
                actual_limit = limit if limit else 10000
                query += " LIMIT ? OFFSET ?"
                params.extend([actual_limit, offset])
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            logger.info(f"Obtenidos {len(rows)} registros de 4K Video Downloader")
            
            for row in rows:
                try:
                    video_data = self._process_4k_video_row(row)
                    if video_data:
                        videos.append(video_data)
                except Exception as e:
                    logger.error(f"Error procesando fila {row['download_id']}: {e}")
                    continue
            
            logger.info(f"✓ Procesados {len(videos)} videos de 4K Video Downloader")
            
        except Exception as e:
            logger.error(f"Error extrayendo videos de YouTube: {e}")
        finally:
            conn.close()
        
        return videos
    
    def extract_4k_video_downloader_by_platform(self, platform_filter: str, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """Extraer videos de 4K Video Downloader filtrados por plataforma específica"""
        logger.info(f"Extrayendo videos de 4K Video Downloader para {platform_filter}...")
        videos = []
        
        conn = self._get_connection(self.external_youtube_db)
        if not conn:
            return videos
        
        try:
            # Query con filtro de plataforma
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
            """
            
            # 🔍 AUTODETECCIÓN: Aplicar filtro de plataforma inteligente
            params = []
            
            if platform_filter == 'other':
                # Filtrar todas las plataformas que NO son principales (YouTube, TikTok, Instagram)
                query += " AND ud.service_name IS NOT NULL AND LOWER(ud.service_name) NOT LIKE '%youtube%'"
            else:
                # 🚀 SIMPLIFICADO: Usar pattern matching para cualquier plataforma
                # Mapeo de nombres de plataforma a patrones de búsqueda
                platform_patterns = {
                    'youtube': ['youtube'],
                    'facebook': ['facebook'],
                    'twitter': ['twitter', 'x'],
                    'vimeo': ['vimeo'],
                    'dailymotion': ['dailymotion'],
                    'twitch': ['twitch'],
                    'soundcloud': ['soundcloud'],
                    'bilibili': ['bilibili']
                }
                
                patterns = platform_patterns.get(platform_filter, [platform_filter])
                
                # Construir condición OR para todos los patrones
                conditions = []
                for pattern in patterns:
                    conditions.append("LOWER(ud.service_name) LIKE LOWER(?)")
                    params.append(f"%{pattern}%")
                
                if conditions:
                    query += f" AND ({' OR '.join(conditions)})"
            
            query += " GROUP BY di.id ORDER BY di.id DESC"
            
            # Aplicar límite y offset
            if limit or offset > 0:
                actual_limit = limit if limit else 10000
                query += " LIMIT ? OFFSET ?"
                params.extend([actual_limit, offset])
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            logger.info(f"Obtenidos {len(rows)} registros de 4K Video Downloader para {platform_filter}")
            
            for row in rows:
                try:
                    video_data = self._process_4k_video_row(row)
                    if video_data:
                        videos.append(video_data)
                except Exception as e:
                    logger.error(f"Error procesando fila {row['download_id']}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extrayendo de 4K Video Downloader para {platform_filter}: {e}")
        finally:
            conn.close()
        
        logger.info(f"✓ Procesados {len(videos)} videos de {platform_filter}")
        return videos
    
    def _process_4k_video_row(self, row) -> Optional[Dict]:
        """Procesar una fila de 4K Video Downloader con nueva estructura"""
        # Verificar que el archivo sea un video
        file_path = Path(row['file_path']) if row['file_path'] else None
        if not file_path or file_path.suffix.lower() not in self.video_extensions:
            return None
        
        # ✅ NUEVO: Verificar que el archivo realmente existe
        if not file_path.exists():
            logger.warning(f"⚠️ Archivo no existe (eliminado manualmente?): {file_path}")
            logger.info(f"   📍 URL: {row.get('video_url', 'URL no disponible')}")
            return None
        
        # Procesar metadata
        metadata = self._parse_4k_metadata(row['metadata_concat'])
        
        # Datos básicos del video
        video_data = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'title': row['video_title'] or file_path.stem,
            'post_url': row['video_url'],
            'platform': self._normalize_platform_name(row['platform']) or 'youtube',
            
            # Datos del downloader
            'downloader_data': {
                'download_item_id': row['download_id'],
                'external_db_source': '4k_video',
                'creator_from_downloader': None,  # Se actualizará después según el creador determinado
                'is_carousel_item': False,  # YouTube no tiene carruseles típicamente
                'carousel_order': None,
                'carousel_base_id': None
            }
        }
        
        # Determinar creador y suscripción solo para plataformas principales
        platform_name = self._normalize_platform_name(row['platform']) or 'youtube'
        
        if platform_name == 'youtube':
            # YouTube: crear estructura completa
            creator_info = self._determine_4k_creator_and_subscription(metadata, file_path)
            video_data.update(creator_info)
            # Actualizar creator_from_downloader con el creador determinado
            if 'downloader_data' in video_data and creator_info.get('creator_name'):
                video_data['downloader_data']['creator_from_downloader'] = creator_info['creator_name']
        else:
            # Otras plataformas (Facebook, Twitter, etc.): solo URL del video
            video_data.update({
                'creator_name': None,
                'creator_url': None,
                'subscription_name': None,
                'subscription_type': None,
                'subscription_url': None,
                'list_types': None  # No listas para plataformas secundarias
            })
        
        return video_data
    
    def _parse_4k_metadata(self, metadata_concat: str) -> Dict:
        """Parsear metadata concatenada de 4K Video Downloader"""
        metadata = {}
        
        if not metadata_concat:
            return metadata
        
        # Dividir por separador y procesar cada entrada
        entries = metadata_concat.split('|||')
        for entry in entries:
            if ':' in entry:
                key, value = entry.split(':', 1)
                if value:  # Solo agregar si hay valor
                    metadata[key] = value
        
        return metadata
    
    def _determine_4k_creator_and_subscription(self, metadata: Dict, file_path: Path) -> Dict:
        """Determinar creador y suscripción para 4K Video Downloader"""
        result = {
            'creator_name': None,
            'creator_url': None,
            'subscription_name': None,
            'subscription_type': None,
            'subscription_url': None,
            'list_types': ['feed']  # Por defecto
        }
        
        # Obtener nombre del creador
        creator_name = metadata.get('creator_name')
        if not creator_name:
            # Fallback: usar el nombre de la carpeta padre
            creator_name = file_path.parent.name
            if creator_name in ['4K Video Downloader+', '4K Video Downloader']:
                creator_name = file_path.stem  # Usar nombre del archivo
        
        result['creator_name'] = creator_name
        
        # Construir URL del creador (por ahora solo YouTube)
        if metadata.get('creator_url'):
            result['creator_url'] = metadata['creator_url']
        elif creator_name:
            result['creator_url'] = f"https://www.youtube.com/@{creator_name}"
        
        # Determinar tipo de suscripción
        if metadata.get('playlist_name'):
            # Es una playlist
            result['subscription_name'] = metadata['playlist_name']
            result['subscription_type'] = 'playlist'
            result['subscription_url'] = metadata.get('playlist_url')
            result['list_types'] = ['playlist']
        else:
            # Es canal/cuenta principal
            result['subscription_name'] = creator_name
            result['subscription_type'] = 'account'
            result['subscription_url'] = result['creator_url']
            result['list_types'] = ['feed']
        
        return result
    
    def _normalize_platform_name(self, platform: str) -> str:
        """Normalizar nombre de plataforma"""
        if not platform:
            return 'youtube'  # Por defecto
        
        platform_map = {
            'YouTube': 'youtube',
            'TikTok': 'tiktok', 
            'Instagram': 'instagram',
            'Facebook': 'facebook'
        }
        
        return platform_map.get(platform, platform.lower())
    
    def _extract_video_id_from_url(self, url: str) -> Optional[str]:
        """Extraer ID del video desde URL"""
        if not url:
            return None
        
        # YouTube
        if 'youtube.com' in url or 'youtu.be' in url:
            patterns = [
                r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
                r'youtu.be/([0-9A-Za-z_-]{11})'
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
        
        # TikTok
        if 'tiktok.com' in url:
            match = re.search(r'/video/(\d+)', url)
            if match:
                return match.group(1)
        
        return None
    
    def extract_tiktok_videos(self, offset: int = 0, limit: int = None) -> List[Dict]:
        """Extraer videos de TikTok desde BD de 4K Tokkit con nueva estructura completa
        Solo incluye videos que han sido descargados (downloaded=1)
        """
        if limit is not None:
            logger.debug(f"Extrayendo videos de TikTok descargados (offset: {offset}, limit: {limit})...")
        else:
            logger.debug("Extrayendo videos de TikTok descargados...")
        videos = []

        conn = self._get_connection(self.tiktok_db_path)
        if not conn:
            return videos

        try:
            # Query completa con datos de suscripción según especificación
            if limit is not None:
                # Para asegurar integridad de carruseles de TikTok, primero obtenemos los base_ids únicos
                # con el límite aplicado, luego obtenemos todos los elementos de esos carruseles
                base_id_query = """
                SELECT DISTINCT 
                    CASE 
                        WHEN mi.id LIKE '%_index_%' THEN SUBSTR(mi.id, 1, INSTR(mi.id, '_index_') - 1)
                        ELSE mi.id
                    END as base_id
                FROM MediaItems mi
                WHERE mi.relativePath IS NOT NULL
                GROUP BY base_id
                ORDER BY MIN(mi.databaseId) DESC
                LIMIT ? OFFSET ?
                """
                base_id_cursor = conn.execute(base_id_query, (limit, offset))
                base_ids = [row[0] for row in base_id_cursor.fetchall()]
                
                if not base_ids:
                    rows = []
                else:
                    # Ahora obtenemos todos los elementos de esos carruseles/posts específicos
                    base_id_placeholders = ','.join(['?' for _ in base_ids])
                    query = f"""
                    SELECT 
                        mi.databaseId as media_id,
                        mi.subscriptionDatabaseId,
                        mi.id as tiktok_id,
                        mi.authorName,
                        mi.description as video_title,
                        mi.relativePath,
                        
                        s.type as subscription_type,
                        s.name as subscription_name,
                        s.id as subscription_external_id
                        
                    FROM MediaItems mi
                    LEFT JOIN Subscriptions s ON mi.subscriptionDatabaseId = s.databaseId
                    WHERE mi.relativePath IS NOT NULL
                    AND (
                        (mi.id LIKE '%_index_%' AND SUBSTR(mi.id, 1, INSTR(mi.id, '_index_') - 1) IN ({base_id_placeholders}))
                        OR (mi.id NOT LIKE '%_index_%' AND mi.id IN ({base_id_placeholders}))
                    )
                    ORDER BY mi.databaseId DESC
                    """
                    cursor = conn.execute(query, base_ids + base_ids)
                    rows = cursor.fetchall()
            else:
                query = """
                SELECT 
                    mi.databaseId as media_id,
                    mi.subscriptionDatabaseId,
                    mi.id as tiktok_id,
                    mi.authorName,
                    mi.description as video_title,
                    mi.relativePath,
                    
                    s.type as subscription_type,
                    s.name as subscription_name,
                    s.id as subscription_external_id
                    
                FROM MediaItems mi
                LEFT JOIN Subscriptions s ON mi.subscriptionDatabaseId = s.databaseId
                WHERE mi.relativePath IS NOT NULL
                ORDER BY mi.databaseId DESC
                LIMIT -1 OFFSET ?
                """
                cursor = conn.execute(query, (offset,))
                rows = cursor.fetchall()
            
            # Obtener ruta base de TikTok
            if not self.tiktok_db_path:
                logger.warning("EXTERNAL_TIKTOK_DB no configurado en .env")
                return []
            
            tiktok_base = Path(self.tiktok_db_path).parent  # D:/4K Tokkit/data.sqlite -> D:/4K Tokkit
            
            # Track statistics
            processed_count = 0
            valid_count = 0
            missing_files_count = 0
            
            for row in rows:
                try:
                    processed_count += 1
                    video_data = self._process_tokkit_row_with_structure(row, tiktok_base)
                    if video_data:
                        videos.append(video_data)
                        valid_count += 1
                    else:
                        # Si video_data es None, significa que el archivo no existe
                        missing_files_count += 1
                except Exception as e:
                    logger.error(f"Error procesando fila TikTok {row['media_id']}: {e}")
                    continue
            
            logger.debug(f"✓ Extraídos {valid_count} videos de TikTok desde BD (solo descargados)")
            if missing_files_count > 0:
                logger.debug(f"⚠️ {missing_files_count} archivos no encontrados (eliminados manualmente?)")
            logger.debug(f"📊 Procesados: {processed_count}, Válidos: {valid_count}, Archivos faltantes: {missing_files_count}")
            
            # Guardar estadísticas para el resumen profesional
            self._last_tiktok_stats = {
                'processed': processed_count,
                'valid': valid_count,
                'missing': missing_files_count
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo videos de TikTok: {e}")
        finally:
            conn.close()
        
        return videos
    
    def _process_tokkit_row_with_structure(self, row, tiktok_base: Path) -> Optional[Dict]:
        """Procesar una fila de 4K Tokkit con nueva estructura completa según especificación"""
        # Construir ruta completa del archivo
        relative_path = row['relativePath']
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        if relative_path.startswith('\\'):
            relative_path = relative_path[1:]
            
        file_path = tiktok_base / relative_path
        
        # ✅ Verificar que el archivo exista ANTES de verificar tipo
        if not file_path.exists():
            logger.debug(f"⚠️ Archivo no existe (eliminado manualmente?): {file_path}")
            logger.debug(f"   📍 URL: https://www.tiktok.com/@{row['authorName']}/video/{row['tiktok_id']}")
            return None
            
        # Aceptar tanto videos como imágenes (para carruseles de TikTok)
        is_video = file_path.suffix.lower() in self.video_extensions
        is_image = file_path.suffix.lower() in self.image_extensions
        
        if not (is_video or is_image):
            return None
        
        # Construir URL del post según especificación
        tiktok_id_clean = row['tiktok_id']
        if '_index_' in str(tiktok_id_clean):
            # Para imágenes: remover _index_n1_n2 del ID
            tiktok_id_clean = tiktok_id_clean.split('_index_')[0]
        
        # URLs según especificación
        if is_video:
            post_url = f"https://www.tiktok.com/@{row['authorName']}/video/{tiktok_id_clean}"
        else:
            post_url = f"https://www.tiktok.com/@{row['authorName']}/photo/{tiktok_id_clean}"
        
        # Datos básicos del video
        video_data = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'title': row['video_title'] or file_path.stem,  # Usar description como título
            'post_url': post_url,  # URL del post según especificación
            'platform': 'tiktok',
            'content_type': 'video' if is_video else 'image',
            
            # Datos del downloader
            'downloader_data': {
                'download_item_id': row['media_id'],
                'external_db_source': '4k_tokkit',
                'creator_from_downloader': row['authorName'],
                'is_carousel_item': '_index_' in str(row['tiktok_id']),
                'carousel_order': self._extract_carousel_order(str(row['tiktok_id'])) if '_index_' in str(row['tiktok_id']) else None,
                'carousel_base_id': str(row['tiktok_id']).split('_index_')[0] if '_index_' in str(row['tiktok_id']) else None
            }
        }
        
        # Determinar creador y suscripción según especificación
        creator_info = self._determine_tokkit_creator_and_subscription_v2(row)
        video_data.update(creator_info)
        
        return video_data
    
    def _determine_tokkit_creator_and_subscription_v2(self, row) -> Dict:
        """Determinar creador y suscripción para TikTok según especificación exacta"""
        result = {
            'creator_name': row['authorName'],
            'creator_url': f"https://www.tiktok.com/@{row['authorName']}",
            'subscription_name': None,
            'subscription_type': None,
            'subscription_url': None,
            'list_types': ['single']  # Por defecto para publicaciones sueltas
        }
        
        # CASO 1: Publicaciones sueltas (subscriptionDatabaseId = NULL)
        if not row['subscriptionDatabaseId']:
            # Publicaciones sueltas se convierten en listas tipo "single"
            result['subscription_name'] = 'Videos sueltos'
            result['subscription_type'] = 'single'
            result['subscription_url'] = None  # No tienen URL específica
            result['list_types'] = ['single']
            return result
        
        # CASO 2: Suscripciones con subscription_type
        subscription_types = {
            1: 'account',    # cuenta - tipo 1
            2: 'hashtag',    # hashtag - tipo 2 
            3: 'music'       # música - tipo 3
        }
        
        if row['subscription_type'] in subscription_types:
            sub_type = subscription_types[row['subscription_type']]
            result['subscription_type'] = sub_type
            subscription_name = row['subscription_name']
            result['subscription_name'] = subscription_name
            
            # Construir URL de suscripción según especificación
            if sub_type == 'account':
                result['subscription_url'] = f"https://www.tiktok.com/@{subscription_name}"
                # Para cuentas, detectar sub-listas desde relativePath
                result['list_types'] = self._detect_account_sublists_tiktok(row['relativePath'])
            elif sub_type == 'hashtag':
                result['subscription_url'] = f"https://www.tiktok.com/tag/{subscription_name}"
                result['list_types'] = ['hashtag']  # Los hashtags son listas simples
            elif sub_type == 'music':
                # Música: "cancion nueva cinco" -> "cancion-nueva-cinco"
                clean_name = subscription_name.replace(' ', '-')
                result['subscription_url'] = f"https://www.tiktok.com/music/{clean_name}-{row['subscription_external_id']}"
                result['list_types'] = ['music']  # Las músicas son listas simples
        else:
            # Tipo desconocido - tratar como cuenta
            result['subscription_type'] = 'account'
            result['subscription_name'] = row['subscription_name'] or row['authorName']
            result['subscription_url'] = f"https://www.tiktok.com/@{result['subscription_name']}"
            result['list_types'] = self._detect_account_sublists_tiktok(row['relativePath'])
        
        return result
        
    def _detect_account_sublists_tiktok(self, relative_path: str) -> List[str]:
        """Detectar sublistas para cuentas TikTok según estructura de carpetas"""
        if not relative_path:
            return ['feed']
            
        # Normalizar separadores
        path_normalized = relative_path.replace('\\', '/').lower()
        
        if '/liked/' in path_normalized or '/liked' in path_normalized:
            return ['liked']
        elif '/favorites/' in path_normalized or '/favorites' in path_normalized:
            return ['favorites']
        else:
            return ['feed']  # Por defecto: feed principal
            
    def _extract_carousel_order(self, tiktok_id: str) -> Optional[int]:
        """Extraer orden de carrusel desde ID de TikTok con _index_n1_n2"""
        if '_index_' not in tiktok_id:
            return None
            
        try:
            # Formato: 7534089319917735182_index_0_3
            # Extraer el primer número después de _index_ (n1 = orden)
            parts = tiktok_id.split('_index_')[1].split('_')
            if len(parts) >= 1:
                return int(parts[0])
        except (ValueError, IndexError):
            pass
            
        return None
    
    def extract_instagram_content(self, offset: int = 0, limit: int = None) -> List[Dict]:
        """🆕 NUEVA ESTRUCTURA: Extraer contenido de Instagram desde 4K Stogram con soporte completo"""
        if limit is not None:
            logger.debug(f"Extrayendo contenido de Instagram (offset: {offset}, limit: {limit})...")
        else:
            logger.debug("Extrayendo contenido de Instagram...")
        content = []
        
        conn = self._get_connection(self.instagram_db_path)
        if not conn:
            return content
        
        try:
            # Query completa con JOIN para obtener datos de suscripción
            if limit is not None:
                # Para asegurar integridad de carruseles, primero obtenemos las URLs de posts únicos
                # con el limite aplicado, luego obtenemos todas las fotos de esos posts
                url_query = """
                SELECT DISTINCT p.web_url
                FROM photos p
                WHERE p.file IS NOT NULL AND p.state = 4
                GROUP BY p.web_url
                ORDER BY MIN(p.id) ASC
                LIMIT ? OFFSET ?
                """
                url_cursor = conn.execute(url_query, (limit, offset))
                urls = [row[0] for row in url_cursor.fetchall()]
                
                if not urls:
                    rows = []
                else:
                    # Ahora obtenemos todas las fotos de esos posts específicos
                    url_placeholders = ','.join(['?' for _ in urls])
                    query = f"""
                    SELECT 
                        p.id as photo_id,
                        p.subscriptionId,
                        p.web_url,
                        p.title,
                        p.file as relative_path,
                        p.is_video,
                        p.ownerName,
                        
                        s.type as subscription_type,
                        s.display_name as subscription_display_name
                        
                    FROM photos p
                    LEFT JOIN subscriptions s ON p.subscriptionId = s.id
                    WHERE p.file IS NOT NULL AND p.state = 4 
                    AND p.web_url IN ({url_placeholders})
                    ORDER BY p.web_url, p.id ASC
                    """
                    cursor = conn.execute(query, urls)
                    rows = cursor.fetchall()
            else:
                query = """
                SELECT 
                    p.id as photo_id,
                    p.subscriptionId,
                    p.web_url,
                    p.title,
                    p.file as relative_path,
                    p.is_video,
                    p.ownerName,
                    
                    s.type as subscription_type,
                    s.display_name as subscription_display_name
                    
                FROM photos p
                LEFT JOIN subscriptions s ON p.subscriptionId = s.id
                WHERE p.file IS NOT NULL AND p.state = 4
                ORDER BY p.web_url, p.id ASC
                LIMIT -1 OFFSET ?
                """
                cursor = conn.execute(query, (offset,))
                rows = cursor.fetchall()
            
            # Obtener ruta base de Instagram
            if not self.instagram_db_path:
                logger.warning("EXTERNAL_INSTAGRAM_DB no configurado en .env")
                return []
            
            instagram_base = Path(self.instagram_db_path).parent
            
            # Agrupar por web_url para manejar carruseles
            posts_by_url = {}
            for row in rows:
                web_url = row['web_url']
                if web_url not in posts_by_url:
                    posts_by_url[web_url] = []
                posts_by_url[web_url].append(row)
            
            # Procesar cada publicación (puede tener múltiples archivos)
            for web_url, post_rows in posts_by_url.items():
                try:
                    post_data_list = self._process_stogram_post_with_carousel(post_rows, instagram_base)
                    if post_data_list:
                        # Ahora post_data_list es una lista, agregar cada elemento individualmente
                        content.extend(post_data_list)
                except Exception as e:
                    logger.error(f"Error procesando post Instagram {web_url}: {e}")
                    continue
            
            logger.debug(f"✓ Extraídos {len(content)} posts de Instagram desde BD")
            
        except Exception as e:
            logger.error(f"Error extrayendo contenido de Instagram: {e}")
        finally:
            conn.close()
        
        return content
    
    def _process_stogram_post_with_carousel(self, post_rows, instagram_base: Path) -> Optional[Dict]:
        """Procesar una publicación de Instagram que puede tener múltiples archivos (carrusel)"""
        if not post_rows:
            return None
        
        # Usar la primera fila como base para metadatos
        main_row = post_rows[0]
        
        # Procesar todos los archivos de la publicación
        media_files = []
        valid_files_count = 0
        
        for row in post_rows:
            # Construir ruta completa del archivo
            relative_path = row['relative_path']
            if relative_path.startswith('/'):
                relative_path = relative_path[1:]
            if relative_path.startswith('\\'):
                relative_path = relative_path[1:]
            
            file_path = instagram_base / relative_path
            
            # Verificar que el archivo exista
            if not file_path.exists():
                logger.warning(f"⚠️ Archivo de Instagram no existe (eliminado manualmente?): {file_path}")
                logger.info(f"   📍 URL: {row.get('web_url', 'URL no disponible')}")
                continue
            
            # Determinar tipo de archivo
            is_video = row['is_video'] == 65
            is_image = not is_video and file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
            
            # Solo incluir videos e imágenes válidas
            if not (is_video or is_image):
                continue
            
            media_files.append({
                'file_path': str(file_path),
                'file_name': file_path.name,
                'is_video': is_video,
                'photo_id': row['photo_id']
            })
            valid_files_count += 1
        
        # Si no hay archivos válidos, descartar publicación
        if valid_files_count == 0:
            return None
        
        # Crear una entrada por cada archivo del carrusel
        all_posts = []
        is_carousel = len(media_files) > 1
        
        for idx, media_file in enumerate(media_files):
            # Datos básicos de la publicación para cada archivo
            post_data = {
                'file_path': media_file['file_path'],
                'file_name': media_file['file_name'],
                'title': main_row['title'] or Path(media_file['file_path']).stem,
                'post_url': main_row['web_url'],  # URL del post de Instagram
                'platform': 'instagram',
                
                # Datos del downloader con información de carrusel
                'downloader_data': {
                    'download_item_id': media_file['photo_id'],  # Usar el photo_id específico del archivo
                    'external_db_source': '4k_stogram',
                    'creator_from_downloader': main_row['ownerName'],
                    'is_carousel_item': is_carousel,
                    'carousel_order': idx if is_carousel else None,  # Solo para carruseles
                    'carousel_base_id': main_row['web_url'] if is_carousel else None  # Solo para carruseles
                }
            }
            
            # Determinar creador y suscripción según especificación
            creator_info = self._determine_stogram_creator_and_subscription(main_row, Path(media_file['file_path']))
            post_data.update(creator_info)
            
            all_posts.append(post_data)
        
        return all_posts
    
    def _determine_stogram_creator_and_subscription(self, row, file_path: Path) -> Dict:
        """Determinar creador y suscripción para Instagram según especificación exacta"""
        result = {
            'creator_name': row['ownerName'],
            'creator_url': f"https://www.instagram.com/{row['ownerName']}/",
            'subscription_name': None,
            'subscription_type': None,
            'subscription_url': None,
            'list_types': ['feed']  # Por defecto
        }
        
        # Si hay suscripción asociada
        if row['subscriptionId'] and row['subscription_display_name']:
            subscription_types = {
                1: 'account',    # cuenta
                2: 'hashtag',    # hashtag
                3: 'location',   # location
                4: 'saved'       # guardados
            }
            
            sub_type = subscription_types.get(row['subscription_type'], 'account')
            result['subscription_type'] = sub_type
            result['subscription_name'] = row['subscription_display_name']
            
            # Construir URL de suscripción según especificación
            if sub_type == 'account':
                result['subscription_url'] = f"https://www.instagram.com/{row['subscription_display_name']}/"
            elif sub_type == 'saved':
                result['subscription_url'] = f"https://www.instagram.com/{row['subscription_display_name']}/saved/"
            # Para hashtag y location, Instagram no tiene URLs directas simples
            
        else:
            # Publicación individual (Single media) - subscriptionId NULL
            # Debe tener una suscripción especial tipo 'folder'
            result['subscription_name'] = 'Single media'
            result['subscription_type'] = 'folder'
            result['subscription_url'] = None  # No tiene URL específica
        
        # Determinar list_types desde file path según especificación
        file_path_str = str(file_path).replace('\\', '/')
        list_types = []
        
        if '/highlights/' in file_path_str:
            list_types.append('highlights')
        elif '/reels/' in file_path_str:
            list_types.append('reels')
        elif '/story/' in file_path_str:
            list_types.append('stories')
        elif '/tagged/' in file_path_str:
            list_types.append('tagged')
        elif 'Single media' in file_path_str:
            list_types.append('feed')  # Publicaciones individuales van al feed
        else:
            list_types.append('feed')  # Por defecto
        
        result['list_types'] = list_types
        
        return result
    
    def extract_organized_videos_extended(self, platform_filter: Optional[str] = None) -> List[Dict]:
        """
        🆕 Extraer videos de TODAS las carpetas organizadas (principales + adicionales)
        
        Args:
            platform_filter: 'youtube', 'tiktok', 'instagram', 'other', 'all-platforms', o nombre específico como 'iwara'
        """
        logger.info("Extrayendo videos de carpetas organizadas (modo extendido)...")
        videos = []
        
        # Obtener plataformas disponibles
        available_platforms = self.get_available_platforms()
        
        # Determinar qué carpetas escanear según el filtro
        folders_to_scan = []
        
        if platform_filter is None or platform_filter == 'all-platforms':
            # Escanear todas las plataformas (principales + adicionales)
            # Plataformas principales
            for platform_key, platform_info in available_platforms['main'].items():
                if platform_info['has_organized']:
                    folder_path = getattr(self, f'organized_{platform_key}_path')
                    folders_to_scan.append((folder_path, platform_key, platform_info['folder_name']))
            
            # Plataformas adicionales
            for platform_key, platform_info in available_platforms['additional'].items():
                folders_to_scan.append((platform_info['folder_path'], platform_key, platform_info['folder_name']))
                
        elif platform_filter == 'other':
            # Solo plataformas adicionales (no principales)
            for platform_key, platform_info in available_platforms['additional'].items():
                folders_to_scan.append((platform_info['folder_path'], platform_key, platform_info['folder_name']))
                
        elif platform_filter in ['youtube', 'tiktok', 'instagram']:
            # Plataforma principal específica
            if platform_filter in available_platforms['main'] and available_platforms['main'][platform_filter]['has_organized']:
                folder_path = getattr(self, f'organized_{platform_filter}_path')
                platform_info = available_platforms['main'][platform_filter]
                folders_to_scan.append((folder_path, platform_filter, platform_info['folder_name']))
                
        else:
            # Buscar plataforma específica por nombre (ej: 'iwara')
            platform_found = False
            
            logger.info(f"🔍 Buscando plataforma '{platform_filter}' en plataformas adicionales...")
            logger.info(f"📁 Plataformas adicionales disponibles: {list(available_platforms['additional'].keys())}")
            
            # Buscar en plataformas adicionales
            for platform_key, platform_info in available_platforms['additional'].items():
                logger.debug(f"Comparando: platform_key='{platform_key}' vs platform_filter.lower()='{platform_filter.lower()}'")
                logger.debug(f"Comparando: folder_name.lower()='{platform_info['folder_name'].lower()}' vs platform_filter.lower()='{platform_filter.lower()}'")
                
                if platform_key == platform_filter.lower() or platform_info['folder_name'].lower() == platform_filter.lower():
                    folders_to_scan.append((platform_info['folder_path'], platform_key, platform_info['folder_name']))
                    platform_found = True
                    logger.info(f"✅ Plataforma encontrada: {platform_key} -> {platform_info['folder_path']}")
                    break
            
            if not platform_found:
                logger.warning(f"❌ Plataforma '{platform_filter}' no encontrada en plataformas adicionales")
                logger.info(f"💡 Plataformas disponibles: {list(available_platforms['additional'].keys())}")
                return []
        
        # Escanear las carpetas seleccionadas
        logger.info(f"📂 Carpetas a escanear: {len(folders_to_scan)}")
        
        for folder_path, platform_key, folder_name in folders_to_scan:
            if not folder_path.exists():
                logger.warning(f"❌ Carpeta no existe: {folder_path}")
                continue
            
            logger.info(f"📁 Escaneando carpeta {platform_key} ({folder_name}): {folder_path}")
            
            # Contar carpetas de creadores
            creator_folders = [d for d in folder_path.iterdir() if d.is_dir()]
            logger.info(f"👤 Carpetas de creadores encontradas: {len(creator_folders)}")
            
            # Escanear carpetas de creadores
            for creator_folder in creator_folders:
                creator_name = creator_folder.name
                logger.debug(f"👤 Escaneando creador: {creator_name}")
                
                # Buscar contenido en la carpeta del creador
                for content_file in creator_folder.rglob('*'):
                    if content_file.is_file():
                        # Verificar si es video o imagen
                        is_video = content_file.suffix.lower() in self.video_extensions
                        is_image = content_file.suffix.lower() in self.image_extensions
                        
                        # Para Instagram aceptar imágenes, para otros solo videos
                        should_include = is_video or (platform_key == 'instagram' and is_image)
                        
                        if should_include:
                            video_data = {
                                'file_path': str(content_file),
                                'file_name': content_file.name,
                                'creator_name': creator_name,
                                'platform': platform_key,
                                'title': content_file.stem,
                                'source': f'organized_folder_{folder_name}',
                                'content_type': 'video' if is_video else 'image'
                            }
                            videos.append(video_data)
            
            platform_count = len([v for v in videos if v['platform'] == platform_key])
            logger.info(f"✓ Extraídos {platform_count} elementos de {platform_key} ({folder_name})")
        
        logger.info(f"🎯 Total de videos extraídos del método extend: {len(videos)}")
        return videos

    def extract_organized_videos(self, platform: Optional[str] = None) -> List[Dict]:
        """Extraer videos de las carpetas organizadas en D:\4K All"""
        logger.info("Extrayendo videos de carpetas organizadas...")
        videos = []
        
        # Determinar qué carpetas escanear
        folders_to_scan = []
        if platform is None or platform == 'all':
            folders_to_scan = [
                (self.organized_youtube_path, 'youtube'),
                (self.organized_tiktok_path, 'tiktok'),
                (self.organized_instagram_path, 'instagram')
            ]
        elif platform == 'youtube':
            folders_to_scan = [(self.organized_youtube_path, 'youtube')]
        elif platform == 'tiktok':
            folders_to_scan = [(self.organized_tiktok_path, 'tiktok')]
        elif platform == 'instagram':
            folders_to_scan = [(self.organized_instagram_path, 'instagram')]
        
        for base_path, platform_name in folders_to_scan:
            if not base_path.exists():
                logger.warning(f"Carpeta no existe: {base_path}")
                continue
            
            logger.info(f"Escaneando carpeta {platform_name}: {base_path}")
            
            # Escanear carpetas de creadores
            for creator_folder in base_path.iterdir():
                if not creator_folder.is_dir():
                    continue
                
                creator_name = creator_folder.name
                logger.debug(f"  Procesando creador: {creator_name}")
                
                # Buscar videos en la carpeta del creador
                for video_file in creator_folder.rglob('*'):
                    if video_file.is_file():
                        # Verificar si es video o imagen (para Instagram)
                        is_video = video_file.suffix.lower() in self.video_extensions
                        is_image = video_file.suffix.lower() in self.image_extensions
                        
                        if is_video or (platform_name == 'instagram' and is_image):
                            video_data = {
                                'file_path': str(video_file),
                                'file_name': video_file.name,
                                'creator_name': creator_name,
                                'platform': platform_name,
                                'title': video_file.stem,
                                'source': 'organized_folder',
                                'content_type': 'video' if is_video else 'image'
                            }
                            videos.append(video_data)
            
            logger.info(f"✓ Extraídos {len([v for v in videos if v['platform'] == platform_name])} elementos de {platform_name}")
        
        return videos
    
    def get_all_videos_from_source(self, source: str, platform: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """
        🚀 ESTRATEGIA POPULATE: Siempre encontrar videos nuevos usando offset dinámico
        
        Args:
            source: 'db' para bases de datos, 'organized' para carpetas organizadas, 'all' para ambas
            platform: 'youtube', 'tiktok', 'instagram' o None para todas
            limit: número máximo de videos a retornar
        """
        all_videos = []
        
        # 🚀 NUEVA LÓGICA: Calcular offset dinámico basado en videos existentes
        def get_dynamic_offset(platform_name: str) -> int:
            try:
                from src.database import DatabaseManager
                db = DatabaseManager()
                with db.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT COUNT(*) FROM videos WHERE platform = ? AND deleted_at IS NULL",
                        (platform_name,)
                    )
                    return cursor.fetchone()[0]
            except Exception as e:
                logger.debug(f"Error calculando offset para {platform_name}: {e}")
                return 0
        
        # 🚀 NUEVA ESTRATEGIA: Obtener rutas ya importadas para filtrado inteligente
        def get_imported_paths(platform_name: str) -> set:
            try:
                from src.database import DatabaseManager
                db = DatabaseManager()
                with db.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT file_path FROM videos WHERE platform = ? AND deleted_at IS NULL",
                        (platform_name,)
                    )
                    return {row[0] for row in cursor.fetchall()}
            except Exception as e:
                logger.debug(f"Error obteniendo rutas importadas para {platform_name}: {e}")
                return set()
        
        if source in ['db', 'all']:
            # Extraer de bases de datos
            # Normalizar plataforma: 'all-platforms' -> None para procesamiento
            normalized_platform = None if platform in [None, 'all-platforms'] else platform
            
            # Distribuir límite entre plataformas si es necesario
            platforms_to_extract = []
            if normalized_platform is None:
                # Extraer de todas las plataformas disponibles
                if self.external_youtube_db and self.external_youtube_db.exists():
                    platforms_to_extract.append('youtube')
                if self.tiktok_db_path and self.tiktok_db_path.exists():
                    platforms_to_extract.append('tiktok')
                if self.instagram_db_path and self.instagram_db_path.exists():
                    platforms_to_extract.append('instagram')
                
                # Agregar todas las plataformas 'other' disponibles en 4K Video Downloader
                if self.external_youtube_db and self.external_youtube_db.exists():
                    available_4k_platforms = self.get_available_4k_platforms()
                    for platform_name in available_4k_platforms.keys():
                        if platform_name not in ['youtube', 'tiktok', 'instagram'] and platform_name not in platforms_to_extract:
                            platforms_to_extract.append(platform_name)
            else:
                # 🔍 AUTODETECCIÓN: Usar autodescubrimiento de plataformas
                available_4k_platforms = self.get_available_4k_platforms()
                
                # Verificar si la plataforma solicitada tiene fuente disponible
                platform_sources = {
                    # Plataformas principales con fuentes específicas
                    'tiktok': self.tiktok_db_path and self.tiktok_db_path.exists(),
                    'instagram': self.instagram_db_path and self.instagram_db_path.exists(),
                    # Filtro especial para plataformas no principales
                    'other': self.external_youtube_db and self.external_youtube_db.exists()
                }
                
                # Agregar automáticamente todas las plataformas descubiertas en 4K Video Downloader
                if self.external_youtube_db and self.external_youtube_db.exists():
                    for platform_name in available_4k_platforms.keys():
                        platform_sources[platform_name] = True
                    # Agregar 'other' como plataforma disponible si hay BD de 4K Video Downloader
                    platform_sources['other'] = True
                
                if platform_sources.get(normalized_platform, False):
                    platforms_to_extract.append(normalized_platform)
                else:
                    logger.warning(f"Plataforma '{normalized_platform}' no disponible o sin fuente de datos")
                    logger.info(f"💡 Plataformas disponibles: {list(platform_sources.keys())}")
            
            # Estrategia inteligente de distribución de límites
            platform_limit = None
            if limit and len(platforms_to_extract) > 1:
                # Para límites pequeños: dar más margen para asegurar que se cumpla
                # Para límites grandes: distribuir eficientemente
                if limit <= 20:
                    # Límites pequeños: cada plataforma puede contribuir hasta el límite completo
                    platform_limit = limit
                else:
                    # Límites grandes: distribuir con margen del 50% para compensar desbalances
                    base_limit = limit // len(platforms_to_extract)
                    margin = max(5, limit // 4)  # Margen mínimo de 5 o 25% del límite
                    platform_limit = base_limit + margin
            elif limit:
                platform_limit = limit
            
            # Extraer de cada plataforma según disponibilidad
            for platform_name in platforms_to_extract:
                platform_offset = get_dynamic_offset(platform_name)
                logger.debug(f"🔍 Extrayendo videos de {platform_name.title()} (offset: {platform_offset})...")
                
                if platform_name == 'tiktok':
                    # TikTok usa 4K Tokkit
                    all_videos.extend(self.extract_tiktok_videos(offset=platform_offset, limit=platform_limit))
                elif platform_name == 'instagram':
                    # Instagram usa 4K Stogram
                    all_videos.extend(self.extract_instagram_content(offset=platform_offset, limit=platform_limit))
                else:
                    # YouTube, Facebook, Twitter, etc. usan 4K Video Downloader
                    all_videos.extend(self.extract_4k_video_downloader_by_platform(
                        platform_name, offset=platform_offset, limit=platform_limit
                    ))
        
        if source in ['organized', 'all']:
            # 🆕 Usar extractor extendido para manejar plataformas adicionales  
            # Normalizar plataforma: 'all-platforms' -> None para procesamiento
            normalized_platform = None if platform in [None, 'all-platforms'] else platform
            
            if normalized_platform in ['other'] or (normalized_platform and normalized_platform not in ['youtube', 'tiktok', 'instagram']):
                # Usar extractor extendido para plataformas adicionales o específicas
                all_videos.extend(self.extract_organized_videos_extended(normalized_platform))
            else:
                # Usar extractor clásico para plataformas principales
                all_videos.extend(self.extract_organized_videos(normalized_platform))
        
        # Eliminar duplicados basados en file_path
        seen_paths = set()
        unique_videos = []
        for video in all_videos:
            if video['file_path'] not in seen_paths:
                seen_paths.add(video['file_path'])
                unique_videos.append(video)
        
        # Aplicar límite final si se especifica
        if limit and len(unique_videos) > limit:
            logger.info(f"🔢 Aplicando límite final: {len(unique_videos)} -> {limit} videos")
            unique_videos = unique_videos[:limit]
        
        logger.debug(f"Total de videos únicos extraídos: {len(unique_videos)}")
        return unique_videos
    
    def get_available_platforms(self) -> Dict[str, Dict]:
        """
        🆕 Auto-detectar todas las plataformas disponibles
        Retorna información sobre plataformas principales y adicionales
        """
        platforms = {
            'main': {  # Plataformas principales con integración de BD
                'youtube': {
                    'has_db': self.external_youtube_db and self.external_youtube_db.exists(),
                    'has_organized': self.organized_youtube_path.exists(),
                    'folder_name': 'Youtube'
                },
                'tiktok': {
                    'has_db': self.tiktok_db_path and self.tiktok_db_path.exists(),
                    'has_organized': self.organized_tiktok_path.exists(),
                    'folder_name': 'Tiktok'
                },
                'instagram': {
                    'has_db': self.instagram_db_path and self.instagram_db_path.exists(),
                    'has_organized': self.organized_instagram_path.exists(),
                    'folder_name': 'Instagram'
                }
            },
            'additional': {}  # Plataformas adicionales solo en carpetas
        }
        
        # Auto-detectar plataformas adicionales en D:\4K All
        if self.organized_base_path.exists():
            main_folders = {'Youtube', 'Tiktok', 'Instagram'}  # Carpetas principales conocidas
            
            for folder in self.organized_base_path.iterdir():
                if folder.is_dir() and folder.name not in main_folders:
                    # Es una plataforma adicional
                    platform_key = folder.name.lower()
                    platforms['additional'][platform_key] = {
                        'has_db': False,  # Plataformas adicionales no tienen BD externa
                        'has_organized': True,
                        'folder_name': folder.name,
                        'folder_path': folder
                    }
        
        return platforms
    
    def get_platform_stats_extended(self) -> Dict:
        """
        🆕 Estadísticas extendidas incluyendo plataformas adicionales
        """
        stats = {
            'main': {
                'youtube': {'db': 0, 'organized': 0},
                'tiktok': {'db': 0, 'organized': 0},
                'instagram': {'db': 0, 'organized': 0}
            },
            'additional': {}
        }
        
        try:
            # Stats de plataformas principales (bases de datos)
            yt_videos = self.extract_youtube_videos()
            stats['main']['youtube']['db'] = len(yt_videos)
            
            tt_videos = self.extract_tiktok_videos(offset=0, limit=None)  # Para stats usar offset 0
            stats['main']['tiktok']['db'] = len(tt_videos)
            
            ig_content = self.extract_instagram_content(offset=0, limit=None)  # Para stats usar offset 0
            stats['main']['instagram']['db'] = len(ig_content)
            
            # Stats de carpetas organizadas (principales + adicionales)
            organized_videos = self.extract_organized_videos_extended()
            for video in organized_videos:
                platform = video['platform']
                if platform in stats['main']:
                    stats['main'][platform]['organized'] += 1
                else:
                    if platform not in stats['additional']:
                        stats['additional'][platform] = 0
                    stats['additional'][platform] += 1
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas extendidas: {e}")
        
        return stats

    def get_platform_stats(self) -> Dict:
        """Obtener estadísticas de todas las fuentes"""
        stats = {
            'youtube': {'db': 0, 'organized': 0},
            'tiktok': {'db': 0, 'organized': 0},
            'instagram': {'db': 0, 'organized': 0}
        }
        
        try:
            # Stats de bases de datos
            yt_videos = self.extract_youtube_videos()
            stats['youtube']['db'] = len(yt_videos)
            
            tt_videos = self.extract_tiktok_videos(offset=0, limit=None)  # Para stats usar offset 0
            stats['tiktok']['db'] = len(tt_videos)
            
            ig_content = self.extract_instagram_content(offset=0, limit=None)  # Para stats usar offset 0
            stats['instagram']['db'] = len(ig_content)
            
            # Stats de carpetas organizadas
            organized_videos = self.extract_organized_videos()
            for video in organized_videos:
                platform = video['platform']
                stats[platform]['organized'] += 1
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
        
        return stats
    
    def extract_single_video_info(self, file_path: str) -> Optional[Dict]:
        """
        🆕 Extraer información de un video específico por ruta
        
        Args:
            file_path: Ruta completa al archivo de video
            
        Returns:
            Dict con información del video o None si no se encuentra
        """
        logger.info(f"Extrayendo información de video específico: {file_path}")
        
        file_path = Path(file_path)
        
        # Verificar que el archivo existe
        if not file_path.exists():
            logger.error(f"Archivo no existe: {file_path}")
            return None
        
        # Verificar que es un archivo de video válido
        is_video = file_path.suffix.lower() in self.video_extensions
        is_image = file_path.suffix.lower() in self.image_extensions
        
        if not (is_video or is_image):
            logger.error(f"El archivo no es un video o imagen válida: {file_path}")
            return None
        
        # Intentar determinar la plataforma y fuente analizando la ruta
        platform_info = self._detect_platform_from_path(file_path)
        
        # Buscar información adicional en las bases de datos si pertenece a alguna app 4K
        db_info = self._search_file_in_databases(file_path)
        
        # Construir información del video
        video_data = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'platform': platform_info['platform'],
            'source': platform_info['source'],
            'content_type': 'video' if is_video else 'image'
        }
        
        # Usar información de BD si está disponible
        if db_info:
            video_data.update({
                'creator_name': db_info.get('creator_name', platform_info['creator_name']),
                'title': db_info.get('title', file_path.stem),
                'external_id': db_info.get('external_id')
            })
        else:
            # Usar información inferida de la ruta
            video_data.update({
                'creator_name': platform_info['creator_name'],
                'title': file_path.stem
            })
        
        logger.info(f"✓ Video procesado: {video_data['platform']} - {video_data['creator_name']} - {video_data['file_name']}")
        return video_data
    
    def _detect_platform_from_path(self, file_path: Path) -> Dict:
        """
        Detectar plataforma y creador analizando la ruta del archivo
        """
        file_path_str = str(file_path).replace('\\', '/')
        
        # Detectar si está en las rutas conocidas de apps 4K (mejorado)
        
        # YouTube (4K Video Downloader+) - detectar por nombre de aplicación
        if '4K Video Downloader' in file_path_str or '4kdownload' in file_path_str.lower():
            return {
                'platform': 'youtube',
                'source': 'youtube_db_manual',
                'creator_name': 'Desconocido'
            }
        
        # TikTok (4K Tokkit) - detectar por nombre de aplicación
        if '4K Tokkit' in file_path_str or 'tokkit' in file_path_str.lower():
            return {
                'platform': 'tiktok', 
                'source': 'tiktok_db_manual',
                'creator_name': 'Desconocido'
            }
        
        # Instagram (4K Stogram) - detectar por nombre de aplicación
        if '4K Stogram' in file_path_str or 'stogram' in file_path_str.lower():
            return {
                'platform': 'instagram',
                'source': 'instagram_db_manual', 
                'creator_name': 'Desconocido'
            }
        
        # Detectar si está en las rutas específicas configuradas (fallback)
        
        # YouTube (ruta específica configurada)
        if self.external_youtube_db and str(self.external_youtube_db.parent) in file_path_str:
            return {
                'platform': 'youtube',
                'source': 'youtube_db_manual',
                'creator_name': 'Desconocido'
            }
        
        # TikTok (ruta específica configurada)
        if self.tiktok_db_path and str(self.tiktok_db_path.parent) in file_path_str:
            return {
                'platform': 'tiktok', 
                'source': 'tiktok_db_manual',
                'creator_name': 'Desconocido'
            }
        
        # Instagram (ruta específica configurada)
        if self.instagram_db_path and str(self.instagram_db_path.parent) in file_path_str:
            return {
                'platform': 'instagram',
                'source': 'instagram_db_manual', 
                'creator_name': 'Desconocido'
            }
        
        # Carpetas organizadas
        if self.organized_base_path and str(self.organized_base_path) in file_path_str:
            # Analizar estructura de carpetas para determinar plataforma y creador
            relative_path = file_path.relative_to(self.organized_base_path)
            path_parts = relative_path.parts
            
            if len(path_parts) >= 2:
                platform_folder = path_parts[0].lower()
                creator_name = path_parts[1]
                
                # Mapear nombres de carpetas a plataformas
                platform_mapping = {
                    'youtube': 'youtube',
                    'tiktok': 'tiktok', 
                    'instagram': 'instagram',
                    'iwara': 'iwara'
                }
                
                platform = platform_mapping.get(platform_folder, platform_folder)
                
                return {
                    'platform': platform,
                    'source': f'organized_folder_{platform_folder}',
                    'creator_name': creator_name
                }
        
        # Si no se puede determinar, usar valores por defecto
        return {
            'platform': 'tiktok',  # Mapear a plataforma válida existente
            'source': 'manual_file',
            'creator_name': 'Desconocido'
        }
    
    def _search_file_in_databases(self, file_path: Path) -> Optional[Dict]:
        """
        Buscar información del archivo en las bases de datos externas
        """
        file_path_str = str(file_path)
        
        # Buscar en YouTube DB
        if self.external_youtube_db and self.external_youtube_db.exists():
            conn = self._get_connection(self.external_youtube_db)
            if conn:
                try:
                    query = """
                    SELECT 
                        di.id as download_id,
                        mid.title as video_title,
                        mim.value as creator_name
                    FROM download_item di
                    LEFT JOIN media_item_description mid ON di.id = mid.download_item_id
                    LEFT JOIN media_item_metadata mim ON di.id = mim.download_item_id AND mim.type = 0
                    WHERE di.filename = ?
                    """
                    
                    cursor = conn.execute(query, (file_path_str,))
                    row = cursor.fetchone()
                    
                    if row:
                        return {
                            'creator_name': row['creator_name'],
                            'title': row['video_title'] or file_path.stem,  # 🔧 ARREGLADO: Agregar fallback como las otras funciones
                            'external_id': row['download_id']
                        }
                finally:
                    conn.close()
        
        # Buscar en TikTok DB
        if self.tiktok_db_path and self.tiktok_db_path.exists():
            conn = self._get_connection(self.tiktok_db_path)
            if conn:
                try:
                    # Construir ruta relativa para comparar
                    tiktok_base = self.tiktok_db_path.parent
                    try:
                        relative_path = file_path.relative_to(tiktok_base)
                        relative_path_str = str(relative_path).replace('\\', '/')
                        
                        # Probar con y sin "/" inicial
                        query = """
                        SELECT 
                            id,
                            authorName as creator_name,
                            description as video_title
                        FROM MediaItems
                        WHERE relativePath = ? OR relativePath = ?
                        """
                        
                        cursor = conn.execute(query, (relative_path_str, f"/{relative_path_str}"))
                        row = cursor.fetchone()
                        
                        if row:
                            return {
                                'creator_name': row['creator_name'],
                                'title': row['video_title'] or file_path.stem,  # 🔧 ARREGLADO: Mapear title como title
                                'external_id': row['id']
                            }
                    except ValueError:
                        # El archivo no está dentro de la ruta base de TikTok
                        pass
                finally:
                    conn.close()
        
        # Buscar en Instagram DB
        if self.instagram_db_path and self.instagram_db_path.exists():
            conn = self._get_connection(self.instagram_db_path)
            if conn:
                try:
                    # Construir ruta relativa para comparar
                    instagram_base = self.instagram_db_path.parent
                    try:
                        relative_path = file_path.relative_to(instagram_base)
                        relative_path_str = str(relative_path).replace('\\', '/')
                        
                        query = """
                        SELECT 
                            id,
                            title,
                            ownerName as creator_name
                        FROM photos
                        WHERE file = ?
                        """
                        
                        cursor = conn.execute(query, (relative_path_str,))
                        row = cursor.fetchone()
                        
                        if row:
                            return {
                                'creator_name': row['creator_name'],
                                'title': row['title'] or file_path.stem,  # 🔧 ARREGLADO: Consistente con función global
                                'external_id': row['id']
                            }
                    except ValueError:
                        # El archivo no está dentro de la ruta base de Instagram
                        pass
                finally:
                    conn.close()
        
        return None

# Instancia global removida - usar lazy initialization
