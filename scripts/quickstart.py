"""
Tag-Flow V2 - Script de Inicio Rápido
Guía paso a paso para configurar y usar el sistema
"""

import sys
import os
import subprocess
from pathlib import Path
import time

def print_header():
    """Imprimir header del programa"""
    print("🎬" + "="*60 + "🎬")
    print("    TAG-FLOW V2 - SISTEMA DE GESTIÓN DE VIDEOS TIKTOK/MMD")
    print("                   🚀 INICIO RÁPIDO 🚀")
    print("🎬" + "="*60 + "🎬")
    print()

def print_step(step_num, title):
    """Imprimir paso con formato"""
    print(f"\n📋 PASO {step_num}: {title}")
    print("-" * 50)

def wait_for_user():
    """Esperar confirmación del usuario"""
    input("   Presiona Enter para continuar...")

def check_python():
    """Verificar Python"""
    print_step(1, "VERIFICAR PYTHON")
    
    version = sys.version_info
    if version >= (3, 10):
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Se requiere 3.10+")
        print("      Actualiza Python desde: https://python.org")
        return False

def setup_virtual_environment():
    """Configurar entorno virtual (opcional)"""
    print_step(2, "ENTORNO VIRTUAL (OPCIONAL)")
    
    print("   Un entorno virtual aísla las dependencias de este proyecto.")
    print("   Recomendado si tienes otros proyectos Python.")
    print()
    use_venv = input("   ¿Crear entorno virtual? [Y/n]: ").lower()
    
    if use_venv == 'n':
        print("   ⏭️  Saltando entorno virtual - usando Python del sistema")
        return True
    
    venv_name = "tag-flow-env"
    venv_path = Path(venv_name)
    
    if venv_path.exists():
        print(f"   ✅ Entorno virtual {venv_name} ya existe")
        return True
    
    try:
        print(f"   Creando entorno virtual: {venv_name}")
        result = subprocess.run([sys.executable, '-m', 'venv', venv_name], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Entorno virtual creado")
            print("   💡 Para activarlo manualmente usa:")
            if os.name == 'nt':
                print(f"      {venv_name}\\Scripts\\activate")
            else:
                print(f"      source {venv_name}/bin/activate")
            return True
        else:
            print("   ⚠️  Error creando entorno virtual, continuando sin él")
            return True
            
    except Exception as e:
        print(f"   ⚠️  Error: {e}, continuando sin entorno virtual")
        return True

def install_dependencies():
    """Instalar dependencias"""
    print_step(3, "INSTALAR DEPENDENCIAS")
    
    print("   Instalando paquetes de requirements.txt...")
    print("   (Esto puede tomar varios minutos)")
    
    try:
        # Verificar si hay entorno virtual activo
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        if in_venv:
            print("   📦 Usando entorno virtual activo")
        else:
            print("   📦 Instalando en Python del sistema")
        
        # Mostrar comando que se ejecutará
        print("   Ejecutando: pip install -r requirements.txt")
        
        # Ejecutar instalación
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Dependencias instaladas correctamente")
            return True
        else:
            print("   ❌ Error instalando dependencias:")
            print(f"      {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def setup_configuration():
    """Configurar el sistema"""
    print_step(4, "CONFIGURACIÓN INICIAL")
    
    if not Path('setup.py').exists():
        print("   ❌ Archivo setup.py no encontrado")
        return False
    
    print("   Iniciando configuración interactiva...")
    print("   (Se te pedirán las claves de API)")
    
    try:
        # Ejecutar script de configuración
        result = subprocess.run([sys.executable, 'setup.py'], 
                              input='y\n' * 10,  # Respuestas automáticas para testing
                              text=True,
                              capture_output=False)
        
        if result.returncode == 0:
            print("   ✅ Configuración completada")
            return True
        else:
            print("   ⚠️  Configuración con advertencias (normal si no tienes todas las APIs)")
            return True
            
    except Exception as e:
        print(f"   ❌ Error en configuración: {e}")
        return False

def create_example_data():
    """Crear datos de ejemplo"""
    print_step(5, "CREAR DATOS DE EJEMPLO")
    
    print("   ¿Quieres crear personajes de ejemplo para probar el reconocimiento?")
    create = input("   [Y/n]: ").lower()
    
    if create == 'n':
        print("   ⏭️  Saltando creación de ejemplos")
        return True
    
    try:
        print("   Creando personajes de ejemplo...")
        result = subprocess.run([sys.executable, 'create_example_characters.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Personajes de ejemplo creados")
            print("   📝 Ver caras_conocidas/ para personajes placeholder")
            return True
        else:
            print("   ⚠️  Error creando ejemplos (puedes hacerlo manualmente después)")
            return True
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return True

def verify_installation():
    """Verificar instalación"""
    print_step(6, "VERIFICAR INSTALACIÓN")
    
    print("   Ejecutando verificación automática...")
    
    try:
        result = subprocess.run([sys.executable, 'check_installation.py'], 
                              capture_output=True, text=True)
        
        if "instalación perfecta" in result.stdout.lower():
            print("   ✅ Instalación perfecta")
        elif "instalación buena" in result.stdout.lower():
            print("   ✅ Instalación buena")
        else:
            print("   ⚠️  Instalación con advertencias")
            print("      Ver check_installation.py para más detalles")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en verificación: {e}")
        return False

def setup_video_directory():
    """Configurar directorio de videos"""
    print_step(7, "CONFIGURAR DIRECTORIO DE VIDEOS")
    
    print("   Necesitas una carpeta con videos para procesar.")
    print("   Formatos soportados: MP4, AVI, MOV, MKV, WebM")
    print()
    
    video_dir = input("   Ruta de videos [D:/Videos_TikTok]: ").strip()
    if not video_dir:
        video_dir = "D:/Videos_TikTok"
    
    video_path = Path(video_dir)
    
    if not video_path.exists():
        create = input(f"   El directorio no existe. ¿Crear? [Y/n]: ").lower()
        if create != 'n':
            try:
                video_path.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ Directorio creado: {video_path}")
                print("   📁 Copia algunos videos a esta carpeta para continuar")
            except Exception as e:
                print(f"   ❌ Error creando directorio: {e}")
                return False
    else:
        # Contar videos
        video_count = sum(1 for f in video_path.rglob('*') 
                         if f.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.webm'])
        print(f"   ✅ Directorio existe con {video_count} videos")
    
    return True

def first_run():
    """Primera ejecución del sistema"""
    print_step(8, "PRIMERA EJECUCIÓN")
    
    print("   ¡Listo para procesar videos!")
    print()
    print("   Opciones:")
    print("   1. Procesar videos ahora")
    print("   2. Lanzar interfaz web")
    print("   3. Salir (procesar después)")
    
    choice = input("\n   Selecciona [1]: ").strip() or "1"
    
    if choice == "1":
        print("\n   🔄 Procesando videos...")
        print("   (Esto puede tomar tiempo dependiendo de la cantidad)")
        
        try:
            result = subprocess.run([sys.executable, 'main.py'], 
                                  capture_output=False, text=True)
            
            if result.returncode == 0:
                print("   ✅ Procesamiento completado")
            else:
                print("   ⚠️  Procesamiento con advertencias")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    elif choice == "2":
        print("\n   🌐 Lanzando interfaz web...")
        print("   Abrirá en: http://localhost:5000")
        print("   Presiona Ctrl+C para detener")
        
        try:
            subprocess.run([sys.executable, 'app.py'])
        except KeyboardInterrupt:
            print("\n   🛑 Aplicación web detenida")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    else:
        print("   ⏭️  Configuración completa")
    
    return True

def print_final_instructions():
    """Imprimir instrucciones finales"""
    print("\n" + "🎉" + "="*58 + "🎉")
    print("                    ¡CONFIGURACIÓN COMPLETA!")
    print("🎉" + "="*58 + "🎉")
    
    print("\n📚 COMANDOS IMPORTANTES:")
    print("-" * 30)
    print("   🔄 Procesar videos nuevos:")
    print("      python main.py")
    print()
    print("   🌐 Lanzar interfaz web:")
    print("      python app.py")
    print("      → http://localhost:5000")
    print()
    print("   🔧 Mantenimiento:")
    print("      python main.py backup")
    print("      python main.py verify")
    print()
    print("   🩺 Verificar sistema:")
    print("      python check_installation.py")
    
    print("\n📖 DOCUMENTACIÓN:")
    print("-" * 20)
    print("   📄 README.md - Guía completa")
    print("   🎭 caras_conocidas/ - Agregar personajes")
    print("   ⚙️ .env - Configuración de APIs")
    
    print("\n🎯 PRÓXIMOS PASOS:")
    print("-" * 18)
    print("   1. Configura tus claves de API reales en .env")
    print("   2. Añade fotos de personajes en caras_conocidas/")
    print("   3. Copia videos a tu directorio configurado")
    print("   4. Ejecuta: python main.py")
    print("   5. Abre la interfaz web: python app.py")
    
    print("\n💡 CONSEJOS:")
    print("-" * 12)
    print("   • YouTube API: 10,000 consultas gratis por día")
    print("   • Spotify API: Completamente gratis")
    print("   • Google Vision: $1.50 por 1,000 detecciones")
    print("   • DeepFace local: 100% gratis (usa tu GPU)")
    
    print("\n🎬 ¡Disfruta usando Tag-Flow V2! 🎬")

def main():
    """Función principal del inicio rápido"""
    print_header()
    
    # Lista de pasos
    steps = [
        ("Verificar Python", check_python),
        ("Entorno virtual (opcional)", setup_virtual_environment),
        ("Instalar dependencias", install_dependencies),
        ("Configuración inicial", setup_configuration),
        ("Crear datos de ejemplo", create_example_data),
        ("Verificar instalación", verify_installation),
        ("Configurar directorio de videos", setup_video_directory),
        ("Primera ejecución", first_run),
    ]
    
    # Ejecutar pasos
    for i, (step_name, step_func) in enumerate(steps, 1):
        try:
            success = step_func()
            if not success and i <= 2:  # Pasos críticos
                print(f"\n❌ Error crítico en paso {i}. Revisar y reintentar.")
                return
            elif not success:
                print(f"\n⚠️  Advertencia en paso {i}. Continuando...")
        except KeyboardInterrupt:
            print(f"\n\n🛑 Configuración interrumpida en paso {i}")
            print("   Puedes continuar ejecutando este script nuevamente")
            return
        except Exception as e:
            print(f"\n❌ Error inesperado en paso {i}: {e}")
            continue
    
    # Instrucciones finales
    print_final_instructions()

if __name__ == "__main__":
    main()