"""
Tag-Flow V2 - Reanalysis Engine
Motor de reanálisis de videos específicos
"""

import logging
from pathlib import Path
from typing import List, Union, Dict

from config import config
# 🚀 MIGRADO: Eliminados imports directos, ahora se usan via service factory
from .video_analyzer import VideoAnalyzer

logger = logging.getLogger(__name__)

class ReanalysisEngine:
    """Motor de reanálisis de videos existentes"""
    
    def __init__(self):
        self.analyzer = VideoAnalyzer()
        # 🚀 LAZY LOADING: Database se carga solo cuando se necesita
        self._db = None
    
    @property
    def db(self):
        """Lazy initialization of DatabaseManager via ServiceFactory"""
        if self._db is None:
            from src.service_factory import get_database
            self._db = get_database()
        return self._db
        
    def reanalyze_videos(self, video_ids: Union[List[int], str], force: bool = False) -> Dict:
        """
        Reanalizar videos específicos por ID
        
        Args:
            video_ids: Lista de IDs o string separado por comas
            force: Forzar reanálisis sobrescribiendo datos existentes
            
        Returns:
            Dict: Resultado del reanálisis
        """
        # Convertir a lista si es string
        if isinstance(video_ids, str):
            video_ids = [int(vid.strip()) for vid in video_ids.split(',')]
        
        logger.info(f"🔄 Iniciando reanálisis de {len(video_ids)} video(s): {video_ids}")
        
        results = {
            'processed': 0,
            'errors': 0,
            'skipped': 0,
            'details': []
        }
        
        for video_id in video_ids:
            result = self._reanalyze_single_video(video_id, force)
            
            if result['success']:
                results['processed'] += 1
                logger.info(f"✅ Video {video_id} reanálisis exitoso")
            else:
                results['errors'] += 1
                logger.error(f"❌ Video {video_id} error: {result.get('error', 'Error desconocido')}")
            
            results['details'].append(result)
        
        # Estadísticas finales
        total = len(video_ids)
        success_rate = (results['processed'] / total * 100) if total > 0 else 0
        
        logger.info(f"📊 Reanálisis completado:")
        logger.info(f"   ✅ Exitosos: {results['processed']}")
        logger.info(f"   ❌ Errores: {results['errors']}")
        logger.info(f"   📈 Tasa de éxito: {success_rate:.1f}%")
        
        return {
            'success': results['errors'] == 0,
            **results
        }
    
    def _reanalyze_single_video(self, video_id: int, force: bool = False) -> Dict:
        """
        Reanalizar un video específico
        
        Args:
            video_id: ID del video en la base de datos
            force: Forzar reanálisis sobrescribiendo datos existentes
            
        Returns:
            Dict: Resultado del reanálisis individual
        """
        try:
            # Obtener video de la base de datos
            video = self.db.get_video_by_id(video_id)
            if not video:
                return {
                    'success': False,
                    'error': f'Video con ID {video_id} no encontrado en BD',
                    'video_id': video_id
                }
            
            # Verificar que el archivo existe
            file_path = video['file_path']
            if not Path(file_path).exists():
                return {
                    'success': False,
                    'error': 'Archivo de video no encontrado en el sistema',
                    'video_id': video_id,
                    'file_path': file_path
                }
            
            # Verificar si ya está procesado (a menos que sea force)
            if not force and video.get('processing_status') == 'completado':
                if video.get('detected_music') or video.get('detected_characters'):
                    return {
                        'success': False,
                        'error': 'Video ya procesado (usa --force para sobrescribir)',
                        'video_id': video_id,
                        'skipped': True
                    }
            
            # Marcar como procesando
            self.db.update_video(video_id, {
                'processing_status': 'procesando',
                'error_message': None
            })
            
            logger.info(f"🔄 Reanalizando video {video_id}: {Path(file_path).name}")
            
            # Preparar datos del video en formato compatible
            video_data = {
                'file_path': file_path,
                'file_name': video['file_name'],
                'creator_name': video['creator_name'],
                'platform': video['platform'],
                'title': video.get('description', ''),
                'description': video.get('description', ''),
                'content_type': 'video',
                'existing_video_id': video_id,  # Marcador para identificar reanálisis
                'source_type': 'reanalysis'
            }
            
            # Procesar el video usando el analizador
            result = self.analyzer.process_video(video_data)
            
            if result.get('success'):
                logger.info(f"✅ Reanálisis de video {video_id} completado exitosamente")
                return {
                    'success': True,
                    'video_id': video_id,
                    'detected_music': result.get('detected_music'),
                    'detected_characters': result.get('detected_characters', []),
                    'message': 'Reanálisis completado exitosamente'
                }
            else:
                # Marcar como error
                self.db.update_video(video_id, {
                    'processing_status': 'error',
                    'error_message': result.get('error', 'Error en reanálisis')
                })
                
                return {
                    'success': False,
                    'error': result.get('error', 'Error desconocido en reanálisis'),
                    'video_id': video_id
                }
                
        except Exception as e:
            logger.error(f"Error fatal reanalizando video {video_id}: {e}")
            
            # Marcar como error en la BD
            try:
                self.db.update_video(video_id, {
                    'processing_status': 'error',
                    'error_message': str(e)
                })
            except:
                pass
            
            return {
                'success': False,
                'error': f'Error fatal: {str(e)}',
                'video_id': video_id
            }