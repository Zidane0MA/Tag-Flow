"""
Tag-Flow V2 - Verificador de Configuración Enterprise
Sistema completo de diagnóstico para validar la configuración optimizada
"""

import os
import sys
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import importlib.util

# Configurar logging para el verificador
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class ConfigVerifier:
    """Verificador enterprise de configuración de Tag-Flow V2"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.issues = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
        
    def verify_all(self) -> bool:
        """Ejecutar verificación completa enterprise"""
        
        print("TAG-FLOW V2 - VERIFICACION ENTERPRISE DE CONFIGURACION")
        print("=" * 70)
        
        # Verificaciones básicas del sistema
        self._verify_python_environment()
        self._verify_project_structure()
        self._verify_dependencies()
        
        # Verificaciones de configuración
        self._verify_env_file()
        self._verify_api_configuration()
        
        # Verificaciones de fuentes externas
        self._verify_external_sources()
        
        # Verificaciones del sistema optimizado
        self._verify_character_intelligence_system()
        self._verify_optimized_detector()
        self._verify_cache_system()
        
        # Verificaciones de base de datos
        self._verify_database_structure()
        self._verify_character_database()
        
        # Verificaciones de directorios
        self._verify_directories()
        
        # Reporte final
        return self._generate_final_report()
    
    def _verify_python_environment(self):
        """Verificar entorno de Python"""
        self._section_header("Entorno de Python")
        
        # Verificar versión de Python
        python_version = sys.version_info
        if python_version >= (3, 12):
            self._success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        elif python_version >= (3, 8):
            self._warning(f"Python {python_version.major}.{python_version.minor} (recomendado 3.12+)")
        else:
            self._error(f"Python {python_version.major}.{python_version.minor} demasiado antiguo (requiere 3.8+)")
        
        # Verificar entorno virtual
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self._success("Entorno virtual detectado")
        else:
            self._warning("No se detectó entorno virtual (recomendado)")
    
    def _verify_project_structure(self):
        """Verificar estructura del proyecto"""
        self._section_header("Estructura del Proyecto")
        
        required_files = [
            "main.py",
            "app.py", 
            "main.py",
            "config.py",
            "requirements.txt",
            ".env.example"
        ]
        
        required_dirs = [
            "src",
            "data", 
            "static",
            "templates",
            "caras_conocidas"
        ]
        
        # Verificar archivos principales
        for file in required_files:
            file_path = self.project_root / file
            if file_path.exists():
                self._success(f"Archivo: {file}")
            else:
                self._error(f"Archivo faltante: {file}")
        
        # Verificar directorios
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self._success(f"Directorio: {dir_name}/")
            else:
                self._error(f"Directorio faltante: {dir_name}/")
        
        # Verificar archivos críticos del sistema optimizado
        optimized_files = [
            "src/character_intelligence.py",
            "src/optimized_detector.py", 
            "src/pattern_cache.py"
        ]
        
        for file in optimized_files:
            file_path = self.project_root / file
            if file_path.exists():
                self._success(f"Sistema optimizado: {file}")
            else:
                self._error(f"Archivo optimizado faltante: {file}")
    
    def _verify_dependencies(self):
        """Verificar dependencias instaladas"""
        self._section_header("Dependencias de Python")
        
        critical_packages = [
            "flask",
            "requests", 
            "PIL",  # pillow se importa como PIL
            "cv2",  # opencv-python se importa como cv2
            "deepface",
            "tensorflow"
        ]
        
        optional_packages = [
            "google-cloud-vision",
            "spotipy"
        ]
        
        # Verificar dependencias críticas
        for package in critical_packages:
            try:
                __import__(package.replace('-', '_'))
                self._success(f"Paquete instalado: {package}")
            except ImportError:
                self._error(f"Paquete faltante: {package}")
        
        # Verificar dependencias opcionales
        for package in optional_packages:
            try:
                __import__(package.replace('-', '_').replace('google_cloud_vision', 'google.cloud.vision'))
                self._success(f"Paquete opcional: {package}")
            except ImportError:
                self._warning(f"Paquete opcional no instalado: {package}")
    
    def _verify_env_file(self):
        """Verificar archivo .env"""
        self._section_header("Configuración de Entorno")
        
        env_path = self.project_root / '.env'
        env_example_path = self.project_root / '.env.example'
        
        if not env_path.exists():
            if env_example_path.exists():
                self._warning("Archivo .env no encontrado, pero .env.example disponible")
                self._info("Ejecuta: copy .env.example .env")
            else:
                self._error("Archivos .env y .env.example no encontrados")
            return
        
        self._success("Archivo .env encontrado")
        
        # Verificar configuración básica
        try:
            from config import config
            self._success("Configuración cargada exitosamente")
            
            # Verificar directorios de configuración
            if hasattr(config, 'DATA_DIR') and Path(config.DATA_DIR).exists():
                self._success(f"Directorio de datos: {config.DATA_DIR}")
            else:
                self._warning("Directorio de datos no configurado o no existe")
                
        except Exception as e:
            self._error(f"Error cargando configuración: {e}")
    
    def _verify_api_configuration(self):
        """Verificar configuración de APIs"""
        self._section_header("Configuración de APIs")
        
        try:
            from config import config
            
            # YouTube API
            youtube_key = getattr(config, 'YOUTUBE_API_KEY', None)
            if youtube_key and len(youtube_key) > 10:
                self._success("YouTube API Key configurada")
            else:
                self._warning("YouTube API Key no configurada")
            
            # Spotify API
            spotify_id = getattr(config, 'SPOTIFY_CLIENT_ID', None)
            spotify_secret = getattr(config, 'SPOTIFY_CLIENT_SECRET', None)
            if spotify_id and spotify_secret:
                self._success("Spotify API configurada")
            else:
                self._warning("Spotify API no configurada")
            
            # Google Vision API
            google_creds = getattr(config, 'GOOGLE_APPLICATION_CREDENTIALS', None)
            if google_creds and Path(google_creds).exists():
                self._success("Google Vision API configurada")
            elif google_creds:
                self._warning("Google Vision API configurada pero archivo de credenciales no encontrado")
            else:
                self._warning("Google Vision API no configurada")
                
        except Exception as e:
            self._error(f"Error verificando APIs: {e}")
    
    def _verify_external_sources(self):
        """Verificar fuentes externas (4K Apps)"""
        self._section_header("Fuentes Externas (4K Apps)")
        
        try:
            from config import config
            
            sources = [
                ("YouTube (4K Video Downloader+)", getattr(config, 'EXTERNAL_YOUTUBE_DB', None)),
                ("TikTok (4K Tokkit)", getattr(config, 'EXTERNAL_TIKTOK_DB', None)),
                ("Instagram (4K Stogram)", getattr(config, 'EXTERNAL_INSTAGRAM_DB', None)),
                ("Carpetas Organizadas", getattr(config, 'ORGANIZED_BASE_PATH', None))
            ]
            
            available_sources = 0
            
            for source_name, source_path in sources:
                if source_path and Path(source_path).exists():
                    self._success(f"{source_name}: {source_path}")
                    available_sources += 1
                    
                    # Verificar que es una base de datos SQLite válida para DB sources
                    if str(source_path).endswith('.sqlite'):
                        try:
                            conn = sqlite3.connect(source_path)
                            cursor = conn.cursor()
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                            tables = cursor.fetchall()
                            conn.close()
                            
                            if tables:
                                self._info(f"  - {len(tables)} tablas encontradas")
                            else:
                                self._warning(f"  - Base de datos vacia")
                                
                        except Exception as e:
                            self._warning(f"  - Error accediendo a BD: {e}")
                elif source_path:
                    self._warning(f"{source_name}: Configurado pero no encontrado ({source_path})")
                else:
                    self._info(f"{source_name}: No configurado")
            
            if available_sources > 0:
                self._success(f"Total fuentes disponibles: {available_sources}/4")
            else:
                self._warning("No hay fuentes externas configuradas")
                
        except Exception as e:
            self._error(f"Error verificando fuentes externas: {e}")
    
    def _verify_character_intelligence_system(self):
        """Verificar sistema de inteligencia de personajes optimizado"""
        self._section_header("Sistema de Inteligencia de Personajes")
        
        try:
            # Importar y verificar CharacterIntelligence
            from src.character_intelligence import CharacterIntelligence
            
            ci = CharacterIntelligence()
            self._success("CharacterIntelligence inicializado correctamente")
            
            # Verificar estadísticas básicas
            stats = ci.get_stats()
            
            total_characters = stats.get('total_characters', 0)
            total_games = stats.get('total_games', 0)
            detector_type = stats.get('detector_type', 'unknown')
            
            if total_characters >= 200:
                self._success(f"Personajes cargados: {total_characters}")
            elif total_characters > 0:
                self._warning(f"Pocos personajes cargados: {total_characters}")
            else:
                self._error("No se cargaron personajes")
            
            if total_games >= 5:
                self._success(f"Juegos/Series: {total_games}")
            else:
                self._warning(f"Pocos juegos configurados: {total_games}")
            
            # Verificar tipo de detector
            if detector_type == 'optimized':
                self._success("Detector optimizado activo")
                
                # Verificar patrones optimizados
                optimized_patterns = stats.get('optimized_patterns', 0)
                if optimized_patterns >= 1000:
                    self._success(f"Patrones jerárquicos: {optimized_patterns}")
                elif optimized_patterns > 0:
                    self._warning(f"Patrones limitados: {optimized_patterns}")
                else:
                    self._error("No se cargaron patrones optimizados")
            else:
                self._warning(f"Usando detector: {detector_type}")
            
            # Test básico de detección
            test_result = ci.analyze_video_title("Hu Tao dance MMD")
            if test_result:
                self._success("Test de detección: OK")
                detection = test_result[0]
                confidence = detection.get('confidence', 0)
                self._info(f"  - Detectado: {detection.get('name')} (confidence: {confidence:.2f})")
            else:
                self._warning("Test de detección: Sin resultados")
                
        except ImportError as e:
            self._error(f"No se pudo importar CharacterIntelligence: {e}")
        except Exception as e:
            self._error(f"Error en sistema de personajes: {e}")
    
    def _verify_optimized_detector(self):
        """Verificar detector optimizado específicamente"""
        self._section_header("Detector Optimizado")
        
        try:
            from src.optimized_detector import OptimizedCharacterDetector
            self._success("OptimizedCharacterDetector disponible")
            
            # Verificar si se puede instanciar
            try:
                from src.character_intelligence import CharacterIntelligence
                ci = CharacterIntelligence()
                
                if ci.optimized_detector:
                    self._success("Detector optimizado inicializado")
                    
                    # Obtener estadísticas de rendimiento
                    perf_stats = ci.get_performance_report()
                    if perf_stats:
                        total_patterns = perf_stats.get('total_patterns', 0)
                        cache_hit_rate = perf_stats.get('cache_hit_rate', 0)
                        
                        self._success(f"Patrones totales: {total_patterns}")
                        
                        if cache_hit_rate > 0:
                            self._success(f"Cache hit rate: {cache_hit_rate}%")
                        else:
                            self._info("Cache vacio (normal en inicio)")
                    
                    # Test de rendimiento básico
                    import time
                    test_titles = ["Hu Tao dance", "Raiden Shogun", "Test title"] * 10
                    start_time = time.time()
                    results = [ci.optimized_detector.detect_in_title(title) for title in test_titles]
                    elapsed = time.time() - start_time
                    
                    avg_time_ms = (elapsed / len(test_titles)) * 1000
                    if avg_time_ms < 1.0:
                        self._success(f"Rendimiento: {avg_time_ms:.2f}ms promedio")
                    else:
                        self._warning(f"Rendimiento lento: {avg_time_ms:.2f}ms promedio")
                        
                else:
                    self._warning("Detector optimizado no se pudo inicializar")
                    
            except Exception as e:
                self._warning(f"Error probando detector optimizado: {e}")
                
        except ImportError:
            self._error("OptimizedCharacterDetector no disponible")
    
    def _verify_cache_system(self):
        """Verificar sistema de cache LRU"""
        self._section_header("Sistema de Cache LRU")
        
        try:
            from src.pattern_cache import PatternCache, get_global_cache
            self._success("PatternCache disponible")
            
            # Verificar cache global
            global_cache = get_global_cache()
            cache_stats = global_cache.get_stats()
            
            self._success(f"Cache global inicializado (tamaño: {cache_stats['max_size']})")
            
            if cache_stats['total_requests'] > 0:
                self._info(f"Estadisticas del cache:")
                self._info(f"  - Hit rate: {cache_stats['hit_rate']}%")
                self._info(f"  - Total requests: {cache_stats['total_requests']}")
                self._info(f"  - Efficiency score: {cache_stats['efficiency_score']}")
            else:
                self._info("Cache vacio (normal en inicio)")
            
            # Test básico del cache
            test_cache = PatternCache(max_size=10)
            
            def dummy_compute(x):
                return x * 2
            
            # Test cache miss y hit
            result1 = test_cache.get_or_compute("test", dummy_compute, 5)
            result2 = test_cache.get_or_compute("test", dummy_compute, 5)
            
            if result1 == result2 == 10:
                self._success("Test de cache: OK")
            else:
                self._warning("Test de cache: Resultados inesperados")
                
        except ImportError:
            self._error("Sistema de cache no disponible")
        except Exception as e:
            self._error(f"Error en sistema de cache: {e}")
    
    def _verify_database_structure(self):
        """Verificar estructura de base de datos principal"""
        self._section_header("Base de Datos Principal")
        
        try:
            from config import config
            db_path = Path(config.DATA_DIR) / 'videos.db'
            
            if db_path.exists():
                self._success(f"Base de datos: {db_path}")
                
                # Verificar estructura de tablas
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                expected_tables = ['videos', 'downloader_mapping', 'sqlite_sequence']
                found_tables = [table[0] for table in tables]
                
                for table in expected_tables:
                    if table in found_tables:
                        self._success(f"Tabla encontrada: {table}")
                        
                        # Contar registros
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        self._info(f"  - {count} registros")
                    else:
                        self._warning(f"Tabla faltante: {table}")
                
                conn.close()
                
            else:
                self._warning("Base de datos principal no existe (se creará automáticamente)")
                
        except Exception as e:
            self._error(f"Error verificando base de datos: {e}")
    
    def _verify_character_database(self):
        """Verificar base de datos de personajes optimizada"""
        self._section_header("Base de Datos de Personajes")
        
        try:
            from config import config
            char_db_path = Path(config.DATA_DIR) / 'character_database.json'
            
            if char_db_path.exists():
                self._success(f"Base de datos de personajes: {char_db_path}")
                
                with open(char_db_path, 'r', encoding='utf-8') as f:
                    char_db = json.load(f)
                
                total_characters = 0
                total_patterns = 0
                
                for game, game_data in char_db.items():
                    if isinstance(game_data.get('characters'), dict):
                        char_count = len(game_data['characters'])
                        total_characters += char_count
                        self._success(f"Juego {game}: {char_count} personajes")
                        
                        # Contar patrones en este juego
                        for char_name, char_data in game_data['characters'].items():
                            variants = char_data.get('variants', {})
                            for variant_type, variant_list in variants.items():
                                total_patterns += len(variant_list)
                    else:
                        self._warning(f"Juego {game}: estructura antigua detectada")
                
                self._success(f"Total personajes: {total_characters}")
                self._success(f"Total patrones estimados: {total_patterns}")
                
                # Verificar TikToker personas
                if 'tiktoker_personas' in char_db:
                    tiktoker_data = char_db['tiktoker_personas']
                    if isinstance(tiktoker_data.get('characters'), dict):
                        tiktoker_count = len(tiktoker_data['characters'])
                        self._success(f"TikToker Personas: {tiktoker_count} configurados")
                    else:
                        self._warning("TikToker Personas: estructura incorrecta")
                else:
                    self._info("TikToker Personas: no configurados")
                    
            else:
                self._error("Base de datos de personajes no encontrada")
                
        except Exception as e:
            self._error(f"Error verificando base de datos de personajes: {e}")
    
    def _verify_directories(self):
        """Verificar directorios del sistema"""
        self._section_header("Directorios del Sistema")
        
        try:
            from config import config
            
            # Verificar directorio de datos
            data_dir = Path(config.DATA_DIR)
            if data_dir.exists():
                self._success(f"Directorio de datos: {data_dir}")
            else:
                self._warning(f"Directorio de datos no existe: {data_dir}")
            
            # Verificar directorio de thumbnails
            thumbnails_dir = data_dir / 'thumbnails'
            if thumbnails_dir.exists():
                thumbnail_count = len(list(thumbnails_dir.glob('*.jpg')))
                self._success(f"Directorio de thumbnails: {thumbnail_count} archivos")
            else:
                self._info("Directorio de thumbnails no existe (se creará automáticamente)")
            
            # Verificar directorio de caras conocidas
            known_faces_dir = getattr(config, 'KNOWN_FACES_PATH', self.project_root / 'caras_conocidas')
            if Path(known_faces_dir).exists():
                # Contar subdirectorios (juegos)
                game_dirs = [d for d in Path(known_faces_dir).iterdir() if d.is_dir()]
                total_faces = sum(len(list(game_dir.glob('*.jpg'))) for game_dir in game_dirs)
                self._success(f"Caras conocidas: {len(game_dirs)} juegos, {total_faces} fotos")
            else:
                self._warning(f"Directorio de caras conocidas no existe: {known_faces_dir}")
                
        except Exception as e:
            self._error(f"Error verificando directorios: {e}")
    
    def _section_header(self, title: str):
        """Imprimir encabezado de sección"""
        print(f"\n{title}")
        print("-" * 50)
    
    def _success(self, message: str):
        """Registrar éxito"""
        print(f"OK {message}")
        self.success_count += 1
        self.total_checks += 1
    
    def _warning(self, message: str):
        """Registrar advertencia"""
        print(f"WARN {message}")
        self.warnings.append(message)
        self.total_checks += 1
    
    def _error(self, message: str):
        """Registrar error"""
        print(f"ERROR {message}")
        self.issues.append(message)
        self.total_checks += 1
    
    def _info(self, message: str):
        """Imprimir información adicional"""
        print(f"   {message}")
    
    def _generate_final_report(self) -> bool:
        """Generar reporte final"""
        print("\n" + "=" * 70)
        print("REPORTE FINAL DE VERIFICACION")
        print("=" * 70)
        
        success_rate = (self.success_count / self.total_checks * 100) if self.total_checks > 0 else 0
        
        print(f"OK Verificaciones exitosas: {self.success_count}/{self.total_checks} ({success_rate:.1f}%)")
        print(f"WARN Advertencias: {len(self.warnings)}")
        print(f"ERROR Errores criticos: {len(self.issues)}")
        
        if self.issues:
            print(f"\nERRORES CRITICOS QUE REQUIEREN ATENCION:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        
        if self.warnings:
            print(f"\nADVERTENCIAS (OPCIONAL):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        # Determinar estado general
        if not self.issues:
            if success_rate >= 90:
                print(f"\nSISTEMA ENTERPRISE COMPLETAMENTE FUNCIONAL")
                print(f"Tag-Flow V2 esta optimizado y listo para uso enterprise")
            elif success_rate >= 70:
                print(f"\nSISTEMA FUNCIONAL CON ADVERTENCIAS MENORES")
                print(f"Tag-Flow V2 esta funcional, revisa las advertencias si es necesario")
            else:
                print(f"\nSISTEMA FUNCIONAL PERO CON LIMITACIONES")
                print(f"Tag-Flow V2 funcionara pero con funcionalidad reducida")
        else:
            print(f"\nSISTEMA CON ERRORES CRITICOS")
            print(f"Resuelve los errores criticos antes de usar Tag-Flow V2")
        
        # Comandos sugeridos
        print(f"\nPROXIMOS PASOS RECOMENDADOS:")
        if not self.issues and success_rate >= 90:
            print(f"  • python main.py character-stats  # Ver estadisticas del sistema")
            print(f"  • python main.py 10                      # Procesar algunos videos")
            print(f"  • python app.py                          # Abrir interfaz web")
        elif self.warnings:
            print(f"  • Revisar y resolver advertencias si es necesario")
            print(f"  • python main.py show-stats       # Ver estado de fuentes")
        
        if self.issues:
            print(f"  • Resolver errores criticos listados arriba")
            print(f"  • python quickstart.py                   # Configuracion guiada")
        
        return len(self.issues) == 0

def main():
    """Función principal"""
    verifier = ConfigVerifier()
    success = verifier.verify_all()
    
    # Exit code para scripts automatizados
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
