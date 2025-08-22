"""
Tag-Flow V2 - Database Statistics and Performance
Statistics gathering and performance monitoring
"""

import statistics
import time
from pathlib import Path
from typing import Dict, List
from .base import DatabaseBase
import logging

logger = logging.getLogger(__name__)


class StatisticsOperations(DatabaseBase):
    """Database statistics and performance monitoring"""
    
    def get_stats(self) -> Dict:
        """Get general database statistics"""
        self._ensure_initialized()
        start_time = time.time()
        
        stats = {}
        
        with self.get_connection() as conn:
            # Total videos (active)
            cursor = conn.execute("SELECT COUNT(*) FROM videos WHERE deleted_at IS NULL")
            stats['total_videos'] = cursor.fetchone()[0]
            
            # Total deleted videos
            cursor = conn.execute("SELECT COUNT(*) FROM videos WHERE deleted_at IS NOT NULL")
            stats['total_deleted'] = cursor.fetchone()[0]
            
            # Videos by platform
            cursor = conn.execute("""
                SELECT platform, COUNT(*) as count 
                FROM videos 
                WHERE deleted_at IS NULL 
                GROUP BY platform
                ORDER BY count DESC
            """)
            stats['by_platform'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Videos by edit status
            cursor = conn.execute("""
                SELECT edit_status, COUNT(*) as count 
                FROM videos 
                WHERE deleted_at IS NULL 
                GROUP BY edit_status
            """)
            stats['by_edit_status'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Videos by processing status
            cursor = conn.execute("""
                SELECT processing_status, COUNT(*) as count 
                FROM videos 
                WHERE deleted_at IS NULL 
                GROUP BY processing_status
            """)
            stats['by_processing_status'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Videos with music
            cursor = conn.execute("""
                SELECT COUNT(*) FROM videos 
                WHERE (detected_music IS NOT NULL OR final_music IS NOT NULL)
                AND deleted_at IS NULL
            """)
            stats['with_music'] = cursor.fetchone()[0]
            
            # Videos with characters
            cursor = conn.execute("""
                SELECT COUNT(*) FROM videos 
                WHERE (detected_characters IS NOT NULL OR final_characters IS NOT NULL)
                AND deleted_at IS NULL
            """)
            stats['with_characters'] = cursor.fetchone()[0]
            
            # Total creators
            cursor = conn.execute("SELECT COUNT(*) FROM creators")
            stats['total_creators'] = cursor.fetchone()[0]
            
            # Primary vs secondary creators
            cursor = conn.execute("SELECT is_primary, COUNT(*) FROM creators GROUP BY is_primary")
            creator_types = {row[0]: row[1] for row in cursor.fetchall()}
            stats['primary_creators'] = creator_types.get(1, 0)  # SQLite stores boolean as int
            stats['secondary_creators'] = creator_types.get(0, 0)
            
            # Total subscriptions
            cursor = conn.execute("SELECT COUNT(*) FROM subscriptions")
            stats['total_subscriptions'] = cursor.fetchone()[0]
        
        self._track_query('get_stats', time.time() - start_time)
        return stats
    
    def get_creator_stats(self, creator_id: int) -> Dict:
        """Get statistics for specific creator"""
        self._ensure_initialized()
        start_time = time.time()
        
        stats = {}
        
        with self.get_connection() as conn:
            # Total videos
            cursor = conn.execute('''
                SELECT COUNT(*) FROM videos 
                WHERE creator_id = ? AND deleted_at IS NULL
            ''', (creator_id,))
            stats['total_videos'] = cursor.fetchone()[0]
            
            # Videos by platform
            cursor = conn.execute('''
                SELECT platform, COUNT(*) FROM videos 
                WHERE creator_id = ? AND deleted_at IS NULL
                GROUP BY platform
            ''', (creator_id,))
            stats['by_platform'] = dict(cursor.fetchall())
            
            # Videos by subscription
            cursor = conn.execute('''
                SELECT s.name, s.type, COUNT(v.id) FROM videos v
                JOIN subscriptions s ON v.subscription_id = s.id
                WHERE v.creator_id = ? AND v.deleted_at IS NULL
                GROUP BY s.id, s.name, s.type
            ''', (creator_id,))
            stats['by_subscription'] = [
                {'name': row[0], 'type': row[1], 'count': row[2]} 
                for row in cursor.fetchall()
            ]
            
            # Videos by edit status
            cursor = conn.execute('''
                SELECT edit_status, COUNT(*) FROM videos 
                WHERE creator_id = ? AND deleted_at IS NULL
                GROUP BY edit_status
            ''', (creator_id,))
            stats['by_edit_status'] = dict(cursor.fetchall())
            
            # Videos with music/characters
            cursor = conn.execute('''
                SELECT 
                    COUNT(CASE WHEN detected_music IS NOT NULL OR final_music IS NOT NULL THEN 1 END) as with_music,
                    COUNT(CASE WHEN detected_characters IS NOT NULL OR final_characters IS NOT NULL THEN 1 END) as with_characters
                FROM videos 
                WHERE creator_id = ? AND deleted_at IS NULL
            ''', (creator_id,))
            music_chars = cursor.fetchone()
            stats['with_music'] = music_chars[0]
            stats['with_characters'] = music_chars[1]
        
        self._track_query('get_creator_stats', time.time() - start_time)
        return stats
    
    def get_platform_stats_external_sources(self) -> Dict:
        """Get platform statistics from external sources"""
        self._ensure_initialized()
        start_time = time.time()
        
        stats = {}
        
        with self.get_connection() as conn:
            # Statistics by external source
            cursor = conn.execute('''
                SELECT dm.external_db_source, v.platform, COUNT(v.id) as video_count
                FROM videos v
                JOIN downloader_mapping dm ON v.id = dm.video_id
                WHERE v.deleted_at IS NULL
                GROUP BY dm.external_db_source, v.platform
            ''')
            
            for row in cursor.fetchall():
                source = row[0] or 'unknown'
                platform = row[1]
                count = row[2]
                
                if source not in stats:
                    stats[source] = {}
                stats[source][platform] = count
            
            # Carousel statistics
            cursor = conn.execute('''
                SELECT 
                    dm.external_db_source,
                    COUNT(CASE WHEN dm.is_carousel_item = 1 THEN 1 END) as carousel_items,
                    COUNT(*) as total_items
                FROM downloader_mapping dm
                JOIN videos v ON dm.video_id = v.id
                WHERE v.deleted_at IS NULL
                GROUP BY dm.external_db_source
            ''')
            
            stats['carousel_stats'] = {}
            for row in cursor.fetchall():
                source = row[0] or 'unknown'
                stats['carousel_stats'][source] = {
                    'carousel_items': row[1],
                    'total_items': row[2],
                    'carousel_percentage': round((row[1] / row[2]) * 100, 1) if row[2] > 0 else 0
                }
        
        self._track_query('get_platform_stats_external_sources', time.time() - start_time)
        return stats
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive database performance report"""
        start_time = time.time()
        
        report = {
            'total_queries': self.total_queries,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': 0.0,
            'queries_by_type': {},
            'database_size_mb': 0.0,
            'performance_grade': 'UNKNOWN'
        }
        
        # Calculate cache hit rate
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests > 0:
            report['cache_hit_rate'] = round((self.cache_hits / total_cache_requests) * 100, 1)
        
        # Statistics by query type
        for query_name, times in self.query_times.items():
            if times:
                report['queries_by_type'][query_name] = {
                    'count': len(times),
                    'avg_time_ms': round(statistics.mean(times) * 1000, 2),
                    'min_time_ms': round(min(times) * 1000, 2),
                    'max_time_ms': round(max(times) * 1000, 2),
                    'median_time_ms': round(statistics.median(times) * 1000, 2)
                }
        
        # Database file size
        try:
            db_size_bytes = Path(self.db_path).stat().st_size
            report['database_size_mb'] = round(db_size_bytes / (1024 * 1024), 2)
        except Exception as e:
            logger.warning(f"Could not get database size: {e}")
        
        # Performance grade
        report['performance_grade'] = self._calculate_performance_grade(report)
        
        self._track_query('get_performance_report', time.time() - start_time)
        return report
    
    def _calculate_performance_grade(self, report: Dict) -> str:
        """Calculate performance grade based on metrics"""
        score = 0
        max_score = 100
        
        # Cache hit rate (30 points)
        cache_score = min(30, (report['cache_hit_rate'] / 100) * 30)
        score += cache_score
        
        # Average query time (40 points) - penalize slow queries
        avg_times = []
        for query_data in report['queries_by_type'].values():
            avg_times.append(query_data['avg_time_ms'])
        
        if avg_times:
            overall_avg = statistics.mean(avg_times)
            if overall_avg < 10:
                score += 40  # Excellent
            elif overall_avg < 50:
                score += 30  # Good
            elif overall_avg < 100:
                score += 20  # Fair
            elif overall_avg < 200:
                score += 10  # Poor
            # 0 points for very slow queries
        
        # Database size efficiency (20 points)
        db_size = report['database_size_mb']
        if db_size < 100:
            score += 20  # Small and efficient
        elif db_size < 500:
            score += 15  # Reasonable size
        elif db_size < 1000:
            score += 10  # Large but manageable
        elif db_size < 2000:
            score += 5   # Very large
        # 0 points for extremely large databases
        
        # Query diversity (10 points) - good if using optimized queries
        optimized_queries = ['get_existing_paths_only', 'check_videos_exist_batch', 'get_videos_by_paths_batch']
        optimized_count = sum(1 for q in optimized_queries if q in report['queries_by_type'])
        score += (optimized_count / len(optimized_queries)) * 10
        
        # Convert to letter grade
        percentage = (score / max_score) * 100
        if percentage >= 90:
            return 'A+'
        elif percentage >= 85:
            return 'A'
        elif percentage >= 80:
            return 'B+'
        elif percentage >= 75:
            return 'B'
        elif percentage >= 70:
            return 'C+'
        elif percentage >= 65:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'
    
    def log_performance_summary(self):
        """Log performance summary to console"""
        try:
            report = self.get_performance_report()
            
            logger.info("=== DATABASE PERFORMANCE SUMMARY ===")
            logger.info(f"📊 Total Queries: {report['total_queries']}")
            logger.info(f"🎯 Cache Hit Rate: {report['cache_hit_rate']}%")
            logger.info(f"💾 Database Size: {report['database_size_mb']} MB")
            logger.info(f"🏆 Performance Grade: {report['performance_grade']}")
            
            if report['queries_by_type']:
                logger.info("⚡ Top Query Types:")
                sorted_queries = sorted(
                    report['queries_by_type'].items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:5]
                
                for query_name, stats in sorted_queries:
                    logger.info(f"  • {query_name}: {stats['count']} calls, "
                              f"avg {stats['avg_time_ms']}ms")
            
            logger.info("=====================================")
            
        except Exception as e:
            logger.error(f"Error logging performance summary: {e}")
    
    def get_unique_music(self) -> List[str]:
        """Get list of unique music tracks"""
        self._ensure_initialized()
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT DISTINCT 
                    COALESCE(final_music, detected_music) as music
                FROM videos 
                WHERE (final_music IS NOT NULL OR detected_music IS NOT NULL)
                AND deleted_at IS NULL
                ORDER BY music
            ''')
            music_list = [row[0] for row in cursor.fetchall() if row[0]]
        
        self._track_query('get_unique_music', time.time() - start_time)
        return music_list
    
    def get_database_health_check(self) -> Dict:
        """Comprehensive database health check"""
        self._ensure_initialized()
        start_time = time.time()
        
        health = {
            'status': 'healthy',
            'issues': [],
            'recommendations': [],
            'integrity_check': False
        }
        
        with self.get_connection() as conn:
            try:
                # Check database integrity
                cursor = conn.execute('PRAGMA integrity_check')
                integrity_result = cursor.fetchone()[0]
                health['integrity_check'] = integrity_result == 'ok'
                
                if not health['integrity_check']:
                    health['status'] = 'critical'
                    health['issues'].append(f"Database integrity failed: {integrity_result}")
                
                # Check for orphaned records
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM videos v
                    LEFT JOIN creators c ON v.creator_id = c.id
                    WHERE c.id IS NULL
                ''')
                orphaned_videos = cursor.fetchone()[0]
                
                if orphaned_videos > 0:
                    health['status'] = 'warning'
                    health['issues'].append(f"{orphaned_videos} videos have invalid creator references")
                    health['recommendations'].append("Run data cleanup to fix orphaned video records")
                
                # Check for missing indices
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
                existing_indices = {row[0] for row in cursor.fetchall()}
                
                required_indices = {
                    'idx_videos_file_path', 'idx_videos_creator_id', 'idx_videos_platform_status',
                    'idx_creators_name', 'idx_subscriptions_platform_type'
                }
                
                missing_indices = required_indices - existing_indices
                if missing_indices:
                    health['status'] = 'warning'
                    health['issues'].append(f"Missing performance indices: {', '.join(missing_indices)}")
                    health['recommendations'].append("Run database initialization to create missing indices")
                
                # Check database size vs record count ratio
                try:
                    db_size_mb = Path(self.db_path).stat().st_size / (1024 * 1024)
                    cursor = conn.execute('SELECT COUNT(*) FROM videos')
                    video_count = cursor.fetchone()[0]
                    
                    if video_count > 0:
                        mb_per_video = db_size_mb / video_count
                        if mb_per_video > 1.0:  # More than 1MB per video suggests bloat
                            health['recommendations'].append("Consider running VACUUM to reduce database size")
                
                except Exception:
                    pass  # Size check is optional
                
            except Exception as e:
                health['status'] = 'critical'
                health['issues'].append(f"Health check failed: {e}")
        
        self._track_query('get_database_health_check', time.time() - start_time)
        return health