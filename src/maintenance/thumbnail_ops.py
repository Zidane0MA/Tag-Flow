#!/usr/bin/env python3
"""
🖼️ Thumbnail Operations Module
Módulo especializado para operaciones de thumbnails extraído de main.py
"""

import os
import time
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos del proyecto
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from src.database import DatabaseManager
from src.thumbnail_generator import ThumbnailGenerator

# Instancias globales - movidas a funciones para evitar inicialización múltiple


class ThumbnailOperations:
    """
    🖼️ Operaciones especializadas de thumbnails
    
    Funcionalidades:
    - Regeneración masiva de thumbnails
    - Regeneración por IDs específicos  
    - Limpieza de thumbnails huérfanos
    - Validación de thumbnails corruptos
    - Procesamiento paralelo optimizado
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.thumbnail_generator = ThumbnailGenerator()
    
    def regenerate_thumbnails(self, force: bool = False) -> Dict[str, Any]:
        """
        🚀 OPTIMIZADO: Regeneración selectiva de thumbnails con procesamiento paralelo
        
        Args:
            force: regenerar thumbnails existentes también
            
        Returns:
            Dict con resultados de la operación
        """
        start_time = time.time()
        logger.info("🚀 Regenerando thumbnails OPTIMIZADO...")
        
        # 🔧 CORREGIDO: Usar configuración del .env en lugar de forzar ultra_fast
        logger.info(f"🎯 Configuración aplicada: Tamaño {self.thumbnail_generator.thumbnail_size}, Calidad {self.thumbnail_generator.quality}%, Validación: {self.thumbnail_generator.enable_validation}")
        
        # 🔍 PASO 1: Obtener videos que necesitan regeneración (consulta optimizada)
        logger.info("📊 Identificando videos que necesitan regeneración...")
        videos_to_regenerate = self._get_videos_for_regeneration_optimized(force)
        
        if not videos_to_regenerate:
            logger.info("✅ Todos los videos tienen thumbnails válidos")
            return {
                'success': True,
                'total_videos': 0,
                'successful': 0,
                'failed': 0,
                'duration': 0.0,
                'message': "Todos los videos tienen thumbnails válidos"
            }
        
        logger.info(f"Videos para regenerar: {len(videos_to_regenerate)}")
        
        # 🎯 PASO 2: Priorizar videos con personajes detectados
        prioritized_videos = self._prioritize_videos_with_characters(videos_to_regenerate)
        logger.info(f"📈 Videos priorizados: {len(prioritized_videos['priority'])} con personajes, {len(prioritized_videos['normal'])} normales")
        
        # Combinar videos priorizados
        ordered_videos = prioritized_videos['priority'] + prioritized_videos['normal']
        
        # 🧹 PASO 3: Limpiar thumbnails corruptos/inválidos
        logger.info("🧹 Limpiando thumbnails corruptos...")
        cleaned_count = self._clean_corrupt_thumbnails(ordered_videos)
        if cleaned_count > 0:
            logger.info(f"✅ Thumbnails corruptos eliminados: {cleaned_count}")
        
        # ⚡ PASO 4: Regeneración en paralelo con ThreadPoolExecutor
        logger.info("⚡ Regenerando thumbnails en paralelo...")
        success, failed = self._regenerate_thumbnails_parallel(ordered_videos, force)
        
        # 📊 PASO 5: Métricas finales
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ Thumbnails regenerados OPTIMIZADO en {duration:.2f}s")
        logger.info(f"   📊 Resultados: {success} exitosos, {failed} fallidos")
        if cleaned_count > 0:
            logger.info(f"   🧹 Limpiezas: {cleaned_count} thumbnails corruptos eliminados")
        if success > 0:
            logger.info(f"   ⚡ Throughput: {success/duration:.1f} thumbnails/segundo")
        
        # 🔧 PASO 6: Optimización automática de BD si fue procesamiento masivo
        if success > 20:
            logger.info("🔧 Optimizando base de datos...")
            try:
                self._optimize_database()
                logger.info("✅ Base de datos optimizada")
            except Exception as e:
                logger.warning(f"Advertencia optimizando BD: {e}")
        
        return {
            'success': True,
            'total_videos': len(ordered_videos),
            'successful': success,
            'failed': failed,
            'duration': duration,
            'cleaned_corrupt': cleaned_count,
            'throughput': success/duration if success > 0 else 0
        }
    
    def regenerate_thumbnails_by_ids(self, video_ids: List[int], force: bool = False) -> Dict[str, Any]:
        """
        🆕 NUEVA: Regenerar thumbnails para IDs específicos (para app web)
        
        Args:
            video_ids: Lista de IDs de videos
            force: regenerar thumbnails existentes también
            
        Returns:
            Dict con resultados de la operación
        """
        start_time = time.time()
        logger.info(f"🚀 Regenerando thumbnails para {len(video_ids)} videos específicos...")
        
        # Obtener información de videos por IDs
        videos_data = self._get_videos_by_ids(video_ids)
        
        if not videos_data:
            return {
                'success': False,
                'error': 'No se encontraron videos válidos para los IDs proporcionados',
                'total_videos': 0,
                'successful': 0,
                'failed': 0
            }
        
        logger.info(f"Videos encontrados: {len(videos_data)}")
        
        # Filtrar videos que necesitan regeneración
        videos_to_process = []
        for video in videos_data:
            file_path = Path(video['file_path'])
            
            # Verificar que el archivo existe
            if not file_path.exists():
                logger.warning(f"Archivo no existe: {file_path}")
                continue
            
            # Verificar si necesita regeneración
            needs_regeneration = force
            if not needs_regeneration:
                thumbnail_path = video.get('thumbnail_path')
                if not thumbnail_path:
                    needs_regeneration = True
                else:
                    thumb_path = Path(thumbnail_path)
                    if not thumb_path.exists():
                        needs_regeneration = True
                    elif self._is_thumbnail_corrupt(thumb_path):
                        needs_regeneration = True
            
            if needs_regeneration:
                videos_to_process.append(video)
        
        if not videos_to_process:
            return {
                'success': True,
                'total_videos': len(videos_data),
                'successful': 0,
                'failed': 0,
                'duration': 0.0,
                'message': "Todos los videos ya tienen thumbnails válidos"
            }
        
        # Regenerar thumbnails en paralelo
        logger.info(f"⚡ Regenerando {len(videos_to_process)} thumbnails...")
        success, failed = self._regenerate_thumbnails_parallel(videos_to_process, force)
        
        # Métricas finales
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ Thumbnails regenerados para IDs específicos en {duration:.2f}s")
        logger.info(f"   📊 Resultados: {success} exitosos, {failed} fallidos")
        
        return {
            'success': True,
            'total_videos': len(videos_data),
            'successful': success,
            'failed': failed,
            'duration': duration,
            'video_ids_processed': [v['id'] for v in videos_to_process]
        }
    
    def clean_thumbnails(self, force: bool = False) -> Dict[str, Any]:
        """
        🧹 Limpiar thumbnails huérfanos (sin video asociado)
        
        Args:
            force: eliminar sin confirmación
            
        Returns:
            Dict con resultados de la operación
        """
        logger.info("🧹 Limpiando thumbnails huérfanos...")
        
        # Obtener videos en BD
        videos = self.db.get_videos()
        valid_thumbnails = set()
        
        for video in videos:
            if video.get('thumbnail_path'):
                thumb_name = Path(video['thumbnail_path']).name
                valid_thumbnails.add(thumb_name)
        
        # Encontrar thumbnails huérfanos
        orphaned = []
        total_size = 0
        
        # Obtener ruta de thumbnails desde configuración centralizada
        if not config.THUMBNAILS_PATH.exists():
            logger.warning(f"Directorio de thumbnails no encontrado: {config.THUMBNAILS_PATH}")
            return {
                'success': True,
                'orphaned_count': 0,
                'total_size_mb': 0,
                'deleted_count': 0,
                'message': f"Directorio de thumbnails no encontrado: {config.THUMBNAILS_PATH}"
            }
        
        for thumb_path in config.THUMBNAILS_PATH.glob('*.jpg'):
            if thumb_path.name not in valid_thumbnails:
                orphaned.append(thumb_path)
                total_size += thumb_path.stat().st_size
        
        if not orphaned:
            logger.info("✅ No se encontraron thumbnails huérfanos")
            return {
                'success': True,
                'orphaned_count': 0,
                'total_size_mb': 0,
                'deleted_count': 0,
                'message': "No se encontraron thumbnails huérfanos"
            }
        
        logger.info(f"Encontrados {len(orphaned)} thumbnails huérfanos ({total_size / 1024 / 1024:.1f} MB)")
        
        if not force:
            # En modo interactivo, solo reportar
            return {
                'success': True,
                'orphaned_count': len(orphaned),
                'total_size_mb': total_size / 1024 / 1024,
                'deleted_count': 0,
                'message': f"Encontrados {len(orphaned)} thumbnails huérfanos, usar force=True para eliminar"
            }
        
        # Eliminar thumbnails
        deleted = 0
        for thumb_path in orphaned:
            try:
                thumb_path.unlink()
                deleted += 1
            except Exception as e:
                logger.warning(f"Error eliminando {thumb_path}: {e}")
        
        logger.info(f"✅ Eliminados {deleted} thumbnails huérfanos")
        
        return {
            'success': True,
            'orphaned_count': len(orphaned),
            'total_size_mb': total_size / 1024 / 1024,
            'deleted_count': deleted,
            'message': f"Eliminados {deleted} thumbnails huérfanos"
        }
    
    def get_thumbnail_stats(self, video_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        📊 Obtener estadísticas de thumbnails
        
        Args:
            video_ids: IDs específicos o None para estadísticas globales
            
        Returns:
            Dict con estadísticas de thumbnails
        """
        logger.info("📊 Obteniendo estadísticas de thumbnails...")
        
        # Construir consulta según parámetros
        if video_ids:
            placeholders = ','.join(['?' for _ in video_ids])
            query = f"""
            SELECT 
                COUNT(*) as total,
                COUNT(thumbnail_path) as with_thumbnails,
                COUNT(*) - COUNT(thumbnail_path) as without_thumbnails
            FROM videos 
            WHERE id IN ({placeholders})
            """
            params = video_ids
        else:
            query = """
            SELECT 
                COUNT(*) as total,
                COUNT(thumbnail_path) as with_thumbnails,
                COUNT(*) - COUNT(thumbnail_path) as without_thumbnails
            FROM videos
            """
            params = []
        
        # Ejecutar consulta
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, params)
            stats = dict(cursor.fetchone())
        
        # Verificar thumbnails existentes en disco
        valid_thumbnails = 0
        corrupt_thumbnails = 0
        missing_thumbnails = 0
        
        if video_ids:
            videos_data = self._get_videos_by_ids(video_ids)
        else:
            videos_data = self.db.get_videos()
        
        for video in videos_data:
            thumbnail_path = video.get('thumbnail_path')
            if thumbnail_path:
                thumb_path = Path(thumbnail_path)
                if thumb_path.exists():
                    if self._is_thumbnail_corrupt(thumb_path):
                        corrupt_thumbnails += 1
                    else:
                        valid_thumbnails += 1
                else:
                    missing_thumbnails += 1
        
        # Calcular estadísticas adicionales
        total_videos = stats['total']
        coverage_percentage = (valid_thumbnails / total_videos * 100) if total_videos > 0 else 0
        
        # Mostrar estadísticas en consola
        logger.info(f"✅ Estadísticas de thumbnails:")
        logger.info(f"   📊 Total de videos: {total_videos}")
        logger.info(f"   🎨 Con thumbnails válidos: {valid_thumbnails} ({coverage_percentage:.1f}%)")
        logger.info(f"   ❌ Sin thumbnails: {stats['without_thumbnails']}")
        
        if missing_thumbnails > 0:
            logger.info(f"   📍 Referencias en BD pero archivos faltantes: {missing_thumbnails}")
        if corrupt_thumbnails > 0:
            logger.info(f"   🚫 Thumbnails corruptos: {corrupt_thumbnails}")
        
        # Status general
        if coverage_percentage >= 90:
            status_icon = "✅"
            status = "Excelente"
        elif coverage_percentage >= 70:
            status_icon = "🟡" 
            status = "Bueno"
        elif coverage_percentage >= 50:
            status_icon = "🟠"
            status = "Regular"
        else:
            status_icon = "🔴"
            status = "Necesita atención"
        
        logger.info(f"   {status_icon} Estado general: {status}")
        
        if coverage_percentage < 90:
            logger.info(f"\n💡 Para mejorar la cobertura:")
            logger.info(f"   python main.py populate-thumbnails")
            if corrupt_thumbnails > 0:
                logger.info(f"   python main.py regenerate-thumbnails --force")
        
        return {
            'success': True,
            'total_videos': total_videos,
            'with_thumbnails_db': stats['with_thumbnails'],
            'without_thumbnails_db': stats['without_thumbnails'],
            'valid_thumbnails': valid_thumbnails,
            'corrupt_thumbnails': corrupt_thumbnails,
            'missing_thumbnails': missing_thumbnails,
            'coverage_percentage': coverage_percentage,
            'video_ids_analyzed': len(video_ids) if video_ids else total_videos,
            'status': status,
            'message': f'Cobertura de thumbnails: {coverage_percentage:.1f}% ({status})'
        }
    
    def populate_thumbnails(self, platform: Optional[str] = None, limit: Optional[int] = None, force: bool = False) -> Dict[str, Any]:
        """
        🚀 OPTIMIZADO: Generación ultra-rápida de thumbnails con procesamiento paralelo
        
        Args:
            platform: plataforma específica o None para todas
            limit: número máximo de thumbnails a generar
            force: regenerar thumbnails existentes
            
        Returns:
            Dict con resultados de la operación
        """
        start_time = time.time()
        logger.info("🚀 Generando thumbnails OPTIMIZADO...")
        
        # 🔧 CORREGIDO: Usar configuración del .env en lugar de forzar ultra_fast
        logger.info(f"🎯 Configuración aplicada: Tamaño {self.thumbnail_generator.thumbnail_size}, Calidad {self.thumbnail_generator.quality}%, Validación: {self.thumbnail_generator.enable_validation}")
        logger.info(f"🧠 Optimización RAM: Cache {self.thumbnail_generator.max_cache_size} frames, Pre-carga habilitada: {self.thumbnail_generator.use_ram_optimization}")
        
        # 🔍 PASO 1: Obtener videos que necesitan thumbnails (consulta optimizada)
        logger.info("📊 Obteniendo videos que necesitan thumbnails...")
        videos_needing_thumbs = self._get_videos_needing_thumbnails_optimized(platform, limit, force)
        
        if not videos_needing_thumbs:
            logger.info("✅ Todos los videos ya tienen thumbnails")
            return {
                'success': True,
                'total_videos': 0,
                'successful': 0,
                'failed': 0,
                'duration': 0.0,
                'message': "Todos los videos ya tienen thumbnails"
            }
        
        logger.info(f"Videos que necesitan thumbnails: {len(videos_needing_thumbs)}")
        
        # 🎯 PASO 2: Priorizar videos con personajes detectados
        prioritized_videos = self._prioritize_videos_with_characters(videos_needing_thumbs)
        logger.info(f"📈 Videos priorizados: {len(prioritized_videos['priority'])} con personajes, {len(prioritized_videos['normal'])} normales")
        
        # Combinar videos priorizados
        ordered_videos = prioritized_videos['priority'] + prioritized_videos['normal']
        
        # ⚡ PASO 3: Generación en paralelo con ThreadPoolExecutor
        logger.info("⚡ Generando thumbnails en paralelo...")
        success, failed = self._generate_thumbnails_parallel(ordered_videos, force)
        
        # 📊 PASO 4: Métricas finales
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ Thumbnails generados OPTIMIZADO en {duration:.2f}s")
        logger.info(f"   📊 Resultados: {success} exitosos, {failed} fallidos")
        if success > 0:
            logger.info(f"   ⚡ Throughput: {success/duration:.1f} thumbnails/segundo")
        
        # 🔧 PASO 5: Optimización automática de BD si fue procesamiento masivo
        if success > 20:
            logger.info("🔧 Optimizando base de datos...")
            try:
                self._optimize_database()
                logger.info("✅ Base de datos optimizada")
            except Exception as e:
                logger.warning(f"Advertencia optimizando BD: {e}")
        
        return {
            'success': True,
            'total_videos': len(ordered_videos),
            'successful': success,
            'failed': failed,
            'duration': duration,
            'throughput': success/duration if success > 0 else 0
        }
    
    def clear_thumbnails(self, platform: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """
        🗑️ Limpiar thumbnails de plataforma específica
        
        Args:
            platform: plataforma específica o None para todas
            force: eliminar sin confirmación
            
        Returns:
            Dict con resultados de la operación
        """
        logger.info(f"🗑️ Limpiando thumbnails de plataforma: {platform or 'todas'}")
        
        # Obtener videos de la plataforma
        if platform:
            with self.db.get_connection() as conn:
                cursor = conn.execute("SELECT id, thumbnail_path FROM videos WHERE platform = ?", (platform,))
                videos = [dict(row) for row in cursor.fetchall()]
        else:
            with self.db.get_connection() as conn:
                cursor = conn.execute("SELECT id, thumbnail_path FROM videos")
                videos = [dict(row) for row in cursor.fetchall()]
        
        # Contar thumbnails a eliminar
        thumbnails_to_delete = []
        for video in videos:
            if video.get('thumbnail_path'):
                thumb_path = Path(video['thumbnail_path'])
                if thumb_path.exists():
                    thumbnails_to_delete.append((video['id'], thumb_path))
        
        if not thumbnails_to_delete:
            return {
                'success': True,
                'deleted_count': 0,
                'message': f"No se encontraron thumbnails para eliminar en {platform or 'todas las plataformas'}"
            }
        
        if not force:
            return {
                'success': True,
                'deleted_count': 0,
                'thumbnails_found': len(thumbnails_to_delete),
                'message': f"Encontrados {len(thumbnails_to_delete)} thumbnails, usar force=True para eliminar"
            }
        
        # Eliminar thumbnails
        deleted = 0
        for video_id, thumb_path in thumbnails_to_delete:
            try:
                thumb_path.unlink()
                # Limpiar referencia en BD
                with self.db.get_connection() as conn:
                    conn.execute("UPDATE videos SET thumbnail_path = NULL WHERE id = ?", (video_id,))
                deleted += 1
            except Exception as e:
                logger.warning(f"Error eliminando thumbnail {thumb_path}: {e}")
        
        logger.info(f"✅ Eliminados {deleted} thumbnails de {platform or 'todas las plataformas'}")
        
        return {
            'success': True,
            'deleted_count': deleted,
            'thumbnails_found': len(thumbnails_to_delete),
            'message': f"Eliminados {deleted} thumbnails"
        }
    
    # Métodos privados auxiliares
    
    def _get_videos_by_ids(self, video_ids: List[int]) -> List[Dict]:
        """Obtener información de videos por IDs"""
        if not video_ids:
            return []
        
        placeholders = ','.join(['?' for _ in video_ids])
        query = f"""
        SELECT id, file_path, file_name, thumbnail_path, detected_characters, platform
        FROM videos 
        WHERE id IN ({placeholders})
        AND file_path IS NOT NULL
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, video_ids)
            return [dict(row) for row in cursor.fetchall()]
    
    def _get_videos_for_regeneration_optimized(self, force: bool = False) -> List[Dict]:
        """🚀 OPTIMIZADO: Obtener videos que necesitan regeneración con consulta SQL eficiente"""
        # Construir consulta SQL optimizada
        if force:
            # Si force=True, regenerar todos los videos
            query = """
            SELECT id, file_path, file_name, thumbnail_path, detected_characters, platform
            FROM videos 
            WHERE file_path IS NOT NULL
            ORDER BY 
                CASE 
                    WHEN detected_characters IS NOT NULL AND detected_characters != '[]' 
                    THEN 0 ELSE 1 
                END,
                id
            """
            params = []
        else:
            # Solo videos sin thumbnails o con thumbnails inválidos
            query = """
            SELECT id, file_path, file_name, thumbnail_path, detected_characters, platform
            FROM videos 
            WHERE file_path IS NOT NULL 
            AND (thumbnail_path IS NULL OR thumbnail_path = '')
            ORDER BY 
                CASE 
                    WHEN detected_characters IS NOT NULL AND detected_characters != '[]' 
                    THEN 0 ELSE 1 
                END,
                id
            """
            params = []
        
        # Ejecutar consulta
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, params)
            videos = [dict(row) for row in cursor.fetchall()]
        
        # Filtrar videos por existencia de archivo y validez de thumbnail
        valid_videos = []
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        
        for video in videos:
            file_path = Path(video['file_path'])
            
            # Verificar que el archivo de video existe
            if not file_path.exists():
                logger.debug(f"Archivo de video no existe: {file_path}")
                continue
            
            # Verificar que es un video (no imagen)
            if file_path.suffix.lower() not in video_extensions:
                continue
            
            # Verificar si necesita regeneración de thumbnail
            needs_regeneration = force
            
            if not needs_regeneration:
                thumbnail_path = video.get('thumbnail_path')
                if not thumbnail_path:
                    needs_regeneration = True
                else:
                    thumb_path = Path(thumbnail_path)
                    if not thumb_path.exists():
                        needs_regeneration = True
                    elif self._is_thumbnail_corrupt(thumb_path):
                        needs_regeneration = True
            
            if needs_regeneration:
                valid_videos.append(video)
        
        return valid_videos
    
    def _get_videos_needing_thumbnails_optimized(self, platform: Optional[str] = None, limit: Optional[int] = None, force: bool = False) -> List[Dict]:
        """🚀 OPTIMIZADO: Obtener videos que necesitan thumbnails con consulta SQL eficiente"""
        # Construir consulta SQL optimizada
        query = """
        SELECT id, file_path, file_name, thumbnail_path, detected_characters, platform
        FROM videos 
        WHERE 1=1
        """
        params = []
        
        # Filtrar por plataforma si se especifica
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        
        # Filtrar por videos que necesitan thumbnails
        if not force:
            query += " AND (thumbnail_path IS NULL OR thumbnail_path = '')"
        
        # Aplicar límite
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        # Ejecutar consulta
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, params)
            videos = [dict(row) for row in cursor.fetchall()]
        
        # Filtrar videos por existencia de archivo y extensión
        valid_videos = []
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        
        for video in videos:
            file_path = Path(video['file_path'])
            
            # Verificar que el archivo existe
            if not file_path.exists():
                logger.debug(f"Archivo no existe: {file_path}")
                continue
            
            # Verificar que es un video (no imagen)
            if file_path.suffix.lower() not in video_extensions:
                continue
            
            # Verificar si necesita thumbnail (para force=True)
            if force or not video.get('thumbnail_path') or not Path(str(video['thumbnail_path'])).exists():
                valid_videos.append(video)
        
        return valid_videos
    
    def _prioritize_videos_with_characters(self, videos: List[Dict]) -> Dict[str, List[Dict]]:
        """🎯 Priorizar videos con personajes detectados para thumbnails"""
        priority_videos = []
        normal_videos = []
        
        for video in videos:
            detected_characters = video.get('detected_characters')
            
            # Verificar si tiene personajes detectados
            has_characters = False
            if detected_characters:
                try:
                    import json
                    characters = json.loads(detected_characters) if isinstance(detected_characters, str) else detected_characters
                    has_characters = len(characters) > 0
                except:
                    has_characters = False
            
            if has_characters:
                priority_videos.append(video)
            else:
                normal_videos.append(video)
        
        return {'priority': priority_videos, 'normal': normal_videos}
    
    def _is_thumbnail_corrupt(self, thumbnail_path: Path) -> bool:
        """Verificar si un thumbnail está corrupto"""
        try:
            thumb_path = Path(thumbnail_path)
            
            # Verificar que el archivo existe
            if not thumb_path.exists():
                return True
            
            # Verificar tamaño mínimo
            if thumb_path.stat().st_size < 1024:  # < 1KB
                return True
            
            # Verificar que es una imagen válida
            try:
                from PIL import Image
                with Image.open(thumb_path) as img:
                    img.verify()
                return False
            except:
                return True
                
        except Exception:
            return True
    
    def _clean_corrupt_thumbnails(self, videos: List[Dict]) -> int:
        """🧹 Limpiar thumbnails corruptos de una lista de videos"""
        cleaned_count = 0
        
        for video in videos:
            thumbnail_path = video.get('thumbnail_path')
            if thumbnail_path:
                thumb_path = Path(thumbnail_path)
                if thumb_path.exists() and self._is_thumbnail_corrupt(thumb_path):
                    try:
                        thumb_path.unlink()
                        cleaned_count += 1
                        logger.debug(f"Thumbnail corrupto eliminado: {thumb_path}")
                    except Exception as e:
                        logger.warning(f"Error eliminando thumbnail corrupto {thumb_path}: {e}")
        
        return cleaned_count
    
    def _regenerate_thumbnails_parallel(self, videos: List[Dict], force: bool = False) -> Tuple[int, int]:
        """⚡ Regenerar thumbnails en paralelo con ThreadPoolExecutor"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        success = 0
        failed = 0
        # Optimizar workers para I/O bound (thumbnail generation)
        cpu_count = os.cpu_count() or 4
        # Para thumbnail generation, usar menos workers para evitar thrashing
        max_workers = min(4, len(videos))
        
        def regenerate_single_thumbnail(video_data):
            """Regenerar thumbnail para un video individual (sin actualizar BD)"""
            try:
                video_path = Path(video_data['file_path'])
                
                # Verificar que el archivo existe
                if not video_path.exists():
                    return {'success': False, 'error': f"Video no existe: {video_path}", 'video_id': video_data['id']}
                
                # Generar thumbnail (siempre con force=True para regeneración)
                thumbnail_path = self.thumbnail_generator.generate_thumbnail(video_path, force_regenerate=True)
                
                if thumbnail_path:
                    # NO actualizar BD aquí - acumular para batch update
                    return {
                        'success': True, 
                        'path': str(thumbnail_path), 
                        'video_name': video_path.name,
                        'video_id': video_data['id'],
                        'thumbnail_path': str(thumbnail_path)
                    }
                else:
                    return {'success': False, 'error': f"Falló regeneración para {video_path.name}", 'video_id': video_data['id']}
                    
            except Exception as e:
                return {'success': False, 'error': f"Error con {video_data.get('file_name', 'unknown')}: {e}", 'video_id': video_data['id']}
        
        # Procesamiento en paralelo con batch updates
        batch_updates = []  # Acumular updates para BD
        batch_size = 25  # Actualizar BD cada 25 thumbnails
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas
            future_to_video = {
                executor.submit(regenerate_single_thumbnail, video): video 
                for video in videos
            }
            
            # Recopilar resultados conforme se completan
            for i, future in enumerate(as_completed(future_to_video), 1):
                try:
                    result = future.result()
                    
                    if result['success']:
                        success += 1
                        logger.info(f"✓ {result['video_name']}")
                        
                        # Acumular update para batch
                        batch_updates.append({
                            'video_id': result['video_id'],
                            'updates': {'thumbnail_path': result['thumbnail_path']}
                        })
                        
                    else:
                        failed += 1
                        logger.warning(f"✗ {result['error']}")
                    
                    # Batch update cada 25 thumbnails o al final
                    if len(batch_updates) >= batch_size or i == len(videos):
                        if batch_updates:
                            try:
                                batch_success, batch_failed = self.db.batch_update_videos(batch_updates)
                                logger.debug(f"🔄 Batch update: {batch_success} exitosos, {batch_failed} fallidos")
                                batch_updates = []  # Limpiar batch
                            except Exception as e:
                                logger.warning(f"Error en batch update: {e}")
                    
                    # Mostrar progreso cada 10 thumbnails
                    if i % 10 == 0 or i == len(videos):
                        logger.info(f"⚡ Progreso: {i}/{len(videos)} ({i/len(videos)*100:.1f}%) - {success} exitosos, {failed} fallidos")
                        
                except Exception as e:
                    failed += 1
                    video = future_to_video[future]
                    logger.error(f"Error procesando {video.get('file_name', 'unknown')}: {e}")
        
        # Procesar cualquier update restante
        if batch_updates:
            try:
                batch_success, batch_failed = self.db.batch_update_videos(batch_updates)
                logger.info(f"🔄 Batch update final: {batch_success} exitosos, {batch_failed} fallidos")
            except Exception as e:
                logger.warning(f"Error en batch update final: {e}")
        
        return success, failed
    
    def _generate_thumbnails_parallel(self, videos: List[Dict], force: bool = False) -> Tuple[int, int]:
        """⚡ Generar thumbnails en paralelo con ThreadPoolExecutor"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        success = 0
        failed = 0
        # Optimizar workers para I/O bound (thumbnail generation)
        cpu_count = os.cpu_count() or 4
        # Para thumbnail generation, usar menos workers para evitar thrashing
        max_workers = min(4, len(videos))
        
        def generate_single_thumbnail(video_data):
            """Generar thumbnail para un video individual"""
            try:
                video_path = Path(video_data['file_path'])
                
                # Verificar que el archivo existe
                if not video_path.exists():
                    return {'success': False, 'error': f"Video no existe: {video_path}", 'video_id': video_data['id']}
                
                # Generar thumbnail
                thumbnail_path = self.thumbnail_generator.generate_thumbnail(video_path, force_regenerate=force)
                
                if thumbnail_path:
                    return {
                        'success': True, 
                        'path': str(thumbnail_path), 
                        'video_name': video_path.name,
                        'video_id': video_data['id'],
                        'thumbnail_path': str(thumbnail_path)
                    }
                else:
                    return {'success': False, 'error': f"Falló generación para {video_path.name}", 'video_id': video_data['id']}
                    
            except Exception as e:
                return {'success': False, 'error': f"Error con {video_data.get('file_name', 'unknown')}: {e}", 'video_id': video_data['id']}
        
        # Procesamiento en paralelo con batch updates
        batch_updates = []  # Acumular updates para BD
        batch_size = 25  # Actualizar BD cada 25 thumbnails
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas
            future_to_video = {
                executor.submit(generate_single_thumbnail, video): video 
                for video in videos
            }
            
            # Recopilar resultados conforme se completan
            for i, future in enumerate(as_completed(future_to_video), 1):
                try:
                    result = future.result()
                    
                    if result['success']:
                        success += 1
                        logger.info(f"✓ {result['video_name']}")
                        
                        # Acumular update para batch
                        batch_updates.append({
                            'video_id': result['video_id'],
                            'updates': {'thumbnail_path': result['thumbnail_path']}
                        })
                        
                    else:
                        failed += 1
                        logger.warning(f"✗ {result['error']}")
                    
                    # Batch update cada 25 thumbnails o al final
                    if len(batch_updates) >= batch_size or i == len(videos):
                        if batch_updates:
                            try:
                                batch_success, batch_failed = self.db.batch_update_videos(batch_updates)
                                logger.debug(f"🔄 Batch update: {batch_success} exitosos, {batch_failed} fallidos")
                                batch_updates = []  # Limpiar batch
                            except Exception as e:
                                logger.warning(f"Error en batch update: {e}")
                    
                    # Mostrar progreso cada 10 thumbnails
                    if i % 10 == 0 or i == len(videos):
                        logger.info(f"⚡ Progreso: {i}/{len(videos)} ({i/len(videos)*100:.1f}%) - {success} exitosos, {failed} fallidos")
                        
                except Exception as e:
                    failed += 1
                    video = future_to_video[future]
                    logger.error(f"Error procesando {video.get('file_name', 'unknown')}: {e}")
        
        # Procesar cualquier update restante
        if batch_updates:
            try:
                batch_success, batch_failed = self.db.batch_update_videos(batch_updates)
                logger.info(f"🔄 Batch update final: {batch_success} exitosos, {batch_failed} fallidos")
            except Exception as e:
                logger.warning(f"Error en batch update final: {e}")
        
        return success, failed
    
    def _optimize_database(self):
        """Optimizar base de datos SQLite"""
        logger.info("Optimizando base de datos...")
        
        try:
            with self.db.get_connection() as conn:
                # VACUUM para compactar BD
                conn.execute('VACUUM')
                
                # ANALYZE para optimizar consultas
                conn.execute('ANALYZE')
                
                # Obtener estadísticas
                cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM videos")
                video_count = cursor.fetchone()[0]
            
            logger.info(f"✅ Base de datos optimizada")
            logger.info(f"   Tamaño: {db_size / 1024 / 1024:.1f} MB")
            logger.info(f"   Videos: {video_count}")
            
        except Exception as e:
            logger.error(f"Error optimizando base de datos: {e}")


# Funciones de conveniencia para compatibilidad
def regenerate_thumbnails(force: bool = False) -> Dict[str, Any]:
    """Función de conveniencia para regenerar thumbnails"""
    ops = ThumbnailOperations()
    return ops.regenerate_thumbnails(force)

def regenerate_thumbnails_by_ids(video_ids: List[int], force: bool = False) -> Dict[str, Any]:
    """Función de conveniencia para regenerar thumbnails por IDs"""
    ops = ThumbnailOperations()
    return ops.regenerate_thumbnails_by_ids(video_ids, force)

def clean_thumbnails(force: bool = False) -> Dict[str, Any]:
    """Función de conveniencia para limpiar thumbnails huérfanos"""
    ops = ThumbnailOperations()
    return ops.clean_thumbnails(force)

def get_thumbnail_stats(video_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """Función de conveniencia para obtener estadísticas de thumbnails"""
    ops = ThumbnailOperations()
    return ops.get_thumbnail_stats(video_ids)

def populate_thumbnails(platform: Optional[str] = None, limit: Optional[int] = None, force: bool = False) -> Dict[str, Any]:
    """Función de conveniencia para poblar thumbnails"""
    ops = ThumbnailOperations()
    return ops.populate_thumbnails(platform, limit, force)

def clear_thumbnails(platform: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """Función de conveniencia para limpiar thumbnails"""
    ops = ThumbnailOperations()
    return ops.clear_thumbnails(platform, force)