#!/usr/bin/env python3
"""
Tag-Flow - Script de Instalación y Configuración
Ayuda a configurar el entorno y verificar dependencias
"""

import sys
import subprocess
import os
from pathlib import Path

def print_header():
    """Mostrar header del instalador"""
    print("="*60)
    print("🎬 TAG-FLOW - INSTALADOR AUTOMÁTICO")
    print("="*60)
    print()

def check_python_version():
    """Verificar versión de Python"""
    print("🔍 Verificando versión de Python...")
    
    if sys.version_info < (3, 8):
        print("❌ ERROR: Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detectado")
    return True

def install_dependencies():
    """Instalar dependencias"""
    print("\n📦 Instalando dependencias...")
    
    try:
        # Actualizar pip primero
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Instalar requirements
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✅ Dependencias instaladas correctamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        print("\n🔧 Intenta instalar manualmente:")
        print("   pip install -r requirements.txt")
        return False

def setup_directories():
    """Crear estructura de directorios"""
    print("\n📁 Configurando estructura de directorios...")
    
    dirs = [
        "data",
        "caras_conocidas", 
        "videos_a_procesar"
    ]
    
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir()
            print(f"  ✅ Creado: {dir_name}/")
        else:
            print(f"  ✓ Ya existe: {dir_name}/")

def check_env_file():
    """Verificar archivo .env"""
    print("\n🔐 Verificando configuración...")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Archivo .env no encontrado")
        return False
    
    # Leer y verificar contenido
    with open(env_path, 'r') as f:
        content = f.read()
    
    if "tu_clave_de_api_aqui" in content:
        print("⚠️  Archivo .env encontrado pero sin configurar")
        print("   📝 Edita el archivo .env y añade tu clave de API real")
        return False
    
    print("✅ Archivo .env configurado")
    return True

def test_imports():
    """Probar imports principales"""
    print("\n🧪 Probando imports de librerías...")
    
    test_modules = [
        ("pandas", "Manipulación de datos"),
        ("streamlit", "Aplicación web"),
        ("cv2", "OpenCV para video"),
        ("face_recognition", "Reconocimiento facial"),
        ("moviepy.editor", "Edición de video")
    ]
    
    all_ok = True
    for module, description in test_modules:
        try:
            __import__(module)
            print(f"  ✅ {module} - {description}")
        except ImportError as e:
            print(f"  ❌ {module} - Error: {e}")
            all_ok = False
    
    return all_ok

def create_example_structure():
    """Crear estructura de ejemplo"""
    print("\n📝 Creando ejemplos...")
    
    # Crear carpeta de ejemplo
    example_creator = Path("videos_a_procesar/Ejemplo_Creador")
    if not example_creator.exists():
        example_creator.mkdir(parents=True)
        
        # Crear archivo de instrucciones
        instructions = """# Carpeta de Ejemplo

Coloca aquí los videos de este creador.

Formatos soportados: .mp4, .mov, .avi, .mkv, .wmv, .flv, .webm

Después ejecuta: python 1_script_analisis.py
"""
        with open(example_creator / "INSTRUCCIONES.txt", 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print("  ✅ Creada carpeta de ejemplo: videos_a_procesar/Ejemplo_Creador/")

def show_next_steps():
    """Mostrar próximos pasos"""
    print("\n" + "="*60)
    print("🎉 ¡INSTALACIÓN COMPLETADA!")
    print("="*60)
    print()
    print("📋 PRÓXIMOS PASOS:")
    print()
    print("1. 🖼️  Añade fotos de personajes en 'caras_conocidas/'")
    print("   └─ Nombra los archivos como quieres que aparezca el personaje")
    print()
    print("2. 🎵 Configura API de música (opcional):")
    print("   └─ Edita '.env' y añade tu clave de API")
    print("   └─ APIs recomendadas: ACRCloud, AudD")
    print()
    print("3. 📹 Organiza videos en 'videos_a_procesar/':")
    print("   └─ Crea carpetas por creador")
    print("   └─ Coloca videos dentro de cada carpeta")
    print()
    print("4. 🔧 Procesa videos:")
    print("   └─ python 1_script_analisis.py")
    print()
    print("5. 🌐 Explora con la aplicación web:")
    print("   └─ streamlit run 2_app_visual.py")
    print()
    print("📚 Más ayuda: Lee el README.md")
    print("="*60)

def main():
    """Función principal del instalador"""
    print_header()
    
    # Verificaciones
    if not check_python_version():
        return False
    
    # Instalaciones
    if not install_dependencies():
        print("\n⚠️  Continúa con configuración manual")
    
    # Configuración
    setup_directories()
    check_env_file()
    
    # Pruebas
    if not test_imports():
        print("\n⚠️  Algunas librerías no se importaron correctamente")
        print("   Intenta: pip install -r requirements.txt")
    
    # Ejemplos
    create_example_structure()
    
    # Instrucciones finales
    show_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Instalación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante la instalación: {e}")
        print("   Revisa el README.md para instalación manual")
