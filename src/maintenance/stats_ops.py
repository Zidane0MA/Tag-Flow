"""
📊 Stats Operations - Operaciones Ligeras de Estadísticas
Módulo especializado para estadísticas que NO carga dependencias pesadas
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Configurar logging
logger = logging.getLogger(__name__)

class StatsOperations:
    """
    📊 Operaciones ligeras exclusivamente para estadísticas
    
    Características:
    - NO importa módulos pesados (AI, procesamiento, etc.)
    - Solo queries SQL directas
    - Inicialización ultra-rápida
    - Optimizado para comando db-stats
    """
    
    def __init__(self):
        """Inicialización ligera - NO carga dependencias pesadas"""
        self._db_path = None
        self._connection = None
    
    @property
    def db_path(self) -> Path:
        """Obtener ruta de base de datos de forma ligera"""
        if self._db_path is None:
            # Import ligero solo de config, NO de database module completo
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from config import config
            self._db_path = config.DATABASE_PATH
        return self._db_path
    
    def get_connection(self) -> sqlite3.Connection:
        """Conexión directa a SQLite sin dependencias pesadas"""
        if self._connection is None or self._connection.execute("SELECT 1").fetchone() is None:
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        📊 OPTIMIZADO: Estadísticas de base de datos ultra-ligeras
        
        Sin imports pesados, sin AI, solo SQL puro
        """
        try:
            conn = self.get_connection()
            stats = {
                'timestamp': datetime.now().isoformat(),
                'database_file': str(self.db_path),
                'database_exists': self.db_path.exists(),
                'database_size_mb': 0,
                'total_records': {}
            }
            
            if self.db_path.exists():
                # Tamaño del archivo de base de datos
                stats['database_size_mb'] = round(self.db_path.stat().st_size / (1024 * 1024), 2)
                
                # Estadísticas básicas de tablas
                basic_stats = self._get_basic_table_stats(conn)
                stats['total_records'] = basic_stats
                
                # Estadísticas de videos por estado
                video_stats = self._get_video_stats(conn)
                stats.update(video_stats)
                
                # Estadísticas por plataforma
                platform_stats = self._get_platform_stats(conn)
                stats['platform_breakdown'] = platform_stats
                
                # Estadísticas temporales
                temporal_stats = self._get_temporal_stats(conn)
                stats['temporal_stats'] = temporal_stats
                
                # Health check de la base de datos
                health_stats = self._get_health_stats(conn)
                stats['health'] = health_stats
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de base de datos: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': {}
            }
    
    def _get_basic_table_stats(self, conn: sqlite3.Connection) -> Dict[str, int]:
        """Estadísticas básicas de todas las tablas"""
        tables = {
            'videos': 'SELECT COUNT(*) FROM videos',
            'video_metadata': 'SELECT COUNT(*) FROM video_metadata',
            'face_data': 'SELECT COUNT(*) FROM face_data WHERE face_data IS NOT NULL',
            'character_data': 'SELECT COUNT(*) FROM character_data WHERE character_data IS NOT NULL'
        }
        
        stats = {}
        for table_name, query in tables.items():
            try:
                result = conn.execute(query).fetchone()
                stats[table_name] = result[0] if result else 0
            except sqlite3.OperationalError:
                # Tabla no existe
                stats[table_name] = 0
        
        return stats
    
    def _get_video_stats(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Estadísticas específicas de videos"""
        try:
            stats = {}
            
            # Videos por estado de procesamiento
            status_query = """
                SELECT 
                    processing_status,
                    COUNT(*) as count
                FROM videos 
                GROUP BY processing_status
            """
            
            status_results = conn.execute(status_query).fetchall()
            stats['by_status'] = {row['processing_status']: row['count'] 
                                for row in status_results}
            
            # Videos con diferentes tipos de datos
            data_queries = {
                'with_thumbnails': "SELECT COUNT(*) FROM videos WHERE thumbnail_path IS NOT NULL",
                'with_music_data': "SELECT COUNT(*) FROM videos WHERE music_data IS NOT NULL",
                'with_face_data': "SELECT COUNT(*) FROM videos WHERE EXISTS (SELECT 1 FROM face_data WHERE face_data.video_id = videos.id)",
                'with_character_data': "SELECT COUNT(*) FROM videos WHERE EXISTS (SELECT 1 FROM character_data WHERE character_data.video_id = videos.id)"
            }
            
            for key, query in data_queries.items():
                try:
                    result = conn.execute(query).fetchone()
                    stats[key] = result[0] if result else 0
                except sqlite3.OperationalError:
                    stats[key] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error en estadísticas de videos: {e}")
            return {}
    
    def _get_platform_stats(self, conn: sqlite3.Connection) -> Dict[str, int]:
        """Estadísticas por plataforma"""
        try:
            query = """
                SELECT 
                    platform,
                    COUNT(*) as count
                FROM videos 
                GROUP BY platform
                ORDER BY count DESC
            """
            
            results = conn.execute(query).fetchall()
            return {row['platform']: row['count'] for row in results}
            
        except Exception as e:
            logger.error(f"Error en estadísticas por plataforma: {e}")
            return {}
    
    def _get_temporal_stats(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Estadísticas temporales (últimos 30 días, etc.)"""
        try:
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            temporal_queries = {
                'added_last_30_days': f"SELECT COUNT(*) FROM videos WHERE added_date >= '{thirty_days_ago}'",
                'added_last_7_days': f"SELECT COUNT(*) FROM videos WHERE added_date >= '{seven_days_ago}'",
                'processed_last_30_days': f"SELECT COUNT(*) FROM videos WHERE last_analysis_date >= '{thirty_days_ago}'",
                'processed_last_7_days': f"SELECT COUNT(*) FROM videos WHERE last_analysis_date >= '{seven_days_ago}'"
            }
            
            stats = {}
            for key, query in temporal_queries.items():
                try:
                    result = conn.execute(query).fetchone()
                    stats[key] = result[0] if result else 0
                except sqlite3.OperationalError:
                    stats[key] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error en estadísticas temporales: {e}")
            return {}
    
    def _get_health_stats(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Health check de la base de datos"""
        try:
            health = {
                'integrity_check': 'unknown',
                'foreign_keys_enabled': False,
                'index_count': 0,
                'vacuum_needed': False
            }
            
            # Integrity check
            try:
                integrity_result = conn.execute("PRAGMA integrity_check").fetchone()
                health['integrity_check'] = 'ok' if integrity_result[0] == 'ok' else 'error'
            except:
                health['integrity_check'] = 'error'
            
            # Foreign keys
            try:
                fk_result = conn.execute("PRAGMA foreign_keys").fetchone()
                health['foreign_keys_enabled'] = bool(fk_result[0]) if fk_result else False
            except:
                pass
            
            # Índices
            try:
                index_result = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'").fetchone()
                health['index_count'] = index_result[0] if index_result else 0
            except:
                pass
            
            return health
            
        except Exception as e:
            logger.error(f"Error en health check: {e}")
            return {'error': str(e)}
    
    def get_quick_summary(self) -> Dict[str, Any]:
        """Resumen ultra-rápido para debugging"""
        try:
            conn = self.get_connection()
            
            # Solo las estadísticas más básicas
            total_videos = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
            db_size = round(self.db_path.stat().st_size / (1024 * 1024), 2) if self.db_path.exists() else 0
            
            return {
                'total_videos': total_videos,
                'database_size_mb': db_size,
                'database_path': str(self.db_path),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'database_path': str(self.db_path) if self._db_path else 'unknown'
            }
    
    def __del__(self):
        """Limpiar conexión al destruir"""
        if self._connection:
            try:
                self._connection.close()
            except:
                pass


# Función de conveniencia
def get_database_stats() -> Dict[str, Any]:
    """Función de conveniencia para obtener estadísticas ligeras"""
    ops = StatsOperations()
    return ops.get_database_stats()

def get_quick_summary() -> Dict[str, Any]:
    """Función de conveniencia para resumen rápido"""
    ops = StatsOperations()
    return ops.get_quick_summary()