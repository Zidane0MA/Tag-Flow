"""
Tag-Flow V2 - Script de Migración
Actualizar bases de datos y configuraciones de versiones anteriores
"""

import sys
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Agregar src al path
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Migration:
    """Gestor de migraciones de Tag-Flow"""
    
    def __init__(self):
        self.migrations_applied = []
        self.backup_dir = Path('migration_backups')
        self.backup_dir.mkdir(exist_ok=True)
    
    def detect_version(self):
        """Detectar versión actual del sistema"""
        
        # Verificar si existe base de datos V2
        if config.DATABASE_PATH.exists():
            try:
                with sqlite3.connect(config.DATABASE_PATH) as conn:
                    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    if 'downloader_mapping' in tables:
                        return '2.0.0'
                    elif 'videos' in tables:
                        return '1.5.0'  # V1 con estructura básica
            except:
                pass
        
        # Verificar archivos de V1
        v1_indicators = [
            'streamlit_app.py',
            'reconocimiento_musical.py',
            'datos_videos.json'
        ]
        
        if any(Path(indicator).exists() for indicator in v1_indicators):
            return '1.0.0'
        
        return 'new'  # Instalación nueva
    
    def create_backup(self, version):
        """Crear backup antes de migración"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_v{version}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"Creando backup: {backup_path}")
        
        # Backup de archivos importantes
        files_to_backup = [
            '.env',
            'datos_videos.json',  # V1
            'config.json',        # V1
            'data/videos.db',     # V2
        ]
        
        for file_path in files_to_backup:
            source = Path(file_path)
            if source.exists():
                if source.is_file():
                    shutil.copy2(source, backup_path / source.name)
                else:
                    shutil.copytree(source, backup_path / source.name)
                logger.info(f"  ✓ {file_path}")
        
        return backup_path
    
    def migrate_from_v1_to_v2(self):
        """Migrar desde Tag-Flow V1 a V2"""
        logger.info("Migrando desde V1 a V2...")
        
        # 1. Migrar datos de videos desde JSON
        self.migrate_v1_json_data()
        
        # 2. Migrar configuración
        self.migrate_v1_config()
        
        # 3. Convertir estructura de archivos
        self.migrate_v1_file_structure()
        
        logger.info("✅ Migración V1→V2 completada")
    
    def migrate_v1_json_data(self):
        """Migrar datos de videos desde JSON de V1"""
        json_path = Path('datos_videos.json')
        
        if not json_path.exists():
            logger.info("No se encontró datos_videos.json - saltando migración de datos")
            return
        
        logger.info("Migrando datos de videos desde JSON...")
        
        try:
            # Cargar datos V1
            with open(json_path, 'r', encoding='utf-8') as f:
                v1_data = json.load(f)
            
            # Inicializar base de datos V2
            from src.database import db
            
            migrated_count = 0
            
            for video_key, video_data in v1_data.items():
                try:
                    # Convertir formato V1 a V2
                    v2_video_data = self.convert_v1_to_v2_format(video_data)
                    
                    # Verificar que el archivo aún existe
                    if Path(v2_video_data['file_path']).exists():
                        video_id = db.add_video(v2_video_data)
                        migrated_count += 1
                        logger.debug(f"  ✓ Migrado: {v2_video_data['file_name']}")
                    else:
                        logger.warning(f"  ⚠ Archivo no existe: {v2_video_data['file_path']}")
                        
                except Exception as e:
                    logger.error(f"  ✗ Error migrando {video_key}: {e}")
            
            logger.info(f"✅ {migrated_count} videos migrados a la nueva base de datos")
            
            # Renombrar archivo original
            json_path.rename(f'datos_videos_v1_backup_{datetime.now().strftime("%Y%m%d")}.json')
            
        except Exception as e:
            logger.error(f"Error migrando datos JSON: {e}")
    
    def convert_v1_to_v2_format(self, v1_data):
        """Convertir formato de datos V1 a V2"""
        
        # Mapeo de campos V1 → V2
        v2_data = {
            'file_path': v1_data.get('ruta_archivo', ''),
            'file_name': Path(v1_data.get('ruta_archivo', '')).name,
            'creator_name': v1_data.get('creador', 'Desconocido'),
            'platform': 'tiktok',  # Default para V1
            'file_size': v1_data.get('tamaño_archivo'),
            'duration_seconds': v1_data.get('duracion'),
            
            # Música
            'detected_music': v1_data.get('musica_detectada'),
            'detected_music_artist': v1_data.get('artista_detectado'),
            'detected_music_confidence': v1_data.get('confianza_musica', 0.0),
            'music_source': 'acrcloud' if v1_data.get('musica_detectada') else None,
            
            # Personajes (si existían en V1)
            'detected_characters': v1_data.get('personajes_detectados', []),
            
            # Estado
            'edit_status': 'completado' if v1_data.get('procesado') else 'nulo',
            'notes': v1_data.get('notas', ''),
            
            'processing_status': 'completado'
        }
        
        return v2_data
    
    def migrate_v1_config(self):
        """Migrar configuración desde V1"""
        config_path = Path('config.json')
        
        if not config_path.exists():
            logger.info("No se encontró config.json - saltando migración de configuración")
            return
        
        logger.info("Migrando configuración desde V1...")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                v1_config = json.load(f)
            
            # Leer .env actual
            env_path = Path('.env')
            env_lines = []
            
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    env_lines = f.readlines()
            
            # Actualizar configuración
            updates = {}
            
            if 'acrcloud' in v1_config:
                acr_config = v1_config['acrcloud']
                updates['ACRCLOUD_HOST'] = acr_config.get('host', '')
                updates['ACRCLOUD_ACCESS_KEY'] = acr_config.get('access_key', '')
                updates['ACRCLOUD_ACCESS_SECRET'] = acr_config.get('access_secret', '')
            
            if 'rutas' in v1_config:
                rutas = v1_config['rutas']
                updates['VIDEOS_BASE_PATH'] = rutas.get('videos', '')
            
            # Escribir .env actualizado
            self.update_env_file(updates)
            
            logger.info("✅ Configuración migrada")
            
            # Renombrar archivo original
            config_path.rename(f'config_v1_backup_{datetime.now().strftime("%Y%m%d")}.json')
            
        except Exception as e:
            logger.error(f"Error migrando configuración: {e}")
    
    def migrate_v1_file_structure(self):
        """Migrar estructura de archivos V1"""
        logger.info("Migrando estructura de archivos...")
        
        # Crear directorios V2 si no existen
        config.ensure_directories()
        
        # Mover archivos de thumbnails si existen
        old_thumbnails = Path('thumbnails')
        if old_thumbnails.exists():
            logger.info("Moviendo thumbnails...")
            for thumb in old_thumbnails.glob('*.jpg'):
                new_path = config.THUMBNAILS_PATH / thumb.name
                if not new_path.exists():
                    shutil.move(str(thumb), str(new_path))
            
            # Remover directorio vacío
            try:
                old_thumbnails.rmdir()
            except:
                pass
        
        logger.info("✅ Estructura de archivos migrada")
    
    def update_env_file(self, updates):
        """Actualizar archivo .env con nuevos valores"""
        env_path = Path('.env')
        lines = []
        
        # Leer líneas existentes
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # Actualizar valores existentes
        updated_keys = set()
        
        for i, line in enumerate(lines):
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in updates:
                    lines[i] = f'{key}="{updates[key]}"\n'
                    updated_keys.add(key)
        
        # Agregar nuevas claves
        for key, value in updates.items():
            if key not in updated_keys:
                lines.append(f'{key}="{value}"\n')
        
        # Escribir archivo actualizado
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def migrate_database_schema(self):
        """Migrar esquema de base de datos entre versiones menores"""
        logger.info("Verificando esquema de base de datos...")
        
        if not config.DATABASE_PATH.exists():
            logger.info("Base de datos no existe - no requiere migración")
            return
        
        try:
            with sqlite3.connect(config.DATABASE_PATH) as conn:
                # Verificar versión del esquema
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Agregar tabla de mapeo si no existe (migración menor)
                if 'videos' in tables and 'downloader_mapping' not in tables:
                    logger.info("Agregando tabla downloader_mapping...")
                    conn.execute('''
                        CREATE TABLE downloader_mapping (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            video_id INTEGER,
                            download_item_id INTEGER,
                            original_filename TEXT,
                            creator_from_downloader TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
                        )
                    ''')
                    logger.info("✅ Tabla agregada")
                
                # Agregar columnas nuevas si faltan
                self.add_missing_columns(conn)
                
        except Exception as e:
            logger.error(f"Error migrando esquema: {e}")
    
    def add_missing_columns(self, conn):
        """Agregar columnas faltantes a la tabla videos"""
        
        # Obtener columnas actuales
        cursor = conn.execute("PRAGMA table_info(videos)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Columnas que deberían existir en V2
        required_columns = {
            'thumbnail_path': 'TEXT',
            'difficulty_level': 'TEXT CHECK(difficulty_level IN ("bajo", "medio", "alto"))',
            'edited_video_path': 'TEXT',
            'error_message': 'TEXT',
            'music_source': 'TEXT CHECK(music_source IN ("youtube", "spotify", "acrcloud", "manual"))'
        }
        
        # Agregar columnas faltantes
        for column, column_type in required_columns.items():
            if column not in existing_columns:
                try:
                    conn.execute(f'ALTER TABLE videos ADD COLUMN {column} {column_type}')
                    logger.info(f"  ✓ Columna agregada: {column}")
                except Exception as e:
                    logger.warning(f"  ⚠ Error agregando columna {column}: {e}")
    
    def run_migration(self):
        """Ejecutar migración completa"""
        logger.info("🔄 Iniciando migración de Tag-Flow")
        logger.info("="*40)
        
        # Detectar versión actual
        current_version = self.detect_version()
        logger.info(f"Versión detectada: {current_version}")
        
        if current_version == 'new':
            logger.info("✅ Instalación nueva - no requiere migración")
            return True
        
        # Crear backup
        backup_path = self.create_backup(current_version)
        
        try:
            # Ejecutar migraciones según versión
            if current_version == '1.0.0':
                self.migrate_from_v1_to_v2()
            elif current_version in ['1.5.0', '2.0.0']:
                self.migrate_database_schema()
            
            logger.info("="*40)
            logger.info("✅ ¡Migración completada exitosamente!")
            logger.info(f"📁 Backup creado en: {backup_path}")
            logger.info("\n🎯 Próximos pasos:")
            logger.info("   1. Verificar configuración: python check_installation.py")
            logger.info("   2. Procesar videos: python main.py")
            logger.info("   3. Lanzar interfaz: python app.py")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error durante migración: {e}")
            logger.error(f"📁 Backup disponible en: {backup_path}")
            return False

def main():
    """Función principal"""
    print("🔄 Tag-Flow V2 - Migración de Datos")
    print("="*40)
    
    migration = Migration()
    
    # Preguntar confirmación
    current_version = migration.detect_version()
    
    if current_version == 'new':
        print("✅ Instalación nueva detectada - no requiere migración")
        return
    
    print(f"📋 Versión actual detectada: {current_version}")
    print("🔄 Se realizará migración a Tag-Flow V2")
    print("\n⚠️  Se creará un backup automático antes de continuar")
    
    confirm = input("\n¿Continuar con la migración? [Y/n]: ").lower()
    if confirm == 'n':
        print("❌ Migración cancelada")
        return
    
    # Ejecutar migración
    success = migration.run_migration()
    
    if success:
        print("\n🎉 ¡Migración exitosa!")
    else:
        print("\n❌ Migración falló - revisar logs")

if __name__ == '__main__':
    main()