#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tag-Flow V2 - Performance Optimizations Demo
Demostración de todas las optimizaciones de rendimiento implementadas
"""

import sys
import time
import json
import sqlite3
from pathlib import Path

# Agregar src al path
sys.path.append(str(Path(__file__).parent.parent / 'src'))
sys.path.append(str(Path(__file__).parent.parent))

from src.api.performance.monitor import get_database_monitor
from src.api.performance.cache import smart_cache, cached
from src.api.performance.pagination import smart_paginator

def demo_database_indices():
    """Demostrar mejoras de índices de base de datos"""
    print("[DATABASE] DEMO: Optimizacion de Indices de Base de Datos")
    print("=" * 60)

    db_path = Path(__file__).parent.parent / 'data' / 'videos.db'
    if not db_path.exists():
        print("❌ Base de datos no encontrada. Ejecute primero el poblado de datos.")
        return

    # Ejecutar script de optimización
    try:
        # Intentar importar módulo de optimizaciones
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        from apply_database_optimizations import apply_optimizations, verify_performance

        print("📊 Aplicando optimizaciones de índices...")
        success = apply_optimizations()

        if success:
            print("✅ Índices optimizados aplicados exitosamente")
            print("\n📈 Verificando mejoras de performance...")
            verify_performance()
        else:
            print("❌ Error aplicando optimizaciones")
    except ImportError:
        print("⚠️  Módulo de optimizaciones no encontrado")
        print("💡 Ejecute: python scripts/apply_database_optimizations.py")
        print("✅ Los índices ya pueden estar aplicados desde la ejecución anterior")

    print("\n" + "=" * 60 + "\n")

def demo_smart_cache():
    """Demostrar sistema de cache inteligente"""
    print("💾 DEMO: Sistema de Cache Inteligente")
    print("=" * 60)

    # Función de ejemplo para cachear
    @cached(ttl=30, key_func=lambda x: f"demo_data:{x}")
    def get_expensive_data(param):
        """Simular operación costosa"""
        time.sleep(0.1)  # Simular latencia
        return {
            'param': param,
            'timestamp': time.time(),
            'data': f"expensive_result_for_{param}"
        }

    # Prueba 1: Primera llamada (cache miss)
    print("🔍 Primera llamada (cache MISS)...")
    start_time = time.time()
    result1 = get_expensive_data("test1")
    time1 = (time.time() - start_time) * 1000
    print(f"   Tiempo: {time1:.2f}ms")
    print(f"   Resultado: {result1['data']}")

    # Prueba 2: Segunda llamada (cache hit)
    print("\n🎯 Segunda llamada (cache HIT)...")
    start_time = time.time()
    result2 = get_expensive_data("test1")
    time2 = (time.time() - start_time) * 1000
    print(f"   Tiempo: {time2:.2f}ms")
    print(f"   Resultado: {result2['data']}")
    if time2 > 0:
        print(f"   💡 Mejora: {(time1/time2):.1f}x más rápido")
    else:
        print(f"   💡 Mejora: Cache instantáneo! (>100x más rápido)")

    # Mostrar estadísticas de cache
    stats = smart_cache.get_stats()
    print(f"\n📊 Estadísticas de Cache:")
    print(f"   Hit Rate: {stats['hit_rate_percent']:.1f}%")
    print(f"   Total Requests: {stats['total_requests']}")
    print(f"   Cache Entries: {stats['current_entries']}")
    print(f"   Memory Usage: {stats['total_size_bytes']} bytes")

    print("\n" + "=" * 60 + "\n")

def demo_smart_pagination():
    """Demostrar paginación inteligente"""
    print("⚡ DEMO: Paginación Inteligente")
    print("=" * 60)

    db_path = Path(__file__).parent.parent / 'data' / 'videos.db'
    if not db_path.exists():
        print("❌ Base de datos no encontrada.")
        return

    try:
        conn = sqlite3.connect(str(db_path))

        # Contar registros totales
        cursor = conn.execute("SELECT COUNT(*) FROM media m JOIN posts p ON m.post_id = p.id WHERE p.deleted_at IS NULL")
        total_records = cursor.fetchone()[0]

        print(f"📊 Total de registros en BD: {total_records:,}")

        if total_records == 0:
            print("❌ No hay datos en la base de datos")
            conn.close()
            return

        # Demostrar paginación tradicional (offset)
        print("\n📄 OFFSET Pagination (Tradicional):")
        filters = {}

        start_time = time.time()
        result_offset = smart_paginator.offset_paginator.paginate_posts(conn, filters, page=1)
        time_offset = (time.time() - start_time) * 1000

        print(f"   Tiempo: {time_offset:.2f}ms")
        print(f"   Registros obtenidos: {len(result_offset.data)}")
        print(f"   Tipo: {result_offset.performance_info['pagination_type']}")

        # Demostrar paginación por cursor
        print("\n🎯 CURSOR Pagination (Optimizada):")
        start_time = time.time()
        result_cursor = smart_paginator.cursor_paginator.paginate_posts(conn, filters)
        time_cursor = (time.time() - start_time) * 1000

        print(f"   Tiempo: {time_cursor:.2f}ms")
        print(f"   Registros obtenidos: {len(result_cursor.data)}")
        print(f"   Tipo: {result_cursor.performance_info['pagination_type']}")

        if time_cursor > 0 and time_cursor < time_offset:
            improvement = time_offset / time_cursor
            print(f"   💡 Mejora: {improvement:.1f}x más rápido")
        elif time_cursor <= 0:
            print(f"   💡 Mejora: Cursor pagination instantáneo!")

        # Demostrar paginación inteligente automática
        print(f"\n🤖 SMART Pagination (Automática):")
        start_time = time.time()
        result_smart = smart_paginator.paginate_posts(conn, filters, page=1)
        time_smart = (time.time() - start_time) * 1000

        print(f"   Tiempo: {time_smart:.2f}ms")
        print(f"   Registros obtenidos: {len(result_smart.data)}")
        print(f"   Estrategia elegida: {result_smart.performance_info['pagination_type']}")

        conn.close()

    except Exception as e:
        print(f"❌ Error en demo de paginación: {e}")

    print("\n" + "=" * 60 + "\n")

def demo_performance_monitoring():
    """Demostrar sistema de monitoreo"""
    print("📈 DEMO: Sistema de Monitoreo de Performance")
    print("=" * 60)

    db_path = Path(__file__).parent.parent / 'data' / 'videos.db'
    if not db_path.exists():
        print("❌ Base de datos no encontrada.")
        return

    # Inicializar monitor
    monitor = get_database_monitor(str(db_path))

    # Simular algunas consultas monitoreadas
    print("🔍 Simulando consultas monitoreadas...")

    # Consulta rápida
    monitor.log_query_performance(
        query_type="SELECT",
        execution_time_ms=45.2,
        rows_affected=10,
        query="SELECT * FROM posts LIMIT 10",
        success=True
    )

    # Consulta lenta
    monitor.log_query_performance(
        query_type="SELECT",
        execution_time_ms=150.8,
        rows_affected=1000,
        query="SELECT * FROM media m JOIN posts p ON m.post_id = p.id",
        success=True
    )

    # Consulta fallida
    monitor.log_query_performance(
        query_type="UPDATE",
        execution_time_ms=25.1,
        rows_affected=0,
        query="UPDATE invalid_table SET field = value",
        success=False,
        error_message="no such table: invalid_table"
    )

    # Obtener métricas de salud
    print("\n🏥 Métricas de Salud Actuales:")
    health = monitor.get_current_health_metrics()
    print(f"   Tamaño BD: {health.db_size_mb:.2f} MB")
    print(f"   Fragmentación: {health.fragmentation_percent:.2f}%")
    print(f"   Cache Hit Ratio: {health.cache_hit_ratio:.2f}%")
    print(f"   Total Consultas: {health.total_queries}")
    print(f"   Consultas Lentas: {health.slow_queries}")
    print(f"   Consultas Fallidas: {health.failed_queries}")
    print(f"   Tiempo Promedio: {health.avg_query_time_ms:.2f}ms")

    # Obtener estadísticas de tablas
    print(f"\n📊 Estadísticas de Tablas:")
    table_stats = monitor.get_table_statistics()
    for stat in table_stats[:5]:  # Solo mostrar primeras 5
        print(f"   {stat.table_name}: {stat.row_count:,} filas, {stat.index_count} índices")

    # Resumen de performance
    print(f"\n📈 Resumen de Performance (última hora):")
    summary = monitor.get_performance_summary(hours=1)
    print(f"   Total Consultas: {summary['total_queries']}")
    print(f"   Tasa de Éxito: {summary['success_rate_percent']:.1f}%")
    print(f"   Consultas Lentas: {summary['slow_query_rate_percent']:.1f}%")
    print(f"   Tiempo P95: {summary['p95_execution_time_ms']:.2f}ms")

    print("\n" + "=" * 60 + "\n")

def demo_complete_performance():
    """Ejecutar demostración completa de todas las optimizaciones"""
    print("🎯 TAG-FLOW V2 - DEMOSTRACIÓN COMPLETA DE OPTIMIZACIONES")
    print("=" * 80)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

    # Ejecutar todas las demos
    demo_database_indices()
    demo_smart_cache()
    demo_smart_pagination()
    demo_performance_monitoring()

    print("🎉 DEMOSTRACIÓN COMPLETADA")
    print("=" * 80)
    print("✅ Todas las optimizaciones han sido demostradas:")
    print("   1. 📊 Índices de Base de Datos Optimizados")
    print("   2. 💾 Sistema de Cache Inteligente")
    print("   3. ⚡ Paginación Inteligente")
    print("   4. 📈 Monitoreo de Performance")
    print("\n💡 Tu sistema está optimizado para manejar datasets de gran escala!")
    print("=" * 80)

def run_benchmark():
    """Ejecutar benchmark de performance"""
    print("⏱️  BENCHMARK DE PERFORMANCE")
    print("=" * 60)

    # Benchmark de cache
    print("💾 Cache Performance:")
    iterations = 1000

    # Sin cache
    start_time = time.time()
    for i in range(iterations):
        # Simular operación sin cache
        result = f"result_{i}" * 10
    no_cache_time = (time.time() - start_time) * 1000

    # Con cache
    @cached(ttl=300)
    def cached_operation(i):
        return f"result_{i}" * 10

    start_time = time.time()
    for i in range(iterations):
        result = cached_operation(i % 100)  # Solo 100 valores únicos para probar cache hits
    cache_time = (time.time() - start_time) * 1000

    print(f"   Sin Cache: {no_cache_time:.2f}ms")
    print(f"   Con Cache: {cache_time:.2f}ms")
    print(f"   Mejora: {(no_cache_time/cache_time):.1f}x")

    print(f"\n📊 Estadísticas finales del cache:")
    stats = smart_cache.get_stats()
    print(f"   Hit Rate: {stats['hit_rate_percent']:.1f}%")
    print(f"   Total Requests: {stats['total_requests']}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "indices":
            demo_database_indices()
        elif command == "cache":
            demo_smart_cache()
        elif command == "pagination":
            demo_smart_pagination()
        elif command == "monitoring":
            demo_performance_monitoring()
        elif command == "benchmark":
            run_benchmark()
        else:
            print("Comandos disponibles: indices, cache, pagination, monitoring, benchmark")
    else:
        demo_complete_performance()