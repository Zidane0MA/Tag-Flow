"""
Tag-Flow V2 - TikTok Tokkit Handler
Specialized handler for TikTok videos from 4K Tokkit database
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from .base import DatabaseExtractor
import subprocess
import json
import os
from datetime import datetime, timedelta

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
            
        # Duration cache system
        self.duration_cache_file = Path("data/duration_cache_tiktok.json")
        self.duration_cache = self._load_duration_cache()
        self.cache_expiry_days = 30  # Cache válido por 30 días
    
    def extract_videos(self, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """Extraer videos e imágenes de TikTok desde BD de 4K Tokkit con nueva estructura completa
        Solo incluye contenido descargado (downloaded=1) y excluye imágenes de perfil (MediaType IN (2,3))
        MediaType: 2=video, 3=imagen, 1=coverimg (ignorar)
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
                base_id_query = """
                SELECT DISTINCT 
                    CASE 
                        WHEN mi.id LIKE '%_index_%' THEN SUBSTR(mi.id, 1, INSTR(mi.id, '_index_') - 1)
                        ELSE mi.id
                    END as base_id
                FROM MediaItems mi
                WHERE mi.relativePath IS NOT NULL 
                AND mi.downloaded = 1 
                AND mi.MediaType IN (2, 3)
                GROUP BY base_id
                ORDER BY MIN(mi.databaseId) DESC
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
                        
                        s.type as subscription_type,
                        s.name as subscription_name,
                        s.id as subscription_external_id
                        
                    FROM MediaItems mi
                    LEFT JOIN Subscriptions s ON mi.subscriptionDatabaseId = s.databaseId
                    WHERE mi.relativePath IS NOT NULL 
                    AND mi.downloaded = 1
                    AND mi.MediaType IN (2, 3)
                    AND (
                        CASE 
                            WHEN mi.id LIKE '%_index_%' THEN SUBSTR(mi.id, 1, INSTR(mi.id, '_index_') - 1)
                            ELSE mi.id
                        END
                    ) IN ({base_id_placeholders})
                    ORDER BY mi.databaseId DESC
                    """
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
                    
                    s.type as subscription_type,
                    s.name as subscription_name,
                    s.id as subscription_external_id
                    
                FROM MediaItems mi
                LEFT JOIN Subscriptions s ON mi.subscriptionDatabaseId = s.databaseId
                WHERE mi.relativePath IS NOT NULL 
                AND mi.downloaded = 1
                AND mi.MediaType IN (2, 3)
                ORDER BY mi.databaseId DESC
                """
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
                    self.logger.debug(f"   📍 URL: https://www.tiktok.com/@{row['authorName']}/video/{row['tiktok_id']}")
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
            
            videos = all_video_data
            return videos

        except Exception as e:
            self.logger.error(f"Error extrayendo videos de TikTok desde Tokkit: {e}")
            return videos

    def _process_tokkit_row_with_structure(self, row, tiktok_base: Path, extract_duration: bool = True, file_stat = None) -> Optional[Dict]:
        """Procesar una fila de 4K Tokkit con nueva estructura completa según especificación"""
        # Construir ruta completa del archivo
        relative_path = row['relativePath']
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        if relative_path.startswith('\\'):
            relative_path = relative_path[1:]
            
        file_path = tiktok_base / relative_path
        
        # ✅ Usar estadísticas pre-calculadas si están disponibles
        if file_stat is None:
            # Fallback para compatibilidad
            if not file_path.exists():
                self.logger.debug(f"⚠️ Archivo no existe (eliminado manualmente?): {file_path}")
                self.logger.debug(f"   📍 URL: https://www.tiktok.com/@{row['authorName']}/video/{row['tiktok_id']}")
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
        if is_video:
            post_url = f"https://www.tiktok.com/@{row['authorName']}/video/{tiktok_id_clean}"
        else:
            post_url = f"https://www.tiktok.com/@{row['authorName']}/photo/{tiktok_id_clean}"
        
        # Obtener duración para videos (optimizado)
        duration_seconds = None
        if is_video and extract_duration:
            duration_seconds = self._get_video_duration(file_path)

        # Datos básicos del video
        video_data = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'title': row['video_title'] or file_path.stem,  # Usar description como título
            'post_url': post_url,  # URL del post según especificación
            'platform': 'tiktok',
            'content_type': 'video' if is_video else 'image',
            'source': 'db',
            'file_size': file_stat.st_size if file_stat else (file_path.stat().st_size if file_path.exists() else 0),
            'duration_seconds': duration_seconds,
            
            # Datos del downloader - CRÍTICO para batch_insert_videos
            'downloader_mapping': {
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
                detected_sublists = self._detect_account_sublists_tiktok(row['relativePath'])
                result['list_types'] = detected_sublists
                
                # Si es una sublista específica, modificar el nombre de suscripción para distinguirlas
                if detected_sublists == ['liked']:
                    result['subscription_name'] = f"{subscription_name} - Liked"
                elif detected_sublists == ['favorites']:
                    result['subscription_name'] = f"{subscription_name} - Favorites"
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
            subscription_name = row['subscription_name'] or row['authorName']
            result['subscription_url'] = f"https://www.tiktok.com/@{subscription_name}"
            
            # Detectar sublistas y modificar nombre si es necesario
            detected_sublists = self._detect_account_sublists_tiktok(row['relativePath'])
            result['list_types'] = detected_sublists
            
            if detected_sublists == ['liked']:
                result['subscription_name'] = f"{subscription_name} - Liked"
            elif detected_sublists == ['favorites']:
                result['subscription_name'] = f"{subscription_name} - Favorites"  
            else:
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
        """Obtener duraciones de múltiples videos usando cache + batch ffprobe (paralelo)"""
        if not video_files:
            return {}
            
        durations = {}
        files_to_process = []
        cache_hits = 0
        
        # Primero, intentar obtener duraciones desde cache
        for file_path in video_files:
            cached_duration = self._get_cached_duration(file_path)
            if cached_duration is not None:
                durations[file_path] = cached_duration
                cache_hits += 1
            else:
                files_to_process.append(file_path)
        
        self.logger.debug(f"🎬 Cache hits: {cache_hits}/{len(video_files)}, procesando: {len(files_to_process)} videos")
        
        # Procesar archivos que no están en cache
        if files_to_process:
            try:
                import concurrent.futures
                import threading
                
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
                max_workers = min(8, len(files_to_process))  # Máximo 8 hilos para evitar sobrecarga
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Enviar todas las tareas
                    future_to_file = {executor.submit(get_duration, file_path): file_path 
                                    for file_path in files_to_process}
                    
                    # Recoger resultados y cachear
                    for future in concurrent.futures.as_completed(future_to_file, timeout=30):
                        file_path, duration = future.result()
                        durations[file_path] = duration
                        # Cachear resultado para futuras ejecuciones
                        self._cache_duration(file_path, duration)
                        
                self.logger.debug(f"✅ Duraciones extraídas: {len(files_to_process)} nuevas, {cache_hits} desde cache")
                
                # Guardar cache actualizado
                self._save_duration_cache()
                
            except Exception as e:
                self.logger.warning(f"Error en batch duration extraction, fallback a método individual: {e}")
                
                # Fallback: procesar uno por uno si batch falla
                for file_path in files_to_process:
                    duration = self._get_video_duration(Path(file_path))
                    durations[file_path] = duration
                    self._cache_duration(file_path, duration)
                
                # Guardar cache incluso en fallback
                self._save_duration_cache()
        
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
    
    def _load_duration_cache(self) -> Dict[str, Dict]:
        """Cargar cache de duraciones desde archivo"""
        try:
            if self.duration_cache_file.exists():
                with open(self.duration_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Limpiar entradas expiradas
                current_time = datetime.now()
                cleaned_cache = {}
                for file_path, entry in cache_data.items():
                    cache_time = datetime.fromisoformat(entry['cached_at'])
                    if current_time - cache_time < timedelta(days=self.cache_expiry_days):
                        cleaned_cache[file_path] = entry
                
                if len(cleaned_cache) != len(cache_data):
                    self.logger.debug(f"Limpiado cache: {len(cache_data) - len(cleaned_cache)} entradas expiradas")
                
                self.logger.debug(f"📦 Cache de duración cargado: {len(cleaned_cache)} entradas")
                return cleaned_cache
        except Exception as e:
            self.logger.debug(f"Error cargando cache de duración: {e}")
        
        return {}
    
    def _save_duration_cache(self) -> None:
        """Guardar cache de duraciones a archivo"""
        try:
            # Crear directorio si no existe
            self.duration_cache_file.parent.mkdir(exist_ok=True)
            
            with open(self.duration_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.duration_cache, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"💾 Cache de duración guardado: {len(self.duration_cache)} entradas")
        except Exception as e:
            self.logger.warning(f"Error guardando cache de duración: {e}")
    
    def _get_cached_duration(self, file_path: str) -> Optional[float]:
        """Obtener duración desde cache si está disponible y válida"""
        try:
            path_str = str(file_path)
            if path_str in self.duration_cache:
                entry = self.duration_cache[path_str]
                
                # Verificar que el archivo no haya cambiado
                file_stat = Path(file_path).stat()
                if (entry['file_size'] == file_stat.st_size and 
                    entry['modified_time'] == file_stat.st_mtime):
                    return entry['duration']
            
        except Exception as e:
            self.logger.debug(f"Error verificando cache para {file_path}: {e}")
        
        return None
    
    def _cache_duration(self, file_path: str, duration: Optional[float]) -> None:
        """Cachear duración de un archivo"""
        try:
            path_str = str(file_path)
            file_stat = Path(file_path).stat()
            
            self.duration_cache[path_str] = {
                'duration': duration,
                'file_size': file_stat.st_size,
                'modified_time': file_stat.st_mtime,
                'cached_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.debug(f"Error cacheando duración para {file_path}: {e}")

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