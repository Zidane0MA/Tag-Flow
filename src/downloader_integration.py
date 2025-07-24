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
                    mim.value AS creator_name
                FROM download_item di
                LEFT JOIN media_item_metadata mim
                    ON di.id = mim.download_item_id AND mim.type = 0
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
            
            # Preparar datos para inserción
            video_data = {
                'file_path': str(file_path_obj),
                'file_name': file_path_obj.name,
                'creator_name': self._extract_creator_name(download_item),
                'platform': self._detect_platform(download_item),
                'file_size': download_item['file_size'] if 'file_size' in download_item.keys() else None,
                'duration_seconds': download_item['duration'] if 'duration' in download_item.keys() else None,
                'processing_status': 'pendiente'
            }
            
            # Insertar en BD
            video_id = self.db.add_video(video_data)
            
            # Crear mapeo en tabla de integración
            db_conn = self.db.get_connection()
            with db_conn:
                db_conn.execute("""
                    INSERT INTO downloader_mapping 
                    (video_id, download_item_id, original_filename, creator_from_downloader)
                    VALUES (?, ?, ?, ?)
                """, (
                    video_id,
                    download_item['id'],
                    download_item['title'] if 'title' in download_item.keys() else '',
                    download_item['creator_name'] if 'creator_name' in download_item.keys() else ''
                ))
        
            logger.info(f"Video importado desde 4K Downloader: {file_path_obj.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando item de descarga: {e}")
            return False
    
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