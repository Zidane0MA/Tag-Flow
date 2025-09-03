"""
Tag-Flow V2 - TikTok Tokkit Handler
Specialized handler for TikTok videos from 4K Tokkit database
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from .base import DatabaseExtractor
import subprocess

import logging
logger = logging.getLogger(__name__)


class TikTokTokkitHandler(DatabaseExtractor):
    """Handler for TikTok videos from 4K Tokkit database"""
    
    def __init__(self, db_path: Optional[Path] = None, base_path: Optional[Path] = None):
        super().__init__(db_path)
        # Auto-derive base path from database path if not provided
        if base_path is None and db_path is not None:
            self.base_path = db_path.parent  # Database is in the same folder as downloaded content
        else:
            self.base_path = base_path
    
    def extract_videos(self, offset: int = 0, limit: Optional[int] = None, min_download_item_id = None, min_recording_date: int = None) -> List[Dict]:
        """Extraer videos e imágenes de TikTok desde BD de 4K Tokkit con nueva estructura completa
        Solo incluye contenido descargado (downloaded=1) y excluye imágenes de perfil (mediaType IN (2,3))
        mediaType: 2=video, 3=imagen, 1=coverimg (ignorar)
        """
        if limit is not None:
            self.logger.debug(f"Extrayendo contenido de TikTok descargado (offset: {offset}, limit: {limit})...")
        else:
            self.logger.debug("Extrayendo contenido de TikTok descargado...")
        videos = []

        if not self.is_available():
            return videos

        try:
            # Query completa con datos de suscripción según especificación
            if limit is not None:
                # Para asegurar integridad de carruseles de TikTok, primero obtenemos los base_ids únicos
                # con el límite aplicado, luego obtenemos todos los elementos de esos carruseles
                # Usar min_recording_date si se proporciona (nuevo método), sino usar min_download_item_id (legacy)
                incremental_filter = ""
                incremental_params = []
                
                if min_recording_date is not None:
                    # Nuevo método: usar recordingDate para incremental (maneja duplicados)
                    incremental_filter = "AND mi.recordingDate > ?"
                    incremental_params.append(min_recording_date)
                elif min_download_item_id is not None:
                    # Método legacy: usar databaseId (puede no funcionar correctamente con BLOBs)
                    incremental_filter = "AND mi.databaseId > ?"  
                    incremental_params.append(min_download_item_id)
                
                if incremental_filter:
                    base_id_query = f"""
                    SELECT DISTINCT 
                        CASE 
                            WHEN mi.id LIKE '%_index_%' THEN SUBSTR(mi.id, 1, INSTR(mi.id, '_index_') - 1)
                            ELSE mi.id
                        END as base_id
                    FROM MediaItems mi
                    WHERE mi.relativePath IS NOT NULL 
                    AND mi.downloaded = 1 
                    AND mi.mediaType IN (2, 3)
                    {incremental_filter}
                    GROUP BY base_id
                    ORDER BY MIN(mi.recordingDate) ASC, MIN(mi.databaseId) ASC
                    LIMIT ? OFFSET ?
                    """
                    base_ids = [row[0] for row in self._execute_query(base_id_query, incremental_params + [limit, offset])]
                else:
                    base_id_query = """
                    SELECT DISTINCT 
                        CASE 
                            WHEN mi.id LIKE '%_index_%' THEN SUBSTR(mi.id, 1, INSTR(mi.id, '_index_') - 1)
                            ELSE mi.id
                        END as base_id
                    FROM MediaItems mi
                    WHERE mi.relativePath IS NOT NULL 
                    AND mi.downloaded = 1 
                    AND mi.mediaType IN (2, 3)
                    GROUP BY base_id
                    ORDER BY MIN(mi.recordingDate) ASC, MIN(mi.databaseId) ASC
                    LIMIT ? OFFSET ?
                    """
                    base_ids = [row[0] for row in self._execute_query(base_id_query, (limit, offset))]
                
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
                        mi.postingDate,
                        mi.recordingDate,
                        mi.height,
                        mi.width,
                        
                        s.type as subscription_type,
                        s.name as subscription_name,
                        s.id as subscription_external_id,
                        
                        sds.downloadFeed,
                        sds.downloadLiked,
                        sds.downloadFavorites
                        
                    FROM MediaItems mi
                    LEFT JOIN Subscriptions s ON mi.subscriptionDatabaseId = s.databaseId
                    LEFT JOIN SubscriptionsDownloadSettings sds ON mi.subscriptionDatabaseId = sds.subscriptionDatabaseId
                    WHERE mi.relativePath IS NOT NULL 
                    AND mi.downloaded = 1
                    AND mi.mediaType IN (2, 3)
                    AND (
                        CASE 
                            WHEN mi.id LIKE '%_index_%' THEN SUBSTR(mi.id, 1, INSTR(mi.id, '_index_') - 1)
                            ELSE mi.id
                        END
                    ) IN ({base_id_placeholders})
                    """
                    # NO aplicar filtro incremental aquí - ya fue aplicado en base_id_query
                    query += " ORDER BY mi.recordingDate ASC, mi.databaseId ASC"
                    
                    rows = self._execute_query(query, base_ids)
            else:
                # Sin límite: obtener todos los videos e imágenes descargados
                query = """
                SELECT 
                    mi.databaseId as media_id,
                    mi.subscriptionDatabaseId,
                    mi.id as tiktok_id,
                    mi.authorName,
                    mi.description as video_title,
                    mi.relativePath,
                    mi.postingDate,
                    mi.recordingDate,
                    mi.height,
                    mi.width,
                    
                    s.type as subscription_type,
                    s.name as subscription_name,
                    s.id as subscription_external_id,
                    
                    sds.downloadFeed,
                    sds.downloadLiked,
                    sds.downloadFavorites
                    
                FROM MediaItems mi
                LEFT JOIN Subscriptions s ON mi.subscriptionDatabaseId = s.databaseId
                LEFT JOIN SubscriptionsDownloadSettings sds ON mi.subscriptionDatabaseId = sds.subscriptionDatabaseId
                WHERE mi.relativePath IS NOT NULL 
                AND mi.downloaded = 1
                AND mi.mediaType IN (2, 3)
                """
                
                # Aplicar filtro incremental y ordenamiento
                if min_recording_date is not None:
                    query += " AND mi.recordingDate > ? ORDER BY mi.recordingDate ASC, mi.databaseId ASC"
                    rows = self._execute_query(query, (min_recording_date,))
                elif min_download_item_id is not None:
                    query += " AND mi.databaseId > ? ORDER BY mi.recordingDate ASC, mi.databaseId ASC"
                    rows = self._execute_query(query, (min_download_item_id,))
                else:
                    query += " ORDER BY mi.recordingDate ASC, mi.databaseId ASC"
                    rows = self._execute_query(query)

            # Configurar base path para TikTok
            tiktok_base = self.base_path or Path(".")

            # Pre-procesar todas las rutas de archivo para batch operations
            file_paths_to_check = []
            row_to_filepath = {}
            
            for i, row in enumerate(rows):
                relative_path = row['relativePath']
                if relative_path.startswith('/'):
                    relative_path = relative_path[1:]
                if relative_path.startswith('\\'):
                    relative_path = relative_path[1:]
                
                file_path = tiktok_base / relative_path
                file_paths_to_check.append(str(file_path))
                row_to_filepath[i] = str(file_path)
            
            # Batch file existence and stat operations
            file_stats = self._batch_file_operations(file_paths_to_check)
            
            # Procesar todas las filas con estadísticas pre-calculadas
            all_video_data = []
            video_files_for_duration = []
            
            for i, row in enumerate(rows):
                file_path = row_to_filepath[i]
                file_stat = file_stats.get(file_path)
                
                if file_stat is None:  # Archivo no existe
                    self.logger.debug(f"⚠️ Archivo no existe (eliminado manualmente?): {file_path}")
                    try:
                        author_name = row['authorName'] if row['authorName'] else 'unknown_creator'
                    except (KeyError, TypeError):
                        author_name = 'unknown_creator'
                    self.logger.debug(f"   📍 URL: https://www.tiktok.com/@{author_name}/video/{row['tiktok_id']}")
                    continue
                
                video_data = self._process_tokkit_row_with_structure(
                    row, tiktok_base, extract_duration=False, file_stat=file_stat
                )
                if video_data:
                    all_video_data.append(video_data)
                    # Solo videos necesitan duración
                    if video_data.get('content_type') == 'video':
                        video_files_for_duration.append(video_data['file_path'])
            
            # Batch extraction de duraciones para todos los videos
            if video_files_for_duration:
                durations = self._get_batch_video_durations(video_files_for_duration)
                
                # Aplicar duraciones a los datos
                for video_data in all_video_data:
                    if video_data.get('content_type') == 'video':
                        file_path = video_data['file_path']
                        video_data['duration_seconds'] = durations.get(file_path)
            
            # Group carousel items into single posts
            videos = self._group_carousel_items(all_video_data)
            return videos

        except Exception as e:
            self.logger.error(f"Error extrayendo videos de TikTok desde Tokkit: {e}")
            return videos

    def _process_tokkit_row_with_structure(self, row, tiktok_base: Path, extract_duration: bool = False, file_stat = None) -> Optional[Dict]:
        """Procesar una fila de 4K Tokkit con nueva estructura completa según especificación"""
        # Construir ruta completa del archivo
        relative_path = row['relativePath']
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        if relative_path.startswith('\\'):
            relative_path = relative_path[1:]
            
        file_path = tiktok_base / relative_path
        
        # ✅ Usar estadísticas pre-calculadas (batch file operations)
        if file_stat is None:
            # Archivo no existe (detectado por batch operations)
            self.logger.debug(f"⚠️ Archivo no existe: {file_path}")
            return None
            
        # Aceptar tanto videos como imágenes (para carruseles de TikTok)
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        is_video = file_path.suffix.lower() in video_extensions
        is_image = file_path.suffix.lower() in image_extensions
        
        if not (is_video or is_image):
            return None
        
        # Construir URL del post según especificación
        tiktok_id_clean = row['tiktok_id']
        if '_index_' in str(tiktok_id_clean):
            # Para imágenes: remover _index_n1_n2 del ID
            tiktok_id_clean = tiktok_id_clean.split('_index_')[0]
        
        # URLs según especificación
        try:
            author_name = row['authorName'] if row['authorName'] else 'unknown_creator'
        except (KeyError, TypeError):
            author_name = 'unknown_creator'
        if is_video:
            post_url = f"https://www.tiktok.com/@{author_name}/video/{tiktok_id_clean}" if author_name != 'unknown_creator' else f"https://www.tiktok.com/video/{tiktok_id_clean}"
        else:
            post_url = f"https://www.tiktok.com/@{author_name}/photo/{tiktok_id_clean}" if author_name != 'unknown_creator' else f"https://www.tiktok.com/photo/{tiktok_id_clean}"
        
        # Duración se obtiene por batch processing - individual extraction eliminado

        # Datos básicos del video
        video_data = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'title': row['video_title'] or file_path.stem,  # Usar description como título
            'post_url': post_url,  # URL del post según especificación
            'platform': 'tiktok',
            'content_type': 'video' if is_video else 'image',
            'source': 'db',
            'file_size': file_stat.st_size if file_stat else 0,
            'duration_seconds': None,  # Se asigna por batch processing posteriormente
            
            # Campos que espera el manager (legacy compatibility)
            'authorName': author_name,
            'id': str(row['tiktok_id']),
            'description': row['video_title'] or file_path.stem,
            'postingDate': row['postingDate'] if 'postingDate' in row.keys() else None,  # Unix timestamp
            'recordingDate': row['recordingDate'] if 'recordingDate' in row.keys() else None,  # Unix timestamp
            'height': row['height'] if 'height' in row.keys() else None,
            'width': row['width'] if 'width' in row.keys() else None,
            
            # Datos del downloader - CRÍTICO para batch_insert_videos
            'downloader_mapping': {
                'download_item_id': row['media_id'],
                'external_db_source': '4k_tokkit',
                'creator_from_downloader': author_name,
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
        # Verificar que authorName existe
        try:
            author_name = row['authorName'] if row['authorName'] else 'unknown_creator'
        except (KeyError, TypeError):
            author_name = 'unknown_creator'
        
        result = {
            'creator_name': author_name,
            'creator_url': f"https://www.tiktok.com/@{author_name}" if author_name != 'unknown_creator' else None,
            'subscription_name': None,
            'subscription_type': None,
            'subscription_url': None,
            'subscription_database_id': row['subscriptionDatabaseId'],  # For external_uuid population
            'list_types': ['single']  # Por defecto para publicaciones sueltas
        }
        
        # CASO 1: Publicaciones sueltas (subscriptionDatabaseId = NULL)
        if not row['subscriptionDatabaseId']:
            # Videos sin suscripción - no crear suscripción
            result['subscription_name'] = None
            result['subscription_type'] = None
            result['subscription_url'] = None
            result['list_types'] = []  # Sin listas específicas
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
                # Para cuentas, detectar sub-listas desde relativePath y modificar nombre si es necesario
                # Para cuentas tipo 1, usar los download settings para determinar qué tipo de contenido
                download_feed = row['downloadFeed'] if 'downloadFeed' in row.keys() else 0
                download_liked = row['downloadLiked'] if 'downloadLiked' in row.keys() else 0
                download_favorites = row['downloadFavorites'] if 'downloadFavorites' in row.keys() else 0

                # Determinar la sublista específica según download settings
                if download_liked and not download_feed and not download_favorites:
                    result['subscription_type'] = 'liked'
                    result['subscription_name'] = subscription_name  # Remove " - Liked" suffix
                    result['list_types'] = ['liked']
                elif download_favorites and not download_feed and not download_liked:
                    result['subscription_type'] = 'saved'  
                    result['subscription_name'] = subscription_name  # Remove " - Favorites" suffix
                    result['list_types'] = ['favorites']
                else:
                    # Default to account feed (may include multiple types)
                    result['list_types'] = ['feed']

                
                # Subscription names and types already configured above
                pass
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
            try:
                fallback_author = row['authorName'] if row['authorName'] else 'unknown_creator'
            except (KeyError, TypeError):
                fallback_author = 'unknown_creator'
            subscription_name = row['subscription_name'] or fallback_author
            result['subscription_url'] = f"https://www.tiktok.com/@{subscription_name}"
            
            # Detectar sublistas y modificar nombre si es necesario
            detected_sublists = self._detect_account_sublists_tiktok(row['relativePath'])
            result['list_types'] = detected_sublists
            
            # Always use the subscription name without suffix as requested
            result['subscription_name'] = subscription_name
        
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
    
    def _batch_file_operations(self, file_paths: List[str]) -> Dict[str, Optional[object]]:
        """Batch file existence and stat operations for better performance"""
        if not file_paths:
            return {}
            
        file_stats = {}
        self.logger.debug(f"📁 Verificando existencia y estadísticas de {len(file_paths)} archivos...")
        
        try:
            import concurrent.futures
            from pathlib import Path
            
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
        """Extraer el orden del carrusel desde el ID de TikTok"""
        try:
            if '_index_' in tiktok_id:
                # Formato: base_id_index_N
                parts = tiktok_id.split('_index_')
                if len(parts) == 2:
                    return self._safe_int(parts[1])
            return None

        except Exception as e:
            self.logger.error(f"Error extrayendo orden de carrusel: {e}")
            return None
    
    def _group_carousel_items(self, all_video_data: List[Dict]) -> List[Dict]:
        """Group carousel items into single posts with multiple media items"""
        if not all_video_data:
            return []
        
        # Group by base_id (for carousel posts) 
        grouped_posts = {}
        single_posts = []
        
        for video_data in all_video_data:
            downloader_mapping = video_data.get('downloader_mapping', {})
            carousel_base_id = downloader_mapping.get('carousel_base_id')
            is_carousel_item = downloader_mapping.get('is_carousel_item', False)
            
            if is_carousel_item and carousel_base_id:
                # This is part of a carousel
                if carousel_base_id not in grouped_posts:
                    # Create the main post using the first item's data
                    grouped_posts[carousel_base_id] = {
                        **video_data,  # Copy all data from first item
                        'is_carousel': True,
                        'carousel_items': [],
                        'carousel_count': 0
                    }
                    # Use the base_id as the post ID (without _index_)
                    grouped_posts[carousel_base_id]['id'] = carousel_base_id
                    
                # Add this item to the carousel
                carousel_order = downloader_mapping.get('carousel_order', 0)
                carousel_item = {
                    'file_path': video_data['file_path'],
                    'file_name': video_data['file_name'],
                    'content_type': video_data.get('content_type'),
                    'file_size': video_data.get('file_size'),
                    'duration_seconds': video_data.get('duration_seconds'),
                    'width': video_data.get('width'),
                    'height': video_data.get('height'),
                    'carousel_order': carousel_order,
                    'downloader_mapping': downloader_mapping
                }
                
                grouped_posts[carousel_base_id]['carousel_items'].append(carousel_item)
                grouped_posts[carousel_base_id]['carousel_count'] += 1
                
            else:
                # Single post (not part of a carousel)
                video_data['is_carousel'] = False
                video_data['carousel_count'] = 1
                single_posts.append(video_data)
        
        # Sort carousel items by carousel_order and convert to final format
        final_posts = []
        
        # Add single posts
        final_posts.extend(single_posts)
        
        # Add carousel posts
        for base_id, carousel_post in grouped_posts.items():
            # Sort carousel items by order
            carousel_post['carousel_items'].sort(key=lambda x: x.get('carousel_order', 0))
            final_posts.append(carousel_post)
        
        self.logger.debug(f"📦 Grouped {len(all_video_data)} items into {len(final_posts)} posts ({len(grouped_posts)} carousels, {len(single_posts)} single)")
        return final_posts
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None