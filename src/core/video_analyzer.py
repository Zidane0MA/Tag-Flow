"""
Tag-Flow V2 - Video Analyzer
Lógica central de análisis de videos extraída del main.py original
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import config
from src.database import db
from src.external_sources import external_sources
from src.video_processor import video_processor
from src.music_recognition import music_recognizer
from src.face_recognition import face_recognizer
from src.thumbnail_generator import thumbnail_generator

logger = logging.getLogger(__name__)

class VideoAnalyzer:
    """Analizador principal de videos refactorizado"""
    
    def __init__(self):
        # Asegurar que los directorios existen
        config.ensure_directories()
        
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
                'other': 'OTHER',
                'all-platforms': 'ALL'
            }
            
            # Obtener plataformas adicionales disponibles
            available_platforms = external_sources.get_available_platforms()
            
            # Agregar plataformas adicionales al mapa
            for platform_key in available_platforms['additional'].keys():
                platform_map[platform_key] = platform_key.upper()
            
            # Convertir nombre moderno a código interno
            internal_platform_code = None
            if platform_filter:
                internal_platform_code = platform_map.get(platform_filter)
                if not internal_platform_code:
                    internal_platform_code = platform_filter.upper()
            
            # Determinar source para external_sources basado en source_filter
            if source_filter == 'db':
                external_source = 'db'
            elif source_filter == 'organized':
                external_source = 'organized'
            else:
                external_source = 'all'
            
            # Obtener videos de fuentes externas
            external_videos = external_sources.get_all_videos_from_source(external_source, internal_platform_code)
            
            # Filtrar nuevos y verificar existencia
            for video_data in external_videos:
                file_path = video_data.get('file_path')
                if file_path and file_path not in existing_videos:
                    # Verificar que el archivo existe físicamente
                    if Path(file_path).exists():
                        new_videos.append(video_data)
                        logger.debug(f"✅ Nuevo video encontrado: {Path(file_path).name}")
                    else:
                        logger.warning(f"⚠️ Archivo no encontrado: {file_path}")
        
        logger.info(f"🆕 Videos nuevos encontrados: {len(new_videos)}")
        return new_videos
    
    def process_videos(self, videos: List[Dict], max_workers: int = None) -> Dict:
        """
        Procesar lista de videos con procesamiento paralelo
        
        Args:
            videos: Lista de diccionarios con información de videos
            max_workers: Número máximo de workers paralelos
            
        Returns:
            Dict: Estadísticas del procesamiento
        """
        if not videos:
            return {
                'success': True,
                'processed': 0,
                'errors': 0,
                'skipped': 0
            }
        
        total_videos = len(videos)
        max_workers = max_workers or config.MAX_CONCURRENT_PROCESSING
        
        logger.info(f"🎬 Procesando {total_videos} videos con {max_workers} workers paralelos...")
        
        results = {
            'processed': 0,
            'errors': 0,
            'skipped': 0,
            'details': []
        }
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar trabajos
            future_to_video = {
                executor.submit(self.process_video, video): video 
                for video in videos
            }
            
            # Procesar resultados conforme van completándose
            for future in as_completed(future_to_video):
                video = future_to_video[future]
                try:
                    result = future.result()
                    
                    if result['success']:
                        results['processed'] += 1
                        logger.info(f"✅ [{results['processed']}/{total_videos}] {Path(video['file_path']).name}")
                    else:
                        results['errors'] += 1
                        logger.error(f"❌ [{results['processed'] + results['errors']}/{total_videos}] {Path(video['file_path']).name}: {result.get('error', 'Error desconocido')}")
                    
                    results['details'].append(result)
                    
                except Exception as e:
                    results['errors'] += 1
                    logger.error(f"❌ Error procesando video: {e}")
                    results['details'].append({
                        'success': False,
                        'error': str(e),
                        'video_path': video.get('file_path', 'Unknown')
                    })
        
        # Estadísticas finales
        success_rate = (results['processed'] / total_videos * 100) if total_videos > 0 else 0
        logger.info(f"📊 Procesamiento completado:")
        logger.info(f"   ✅ Procesados: {results['processed']}")
        logger.info(f"   ❌ Errores: {results['errors']}")
        logger.info(f"   📈 Tasa de éxito: {success_rate:.1f}%")
        
        return {
            'success': True,
            **results
        }
    
    def process_video(self, video_data: Dict) -> Dict:
        """
        Procesar un video individual
        
        Args:
            video_data: Diccionario con información del video
            
        Returns:
            Dict: Resultado del procesamiento
        """
        try:
            file_path = video_data['file_path']
            file_name = video_data.get('file_name', Path(file_path).name)
            
            logger.debug(f"🎬 Procesando: {file_name}")
            
            # Verificar que el archivo existe
            if not Path(file_path).exists():
                return {
                    'success': False,
                    'error': 'Archivo no encontrado',
                    'video_path': file_path
                }
            
            # Procesar video usando video_processor
            processing_result = video_processor.process_video(video_data)
            
            if not processing_result.get('success'):
                return {
                    'success': False,
                    'error': processing_result.get('error', 'Error en procesamiento'),
                    'video_path': file_path
                }
            
            # Obtener metadata del resultado
            video_metadata = processing_result.get('metadata', {})
            
            # Análisis de música
            music_result = music_recognizer.analyze_video_music(file_path)
            
            # Análisis de personajes y reconocimiento facial
            face_result = face_recognizer.analyze_video_faces(file_path)
            
            # Generar thumbnail
            thumbnail_result = thumbnail_generator.generate_thumbnail(file_path)
            
            # Preparar datos para la base de datos
            db_data = {
                'file_path': file_path,
                'file_name': file_name,
                'creator_name': video_data.get('creator_name', 'Unknown'),
                'platform': video_data.get('platform', 'unknown'),
                'title': video_data.get('title', ''),
                'description': video_data.get('description', ''),
                'content_type': video_data.get('content_type', 'video'),
                
                # Metadata técnica
                **video_metadata,
                
                # Música detectada
                'detected_music': music_result.get('song_name'),
                'detected_music_artist': music_result.get('artist_name'),
                'music_confidence': music_result.get('confidence'),
                'music_source': music_result.get('source'),
                
                # Personajes detectados
                'detected_characters': face_result.get('characters', []),
                'detected_faces': face_result.get('faces', []),
                
                # Thumbnail
                'thumbnail_path': thumbnail_result.get('thumbnail_path'),
                
                # Estado
                'processing_status': 'completado',
                'created_at': 'CURRENT_TIMESTAMP'
            }
            
            # Insertar en base de datos
            video_id = db.insert_video(db_data)
            
            if video_id:
                return {
                    'success': True,
                    'video_id': video_id,
                    'detected_music': music_result.get('song_name'),
                    'detected_characters': face_result.get('characters', []),
                    'video_path': file_path
                }
            else:
                return {
                    'success': False,
                    'error': 'Error insertando en base de datos',
                    'video_path': file_path
                }
                
        except Exception as e:
            logger.error(f"Error procesando video {video_data.get('file_path', 'Unknown')}: {e}")
            return {
                'success': False,
                'error': str(e),
                'video_path': video_data.get('file_path', 'Unknown')
            }