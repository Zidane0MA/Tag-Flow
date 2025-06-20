#!/usr/bin/env python3
"""
Tag-Flow - Instalador de Dependencias
Script para instalar todas las dependencias necesarias
"""

import sys
import subprocess
import os

def run_command(cmd, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"  ✅ {description} - Completado")
            return True
        else:
            print(f"  ⚠️ {description} - Advertencia: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ {description} - Error: {e}")
        return False

def install_dependencies():
    """Instalar todas las dependencias de Tag-Flow"""
    print("🎬 Tag-Flow - Instalador de Dependencias")
    print("="*50)
    
    # Lista de instalaciones en orden correcto
    installations = [
        ("python -m pip install --upgrade pip", "Actualizando pip"),
        ("pip install pandas", "Instalando pandas"),
        ("pip install streamlit", "Instalando streamlit"),
        ("pip install opencv-python", "Instalando opencv-python"),
        ("pip install python-dotenv", "Instalando python-dotenv"),
        ("pip install requests", "Instalando requests"),
        ("pip install pillow", "Instalando pillow"),
        ("pip install numpy", "Instalando numpy"),
        ("pip install moviepy", "Instalando moviepy"),
    ]
    
    # Dependencias opcionales (face_recognition)
    optional_installations = [
        ("pip install cmake", "Instalando cmake"),
        ("pip install dlib", "Instalando dlib"),
        ("pip install face_recognition", "Instalando face_recognition"),
    ]
    
    print("📦 Instalando dependencias básicas...")
    basic_success = 0
    for cmd, desc in installations:
        if run_command(cmd, desc):
            basic_success += 1
    
    print(f"\n📊 Dependencias básicas: {basic_success}/{len(installations)} instaladas")
    
    # Preguntar por face_recognition
    print("\n🤔 ¿Quieres intentar instalar face_recognition? (puede fallar)")
    install_face = input("s/n: ").lower().strip() in ['s', 'si', 'y', 'yes']
    
    if install_face:
        print("\n📦 Instalando dependencias opcionales...")
        optional_success = 0
        for cmd, desc in optional_installations:
            if run_command(cmd, desc):
                optional_success += 1
        print(f"📊 Dependencias opcionales: {optional_success}/{len(optional_installations)} instaladas")
    
    # Verificar instalación
    print("\n🧪 Verificando instalación...")
    test_imports = [
        ("pandas", "Manipulación de datos"),
        ("streamlit", "Aplicación web"),
        ("cv2", "OpenCV"),
        ("dotenv", "Variables de entorno"),
        ("requests", "HTTP requests"),
    ]
    
    working_imports = 0
    for module, desc in test_imports:
        try:
            __import__(module)
            print(f"  ✅ {module} - {desc}")
            working_imports += 1
        except ImportError:
            print(f"  ❌ {module} - {desc}")
    
    # Verificar moviepy específicamente
    try:
        from moviepy.editor import VideoFileClip
        print(f"  ✅ moviepy.editor - Edición de video")
        working_imports += 1
    except ImportError:
        print(f"  ❌ moviepy.editor - Edición de video")
    
    # Verificar face_recognition si se instaló
    if install_face:
        try:
            import face_recognition
            print(f"  ✅ face_recognition - Reconocimiento facial")
        except ImportError:
            print(f"  ❌ face_recognition - Reconocimiento facial")
    
    print(f"\n📋 Resumen: {working_imports}/{len(test_imports) + 1} módulos básicos funcionando")
    
    if working_imports >= len(test_imports):
        print("🎉 ¡Instalación exitosa! Puedes usar Tag-Flow")
        return True
    else:
        print("⚠️ Algunos módulos fallaron. Usa la versión ultra-básica")
        return False

if __name__ == "__main__":
    install_dependencies()
