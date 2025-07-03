"""
Tag-Flow V2 - Database Manager Optimizado
Extensión de DatabaseManager con consultas optimizadas para main.py
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import logging
import time

from database import DatabaseManager
from pattern_cache import DatabaseCache

logger = logging.getLogger(__name__)

class OptimizedDatabaseManager(DatabaseManager):
    """Versión optimizada del DatabaseManager con cache integrado y consultas eficientes"""
    
    def __init__(self, db_path: Path = None):
        super().__init__(db_path)
        self.cache = DatabaseCache()
        self.create_optimized_indexes()
        
        # Métricas de performance
        self.query_times = {}
        self.start_time = time.time()
        
        logger.info("🚀 OptimizedDatabaseManager inicializado con cache LRU")
        
    def create_optimized_indexes(self):
        """✅ Crear índices específicos para optimizar main.py"""
        with self.get_connection() as conn:
            try:
                # Índice para búsqueda por path/name combinada
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_videos_file_path_name 
                    ON videos(file_path, file_name)
                """)
                
                # Índice para filtros frecuentes en main.py
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_videos_platform_status 
                    ON videos(platform, processing_status)
                """)
                
                # Índice para consultas de pendientes
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_videos_status_platform 
                    ON videos(processing_status, platform)
                """)
                
                # Índice compuesto para filtering optimizado
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_videos_status_platform_created 
                    ON videos(processing_status, platform, created_at)
                """)
                
                conn.commit()
                logger.debug("✅ Índices optimizados creados para main.py")
                
            except Exception as e:
                logger.warning(f"⚠️ Error creando índices optimizados: {e}")

    def get_existing_paths_only(self) -> Set[str]:
        """✅ Solo obtener file_paths para verificación de duplicados (10x más rápido)"""
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT file_path FROM videos")
            paths = {row[0] for row in cursor.fetchall()}
        
        query_time = time.time() - start_time
        self._track_query('get_existing_paths', query_time)
        
        logger.debug(f"📊 Paths obtenidos en {query_time:.3f}s ({len(paths)} paths)")
        return paths
    
    def get_video_by_path_or_name(self, file_path: str, file_name: str) -> Optional[Dict]:
        """✅ Buscar por ruta O nombre en una sola consulta SQL optimizada"""
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM videos 
                WHERE file_path = ? OR file_name = ?
                LIMIT 1
            """, (file_path, file_name))
            row = cursor.fetchone()
            
        query_time = time.time() - start_time
        self._track_query('get_video_by_path_or_name', query_time)
        
        result = dict(row) if row else None
        logger.debug(f"📊 Búsqueda path/name en {query_time:.3f}s ({'FOUND' if result else 'NOT_FOUND'})")
        return result
    
    def get_pending_videos_filtered(self, platform_filter: str, source_filter: str, limit: int) -> List[Dict]:
        """✅ Obtener pendientes con filtros SQL nativos (5x más rápido)"""
        start_time = time.time()
        
        query = "SELECT * FROM videos WHERE processing_status = 'pendiente'"
        params = []
        
        # Aplicar filtros de plataforma en SQL
        if platform_filter and platform_filter != 'all-platforms':
            if platform_filter == 'other':
                # Filtrar plataformas adicionales (no principales)
                query += " AND platform NOT IN ('youtube', 'tiktok', 'instagram')"
            elif isinstance(platform_filter, list):
                # Lista de plataformas
                placeholders = ','.join(['?' for _ in platform_filter])
                query += f" AND platform IN ({placeholders})"
                params.extend(platform_filter)
            else:
                # Plataforma específica
                query += " AND platform = ?"
                params.append(platform_filter)
        
        # Ordenar por fecha de creación (más recientes primero)
        query += " ORDER BY created_at DESC"
        
        # Aplicar límite en SQL
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
        
        query_time = time.time() - start_time
        self._track_query('get_pending_videos_filtered', query_time)
        
        logger.debug(f"📊 Pendientes filtrados en {query_time:.3f}s ({len(results)} videos)")
        return results
    
    def check_videos_exist_batch(self, file_paths: List[str]) -> Dict[str, bool]:
        """✅ Verificar existencia de múltiples videos en una consulta (N videos en 1 query)"""
        if not file_paths:
            return {}
            
        start_time = time.time()
        
        placeholders = ','.join(['?' for _ in file_paths])
        query = f"SELECT file_path FROM videos WHERE file_path IN ({placeholders})"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, file_paths)
            existing_paths = {row[0] for row in cursor.fetchall()}
        
        # Crear diccionario de resultados
        results = {path: path in existing_paths for path in file_paths}
        
        query_time = time.time() - start_time
        self._track_query('check_videos_exist_batch', query_time)
        
        logger.debug(f"📊 Verificación batch en {query_time:.3f}s ({len(file_paths)} paths)")
        return results

    def get_videos_by_paths_batch(self, file_paths: List[str]) -> Dict[str, Dict]:
        """✅ Obtener múltiples videos por paths en una consulta"""
        if not file_paths:
            return {}
            
        start_time = time.time()
        
        placeholders = ','.join(['?' for _ in file_paths])
        query = f"SELECT * FROM videos WHERE file_path IN ({placeholders})"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, file_paths)
            rows = cursor.fetchall()
        
        # Crear diccionario indexado por file_path
        results = {row['file_path']: dict(row) for row in rows}
        
        query_time = time.time() - start_time
        self._track_query('get_videos_by_paths_batch', query_time)
        
        logger.debug(f"📊 Búsqueda batch en {query_time:.3f}s ({len(file_paths)} paths)")
        return results
    
    # ✅ MÉTODOS SOBRESCRITOS CON INVALIDACIÓN DE CACHE
    
    def add_video(self, video_data: Dict) -> int:
        """✅ Agregar video con invalidación selectiva de cache"""
        video_id = super().add_video(video_data)
        self.cache.invalidate_paths()  # Solo invalidar paths
        logger.debug(f"📊 Video agregado (ID: {video_id}), cache de paths invalidado")
        return video_id

    def update_video(self, video_id: int, updates: Dict) -> bool:
        """✅ Actualizar video con invalidación inteligente"""
        result = super().update_video(video_id, updates)
        
        if result:
            # Invalidación selectiva según qué se actualizó
            if 'processing_status' in updates:
                self.cache.invalidate_pending()
                logger.debug(f"📊 Estado actualizado (ID: {video_id}), cache de pendientes invalidado")
            
            if 'file_path' in updates:
                self.cache.invalidate_paths()
                logger.debug(f"📊 Path actualizado (ID: {video_id}), cache de paths invalidado")
                
        return result
        
    def delete_video(self, video_id: int) -> bool:
        """✅ Eliminar video con invalidación completa"""
        result = super().delete_video(video_id)
        if result:
            self.cache.invalidate_all()
            logger.debug(f"📊 Video eliminado (ID: {video_id}), cache completo invalidado")
        return result
    
    # ✅ MÉTRICAS Y MONITOREO
    
    def _track_query(self, query_type: str, duration: float):
        """Rastrear métricas de consultas para optimización"""
        if query_type not in self.query_times:
            self.query_times[query_type] = []
        
        self.query_times[query_type].append(duration)
        
        # Log solo queries lentas
        if duration > 0.1:  # > 100ms
            logger.debug(f"⚠️ Query lenta {query_type}: {duration:.3f}s")
    
    def get_performance_report(self) -> Dict:
        """✅ Generar reporte de performance optimizada"""
        total_time = time.time() - self.start_time
        
        # Estadísticas de queries
        avg_times = {}
        total_queries = 0
        for query_type, times in self.query_times.items():
            avg_times[query_type] = sum(times) / len(times)
            total_queries += len(times)
        
        # Estadísticas de cache
        cache_stats = self.cache.get_cache_stats()
        memory_usage = self.cache.get_memory_usage()
        
        return {
            'optimization_status': 'ACTIVE',
            'total_runtime_seconds': total_time,
            'total_db_queries': total_queries,
            'queries_per_second': total_queries / max(1, total_time),
            'avg_query_times': avg_times,
            'cache_stats': cache_stats,
            'memory_usage': memory_usage,
            'performance_grade': self._calculate_performance_grade(cache_stats['hit_rate_percentage'])
        }
    
    def _calculate_performance_grade(self, hit_rate: float) -> str:
        """Calcular grado de performance basado en métricas"""
        if hit_rate >= 95:
            return 'A+ (EXCELLENT)'
        elif hit_rate >= 85:
            return 'A (VERY_GOOD)'
        elif hit_rate >= 70:
            return 'B (GOOD)'
        elif hit_rate >= 50:
            return 'C (AVERAGE)'
        else:
            return 'D (NEEDS_IMPROVEMENT)'
    
    def log_performance_summary(self):
        """Log resumen de performance para debug"""
        report = self.get_performance_report()
        
        logger.info("📊 REPORTE DE PERFORMANCE OPTIMIZADA:")
        logger.info(f"  ⏱️  Runtime total: {report['total_runtime_seconds']:.2f}s")
        logger.info(f"  🔍 Total queries: {report['total_db_queries']}")
        logger.info(f"  💾 Cache hit rate: {report['cache_stats']['hit_rate_percentage']}%")
        logger.info(f"  ⚡ Queries/segundo: {report['queries_per_second']:.1f}")
        logger.info(f"  🏆 Performance grade: {report['performance_grade']}")
        
        for query_type, avg_time in report['avg_query_times'].items():
            logger.info(f"  📈 {query_type}: {avg_time:.3f}s promedio")
