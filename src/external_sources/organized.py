"""
Tag-Flow V2 - Organized Folders Handler
Specialized handler for videos from organized folder structures
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from .base import FolderExtractor

import logging
logger = logging.getLogger(__name__)


class OrganizedFoldersHandler(FolderExtractor):
    """Handler for videos from organized folder structures"""
    
    def __init__(self, base_path: Optional[Path] = None):
        super().__init__(base_path)
        
        # Define organized folder structure
        if self.base_path:
            self.organized_youtube_path = self.base_path / "youtube"
            self.organized_tiktok_path = self.base_path / "tiktok"  
            self.organized_instagram_path = self.base_path / "instagram"
        else:
            self.organized_youtube_path = None
            self.organized_tiktok_path = None
            self.organized_instagram_path = None
    
    def get_available_platforms(self) -> Dict:
        """Obtener plataformas disponibles en carpetas organizadas"""
        platforms = {
            'main': {},
            'additional': {}
        }
        
        if not self.is_available():
            return platforms
        
        try:
            # Plataformas principales predefinidas
            main_platforms = {
                'youtube': {
                    'folder_name': 'YouTube',
                    'has_organized': self.organized_youtube_path and self.organized_youtube_path.exists()
                },
                'tiktok': {
                    'folder_name': 'TikTok',
                    'has_organized': self.organized_tiktok_path and self.organized_tiktok_path.exists()
                },
                'instagram': {
                    'folder_name': 'Instagram',
                    'has_organized': self.organized_instagram_path and self.organized_instagram_path.exists()
                }
            }
            
            platforms['main'] = main_platforms
            
            # Buscar plataformas adicionales automáticamente
            additional_platforms = self._discover_additional_platforms()
            platforms['additional'] = additional_platforms
            
            return platforms
            
        except Exception as e:
            self.logger.error(f"Error obteniendo plataformas organizadas: {e}")
            return platforms
    
    def _discover_additional_platforms(self) -> Dict:
        """Descubrir plataformas adicionales en el directorio base"""
        additional = {}
        
        try:
            if not self.base_path or not self.base_path.exists():
                return additional
            
            # Plataformas principales a excluir
            main_folders = {'youtube', 'tiktok', 'instagram'}
            
            # Escanear directorios en busca de plataformas adicionales
            for folder in self.base_path.iterdir():
                if (folder.is_dir() and 
                    folder.name.lower() not in main_folders and
                    not folder.name.startswith('.') and
                    not folder.name.startswith('_')):
                    
                    # Verificar si contiene videos
                    video_files = self._get_video_files(folder)
                    if video_files:
                        platform_key = folder.name.lower()
                        additional[platform_key] = {
                            'folder_name': folder.name,
                            'folder_path': folder,
                            'video_count': len(video_files)
                        }
            
            return additional
            
        except Exception as e:
            self.logger.error(f"Error descubriendo plataformas adicionales: {e}")
            return additional
    
    def extract_videos(self, platform_filter: Optional[str] = None) -> List[Dict]:
        """
        🆕 Extraer videos de TODAS las carpetas organizadas (principales + adicionales)
        
        Args:
            platform_filter: 'youtube', 'tiktok', 'instagram', 'other', 'all-platforms', o nombre específico como 'iwara'
        """
        self.logger.info("Extrayendo videos de carpetas organizadas (modo extendido)...")
        videos = []
        
        # Obtener plataformas disponibles
        available_platforms = self.get_available_platforms()
        
        # Determinar qué carpetas escanear según el filtro
        folders_to_scan = []
        
        if platform_filter is None or platform_filter == 'all-platforms':
            # Escanear todas las plataformas (principales + adicionales)
            # Plataformas principales
            for platform_key, platform_info in available_platforms['main'].items():
                if platform_info['has_organized']:
                    folder_path = getattr(self, f'organized_{platform_key}_path')
                    folders_to_scan.append((folder_path, platform_key, platform_info['folder_name']))
            
            # Plataformas adicionales
            for platform_key, platform_info in available_platforms['additional'].items():
                folders_to_scan.append((platform_info['folder_path'], platform_key, platform_info['folder_name']))
                
        elif platform_filter == 'other':
            # Solo plataformas adicionales (no principales)
            for platform_key, platform_info in available_platforms['additional'].items():
                folders_to_scan.append((platform_info['folder_path'], platform_key, platform_info['folder_name']))
                
        elif platform_filter in ['youtube', 'tiktok', 'instagram']:
            # Plataforma principal específica
            if platform_filter in available_platforms['main'] and available_platforms['main'][platform_filter]['has_organized']:
                folder_path = getattr(self, f'organized_{platform_filter}_path')
                platform_info = available_platforms['main'][platform_filter]
                folders_to_scan.append((folder_path, platform_filter, platform_info['folder_name']))
                
        else:
            # Buscar plataforma específica por nombre (ej: 'iwara')
            platform_found = False
            
            self.logger.info(f"🔍 Buscando plataforma '{platform_filter}' en plataformas adicionales...")
            self.logger.info(f"📁 Plataformas adicionales disponibles: {list(available_platforms['additional'].keys())}")
            
            # Buscar en plataformas adicionales
            for platform_key, platform_info in available_platforms['additional'].items():
                self.logger.debug(f"Comparando: platform_key='{platform_key}' vs platform_filter.lower()='{platform_filter.lower()}'")
                
                if platform_key == platform_filter.lower():
                    folders_to_scan.append((platform_info['folder_path'], platform_key, platform_info['folder_name']))
                    platform_found = True
                    self.logger.info(f"✅ Plataforma '{platform_filter}' encontrada!")
                    break
            
            if not platform_found:
                self.logger.warning(f"⚠️ Plataforma '{platform_filter}' no encontrada en carpetas organizadas")
                return videos
        
        # Escanear las carpetas seleccionadas
        for folder_path, platform_key, folder_name in folders_to_scan:
            self.logger.info(f"📁 Escaneando {folder_name} ({folder_path})...")
            
            try:
                platform_videos = self._extract_from_organized_folder(folder_path, platform_key)
                videos.extend(platform_videos)
                self.logger.info(f"✅ Extraídos {len(platform_videos)} videos de {folder_name}")
                
            except Exception as e:
                self.logger.error(f"❌ Error escaneando {folder_name}: {e}")
                continue
        
        self.logger.info(f"🎯 Total de videos extraídos de carpetas organizadas: {len(videos)}")
        return videos
    
    def extract_legacy(self, platform: Optional[str] = None) -> List[Dict]:
        """Método legacy para compatibilidad con código existente"""
        return self.extract_videos(platform)
    
    def _extract_from_organized_folder(self, folder_path: Path, platform: str) -> List[Dict]:
        """Extraer videos de una carpeta organizada específica"""
        videos = []
        
        if not folder_path or not folder_path.exists():
            return videos
        
        try:
            video_files = self._get_video_files(folder_path)
            
            for video_file in video_files:
                video_data = self._process_organized_video_file(video_file, platform)
                if video_data:
                    videos.append(video_data)
            
            return videos
            
        except Exception as e:
            self.logger.error(f"Error extrayendo de carpeta organizada {folder_path}: {e}")
            return videos
    
    def _process_organized_video_file(self, file_path: Path, platform: str) -> Optional[Dict]:
        """Procesar un archivo de video de carpeta organizada"""
        try:
            if not file_path.exists():
                return None
            
            # Determinar creador desde la estructura de carpetas
            creator_name = self._extract_creator_from_organized_path(file_path, platform)
            
            # Construir estructura del video
            video_data = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'title': file_path.stem,
                'platform': self._normalize_platform_name(platform),
                'source': 'organized',
                
                # Información del creador
                'creator_name': creator_name,
                'creator_url': self._build_creator_url(creator_name, platform),
                
                # Para carpetas organizadas, generalmente no hay suscripciones específicas
                'subscription_name': None,
                'subscription_type': None,
                'subscription_url': None,
                
                # Información de archivo
                **self._get_file_stats(file_path)
            }
            
            return video_data
            
        except Exception as e:
            self.logger.error(f"Error procesando archivo organizado {file_path}: {e}")
            return None
    
    def _extract_creator_from_organized_path(self, file_path: Path, platform: str) -> Optional[str]:
        """Extraer creador desde la estructura de carpetas organizadas"""
        try:
            # Obtener partes de la ruta relativa al directorio de la plataforma
            platform_folder = getattr(self, f'organized_{platform}_path', None)
            
            if platform_folder and platform_folder in file_path.parents:
                # Obtener ruta relativa desde la carpeta de la plataforma
                try:
                    relative_path = file_path.relative_to(platform_folder)
                    parts = relative_path.parts[:-1]  # Excluir el nombre del archivo
                    
                    if parts:
                        # El primer directorio después de la plataforma suele ser el creador
                        creator_candidate = parts[0]
                        
                        # Limpiar y validar el nombre del creador
                        creator_clean = self._clean_creator_name(creator_candidate)
                        if creator_clean:
                            return creator_clean
                            
                except ValueError:
                    pass
            
            # Fallback: usar método base
            return self._extract_creator_from_path(file_path)
            
        except Exception as e:
            self.logger.error(f"Error extrayendo creador de ruta organizada: {e}")
            return None
    
    def _clean_creator_name(self, creator_name: str) -> Optional[str]:
        """Limpiar y validar nombre de creador"""
        if not creator_name:
            return None
        
        # Remover caracteres especiales y limpiar
        creator_clean = re.sub(r'[^\w\s\-_.]', '', creator_name).strip()
        
        # Validar longitud y contenido
        if len(creator_clean) < 2 or len(creator_clean) > 100:
            return None
        
        # Evitar nombres genéricos comunes
        generic_names = {
            'downloads', 'videos', 'content', 'media', 'files',
            'new', 'temp', 'tmp', 'data', 'misc', 'other'
        }
        
        if creator_clean.lower() in generic_names:
            return None
        
        return creator_clean
    
    def _build_creator_url(self, creator_name: str, platform: str) -> Optional[str]:
        """Construir URL del creador basada en la plataforma"""
        if not creator_name:
            return None
        
        # Mapeo de plataformas a formatos de URL
        url_patterns = {
            'youtube': f"https://www.youtube.com/@{creator_name}",
            'tiktok': f"https://www.tiktok.com/@{creator_name}",
            'instagram': f"https://www.instagram.com/{creator_name}/",
            'twitter': f"https://twitter.com/{creator_name}",
            'x': f"https://x.com/{creator_name}",
            'twitch': f"https://www.twitch.tv/{creator_name}",
            'facebook': f"https://www.facebook.com/{creator_name}",
        }
        
        return url_patterns.get(platform.lower())