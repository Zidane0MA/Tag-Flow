#!/usr/bin/env python3
"""
🔧 Maintenance Utils Module
Módulo de utilidades comunes para operaciones de mantenimiento
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
import hashlib
import shutil
import psutil
import threading
from functools import wraps
from dataclasses import dataclass
from enum import Enum

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos del proyecto
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config


class LogLevel(Enum):
    """Niveles de logging"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class SystemStats:
    """Estadísticas del sistema"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    memory_total_gb: float
    memory_used_gb: float
    disk_total_gb: float
    disk_used_gb: float
    uptime_hours: float
    load_average: List[float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'disk_percent': self.disk_percent,
            'memory_total_gb': self.memory_total_gb,
            'memory_used_gb': self.memory_used_gb,
            'disk_total_gb': self.disk_total_gb,
            'disk_used_gb': self.disk_used_gb,
            'uptime_hours': self.uptime_hours,
            'load_average': self.load_average
        }


class ProgressTracker:
    """Seguimiento de progreso para operaciones largas"""
    
    def __init__(self, total_items: int, description: str = "Processing"):
        self.total_items = total_items
        self.description = description
        self.processed_items = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.callbacks: List[Callable] = []
    
    def add_callback(self, callback: Callable):
        """Agregar callback para notificaciones de progreso"""
        with self.lock:
            self.callbacks.append(callback)
    
    def update(self, increment: int = 1, current_item: str = ""):
        """Actualizar progreso"""
        with self.lock:
            self.processed_items += increment
            progress_percentage = (self.processed_items / self.total_items) * 100 if self.total_items > 0 else 0
            
            # Notificar callbacks
            for callback in self.callbacks:
                try:
                    callback(self.processed_items, self.total_items, current_item)
                except Exception as e:
                    logger.warning(f"Error en callback de progreso: {e}")
    
    def get_progress(self) -> Dict[str, Any]:
        """Obtener estado actual del progreso"""
        with self.lock:
            elapsed_time = time.time() - self.start_time
            progress_percentage = (self.processed_items / self.total_items) * 100 if self.total_items > 0 else 0
            
            # Estimar tiempo restante
            if self.processed_items > 0:
                avg_time_per_item = elapsed_time / self.processed_items
                remaining_items = self.total_items - self.processed_items
                eta_seconds = remaining_items * avg_time_per_item
            else:
                eta_seconds = 0
            
            return {
                'description': self.description,
                'processed_items': self.processed_items,
                'total_items': self.total_items,
                'progress_percentage': progress_percentage,
                'elapsed_time': elapsed_time,
                'eta_seconds': eta_seconds,
                'items_per_second': self.processed_items / elapsed_time if elapsed_time > 0 else 0
            }


class FileUtils:
    """Utilidades para manejo de archivos"""
    
    @staticmethod
    def safe_path(path: Union[str, Path]) -> Path:
        """Convertir a Path de forma segura"""
        try:
            return Path(path).resolve()
        except Exception as e:
            logger.warning(f"Error convirtiendo path {path}: {e}")
            return Path(str(path))
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Crear directorio si no existe"""
        dir_path = FileUtils.safe_path(path)
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            return dir_path
        except Exception as e:
            logger.error(f"Error creando directorio {dir_path}: {e}")
            raise
    
    @staticmethod
    def get_file_size(path: Union[str, Path]) -> int:
        """Obtener tamaño de archivo en bytes"""
        try:
            return FileUtils.safe_path(path).stat().st_size
        except Exception:
            return 0
    
    @staticmethod
    def get_file_hash(path: Union[str, Path], algorithm: str = 'md5') -> str:
        """Obtener hash de archivo"""
        try:
            hash_obj = hashlib.new(algorithm)
            with open(FileUtils.safe_path(path), 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.warning(f"Error calculando hash de {path}: {e}")
            return ""
    
    @staticmethod
    def copy_file_safe(source: Union[str, Path], destination: Union[str, Path], 
                      preserve_metadata: bool = True) -> bool:
        """Copiar archivo de forma segura"""
        try:
            source_path = FileUtils.safe_path(source)
            dest_path = FileUtils.safe_path(destination)
            
            # Crear directorio de destino si no existe
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copiar archivo
            if preserve_metadata:
                shutil.copy2(source_path, dest_path)
            else:
                shutil.copy(source_path, dest_path)
            
            return True
        except Exception as e:
            logger.error(f"Error copiando archivo {source} -> {destination}: {e}")
            return False
    
    @staticmethod
    def move_file_safe(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Mover archivo de forma segura"""
        try:
            source_path = FileUtils.safe_path(source)
            dest_path = FileUtils.safe_path(destination)
            
            # Crear directorio de destino si no existe
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Mover archivo
            shutil.move(source_path, dest_path)
            return True
        except Exception as e:
            logger.error(f"Error moviendo archivo {source} -> {destination}: {e}")
            return False
    
    @staticmethod
    def delete_file_safe(path: Union[str, Path]) -> bool:
        """Eliminar archivo de forma segura"""
        try:
            file_path = FileUtils.safe_path(path)
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Error eliminando archivo {path}: {e}")
            return False
    
    @staticmethod
    def find_files(directory: Union[str, Path], pattern: str = "*", 
                  recursive: bool = True) -> List[Path]:
        """Encontrar archivos que coincidan con patrón"""
        try:
            dir_path = FileUtils.safe_path(directory)
            if not dir_path.exists():
                return []
            
            if recursive:
                return list(dir_path.rglob(pattern))
            else:
                return list(dir_path.glob(pattern))
        except Exception as e:
            logger.warning(f"Error buscando archivos en {directory}: {e}")
            return []
    
    @staticmethod
    def get_directory_size(directory: Union[str, Path]) -> int:
        """Obtener tamaño total de directorio en bytes"""
        try:
            dir_path = FileUtils.safe_path(directory)
            total_size = 0
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except Exception as e:
            logger.warning(f"Error calculando tamaño de {directory}: {e}")
            return 0


class JsonUtils:
    """Utilidades para manejo de JSON"""
    
    @staticmethod
    def load_json(path: Union[str, Path], default: Any = None) -> Any:
        """Cargar archivo JSON de forma segura"""
        try:
            with open(FileUtils.safe_path(path), 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Archivo JSON no encontrado: {path}")
            return default
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON {path}: {e}")
            return default
        except Exception as e:
            logger.error(f"Error cargando JSON {path}: {e}")
            return default
    
    @staticmethod
    def save_json(data: Any, path: Union[str, Path], indent: int = 2, 
                 ensure_ascii: bool = False) -> bool:
        """Guardar datos como JSON de forma segura"""
        try:
            file_path = FileUtils.safe_path(path)
            
            # Crear directorio si no existe
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar con archivo temporal para atomicidad
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            
            # Mover archivo temporal al final
            temp_path.rename(file_path)
            return True
        except Exception as e:
            logger.error(f"Error guardando JSON {path}: {e}")
            return False
    
    @staticmethod
    def merge_json(base_data: Dict, update_data: Dict, deep: bool = True) -> Dict:
        """Fusionar diccionarios JSON"""
        if not deep:
            return {**base_data, **update_data}
        
        result = base_data.copy()
        for key, value in update_data.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = JsonUtils.merge_json(result[key], value, deep=True)
            else:
                result[key] = value
        return result


class SystemUtils:
    """Utilidades del sistema"""
    
    @staticmethod
    def get_system_stats() -> SystemStats:
        """Obtener estadísticas del sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memoria
            memory = psutil.virtual_memory()
            
            # Disco
            disk = psutil.disk_usage('/')
            
            # Uptime
            boot_time = psutil.boot_time()
            uptime_hours = (time.time() - boot_time) / 3600
            
            # Load average (solo en sistemas Unix)
            try:
                load_avg = list(os.getloadavg())
            except (OSError, AttributeError):
                load_avg = [0.0, 0.0, 0.0]
            
            return SystemStats(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=(disk.used / disk.total) * 100,
                memory_total_gb=memory.total / (1024**3),
                memory_used_gb=memory.used / (1024**3),
                disk_total_gb=disk.total / (1024**3),
                disk_used_gb=disk.used / (1024**3),
                uptime_hours=uptime_hours,
                load_average=load_avg
            )
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del sistema: {e}")
            return SystemStats(0, 0, 0, 0, 0, 0, 0, 0, [0, 0, 0])
    
    @staticmethod
    def check_disk_space(path: Union[str, Path], min_gb: float = 1.0) -> bool:
        """Verificar espacio en disco disponible"""
        try:
            disk_usage = psutil.disk_usage(str(path))
            available_gb = disk_usage.free / (1024**3)
            return available_gb >= min_gb
        except Exception as e:
            logger.warning(f"Error verificando espacio en disco: {e}")
            return False
    
    @staticmethod
    def check_memory_usage(max_percent: float = 90.0) -> bool:
        """Verificar uso de memoria"""
        try:
            memory = psutil.virtual_memory()
            return memory.percent <= max_percent
        except Exception as e:
            logger.warning(f"Error verificando uso de memoria: {e}")
            return False
    
    @staticmethod
    def get_process_info(pid: Optional[int] = None) -> Dict[str, Any]:
        """Obtener información del proceso"""
        try:
            if pid is None:
                pid = os.getpid()
            
            process = psutil.Process(pid)
            
            return {
                'pid': pid,
                'name': process.name(),
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'memory_mb': process.memory_info().rss / (1024**2),
                'status': process.status(),
                'create_time': process.create_time(),
                'num_threads': process.num_threads()
            }
        except Exception as e:
            logger.warning(f"Error obteniendo info del proceso: {e}")
            return {}


class TimeUtils:
    """Utilidades de tiempo"""
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Formatear duración en segundos a string legible"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    @staticmethod
    def format_timestamp(timestamp: Union[float, datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Formatear timestamp a string"""
        try:
            if isinstance(timestamp, float):
                dt = datetime.fromtimestamp(timestamp)
            else:
                dt = timestamp
            return dt.strftime(format_str)
        except Exception as e:
            logger.warning(f"Error formateando timestamp: {e}")
            return "Unknown"
    
    @staticmethod
    def get_age_in_days(timestamp: Union[float, datetime]) -> int:
        """Obtener edad en días"""
        try:
            if isinstance(timestamp, float):
                dt = datetime.fromtimestamp(timestamp)
            else:
                dt = timestamp
            return (datetime.now() - dt).days
        except Exception as e:
            logger.warning(f"Error calculando edad: {e}")
            return 0
    
    @staticmethod
    def is_older_than(timestamp: Union[float, datetime], days: int) -> bool:
        """Verificar si fecha es más antigua que X días"""
        return TimeUtils.get_age_in_days(timestamp) > days


class ValidationUtils:
    """Utilidades de validación"""
    
    @staticmethod
    def validate_video_file(path: Union[str, Path]) -> bool:
        """Validar archivo de video"""
        try:
            file_path = FileUtils.safe_path(path)
            
            # Verificar existencia
            if not file_path.exists():
                return False
            
            # Verificar extensión
            valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
            if file_path.suffix.lower() not in valid_extensions:
                return False
            
            # Verificar tamaño mínimo
            if file_path.stat().st_size < 1024:  # Menos de 1KB
                return False
            
            return True
        except Exception as e:
            logger.warning(f"Error validando archivo de video {path}: {e}")
            return False
    
    @staticmethod
    def validate_image_file(path: Union[str, Path]) -> bool:
        """Validar archivo de imagen"""
        try:
            file_path = FileUtils.safe_path(path)
            
            # Verificar existencia
            if not file_path.exists():
                return False
            
            # Verificar extensión
            valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            if file_path.suffix.lower() not in valid_extensions:
                return False
            
            # Verificar tamaño mínimo
            if file_path.stat().st_size < 100:  # Menos de 100 bytes
                return False
            
            return True
        except Exception as e:
            logger.warning(f"Error validando archivo de imagen {path}: {e}")
            return False
    
    @staticmethod
    def validate_json_file(path: Union[str, Path]) -> bool:
        """Validar archivo JSON"""
        try:
            file_path = FileUtils.safe_path(path)
            
            # Verificar existencia
            if not file_path.exists():
                return False
            
            # Intentar cargar JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            
            return True
        except Exception as e:
            logger.warning(f"Error validando archivo JSON {path}: {e}")
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validar formato de email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validar formato de URL"""
        import re
        pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        return re.match(pattern, url) is not None


class ErrorUtils:
    """Utilidades para manejo de errores"""
    
    @staticmethod
    def safe_execute(func: Callable, *args, default=None, **kwargs) -> Any:
        """Ejecutar función de forma segura"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Error ejecutando {func.__name__}: {e}")
            return default
    
    @staticmethod
    def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
        """Decorador para reintentar en caso de falla"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries:
                            logger.warning(f"Error en {func.__name__} (intento {attempt + 1}/{max_retries + 1}): {e}")
                            time.sleep(delay)
                        else:
                            logger.error(f"Error final en {func.__name__}: {e}")
                            raise last_exception
            return wrapper
        return decorator
    
    @staticmethod
    def log_exceptions(level: LogLevel = LogLevel.ERROR):
        """Decorador para logging automático de excepciones"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    log_method = getattr(logger, level.value.lower())
                    log_method(f"Excepción en {func.__name__}: {e}")
                    raise
            return wrapper
        return decorator


class ConfigUtils:
    """Utilidades de configuración"""
    
    @staticmethod
    def get_config_value(key: str, default: Any = None) -> Any:
        """Obtener valor de configuración"""
        try:
            return getattr(config, key, default)
        except Exception as e:
            logger.warning(f"Error obteniendo configuración {key}: {e}")
            return default
    
    @staticmethod
    def get_database_path() -> Path:
        """Obtener ruta de base de datos"""
        return FileUtils.safe_path(
            ConfigUtils.get_config_value('DATABASE_PATH', 'data/videos.db')
        )
    
    @staticmethod
    def get_thumbnails_path() -> Path:
        """Obtener ruta de thumbnails"""
        return FileUtils.safe_path(
            ConfigUtils.get_config_value('THUMBNAILS_PATH', 'data/thumbnails')
        )
    
    @staticmethod
    def get_known_faces_path() -> Path:
        """Obtener ruta de caras conocidas"""
        return FileUtils.safe_path(
            ConfigUtils.get_config_value('KNOWN_FACES_PATH', 'caras_conocidas')
        )
    
    @staticmethod
    def get_backup_path() -> Path:
        """Obtener ruta de backups"""
        return FileUtils.safe_path(
            ConfigUtils.get_config_value('BACKUP_PATH', 'backups')
        )


# Funciones de conveniencia
def format_bytes(bytes_count: int) -> str:
    """Formatear bytes a string legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"

def format_number(number: Union[int, float]) -> str:
    """Formatear número con separadores de miles"""
    return f"{number:,}"

def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncar string a longitud máxima"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def normalize_path(path: Union[str, Path]) -> str:
    """Normalizar ruta para comparación"""
    return str(FileUtils.safe_path(path)).replace('\\', '/')

def get_file_extension(path: Union[str, Path]) -> str:
    """Obtener extensión de archivo"""
    return FileUtils.safe_path(path).suffix.lower()

def create_timestamp() -> str:
    """Crear timestamp actual"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parsear timestamp string"""
    try:
        return datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
    except ValueError:
        try:
            return datetime.fromisoformat(timestamp_str)
        except ValueError:
            return None