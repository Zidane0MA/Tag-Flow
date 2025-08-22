"""
Tag-Flow V2 - Integración con 4K Video Downloader
Importar información de creadores y videos desde 4K Downloader
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from config import config
# 🚀 MIGRADO: Eliminado import directo, ahora se usa via service factory

logger = logging.getLogger(__name__)

class DownloaderIntegration:
    """Integración con 4K Video Downloader para importar metadatos"""
    
    def __init__(self):
        self.external_youtube_db = config.EXTERNAL_YOUTUBE_DB
        self.is_available = self._check_availability()
        # 🚀 LAZY LOADING: Database se carga solo cuando se necesita
        self._db = None
        
        if self.is_available:
            logger.info("4K Video Downloader disponible")
        else:
            logger.warning("4K Video Downloader no disponible o no configurado")
    
    @property
    def db(self):
        """Lazy initialization of DatabaseManager via ServiceFactory"""
        if self._db is None:
            from src.service_factory import get_database
            self._db = get_database()
        return self._db
    
    def _check_availability(self) -> bool:
        """Verificar si la base de datos de 4K Downloader está disponible"""
        if not self.external_youtube_db:
            return False
            
        db_path = Path(self.external_youtube_db)
        return db_path.exists() and db_path.is_file()
    
    def get_downloader_connection(self) -> Optional[sqlite3.Connection]:
        """Obtener conexión a la base de datos de 4K Downloader"""
        if not self.is_available:
            return None
            
        try:
            conn = sqlite3.connect(self.external_youtube_db)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Error conectando a 4K Downloader DB: {e}")
            return None
    
    def import_creators_and_videos(self, limit: Optional[int] = None) -> Dict:
        """Importar creadores y videos desde 4K Downloader
        
        Args:
            limit: Número máximo de videos a importar (None = sin límite)
        """
        if not self.is_available:
            return {
                'success': False,
                'error': '4K Video Downloader no disponible',
                'imported_videos': 0,
                'creators_found': 0
            }
        
        result = {
            'success': False,
            'imported_videos': 0,
            'creators_found': 0,
            'errors': [],
            'creators': []
        }
        
        try:
            with self.get_downloader_connection() as conn:
                if not conn:
                    result['error'] = 'No se pudo conectar a la base de datos'
                    return result
                
                # Obtener información de descargas con límite respetado
                downloads_data = self._get_downloads_data(conn, limit)
                
                # Procesar cada descarga
                for download in downloads_data:
                    try:
                        processed = self._process_download_item(download)
                        if processed:
                            result['imported_videos'] += 1
                            # Agregar creador si es nuevo
                            creator = download['creator_name'].strip() if 'creator_name' in download.keys() and download['creator_name'] else ''
                            if creator and creator not in result['creators']:
                                result['creators'].append(creator)
                    except Exception as e:
                        logger.warning(f"Error procesando item de descarga: {e}")
                        result['errors'].append(str(e))
                
                result['creators_found'] = len(result['creators'])
                result['success'] = True
                
                logger.info(f"Importación completada: {result['imported_videos']} videos, {result['creators_found']} creadores")
                
        except Exception as e:
            logger.error(f"Error en importación de 4K Downloader: {e}")
            result['error'] = str(e)
        
        return result
    
    def _get_downloads_data(self, conn: sqlite3.Connection, limit: Optional[int] = None) -> List[sqlite3.Row]:
        """Obtener datos de descargas desde 4K Downloader+ (YouTube)
        
        Args:
            conn: Conexión a la base de datos
            limit: Número máximo de registros a obtener (None = sin límite)
        """
        try:
            query = """
                SELECT 
                    di.id,
                    di.filename AS file_path,
                    mid.title,
                    ud.service_name,
                    ud.url,
                    -- Obtener información del creador (type 0)
                    creator_meta.value AS creator_name,
                    creator_url.value AS creator_url,
                    -- Obtener información de playlist/subscription (type 3,4,5,6,7)
                    playlist_name.value AS playlist_name,
                    playlist_url.value AS playlist_url,
                    subscription_info.value AS subscription_uuid,
                    -- Determinar tipo de suscripción basado en los types presentes
                    -- PRIORIDAD: playlist_subscription > creator_subscription > individual_video
                    CASE 
                        -- 🎯 PLAYLIST SUBSCRIPTION: Videos que pertenecen a una playlist específica (likes, etc.)
                        WHEN playlist_name.value IS NOT NULL THEN 'playlist_subscription'
                        -- 🎯 CREATOR SUBSCRIPTION: Videos que pertenecen a una suscripción de canal específico
                        WHEN creator_channel_name.value IS NOT NULL THEN 'creator_subscription'  
                        -- 🎯 INDIVIDUAL VIDEO: Videos descargados individualmente
                        ELSE 'individual_video'
                    END AS video_source_type
                FROM download_item di
                LEFT JOIN media_item_description mid ON di.id = mid.download_item_id
                LEFT JOIN url_description ud ON mid.id = ud.media_item_description_id
                -- Información del creador (type 0,1)
                LEFT JOIN media_item_metadata creator_meta 
                    ON di.id = creator_meta.download_item_id AND creator_meta.type = 0
                LEFT JOIN media_item_metadata creator_url 
                    ON di.id = creator_url.download_item_id AND creator_url.type = 1
                -- Información de playlist subscription (type 3,4)
                LEFT JOIN media_item_metadata playlist_name 
                    ON di.id = playlist_name.download_item_id AND playlist_name.type = 3
                LEFT JOIN media_item_metadata playlist_url 
                    ON di.id = playlist_url.download_item_id AND playlist_url.type = 4
                -- Información de creator subscription (type 5,6)
                LEFT JOIN media_item_metadata creator_channel_name 
                    ON di.id = creator_channel_name.download_item_id AND creator_channel_name.type = 5
                LEFT JOIN media_item_metadata creator_channel_url 
                    ON di.id = creator_channel_url.download_item_id AND creator_channel_url.type = 6
                -- UUID de suscripción (type 7)
                LEFT JOIN media_item_metadata subscription_info 
                    ON di.id = subscription_info.download_item_id AND subscription_info.type = 7
                WHERE di.filename IS NOT NULL
                    AND di.filename != ''
                ORDER BY di.id DESC
            """
            
            # Agregar límite si se especifica
            if limit is not None:
                query += f" LIMIT {limit}"
                logger.info(f"🔢 Consultando 4K Downloader con límite: {limit}")
            else:
                logger.info(f"🔢 Consultando 4K Downloader sin límite")
            
            cursor = conn.execute(query)
            return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error consultando 4K Downloader DB: {e}")
            return []
    
    def _process_download_item(self, download_item: sqlite3.Row) -> bool:
        """Procesar un item de descarga individual"""
        try:
            # Extraer información del item
            file_path = download_item['file_path'] if 'file_path' in download_item.keys() else ''
            if not file_path:
                return False
            
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.debug(f"Archivo no existe: {file_path}")
                return False
            
            # Verificar si ya está en nuestra BD
            existing_videos = self.db.get_videos()
            if any(video['file_path'] == str(file_path_obj) for video in existing_videos):
                logger.debug(f"Video ya existe en BD: {file_path_obj.name}")
                return False
            
            # Determinar y crear/buscar la suscripción correcta
            subscription_id = self._get_or_create_subscription(download_item)
            
            # Preparar datos para inserción
            video_data = {
                'file_path': str(file_path_obj),
                'file_name': file_path_obj.name,
                'title': download_item['title'] if 'title' in download_item.keys() else file_path_obj.stem,
                'creator_name': self._extract_creator_name(download_item),
                'platform': self._detect_platform(download_item),
                'post_url': download_item['url'] if 'url' in download_item.keys() else None,
                'file_size': download_item['file_size'] if 'file_size' in download_item.keys() else None,
                'duration_seconds': download_item['duration'] if 'duration' in download_item.keys() else None,
                'processing_status': 'pendiente'
            }
            
            # Agregar subscription_id si se encontró/creó una suscripción
            if subscription_id:
                video_data['subscription_id'] = subscription_id
            
            # Insertar en BD
            video_id = self.db.add_video(video_data)
            
            # Crear mapeo en tabla de integración
            db_conn = self.db.get_connection()
            with db_conn:
                db_conn.execute("""
                    INSERT INTO downloader_mapping 
                    (video_id, download_item_id, original_filename, creator_from_downloader, external_db_source)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    video_id,
                    download_item['id'],
                    download_item['title'] if 'title' in download_item.keys() else '',
                    download_item['creator_name'] if 'creator_name' in download_item.keys() else '',
                    '4k_video'  # Source identifier
                ))
        
            subscription_info = f" (Suscripción ID: {subscription_id})" if subscription_id else ""
            logger.info(f"Video importado desde 4K Downloader: {file_path_obj.name}{subscription_info}")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando item de descarga: {e}")
            return False
    
    def _get_or_create_subscription(self, download_item: sqlite3.Row) -> Optional[int]:
        """Buscar o crear la suscripción correcta basada en el tipo de fuente y retornar su ID"""
        try:
            video_source_type = download_item['video_source_type'] if 'video_source_type' in download_item.keys() else 'individual_video'
            platform = self._detect_platform(download_item)
            
            # Videos individuales no tienen suscripción específica
            if video_source_type == 'individual_video':
                return None
            
            subscription_name = None
            subscription_type = None
            creator_id = None
            subscription_url = None
            
            if video_source_type == 'playlist_subscription':
                # Para suscripciones de playlist (likes, etc.)
                playlist_name = download_item['playlist_name'] if 'playlist_name' in download_item.keys() else None
                if playlist_name:
                    subscription_name = playlist_name.strip()
                    # 🔄 NORMALIZAR nombres equivalentes para usar un nombre preferido
                    if subscription_name in ['Liked videos', 'Videos que me gustan']:
                        subscription_name = 'Liked videos'  # Usar nombre en inglés como preferido
                else:
                    # Fallback: extraer desde la ruta del archivo
                    file_path = download_item['file_path'] if 'file_path' in download_item.keys() else ''
                    if file_path:
                        path_obj = Path(file_path)
                        if len(path_obj.parts) >= 2:
                            subscription_name = path_obj.parts[-2]  # Directorio padre
                    
                    if not subscription_name:
                        return None  # No crear suscripción si no se puede determinar
                
                # 🚫 VERIFICAR: No crear suscripciones para playlists que son solo videos individuales
                if not self._is_valid_playlist_subscription(subscription_name, platform):
                    logger.debug(f"Omitiendo suscripción de playlist para video individual: {subscription_name}")
                    return None
                
                subscription_type = 'playlist'
                subscription_url = download_item['playlist_url'] if 'playlist_url' in download_item.keys() else None
            
            elif video_source_type == 'creator_subscription':
                # Para suscripciones de creador (SOLO para videos que NO pertenecen a playlists)
                creator_name = self._extract_creator_name(download_item)
                
                # 🚫 VERIFICAR: Solo crear suscripciones de creador si hay múltiples videos del mismo creador
                # Y el creador NO es parte de videos de playlist
                if not self._is_valid_creator_subscription(creator_name, platform):
                    logger.debug(f"Omitiendo suscripción de creador para video individual: {creator_name}")
                    return None
                
                subscription_name = creator_name  # Usar solo el nombre del creador
                subscription_type = 'account'
                subscription_url = download_item['creator_url'] if 'creator_url' in download_item.keys() else None
                
                # Buscar creator_id si existe
                creator = self.db.get_creator_by_name(creator_name)
                if creator:
                    creator_id = creator['id']
            
            if not subscription_name:
                return None
            
            # Buscar suscripción existente
            existing_subscription = self._find_existing_subscription(subscription_name, subscription_type, platform, creator_id)
            if existing_subscription:
                return existing_subscription['id']
            
            # Crear nueva suscripción solo si es válida
            return self._create_subscription(subscription_name, subscription_type, platform, creator_id, subscription_url)
                
        except Exception as e:
            logger.warning(f"Error gestionando suscripción: {e}")
            return None
    
    def _is_valid_playlist_subscription(self, playlist_name: str, platform: str) -> bool:
        """Verificar si una playlist tiene múltiples videos y merece ser una suscripción"""
        try:
            # Verificar si ya hay videos en la BD con esta playlist (en la ruta)
            # o si hay múltiples items en 4K Downloader con el mismo playlist_name
            with self.get_downloader_connection() as conn:
                if not conn:
                    return False
                
                # Contar cuántos videos hay con este nombre de playlist en 4K Downloader
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT di.id)
                    FROM download_item di
                    LEFT JOIN media_item_metadata mim ON di.id = mim.download_item_id AND mim.type = 3
                    WHERE mim.value = ? OR di.filename LIKE ?
                """, (playlist_name, f"%{playlist_name}%"))
                
                count = cursor.fetchone()[0] if cursor.fetchone() else 0
                
                # Solo crear suscripción si hay 2 o más videos
                return count >= 2
                
        except Exception as e:
            logger.debug(f"Error verificando playlist válida: {e}")
            # En caso de error, ser conservador y no crear la suscripción
            return False
    
    def _is_valid_creator_subscription(self, creator_name: str, platform: str) -> bool:
        """Verificar si un creador tiene múltiples videos Y NO es parte de playlists"""
        try:
            with self.get_downloader_connection() as conn:
                if not conn:
                    return False
                
                # Verificar si este creador tiene videos que NO pertenecen a playlists
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT di.id) as total_videos,
                           COUNT(DISTINCT CASE WHEN playlist_meta.value IS NULL THEN di.id END) as non_playlist_videos
                    FROM download_item di
                    LEFT JOIN media_item_metadata creator_meta ON di.id = creator_meta.download_item_id AND creator_meta.type = 0
                    LEFT JOIN media_item_metadata playlist_meta ON di.id = playlist_meta.download_item_id AND playlist_meta.type = 3
                    WHERE creator_meta.value = ?
                """, (creator_name,))
                
                row = cursor.fetchone()
                if not row:
                    return False
                
                total_videos = row[0]
                non_playlist_videos = row[1]
                
                # Solo crear suscripción si:
                # 1. Tiene 3+ videos en total del creador
                # 2. Al menos 2 videos NO pertenecen a playlists
                return total_videos >= 3 and non_playlist_videos >= 2
                
        except Exception as e:
            logger.debug(f"Error verificando creador válido: {e}")
            return False
    
    def _find_existing_subscription(self, name: str, subscription_type: str, platform: str, creator_id: Optional[int]) -> Optional[Dict]:
        """Buscar suscripción existente, incluyendo búsqueda por UUID para playlists"""
        try:
            with self.db.get_connection() as conn:
                # Para playlists, buscar también por UUID equivalente
                if subscription_type == 'playlist':
                    # Nombres equivalentes para la misma playlist
                    equivalent_names = []
                    if name in ['Liked videos', 'Videos que me gustan']:
                        equivalent_names = ['Liked videos', 'Videos que me gustan']
                    else:
                        equivalent_names = [name]
                    
                    placeholders = ','.join(['?' for _ in equivalent_names])
                    cursor = conn.execute(f"""
                        SELECT * FROM subscriptions 
                        WHERE name IN ({placeholders}) AND type = ? AND platform = ? AND creator_id IS NULL
                        LIMIT 1
                    """, equivalent_names + [subscription_type, platform])
                else:
                    # Para creators, búsqueda normal
                    if creator_id:
                        cursor = conn.execute("""
                            SELECT * FROM subscriptions 
                            WHERE name = ? AND type = ? AND platform = ? AND creator_id = ?
                        """, (name, subscription_type, platform, creator_id))
                    else:
                        cursor = conn.execute("""
                            SELECT * FROM subscriptions 
                            WHERE name = ? AND type = ? AND platform = ? AND creator_id IS NULL
                        """, (name, subscription_type, platform))
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error buscando suscripción: {e}")
            return None
    
    def _create_subscription(self, name: str, subscription_type: str, platform: str, creator_id: Optional[int], subscription_url: Optional[str]) -> Optional[int]:
        """Crear nueva suscripción y retornar su ID"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO subscriptions (name, type, platform, creator_id, subscription_url)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, subscription_type, platform, creator_id, subscription_url))
                
                subscription_id = cursor.lastrowid
                logger.info(f"Nueva suscripción creada: {name} (ID: {subscription_id})")
                return subscription_id
        except Exception as e:
            logger.error(f"Error creando suscripción: {e}")
            return None
    
    def _extract_creator_name(self, download_item: sqlite3.Row) -> str:
        """Extraer nombre del creador desde los datos de descarga"""
        # Estrategias para extraer el creador:
        # 1. Campo directo
        creator = download_item['creator_name'].strip() if 'creator_name' in download_item.keys() and download_item['creator_name'] else ''
        if creator:
            return creator
        
        # 2. Desde URL (para TikTok/Instagram)
        url = download_item['url'] if 'url' in download_item.keys() and download_item['url'] else ''
        if url:
            creator = self._extract_creator_from_url(url)
            if creator:
                return creator
        
        # 3. Desde título del video
        title = download_item['title'] if 'title' in download_item.keys() and download_item['title'] else ''
        if title:
            creator = self._extract_creator_from_title(title)
            if creator:
                return creator
        
        # Fallback
        return 'Creador Desconocido'
    
    def _extract_creator_from_url(self, url: str) -> Optional[str]:
        """Extraer creador desde URL de TikTok/Instagram"""
        try:
            if 'tiktok.com/@' in url:
                # TikTok: https://www.tiktok.com/@username/video/...
                parts = url.split('@')
                if len(parts) > 1:
                    username = parts[1].split('/')[0]
                    return username
                    
            elif 'instagram.com/' in url:
                # Instagram: https://www.instagram.com/p/... o /username/
                if '/p/' in url:
                    # Post específico - más difícil extraer username
                    pass
                else:
                    parts = url.split('instagram.com/')
                    if len(parts) > 1:
                        username = parts[1].split('/')[0]
                        return username
            
            elif 'youtube.com/watch' in url:
                # YouTube - más complejo, necesitaría API
                pass
                
        except Exception as e:
            logger.debug(f"Error extrayendo creador de URL: {e}")
        
        return None
    
    def _extract_creator_from_title(self, title: str) -> Optional[str]:
        """Extraer creador desde título del video"""
        # Patrones comunes en títulos
        patterns = [
            '@',  # @username en el título
            'by ',  # "by username"
            'de ',  # "de username" 
        ]
        
        for pattern in patterns:
            if pattern in title.lower():
                # Lógica simple para extraer username
                parts = title.split(pattern)
                if len(parts) > 1:
                    potential_creator = parts[1].split()[0].strip()
                    if len(potential_creator) > 2:  # Filtrar abreviaciones
                        return potential_creator.replace('@', '')
        
        return None
    
    def _detect_platform(self, download_item: sqlite3.Row) -> str:
        """Detectar plataforma desde los datos de descarga"""
        url = download_item['url'].lower() if 'url' in download_item.keys() and download_item['url'] else ''
        if 'tiktok.com' in url:
            return 'tiktok'
        elif 'instagram.com' in url:
            return 'instagram'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        else:
            # 🔧 CORREGIDO: 4K Video Downloader es específicamente para YouTube
            return 'youtube'  # Default para videos de YouTube (4K Video Downloader)
    
    def get_integration_stats(self) -> Dict:
        """Obtener estadísticas de la integración"""
        if not self.is_available:
            return {'available': False}
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM downloader_mapping')
                mapped_count = cursor.fetchone()[0]
                
                cursor = conn.execute('''
                    SELECT COUNT(DISTINCT creator_from_downloader) 
                    FROM downloader_mapping 
                    WHERE creator_from_downloader IS NOT NULL
                ''')
                unique_creators = cursor.fetchone()[0]
            
            return {
                'available': True,
                'mapped_videos': mapped_count,
                'unique_creators': unique_creators,
                'last_sync': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de integración: {e}")
            return {'available': True, 'error': str(e)}

# DEPRECATED: Global instance deprecated in favor of ServiceFactory
# Use: from src.services.service_factory import ServiceFactory; service_factory = ServiceFactory(); downloader_integration = service_factory.get_downloader_integration()
# downloader_integration = DownloaderIntegration()