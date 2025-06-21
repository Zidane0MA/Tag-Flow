#!/usr/bin/env python3
"""
Tag-Flow V2 - Verificador de Configuración Actualizada
Verifica que todas las nuevas configuraciones en .env están correctas
"""

import sys
import os
from pathlib import Path

# Agregar el directorio principal al path
sys.path.append(str(Path(__file__).parent))

def verify_config():
    """Verificar todas las configuraciones del archivo .env actualizado"""
    print("TAG-FLOW V2 - VERIFICADOR DE CONFIGURACION ACTUALIZADA")
    print("=" * 60)
    
    try:
        from config import config
        print("[OK] Configuracion cargada exitosamente")
    except Exception as e:
        print(f"[ERROR] No se pudo cargar la configuracion: {e}")
        return False
    
    print("\nVerificando configuraciones...")
    
    # Verificar APIs básicas
    apis_ok = True
    if config.YOUTUBE_API_KEY:
        print("[OK] YouTube API Key configurada")
    else:
        print("[WARN] YouTube API Key no configurada")
        apis_ok = False
    
    if config.SPOTIFY_CLIENT_ID and config.SPOTIFY_CLIENT_SECRET:
        print("[OK] Spotify API configurada")
    else:
        print("[WARN] Spotify API no configurada")
        apis_ok = False
    
    # Verificar nuevas rutas de fuentes externas
    print("\nVerificando fuentes externas...")
    
    sources_ok = True
    
    # Carpetas organizadas
    if config.ORGANIZED_BASE_PATH.exists():
        print(f"[OK] Carpetas organizadas: {config.ORGANIZED_BASE_PATH}")
        
        # Verificar subcarpetas
        subcarpetas = ['Youtube', 'Tiktok', 'Instagram']
        for subcarpeta in subcarpetas:
            ruta = config.ORGANIZED_BASE_PATH / subcarpeta
            status = "[OK]" if ruta.exists() else "[CREAR]"
            print(f"  {status} {subcarpeta}: {ruta}")
    else:
        print(f"[WARN] Carpetas organizadas no existen: {config.ORGANIZED_BASE_PATH}")
        print("       Creala con: mkdir 'D:\\4K All\\Youtube' 'D:\\4K All\\Tiktok' 'D:\\4K All\\Instagram'")
        sources_ok = False
    
    # Bases de datos externas
    external_dbs = [
        ("YouTube DB", config.EXTERNAL_YOUTUBE_DB),
        ("TikTok DB", config.EXTERNAL_TIKTOK_DB),
        ("Instagram DB", config.EXTERNAL_INSTAGRAM_DB)
    ]
    
    for name, path in external_dbs:
        if path.exists():
            size_mb = path.stat().st_size / 1024 / 1024
            print(f"[OK] {name}: {path} ({size_mb:.1f} MB)")
        else:
            print(f"[WARN] {name} no encontrada: {path}")
    
    # Verificar directorios internos
    print("\nVerificando directorios internos...")
    
    internal_dirs = [
        ("Base de datos", config.DATABASE_PATH.parent),
        ("Thumbnails", config.THUMBNAILS_PATH),
        ("Videos procesados", config.PROCESSED_VIDEOS_PATH),
        ("Caras conocidas", config.KNOWN_FACES_PATH)
    ]
    
    for name, path in internal_dirs:
        if path.exists():
            print(f"[OK] {name}: {path}")
        else:
            print(f"[CREAR] {name}: {path}")
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREADO] {name}")
            except Exception as e:
                print(f"  [ERROR] No se pudo crear {name}: {e}")
    
    # Probar conexión a fuentes externas
    print("\nProbando conexiones a fuentes externas...")
    
    try:
        from src.external_sources import external_sources
        stats = external_sources.get_platform_stats()
        
        total_disponibles = sum(counts['db'] + counts['organized'] for counts in stats.values())
        print(f"[OK] Conexiones exitosas - {total_disponibles} videos disponibles")
        
        for platform, counts in stats.items():
            total = counts['db'] + counts['organized']
            if total > 0:
                print(f"  [OK] {platform.upper()}: {total} videos")
        
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a fuentes externas: {e}")
        sources_ok = False
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN DE VERIFICACION")
    print("=" * 60)
    
    if apis_ok:
        print("[OK] APIs configuradas correctamente")
    else:
        print("[WARN] Algunas APIs necesitan configuracion")
    
    if sources_ok:
        print("[OK] Fuentes externas disponibles")
    else:
        print("[WARN] Algunas fuentes externas no disponibles")
    
    print("\nComandos disponibles para probar:")
    print("  python maintenance.py show-stats")
    print("  python maintenance.py populate-db --source db --platform youtube --limit 5")
    print("  python maintenance.py populate-thumbnails --limit 5")
    print("  python main.py 3 YT")
    
    print("\nEl sistema esta listo para usar con las nuevas funcionalidades!")
    return True

if __name__ == "__main__":
    verify_config()
