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
                
                # 🆕 NUEVA ESTRUCTURA: Estadísticas de creadores y suscripciones
                new_structure_stats = self._get_new_structure_stats(conn)
                stats['new_structure'] = new_structure_stats
                
                # 🆕 Estadísticas de fuentes externas
                external_stats = self._get_external_sources_stats()
                stats['external_sources'] = external_stats
            
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
    
    def _get_new_structure_stats(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Estadísticas de la nueva estructura (creadores, suscripciones, listas)"""
        try:
            stats = {}
            
            # Verificar si las nuevas tablas existen
            tables_check = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('creators', 'subscriptions', 'creator_urls', 'video_lists')
            """).fetchall()
            
            existing_tables = [row[0] for row in tables_check]
            stats['tables_exist'] = existing_tables
            
            if 'creators' in existing_tables:
                # Estadísticas de creadores
                creator_count = conn.execute("SELECT COUNT(*) FROM creators").fetchone()[0]
                stats['total_creators'] = creator_count
                
                # Creadores con URLs por plataforma
                if 'creator_urls' in existing_tables:
                    platform_creators = conn.execute("""
                        SELECT platform, COUNT(DISTINCT creator_id) as count
                        FROM creator_urls
                        GROUP BY platform
                    """).fetchall()
                    stats['creators_by_platform'] = {row[0]: row[1] for row in platform_creators}
            
            if 'subscriptions' in existing_tables:
                # Estadísticas de suscripciones
                subscription_count = conn.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
                stats['total_subscriptions'] = subscription_count
                
                # Suscripciones por tipo y plataforma
                sub_breakdown = conn.execute("""
                    SELECT platform, type, COUNT(*) as count
                    FROM subscriptions
                    GROUP BY platform, type
                """).fetchall()
                
                platform_subs = {}
                for row in sub_breakdown:
                    platform = row[0]
                    sub_type = row[1]
                    count = row[2]
                    
                    if platform not in platform_subs:
                        platform_subs[platform] = {}
                    platform_subs[platform][sub_type] = count
                
                stats['subscriptions_breakdown'] = platform_subs
            
            if 'video_lists' in existing_tables:
                # Estadísticas de listas de videos
                list_stats = conn.execute("""
                    SELECT list_type, COUNT(*) as count
                    FROM video_lists
                    GROUP BY list_type
                """).fetchall()
                stats['video_lists'] = {row[0]: row[1] for row in list_stats}
            
            # Videos con nueva estructura
            videos_with_creator = conn.execute("""
                SELECT COUNT(*) FROM videos WHERE creator_id IS NOT NULL
            """).fetchone()[0]
            
            videos_with_subscription = conn.execute("""
                SELECT COUNT(*) FROM videos WHERE subscription_id IS NOT NULL
            """).fetchone()[0]
            
            stats['videos_with_creator_id'] = videos_with_creator
            stats['videos_with_subscription_id'] = videos_with_subscription
            
            return stats
            
        except Exception as e:
            logger.error(f"Error en estadísticas de nueva estructura: {e}")
            return {'error': str(e)}
    
    def _get_external_sources_stats(self) -> Dict[str, Any]:
        """Estadísticas de fuentes externas disponibles con desglose por plataforma"""
        try:
            # Usar external_sources integrado (no v2)
            from src.service_factory import get_external_sources
            
            external_sources = get_external_sources()
            
            # Contar videos disponibles por plataforma
            available_sources = {}
            platform_breakdown = {}
            
            # 4K Video Downloader - Desglose por todas las plataformas
            if external_sources.external_youtube_db and external_sources.external_youtube_db.exists():
                # Obtener desglose por plataforma de 4K Video Downloader
                platform_stats = self._get_4k_video_platform_breakdown(external_sources)
                platform_breakdown['4k_video_downloader'] = platform_stats
                
                # Total de 4K Video Downloader
                total_4k_video = sum(platform_stats.values())
                available_sources['4k_video_downloader_total'] = total_4k_video
                
                # YouTube específico
                available_sources['4k_video_youtube'] = platform_stats.get('youtube', 0)
            
            # TikTok (4K Tokkit)
            if external_sources.tiktok_db_path and external_sources.tiktok_db_path.exists():
                tiktok_videos = external_sources.extract_tiktok_videos()
                available_sources['4k_tokkit_tiktok'] = len(tiktok_videos)
            
            # Instagram (4K Stogram)
            if external_sources.instagram_db_path and external_sources.instagram_db_path.exists():
                instagram_content = external_sources.extract_instagram_content()
                available_sources['4k_stogram_instagram'] = len(instagram_content)
            
            # Carpetas organizadas
            organized_stats = self._get_organized_folders_stats(external_sources)
            
            return {
                'available_sources': available_sources,
                'platform_breakdown': platform_breakdown,
                'organized_folders': organized_stats,
                'total_external_videos': sum(available_sources.values()),
                'total_organized_videos': organized_stats.get('total_videos', 0),
                'sources_found': len(available_sources)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de fuentes externas: {e}")
            return {
                'error': str(e),
                'available_sources': {},
                'platform_breakdown': {},
                'total_external_videos': 0,
                'sources_found': 0
            }
    
    def _get_4k_video_platform_breakdown(self, external_sources) -> Dict[str, int]:
        """Obtener desglose por plataforma de 4K Video Downloader"""
        try:
            import sqlite3
            platform_stats = {}
            
            # Conectar directamente a la BD de 4K Video Downloader
            conn = sqlite3.connect(str(external_sources.external_youtube_db))
            conn.row_factory = sqlite3.Row
            
            # Query para obtener estadísticas por plataforma
            query = """
            SELECT 
                LOWER(ud.service_name) as platform,
                COUNT(*) as count
            FROM download_item di
            LEFT JOIN media_item_description mid ON di.id = mid.download_item_id
            LEFT JOIN url_description ud ON mid.id = ud.media_item_description_id
            WHERE di.filename IS NOT NULL AND ud.service_name IS NOT NULL
            GROUP BY LOWER(ud.service_name)
            ORDER BY count DESC
            """
            
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
            # Normalizar nombres de plataforma
            platform_mapping = {
                'youtube': 'youtube',
                'facebook': 'facebook',
                'twitter': 'twitter',
                'x': 'twitter',  # X (antes Twitter)
                'vimeo': 'vimeo',
                'dailymotion': 'dailymotion',
                'twitch': 'twitch',
                'soundcloud': 'soundcloud'
            }
            
            for row in rows:
                platform_raw = row['platform']
                count = row['count']
                
                # Normalizar nombre de plataforma
                platform_normalized = platform_mapping.get(platform_raw, platform_raw)
                
                if platform_normalized in platform_stats:
                    platform_stats[platform_normalized] += count
                else:
                    platform_stats[platform_normalized] = count
            
            conn.close()
            
            return platform_stats
            
        except Exception as e:
            logger.error(f"Error obteniendo desglose de plataformas 4K Video Downloader: {e}")
            return {}
    
    def _get_organized_folders_stats(self, external_sources) -> Dict[str, Any]:
        """Obtener estadísticas de carpetas organizadas"""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from config import config
            
            organized_stats = {
                'base_path': str(config.ORGANIZED_BASE_PATH),
                'base_path_exists': config.ORGANIZED_BASE_PATH.exists(),
                'platforms': {},
                'total_videos': 0,
                'total_creators': 0
            }
            
            if not config.ORGANIZED_BASE_PATH.exists():
                organized_stats['error'] = f"Carpeta base no existe: {config.ORGANIZED_BASE_PATH}"
                return organized_stats
            
            # Escanear plataformas principales
            main_platforms = ['Youtube', 'Tiktok', 'Instagram']
            
            for platform in main_platforms:
                platform_path = config.ORGANIZED_BASE_PATH / platform
                platform_lower = platform.lower()
                
                if platform_path.exists():
                    # Contar carpetas de creadores
                    creator_folders = [d for d in platform_path.iterdir() if d.is_dir()]
                    
                    # Contar videos en cada carpeta de creador
                    total_videos = 0
                    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
                    
                    for creator_folder in creator_folders:
                        if creator_folder.is_dir():
                            # Contar videos recursivamente
                            for file_path in creator_folder.rglob('*'):
                                if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                                    total_videos += 1
                    
                    organized_stats['platforms'][platform_lower] = {
                        'path': str(platform_path),
                        'creators': len(creator_folders),
                        'videos': total_videos
                    }
                    
                    organized_stats['total_videos'] += total_videos
                    organized_stats['total_creators'] += len(creator_folders)
                else:
                    organized_stats['platforms'][platform_lower] = {
                        'path': str(platform_path),
                        'exists': False,
                        'creators': 0,
                        'videos': 0
                    }
            
            # Escanear otras plataformas (carpetas adicionales)
            other_platforms = []
            for item in config.ORGANIZED_BASE_PATH.iterdir():
                if item.is_dir() and item.name not in main_platforms:
                    other_platforms.append(item.name)
            
            if other_platforms:
                organized_stats['other_platforms'] = other_platforms
                organized_stats['other_platforms_count'] = len(other_platforms)
            
            return organized_stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de carpetas organizadas: {e}")
            return {
                'error': str(e),
                'platforms': {},
                'total_videos': 0,
                'total_creators': 0
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