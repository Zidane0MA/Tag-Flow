#!/usr/bin/env python3
"""
Tag-Flow - Diagnóstico de MoviePy
Script para diagnosticar problemas con MoviePy y encontrar la configuración correcta
"""

import sys
from pathlib import Path

def test_moviepy_import():
    """Probar diferentes formas de importar MoviePy"""
    print("🎬 Diagnóstico de MoviePy")
    print("=" * 40)
    
    # Intentar diferentes importaciones
    import_methods = [
        ("from moviepy import VideoFileClip", "moviepy", "VideoFileClip"),
        ("from moviepy.editor import VideoFileClip", "moviepy.editor", "VideoFileClip"),
        ("import moviepy", "moviepy", None),
    ]
    
    successful_imports = []
    
    for import_str, module_name, class_name in import_methods:
        try:
            print(f"📦 Intentando: {import_str}")
            
            if module_name == "moviepy" and class_name == "VideoFileClip":
                from moviepy import VideoFileClip
                successful_imports.append(("from moviepy import VideoFileClip", VideoFileClip))
                print(f"  ✅ Éxito")
                
            elif module_name == "moviepy.editor" and class_name == "VideoFileClip":
                from moviepy.editor import VideoFileClip
                successful_imports.append(("from moviepy.editor import VideoFileClip", VideoFileClip))
                print(f"  ✅ Éxito")
                
            elif module_name == "moviepy":
                import moviepy
                print(f"  ✅ Éxito - Versión: {getattr(moviepy, '__version__', 'Desconocida')}")
                
        except ImportError as e:
            print(f"  ❌ Error: {e}")
        except Exception as e:
            print(f"  ⚠️ Error inesperado: {e}")
    
    return successful_imports

def test_video_methods(VideoFileClip_class):
    """Probar métodos disponibles en VideoFileClip"""
    print(f"\n🔍 Analizando métodos de VideoFileClip...")
    
    # Crear un video ficticio muy corto para probar
    test_video_path = Path(__file__).parent / "videos_a_procesar"
    
    # Buscar cualquier video para pruebas
    video_files = []
    if test_video_path.exists():
        for ext in ['.mp4', '.mov', '.avi', '.mkv']:
            video_files.extend(list(test_video_path.rglob(f"*{ext}")))
    
    if not video_files:
        print("⚠️ No se encontraron videos para probar")
        print("   Métodos disponibles en la clase:")
        
        # Mostrar métodos disponibles
        methods = [method for method in dir(VideoFileClip_class) if not method.startswith('_')]
        for method in sorted(methods):
            if 'clip' in method.lower():
                print(f"    🎯 {method}")
            else:
                print(f"    • {method}")
        return
    
    test_video = video_files[0]
    print(f"📹 Probando con: {test_video.name}")
    
    try:
        # Cargar video
        video = VideoFileClip_class(str(test_video))
        print(f"  ✅ Video cargado correctamente")
        print(f"  ⏱️ Duración: {getattr(video, 'duration', 'No disponible')}")
        
        # Probar métodos de subclip
        subclip_methods = ['subclip', 'subclipped', 'cut']
        
        print(f"\n🔧 Probando métodos de extracción:")
        
        for method_name in subclip_methods:
            if hasattr(video, method_name):
                print(f"  ✅ {method_name}: DISPONIBLE")
                
                # Probar el método
                try:
                    method = getattr(video, method_name)
                    if video.duration and video.duration > 5:
                        # Probar extraer 2 segundos del principio
                        if method_name in ['subclip', 'subclipped']:
                            test_clip = method(0, 2)
                        else:
                            test_clip = method(0, 2)
                        print(f"    ✅ {method_name} funciona correctamente")
                        test_clip.close()
                    else:
                        print(f"    ⚠️ Video muy corto para probar {method_name}")
                        
                except Exception as e:
                    print(f"    ❌ Error con {method_name}: {e}")
            else:
                print(f"  ❌ {method_name}: NO DISPONIBLE")
        
        # Probar audio
        print(f"\n🔊 Probando audio:")
        if hasattr(video, 'audio') and video.audio is not None:
            print(f"  ✅ Audio disponible")
            
            # Probar métodos de subclip en audio
            for method_name in subclip_methods:
                if hasattr(video.audio, method_name):
                    print(f"    ✅ audio.{method_name}: DISPONIBLE")
                else:
                    print(f"    ❌ audio.{method_name}: NO DISPONIBLE")
        else:
            print(f"  ❌ Sin audio o audio no accesible")
        
        video.close()
        
    except Exception as e:
        print(f"  ❌ Error cargando video: {e}")

def recommend_configuration(successful_imports):
    """Recomendar configuración basada en los tests"""
    print(f"\n💡 RECOMENDACIONES:")
    print("=" * 40)
    
    if not successful_imports:
        print("❌ No se pudo importar MoviePy correctamente")
        print("\n🔧 Soluciones:")
        print("1. Reinstalar MoviePy:")
        print("   pip uninstall moviepy")
        print("   pip install moviepy")
        print("\n2. Si falla, probar versión específica:")
        print("   pip install moviepy==1.0.3")
        return
    
    print("✅ MoviePy se puede importar correctamente")
    
    for import_str, VideoFileClip_class in successful_imports:
        print(f"\n📝 Configuración recomendada:")
        print(f"   {import_str}")
        
        # Test métodos
        test_video_methods(VideoFileClip_class)
        break  # Solo probar el primero que funcione

def create_fixed_script():
    """Crear script corregido basado en el diagnóstico"""
    print(f"\n🛠️ SCRIPT CORREGIDO:")
    print("=" * 40)
    print("""
He actualizado el script 1_script_analisis_con_musica.py con:

✅ Múltiples métodos de extracción de subclip
✅ Manejo robusto de errores
✅ Limpieza automática de recursos
✅ Debugging mejorado

El script ahora intentará automáticamente:
1. video.subclip() - Método estándar
2. video.subclipped() - Método alternativo  
3. video.audio.subclip() - Directo en audio
4. video.audio completo - Como fallback

¡Prueba ejecutar de nuevo!
    """)

def main():
    """Función principal"""
    try:
        successful_imports = test_moviepy_import()
        recommend_configuration(successful_imports)
        create_fixed_script()
        
        print(f"\n🚀 PRÓXIMOS PASOS:")
        print("1. Ejecuta el script corregido: python 1_script_analisis_con_musica.py")
        print("2. Si sigue fallando, reporta el error específico")
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")

if __name__ == "__main__":
    main()
