"""
Tag-Flow V2 - Instagram Stogram Handler
Specialized handler for Instagram content from 4K Stogram database
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .base import DatabaseExtractor

import logging
logger = logging.getLogger(__name__)


class InstagramStogramHandler(DatabaseExtractor):
    """Handler for Instagram content from 4K Stogram database"""
    
    def __init__(self, db_path: Optional[Path] = None, base_path: Optional[Path] = None):
        super().__init__(db_path)
        # Auto-derive base path from database path if not provided
        if base_path is None and db_path is not None:
            self.base_path = db_path.parent  # Database is in the same folder as downloaded content
        else:
            self.base_path = base_path
    
    def extract_videos(self, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """🆕 NUEVA ESTRUCTURA: Extraer contenido de Instagram desde 4K Stogram con soporte completo"""
        if limit is not None:
            self.logger.debug(f"Extrayendo contenido de Instagram (offset: {offset}, limit: {limit})...")
        else:
            self.logger.debug("Extrayendo contenido de Instagram...")
        content = []
        
        if not self.is_available():
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
                urls = [row[0] for row in self._execute_query(url_query, (limit, offset))]
                
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
                    ORDER BY p.id ASC
                    """
                    rows = self._execute_query(query, urls)
            else:
                # Sin límite: obtener todo el contenido descargado
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
                ORDER BY p.id ASC
                """
                rows = self._execute_query(query)

            # Configurar base path para Instagram
            instagram_base = self.base_path or Path(".")

            # Agrupar por URL de post para manejar carruseles
            posts_by_url = {}
            for row in rows:
                web_url = self._safe_str(row['web_url'])
                if web_url not in posts_by_url:
                    posts_by_url[web_url] = []
                posts_by_url[web_url].append(row)

            # Procesar cada post - NUEVO: crear un registro por cada elemento del carrusel
            for web_url, post_rows in posts_by_url.items():
                carousel_items = self._process_stogram_carousel_elements(post_rows, instagram_base, web_url)
                content.extend(carousel_items)

            self.logger.info(f"Extraídos {len(content)} posts de Instagram desde Stogram")
            return content

        except Exception as e:
            self.logger.error(f"Error extrayendo contenido de Instagram desde Stogram: {e}")
            return content

    def _process_stogram_carousel_elements(self, post_rows, instagram_base: Path, web_url: str) -> List[Dict]:
        """Procesar cada elemento de un carrusel de Instagram como registro individual"""
        carousel_items = []
        
        try:
            if not post_rows or not web_url:
                return carousel_items

            # Determinar si es carrusel (múltiples elementos)
            is_carousel = len(post_rows) > 1
            
            # Procesar cada elemento del carrusel individualmente
            for carousel_order, row in enumerate(post_rows):
                video_data = self._process_single_stogram_element(row, instagram_base, web_url, is_carousel, carousel_order)
                if video_data:
                    carousel_items.append(video_data)
            
            return carousel_items
            
        except Exception as e:
            self.logger.error(f"Error procesando carrusel de Instagram: {e}")
            return carousel_items

    def _process_single_stogram_element(self, row, instagram_base: Path, web_url: str, is_carousel: bool, carousel_order: int) -> Optional[Dict]:
        """Procesar un solo elemento de Instagram (parte de carrusel o post individual)"""
        try:
            # Verificar que el archivo existe
            relative_path = self._safe_str(row['relative_path'])
            if not relative_path:
                return None
                
            file_path = instagram_base / relative_path
            if not file_path.exists():
                self.logger.debug(f"⚠️ Archivo no existe: {file_path}")
                return None

            # Verificar que es un tipo de archivo válido
            video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            
            is_video_file = file_path.suffix.lower() in video_extensions
            is_image_file = file_path.suffix.lower() in image_extensions
            
            if not (is_video_file or is_image_file):
                return None

            # Determinar creador y suscripción
            creator_subscription_data = self._determine_stogram_creator_and_subscription(row, file_path)

            # Detectar tipo de lista desde la ruta del archivo
            list_type = self._detect_instagram_list_type(relative_path)

            # Construir estructura completa del elemento
            video_data = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'title': self._safe_str(row['title']) or file_path.stem,
                'platform': 'instagram',
                'post_url': web_url,
                'source': 'db',

                # Información del creador y suscripción
                'creator_name': creator_subscription_data.get('creator_name'),
                'creator_url': creator_subscription_data.get('creator_url'),
                'subscription_name': creator_subscription_data.get('subscription_name'),
                'subscription_type': creator_subscription_data.get('subscription_type'),
                'subscription_url': creator_subscription_data.get('subscription_url'),

                # Metadatos específicos de Instagram
                'photo_id': self._safe_int(row['photo_id']),
                'is_video': self._safe_int(row['is_video']) == 1,
                'web_url': web_url,

                # Información de archivo
                'file_size': file_path.stat().st_size if file_path.exists() else 0,
                'duration_seconds': self._get_video_duration(file_path) if is_video_file else None,

                # 🆕 LISTA TYPES - Detectado desde ruta de archivo
                'list_types': [list_type],

                # 🆕 DOWNLOADER MAPPING - Para trazabilidad con BD Stogram
                'downloader_mapping': {
                    'download_item_id': self._safe_int(row['photo_id']),
                    'external_db_source': '4k_stogram',
                    'creator_from_downloader': creator_subscription_data.get('creator_name'),
                    'is_carousel_item': is_carousel,
                    'carousel_order': carousel_order if is_carousel else None,
                    'carousel_base_id': web_url if is_carousel else None
                }
            }

            return video_data

        except Exception as e:
            self.logger.error(f"Error procesando elemento de Instagram Stogram: {e}")
            return None

    def _process_stogram_post_with_carousel(self, post_rows, instagram_base: Path) -> Optional[Dict]:
        """Procesar un post de Instagram que puede tener múltiples elementos (carrusel)"""
        try:
            if not post_rows:
                return None

            # Usar la primera fila como base para metadatos del post
            first_row = post_rows[0]
            web_url = self._safe_str(first_row['web_url'])
            
            if not web_url:
                return None

            # Encontrar el primer video válido en el post
            video_row = None
            for row in post_rows:
                relative_path = self._safe_str(row['relative_path'])
                if not relative_path:
                    continue
                
                file_path = instagram_base / relative_path
                if not file_path.exists():
                    continue
                    
                # Priorizar videos sobre imágenes
                is_video = self._safe_int(row['is_video'])
                if is_video == 1:
                    video_row = row
                    break
                elif video_row is None:  # Si no hay video, usar la primera imagen
                    video_row = row

            if not video_row:
                self.logger.debug(f"No se encontraron archivos válidos para post de Instagram: {web_url}")
                return None

            # Construir ruta del archivo principal
            relative_path = self._safe_str(video_row['relative_path'])
            file_path = instagram_base / relative_path

            # Determinar creador y suscripción
            creator_subscription_data = self._determine_stogram_creator_and_subscription(video_row, file_path)

            # Detectar tipo de lista desde la ruta del archivo
            list_type = self._detect_instagram_list_type(relative_path)
            
            # Determinar si es carrusel y configurar datos del carrusel
            is_carousel = len(post_rows) > 1
            carousel_order = None
            if is_carousel:
                # Encontrar el orden de este elemento específico en el carrusel
                for i, row in enumerate(post_rows):
                    if row['photo_id'] == video_row['photo_id']:
                        carousel_order = i
                        break

            # Construir estructura completa del post
            video_data = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'title': self._safe_str(first_row['title']) or file_path.stem,
                'platform': 'instagram',
                'post_url': web_url,  # Cambio: usar post_url en lugar de video_url para consistencia
                'source': 'db',

                # Información del creador y suscripción
                'creator_name': creator_subscription_data.get('creator_name'),
                'creator_url': creator_subscription_data.get('creator_url'),
                'subscription_name': creator_subscription_data.get('subscription_name'),
                'subscription_type': creator_subscription_data.get('subscription_type'),
                'subscription_url': creator_subscription_data.get('subscription_url'),

                # Metadatos específicos de Instagram
                'photo_id': self._safe_int(video_row['photo_id']),
                'is_video': self._safe_int(video_row['is_video']) == 1,
                'web_url': web_url,

                # Información de archivo
                'file_size': file_path.stat().st_size if file_path.exists() else 0,

                # 🆕 LISTA TYPES - Detectado desde ruta de archivo
                'list_types': [list_type],

                # 🆕 DOWNLOADER MAPPING - Para trazabilidad con BD Stogram
                'downloader_mapping': {
                    'download_item_id': self._safe_int(video_row['photo_id']),
                    'external_db_source': '4k_stogram',
                    'creator_from_downloader': creator_subscription_data.get('creator_name'),
                    'is_carousel_item': is_carousel,
                    'carousel_order': carousel_order,
                    'carousel_base_id': web_url if is_carousel else None
                }
            }

            # Si es un carrusel (múltiples elementos), agregar información
            if len(post_rows) > 1:
                video_data['is_carousel'] = True
                video_data['carousel_count'] = len(post_rows)
                
                # Agregar IDs de todos los elementos del carrusel
                carousel_items = []
                for i, row in enumerate(post_rows):
                    carousel_items.append({
                        'photo_id': self._safe_int(row['photo_id']),
                        'relative_path': self._safe_str(row['relative_path']),
                        'is_video': self._safe_int(row['is_video']) == 1,
                        'order': i
                    })
                video_data['carousel_items'] = carousel_items

            return video_data

        except Exception as e:
            self.logger.error(f"Error procesando post de Instagram Stogram: {e}")
            return None

    def _determine_stogram_creator_and_subscription(self, row, file_path: Path) -> Dict:
        """Determinar creador y suscripción para contenido de Instagram Stogram"""
        result = {
            'creator_name': None,
            'creator_url': None,
            'subscription_name': None,
            'subscription_type': None,
            'subscription_url': None
        }

        try:
            # Información del creador individual del post
            owner_name = self._safe_str(row['ownerName'])
            
            # Información de la suscripción
            subscription_type_raw = self._safe_str(row['subscription_type'])
            subscription_display_name = self._safe_str(row['subscription_display_name'])

            # 🎯 ESTABLECER CREADOR DEL POST (siempre el owner)
            if owner_name:
                result['creator_name'] = owner_name
                result['creator_url'] = f"https://www.instagram.com/{owner_name}/"

            # 🎯 VERIFICAR SI ES PUBLICACIÓN SUELTA (subscriptionId = NULL)
            if not row['subscriptionId']:
                # PUBLICACIÓN SUELTA: Sin suscripción según especificación
                result['subscription_name'] = None
                result['subscription_type'] = None  
                result['subscription_url'] = None
                return result

            # 🎯 ESTABLECER SUSCRIPCIÓN SEGÚN TIPO DE STOGRAM (solo si subscriptionId != NULL)
            if subscription_display_name and subscription_type_raw:
                # Mapear tipos de suscripción de Stogram según especificación
                subscription_type_map = {
                    '1': 'account',      # Cuenta de usuario  
                    '2': 'hashtag',      # Hashtag
                    '3': 'location',     # Ubicación
                    '4': 'saved',        # Contenido guardado/collection
                    # Compatibility fallbacks
                    'account': 'account',
                    'hashtag': 'hashtag', 
                    'location': 'location',
                    'collection': 'saved',
                    'saved': 'saved'
                }

                subscription_type = subscription_type_map.get(str(subscription_type_raw), 'unknown')

                if subscription_type == 'account':
                    # 🎯 SUSCRIPCIÓN TIPO CUENTA: Posts de un usuario específico
                    result['subscription_name'] = subscription_display_name
                    result['subscription_type'] = 'creator'
                    result['subscription_url'] = f"https://www.instagram.com/{subscription_display_name}/"

                elif subscription_type == 'hashtag':
                    # 🎯 SUSCRIPCIÓN TIPO HASHTAG: Posts de un hashtag específico
                    result['subscription_name'] = subscription_display_name
                    result['subscription_type'] = 'hashtag'
                    result['subscription_url'] = f"https://www.instagram.com/explore/tags/{subscription_display_name.lstrip('#')}/"

                elif subscription_type == 'location':
                    # 🎯 SUSCRIPCIÓN TIPO UBICACIÓN: Posts de una ubicación específica
                    result['subscription_name'] = subscription_display_name
                    result['subscription_type'] = 'location'
                    result['subscription_url'] = None  # Las URLs de ubicación son complejas en Instagram

                elif subscription_type == 'collection':
                    # 🎯 SUSCRIPCIÓN TIPO COLECCIÓN: Posts de una colección específica
                    result['subscription_name'] = subscription_display_name
                    result['subscription_type'] = 'collection'
                    result['subscription_url'] = None

                elif subscription_type == 'saved':
                    # 🎯 SUSCRIPCIÓN TIPO SAVED: Contenido guardado/collection
                    result['subscription_name'] = subscription_display_name
                    result['subscription_type'] = 'saved'
                    result['subscription_url'] = None

            # 🎯 FALLBACK: Si hay subscriptionId pero no se pudo determinar tipo, usar fallback
            if not result['subscription_name'] and result['creator_name']:
                result['subscription_name'] = result['creator_name']
                result['subscription_type'] = 'creator'
                result['subscription_url'] = result['creator_url']

            # 🎯 FALLBACK FINAL: Si no hay creador, extraer de la ruta
            if not result['creator_name']:
                extracted_creator = self._extract_creator_from_path(file_path)
                if extracted_creator:
                    result['creator_name'] = extracted_creator
                    result['creator_url'] = f"https://www.instagram.com/{extracted_creator}/"
                    
                    if not result['subscription_name']:
                        result['subscription_name'] = extracted_creator
                        result['subscription_type'] = 'creator'
                        result['subscription_url'] = result['creator_url']

            return result

        except Exception as e:
            self.logger.error(f"Error determinando creador/suscripción Instagram: {e}")
            return result

    def _get_video_duration(self, file_path: Path) -> Optional[float]:
        """Obtener duración del video usando FFprobe (rápido y ligero)"""
        try:
            # Solo procesar videos, no imágenes
            video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
            if file_path.suffix.lower() not in video_extensions:
                return None
            
            # Usar FFprobe para obtener duración rápidamente
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', str(file_path)
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                return duration
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError) as e:
            self.logger.debug(f"Error obteniendo duración de {file_path.name}: {e}")
        except Exception as e:
            self.logger.debug(f"Error inesperado obteniendo duración: {e}")
            
        return None

    def _detect_instagram_list_type(self, relative_path: str) -> str:
        """Detectar tipo de lista de Instagram desde la ruta relativa del archivo"""
        if not relative_path:
            return 'feed'
        
        # Normalizar separadores de ruta
        path_normalized = relative_path.replace('\\', '/').lower()
        
        # Detectar según estructura de carpetas de 4K Stogram
        if '/reels/' in path_normalized:
            return 'reels'
        elif '/highlights/' in path_normalized:
            return 'highlights'
        elif '/story/' in path_normalized:
            return 'story'
        elif '/tagged/' in path_normalized:
            return 'tagged'
        else:
            return 'feed'  # Por defecto: publicaciones del feed principal