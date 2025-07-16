"""
Tag-Flow V2 - Script Principal de Procesamiento
Motor que analiza videos nuevos y alimenta la base de datos
"""

import os
# Ocultar logs de TensorFlow y Keras antes de cualquier import relacionado
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import sys
import logging
from pathlib import Path
from typing import List, Dict
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import os
import argparse

# Agregar el directorio src al path para imports
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config
from src.database import db
from src.video_processor import video_processor
from src.music_recognition import music_recognizer
from src.face_recognition import face_recognizer
from src.thumbnail_generator import thumbnail_generator
from src.downloader_integration import downloader_integration
from src.external_sources import external_sources

# Configurar logging
file_handler = logging.FileHandler('tag_flow_processing.log', encoding='utf-8')
stream_handler = logging.StreamHandler()
try:
    # Python 3.9+ permite encoding en StreamHandler
    stream_handler = logging.StreamHandler()
    stream_handler.setStream(open(1, 'w', encoding='utf-8', closefd=False))
except Exception:
    # Fallback para versiones antiguas
    pass
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        file_handler,
        stream_handler
    ]
)
logger = logging.getLogger(__name__)

class VideoAnalyzer:
    """Analizador principal de videos TikTok/MMD"""
    
    def __init__(self):
        # Asegurar que los directorios existen
        config.ensure_directories()
        
        # 🆕 LIMPIEZA: Sistema moderno usa únicamente fuentes externas configuradas en .env
        # Eliminado: self.scan_paths (legacy) - Todo viene de variables de entorno
        
        # Extensiones de video soportadas
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        
        logger.info("VideoAnalyzer inicializado")
        
        # Validar configuración
        warnings = config.validate_config()
        if warnings:
            logger.warning("Advertencias de configuración:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
    
    def find_new_videos(self, platform_filter=None, source_filter='all') -> List[Dict]:
        """
        Encontrar videos que no están en la base de datos
        
        Args:
            platform_filter: 'youtube', 'tiktok', 'instagram', 'other', 'all-platforms' o None para todas
            source_filter: 'db', 'organized', 'all' - determina las fuentes a usar
            
        Returns:
            List[Dict]: Lista de diccionarios con información completa del video
        """
        logger.info(f"🔍 Buscando videos nuevos (source: {source_filter}, platform: {platform_filter or 'todas'})...")
        
        # Obtener videos ya procesados de la BD
        existing_videos = set()
        try:
            videos_in_db = db.get_videos()
            existing_videos = {video['file_path'] for video in videos_in_db}
            logger.info(f"📊 Videos ya en BD: {len(existing_videos)}")
        except Exception as e:
            logger.error(f"❌ Error consultando BD: {e}")
        
        new_videos = []
        
        # Determinar qué fuentes usar basado en source_filter
        use_external_sources = source_filter in ['db', 'all']
        use_organized_folders = source_filter in ['organized', 'all']
        
        # 🆕 MEJORADO: Logging detallado de fuentes seleccionadas
        logger.info(f"📂 Fuentes seleccionadas por --source '{source_filter}':")
        if use_external_sources:
            logger.info(f"  ✅ Bases de datos externas (4K Apps)")
        if use_organized_folders:
            logger.info(f"  ✅ Carpetas organizadas (D:\\4K All)")
        
        if use_external_sources:
            # Usar fuentes externas (bases de datos y carpetas organizadas)
            logger.info("📁 Consultando fuentes externas para videos nuevos...")
            
            # Mapear nombres de plataforma modernos a códigos legacy internos
            platform_map = {
                'youtube': 'YT',
                'tiktok': 'TT', 
                'instagram': 'IG',
                'other': 'OTHER',  # Solo plataformas adicionales
                'all-platforms': 'ALL'  # Todas las plataformas
            }
            
            # Obtener plataformas adicionales disponibles
            available_platforms = external_sources.get_available_platforms()
            
            # Agregar plataformas adicionales al mapa (nombre -> nombre)
            for platform_key in available_platforms['additional'].keys():
                platform_map[platform_key] = platform_key.upper()
            
            # Convertir nombre moderno a código interno
            internal_platform_code = None
            if platform_filter:
                internal_platform_code = platform_map.get(platform_filter)
                if not internal_platform_code:
                    # Si no está en el mapa, asumir que es una plataforma adicional
                    internal_platform_code = platform_filter.upper()
            
            # Determinar source para external_sources basado en source_filter
            if source_filter == 'db':
                external_source = 'db'  # Solo bases de datos externas
            elif source_filter == 'organized':
                external_source = 'organized'  # Solo carpetas organizadas
            else:  # 'all'
                external_source = 'all'  # Ambas fuentes
            
            # Obtener videos de fuentes externas
            external_videos = external_sources.get_all_videos_from_source(external_source, internal_platform_code)
            
            # Filtrar nuevos y verificar existencia
            for video_data in external_videos:
                video_path = Path(video_data['file_path'])
                
                # Verificar duplicados con múltiples estrategias
                is_duplicate = False
                
                # Estrategia 1: Ruta exacta
                if str(video_path) in existing_videos:
                    is_duplicate = True
                
                # Estrategia 2: Nombre de archivo (para rutas normalizadas)
                if not is_duplicate:
                    for existing_path in existing_videos:
                        if Path(existing_path).name == video_path.name:
                            is_duplicate = True
                            break
                
                # Si no es duplicado y existe el archivo físico
                if not is_duplicate and video_path.exists():
                    # Solo videos, no imágenes para el procesamiento principal
                    if video_data.get('content_type', 'video') == 'video':
                        new_videos.append(video_data)  # Retornar datos completos
        
        # 🆕 MEJORADO: Logging detallado del resultado
        logger.info(f"✅ Videos nuevos encontrados: {len(new_videos)}")
        if platform_filter:
            logger.info(f"   🎯 Filtrados por platform: {platform_filter}")
        if source_filter != 'all':
            logger.info(f"   📂 Filtrados por source: {source_filter}")
        
        return new_videos    
    def process_video(self, video_data: Dict) -> Dict:
        """Procesar un video individual completamente
        
        Args:
            video_data: Diccionario con información completa del video
        """
        video_path = Path(video_data['file_path'])
        logger.info(f"Procesando: {video_path.name}")
        
        start_time = time.time()
        result = {
            'success': False,
            'video_id': None,
            'error': None,
            'processing_time': 0
        }
        
        try:
            # 1. Extraer metadatos básicos
            logger.info(f"  Extrayendo metadatos...")
            metadata = video_processor.extract_metadata(video_path)
            if 'error' in metadata:
                result['error'] = f"Error en metadatos: {metadata['error']}"
                return result
            
            # Enriquecer metadatos con información de fuentes externas (TikTok, etc.)
            if 'title' in video_data and video_data['title']:
                metadata['description'] = video_data['title']  # Descripción del TikTok
            if 'creator_name' in video_data:
                metadata['creator_name'] = video_data['creator_name']
            if 'platform' in video_data:
                metadata['platform'] = video_data['platform']

            # Determinar si es un video existente (pendiente) o nuevo
            existing_video = None
            video_id = None
            
            # Caso 1: Video pendiente marcado explícitamente
            if 'existing_video_id' in video_data:
                video_id = video_data['existing_video_id']
                logger.info(f"  Procesando video pendiente (ID: {video_id})")
                
            else:
                # Caso 2: Buscar si el video ya existe en la BD
                # Estrategia 1: Ruta exacta
                existing_video = db.get_video_by_path(str(video_path))
                
                # Estrategia 2: Por nombre de archivo si no se encontró por ruta exacta
                if not existing_video:
                    videos_in_db = db.get_videos()
                    for db_video in videos_in_db:
                        if Path(db_video['file_path']).name == video_path.name:
                            existing_video = db_video
                            logger.info(f"  Video encontrado por nombre de archivo: {video_path.name}")
                            break
                
                if existing_video:
                    # Ya existe: usar los metadatos originales
                    video_id = existing_video['id']
                    logger.info(f"  Video ya existe en BD (ID: {video_id}), se conservarán los datos originales")
                else:
                    # Nuevo: usar información de external_sources y crear en BD
                    metadata.update({
                        'creator_name': video_data.get('creator_name', 'Desconocido'),
                        'platform': video_data.get('platform', 'tiktok'),
                        'file_name': video_data.get('file_name', video_path.name),
                        'file_path': video_data.get('file_path', str(video_path)),
                        'processing_status': 'procesando'
                    })
                    
                    # Agregar información adicional si está disponible
                    if 'title' in video_data:
                        metadata['title'] = video_data['title']
                        
                    logger.info(f"  Creando nuevo video: plataforma={metadata['platform']}, creador={metadata['creator_name']}")
                    video_id = db.add_video(metadata)
            
            result['video_id'] = video_id
            
            # 5. Reconocimiento musical (si hay audio)
            music_result = {'detected_music': None, 'detected_music_artist': None, 'detected_music_confidence': 0.0, 'music_source': None}
            
            if metadata.get('has_audio', False):
                logger.info(f"  Analizando música...")
                try:
                    # Extraer audio temporal
                    audio_path = video_processor.extract_audio(video_path, duration=30)
                    if audio_path:
                        # Pasar filename para extracción de música del nombre
                        filename = video_path.name if hasattr(video_path, 'name') else str(video_path).split('\\')[-1]
                        music_result = music_recognizer.recognize_music(audio_path, filename)
                        # Limpiar archivo temporal
                        if audio_path.exists():
                            audio_path.unlink()
                except Exception as e:
                    logger.warning(f"  Error en reconocimiento musical: {e}")
            
            # 6. Reconocimiento facial inteligente (combina visual + título + creador)
            faces_result = {'detected_characters': [], 'recognition_sources': []}
            
            logger.info(f"  Analizando personajes con IA mejorada...")
            try:
                frame_data = video_processor.get_video_frame(video_path, timestamp=2.0)
                if frame_data:
                    # Preparar datos del video para análisis inteligente
                    video_data_for_recognition = {
                        'creator_name': video_data.get('creator_name', ''),
                        'platform': video_data.get('platform', 'unknown')
                    }
                    
                    # Para videos pendientes, usar descripción de la BD; para nuevos, usar título de video_data
                    if video_id and 'existing_video_id' in video_data:
                        # Video pendiente: obtener descripción de la BD
                        existing_video = db.get_video(video_id)
                        video_data_for_recognition['title'] = existing_video.get('description', '') or video_data.get('title', '')
                    else:
                        # Video nuevo: usar título de fuente externa
                        video_data_for_recognition['title'] = video_data.get('title', '')
                    
                    # Usar reconocimiento inteligente que combina todas las estrategias
                    faces_result = face_recognizer.recognize_faces_intelligent(frame_data, video_data_for_recognition)
                    
                    if faces_result.get('detected_characters'):
                        logger.info(f"  ✅ Personajes detectados: {', '.join(faces_result['detected_characters'])}")
                        logger.info(f"  📊 Fuentes: {', '.join(faces_result.get('recognition_sources', []))}")
                    else:
                        logger.info(f"  ℹ️ No se detectaron personajes conocidos")
                        
            except Exception as e:
                logger.warning(f"  Error en reconocimiento de personajes: {e}")
            
            # 7. Actualizar base de datos con resultados
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
            
            db.update_video(video_id, updates)
            
            result['success'] = True
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            
            logger.info(f"  ✓ Completado en {processing_time:.1f}s - Música: {music_result.get('final_music') or music_result.get('detected_music', 'N/A')} - Caras: {len(faces_result.get('detected_characters', []))}")
            
        except Exception as e:
            logger.error(f"  ✗ Error procesando {video_path.name}: {e}")
            result['error'] = str(e)
            
            # Marcar como error en BD si se creó el registro
            if result['video_id']:
                db.update_video(result['video_id'], {
                    'processing_status': 'error',
                    'error_message': str(e)
                })
        
        return result
    
    # 🆕 LIMPIEZA: Eliminada función _infer_creator_name (legacy)
    # El sistema moderno obtiene creadores directamente de las BD externas
    
    def process_videos_batch(self, video_data_list: List[Dict]) -> Dict:
        """Procesar múltiples videos con threading
        
        Args:
            video_data_list: Lista de diccionarios con información completa de videos
        """
        logger.info(f"Procesando {len(video_data_list)} videos...")
        
        results = {
            'total': len(video_data_list),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'processing_time': 0
        }
        
        start_time = time.time()
        
        # Procesar con threading
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
        
        logger.info(f"Procesamiento completado:")
        logger.info(f"  ✓ Exitosos: {results['successful']}")
        logger.info(f"  ✗ Fallidos: {results['failed']}")
        logger.info(f"  ⏱ Tiempo total: {results['processing_time']:.1f}s")
        
        return results
    
    def get_pending_videos(self, platform_filter=None, source_filter='all', limit=None) -> List[Dict]:
        """
        Obtener videos pendientes de la base de datos para procesamiento
        
        Args:
            platform_filter: 'youtube', 'tiktok', 'instagram', 'other', 'all-platforms' o None para todas las plataformas
            source_filter: 'db', 'organized', 'all' - determina las fuentes a considerar
            limit: número máximo de videos a retornar
            
        Returns:
            List[Dict]: Lista de diccionarios con información completa del video
        """
        logger.info(f"Buscando videos pendientes en la base de datos (source: {source_filter})...")
        
        # Obtener plataformas disponibles
        available_platforms = external_sources.get_available_platforms()
        
        # Construir filtros
        filters = {'processing_status': 'pendiente'}
        
        if platform_filter:
            # Manejar casos especiales
            if platform_filter == 'other':
                # Solo plataformas adicionales - filtrar por todas las adicionales
                additional_platforms = list(available_platforms['additional'].keys())
                if additional_platforms:
                    filters['platform'] = additional_platforms  # Lista de plataformas
                else:
                    # Si no hay plataformas adicionales, no devolver nada
                    return []
            elif platform_filter == 'all-platforms':
                # Todas las plataformas - no agregar filtro de plataforma
                pass
            elif platform_filter in ['youtube', 'tiktok', 'instagram']:
                # Plataformas principales específicas
                filters['platform'] = platform_filter
            elif platform_filter in available_platforms['additional']:
                # Plataforma adicional específica
                filters['platform'] = platform_filter
            else:
                # Plataforma no reconocida
                logger.warning(f"Plataforma no reconocida: {platform_filter}")
                return []
        
        # Obtener videos pendientes de la BD
        pending_videos_db = db.get_videos(filters, limit=limit)
        
        logger.info(f"Videos pendientes encontrados (antes de filtrar por source): {len(pending_videos_db)}")
        
        # 🆕 FILTRAR POR SOURCE: Solo videos que correspondan al source seleccionado
        if source_filter != 'all':
            filtered_videos_db = []
            
            for video in pending_videos_db:
                video_path = Path(video['file_path'])
                should_include = False
                
                if source_filter == 'db':
                    # Solo videos que provienen de bases de datos externas
                    # Verificar si el video está en alguna ruta de BD externa
                    if (config.EXTERNAL_YOUTUBE_DB and 'youtube' in video['platform'].lower()) or \
                       (config.EXTERNAL_TIKTOK_DB and 'tiktok' in video['platform'].lower()) or \
                       (config.EXTERNAL_INSTAGRAM_DB and 'instagram' in video['platform'].lower()):
                        should_include = True
                        
                elif source_filter == 'organized':
                    # Solo videos que provienen de carpetas organizadas
                    # Verificar si el video está en la ruta base de carpetas organizadas
                    if config.ORGANIZED_BASE_PATH and str(video_path).startswith(str(config.ORGANIZED_BASE_PATH)):
                        should_include = True
                
                if should_include:
                    filtered_videos_db.append(video)
            
            logger.info(f"Videos pendientes filtrados por source '{source_filter}': {len(filtered_videos_db)}")
            pending_videos_db = filtered_videos_db
        
        # Convertir a formato compatible con process_video
        pending_videos = []
        for video in pending_videos_db:
            # Usar file_name como título, limpiando numeración inicial
            raw_title = video['file_name']
            # Remover extensión
            title = Path(raw_title).stem
            # Limpiar numeración inicial (ej: "501. " -> "")
            if '. ' in title:
                title = title.split('. ', 1)[1]
            
            video_data = {
                'file_path': video['file_path'],
                'file_name': video['file_name'],
                'creator_name': video['creator_name'],
                'platform': video['platform'],
                'title': title,  # ✅ Título derivado de file_name
                'content_type': 'video',
                'existing_video_id': video['id'],  # Marcador para identificar que ya existe
                'source_type': 'pending'  # 🆕 Marcador para debug
            }
            
            # Verificar que el archivo aún existe
            if Path(video['file_path']).exists():
                pending_videos.append(video_data)
            else:
                logger.warning(f"Archivo no encontrado: {video['file_path']}")
        
        logger.info(f"Videos pendientes válidos finales: {len(pending_videos)}")
        return pending_videos

    def run(self, limit=None, platform=None, source='all'):
        """Ejecutar el análisis completo
        
        Args:
            limit (int, optional): Número máximo de videos a procesar. Si es None, procesa todos.
            platform (str, optional): Plataforma específica a procesar ('youtube', 'tiktok', 'instagram', 'other', 'all-platforms')
            source (str, optional): Fuente de datos ('db', 'organized', 'all')
        """
        logger.info("=== INICIANDO TAG-FLOW V2 ANALYSIS ===")
        
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
            available_platforms = external_sources.get_available_platforms()
            for platform_key, platform_info in available_platforms['additional'].items():
                platform_names[platform_key] = f"{platform_info['folder_name']} (D:\\4K All\\{platform_info['folder_name']})"
            
            logger.info(f"PLATAFORMA ESPECÍFICA: {platform_names.get(platform, platform)}")
        
        if source != 'all':
            source_names = {
                'db': 'Solo Bases de Datos Externas (4K Apps)',
                'organized': 'Solo Carpetas Organizadas (D:\\4K All)',
                'all': 'Todas las Fuentes'
            }
            logger.info(f"FUENTE ESPECÍFICA: {source_names.get(source, source)}")
        
        try:
            # 0. 🆕 MEJORADO: Importar desde 4K Downloader respetando límites y filtros
            imported_count = 0
            if downloader_integration.is_available:
                # Solo importar si source permite BD externas Y la plataforma es compatible
                should_import_4k = False
                
                if source in ['db', 'all']:
                    # 🔧 CORREGIDO: Solo importar de 4K Downloader si es YouTube o no hay filtro de plataforma
                    if platform is None or platform in ['youtube', 'all-platforms']:
                        should_import_4k = True
                        logger.info(f"🔄 4K Video Downloader compatible con plataforma: {platform or 'todas'}")
                    else:
                        should_import_4k = False
                        logger.info(f"⏭️ Saltando 4K Video Downloader (solo maneja YouTube, solicitado: {platform})")
                
                if should_import_4k:
                    # Determinar límite para importación
                    import_limit = None
                    if limit:
                        # Si hay límite global, usar para importación también
                        import_limit = limit
                        logger.info(f"🔄 Importando desde 4K Video Downloader con límite: {import_limit}")
                    else:
                        logger.info(f"🔄 Importando desde 4K Video Downloader sin límite")
                    
                    # Importar con límite respetado
                    import_result = downloader_integration.import_creators_and_videos(limit=import_limit)
                    if import_result['success']:
                        imported_count = import_result.get('imported_videos', 0)
                        logger.info(f"✅ Importados {imported_count} videos, {import_result['creators_found']} creadores")
                    else:
                        logger.warning(f"⚠️ Importación falló: {import_result.get('error', 'Error desconocido')}")
                else:
                    logger.info(f"ℹ️ 4K Video Downloader no aplica para esta configuración")
            else:
                logger.info(f"ℹ️ 4K Video Downloader no disponible")
            
            # 1. 🆕 MEJORADO: Buscar videos pendientes con límite ajustado
            videos_to_process = []
            
            # 1a. 🔧 CORREGIDO: Coordinación de límites - importar Y procesar dentro del límite
            remaining_limit_for_pending = limit
            if limit and imported_count > 0:
                # Si se importaron videos, SIEMPRE buscarlos como pendientes para procesarlos
                logger.info(f"📥 Importados {imported_count} videos que necesitan procesamiento")
                logger.info(f"📋 Buscando videos pendientes (incluidos recién importados) para procesar...")
                
                # El límite se aplica al TOTAL procesado, no solo importado
                remaining_limit_for_pending = limit
            
            # 1b. Obtener videos pendientes que correspondan al source seleccionado
            pending_videos = self.get_pending_videos(
                platform_filter=platform, 
                source_filter=source, 
                limit=remaining_limit_for_pending
            )
            videos_to_process.extend(pending_videos)
            
            # 1c. 🆕 COORDINACIÓN FINAL: Calcular límite restante total
            final_remaining_limit = None
            if limit:
                total_videos_so_far = imported_count + len(videos_to_process)
                final_remaining_limit = limit - total_videos_so_far
                
                if final_remaining_limit <= 0:
                    logger.info(f"✅ Límite alcanzado completamente:")
                    logger.info(f"  📥 Videos importados: {imported_count}")
                    logger.info(f"  📋 Videos pendientes: {len(videos_to_process)}")
                    logger.info(f"  📊 Total: {total_videos_so_far}/{limit}")
                    logger.info(f"⏭️ No se buscarán videos nuevos adicionales (límite ya alcanzado)")
                else:
                    logger.info(f"📋 Videos hasta ahora: {total_videos_so_far}")
                    logger.info(f"🔍 Buscando hasta {final_remaining_limit} videos nuevos para completar límite...")
            else:
                logger.info(f"📋 Videos encontrados hasta ahora: {imported_count + len(videos_to_process)}")
                logger.info(f"🔍 Buscando videos nuevos adicionales (sin límite)...")
            
            # Solo buscar videos nuevos si no hemos alcanzado el límite
            if not limit or final_remaining_limit > 0:
                # 🆕 MEJORADO: Usar fuentes según source filter con coordinación inteligente
                logger.info(f"🔍 Buscando videos nuevos (source: {source}, platform: {platform or 'todas'})...")
                new_videos = self.find_new_videos(platform_filter=platform, source_filter=source)
                
                # 🆕 MEJORADO: Aplicar límite restante FINAL a videos nuevos con logging detallado
                if final_remaining_limit and len(new_videos) > final_remaining_limit:
                    logger.info(f"📊 Videos nuevos encontrados: {len(new_videos)}")
                    logger.info(f"⚡ Aplicando límite restante FINAL: {len(new_videos)} -> {final_remaining_limit} seleccionados")
                    new_videos = new_videos[:final_remaining_limit]
                elif new_videos:
                    logger.info(f"📊 Videos nuevos encontrados: {len(new_videos)} (todos serán procesados)")
                else:
                    logger.info(f"📊 No se encontraron videos nuevos para procesar")
                
                # 🆕 MEJORADO: Marcar videos nuevos para debug
                for video in new_videos:
                    video['source_type'] = 'new'
                
                videos_to_process.extend(new_videos)
            else:
                logger.info(f"⏭️ Saltando búsqueda de videos nuevos (límite ya alcanzado)")
            
            if not videos_to_process:
                if imported_count > 0:
                    if limit and imported_count >= limit:
                        logger.info(f"✅ Procesamiento completado: límite alcanzado con importación")
                        logger.info(f"   📥 {imported_count} videos importados y agregados a la BD")
                        logger.info(f"   ⚡ Límite de {limit} respetado perfectamente")
                        return
                    else:
                        logger.info(f"✅ Procesamiento completado con {imported_count} videos importados solamente")
                        return
                else:
                    logger.info("❌ No hay videos para procesar (ni importados, ni pendientes, ni nuevos)")
                    logger.info(f"💡 Sugerencia: Verificar source '{source}' y platform '{platform or 'todas'}'")
                    return
            
            # 🆕 MEJORADO: Estadísticas finales COMPLETAS antes del procesamiento
            imported_for_stats = imported_count if imported_count > 0 else 0
            pending_count = sum(1 for v in videos_to_process if v.get('source_type') == 'pending')
            new_count = sum(1 for v in videos_to_process if v.get('source_type') == 'new')
            
            logger.info(f"📋 RESUMEN COMPLETO DE PROCESAMIENTO:")
            logger.info(f"  📥 Videos importados (nuevos en BD): {imported_for_stats}")
            logger.info(f"  📁 Videos ya poblados (pendientes): {pending_count}")
            logger.info(f"  🆕 Videos nuevos (se poblarán): {new_count}")
            logger.info(f"  📊 Total a procesar: {len(videos_to_process)}")
            if imported_for_stats > 0:
                logger.info(f"  🎯 Total de videos nuevos en BD: {imported_for_stats + new_count}")
            logger.info(f"  🎯 Source: {source} | Platform: {platform or 'todas'}")
            if limit:
                total_final = imported_for_stats + len(videos_to_process)
                if total_final <= limit:
                    logger.info(f"  ✅ Límite respetado: {total_final}/{limit}")
                else:
                    logger.error(f"  ❌ Error: Límite excedido: {total_final}/{limit}")
            logger.info("=" * 60)
            
            # 2. Procesar videos en lotes
            batch_results = self.process_videos_batch(videos_to_process)
            
            # 4. Mostrar estadísticas finales
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
            
        except Exception as e:
            logger.error(f"Error en ejecución principal: {e}")
            raise

def reanalyze_videos(video_ids_str, force=False):
    """Reanalizar uno o múltiples videos por sus IDs"""
    try:
        # Parsear IDs: puede ser un ID único o múltiples separados por comas
        video_ids = []
        for id_str in video_ids_str.split(','):
            id_str = id_str.strip()
            if id_str:
                try:
                    video_ids.append(int(id_str))
                except ValueError:
                    print(f"Error: ID inválido '{id_str}'. Debe ser un número entero.")
                    return False
        
        if not video_ids:
            print("Error: No se proporcionaron IDs válidos.")
            return False
        
        print(f"Tag-Flow V2 - Reanálisis de {len(video_ids)} Video(s)")
        print("=" * 60)
        
        successful_count = 0
        failed_count = 0
        errors = []
        
        # Procesar cada video
        for video_id in video_ids:
            print(f"\n[{video_ids.index(video_id) + 1}/{len(video_ids)}] Procesando video ID: {video_id}")
            print("-" * 40)
            
            success = reanalyze_single_video(video_id, force, show_header=False)
            if success:
                successful_count += 1
            else:
                failed_count += 1
                errors.append(video_id)
        
        # Mostrar resumen final
        print("\n" + "=" * 60)
        print("RESUMEN DE REANÁLISIS")
        print("=" * 60)
        print(f"Total videos procesados: {len(video_ids)}")
        print(f"✅ Exitosos: {successful_count}")
        print(f"❌ Fallidos: {failed_count}")
        
        if errors:
            print(f"Videos con errores: {', '.join(map(str, errors))}")
        
        return successful_count > 0
        
    except Exception as e:
        print(f"❌ Error fatal en reanálisis múltiple: {e}")
        logger.error(f"Error reanalizing videos {video_ids_str}: {e}")
        return False

def reanalyze_single_video(video_id, force=False, show_header=True):
    """Reanalizar un video específico por su ID"""
    try:
        if show_header:
            print(f"Tag-Flow V2 - Reanálisis de Video ID: {video_id}")
            print("=" * 60)
        
        # Verificar que el video existe
        video = db.get_video(video_id)
        if not video:
            print(f"Error: Video con ID {video_id} no encontrado en la base de datos")
            return False
        
        print(f"Video encontrado: {video['file_name']}")
        print(f"Creador: {video['creator_name']}")
        print(f"Plataforma: {video['platform']}")
        print(f"Estado actual: {video['processing_status']}")
        
        # Verificar que el archivo existe
        video_path = Path(video['file_path'])
        if not video_path.exists():
            print(f"Error: Archivo no encontrado en: {video_path}")
            db.update_video(video_id, {
                'processing_status': 'error',
                'error_message': 'Archivo no encontrado'
            })
            return False
        
        # Verificar si ya está procesado y no es forzado
        if video['processing_status'] == 'completado' and not force:
            print("Video ya está procesado. Use --force para forzar reanálisis.")
            return False
        
        # Marcar como procesando
        db.update_video(video_id, {
            'processing_status': 'procesando',
            'error_message': None
        })
        
        print("Iniciando reanálisis...")
        
        # Crear VideoAnalyzer
        analyzer = VideoAnalyzer()
        
        # Preparar datos del video en formato compatible
        video_data = {
            'file_path': video['file_path'],
            'file_name': video['file_name'],
            'creator_name': video['creator_name'],
            'platform': video['platform'],
            'title': video.get('description', ''),
            'content_type': 'video',
            'existing_video_id': video_id,  # Marcador para identificar reanálisis
            'source_type': 'reanalysis'
        }
        
        # Procesar el video
        result = analyzer.process_video(video_data)
        
        if result.get('success'):
            print(f"✅ Reanálisis completado exitosamente")
            print(f"   Música detectada: {result.get('detected_music', 'N/A')}")
            print(f"   Personajes detectados: {len(result.get('detected_characters', []))}")
            return True
        else:
            print(f"❌ Error en reanálisis: {result.get('error', 'Error desconocido')}")
            return False
            
    except Exception as e:
        print(f"❌ Error fatal en reanálisis: {e}")
        logger.error(f"Error reanalizing video {video_id}: {e}")
        
        # Marcar como error en la BD
        try:
            db.update_video(video_id, {
                'processing_status': 'error',
                'error_message': str(e)
            })
        except:
            pass
            
        return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Tag-Flow V2 - Procesador de Videos TikTok/MMD con Flags Profesionales',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                                    # Procesar todos los videos nuevos
  python main.py --limit 10                        # Procesar solo 10 videos
  python main.py --platform youtube --limit 5      # Procesar 5 videos de YouTube
  python main.py --platform tiktok --source db     # Procesar TikTok solo desde BD externa
  python main.py --source organized --limit 20     # Procesar 20 videos solo de carpetas organizadas
  python main.py --platform other --limit 10       # Procesar 10 videos de plataformas adicionales
  python main.py --platform all-platforms          # Procesar videos de todas las plataformas
  python main.py --reanalyze-video 123             # Reanalizar video específico por ID
  python main.py --reanalyze-video 1,2,3           # Reanalizar videos específicos por IDs
  python main.py --reanalyze-video 123 --force     # Forzar reanálisis sobrescribiendo datos
  python main.py --reanalyze-video 10,20,30 --force # Forzar reanálisis múltiple sobrescribiendo datos

Opciones de source:
  db        = Solo bases de datos externas (4K Apps)
  organized = Solo carpetas organizadas (D:\\4K All)
  all       = Ambas fuentes (por defecto)

Opciones de platform:
  youtube        = YouTube (4K Video Downloader+)
  tiktok         = TikTok (4K Tokkit)
  instagram      = Instagram (4K Stogram)  
  other          = Solo plataformas adicionales
  all-platforms  = Todas las plataformas
  [NOMBRE]       = Plataforma específica (ej: iwara)

Notas:
  - Sin límite: procesa todos los videos encontrados
  - Con límite: selecciona los primeros N videos de la lista
  - Los videos ya procesados se omiten automáticamente
        """)
    
    # Opciones principales
    parser.add_argument(
        '--limit', 
        type=int,
        help='Número máximo de videos a procesar'
    )
    
    parser.add_argument(
        '--source',
        choices=['db', 'organized', 'all'],
        default='all',
        help='Fuente de datos: db=bases externas, organized=carpetas D:\\4K All, all=ambas (por defecto)'
    )
    
    # Obtener plataformas disponibles dinámicamente
    available_platforms = external_sources.get_available_platforms()
    
    # Crear lista de opciones de plataforma
    platform_choices = ['youtube', 'tiktok', 'instagram']  # Principales
    platform_choices.extend(available_platforms['additional'].keys())  # Adicionales
    platform_choices.extend(['other', 'all-platforms'])  # Especiales
    
    parser.add_argument(
        '--platform',
        choices=platform_choices,
        help=f'Plataforma específica. Principales: youtube, tiktok, instagram. Adicionales: {", ".join(available_platforms["additional"].keys()) if available_platforms["additional"] else "ninguna"}. Especiales: other (solo adicionales), all-platforms (todas)'
    )
    
    # Opción para reanálisis de video específico
    parser.add_argument(
        '--reanalyze-video',
        type=str,
        help='ID(s) del video específico a reanalizar (fuerza re-procesamiento de música y personajes). Puede ser un ID único o múltiples IDs separados por comas (ej: 1,2,3)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Forzar reanálisis sobrescribiendo datos existentes'
    )
    
    args = parser.parse_args()
    
    # Validaciones
    if args.limit is not None and args.limit <= 0:
        print("Error: El límite debe ser un número positivo")
        sys.exit(1)
    
    # Modo especial: reanálisis de video específico o múltiple
    if args.reanalyze_video:
        return reanalyze_videos(args.reanalyze_video, args.force)
    
    # Mostrar información de configuración
    print("Tag-Flow V2 - Procesador con Flags Profesionales")
    print("=" * 60)
    
    # Mostrar fuente
    source_names = {
        'db': 'Bases de Datos Externas (4K Apps)',
        'organized': 'Carpetas Organizadas (D:\\4K All)',
        'all': 'Todas las Fuentes'
    }
    print(f"Fuente: {source_names[args.source]}")
    
    # Mostrar plataforma
    if args.platform:
        platform_names = {
            'youtube': 'YouTube (4K Video Downloader+)',
            'tiktok': 'TikTok (4K Tokkit)', 
            'instagram': 'Instagram (4K Stogram)',
            'other': 'Solo Plataformas Adicionales',
            'all-platforms': 'Todas las Plataformas'
        }
        
        # Agregar plataformas adicionales
        for platform_key, platform_info in available_platforms['additional'].items():
            platform_names[platform_key] = f"{platform_info['folder_name']} (D:\\4K All\\{platform_info['folder_name']})"
        
        print(f"Plataforma: {platform_names.get(args.platform, args.platform.title())}")
    else:
        print(f"Plataforma: Todas las Disponibles")
    
    # Mostrar límite
    if args.limit:
        print(f"Limite: Maximo {args.limit} videos")
    else:
        print(f"Limite: Todos los videos disponibles")
    
    print("=" * 60)
    print("Iniciando procesamiento...")
    print()
    
    try:
        # ✅ OPTIMIZACIONES: Usar VideoAnalyzer optimizado si está configurado
        if config.USE_OPTIMIZED_DATABASE:
            try:
                # Intentar importar y usar OptimizedVideoAnalyzer
                sys.path.append(str(Path(__file__).parent / 'src'))
                from src.optimized_video_analyzer import OptimizedVideoAnalyzer
                analyzer = OptimizedVideoAnalyzer()
                logger.info("🚀 Usando VideoAnalyzer OPTIMIZADO")
            except Exception as e:
                logger.warning(f"⚠️ Error cargando optimizaciones, fallback a estándar: {e}")
                analyzer = VideoAnalyzer()
                logger.info("📊 Usando VideoAnalyzer ESTÁNDAR (fallback)")
        else:
            analyzer = VideoAnalyzer()
            logger.info("📊 Usando VideoAnalyzer ESTÁNDAR (configuración)")
        
        analyzer.run(limit=args.limit, platform=args.platform, source=args.source)
        
        # ✅ MÉTRICAS: Log de performance si están disponibles
        if config.USE_OPTIMIZED_DATABASE and hasattr(analyzer, 'get_performance_report'):
            try:
                performance_report = analyzer.get_performance_report()
                if performance_report.get('optimization_status') == 'ACTIVE':
                    logger.info("📊 MÉTRICAS DE OPTIMIZACIÓN:")
                    logger.info(f"  💾 Cache hit rate: {performance_report['cache_stats']['hit_rate_percentage']}%")
                    logger.info(f"  ⚡ Queries/segundo: {performance_report['queries_per_second']:.1f}")
                    logger.info(f"  🏆 Performance grade: {performance_report['performance_grade']}")
            except Exception as e:
                logger.debug(f"Error mostrando métricas: {e}")
        
        print()
        print("=" * 60)
        print("Procesamiento completado exitosamente")
        
    except KeyboardInterrupt:
        print()
        print("Procesamiento interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"Error durante el procesamiento: {e}")
        logger.error(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()