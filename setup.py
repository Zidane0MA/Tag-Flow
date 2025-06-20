"""
Tag-Flow V2 - Script de Configuración Inicial
Asistente para configurar APIs y directorios
"""

import os
import sys
from pathlib import Path
import json
import subprocess
from urllib.parse import urlparse

def main():
    """Configuración inicial interactiva"""
    print("🎬 Tag-Flow V2 - Configuración Inicial")
    print("=" * 50)
    
    # Verificar Python
    if sys.version_info < (3, 12):
        print("⚠️  Se recomienda Python 3.12 o superior")
        print(f"   Versión actual: {sys.version}")
    else:
        print(f"✅ Python {sys.version.split()[0]} - OK")
    
    # Crear configuración
    config = load_existing_config()
    
    print("\n📋 Configuración de APIs")
    configure_apis(config)
    
    print("\n📁 Configuración de Directorios") 
    configure_directories(config)
    
    print("\n🔧 Configuración de Procesamiento")
    configure_processing(config)
    
    # Guardar configuración
    save_config(config)
    
    print("\n🚀 Configuración completa!")
    print_next_steps()

def load_existing_config():
    """Cargar configuración existente"""
    config = {}
    env_path = Path('.env')
    
    if env_path.exists():
        print("📝 Cargando configuración existente...")
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value.strip('"')
    
    return config

def configure_apis(config):
    """Configurar claves de API"""
    
    # YouTube API
    print("\n🔴 YouTube Data API v3")
    print("   1. Ve a: https://console.developers.google.com/")
    print("   2. Crea un proyecto nuevo")
    print("   3. Habilita 'YouTube Data API v3'")
    print("   4. Crea credenciales (API Key)")
    
    current = config.get('YOUTUBE_API_KEY', '')
    youtube_key = input(f"   Clave YouTube API [{current or 'vacío'}]: ").strip()
    if youtube_key:
        config['YOUTUBE_API_KEY'] = youtube_key
    
    # Spotify API
    print("\n🟢 Spotify Web API")
    print("   1. Ve a: https://developer.spotify.com/dashboard/")
    print("   2. Crea una aplicación nueva")
    print("   3. Copia Client ID y Client Secret")
    
    current_id = config.get('SPOTIFY_CLIENT_ID', '')
    spotify_id = input(f"   Spotify Client ID [{current_id or 'vacío'}]: ").strip()
    if spotify_id:
        config['SPOTIFY_CLIENT_ID'] = spotify_id
    
    current_secret = config.get('SPOTIFY_CLIENT_SECRET', '')
    spotify_secret = input(f"   Spotify Client Secret [{current_secret or 'vacío'}]: ").strip()
    if spotify_secret:
        config['SPOTIFY_CLIENT_SECRET'] = spotify_secret
    
    # Google Vision API
    print("\n🔵 Google Vision API (opcional)")
    print("   1. Ve a: https://console.cloud.google.com/")
    print("   2. Habilita 'Vision API'")
    print("   3. Crea cuenta de servicio y descarga JSON")
    print("   4. Guarda el archivo como 'config/gcp_credentials.json'")
    
    vision_configured = input("   ¿Has configurado Google Vision? [y/N]: ").lower() == 'y'
    if vision_configured:
        config['GOOGLE_APPLICATION_CREDENTIALS'] = "config/gcp_credentials.json"
        
        # Crear directorio config si no existe
        config_dir = Path('config')
        config_dir.mkdir(exist_ok=True)
        
        if not Path('config/gcp_credentials.json').exists():
            print("   ⚠️  Recuerda colocar el archivo JSON en config/gcp_credentials.json")

def configure_directories(config):
    """Configurar directorios de trabajo"""
    
    # Directorio de videos de entrada
    print("\n📂 Directorio de videos a analizar")
    current_videos = config.get('VIDEOS_BASE_PATH', '')
    videos_path = input(f"   Ruta de videos [{current_videos or 'D:/Videos_TikTok'}]: ").strip()
    
    if not videos_path:
        videos_path = current_videos or 'D:/Videos_TikTok'
    
    videos_path_obj = Path(videos_path)
    if not videos_path_obj.exists():
        create = input(f"   La ruta no existe. ¿Crear directorio? [Y/n]: ").lower()
        if create != 'n':
            try:
                videos_path_obj.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ Directorio creado: {videos_path}")
            except Exception as e:
                print(f"   ❌ Error creando directorio: {e}")
    
    config['VIDEOS_BASE_PATH'] = str(videos_path_obj)
    
    # 4K Video Downloader (opcional)
    print("\n💾 4K Video Downloader (opcional)")
    print("   Si usas 4K Video Downloader, se pueden importar metadatos automáticamente")
    
    has_4k = input("   ¿Usas 4K Video Downloader? [y/N]: ").lower() == 'y'
    if has_4k:
        print("   Busca el archivo de base de datos en:")
        print("   Windows: C:/Users/[usuario]/AppData/Local/4kdownload.com/...")
        print("   macOS: ~/Library/Application Support/4kdownload.com/...")
        
        current_4k = config.get('DOWNLOADER_DB_PATH', '')
        downloader_path = input(f"   Ruta BD 4K Downloader [{current_4k or 'vacío'}]: ").strip()
        
        if downloader_path:
            if Path(downloader_path).exists():
                config['DOWNLOADER_DB_PATH'] = downloader_path
                print("   ✅ Base de datos encontrada")
            else:
                print("   ⚠️  Archivo no encontrado, verifica la ruta")

