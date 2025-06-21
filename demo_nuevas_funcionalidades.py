#!/usr/bin/env python3
"""
Tag-Flow V2 - Script de Demostración de Nuevas Funcionalidades
Muestra el uso de las nuevas características implementadas
"""

import sys
import os
from pathlib import Path

# Agregar el directorio principal al path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / 'src'))

def demo_external_sources():
    """Demostrar estadísticas de fuentes externas"""
    print("\n" + "="*60)
    print("DEMO: ESTADISTICAS DE FUENTES EXTERNAS")
    print("="*60)
    
    try:
        from src.external_sources import external_sources
        
        # Obtener estadísticas
        stats = external_sources.get_platform_stats()
        
        print("Videos disponibles en fuentes externas:")
        print()
        
        total_db = 0
        total_organized = 0
        
        for platform, counts in stats.items():
            db_count = counts['db']
            org_count = counts['organized']
            total_db += db_count
            total_organized += org_count
            
            print(f"{platform.upper()}:")
            print(f"   [BD Externa]: {db_count} videos")
            print(f"   [Carpetas]: {org_count} videos")
            print(f"   [Total]: {db_count + org_count} videos")
            print()
        
        print(f"TOTALES GENERALES:")
        print(f"   [BD Externas]: {total_db} videos")
        print(f"   [Carpetas]: {total_organized} videos")
        print(f"   [Gran Total]: {total_db + total_organized} videos")
        
    except Exception as e:
        print(f"[ERROR] No se pudieron obtener estadisticas: {e}")

def demo_maintenance_commands():
    """Mostrar comandos de mantenimiento disponibles"""
    print("\n" + "="*60)
    print("DEMO: COMANDOS DE MANTENIMIENTO DISPONIBLES")
    print("="*60)
    
    commands = [
        ("Poblar BD desde todas las fuentes", "python maintenance.py populate-db --source all"),
        ("Poblar BD solo desde YouTube", "python maintenance.py populate-db --platform youtube --limit 10"),
        ("Generar thumbnails faltantes", "python maintenance.py populate-thumbnails"),
        ("Ver estadisticas de fuentes", "python maintenance.py show-stats"),
        ("Limpiar BD de TikTok", "python maintenance.py clear-db --platform tiktok"),
        ("Backup completo", "python maintenance.py backup"),
        ("Optimizar base de datos", "python maintenance.py optimize-db")
    ]
    
    for description, command in commands:
        print(f"[{description}]:")
        print(f"   {command}")
        print()

def demo_processing_commands():
    """Mostrar comandos de procesamiento específico"""
    print("\n" + "="*60)
    print("DEMO: PROCESAMIENTO ESPECIFICO POR PLATAFORMA")
    print("="*60)
    
    commands = [
        ("Analizar 5 videos de YouTube", "python main.py 5 YT"),
        ("Analizar 3 videos de TikTok", "python main.py 3 TT"),
        ("Analizar 2 videos de Instagram", "python main.py 2 IG"),
        ("Analizar 10 videos de carpetas organizadas", "python main.py 10 O"),
        ("Procesamiento tradicional (20 videos)", "python main.py 20"),
        ("Procesamiento completo sin limite", "python main.py")
    ]
    
    print("Codigos de plataforma:")
    print("   YT = YouTube (4K Video Downloader+)")
    print("   TT = TikTok (4K Tokkit)")
    print("   IG = Instagram (4K Stogram)")
    print("   O  = Otros (carpetas D:\\4K All)")
    print()
    
    for description, command in commands:
        print(f"[{description}]:")
        print(f"   {command}")
        print()

def demo_workflow_examples():
    """Mostrar ejemplos de flujos de trabajo completos"""
    print("\n" + "="*60)
    print("DEMO: FLUJOS DE TRABAJO RECOMENDADOS")
    print("="*60)
    
    workflows = [
        {
            "name": "Analisis Rapido de YouTube",
            "steps": [
                "python maintenance.py populate-db --source db --platform youtube --limit 20",
                "python maintenance.py populate-thumbnails --platform youtube --limit 20",
                "python main.py 10 YT",
                "python app.py  # Ver resultados en interfaz web"
            ]
        },
        {
            "name": "Importacion Completa de Instagram",
            "steps": [
                "python maintenance.py populate-db --source all --platform instagram",
                "python maintenance.py populate-thumbnails --platform instagram",
                "python main.py 5 IG",
                "python app.py  # Gestionar en interfaz web"
            ]
        },
        {
            "name": "Limpieza y Repoblado Completo",
            "steps": [
                "python maintenance.py backup",
                "python maintenance.py clear-db --force",
                "python maintenance.py clear-thumbnails --force",
                "python maintenance.py populate-db --source all --limit 100",
                "python maintenance.py populate-thumbnails --limit 100",
                "python main.py 20"
            ]
        }
    ]
    
    for workflow in workflows:
        print(f"\n[{workflow['name']}]:")
        for i, step in enumerate(workflow['steps'], 1):
            print(f"   {i}. {step}")
        print()

def main():
    """Función principal de demostración"""
    print("TAG-FLOW V2 - DEMOSTRACION DE NUEVAS FUNCIONALIDADES")
    print("=" * 60)
    print("Este script muestra las nuevas caracteristicas implementadas.")
    print("Todas las funcionalidades han sido probadas y estan listas para usar.")
    
    # Ejecutar demostraciones
    demo_external_sources()
    demo_maintenance_commands()
    demo_processing_commands()
    demo_workflow_examples()
    
    print("\n" + "="*60)
    print("DEMOSTRACION COMPLETADA")
    print("="*60)
    print("Para usar las nuevas funcionalidades:")
    print("1. Revisa NUEVAS_FUNCIONALIDADES.md para documentacion detallada")
    print("2. Usa 'python maintenance.py show-stats' para ver estadisticas")
    print("3. Empieza con 'python maintenance.py populate-db --source all --limit 10'")
    print("4. Luego 'python main.py 5 YT' para probar procesamiento especifico")
    print()
    print("El sistema esta listo para usar!")

if __name__ == "__main__":
    main()
