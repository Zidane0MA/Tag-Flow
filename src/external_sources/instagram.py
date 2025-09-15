"""
Tag-Flow V2 - Instagram Stogram Handler
Specialized handler for Instagram content from 4K Stogram database
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .base import DatabaseExtractor
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

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
                        p.ownerId,
                        p.created_time,
                        
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
                    p.ownerId,
                    p.created_time,
                    
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

            # Procesar cada post - FIXED: crear un único post con múltiples media para carruseles
            for web_url, post_rows in posts_by_url.items():
                post_data = self._process_stogram_post_as_single_entry(post_rows, instagram_base, web_url)
                if post_data:
                    content.append(post_data)
            return content

        except Exception as e:
            self.logger.error(f"Error extrayendo contenido de Instagram desde Stogram: {e}")
            return content

    def _process_stogram_carousel_elements(self, post_rows, instagram_base: Path, web_url: str) -> List[Dict]:
        """🚀 ULTRA-OPTIMIZED: Procesar cada elemento con batch operations para máximo rendimiento"""
        carousel_items = []
        
        try:
            if not post_rows or not web_url:
                return carousel_items

            # Determinar si es carrusel (múltiples elementos)
            is_carousel = len(post_rows) > 1
            
            # 🚀 EXTRACT PHASE: Recolectar todas las rutas de archivos
            file_paths_to_check = []
            row_to_filepath = {}
            video_files_for_duration = []
            all_element_data = []
            
            for carousel_order, row in enumerate(post_rows):
                relative_path = self._safe_str(row['relative_path'])
                if not relative_path:
                    continue
                    
                file_path = instagram_base / relative_path
                file_path_str = str(file_path)
                
                file_paths_to_check.append(file_path_str)
                row_to_filepath[carousel_order] = file_path_str
                
                # Preparar datos del elemento para procesamiento posterior
                element_data = {
                    'row': row,
                    'carousel_order': carousel_order,
                    'file_path': file_path,
                    'file_path_str': file_path_str,
                    'relative_path': relative_path
                }
                all_element_data.append(element_data)
            
            # 🚀 BATCH PHASE: Operaciones en lote para máximo rendimiento
            file_stats = self._batch_file_operations(file_paths_to_check)
            
            # Identificar videos para batch duration extraction
            for element_data in all_element_data:
                file_path = element_data['file_path']
                file_stat = file_stats.get(element_data['file_path_str'])
                
                if file_stat is None:  # Archivo no existe
                    continue
                
                # Verificar si es video para batch duration
                video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
                if file_path.suffix.lower() in video_extensions:
                    video_files_for_duration.append(element_data['file_path_str'])
                    
                element_data['file_stat'] = file_stat
            
            # Batch extraction de duraciones para todos los videos
            durations = {}
            if video_files_for_duration:
                durations = self._get_batch_video_durations(video_files_for_duration)
            
            # 🚀 PROCESS PHASE: Aplicar resultados batch a cada elemento
            for element_data in all_element_data:
                file_stat = element_data.get('file_stat')
                if file_stat is None:  # Skip archivos que no existen
                    continue
                    
                video_data = self._process_single_stogram_element_optimized(
                    element_data, instagram_base, web_url, is_carousel, file_stat, durations
                )
                if video_data:
                    carousel_items.append(video_data)
            
            return carousel_items
            
        except Exception as e:
            self.logger.error(f"Error procesando carrusel de Instagram: {e}")
            return carousel_items

    def _process_single_stogram_element_optimized(self, element_data: Dict, instagram_base: Path, web_url: str, is_carousel: bool, file_stat, durations: Dict) -> Optional[Dict]:
        """🚀 OPTIMIZED: Procesar elemento con datos pre-computados (file_stat, durations)"""
        try:
            row = element_data['row']
            carousel_order = element_data['carousel_order']
            file_path = element_data['file_path']
            relative_path = element_data['relative_path']

            # Verificar que es un tipo de archivo válido
            video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            
            is_video_file = file_path.suffix.lower() in video_extensions
            is_image_file = file_path.suffix.lower() in image_extensions
            
            if not (is_video_file or is_image_file):
                return None

            # FIXED: Detect correct media type based on file extension (not database field)
            media_type = 'video' if is_video_file else 'image'

            # Determinar creador y suscripción
            creator_subscription_data = self._determine_stogram_creator_and_subscription(row, file_path)

            # Detectar tipo de lista desde la ruta del archivo
            list_type = self._detect_instagram_list_type(relative_path)

            # 🚀 OPTIMIZED: Usar duración pre-computada en lugar de llamada individual
            duration_seconds = None
            if is_video_file:
                duration_seconds = durations.get(element_data['file_path_str'])

            # Check if we need to use filename as title (when no title from DB)
            title_from_db = self._safe_str(row['title'])
            title_is_filename = not title_from_db or title_from_db.strip() == ''
            final_title = title_from_db if not title_is_filename else file_path.stem

            # Construir estructura completa del elemento
            video_data = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'title': final_title,
                'title_is_filename': title_is_filename,  # Track if filename was used as title
                'platform': 'instagram',
                'content_type': media_type,  # FIXED: Correct media type detection
                'post_url': web_url,
                'source': 'db',

                # Información del creador y suscripción
                'creator_name': creator_subscription_data.get('creator_name'),
                'creator_url': creator_subscription_data.get('creator_url'),
                'subscription_name': creator_subscription_data.get('subscription_name'),
                'subscription_type': creator_subscription_data.get('subscription_type'),
                'subscription_url': creator_subscription_data.get('subscription_url'),
                'subscription_database_id': row['subscriptionId'],  # For external_uuid

                # Metadatos específicos de Instagram - FIXED: Critical fields
                'id': str(self._safe_int(row['photo_id'])),  # platform_post_id
                'photo_id': self._safe_int(row['photo_id']),
                'is_video': self._safe_int(row['is_video']) == 1,
                'web_url': web_url,
                'created_time': self._safe_int(row['created_time']),  # For download_date
                'ownerId': self._safe_str(row['ownerId']) if 'ownerId' in row else None,

                # 🚀 OPTIMIZED: Información de archivo usando file_stat pre-computado
                'file_size': file_stat.st_size,
                'duration_seconds': duration_seconds,

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
            self.logger.error(f"Error procesando elemento optimizado de Instagram Stogram: {e}")
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

    def _process_stogram_post_as_single_entry(self, post_rows, instagram_base: Path, web_url: str) -> Optional[Dict]:
        """🚀 NEW: Process Instagram post as single entry with full carousel support for manager"""
        try:
            if not post_rows or not web_url:
                return None

            # Use first row as base for post metadata
            first_row = post_rows[0]
            is_carousel = len(post_rows) > 1
            
            # Batch file operations for performance
            file_paths_to_check = []
            row_to_data = {}
            
            for row in post_rows:
                relative_path = self._safe_str(row['relative_path'])
                if not relative_path:
                    continue
                    
                file_path = instagram_base / relative_path
                file_path_str = str(file_path)
                file_paths_to_check.append(file_path_str)
                row_to_data[file_path_str] = {
                    'row': row,
                    'file_path': file_path,
                    'relative_path': relative_path
                }
            
            # Batch check file existence
            file_stats = self._batch_file_operations(file_paths_to_check)
            
            # Filter valid files
            valid_items = []
            video_files_for_duration = []
            
            for file_path_str, file_stat in file_stats.items():
                if file_stat is None:
                    continue
                    
                data = row_to_data[file_path_str]
                file_path = data['file_path']
                
                # Check file type
                video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
                image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
                
                is_video_file = file_path.suffix.lower() in video_extensions
                is_image_file = file_path.suffix.lower() in image_extensions
                
                if not (is_video_file or is_image_file):
                    continue
                
                if is_video_file:
                    video_files_for_duration.append(file_path_str)
                
                valid_items.append({
                    'row': data['row'],
                    'file_path': file_path,
                    'file_path_str': file_path_str,
                    'file_stat': file_stat,
                    'is_video': is_video_file,
                    'media_type': 'video' if is_video_file else 'image'
                })
            
            if not valid_items:
                return None
            
            # Batch extract video durations
            durations = {}
            if video_files_for_duration:
                durations = self._get_batch_video_durations(video_files_for_duration)
            
            # Batch extract media resolutions
            all_file_paths = [item['file_path_str'] for item in valid_items]
            resolutions = self._get_batch_media_resolutions(all_file_paths)
            
            # Use first valid item as primary file
            primary_item = valid_items[0]
            primary_row = primary_item['row']
            primary_file_path = primary_item['file_path']
            
            # Determine creator and subscription
            creator_subscription_data = self._determine_stogram_creator_and_subscription(primary_row, primary_file_path)
            
            # Detect list type
            list_type = self._detect_instagram_list_type(primary_item['row']['relative_path'])
            
            # Prepare title
            title_from_db = self._safe_str(primary_row['title'])
            title_is_filename = not title_from_db or title_from_db.strip() == ''
            final_title = title_from_db if not title_is_filename else primary_file_path.stem
            
            # Build main post data
            video_data = {
                'file_path': str(primary_file_path),
                'file_name': primary_file_path.name,
                'title': final_title,
                'title_is_filename': title_is_filename,
                'platform': 'instagram',
                'content_type': primary_item['media_type'],
                'post_url': web_url,
                'source': 'db',

                # Creator and subscription info
                'creator_name': creator_subscription_data.get('creator_name'),
                'creator_url': creator_subscription_data.get('creator_url'),
                'subscription_name': creator_subscription_data.get('subscription_name'),
                'subscription_type': creator_subscription_data.get('subscription_type'),
                'subscription_url': creator_subscription_data.get('subscription_url'),
                'subscription_database_id': primary_row['subscriptionId'],

                # Instagram-specific metadata
                'id': str(self._safe_int(primary_row['photo_id'])),
                'photo_id': self._safe_int(primary_row['photo_id']),
                'is_video': primary_item['is_video'],
                'web_url': web_url,
                'created_time': self._safe_int(primary_row['created_time']),
                'ownerId': self._safe_str(primary_row['ownerId']) if 'ownerId' in primary_row else None,

                # File info
                'file_size': primary_item['file_stat'].st_size,
                'duration_seconds': durations.get(primary_item['file_path_str']) if primary_item['is_video'] else None,

                # Resolution info
                'resolution_width': resolutions.get(primary_item['file_path_str'], (None, None))[0],
                'resolution_height': resolutions.get(primary_item['file_path_str'], (None, None))[1],

                # List types
                'list_types': [list_type],

                # Downloader mapping
                'downloader_mapping': {
                    'download_item_id': self._safe_int(primary_row['photo_id']),
                    'external_db_source': '4k_stogram',
                    'creator_from_downloader': creator_subscription_data.get('creator_name'),
                    'is_carousel_item': is_carousel,
                    'carousel_order': 0 if is_carousel else None,
                    'carousel_base_id': web_url if is_carousel else None
                }
            }
            
            # Add carousel data if multiple items
            if is_carousel:
                video_data['is_carousel'] = True
                carousel_items = []
                
                for order, item in enumerate(valid_items):
                    # Get resolution from batch extraction
                    resolution = resolutions.get(item['file_path_str'], (None, None))
                    width, height = resolution if resolution != (None, None) else (None, None)
                    
                    carousel_item = {
                        'file_path': str(item['file_path']),
                        'file_name': item['file_path'].name,
                        'content_type': item['media_type'],
                        'file_size': item['file_stat'].st_size,
                        'duration_seconds': durations.get(item['file_path_str']) if item['is_video'] else None,
                        'resolution_width': width,
                        'resolution_height': height,
                        'fps': None,
                        'order': order,
                        'photo_id': self._safe_int(item['row']['photo_id'])
                    }
                    carousel_items.append(carousel_item)
                
                video_data['carousel_items'] = carousel_items
            
            return video_data

        except Exception as e:
            self.logger.error(f"Error processing Instagram post as single entry: {e}")
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
                    result['subscription_type'] = 'account'  # FIXED: Use 'account' not 'creator'
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

                elif subscription_type == 'saved':
                    # 🎯 SUSCRIPCIÓN TIPO SAVED: Contenido guardado  
                    # FIXED: Check if name contains ' - saved' pattern and clean it
                    clean_name = subscription_display_name
                    if ' - saved' in subscription_display_name.lower():
                        clean_name = subscription_display_name.split(' - ')[0]
                    
                    result['subscription_name'] = clean_name
                    result['subscription_type'] = 'saved'
                    result['subscription_url'] = f"https://www.instagram.com/{clean_name}/saved/"

            # 🎯 FALLBACK: Si hay subscriptionId pero no se pudo determinar tipo, usar fallback
            if not result['subscription_name'] and result['creator_name']:
                result['subscription_name'] = result['creator_name']
                result['subscription_type'] = 'account'  # FIXED: Use 'account' not 'creator'
                result['subscription_url'] = result['creator_url']

            # 🎯 FALLBACK FINAL: Si no hay creador, extraer de la ruta
            if not result['creator_name']:
                extracted_creator = self._extract_creator_from_path(file_path)
                if extracted_creator:
                    result['creator_name'] = extracted_creator
                    result['creator_url'] = f"https://www.instagram.com/{extracted_creator}/"
                    
                    if not result['subscription_name']:
                        result['subscription_name'] = extracted_creator
                        result['subscription_type'] = 'account'  # FIXED: Use 'account' not 'creator'
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

    def _get_batch_video_durations(self, video_files: List[str]) -> Dict[str, Optional[float]]:
        """Obtener duraciones de múltiples videos usando batch ffprobe (paralelo)"""
        if not video_files:
            return {}
            
        durations = {}
        self.logger.debug(f"🎬 Extrayendo duración de {len(video_files)} videos en lote...")
        
        try:
            import concurrent.futures
            
            def get_duration(file_path: str) -> tuple[str, Optional[float]]:
                """Get duration for single video file"""
                try:
                    path = Path(file_path)
                    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
                    
                    if path.suffix.lower() not in video_extensions:
                        return file_path, None
                    
                    # Usar FFprobe con timeout reducido para batch
                    result = subprocess.run([
                        'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', str(path)
                    ], capture_output=True, text=True, timeout=3)  # Timeout reducido
                    
                    if result.returncode == 0 and result.stdout.strip():
                        duration = float(result.stdout.strip())
                        return file_path, duration
                    return file_path, None
                        
                except Exception as e:
                    self.logger.debug(f"Error obteniendo duración de {Path(file_path).name}: {e}")
                    return file_path, None
            
            # Procesar en paralelo con ThreadPoolExecutor
            max_workers = min(8, len(video_files))  # Máximo 8 hilos para evitar sobrecarga
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Enviar todas las tareas
                future_to_file = {executor.submit(get_duration, file_path): file_path 
                                for file_path in video_files}
                
                # Recoger resultados
                for future in concurrent.futures.as_completed(future_to_file, timeout=30):
                    file_path, duration = future.result()
                    durations[file_path] = duration
                    
            self.logger.debug(f"✅ Duraciones extraídas: {len(durations)} archivos procesados")
            return durations
            
        except Exception as e:
            self.logger.warning(f"Error en batch duration extraction, fallback a método individual: {e}")
            
            # Fallback: procesar uno por uno si batch falla
            for file_path in video_files:
                durations[file_path] = self._get_video_duration(Path(file_path))
                
            return durations

    def _get_batch_media_resolutions(self, file_paths: List[str]) -> Dict[str, tuple]:
        """🚀 NEW: Extract resolution (width, height) from media files in batch"""
        resolutions = {}
        
        if not file_paths:
            return resolutions
        
        try:
            import concurrent.futures
            
            def get_resolution(file_path: str) -> tuple:
                """Extract resolution from single file"""
                try:
                    path = Path(file_path)
                    if not path.exists():
                        return file_path, (None, None)
                    
                    # Determine file type
                    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
                    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
                    
                    suffix = path.suffix.lower()
                    
                    if suffix in video_extensions:
                        # Extract video resolution using OpenCV
                        if CV2_AVAILABLE:
                            try:
                                cap = cv2.VideoCapture(str(path))
                                if cap.isOpened():
                                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                                    cap.release()
                                    if width > 0 and height > 0:
                                        return file_path, (width, height)
                            except Exception as e:
                                self.logger.debug(f"OpenCV failed for {path.name}: {e}")
                        
                        # Fallback to ffprobe for videos
                        try:
                            result = subprocess.run([
                                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                                '-show_entries', 'stream=width,height',
                                '-of', 'csv=p=0', str(path)
                            ], capture_output=True, text=True, timeout=5)
                            
                            if result.returncode == 0 and result.stdout.strip():
                                dimensions = result.stdout.strip().split(',')
                                if len(dimensions) == 2:
                                    width = int(dimensions[0])
                                    height = int(dimensions[1])
                                    if width > 0 and height > 0:
                                        return file_path, (width, height)
                        except Exception as e:
                            self.logger.debug(f"FFprobe failed for {path.name}: {e}")
                    
                    elif suffix in image_extensions:
                        # Extract image resolution using PIL
                        if PIL_AVAILABLE:
                            try:
                                with Image.open(path) as img:
                                    return file_path, img.size  # Returns (width, height)
                            except Exception as e:
                                self.logger.debug(f"PIL failed for {path.name}: {e}")
                        
                        # Fallback to ffprobe for images
                        try:
                            result = subprocess.run([
                                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                                '-show_entries', 'stream=width,height',
                                '-of', 'csv=p=0', str(path)
                            ], capture_output=True, text=True, timeout=5)
                            
                            if result.returncode == 0 and result.stdout.strip():
                                dimensions = result.stdout.strip().split(',')
                                if len(dimensions) == 2:
                                    width = int(dimensions[0])
                                    height = int(dimensions[1])
                                    if width > 0 and height > 0:
                                        return file_path, (width, height)
                        except Exception as e:
                            self.logger.debug(f"FFprobe fallback failed for {path.name}: {e}")
                    
                    return file_path, (None, None)
                    
                except Exception as e:
                    self.logger.debug(f"Error getting resolution for {Path(file_path).name}: {e}")
                    return file_path, (None, None)
            
            # Process in parallel with ThreadPoolExecutor
            max_workers = min(6, len(file_paths))  # Limit workers for resolution extraction
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_file = {executor.submit(get_resolution, file_path): file_path 
                                for file_path in file_paths}
                
                # Collect results
                for future in concurrent.futures.as_completed(future_to_file, timeout=60):
                    file_path, resolution = future.result()
                    resolutions[file_path] = resolution
                    
            self.logger.debug(f"✅ Resolutions extracted: {len(resolutions)} files processed")
            return resolutions
            
        except Exception as e:
            self.logger.warning(f"Error in batch resolution extraction: {e}")
            return resolutions

    def _batch_file_operations(self, file_paths: List[str]) -> Dict[str, Optional[object]]:
        """Batch file existence and stat operations for better performance"""
        if not file_paths:
            return {}
            
        file_stats = {}
        self.logger.debug(f"📁 Verificando existencia y estadísticas de {len(file_paths)} archivos...")
        
        try:
            import concurrent.futures
            
            def get_file_stat(file_path: str) -> tuple[str, Optional[object]]:
                """Get file stat for single file"""
                try:
                    path = Path(file_path)
                    if path.exists():
                        return file_path, path.stat()
                    return file_path, None
                except Exception as e:
                    self.logger.debug(f"Error getting stat for {file_path}: {e}")
                    return file_path, None
            
            # Procesar en paralelo (más rápido para muchos archivos)
            max_workers = min(16, len(file_paths))  # Operaciones I/O pueden usar más hilos
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Enviar todas las tareas
                future_to_file = {executor.submit(get_file_stat, file_path): file_path 
                                for file_path in file_paths}
                
                # Recoger resultados
                for future in concurrent.futures.as_completed(future_to_file, timeout=30):
                    file_path, stat_result = future.result()
                    file_stats[file_path] = stat_result
                    
            existing_count = sum(1 for stat in file_stats.values() if stat is not None)
            self.logger.debug(f"✅ Archivos procesados: {len(file_stats)} total, {existing_count} existentes")
            return file_stats
            
        except Exception as e:
            self.logger.warning(f"Error en batch file operations, fallback a método individual: {e}")
            
            # Fallback: procesar uno por uno si batch falla
            for file_path in file_paths:
                try:
                    path = Path(file_path)
                    if path.exists():
                        file_stats[file_path] = path.stat()
                    else:
                        file_stats[file_path] = None
                except Exception as e:
                    self.logger.debug(f"Error getting stat for {file_path}: {e}")
                    file_stats[file_path] = None
                    
            return file_stats

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