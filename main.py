"""
Tag-Flow V2 - Script Principal de Procesamiento
Motor que analiza videos nuevos y alimenta la base de datos
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import os

# Agregar el directorio src al path para imports
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config
from src.database import db
from src.video_processor import video_processor
from src.music_recognition import music_recognizer
from src.face_recognition import face_recognizer
from src.thumbnail_generator import thumbnail_generator
from src.downloader_integration import downloader_integration

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tag_flow_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VideoAnalyzer:
    """Analizador principal de videos TikTok/MMD"""
    
    def __init__(self):
        # Asegurar que los directorios existen
        config.ensure_directories()
        
        # Configurar rutas de escaneo
        self.scan_paths = [config.VIDEOS_BASE_PATH]
        
        # Extensiones de video soportadas
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        
        logger.info("VideoAnalyzer inicializado")
        
        # Validar configuración
        warnings = config.validate_config()
        if warnings:
            logger.warning("Advertencias de configuración:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
    
    def find_new_videos(self) -> List[Path]:
        """Encontrar videos que no están en la base de datos"""
        logger.info("Buscando videos nuevos...")
        
        # Obtener videos ya procesados de la BD
        existing_videos = set()
        try:
            videos_in_db = db.get_videos()
            existing_videos = {video['file_path'] for video in videos_in_db}
            logger.info(f"Videos en BD: {len(existing_videos)}")
        except Exception as e:
            logger.error(f"Error consultando BD: {e}")
        
        # Buscar archivos de video en las rutas configuradas
        new_videos = []
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
                            new_videos.append(video_file)
                        else:
                            logger.warning(f"Video inválido: {video_file}")
        
        logger.info(f"Videos encontrados: {total_found}, Nuevos: {len(new_videos)}")
        return new_videos    
    def process_video(self, video_path: Path) -> Dict:
        """Procesar un video individual completamente"""
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
            
            # 2. Inferir creador desde la ruta del archivo
            creator_name = self._infer_creator_name(video_path)
            metadata['creator_name'] = creator_name
            
            # 3. Generar thumbnail
            logger.info(f"  Generando thumbnail...")
            thumbnail_path = thumbnail_generator.generate_thumbnail(video_path, timestamp=2.0)
            if thumbnail_path:
                metadata['thumbnail_path'] = str(thumbnail_path)
            
            # 4. Agregar a la base de datos (estado pendiente)
            metadata['processing_status'] = 'procesando'
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
                        music_result = music_recognizer.recognize_music(audio_path)
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
                'detected_characters': faces_result.get('detected_characters', []),
                'processing_status': 'completado'
            }
            
            db.update_video(video_id, updates)
            
            result['success'] = True
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            
            logger.info(f"  ✓ Completado en {processing_time:.1f}s - Música: {music_result.get('detected_music', 'N/A')} - Caras: {len(faces_result.get('detected_characters', []))}")
            
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
        if parent_folder and parent_folder != str(config.VIDEOS_BASE_PATH.name):
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
    
    def process_videos_batch(self, video_paths: List[Path]) -> Dict:
        """Procesar múltiples videos con threading"""
        logger.info(f"Procesando {len(video_paths)} videos...")
        
        results = {
            'total': len(video_paths),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'processing_time': 0
        }
        
        start_time = time.time()
        
        # Procesar con threading
        max_workers = min(config.MAX_CONCURRENT_PROCESSING, len(video_paths))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todos los trabajos
            future_to_video = {
                executor.submit(self.process_video, video_path): video_path 
                for video_path in video_paths
            }
            
            # Recopilar resultados
            for future in as_completed(future_to_video):
                video_path = future_to_video[future]
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
    
    def run(self):
        """Ejecutar el análisis completo"""
        logger.info("=== INICIANDO TAG-FLOW V2 ANALYSIS ===")
        
        try:
            # 0. Importar desde 4K Downloader si está disponible
            if downloader_integration.is_available:
                logger.info("Importando desde 4K Video Downloader...")
                import_result = downloader_integration.import_creators_and_videos()
                if import_result['success']:
                    logger.info(f"✓ Importados {import_result['imported_videos']} videos, {import_result['creators_found']} creadores")
                else:
                    logger.warning(f"Importación falló: {import_result.get('error', 'Error desconocido')}")
            
            # 1. Buscar videos nuevos
            new_videos = self.find_new_videos()
            
            if not new_videos:
                logger.info("No hay videos nuevos para procesar")
                return
            
            # 2. Procesar videos en lotes
            batch_results = self.process_videos_batch(new_videos)
            
            # 3. Mostrar estadísticas finales
            stats = db.get_stats()
            logger.info("=== ESTADÍSTICAS FINALES ===")
            logger.info(f"Total videos en BD: {stats['total_videos']}")
            logger.info(f"Videos con música: {stats['with_music']}")
            logger.info(f"Videos con personajes: {stats['with_characters']}")
            
            # Por estado
            for status, count in stats['by_status'].items():
                logger.info(f"Estado '{status}': {count}")
            
        except Exception as e:
            logger.error(f"Error en ejecución principal: {e}")
            raise

def main():
    """Función principal"""
    analyzer = VideoAnalyzer()
    analyzer.run()

if __name__ == "__main__":
    main()