def configure_processing(config):
    """Configurar opciones de procesamiento"""
    
    print("\n⚙️ Opciones de procesamiento")
    
    # Tamaño de thumbnails
    current_size = config.get('THUMBNAIL_SIZE', '320x180')
    print(f"   Tamaño de thumbnails actual: {current_size}")
    
    sizes = {
        '1': '320x180',
        '2': '480x270', 
        '3': '640x360',
        '4': 'personalizado'
    }
    
    print("   Opciones:")
    for key, size in sizes.items():
        print(f"   {key}. {size}")
    
    choice = input("   Selecciona tamaño [1]: ").strip() or '1'
    
    if choice == '4':
        custom_size = input("   Tamaño personalizado (ej: 400x225): ").strip()
        if 'x' in custom_size:
            config['THUMBNAIL_SIZE'] = custom_size
    else:
        config['THUMBNAIL_SIZE'] = sizes.get(choice, '320x180')
    
    # Procesamiento concurrente
    current_workers = config.get('MAX_CONCURRENT_PROCESSING', '3')
    workers = input(f"   Procesos concurrentes [{current_workers}]: ").strip()
    if workers.isdigit():
        config['MAX_CONCURRENT_PROCESSING'] = workers
    
    # GPU para DeepFace
    current_gpu = config.get('USE_GPU_DEEPFACE', 'true')
    use_gpu = input(f"   ¿Usar GPU para reconocimiento facial? [Y/n]: ").lower()
    config['USE_GPU_DEEPFACE'] = 'false' if use_gpu == 'n' else 'true'

def save_config(config):
    """Guardar configuración en .env"""
    print("\n💾 Guardando configuración...")
    
    env_content = [
        "# Tag-Flow V2 - Configuración generada automáticamente",
        f"# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "# YouTube Data API v3 (GRATIS - 10k consultas/día)",
        f'YOUTUBE_API_KEY="{config.get("YOUTUBE_API_KEY", "")}"',
        "",
        "# Google Vision API",
        f'GOOGLE_APPLICATION_CREDENTIALS="{config.get("GOOGLE_APPLICATION_CREDENTIALS", "")}"',
        "",
        "# Spotify Web API (GRATIS)",
        f'SPOTIFY_CLIENT_ID="{config.get("SPOTIFY_CLIENT_ID", "")}"',
        f'SPOTIFY_CLIENT_SECRET="{config.get("SPOTIFY_CLIENT_SECRET", "")}"',
        "",
        "# 4K Video Downloader Integration",
        f'DOWNLOADER_DB_PATH="{config.get("DOWNLOADER_DB_PATH", "")}"',
        "",
        "# Configuración de Procesamiento",
        f'THUMBNAIL_SIZE="{config.get("THUMBNAIL_SIZE", "320x180")}"',
        f'MAX_CONCURRENT_PROCESSING={config.get("MAX_CONCURRENT_PROCESSING", "3")}',
        f'USE_GPU_DEEPFACE={config.get("USE_GPU_DEEPFACE", "true")}',
        f'DEEPFACE_MODEL="ArcFace"',
        "",
        "# Configuración de la aplicación Flask",
        f'FLASK_ENV="development"',
        f'FLASK_DEBUG=true',
        f'FLASK_HOST="localhost"',
        f'FLASK_PORT=5000',
        "",
        "# Rutas de trabajo",
        f'VIDEOS_BASE_PATH="{config.get("VIDEOS_BASE_PATH", "")}"',
        f'THUMBNAILS_PATH="data/thumbnails"',
        f'PROCESSED_VIDEOS_PATH="videos_procesados"',
        "",
        "# ACRCloud (fallback - mantener)",
        f'ACRCLOUD_HOST="identify-eu-west-1.acrcloud.com"',
        f'ACRCLOUD_ACCESS_KEY="2e0484a82ca8ab4069838fdffed5317b"',
        f'ACRCLOUD_ACCESS_SECRET="gD4cv7Ec6as3b7nOvu7oEAsv9ge5iu7Jk6UdQd24"',
        ""
    ]
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write('\n'.join(env_content))
    
    print("✅ Configuración guardada en .env")

def print_next_steps():
    """Mostrar pasos siguientes"""
    print("\n🎯 Siguientes pasos:")
    print("   1. Instalar dependencias:")
    print("      pip install -r requirements.txt")
    print("")
    print("   2. (Opcional) Añadir fotos de personajes:")
    print("      - caras_conocidas/genshin/zhongli.jpg")
    print("      - caras_conocidas/honkai/firefly.jpg")
    print("")
    print("   3. Procesar videos:")
    print("      python main.py")
    print("")
    print("   4. Lanzar interfaz web:")
    print("      python app.py")
    print("      http://localhost:5000")
    print("")
    print("📖 Ver README.md para más información")

if __name__ == "__main__":
    from datetime import datetime
    main()