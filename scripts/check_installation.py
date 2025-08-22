"""
Tag-Flow V2 - Verificador de Instalación
Script para diagnosticar problemas de configuración e instalación
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path
import json

def check_python_version():
    """Verificar versión de Python"""
    print("🐍 Python")
    version = sys.version_info
    
    if version >= (3, 12):
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - Excelente")
        return True
    elif version >= (3, 10):
        print(f"   ⚠️  Python {version.major}.{version.minor}.{version.micro} - Funcional pero se recomienda 3.12+")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Se requiere Python 3.10+")
        return False

def check_dependencies():
    """Verificar dependencias instaladas"""
    print("\n📦 Dependencias")
    
    required_packages = {
        'flask': 'Flask',
        'opencv-python': 'OpenCV',
        'pillow': 'Pillow (PIL)',
        'requests': 'Requests',
        'python-dotenv': 'Python-dotenv',
        'moviepy': 'MoviePy',
    }
    
    optional_packages = {
        'deepface': 'DeepFace (reconocimiento facial)',
        'google-cloud-vision': 'Google Vision API',
        'spotipy': 'Spotify API',
        'googleapiclient': 'YouTube API',
    }
    
    all_good = True
    
    # Verificar paquetes requeridos
    print("   Paquetes requeridos:")
    for package, name in required_packages.items():
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - Instalar con: pip install {package}")
            all_good = False
    
    # Verificar paquetes opcionales
    print("\n   Paquetes opcionales:")
    for package, name in optional_packages.items():
        try:
            if package == 'googleapiclient':
                importlib.import_module('googleapiclient.discovery')
            else:
                importlib.import_module(package.replace('-', '_'))
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ⚠️  {name} - Instalar con: pip install {package}")
    
    return all_good

def check_ffmpeg():
    """Verificar instalación de FFmpeg"""
    print("\n🎬 FFmpeg")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"   ✅ {version_line}")
            return True
        else:
            print("   ❌ FFmpeg no funciona correctamente")
            return False
    except FileNotFoundError:
        print("   ❌ FFmpeg no instalado")
        print("      Instalar desde: https://ffmpeg.org/download.html")
        return False
    except subprocess.TimeoutExpired:
        print("   ❌ FFmpeg timeout")
        return False

def check_config_file():
    """Verificar archivo de configuración"""
    print("\n⚙️ Archivo de Configuración")
    
    env_path = Path('.env')
    if not env_path.exists():
        print("   ❌ Archivo .env no encontrado")
        print("      Ejecutar: python setup.py")
        return False
    
    print("   ✅ Archivo .env existe")
    
    # Leer configuración
    config = {}
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value.strip('"')
    except Exception as e:
        print(f"   ❌ Error leyendo .env: {e}")
        return False
    
    # Verificar claves importantes
    api_keys = {
        'YOUTUBE_API_KEY': 'YouTube Data API',
        'SPOTIFY_CLIENT_ID': 'Spotify Client ID',
        'SPOTIFY_CLIENT_SECRET': 'Spotify Client Secret',
        'GOOGLE_APPLICATION_CREDENTIALS': 'Google Vision API'
    }
    
    print("   Claves de API configuradas:")
    any_api = False
    for key, name in api_keys.items():
        value = config.get(key, '')
        if value and value not in ['', 'TU_CLAVE_AQUI', 'tu_clave_youtube_aqui']:
            print(f"   ✅ {name}")
            any_api = True
        else:
            print(f"   ⚠️  {name} - No configurada")
    
    if not any_api:
        print("   ❌ No hay APIs configuradas - Funcionalidad limitada")
    
    return True

def check_directories():
    """Verificar directorios necesarios"""
    print("\n📁 Directorios")
    
    directories = [
        ('src', 'Código fuente'),
        ('templates', 'Templates HTML'),
        ('static', 'Archivos estáticos'),
        ('data', 'Datos de la aplicación'),
        ('caras_conocidas', 'Caras conocidas'),
    ]
    
    all_exist = True
    for dir_name, description in directories:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"   ✅ {description} ({dir_name})")
        else:
            print(f"   ❌ {description} ({dir_name}) - Faltante")
            all_exist = False
    
    return all_exist

def check_database():
    """Verificar base de datos"""
    print("\n🗄️ Base de Datos")
    
    try:
        # Importar configuración
        sys.path.append(str(Path.cwd() / 'src'))
        from config import config
        
        db_path = config.DATABASE_PATH
        
        if db_path.exists():
            print(f"   ✅ Base de datos existe: {db_path}")
            
            # Verificar contenido
            import sqlite3
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM videos")
                video_count = cursor.fetchone()[0]
                print(f"   📊 Videos en base de datos: {video_count}")
        else:
            print(f"   ⚠️  Base de datos no existe: {db_path}")
            print("      Se creará automáticamente al ejecutar main.py")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error verificando base de datos: {e}")
        return False

def check_gpu():
    """Verificar disponibilidad de GPU"""
    print("\n🎮 GPU (Opcional)")
    
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            print(f"   ✅ GPU CUDA disponible: {gpu_name}")
            print(f"   📊 GPUs detectadas: {gpu_count}")
            return True
        else:
            print("   ⚠️  GPU CUDA no disponible - Se usará CPU")
            return False
    except ImportError:
        print("   ⚠️  PyTorch no instalado - No se puede verificar GPU")
        return False

def test_basic_functionality():
    """Probar funcionalidad básica"""
    print("\n🧪 Pruebas Básicas")
    
    try:
        # Probar importación de módulos principales
        sys.path.append(str(Path.cwd() / 'src'))
        
        print("   Importando módulos...")
        from config import config
        print("   ✅ Configuración")
        
        from src.service_factory import get_database
        db = get_database()
        print("   ✅ Base de datos")
        
        from src.video_processor import video_processor
        print("   ✅ Procesador de video")
        
        from src.music_recognition import music_recognizer
        print("   ✅ Reconocimiento musical")
        
        from src.face_recognition import face_recognizer
        print("   ✅ Reconocimiento facial")
        
        # Probar Flask
        from app import app
        print("   ✅ Aplicación Flask")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en pruebas básicas: {e}")
        return False

def generate_diagnosis_report():
    """Generar reporte de diagnóstico"""
    print("\n📋 Generando reporte de diagnóstico...")
    
    diagnosis = {
        'timestamp': str(Path(__file__).parent.absolute()),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'platform': sys.platform,
        'checks': {}
    }
    
    # Ejecutar todas las verificaciones y guardar resultados
    checks = [
        ('python', check_python_version),
        ('dependencies', check_dependencies),
        ('ffmpeg', check_ffmpeg),
        ('config', check_config_file),
        ('directories', check_directories),
        ('database', check_database),
        ('gpu', check_gpu),
        ('functionality', test_basic_functionality)
    ]
    
    for check_name, check_func in checks:
        try:
            diagnosis['checks'][check_name] = check_func()
        except Exception as e:
            diagnosis['checks'][check_name] = f"Error: {e}"
    
    # Guardar reporte
    report_path = 'diagnosis_report.json'
    with open(report_path, 'w') as f:
        json.dump(diagnosis, f, indent=2)
    
    print(f"   ✅ Reporte guardado: {report_path}")
    return diagnosis

def print_summary(diagnosis):
    """Imprimir resumen final"""
    print("\n" + "="*50)
    print("📊 RESUMEN DE DIAGNÓSTICO")
    print("="*50)
    
    passed = sum(1 for result in diagnosis['checks'].values() if result is True)
    total = len(diagnosis['checks'])
    
    if passed == total:
        print("🎉 ¡Instalación perfecta! Todo funcionando correctamente.")
    elif passed >= total * 0.8:
        print("✅ Instalación buena. Algunos componentes opcionales faltan.")
    elif passed >= total * 0.6:
        print("⚠️  Instalación parcial. Revisa los componentes faltantes.")
    else:
        print("❌ Instalación problemática. Se requiere más configuración.")
    
    print(f"\nVerificaciones: {passed}/{total} exitosas")
    
    # Mostrar próximos pasos
    print("\n🎯 Próximos pasos:")
    
    if not diagnosis['checks'].get('dependencies'):
        print("   1. Instalar dependencias: pip install -r requirements.txt")
    
    if not diagnosis['checks'].get('config'):
        print("   2. Configurar APIs: python setup.py")
    
    if not diagnosis['checks'].get('ffmpeg'):
        print("   3. Instalar FFmpeg: https://ffmpeg.org/download.html")
    
    print("   4. Procesar videos: python main.py")
    print("   5. Lanzar web app: python app.py")

def main():
    """Función principal"""
    print("🔍 Tag-Flow V2 - Verificador de Instalación")
    print("="*50)
    
    # Ejecutar verificaciones
    diagnosis = generate_diagnosis_report()
    
    # Mostrar resumen
    print_summary(diagnosis)

if __name__ == "__main__":
    main()