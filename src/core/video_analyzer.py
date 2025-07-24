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
        
        # Validar configuración (solo mostrar errores críticos)
        warnings = config.validate_config()
        critical_warnings = [w for w in warnings if "API" in w or "configurada" in w]
        if critical_warnings:
            logger.warning("⚠️ Configuración: " + "; ".join(critical_warnings))
    
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
        
        logger.info(f"🎬 Procesando {total_videos} videos (workers: {max_workers})...")
        
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
                    
                    current_num = results['processed'] + results['errors'] + 1
                    
                    if result['success']:
                        results['processed'] += 1
                        # Solo mostrar detalles de procesamiento exitoso si hay pocos videos
                        if total_videos <= 3:
                            music = result.get('detected_music') or 'N/A'
                            chars = len(result.get('detected_characters', []))
                            logger.info(f"✅ [{current_num}/{total_videos}] {Path(video['file_path']).name} - Música: {music}, Personajes: {chars}")
                        else:
                            logger.info(f"✅ [{current_num}/{total_videos}] {Path(video['file_path']).name}")
                    else:
                        results['errors'] += 1
                        logger.error(f"❌ [{current_num}/{total_videos}] {Path(video['file_path']).name}: {result.get('error', 'Error desconocido')}")
                    
                    results['details'].append(result)
                    
                except Exception as e:
                    results['errors'] += 1
                    logger.error(f"❌ Error procesando video: {e}")
                    results['details'].append({
                        'success': False,
                        'error': str(e),
                        'video_path': video.get('file_path', 'Unknown')
                    })
        
        # Solo mostrar estadísticas si hay errores o múltiples videos
        if results['errors'] > 0 or total_videos > 1:
            success_rate = (results['processed'] / total_videos * 100) if total_videos > 0 else 0
            logger.info(f"📊 Resumen: {results['processed']} exitosos, {results['errors']} errores ({success_rate:.1f}%)")
        
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
            
            # Removido log individual - se muestra en process_videos
            
            # Verificar que el archivo existe
            if not Path(file_path).exists():
                return {
                    'success': False,
                    'error': 'Archivo no encontrado',
                    'video_path': file_path
                }
            
            # Verificar que es un video válido
            if not video_processor.is_valid_video(Path(file_path)):
                return {
                    'success': False,
                    'error': 'Archivo de video inválido',
                    'video_path': file_path
                }
            
            # Extraer metadatos básicos
            video_metadata = video_processor.extract_metadata(file_path)
            
            # Análisis de música (si hay audio)
            music_result = {'song_name': None, 'artist_name': None, 'confidence': 0.0, 'source': None}
            
            if video_metadata.get('has_audio', False):
                try:
                    # Extraer audio temporal
                    audio_path = video_processor.extract_audio(Path(file_path), duration=30)
                    if audio_path:
                        # Usar reconocimiento de música con filename para análisis completo
                        filename = Path(file_path).name
                        music_result = music_recognizer.recognize_music(audio_path, filename)
                        # Limpiar archivo temporal
                        if audio_path.exists():
                            audio_path.unlink()
                except Exception as e:
                    logger.warning(f"  Error en reconocimiento musical: {e}")
            
            # Análisis de personajes y reconocimiento facial inteligente
            face_result = {'characters': [], 'faces': []}
            
            try:
                frame_data = video_processor.get_video_frame(Path(file_path), timestamp=2.0)
                if frame_data:
                    # Preparar datos del video para análisis inteligente
                    video_data_for_recognition = {
                        'creator_name': video_data.get('creator_name', ''),
                        'platform': video_data.get('platform', 'unknown'),
                        'title': video_data.get('title', '') or video_data.get('description', '')
                    }
                    
                    # Usar reconocimiento inteligente que combina todas las estrategias
                    face_result = face_recognizer.recognize_faces_intelligent(frame_data, video_data_for_recognition)
                        
            except Exception as e:
                logger.warning(f"  Error en reconocimiento de personajes: {e}")
            
            # Generar thumbnail
            thumbnail_result = thumbnail_generator.generate_thumbnail(Path(file_path))
            
            # Preparar datos para actualizar el video existente
            update_data = {
                # Música detectada - corregir nombres de campos
                'detected_music': music_result.get('detected_music'),
                'detected_music_artist': music_result.get('detected_music_artist'),
                'detected_music_confidence': music_result.get('detected_music_confidence'),
                'music_source': music_result.get('music_source'),
                
                # Personajes detectados - corregir nombre de campo
                'detected_characters': face_result.get('detected_characters', []),
                
                # Thumbnail
                'thumbnail_path': str(thumbnail_result) if thumbnail_result else None,
                
                # Estado
                'processing_status': 'completado'
            }
            
            # Actualizar video existente en base de datos
            video_id = video_data.get('id')
            if video_id:
                
                success = db.update_video(video_id, update_data)
                
                if success:
                    return {
                        'success': True,
                        'video_id': video_id,
                        'detected_music': music_result.get('detected_music'),
                        'detected_characters': face_result.get('detected_characters', []),
                        'video_path': file_path
                    }
                else:
                    logger.error(f"❌ Error actualizando video {video_id} en BD")
                    return {
                        'success': False,
                        'error': 'Error actualizando video en base de datos',
                        'video_path': file_path
                    }
            else:
                return {
                    'success': False,
                    'error': 'Video ID no encontrado para actualización',
                    'video_path': file_path
                }
                
        except Exception as e:
            logger.error(f"Error procesando video {video_data.get('file_path', 'Unknown')}: {e}")
            return {
                'success': False,
                'error': str(e),
                'video_path': video_data.get('file_path', 'Unknown')
            }
    
    def run(self, limit=None, platform=None, source='all', force=False):
        """
        Ejecutar análisis completo con la lógica correcta
        
        Args:
            limit (int, optional): Número máximo de videos a procesar. 
                                 Si es None, procesa todos. Si es 0, solo analiza existentes.
            platform (str, optional): Plataforma específica a procesar
            source (str, optional): Fuente de datos ('db', 'organized', 'all')
            force (bool, optional): Si True, reanaliza videos completados
        """
        # Mostrar configuración inicial compacta
        filter_info = f"platform={platform or 'todas'}, source={source}"
        if limit == 0:
            filter_info += " (solo existentes)"
        elif limit:
            filter_info += f", limit={limit}"
        if force:
            filter_info += ", force=True"
        
        logger.info(f"🎯 Análisis: {filter_info}")
        
        # Paso 1: Obtener videos existentes en BD según filtros
        filters = {}
        if platform:
            filters['platform'] = platform
        
        # Obtener videos pendientes de análisis o todos según filtros
        existing_videos = db.get_videos(filters)
        
        # Filtrar solo videos que necesitan análisis (sin personajes o música)
        videos_to_analyze = []
        for video in existing_videos:
            # Un video necesita análisis si:
            # 1. No tiene estado completado
            # 2. No tiene personajes detectados (None, vacío o "[]")
            # 3. No tiene música detectada
            processing_status = video.get('processing_status')
            detected_chars = video.get('detected_characters')
            detected_music = video.get('detected_music')
            
            # Con force=True, analizar todos los videos
            if force:
                needs_analysis = True
            else:
                needs_analysis = (
                    processing_status != 'completado' or
                    not detected_chars or 
                    detected_chars == '[]' or
                    detected_chars == 'null' or
                    not detected_music
                )
            
            if needs_analysis:
                videos_to_analyze.append(video)
        
        logger.info(f"📊 BD: {len(existing_videos)} total, {len(videos_to_analyze)} pendientes")
        
        # Paso 2: Determinar si necesitamos importar más videos
        if limit == 0:
            # limit=0: Solo analizar existentes, no importar
            need_to_import = False
            videos_needed = len(videos_to_analyze)
        elif limit is None:
            # Sin limit: Importar todos los disponibles, luego analizar todos
            need_to_import = True
            videos_needed = None  # Ilimitado
        else:
            # limit>0: Importar solo si necesitamos más videos para alcanzar el límite
            videos_needed = limit
            need_to_import = videos_needed > len(videos_to_analyze)
        
        if need_to_import:
            additional_needed = videos_needed - len(videos_to_analyze) if limit else None
            logger.info(f"📥 Importando {additional_needed or 'todos'} videos adicionales...")
            
            # Importar videos adicionales usando populate-db
            from src.maintenance.database_ops import DatabaseOperations
            db_ops = DatabaseOperations()
            import_result = db_ops.populate_database(
                source=source,
                platform=platform,
                limit=additional_needed
            )
            
            if import_result['success'] and import_result['imported'] > 0:
                logger.info(f"✅ +{import_result['imported']} videos importados")
                
                # Actualizar lista de videos para analizar
                new_existing = db.get_videos(filters)
                for video in new_existing:
                    if video not in existing_videos:
                        needs_analysis = (
                            not video.get('detected_characters') or 
                            video.get('detected_characters') == '[]' or 
                            video.get('processing_status') != 'completado'
                        )
                        if needs_analysis:
                            videos_to_analyze.append(video)
        
        # Paso 3: Aplicar límite final
        if limit and limit > 0:
            videos_to_analyze = videos_to_analyze[:limit]
        
        if not videos_to_analyze:
            logger.info("🎉 No hay videos para analizar")
            return {'success': True, 'processed': 0, 'errors': 0}
        
        # Paso 4: Procesar videos con IA
        result = self.process_videos(videos_to_analyze)
        
        # Log compacto del resultado final
        if result['success']:
            processed = result.get('processed', 0)
            errors = result.get('errors', 0) 
            logger.info(f"✅ Completado: {processed} procesados, {errors} errores")
        else:
            logger.error("❌ Análisis falló")
        
        return result