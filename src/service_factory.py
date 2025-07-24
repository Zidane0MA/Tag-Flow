"""
🏭 Service Factory - Sistema Centralizado de Gestión de Dependencias
Factory pattern para manejo limpio de singletons y lazy loading consistente
"""

import logging
from typing import Dict, Any, Optional, Callable
from threading import Lock

logger = logging.getLogger(__name__)

class ServiceFactory:
    """
    🏭 Factory centralizado para todos los servicios del sistema
    
    Características:
    - Lazy loading: Servicios se crean solo cuando se necesitan
    - Thread-safe: Manejo seguro de concurrencia  
    - Singleton pattern: Una instancia por servicio
    - Eliminación de dependencias circulares
    - Logging de inicialización para debugging
    """
    
    _instances: Dict[str, Any] = {}
    _factories: Dict[str, Callable] = {}
    _locks: Dict[str, Lock] = {}
    _main_lock = Lock()
    
    @classmethod
    def register_factory(cls, service_name: str, factory_func: Callable):
        """Registrar factory function para un servicio"""
        with cls._main_lock:
            cls._factories[service_name] = factory_func
            cls._locks[service_name] = Lock()
            logger.debug(f"🏭 Factory registrado: {service_name}")
    
    @classmethod
    def get_service(cls, service_name: str) -> Any:
        """Obtener instancia de servicio con lazy loading thread-safe"""
        if service_name not in cls._factories:
            raise ValueError(f"Servicio no registrado: {service_name}")
        
        # Double-checked locking pattern para performance
        if service_name not in cls._instances:
            with cls._locks[service_name]:
                if service_name not in cls._instances:
                    logger.info(f"🚀 Inicializando servicio: {service_name}")
                    cls._instances[service_name] = cls._factories[service_name]()
                    logger.info(f"✅ Servicio inicializado: {service_name}")
        
        return cls._instances[service_name]
    
    @classmethod
    def is_service_loaded(cls, service_name: str) -> bool:
        """Verificar si un servicio ya está cargado en memoria"""
        return service_name in cls._instances
    
    @classmethod
    def reset_service(cls, service_name: str):
        """Reinicializar un servicio específico (útil para testing)"""
        with cls._main_lock:
            if service_name in cls._instances:
                del cls._instances[service_name]
                logger.info(f"🔄 Servicio reiniciado: {service_name}")
    
    @classmethod
    def reset_all(cls):
        """Reinicializar todos los servicios (útil para testing)"""
        with cls._main_lock:
            cls._instances.clear()
            logger.info("🔄 Todos los servicios reiniciados")
    
    @classmethod
    def get_loaded_services(cls) -> list:
        """Obtener lista de servicios actualmente cargados en memoria"""
        return list(cls._instances.keys())


# Factory functions para cada servicio
def _create_database_manager():
    """Factory para DatabaseManager"""
    from src.database import DatabaseManager
    return DatabaseManager()

def _create_character_intelligence():
    """Factory para CharacterIntelligence"""
    from src.character_intelligence import CharacterIntelligence
    return CharacterIntelligence()

def _create_thumbnail_generator():
    """Factory para ThumbnailGenerator"""
    from src.thumbnail_generator import ThumbnailGenerator
    return ThumbnailGenerator()

def _create_face_recognizer():
    """Factory para FaceRecognizer"""
    from src.face_recognition import FaceRecognizer
    return FaceRecognizer()

def _create_music_recognizer():
    """Factory para MusicRecognizer"""
    from src.music_recognition import MusicRecognizer
    return MusicRecognizer()

def _create_video_processor():
    """Factory para VideoProcessor"""
    from src.video_processor import VideoProcessor
    return VideoProcessor()

def _create_external_sources():
    """Factory para ExternalSourcesManager"""
    from src.external_sources import ExternalSourcesManager
    return ExternalSourcesManager()

def _create_downloader_integration():
    """Factory para DownloaderIntegration"""
    from src.downloader_integration import DownloaderIntegration
    return DownloaderIntegration()


# Registrar todos los factories
ServiceFactory.register_factory('database', _create_database_manager)
ServiceFactory.register_factory('character_intelligence', _create_character_intelligence)
ServiceFactory.register_factory('thumbnail_generator', _create_thumbnail_generator)
ServiceFactory.register_factory('face_recognizer', _create_face_recognizer)
ServiceFactory.register_factory('music_recognizer', _create_music_recognizer)
ServiceFactory.register_factory('video_processor', _create_video_processor)
ServiceFactory.register_factory('external_sources', _create_external_sources)
ServiceFactory.register_factory('downloader_integration', _create_downloader_integration)


# Funciones de conveniencia para mantener compatibilidad
def get_database():
    """Obtener instancia de DatabaseManager"""
    return ServiceFactory.get_service('database')

def get_character_intelligence():
    """Obtener instancia de CharacterIntelligence"""
    return ServiceFactory.get_service('character_intelligence')

def get_thumbnail_generator():
    """Obtener instancia de ThumbnailGenerator"""
    return ServiceFactory.get_service('thumbnail_generator')

def get_face_recognizer():
    """Obtener instancia de FaceRecognizer"""
    return ServiceFactory.get_service('face_recognizer')

def get_music_recognizer():
    """Obtener instancia de MusicRecognizer"""
    return ServiceFactory.get_service('music_recognizer')

def get_video_processor():
    """Obtener instancia de VideoProcessor"""
    return ServiceFactory.get_service('video_processor')

def get_external_sources():
    """Obtener instancia de ExternalSourcesManager"""
    return ServiceFactory.get_service('external_sources')

def get_downloader_integration():
    """Obtener instancia de DownloaderIntegration"""
    return ServiceFactory.get_service('downloader_integration')