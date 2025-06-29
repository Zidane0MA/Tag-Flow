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
        
        # Configurar rutas de escaneo
        self.scan_paths = [config.YOUTUBE_BASE_PATH]
        
        # Extensiones de video soportadas
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        
        logger.info("VideoAnalyzer inicializado")
        
        # Validar configuración
        warnings = config.validate_config()
        if warnings:
            logger.warning("Advertencias de configuración:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
    
    def find_new_videos(self, platform_filter=None, use_external_sources=False) -> List[Dict]:
        """
        Encontrar videos que no están en la base de datos
        
        Args:
            platform_filter: 'youtube', 'tiktok', 'instagram' o None para todas
            use_external_sources: si usar fuentes externas en lugar de escaneo local
            
        Returns:
            List[Dict]: Lista de diccionarios con información completa del video
        """
        logger.info("Buscando videos nuevos...")
        
        # Obtener videos ya procesados de la BD
        existing_videos = set()
        try:
            videos_in_db = db.get_videos()
            existing_videos = {video['file_path'] for video in videos_in_db}
            logger.info(f"Videos en BD: {len(existing_videos)}")
        except Exception as e:
            logger.error(f"Error consultando BD: {e}")
        
        new_videos = []
        
        if use_external_sources:
            # Usar fuentes externas (bases de datos y carpetas organizadas)
            logger.info("Usando fuentes externas para búsqueda de videos...")
            
            # Mapear códigos de plataforma
            platform_map = {
                'YT': 'youtube',
                'TT': 'tiktok', 
                'IG': 'instagram',
                'O': None  # Carpetas organizadas, todas las plataformas
            }
            
            actual_platform = platform_map.get(platform_filter, platform_filter)
            
            # Obtener videos de fuentes externas
            external_videos = external_sources.get_all_videos_from_source('all', actual_platform)
            
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
        
        else:
            # Búsqueda local tradicional
            total_found = 0
            
            for scan_path in self.scan_paths:
                if not scan_path.exists():
                    logger.warning(f"Ruta de escaneo no existe: {scan_path}")
                    continue
                    
                logger.info(f"Escaneando: {scan_path}")
                
                # Buscar recursivamente
                for video_file in scan_path.rglob('*'):
                    if video_file.is_file() and video_file.suffix.lower() in self.video_extensions:
                        total_found += 1
                        
                        # Verificar si es válido y no está en BD
                        if str(video_file) not in existing_videos:
                            if video_processor.is_valid_video(video_file):
                                # Para compatibilidad, crear estructura de datos
                                video_data = {
                                    'file_path': str(video_file),
                                    'file_name': video_file.name,
                                    'creator_name': self._infer_creator_name(video_file),
                                    'platform': 'tiktok',  # Valor por defecto para escaneo local
                                    'content_type': 'video'
                                }
                                new_videos.append(video_data)
                            else:
                                logger.warning(f"Video inválido: {video_file}")
            
            logger.info(f"Videos encontrados: {total_found}, Nuevos: {len(new_videos)}")
        
        logger.info(f"Videos nuevos para procesar: {len(new_videos)}")
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
            
            # 6. Reconocimiento facial (frame del segundo 2)
            faces_result = {'detected_characters': [], 'recognition_source': None}
            
            logger.info(f"  Analizando caras/personajes...")
            try:
                frame_data = video_processor.get_video_frame(video_path, timestamp=2.0)
                if frame_data:
                    faces_result = face_recognizer.recognize_faces(frame_data)
            except Exception as e:
                logger.warning(f"  Error en reconocimiento facial: {e}")
            
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
    def _infer_creator_name(self, video_path: Path) -> str:
        """Inferir nombre del creador desde la ruta del archivo"""
        # Estrategias para inferir el creador:
        # 1. Carpeta padre (si está organizado por creador)
        # 2. Prefijo del archivo
        # 3. Integración con 4K Downloader (futuro)
        
        # Estrategia 1: Usar nombre de la carpeta padre
        parent_folder = video_path.parent.name
        if parent_folder and parent_folder != str(config.YOUTUBE_BASE_PATH.name):
            # Limpiar nombre de carpeta
            creator = parent_folder.replace('_', ' ').replace('-', ' ').title()
            return creator
        
        # Estrategia 2: Extraer del nombre del archivo si tiene patrón
        filename = video_path.stem
        if '_' in filename:
            # Asumir formato: creador_titulo o similar
            potential_creator = filename.split('_')[0]
            if len(potential_creator) > 2:  # Filtrar abreviaciones muy cortas
                return potential_creator.replace('-', ' ').title()
        
        # Fallback: usar "Desconocido"
        return "Desconocido"
    
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
    
    def get_pending_videos(self, platform_filter=None, limit=None) -> List[Dict]:
        """
        Obtener videos pendientes de la base de datos para procesamiento
        
        Args:
            platform_filter: 'YT', 'TT', 'IG', 'O' o None para todas las plataformas
            limit: número máximo de videos a retornar
            
        Returns:
            List[Dict]: Lista de diccionarios con información completa del video
        """
        logger.info("Buscando videos pendientes en la base de datos...")
        
        # Mapear códigos de plataforma a nombres reales
        platform_map = {
            'YT': 'youtube',
            'TT': 'tiktok', 
            'IG': 'instagram',
            'O': None  # Para carpetas organizadas, puede ser cualquier plataforma
        }
        
        # Construir filtros
        filters = {'processing_status': 'pendiente'}
        
        if platform_filter:
            actual_platform = platform_map.get(platform_filter, platform_filter)
            if actual_platform:  # Solo filtrar si no es 'O' (None)
                filters['platform'] = actual_platform
        
        # Obtener videos pendientes de la BD
        pending_videos_db = db.get_videos(filters, limit=limit)
        
        logger.info(f"Videos pendientes encontrados: {len(pending_videos_db)}")
        
        # Convertir a formato compatible con process_video
        pending_videos = []
        for video in pending_videos_db:
            video_data = {
                'file_path': video['file_path'],
                'file_name': video['file_name'],
                'creator_name': video['creator_name'],
                'platform': video['platform'],
                'content_type': 'video',
                'existing_video_id': video['id']  # Marcador para identificar que ya existe
            }
            
            # Verificar que el archivo aún existe
            if Path(video['file_path']).exists():
                pending_videos.append(video_data)
            else:
                logger.warning(f"Archivo no encontrado: {video['file_path']}")
        
        logger.info(f"Videos pendientes válidos: {len(pending_videos)}")
        return pending_videos

    def run(self, limit=None, platform=None):
        """Ejecutar el análisis completo
        
        Args:
            limit (int, optional): Número máximo de videos a procesar. Si es None, procesa todos.
            platform (str, optional): Plataforma específica a procesar ('YT', 'TT', 'IG', 'O')
        """
        logger.info("=== INICIANDO TAG-FLOW V2 ANALYSIS ===")
        
        if limit:
            logger.info(f"MODO LIMITADO: Procesando máximo {limit} videos")
        
        if platform:
            platform_names = {
                'YT': 'YouTube', 
                'TT': 'TikTok', 
                'IG': 'Instagram', 
                'O': 'Carpetas Organizadas (D:\\4K All)'
            }
            logger.info(f"PLATAFORMA ESPECÍFICA: {platform_names.get(platform, platform)}")
        
        try:
            # 0. Importar desde 4K Downloader si está disponible (solo si no hay filtro de plataforma)
            if not platform and downloader_integration.is_available:
                logger.info("Importando desde 4K Video Downloader...")
                import_result = downloader_integration.import_creators_and_videos()
                if import_result['success']:
                    logger.info(f"✓ Importados {import_result['imported_videos']} videos, {import_result['creators_found']} creadores")
                else:
                    logger.warning(f"Importación falló: {import_result.get('error', 'Error desconocido')}")
            
            # 1. Buscar videos pendientes primero
            videos_to_process = []
            
            # 1a. Obtener videos pendientes de la BD
            pending_videos = self.get_pending_videos(platform_filter=platform, limit=limit)
            videos_to_process.extend(pending_videos)
            
            # 1b. Si no hay suficientes videos pendientes, buscar videos nuevos
            remaining_limit = None
            if limit:
                remaining_limit = limit - len(videos_to_process)
                if remaining_limit <= 0:
                    logger.info(f"Límite alcanzado con videos pendientes: {len(videos_to_process)}")
                else:
                    logger.info(f"Videos pendientes: {len(videos_to_process)}, buscando {remaining_limit} videos nuevos...")
            else:
                logger.info(f"Videos pendientes: {len(videos_to_process)}, buscando videos nuevos adicionales...")
            
            # Solo buscar videos nuevos si no hemos alcanzado el límite
            if not limit or remaining_limit > 0:
                use_external = platform is not None  # Si hay filtro de plataforma, usar fuentes externas
                new_videos = self.find_new_videos(platform_filter=platform, use_external_sources=use_external)
                
                # Aplicar límite restante a videos nuevos
                if remaining_limit and len(new_videos) > remaining_limit:
                    logger.info(f"Limitando videos nuevos: {len(new_videos)} encontrados -> {remaining_limit} seleccionados")
                    new_videos = new_videos[:remaining_limit]
                
                videos_to_process.extend(new_videos)
            
            if not videos_to_process:
                logger.info("No hay videos para procesar (ni pendientes ni nuevos)")
                return
            
            logger.info(f"Total de videos a procesar: {len(videos_to_process)}")
            
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

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Tag-Flow V2 - Procesador de Videos TikTok/MMD',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                    # Procesar todos los videos nuevos
  python main.py 10                 # Procesar solo 10 videos
  python main.py 5 YT               # Procesar 5 videos de YouTube
  python main.py 3 TT               # Procesar 3 videos de TikTok  
  python main.py 2 IG               # Procesar 2 videos de Instagram
  python main.py 10 O               # Procesar 10 videos de carpetas organizadas (D:\\4K All)

Códigos de plataforma:
  YT  = YouTube (desde 4K Video Downloader+)
  TT  = TikTok (desde 4K Tokkit)  
  IG  = Instagram (desde 4K Stogram)
  O   = Otros (carpetas organizadas en D:\\4K All)

Notas:
  - Sin límite: procesa todos los videos encontrados
  - Con límite: selecciona los primeros N videos de la lista
  - Los videos ya procesados se omiten automáticamente
  - Con código de plataforma: usa fuentes externas específicas
        """)
    
    parser.add_argument(
        'limit', 
        type=int, 
        nargs='?', 
        default=None,
        help='Número máximo de videos a procesar (opcional)'
    )
    
    parser.add_argument(
        'platform',
        nargs='?',
        choices=['YT', 'TT', 'IG', 'O'],
        help='Código de plataforma específica (YT=YouTube, TT=TikTok, IG=Instagram, O=Carpetas organizadas)'
    )
    
    parser.add_argument(
        '--limit', 
        type=int, 
        dest='limit_alt',
        help='Número máximo de videos a procesar (formato alternativo)'
    )
    
    args = parser.parse_args()
    
    # Determinar el límite (prioridad al argumento posicional)
    limit = args.limit or args.limit_alt
    platform = args.platform
    
    if limit is not None and limit <= 0:
        print("Error: El límite debe ser un número positivo")
        sys.exit(1)
    
    # Mostrar información de configuración
    platform_names = {
        'YT': 'YouTube', 
        'TT': 'TikTok', 
        'IG': 'Instagram', 
        'O': 'Carpetas Organizadas'
    }
    
    if platform:
        print(f"Tag-Flow V2 - Plataforma: {platform_names[platform]}")
        if limit:
            print(f"Máximo {limit} videos")
        else:
            print("Todos los videos disponibles")
    elif limit:
        print(f"Tag-Flow V2 - Modo Limitado ({limit} videos máximo)")
    else:
        print("Tag-Flow V2 - Modo Completo (todos los videos)")
    
    print("Iniciando procesamiento...")
    print("-" * 50)
    
    try:
        analyzer = VideoAnalyzer()
        analyzer.run(limit=limit, platform=platform)
        
        print("-" * 50)
        print("Procesamiento completado exitosamente")
        
    except KeyboardInterrupt:
        print("\nProcesamiento interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError durante el procesamiento: {e}")
        logger.error(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()