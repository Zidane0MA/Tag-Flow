"""
Tag-Flow V2 - Configuración Central Refactorizada
Sistema de Gestión de Videos TikTok/MMD

🎯 PATRÓN: Una sola fuente de verdad para todas las configuraciones
✅ Rutas internas del proyecto: Hardcodeadas para robustez
🔧 Rutas externas y APIs: Configurables via .env
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ========================================
# 📁 RUTAS BASE DEL PROYECTO (Hardcodeadas)
# ========================================

BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / 'data'
STATIC_DIR = BASE_DIR / 'static'
TEMPLATES_DIR = BASE_DIR / 'templates'

# ========================================
# 🗄️ RUTAS DE DATOS INTERNOS (Hardcodeadas) 
# ========================================

# Base de datos principal
DATABASE_PATH = DATA_DIR / 'videos.db'

# Thumbnails generados
THUMBNAILS_PATH = DATA_DIR / 'thumbnails'

# Base de datos de caracteres/personajes
CHARACTER_DATABASE_PATH = DATA_DIR / 'character_database.json'

# Directorio de caras conocidas para reconocimiento facial
KNOWN_FACES_PATH = BASE_DIR / 'caras_conocidas'

# Directorio de backups del sistema
BACKUPS_PATH = BASE_DIR / 'backups'

# Directorio de videos procesados
PROCESSED_VIDEOS_PATH = BASE_DIR / 'videos_procesados'

# ========================================
# 🌐 CONFIGURACIÓN DE FLASK
# ========================================

SECRET_KEY = os.getenv('SECRET_KEY', 'tag-flow-v2-secret-key-change-in-production')
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
FLASK_HOST = os.getenv('FLASK_HOST', 'localhost')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

# ========================================
# 🔑 APIs Y SERVICIOS EXTERNOS (Configurables)
# ========================================

# YouTube Data API
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Google Vision API para reconocimiento facial
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Spotify Web API para identificación musical
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# ACRCloud para identificación musical (fallback)
ACRCLOUD_HOST = os.getenv('ACRCLOUD_HOST')
ACRCLOUD_ACCESS_KEY = os.getenv('ACRCLOUD_ACCESS_KEY')
ACRCLOUD_ACCESS_SECRET = os.getenv('ACRCLOUD_ACCESS_SECRET')

# ========================================
# 📱 RUTAS EXTERNAS - 4K DOWNLOADERS (Configurables)
# ========================================

def _clean_path_string(path_str: str) -> str:
    """Limpiar caracteres de control en rutas de Windows"""
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', r'\\', path_str) if path_str else ''

# Bases de datos externas de downloaders
_raw_youtube_db = os.getenv('EXTERNAL_YOUTUBE_DB', 
    r'C:\Users\loler\AppData\Local\4kdownload.com\4K Video Downloader+\4K Video Downloader+\faefbcd1-76a6-4fbc-b730-724f2735eee4.sqlite')
EXTERNAL_YOUTUBE_DB = Path(_clean_path_string(_raw_youtube_db)) if _raw_youtube_db else None

EXTERNAL_TIKTOK_DB = Path(os.getenv('EXTERNAL_TIKTOK_DB', r'D:\4K Tokkit\data.sqlite'))
EXTERNAL_INSTAGRAM_DB = Path(os.getenv('EXTERNAL_INSTAGRAM_DB', r'D:\4K Stogram\.stogram.sqlite'))

# Carpetas organizadas de videos descargados
ORGANIZED_BASE_PATH = Path(os.getenv('ORGANIZED_BASE_PATH', r'D:\4K All'))
ORGANIZED_YOUTUBE_PATH = ORGANIZED_BASE_PATH / 'Youtube'
ORGANIZED_TIKTOK_PATH = ORGANIZED_BASE_PATH / 'Tiktok'  
ORGANIZED_INSTAGRAM_PATH = ORGANIZED_BASE_PATH / 'Instagram'

# ========================================
# ⚙️ CONFIGURACIONES DE PROCESAMIENTO
# ========================================

# Thumbnails
THUMBNAIL_SIZE = tuple(map(int, os.getenv('THUMBNAIL_SIZE', '320x180').split('x')))
THUMBNAIL_MODE = os.getenv('THUMBNAIL_MODE', 'balanced')  # ultra_fast, balanced, quality, gpu, auto

# Procesamiento concurrente
MAX_CONCURRENT_PROCESSING = int(os.getenv('MAX_CONCURRENT_PROCESSING', 3))

# Deep Learning (reconocimiento facial)
USE_GPU_DEEPFACE = os.getenv('USE_GPU_DEEPFACE', 'true').lower() == 'true'
DEEPFACE_MODEL = os.getenv('DEEPFACE_MODEL', 'ArcFace')

# Optimizaciones de base de datos
USE_OPTIMIZED_DATABASE = os.getenv('USE_OPTIMIZED_DATABASE', 'true').lower() == 'true'
DATABASE_CACHE_TTL = int(os.getenv('DATABASE_CACHE_TTL', '300'))  # 5 minutos
DATABASE_CACHE_SIZE = int(os.getenv('DATABASE_CACHE_SIZE', '1000'))
ENABLE_PERFORMANCE_METRICS = os.getenv('ENABLE_PERFORMANCE_METRICS', 'true').lower() == 'true'

# ========================================
# 🛠️ FUNCIONES UTILITARIAS
# ========================================

def ensure_directories():
    """Crear directorios necesarios del proyecto"""
    essential_dirs = [
        DATA_DIR,
        THUMBNAILS_PATH,
        KNOWN_FACES_PATH,
        BACKUPS_PATH,
        PROCESSED_VIDEOS_PATH
    ]
    
    for directory in essential_dirs:
        directory.mkdir(parents=True, exist_ok=True)

def validate_config():
    """Validar configuración y reportar problemas"""
    warnings = []
    
    # APIs críticas
    if not YOUTUBE_API_KEY:
        warnings.append("⚠️  YOUTUBE_API_KEY no configurada - funcionalidad de música limitada")
        
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        warnings.append("⚠️  Credenciales de Spotify no configuradas - identificación musical limitada")
    
    # Bases de datos externas (informativo, no crítico)
    if EXTERNAL_YOUTUBE_DB and not EXTERNAL_YOUTUBE_DB.exists():
        warnings.append(f"ℹ️  BD de 4K YouTube Downloader no encontrada: {EXTERNAL_YOUTUBE_DB}")
    
    if not EXTERNAL_TIKTOK_DB.exists():
        warnings.append(f"ℹ️  BD de 4K Tokkit no encontrada: {EXTERNAL_TIKTOK_DB}")
        
    if not EXTERNAL_INSTAGRAM_DB.exists():
        warnings.append(f"ℹ️  BD de 4K Stogram no encontrada: {EXTERNAL_INSTAGRAM_DB}")
    
    # Carpetas organizadas (informativo)
    if not ORGANIZED_BASE_PATH.exists():
        warnings.append(f"ℹ️  Carpeta organizada no encontrada: {ORGANIZED_BASE_PATH}")
    
    return warnings

def get_config_summary():
    """Obtener resumen de configuración para debugging"""
    return {
        'base_dir': str(BASE_DIR),
        'data_dir': str(DATA_DIR),
        'database_path': str(DATABASE_PATH),
        'thumbnails_path': str(THUMBNAILS_PATH),
        'external_dbs_available': {
            'youtube': EXTERNAL_YOUTUBE_DB and EXTERNAL_YOUTUBE_DB.exists() if EXTERNAL_YOUTUBE_DB else False,
            'tiktok': EXTERNAL_TIKTOK_DB.exists(),
            'instagram': EXTERNAL_INSTAGRAM_DB.exists()
        },
        'organized_folders_available': ORGANIZED_BASE_PATH.exists(),
        'apis_configured': {
            'youtube': bool(YOUTUBE_API_KEY),
            'spotify': bool(SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET),
            'google_vision': bool(GOOGLE_APPLICATION_CREDENTIALS),
            'acrcloud': bool(ACRCLOUD_ACCESS_KEY and ACRCLOUD_ACCESS_SECRET)
        }
    }

# ========================================
# 🚀 INICIALIZACIÓN AUTOMÁTICA
# ========================================

# Crear directorios al importar el módulo
ensure_directories()

# ========================================
# 🔄 COMPATIBILIDAD CON IMPORTS EXISTENTES
# ========================================

# Para mantener compatibilidad con código que usa "from config import config"
import sys
config = sys.modules[__name__]  # Referencia al módulo actual