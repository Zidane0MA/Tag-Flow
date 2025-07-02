"""
Tag-Flow V2 - Manejo de Fuentes Externas
Extracción de datos desde múltiples bases de datos y carpetas organizadas
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Usar config para las rutas
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import config

logger = logging.getLogger(__name__)

class ExternalSourcesManager:
    """Gestor para extraer datos de fuentes externas (4K Downloader apps + carpetas organizadas)"""
    
    def __init__(self):
        # Rutas de las bases de datos externas (desde config)
        self.external_youtube_db = config.EXTERNAL_YOUTUBE_DB
        self.tiktok_db_path = config.EXTERNAL_TIKTOK_DB  
        self.instagram_db_path = config.EXTERNAL_INSTAGRAM_DB
        
        # Rutas de las carpetas organizadas (desde config)
        self.organized_base_path = config.ORGANIZED_BASE_PATH
        self.organized_youtube_path = config.ORGANIZED_YOUTUBE_PATH
        self.organized_tiktok_path = config.ORGANIZED_TIKTOK_PATH
        self.organized_instagram_path = config.ORGANIZED_INSTAGRAM_PATH
        
        # Extensiones de video soportadas
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
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
    
    def extract_youtube_videos(self) -> List[Dict]:
        """Extraer videos de la base de datos de 4K Video Downloader+"""
        logger.info("Extrayendo videos de YouTube...")
        videos = []
        
        conn = self._get_connection(self.external_youtube_db)
        if not conn:
            return videos
        
        try:
            # Query para obtener videos con metadatos y creadores
            query = """
            SELECT 
                di.id as download_id,
                di.filename as file_path,
                mid.title as video_title,
                mim.value as creator_name
            FROM download_item di
            LEFT JOIN media_item_description mid ON di.id = mid.download_item_id
            LEFT JOIN media_item_metadata mim ON di.id = mim.download_item_id AND mim.type = 0
            WHERE di.filename IS NOT NULL
            ORDER BY di.id DESC
            """
            
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                file_path = Path(row['file_path'])
                
                # Verificar que el archivo exista y sea un video
                if file_path.exists() and file_path.suffix.lower() in self.video_extensions:
                    video_data = {
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'creator_name': row['creator_name'] or 'Desconocido',
                        'platform': 'youtube',
                        'title': row['video_title'] or file_path.stem,
                        'source': 'youtube_db',
                        'external_id': row['download_id']
                    }
                    videos.append(video_data)
            
            logger.info(f"✓ Extraídos {len(videos)} videos de YouTube desde BD")
            
        except Exception as e:
            logger.error(f"Error extrayendo videos de YouTube: {e}")
        finally:
            conn.close()
        
        return videos
    
    def extract_tiktok_videos(self) -> List[Dict]:
        """Extraer videos de la base de datos de 4K Tokkit"""
        logger.info("Extrayendo videos de TikTok...")
        videos = []
        
        conn = self._get_connection(self.tiktok_db_path)
        if not conn:
            return videos
        
        try:
            query = """
            SELECT 
                id,
                authorName as creator_name,
                description as video_title,
                relativePath as relative_path
            FROM MediaItems
            WHERE relativePath IS NOT NULL
            ORDER BY id DESC
            """
            
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
            # 🆕 MEJORADO: Extraer ruta base dinámicamente de EXTERNAL_TIKTOK_DB
            if not self.tiktok_db_path:
                logger.warning("EXTERNAL_TIKTOK_DB no configurado en .env")
                return []
            
            tiktok_base = Path(self.tiktok_db_path).parent  # D:/4K Tokkit/data.sqlite -> D:/4K Tokkit
            
            for row in rows:
                relative_path = row['relative_path']
                
                # Manejar paths que empiezan con "/" (eliminar para hacer verdaderamente relativo)
                if relative_path.startswith('/'):
                    relative_path = relative_path[1:]  # Remover el "/" inicial
                
                file_path = tiktok_base / relative_path
                
                # Verificar que el archivo exista y sea un video
                if file_path.exists() and file_path.suffix.lower() in self.video_extensions:
                    video_data = {
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'creator_name': row['creator_name'] or 'Desconocido',
                        'platform': 'tiktok',
                        'title': row['video_title'] or file_path.stem,
                        'source': 'tiktok_db',
                        'external_id': row['id']
                    }
                    videos.append(video_data)
            
            logger.info(f"✓ Extraídos {len(videos)} videos de TikTok desde BD")
            
        except Exception as e:
            logger.error(f"Error extrayendo videos de TikTok: {e}")
        finally:
            conn.close()
        
        return videos
    
    def extract_instagram_content(self) -> List[Dict]:
        """Extraer contenido de la base de datos de 4K Stogram"""
        logger.info("Extrayendo contenido de Instagram...")
        content = []
        
        conn = self._get_connection(self.instagram_db_path)
        if not conn:
            return content
        
        try:
            query = """
            SELECT 
                id,
                title,
                file as relative_path,
                ownerName as creator_name
            FROM photos
            WHERE file IS NOT NULL
            ORDER BY id DESC
            """
            
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
            # 🆕 MEJORADO: Extraer ruta base dinámicamente de EXTERNAL_INSTAGRAM_DB
            if not self.instagram_db_path:
                logger.warning("EXTERNAL_INSTAGRAM_DB no configurado en .env")
                return []
            
            instagram_base = Path(self.instagram_db_path).parent  # D:/4K Stogram/.stogram.sqlite -> D:/4K Stogram
            
            for row in rows:
                relative_path = row['relative_path']
                file_path = instagram_base / relative_path
                
                # Verificar que el archivo exista
                if file_path.exists():
                    # Determinar si es video o imagen
                    is_video = file_path.suffix.lower() in self.video_extensions
                    is_image = file_path.suffix.lower() in self.image_extensions
                    
                    if is_video or is_image:
                        content_data = {
                            'file_path': str(file_path),
                            'file_name': file_path.name,
                            'creator_name': row['creator_name'] or 'Desconocido',
                            'platform': 'instagram',
                            'title': row['title'] or file_path.stem,
                            'source': 'instagram_db',
                            'external_id': row['id'],
                            'content_type': 'video' if is_video else 'image'
                        }
                        content.append(content_data)
            
            logger.info(f"✓ Extraídos {len(content)} elementos de Instagram desde BD")
            
        except Exception as e:
            logger.error(f"Error extrayendo contenido de Instagram: {e}")
        finally:
            conn.close()
        
        return content
    
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
            
            # Buscar en plataformas adicionales
            for platform_key, platform_info in available_platforms['additional'].items():
                if platform_key == platform_filter.lower() or platform_info['folder_name'].lower() == platform_filter.lower():
                    folders_to_scan.append((platform_info['folder_path'], platform_key, platform_info['folder_name']))
                    platform_found = True
                    break
            
            if not platform_found:
                logger.warning(f"Plataforma '{platform_filter}' no encontrada")
                return []
        
        # Escanear las carpetas seleccionadas
        for folder_path, platform_key, folder_name in folders_to_scan:
            if not folder_path.exists():
                logger.warning(f"Carpeta no existe: {folder_path}")
                continue
            
            logger.info(f"Escaneando carpeta {platform_key} ({folder_name}): {folder_path}")
            
            # Escanear carpetas de creadores
            for creator_folder in folder_path.iterdir():
                if not creator_folder.is_dir():
                    continue
                
                creator_name = creator_folder.name
                logger.debug(f"  Procesando creador: {creator_name}")
                
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
        Obtener videos de una fuente específica
        
        Args:
            source: 'db' para bases de datos, 'organized' para carpetas organizadas, 'all' para ambas
            platform: 'youtube', 'tiktok', 'instagram' o None para todas
            limit: número máximo de videos a retornar
        """
        all_videos = []
        
        if source in ['db', 'all']:
            # Extraer de bases de datos
            if platform is None or platform == 'youtube':
                all_videos.extend(self.extract_youtube_videos())
            
            if platform is None or platform == 'tiktok':
                all_videos.extend(self.extract_tiktok_videos())
            
            if platform is None or platform == 'instagram':
                all_videos.extend(self.extract_instagram_content())
        
        if source in ['organized', 'all']:
            # 🆕 Usar extractor extendido para manejar plataformas adicionales
            if platform in ['other', 'all-platforms'] or (platform and platform not in ['youtube', 'tiktok', 'instagram']):
                # Usar extractor extendido para plataformas adicionales o específicas
                all_videos.extend(self.extract_organized_videos_extended(platform))
            else:
                # Usar extractor clásico para plataformas principales
                all_videos.extend(self.extract_organized_videos(platform))
        
        # Eliminar duplicados basados en file_path
        seen_paths = set()
        unique_videos = []
        for video in all_videos:
            if video['file_path'] not in seen_paths:
                seen_paths.add(video['file_path'])
                unique_videos.append(video)
        
        # Aplicar límite si se especifica
        if limit and len(unique_videos) > limit:
            unique_videos = unique_videos[:limit]
        
        logger.info(f"Total de videos únicos extraídos: {len(unique_videos)}")
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
            
            tt_videos = self.extract_tiktok_videos()
            stats['main']['tiktok']['db'] = len(tt_videos)
            
            ig_content = self.extract_instagram_content()
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
            
            tt_videos = self.extract_tiktok_videos()
            stats['tiktok']['db'] = len(tt_videos)
            
            ig_content = self.extract_instagram_content()
            stats['instagram']['db'] = len(ig_content)
            
            # Stats de carpetas organizadas
            organized_videos = self.extract_organized_videos()
            for video in organized_videos:
                platform = video['platform']
                stats[platform]['organized'] += 1
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
        
        return stats

# Instancia global
external_sources = ExternalSourcesManager()
