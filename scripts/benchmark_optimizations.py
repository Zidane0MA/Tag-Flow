"""
Tag-Flow V2 - Benchmark de Optimizaciones
Script para medir y comparar el rendimiento de las optimizaciones de BD
"""

import time
import sys
from pathlib import Path
import sqlite3
from typing import List, Dict, Set

# Agregar src al path
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config
from src.service_factory import get_database
from src.pattern_cache import get_global_cache, clear_global_cache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceBenchmark:
    """Benchmark para medir mejoras de rendimiento de las optimizaciones"""
    
    def __init__(self):
        # Ahora todas las optimizaciones están en el sistema principal
        self.db = get_database()  # Ya incluye todas las optimizaciones migradas
        self.cache = get_global_cache()
        
    def benchmark_get_existing_paths(self, iterations=100):
        """Benchmark: Obtener paths existentes (verificación de duplicados)"""
        print("\nBENCHMARK: Verificacion de Duplicados")
        print("="*50)
        
        # Método Legacy (cargar todos los videos)
        print("Ejecutando método LEGACY...")
        start_time = time.time()
        
        for i in range(iterations):
            videos_in_db = self.regular_db.get_videos()
            existing_paths = {video['file_path'] for video in videos_in_db}
        
        legacy_time = time.time() - start_time
        
        # Limpiar cache para test justo
        clear_global_cache()
        
        # Método Optimizado (solo paths)
        print("Ejecutando método OPTIMIZADO...")
        start_time = time.time()
        
        for i in range(iterations):
            existing_paths = self.optimized_db.get_existing_paths_only()
        
        optimized_time = time.time() - start_time
        
        # Calcular mejora
        speedup = legacy_time / optimized_time if optimized_time > 0 else float('inf')
        
        print(f"RESULTADOS:")
        print(f"  Legacy:     {legacy_time:.3f}s ({iterations} iteraciones)")
        print(f"  Optimizado: {optimized_time:.3f}s ({iterations} iteraciones)")
        print(f"  Speedup:    {speedup:.1f}x más rápido")
        print(f"  Paths encontrados: {len(existing_paths)}")
        
        return {
            'legacy_time': legacy_time,
            'optimized_time': optimized_time,
            'speedup': speedup,
            'paths_count': len(existing_paths)
        }
    
    def benchmark_get_pending_videos(self, iterations=10):
        """Benchmark: Búsqueda de videos pendientes"""
        print("\nBENCHMARK: Busqueda de Videos Pendientes")
        print("="*50)
        
        # Método Legacy
        print("Ejecutando método LEGACY...")
        start_time = time.time()
        
        for i in range(iterations):
            filters = {'processing_status': 'pendiente'}
            pending_videos = self.regular_db.get_videos(filters, limit=50)
        
        legacy_time = time.time() - start_time
        
        # Limpiar cache
        clear_global_cache()
        
        # Método Optimizado
        print("Ejecutando método OPTIMIZADO...")
        start_time = time.time()
        
        for i in range(iterations):
            pending_videos = self.optimized_db.get_pending_videos_filtered(
                platform_filter=None, 
                source_filter='all', 
                limit=50
            )
        
        optimized_time = time.time() - start_time
        
        speedup = legacy_time / optimized_time if optimized_time > 0 else float('inf')
        
        print(f"RESULTADOS:")
        print(f"  Legacy:     {legacy_time:.3f}s ({iterations} iteraciones)")
        print(f"  Optimizado: {optimized_time:.3f}s ({iterations} iteraciones)")
        print(f"  Speedup:    {speedup:.1f}x más rápido")
        print(f"  Videos encontrados: {len(pending_videos)}")
        
        return {
            'legacy_time': legacy_time,
            'optimized_time': optimized_time,
            'speedup': speedup,
            'videos_count': len(pending_videos)
        }
    
    def benchmark_cache_efficiency(self, iterations=100):
        """Benchmark: Eficiencia del cache LRU"""
        print("\nBENCHMARK: Eficiencia del Cache LRU")
        print("="*50)
        
        # Limpiar cache inicial
        clear_global_cache()
        
        # Primera ronda - poblar cache
        print("Poblando cache...")
        for i in range(10):
            self.cache.get_existing_paths(self.optimized_db)
        
        # Segunda ronda - medir cache hits
        print("Midiendo cache hits...")
        start_time = time.time()
        
        for i in range(iterations):
            self.cache.get_existing_paths(self.optimized_db)
        
        cached_time = time.time() - start_time
        
        # Estadísticas del cache
        cache_stats = self.cache.get_cache_stats()
        
        print(f"RESULTADOS DEL CACHE:")
        print(f"  Tiempo con cache: {cached_time:.3f}s ({iterations} iteraciones)")
        print(f"  Cache hits: {cache_stats['cache_hits']}")
        print(f"  Cache misses: {cache_stats['cache_misses']}")
        print(f"  Hit rate: {cache_stats['hit_rate_percentage']:.1f}%")
        print(f"  Eficiencia: {cache_stats['cache_efficiency']}")
        
        return cache_stats
    
    def benchmark_batch_operations(self, batch_size=50):
        """Benchmark: Operaciones por lotes vs individuales"""
        print("\nBENCHMARK: Operaciones por Lotes")
        print("="*50)
        
        # Obtener sample de paths para testing
        sample_videos = self.regular_db.get_videos(limit=batch_size)
        file_paths = [video['file_path'] for video in sample_videos]
        
        # Método Individual (simulando búsquedas una por una)
        print("Ejecutando busquedas INDIVIDUALES...")
        start_time = time.time()
        
        results_individual = []
        for path in file_paths:
            result = self.regular_db.get_video_by_path(path)
            results_individual.append(result is not None)
        
        individual_time = time.time() - start_time
        
        # Método Batch
        print("Ejecutando busqueda por LOTES...")
        start_time = time.time()
        
        results_batch = self.optimized_db.check_videos_exist_batch(file_paths)
        
        batch_time = time.time() - start_time
        
        speedup = individual_time / batch_time if batch_time > 0 else float('inf')
        
        print(f"RESULTADOS:")
        print(f"  Individual: {individual_time:.3f}s ({len(file_paths)} consultas)")
        print(f"  Batch:      {batch_time:.3f}s (1 consulta)")
        print(f"  Speedup:    {speedup:.1f}x más rápido")
        print(f"  Videos verificados: {len(file_paths)}")
        
        return {
            'individual_time': individual_time,
            'batch_time': batch_time,
            'speedup': speedup,
            'batch_size': len(file_paths)
        }
    
    def run_complete_benchmark(self):
        """Ejecutar benchmark completo"""
        print("\n" + "="*60)
        print("TAG-FLOW V2 - BENCHMARK DE OPTIMIZACIONES")
        print("="*60)
        
        # Información del sistema
        videos_total = len(self.regular_db.get_videos())
        print(f"Base de datos: {videos_total} videos")
        print(f"Optimizaciones: {'ACTIVAS' if config.USE_OPTIMIZED_DATABASE else 'INACTIVAS'}")
        print(f"Cache TTL: {config.DATABASE_CACHE_TTL}s")
        print(f"Cache size: {config.DATABASE_CACHE_SIZE}")
        
        results = {}
        
        # Ejecutar benchmarks individuales
        results['duplicates'] = self.benchmark_get_existing_paths(iterations=10)
        results['pending'] = self.benchmark_get_pending_videos(iterations=5)
        results['cache'] = self.benchmark_cache_efficiency(iterations=50)
        results['batch'] = self.benchmark_batch_operations(batch_size=30)
        
        # Resumen final
        print("\n" + "="*60)
        print("RESUMEN DE MEJORAS DE RENDIMIENTO")
        print("="*60)
        
        total_speedup = (
            results['duplicates']['speedup'] +
            results['pending']['speedup'] +
            results['batch']['speedup']
        ) / 3
        
        print(f"Verificacion duplicados: {results['duplicates']['speedup']:.1f}x más rápido")
        print(f"Busqueda pendientes:     {results['pending']['speedup']:.1f}x más rápido")
        print(f"Operaciones por lotes:   {results['batch']['speedup']:.1f}x más rápido")
        print(f"Cache hit rate:          {results['cache']['hit_rate_percentage']:.1f}%")
        print(f"SPEEDUP PROMEDIO:        {total_speedup:.1f}x MAS RAPIDO")
        
        # Estimación de tiempo ahorrado
        print(f"\nESTIMACION DE TIEMPO AHORRADO (para 1000 videos):")
        legacy_time_1000 = results['duplicates']['legacy_time'] * 100  # Extrapolación
        optimized_time_1000 = results['duplicates']['optimized_time'] * 100
        time_saved = legacy_time_1000 - optimized_time_1000
        
        print(f"  Tiempo legacy:     {legacy_time_1000:.1f}s")
        print(f"  Tiempo optimizado: {optimized_time_1000:.1f}s")
        print(f"  TIEMPO AHORRADO:   {time_saved:.1f}s ({time_saved/60:.1f} minutos)")
        
        print("\nCONCLUSION:")
        if total_speedup >= 10:
            print("OPTIMIZACIONES EXCEPCIONALES - Mejoras transformacionales!")
        elif total_speedup >= 5:
            print("OPTIMIZACIONES EXCELENTES - Mejoras significativas!")
        elif total_speedup >= 2:
            print("OPTIMIZACIONES BUENAS - Mejoras notables!")
        else:
            print("OPTIMIZACIONES MODESTAS - Revisar configuracion")
        
        print("="*60)
        
        return results

def main():
    """Ejecutar benchmark completo"""
    try:
        benchmark = PerformanceBenchmark()
        results = benchmark.run_complete_benchmark()
        
        print("\nBenchmark completado exitosamente!")
        print("Para mejores resultados, ejecuta main.py varias veces para poblar cache")
        
    except Exception as e:
        print(f"\nError en benchmark: {e}")
        logger.error(f"Error en benchmark: {e}")

if __name__ == "__main__":
    main()
