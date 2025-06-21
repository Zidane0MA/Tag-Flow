#!/usr/bin/env python3
"""
Script de prueba para verificar las nuevas funcionalidades de Tag-Flow V2
"""

import sys
import os
from pathlib import Path

# Agregar el directorio principal al path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    # Probar importaciones
    print("Probando importaciones...")
    from config import config
    print("[OK] Config importado correctamente")
    
    from src.database import db
    print("[OK] Database importado correctamente")
    
    from src.external_sources import external_sources
    print("[OK] External sources importado correctamente")
    
    # Probar configuración
    print("\nProbando configuracion...")
    print(f"Base de datos: {config.DATABASE_PATH}")
    print(f"Carpetas organizadas: {config.ORGANIZED_BASE_PATH}")
    print(f"YouTube DB: {config.EXTERNAL_YOUTUBE_DB}")
    print(f"TikTok DB: {config.EXTERNAL_TIKTOK_DB}")
    print(f"Instagram DB: {config.EXTERNAL_INSTAGRAM_DB}")
    
    # Verificar existencia de archivos
    print("\nVerificando existencia de fuentes...")
    sources = [
        ("YouTube DB", config.EXTERNAL_YOUTUBE_DB),
        ("TikTok DB", config.EXTERNAL_TIKTOK_DB), 
        ("Instagram DB", config.EXTERNAL_INSTAGRAM_DB),
        ("Carpetas organizadas", config.ORGANIZED_BASE_PATH)
    ]
    
    for name, path in sources:
        exists = "[OK]" if path.exists() else "[FAIL]"
        print(f"{exists} {name}: {path}")
    
    # Probar estadísticas de fuentes externas
    print("\nProbando estadisticas de fuentes externas...")
    try:
        stats = external_sources.get_platform_stats()
        print("[OK] Estadisticas obtenidas correctamente:")
        for platform, counts in stats.items():
            print(f"  {platform}: BD={counts['db']}, Organizadas={counts['organized']}")
    except Exception as e:
        print(f"[FAIL] Error obteniendo estadisticas: {e}")
    
    print("\n[SUCCESS] Pruebas completadas!")
    
except Exception as e:
    print(f"[ERROR] Error durante las pruebas: {e}")
    import traceback
    traceback.print_exc()
