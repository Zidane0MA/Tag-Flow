"""
Tag-Flow V2 - Database Migrations
Sistema automático de migraciones y optimizaciones de base de datos
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Sistema de migraciones automáticas para la base de datos"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migrations_applied = self._get_applied_migrations()

    def _get_applied_migrations(self) -> set:
        """Obtener migraciones ya aplicadas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Crear tabla de migraciones si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY,
                    migration_name TEXT UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Obtener migraciones aplicadas
            cursor.execute("SELECT migration_name FROM schema_migrations")
            applied = {row[0] for row in cursor.fetchall()}

            conn.close()
            return applied

        except Exception as e:
            logger.warning(f"Error obteniendo migraciones aplicadas: {e}")
            return set()

    def _mark_migration_applied(self, migration_name: str):
        """Marcar migración como aplicada"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO schema_migrations (migration_name) VALUES (?)",
                (migration_name,)
            )
            conn.commit()
            conn.close()
            logger.info(f"✅ Migración marcada como aplicada: {migration_name}")
        except Exception as e:
            logger.error(f"Error marcando migración {migration_name}: {e}")

    def apply_performance_indices(self) -> bool:
        """Aplicar índices de performance automáticamente"""
        migration_name = "performance_indices_v1"

        if migration_name in self.migrations_applied:
            logger.info(f"📊 Índices de performance ya aplicados")
            return True

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            logger.info("📊 Aplicando índices de performance...")

            # Índices para carruseles y media
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_media_post_carousel
                ON media(post_id, carousel_order, is_primary)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_media_type_status
                ON media(media_type, processing_status)
            """)

            # Índices para ordenamiento temporal
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_posts_creator_date
                ON posts(creator_id, publication_date DESC, deleted_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_posts_platform_date
                ON posts(platform_id, publication_date DESC, deleted_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_posts_subscription_date
                ON posts(subscription_id, publication_date DESC, deleted_at)
            """)

            # Índices para filtros comunes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_media_edit_processing
                ON media(edit_status, processing_status, difficulty_level)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_posts_carousel_type
                ON posts(is_carousel, carousel_count, deleted_at)
            """)

            # Índices para búsquedas
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_posts_title_search
                ON posts(title_post COLLATE NOCASE, deleted_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_media_filename_search
                ON media(file_name COLLATE NOCASE)
            """)

            # Índices para creadores
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_creators_platform_name
                ON creators(platform_id, name COLLATE NOCASE)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_creators_hierarchy
                ON creators(parent_creator_id, is_primary, alias_type)
            """)

            # Índices para estadísticas
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_posts_stats_combo
                ON posts(platform_id, creator_id, subscription_id, deleted_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_media_stats_combo
                ON media(media_type, edit_status, processing_status)
            """)

            # Índices para categorías
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_post_categories_type
                ON post_categories(category_type, post_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_subscriptions_type_platform
                ON subscriptions(subscription_type, platform_id, is_account)
            """)

            # Índices compuestos para consultas complejas
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_media_posts_full_query
                ON media(processing_status, edit_status, post_id, created_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_posts_creators_platforms
                ON posts(creator_id, platform_id, publication_date DESC, deleted_at)
            """)

            # Optimizar base de datos
            cursor.execute("ANALYZE")

            conn.commit()
            conn.close()

            # Marcar como aplicada
            self._mark_migration_applied(migration_name)

            logger.info("✅ Índices de performance aplicados exitosamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error aplicando índices de performance: {e}")
            return False

    def run_all_migrations(self) -> bool:
        """Ejecutar todas las migraciones necesarias"""
        success = True

        # Aplicar índices de performance
        if not self.apply_performance_indices():
            success = False

        return success

def ensure_database_optimized(db_path: str) -> bool:
    """Asegurar que la base de datos está optimizada (llamar al inicio de la app)"""
    try:
        migration = DatabaseMigration(db_path)
        return migration.run_all_migrations()
    except Exception as e:
        logger.error(f"Error en migraciones de base de datos: {e}")
        return False