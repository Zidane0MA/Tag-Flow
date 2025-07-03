"""
Tag-Flow V2 - Configuración Central
Sistema de Gestión de Videos TikTok/MMD
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración principal de la aplicación"""
    
    # Rutas base
    BASE_DIR = Path(__file__).parent.absolute()
    DATA_DIR = BASE_DIR / 'data'
    STATIC_DIR = BASE_DIR / 'static'
    TEMPLATES_DIR = BASE_DIR / 'templates'
    
    # Base de datos
    DATABASE_PATH = DATA_DIR / 'videos.db'
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'tag-flow-v2-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    FLASK_HOST = os.getenv('FLASK_HOST', 'localhost')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # APIs - YouTube
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    
    # APIs - Google Vision
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # APIs - Spotify
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    # 4K Video Downloader Integration
    EXTERNAL_YOUTUBE_DB = os.getenv('EXTERNAL_YOUTUBE_DB')
    
    # Procesamiento
    THUMBNAIL_SIZE = tuple(map(int, os.getenv('THUMBNAIL_SIZE', '320x180').split('x')))
    MAX_CONCURRENT_PROCESSING = int(os.getenv('MAX_CONCURRENT_PROCESSING', 3))
    USE_GPU_DEEPFACE = os.getenv('USE_GPU_DEEPFACE', 'true').lower() == 'true'
    DEEPFACE_MODEL = os.getenv('DEEPFACE_MODEL', 'ArcFace')
    
    # Rutas de archivos
    # 🆕 LIMPIEZA: Eliminado YOUTUBE_BASE_PATH (legacy) - Sistema usa únicamente variables .env
    THUMBNAILS_PATH = Path(os.getenv('THUMBNAILS_PATH', DATA_DIR / 'thumbnails'))
    PROCESSED_VIDEOS_PATH = Path(os.getenv('PROCESSED_VIDEOS_PATH', BASE_DIR / 'videos_procesados'))
    KNOWN_FACES_PATH = BASE_DIR / 'caras_conocidas'
    
    # Rutas de carpetas organizadas (D:\4K All)
    ORGANIZED_BASE_PATH = Path(os.getenv('ORGANIZED_BASE_PATH', r'D:\4K All'))
    ORGANIZED_YOUTUBE_PATH = ORGANIZED_BASE_PATH / 'Youtube'
    ORGANIZED_TIKTOK_PATH = ORGANIZED_BASE_PATH / 'Tiktok'
    ORGANIZED_INSTAGRAM_PATH = ORGANIZED_BASE_PATH / 'Instagram'
    
    # Rutas de bases de datos externas
    EXTERNAL_YOUTUBE_DB = Path(os.getenv('EXTERNAL_YOUTUBE_DB', r'C:\Users\loler\AppData\Local\4kdownload.com\4K Video Downloader+\4K Video Downloader+\faefbcd1-76a6-4fbc-b730-724f2735eee4.sqlite'))
    EXTERNAL_TIKTOK_DB = Path(os.getenv('EXTERNAL_TIKTOK_DB', r'D:\4K Tokkit\data.sqlite'))
    EXTERNAL_INSTAGRAM_DB = Path(os.getenv('EXTERNAL_INSTAGRAM_DB', r'D:\4K Stogram\.stogram.sqlite'))
    
    # ACRCloud (fallback de V1)
    ACRCLOUD_HOST = os.getenv('ACRCLOUD_HOST')
    ACRCLOUD_ACCESS_KEY = os.getenv('ACRCLOUD_ACCESS_KEY')
    ACRCLOUD_ACCESS_SECRET = os.getenv('ACRCLOUD_ACCESS_SECRET')
    
    # 🆕 CONFIGURACIÓN DE OPTIMIZACIONES DE BD PARA MAIN.PY
    USE_OPTIMIZED_DATABASE = os.getenv('USE_OPTIMIZED_DATABASE', 'true').lower() == 'true'
    DATABASE_CACHE_TTL = int(os.getenv('DATABASE_CACHE_TTL', '300'))  # 5 minutos
    DATABASE_CACHE_SIZE = int(os.getenv('DATABASE_CACHE_SIZE', '1000'))
    ENABLE_PERFORMANCE_METRICS = os.getenv('ENABLE_PERFORMANCE_METRICS', 'true').lower() == 'true'
    
    @classmethod
    def ensure_directories(cls):
        """Crear directorios necesarios si no existen"""
        # 🆕 LIMPIEZA: Crear solo directorios esenciales (sin rutas legacy)
        dirs_to_create = [
            cls.DATA_DIR,
            cls.THUMBNAILS_PATH,
            cls.PROCESSED_VIDEOS_PATH,
            cls.KNOWN_FACES_PATH  # Eliminado: YOUTUBE_BASE_PATH (legacy)
        ]
        
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls):
        """Validar configuración crítica"""
        warnings = []
        
        if not cls.YOUTUBE_API_KEY:
            warnings.append("YOUTUBE_API_KEY no configurada")
            
        if not cls.SPOTIFY_CLIENT_ID or not cls.SPOTIFY_CLIENT_SECRET:
            warnings.append("Credenciales de Spotify no configuradas")
            
        if cls.EXTERNAL_YOUTUBE_DB and not Path(cls.EXTERNAL_YOUTUBE_DB).exists():
            warnings.append(f"Base de datos de 4K Downloader no encontrada: {cls.EXTERNAL_YOUTUBE_DB}")
        
        # Validar bases de datos externas
        if not cls.EXTERNAL_YOUTUBE_DB.exists():
            warnings.append(f"Base de datos de YouTube no encontrada: {cls.EXTERNAL_YOUTUBE_DB}")
        
        if not cls.EXTERNAL_TIKTOK_DB.exists():
            warnings.append(f"Base de datos de TikTok no encontrada: {cls.EXTERNAL_TIKTOK_DB}")
            
        if not cls.EXTERNAL_INSTAGRAM_DB.exists():
            warnings.append(f"Base de datos de Instagram no encontrada: {cls.EXTERNAL_INSTAGRAM_DB}")
        
        # Validar carpetas organizadas
        if not cls.ORGANIZED_BASE_PATH.exists():
            warnings.append(f"Carpeta base organizada no encontrada: {cls.ORGANIZED_BASE_PATH}")
        
        return warnings

# Configuración para desarrollo
class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'

# Configuración para producción    
class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'

# Configuración por defecto
config = DevelopmentConfig if Config.FLASK_ENV == 'development' else ProductionConfig