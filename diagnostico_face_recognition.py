#!/usr/bin/env python3
"""
Tag-Flow - Diagnóstico de Face Recognition
Script para diagnosticar y solucionar problemas de instalación
"""

import sys
import subprocess
import importlib

def check_installation():
    """Verificar instalación de face_recognition"""
    print("🔍 Diagnóstico de Face Recognition")
    print("="*50)
    
    # Verificar Python
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Ejecutable: {sys.executable}")
    
    # Verificar módulos
    modules_to_check = [
        'face_recognition',
        'face_recognition_models', 
        'dlib',
        'cv2',
        'numpy'
    ]
    
    print("\n📦 Verificando módulos:")
    for module in modules_to_check:
        try:
            mod = importlib.import_module(module)
            if hasattr(mod, '__version__'):
                print(f"  ✅ {module}: {mod.__version__}")
            else:
                print(f"  ✅ {module}: instalado")
        except ImportError as e:
            print(f"  ❌ {module}: NO ENCONTRADO - {e}")
    
    # Verificar face_recognition específicamente
    print("\n🔍 Prueba específica de face_recognition:")
    try:
        import face_recognition
        print("  ✅ face_recognition importado correctamente")
        
        # Probar función básica
        import numpy as np
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        face_recognition.face_locations(test_image)
        print("  ✅ Función face_locations funciona")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    return True

def reinstall_face_recognition():
    """Reinstalar face_recognition completamente"""
    print("\n🔧 Reinstalando face_recognition...")
    
    commands = [
        [sys.executable, "-m", "pip", "uninstall", "-y", "face_recognition"],
        [sys.executable, "-m", "pip", "uninstall", "-y", "face_recognition_models"],
        [sys.executable, "-m", "pip", "uninstall", "-y", "dlib"],
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        [sys.executable, "-m", "pip", "install", "cmake"],
        [sys.executable, "-m", "pip", "install", "dlib"],
        [sys.executable, "-m", "pip", "install", "face_recognition"],
    ]
    
    for cmd in commands:
        try:
            print(f"  Ejecutando: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  ⚠️ Advertencia: {result.stderr}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

def main():
    print("🎬 Tag-Flow - Diagnóstico Face Recognition")
    print("="*50)
    
    if check_installation():
        print("\n✅ ¡Todo funciona correctamente!")
    else:
        print("\n❌ Hay problemas con la instalación")
        
        reinstall = input("\n¿Quieres intentar reinstalar? (s/n): ")
        if reinstall.lower() in ['s', 'si', 'y', 'yes']:
            reinstall_face_recognition()
            print("\n🔄 Verificando instalación después de reinstalar...")
            if check_installation():
                print("\n🎉 ¡Problema solucionado!")
            else:
                print("\n⚠️ Aún hay problemas. Ver soluciones manuales.")

if __name__ == "__main__":
    main()
