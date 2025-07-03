"""
Tag-Flow V2 - Video Analyzer Optimizado
VideoAnalyzer con optimizaciones de BD manteniendo compatibilidad total
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
import time

# Agregar el directorio src al path para imports
sys.path.append(str(Path(__file__).parent))

from database import db
from optimized_database import OptimizedDatabaseManager
from pattern_cache import get_global_cache
import external_sources

logger = logging.getLogger(__name__)

class OptimizedVideoAnalyzer:
    """VideoAnalyzer con optimizaciones de BD manteniendo interfaz idéntica"""
    
    def __init__(self):
        # Intentar usar optimizaciones
        try:
            self.optimized_db = OptimizedDatabaseManager()
            self.use_optimizations = True
            self.cache = get_global_cache()
            logger.info("🚀 VideoAnalyzer OPTIMIZADO inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando optimizaciones, usando estándar: {e}")
            self.use_optimizations = False
            self.optimized_db = None
        
        # Mantener configuración original
        from config import config
        config.ensure_directories()
        
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        
        logger.debug(f"Optimizaciones: {'ACTIVAS' if self.use_optimizations else 'INACTIVAS'}")
    
    def find_new_videos(self, platform_filter=None, source_filter='all') -> List[Dict]:
        """🚀 OPTIMIZADO: Versión mejorada manteniendo interfaz idéntica"""
        
        if not self.use_optimizations:
            # Fallback a método original (importar VideoAnalyzer original)
            logger.debug("Usando find_new_videos estándar (fallback)")
            return self._find_new_videos_fallback(platform_filter, source_filter)
        
        logger.info(f"🔍 Buscando videos nuevos OPTIMIZADO (source: {source_filter}, platform: {platform_filter or 'todas'})...")
        
        start_time = time.time()
        
        try:
            # ✅ OPTIMIZACIÓN 1: Cache de paths existentes
            existing_paths = self.cache.get_existing_paths(self.optimized_db)
            paths_time = time.time() - start_time
            logger.debug(f"📊 Paths existentes obtenidos en {paths_time:.3f}s (cache: {len(existing_paths)} paths)")
            
            # ✅ OPTIMIZACIÓN 2: Obtener videos externos (sin cambios para compatibilidad)
            external_videos = external_sources.get_all_videos_from_source(source_filter, self._map_platform_to_internal(platform_filter))
            external_time = time.time() - start_time - paths_time
            logger.debug(f"📊 Videos externos obtenidos en {external_time:.3f}s ({len(external_videos)} videos)")
            
            # ✅ OPTIMIZACIÓN 3: Filtrado O(1) con set lookup
            new_videos = []
            for video_data in external_videos:
                video_path = Path(video_data['file_path'])
                
                # Verificación de duplicados ultra-rápida O(1)
                if str(video_path) not in existing_paths:
                    # Verificación adicional por nombre (también O(1) con set)
                    path_names = {Path(p).name for p in existing_paths}
                    if video_path.name not in path_names:
                        # Verificación de existencia del archivo
                        if video_path.exists() and video_data.get('content_type', 'video') == 'video':
                            new_videos.append(video_data)
            
            filter_time = time.time() - start_time - paths_time - external_time
            total_time = time.time() - start_time
            
            logger.info(f"✅ Videos nuevos encontrados OPTIMIZADO: {len(new_videos)}")
            logger.debug(f"📊 Timing: paths={paths_time:.3f}s, external={external_time:.3f}s, filter={filter_time:.3f}s, total={total_time:.3f}s")
            
            return new_videos
            
        except Exception as e:
            logger.warning(f"⚠️ Error en find_new_videos optimizado, fallback: {e}")
            self.use_optimizations = False
            return self._find_new_videos_fallback(platform_filter, source_filter)
    
    def get_pending_videos(self, platform_filter=None, source_filter='all', limit=None) -> List[Dict]:
        """🚀 OPTIMIZADO: Con cache y consultas eficientes manteniendo interfaz"""
        
        if not self.use_optimizations:
            logger.debug("Usando get_pending_videos estándar (fallback)")
            return self._get_pending_videos_fallback(platform_filter, source_filter, limit)
        
        logger.info(f"🔍 Buscando videos pendientes OPTIMIZADO (source: {source_filter}, platform: {platform_filter or 'todas'})...")
        
        start_time = time.time()
        
        try:
            # ✅ Crear clave de cache basada en parámetros
            cache_key = f"pending_{platform_filter}_{source_filter}_{limit}"
            
            # ✅ Mapear plataforma para filtros especiales
            mapped_platform = self._map_platform_filter(platform_filter)
            
            # ✅ Obtener desde cache con fallback a consulta optimizada
            pending_videos_db = self.cache.get_pending_videos_cached(
                cache_key, self.optimized_db, mapped_platform, source_filter, limit
            )
            
            query_time = time.time() - start_time
            logger.debug(f"📊 Consulta pendientes en {query_time:.3f}s ({len(pending_videos_db)} videos)")
            
            # ✅ FILTRADO POR SOURCE: Manteniendo lógica original para compatibilidad
            if source_filter != 'all':
                pending_videos_db = self._filter_by_source(pending_videos_db, source_filter)
            
            # ✅ Convertir a formato compatible (manteniendo lógica original)
            pending_videos = self._convert_pending_to_video_data(pending_videos_db)
            
            total_time = time.time() - start_time
            logger.info(f"✅ Videos pendientes OPTIMIZADO: {len(pending_videos)} válidos")
            logger.debug(f"📊 Tiempo total: {total_time:.3f}s")
            
            return pending_videos
            
        except Exception as e:
            logger.warning(f"⚠️ Error en get_pending_videos optimizado, fallback: {e}")
            self.use_optimizations = False
            return self._get_pending_videos_fallback(platform_filter, source_filter, limit)
    
    def process_video(self, video_data: Dict) -> Dict:
        """🚀 OPTIMIZADO: Con consultas combinadas manteniendo funcionalidad completa"""
        
        if not self.use_optimizations:
            logger.debug("Usando process_video estándar (fallback)")
            return self._process_video_fallback(video_data)
        
        video_path = Path(video_data['file_path'])
        logger.info(f"Procesando OPTIMIZADO: {video_path.name}")
        
        start_time = time.time()
        result = {
            'success': False,
            'video_id': None,
            'error': None,
            'processing_time': 0
        }
        
        try:
            # ✅ OPTIMIZACIÓN 1: Búsqueda combinada por path/name
            existing_video = None
            video_id = None
            
            if 'existing_video_id' in video_data:
                video_id = video_data['existing_video_id']
                logger.debug(f"📊 Video pendiente (ID: {video_id})")
            else:
                # Búsqueda optimizada por path/name en una consulta
                existing_video = self.optimized_db.get_video_by_path_or_name(
                    str(video_path), 
                    video_path.name
                )
                
                if existing_video:
                    video_id = existing_video['id']
                    logger.debug(f"📊 Video existente encontrado OPTIMIZADO (ID: {video_id})")
            
            # ✅ El resto del procesamiento permanece IDÉNTICO para compatibilidad
            # (Importar y usar los módulos originales para mantener funcionalidad)
            result = self._process_video_core(video_data, video_path, video_id, existing_video)
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Error en process_video optimizado, fallback: {e}")
            self.use_optimizations = False
            return self._process_video_fallback(video_data)
    
    # ✅ MÉTODOS DE SOPORTE PARA MANTENER COMPATIBILIDAD
    
    def _map_platform_to_internal(self, platform_filter: str) -> Optional[str]:
        """Mapear nombres de plataforma modernos a códigos legacy internos"""
        if not platform_filter:
            return None
            
        platform_map = {
            'youtube': 'YT',
            'tiktok': 'TT', 
            'instagram': 'IG',
            'other': 'OTHER',
            'all-platforms': 'ALL'
        }
        
        # Obtener plataformas adicionales disponibles
        try:
            available_platforms = external_sources.get_available_platforms()
            for platform_key in available_platforms['additional'].keys():
                platform_map[platform_key] = platform_key.upper()
        except Exception as e:
            logger.debug(f"Error obteniendo plataformas adicionales: {e}")
        
        return platform_map.get(platform_filter, platform_filter.upper())
    
    def _map_platform_filter(self, platform_filter: str) -> str:
        """Mapear filtro de plataforma para consultas optimizadas"""
        if not platform_filter:
            return 'all-platforms'
            
        if platform_filter == 'other':
            return 'other'
        elif platform_filter == 'all-platforms':
            return 'all-platforms'
        else:
            return platform_filter
    
    def _filter_by_source(self, videos: List[Dict], source_filter: str) -> List[Dict]:
        """Filtrar videos por source manteniendo lógica original"""
        if source_filter == 'all':
            return videos
            
        from config import config
        filtered_videos = []
        
        for video in videos:
            video_path = Path(video['file_path'])
            should_include = False
            
            if source_filter == 'db':
                # Solo videos que provienen de bases de datos externas
                if (config.EXTERNAL_YOUTUBE_DB and 'youtube' in video['platform'].lower()) or \
                   (config.EXTERNAL_TIKTOK_DB and 'tiktok' in video['platform'].lower()) or \
                   (config.EXTERNAL_INSTAGRAM_DB and 'instagram' in video['platform'].lower()):
                    should_include = True
                    
            elif source_filter == 'organized':
                # Solo videos que provienen de carpetas organizadas
                if config.ORGANIZED_BASE_PATH and str(video_path).startswith(str(config.ORGANIZED_BASE_PATH)):
                    should_include = True
            
            if should_include:
                filtered_videos.append(video)
        
        return filtered_videos
    
    def _convert_pending_to_video_data(self, pending_videos_db: List[Dict]) -> List[Dict]:
        """Convertir videos pendientes a formato compatible"""
        pending_videos = []
        
        for video in pending_videos_db:
            # Usar file_name como título, limpiando numeración inicial
            raw_title = video['file_name']
            title = Path(raw_title).stem
            
            # Limpiar numeración inicial (ej: "501. " -> "")
            if '. ' in title:
                title = title.split('. ', 1)[1]
            
            video_data = {
                'file_path': video['file_path'],
                'file_name': video['file_name'],
                'creator_name': video['creator_name'],
                'platform': video['platform'],
                'title': title,
                'content_type': 'video',
                'existing_video_id': video['id'],
                'source_type': 'pending'
            }
            
            # Verificar que el archivo aún existe
            if Path(video['file_path']).exists():
                pending_videos.append(video_data)
            else:
                logger.warning(f"Archivo no encontrado: {video['file_path']}")
        
        return pending_videos
    
    def _process_video_core(self, video_data: Dict, video_path: Path, video_id: Optional[int], existing_video: Optional[Dict]) -> Dict:
        """Procesamiento core del video manteniendo funcionalidad original"""
        # Importar módulos necesarios con imports absolutos
        try:
            # Asegurar que el path esté correcto
            import sys
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.append(str(project_root))
            
            # Imports absolutos como en main.py
            from src.video_processor import video_processor
            from src.music_recognition import music_recognizer  
            from src.face_recognition import face_recognizer
            
        except ImportError as e:
            logger.warning(f"Error importando módulos core: {e}")
            # Fallback: usar proceso original completo
            return self._process_video_fallback(video_data)
        
        result = {
            'success': False,
            'video_id': video_id,
            'error': None,
            'processing_time': 0
        }
        
        start_time = time.time()
        
        # 1. Extraer metadatos básicos
        logger.info(f"  Extrayendo metadatos...")
        metadata = video_processor.extract_metadata(video_path)
        if 'error' in metadata:
            result['error'] = f"Error en metadatos: {metadata['error']}"
            return result
        
        # Enriquecer metadatos
        if 'title' in video_data and video_data['title']:
            metadata['description'] = video_data['title']
        if 'creator_name' in video_data:
            metadata['creator_name'] = video_data['creator_name']
        if 'platform' in video_data:
            metadata['platform'] = video_data['platform']
        
        # Crear nuevo video si no existe
        if not existing_video and not video_id:
            metadata.update({
                'creator_name': video_data.get('creator_name', 'Desconocido'),
                'platform': video_data.get('platform', 'tiktok'),
                'file_name': video_data.get('file_name', video_path.name),
                'file_path': video_data.get('file_path', str(video_path)),
                'processing_status': 'procesando'
            })
            
            if 'title' in video_data:
                metadata['title'] = video_data['title']
                
            logger.info(f"  Creando nuevo video: plataforma={metadata['platform']}, creador={metadata['creator_name']}")
            video_id = self.optimized_db.add_video(metadata)
        
        result['video_id'] = video_id
        
        # 2. Reconocimiento musical (sin cambios)
        music_result = {'detected_music': None, 'detected_music_artist': None, 'detected_music_confidence': 0.0, 'music_source': None}
        
        if metadata.get('has_audio', False):
            logger.info(f"  Analizando música...")
            try:
                audio_path = video_processor.extract_audio(video_path, duration=30)
                if audio_path:
                    filename = video_path.name if hasattr(video_path, 'name') else str(video_path).split('\\')[-1]
                    music_result = music_recognizer.recognize_music(audio_path, filename)
                    if audio_path.exists():
                        audio_path.unlink()
            except Exception as e:
                logger.warning(f"  Error en reconocimiento musical: {e}")
        
        # 3. Reconocimiento facial (sin cambios)
        faces_result = {'detected_characters': [], 'recognition_sources': []}
        
        logger.info(f"  Analizando personajes con IA mejorada...")
        try:
            frame_data = video_processor.get_video_frame(video_path, timestamp=2.0)
            if frame_data:
                video_data_for_recognition = {
                    'creator_name': video_data.get('creator_name', ''),
                    'platform': video_data.get('platform', 'unknown')
                }
                
                if video_id and 'existing_video_id' in video_data:
                    existing_video = self.optimized_db.get_video(video_id)
                    video_data_for_recognition['title'] = existing_video.get('description', '') or video_data.get('title', '')
                else:
                    video_data_for_recognition['title'] = video_data.get('title', '')
                
                faces_result = face_recognizer.recognize_faces_intelligent(frame_data, video_data_for_recognition)
                
                if faces_result.get('detected_characters'):
                    logger.info(f"  ✅ Personajes detectados: {', '.join(faces_result['detected_characters'])}")
                    logger.info(f"  📊 Fuentes: {', '.join(faces_result.get('recognition_sources', []))}")
                else:
                    logger.info(f"  ℹ️ No se detectaron personajes conocidos")
                    
        except Exception as e:
            logger.warning(f"  Error en reconocimiento de personajes: {e}")
        
        # 4. Actualizar BD con resultados
        updates = {
            'detected_music': music_result.get('detected_music'),
            'detected_music_artist': music_result.get('detected_music_artist'),
            'detected_music_confidence': music_result.get('detected_music_confidence'),
            'music_source': music_result.get('music_source'),
            'final_music': music_result.get('final_music'),
            'final_music_artist': music_result.get('final_music_artist'),
            'detected_characters': faces_result.get('detected_characters', []),
            'processing_status': 'completado'
        }
        
        self.optimized_db.update_video(video_id, updates)
        
        result['success'] = True
        processing_time = time.time() - start_time
        result['processing_time'] = processing_time
        
        logger.info(f"  ✓ Completado OPTIMIZADO en {processing_time:.1f}s - Música: {music_result.get('final_music') or music_result.get('detected_music', 'N/A')} - Caras: {len(faces_result.get('detected_characters', []))}")
        
        return result
    
    def run(self, limit=None, platform=None, source='all'):
        """Ejecutar el análisis completo con optimizaciones
        
        Args:
            limit (int, optional): Número máximo de videos a procesar
            platform (str, optional): Plataforma específica a procesar
            source (str, optional): Fuente de datos ('db', 'organized', 'all')
        """
        logger.info("=== INICIANDO TAG-FLOW V2 ANALYSIS (OPTIMIZADO) ===")
        
        if limit:
            logger.info(f"MODO LIMITADO: Procesando máximo {limit} videos")
        
        if platform:
            platform_names = {
                'youtube': 'YouTube (4K Video Downloader+)', 
                'tiktok': 'TikTok (4K Tokkit)', 
                'instagram': 'Instagram (4K Stogram)', 
                'other': 'Solo Plataformas Adicionales',
                'all-platforms': 'Todas las Plataformas'
            }
            
            # Agregar plataformas adicionales disponibles
            try:
                available_platforms = external_sources.get_available_platforms()
                for platform_key, platform_info in available_platforms['additional'].items():
                    platform_names[platform_key] = f"{platform_info['folder_name']} (D:\\4K All\\{platform_info['folder_name']})"
            except Exception as e:
                logger.debug(f"Error obteniendo plataformas adicionales: {e}")
            
            logger.info(f"PLATAFORMA ESPECÍFICA: {platform_names.get(platform, platform)}")
        
        if source != 'all':
            source_names = {
                'db': 'Solo Bases de Datos Externas (4K Apps)',
                'organized': 'Solo Carpetas Organizadas (D:\\4K All)',
                'all': 'Todas las Fuentes'
            }
            logger.info(f"FUENTE ESPECÍFICA: {source_names.get(source, source)}")
        
        try:
            # 1. Buscar videos pendientes con límite optimizado
            videos_to_process = []
            
            # 1a. Obtener videos pendientes que correspondan al source seleccionado
            pending_videos = self.get_pending_videos(
                platform_filter=platform, 
                source_filter=source, 
                limit=limit
            )
            videos_to_process.extend(pending_videos)
            
            # 1b. Calcular límite restante para videos nuevos
            remaining_limit = None
            if limit:
                remaining_limit = limit - len(videos_to_process)
                if remaining_limit <= 0:
                    logger.info(f"✅ Límite alcanzado con videos pendientes: {len(videos_to_process)}")
                    logger.info(f"⏭️ No se buscarán videos nuevos adicionales")
                else:
                    logger.info(f"🔍 Buscando hasta {remaining_limit} videos nuevos para completar límite...")
            else:
                logger.info(f"📋 Videos pendientes encontrados: {len(videos_to_process)}")
                logger.info(f"🔍 Buscando videos nuevos adicionales (sin límite)...")
            
            # Solo buscar videos nuevos si no hemos alcanzado el límite
            if not limit or remaining_limit > 0:
                new_videos = self.find_new_videos(platform_filter=platform, source_filter=source)
                
                # Aplicar límite restante a videos nuevos
                if remaining_limit and len(new_videos) > remaining_limit:
                    logger.info(f"📊 Videos nuevos encontrados: {len(new_videos)}")
                    logger.info(f"⚡ Aplicando límite restante: {len(new_videos)} -> {remaining_limit} seleccionados")
                    new_videos = new_videos[:remaining_limit]
                elif new_videos:
                    logger.info(f"📊 Videos nuevos encontrados: {len(new_videos)} (todos serán procesados)")
                else:
                    logger.info(f"📊 No se encontraron videos nuevos para procesar")
                
                # Marcar videos nuevos para debug
                for video in new_videos:
                    video['source_type'] = 'new'
                
                videos_to_process.extend(new_videos)
            else:
                logger.info(f"⏭️ Saltando búsqueda de videos nuevos (límite ya alcanzado)")
            
            if not videos_to_process:
                logger.info("❌ No hay videos para procesar")
                logger.info(f"💡 Sugerencia: Verificar source '{source}' y platform '{platform or 'todas'}'")
                return
            
            # Estadísticas finales antes del procesamiento
            pending_count = sum(1 for v in videos_to_process if v.get('source_type') == 'pending')
            new_count = sum(1 for v in videos_to_process if v.get('source_type') == 'new')
            
            logger.info(f"📋 RESUMEN OPTIMIZADO:")
            logger.info(f"  📁 Videos pendientes: {pending_count}")
            logger.info(f"  🆕 Videos nuevos: {new_count}")
            logger.info(f"  📊 Total a procesar: {len(videos_to_process)}")
            if limit:
                logger.info(f"  ✅ Límite respetado: {len(videos_to_process)}/{limit}")
            logger.info("=" * 60)
            
            # 2. Procesar videos en lotes con optimizaciones
            batch_results = self.process_videos_batch(videos_to_process)
            
            # 3. Mostrar estadísticas finales
            if hasattr(db, 'get_stats'):
                stats = db.get_stats()
                logger.info("=== ESTADÍSTICAS FINALES ===")
                logger.info(f"Total videos en BD: {stats['total_videos']}")
                logger.info(f"Videos con música: {stats['with_music']}")
                logger.info(f"Videos con personajes: {stats['with_characters']}")
                
                # Por estado
                for status, count in stats['by_status'].items():
                    logger.info(f"Estado '{status}': {count}")
                
                # Por plataforma si es relevante
                if stats['by_platform']:
                    logger.info("Por plataforma:")
                    for platform_name, count in stats['by_platform'].items():
                        logger.info(f"  {platform_name}: {count}")
            
            # 4. Log de performance si las optimizaciones están activas
            if self.use_optimizations:
                self.log_performance_summary()
                
        except Exception as e:
            logger.error(f"Error en ejecución principal optimizada: {e}")
            # Si hay error en optimizaciones, intentar fallback
            if self.use_optimizations:
                logger.warning("⚠️ Intentando fallback a VideoAnalyzer estándar...")
                self.use_optimizations = False
                # Aquí se podría implementar un fallback al VideoAnalyzer original
            raise

    def process_videos_batch(self, video_data_list: List[Dict]) -> Dict:
        """Procesar múltiples videos con threading optimizado"""
        logger.info(f"Procesando {len(video_data_list)} videos con optimizaciones...")
        
        results = {
            'total': len(video_data_list),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'processing_time': 0
        }
        
        start_time = time.time()
        
        # Procesar con threading (mantener lógica original)
        from config import config
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        max_workers = min(config.MAX_CONCURRENT_PROCESSING, len(video_data_list))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todos los trabajos
            future_to_video = {
                executor.submit(self.process_video, video_data): video_data 
                for video_data in video_data_list
            }
            
            # Recopilar resultados
            for future in as_completed(future_to_video):
                video_data = future_to_video[future]
                video_path = Path(video_data['file_path'])
                try:
                    result = future.result()
                    if result['success']:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'video': str(video_path),
                            'error': result['error']
                        })
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'video': str(video_path),
                        'error': f"Error inesperado: {e}"
                    })
        
        results['processing_time'] = time.time() - start_time
        
        logger.info(f"Procesamiento optimizado completado:")
        logger.info(f"  ✓ Exitosos: {results['successful']}")
        logger.info(f"  ✗ Fallidos: {results['failed']}")
        logger.info(f"  ⏱ Tiempo total: {results['processing_time']:.1f}s")
        
    # ✅ MÉTODOS DE FALLBACK PARA MÁXIMA COMPATIBILIDAD
    
    def _find_new_videos_fallback(self, platform_filter, source_filter):
        """Fallback al método original de VideoAnalyzer"""
        logger.debug("Ejecutando find_new_videos en modo fallback")
        try:
            # Importar VideoAnalyzer original y usar su lógica
            from main import VideoAnalyzer
            analyzer = VideoAnalyzer()
            return analyzer.find_new_videos(platform_filter, source_filter)
        except Exception as e:
            logger.error(f"Error en fallback find_new_videos: {e}")
            return []
    
    def _get_pending_videos_fallback(self, platform_filter, source_filter, limit):
        """Fallback al método original de VideoAnalyzer"""
        logger.debug("Ejecutando get_pending_videos en modo fallback")
        try:
            from main import VideoAnalyzer
            analyzer = VideoAnalyzer()
            return analyzer.get_pending_videos(platform_filter, source_filter, limit)
        except Exception as e:
            logger.error(f"Error en fallback get_pending_videos: {e}")
            return []
    
    def _process_video_fallback(self, video_data):
        """Fallback al método original de VideoAnalyzer"""
        logger.debug("Ejecutando process_video en modo fallback")
        try:
            from main import VideoAnalyzer
            analyzer = VideoAnalyzer()
            return analyzer.process_video(video_data)
        except Exception as e:
            logger.error(f"Error en fallback process_video: {e}")
            return {'success': False, 'error': f'Fallback error: {e}'}
    
    # ✅ MÉTODOS DE MONITOREO Y MÉTRICAS
    
    def get_performance_report(self) -> Dict:
        """Obtener reporte de performance de las optimizaciones"""
        if not self.use_optimizations:
            return {'status': 'OPTIMIZATIONS_DISABLED'}
        
        return self.optimized_db.get_performance_report()
    
    def clear_detection_cache(self):
        """Limpiar cache para forzar actualización"""
        if self.use_optimizations:
            self.cache.clear_detection_cache()
            logger.info("🔄 Cache de detección limpiado")
        else:
            logger.info("ℹ️ Optimizaciones no activas, no hay cache que limpiar")
    
    def log_performance_summary(self):
        """Log resumen de performance optimizada"""
        if self.use_optimizations:
            self.optimized_db.log_performance_summary()
        else:
            logger.info("📊 Optimizaciones no activas")
    
    # ✅ MÉTODOS DE MONITOREO Y MÉTRICAS
    
    def get_performance_report(self) -> Dict:
        """Obtener reporte de performance de las optimizaciones"""
        if not self.use_optimizations:
            return {'status': 'OPTIMIZATIONS_DISABLED'}
        
        return self.optimized_db.get_performance_report()
    
    def clear_detection_cache(self):
        """Limpiar cache para forzar actualización"""
        if self.use_optimizations:
            self.cache.clear_detection_cache()
            logger.info("🔄 Cache de detección limpiado")
        else:
            logger.info("ℹ️ Optimizaciones no activas, no hay cache que limpiar")
    
    def log_performance_summary(self):
        """Log resumen de performance optimizada"""
        if self.use_optimizations:
            self.optimized_db.log_performance_summary()
        else:
            logger.info("📊 Optimizaciones no activas")
