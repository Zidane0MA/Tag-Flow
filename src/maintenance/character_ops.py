#!/usr/bin/env python3
"""
👥 Character Operations Module
Módulo especializado para operaciones de personajes extraído de main.py
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import requests
from urllib.parse import quote

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos del proyecto
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from src.database import DatabaseManager
from src.character_intelligence import CharacterIntelligence

# Instancias globales - movidas a funciones para evitar inicialización múltiple


class CharacterOperations:
    """
    👥 Operaciones especializadas de personajes
    
    Funcionalidades:
    - Gestión de personajes
    - Análisis de títulos
    - Mapeo de creadores
    - Limpieza de falsos positivos
    - Descarga de imágenes de personajes
    - Estadísticas del sistema
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.character_intelligence = CharacterIntelligence()
    
    def show_character_stats(self) -> Dict[str, Any]:
        """
        📊 Mostrar estadísticas completas del sistema optimizado
        
        Returns:
            Dict con estadísticas del sistema de personajes
        """
        logger.info("📊 Obteniendo estadísticas de Character Intelligence...")
        
        try:
            stats = self.character_intelligence.get_stats()
            
            # Estadísticas básicas
            basic_stats = {
                'total_characters': stats['total_characters'],
                'total_games': stats['total_games'],
                'detector_type': stats['detector_type'],
                'creator_mappings': stats['creator_mappings'],
                'auto_detected_mappings': stats['auto_detected_mappings'],
                'database_file': stats['database_file'],
                'mapping_file': stats['mapping_file']
            }
            
            # Estadísticas específicas del detector optimizado
            optimized_stats = {}
            if stats['detector_type'] == 'optimized':
                optimized_stats = {
                    'optimized_patterns': stats.get('optimized_patterns', 'N/A'),
                    'cache_hit_rate': stats.get('cache_hit_rate', 'N/A'),
                    'avg_detection_time_ms': stats.get('avg_detection_time_ms', 'N/A'),
                    'pattern_distribution': stats.get('pattern_distribution', {})
                }
            
            # Personajes por juego
            characters_by_game = {}
            for game, game_data in self.character_intelligence.character_db.items():
                if isinstance(game_data.get('characters'), dict):
                    count = len(game_data['characters'])
                    examples = list(game_data['characters'].keys())[:3]
                    characters_by_game[game] = {
                        'count': count,
                        'examples': examples,
                        'display_name': game.replace('_', ' ').title()
                    }
            
            # Mapeos de TikToker Personas
            auto_detected = self.character_intelligence.creator_mapping.get('auto_detected', {})
            tiktoker_personas = {}
            for creator, data in auto_detected.items():
                tiktoker_personas[creator] = {
                    'character': data.get('character', 'N/A'),
                    'confidence': data.get('confidence', 'N/A'),
                    'platform': data.get('platform', 'N/A')
                }
            
            # Reporte de rendimiento
            performance_report = {}
            if stats['detector_type'] == 'optimized':
                try:
                    performance = self.character_intelligence.get_performance_report()
                    if performance and 'total_patterns' in performance:
                        performance_report = {
                            'cache_size': performance.get('cache_size', 0),
                            'total_patterns': performance.get('total_patterns', 0),
                            'pattern_distribution': performance.get('pattern_distribution', {})
                        }
                except Exception as e:
                    logger.debug(f"Error obteniendo estadísticas detalladas: {e}")
            
            return {
                'success': True,
                'basic_stats': basic_stats,
                'optimized_stats': optimized_stats,
                'characters_by_game': characters_by_game,
                'tiktoker_personas': tiktoker_personas,
                'performance_report': performance_report,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de personajes: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_custom_character(self, character_name: str, game: str, 
                           aliases: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        👤 Agregar personaje personalizado
        
        Args:
            character_name: nombre del personaje
            game: juego/serie del personaje
            aliases: lista de alias del personaje
            
        Returns:
            Dict con resultado de la operación
        """
        logger.info(f"👤 Agregando personaje personalizado: {character_name} ({game})")
        
        try:
            # Validar entrada
            if not character_name or not game:
                return {
                    'success': False,
                    'error': 'Nombre de personaje y juego son requeridos'
                }
            
            # Cargar base de datos de personajes
            character_db_path = Path('data/character_database.json')
            if not character_db_path.exists():
                return {
                    'success': False,
                    'error': 'Base de datos de personajes no encontrada'
                }
            
            with open(character_db_path, 'r', encoding='utf-8') as f:
                character_db = json.load(f)
            
            # Normalizar nombre del juego
            game_key = game.lower().replace(' ', '_')
            
            # Crear entrada del juego si no existe
            if game_key not in character_db:
                character_db[game_key] = {
                    'name': game,
                    'characters': {}
                }
            
            # Crear patrones para el personaje
            patterns = [character_name]
            if aliases:
                patterns.extend(aliases)
            
            # Agregar personaje
            character_db[game_key]['characters'][character_name] = {
                'name': character_name,
                'patterns': patterns,
                'custom': True,
                'added_date': datetime.now().isoformat()
            }
            
            # Guardar base de datos
            with open(character_db_path, 'w', encoding='utf-8') as f:
                json.dump(character_db, f, indent=2, ensure_ascii=False)
            
            # Recargar intelligence system
            self.character_intelligence = CharacterIntelligence()
            
            logger.info(f"✅ Personaje agregado: {character_name}")
            
            return {
                'success': True,
                'character_name': character_name,
                'game': game,
                'aliases': aliases or [],
                'patterns': patterns,
                'message': f'Personaje {character_name} agregado exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error agregando personaje: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def clean_false_positives(self, force: bool = False) -> Dict[str, Any]:
        """
        🧹 Limpiar falsos positivos del sistema de reconocimiento de personajes
        
        Args:
            force: forzar limpieza sin confirmación
            
        Returns:
            Dict con resultado de la limpieza
        """
        logger.info("🧹 Iniciando limpieza de falsos positivos...")
        
        try:
            # Lista de falsos positivos conocidos
            false_positives = {
                'common_words': [
                    'and', 'the', 'with', 'for', 'you', 'are', 'not', 'but',
                    'this', 'that', 'have', 'was', 'one', 'our', 'out', 'day',
                    'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now',
                    'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its',
                    'let', 'put', 'say', 'she', 'too', 'use'
                ],
                'platform_terms': [
                    'tiktok', 'youtube', 'instagram', 'twitter', 'facebook',
                    'live', 'stream', 'video', 'part', 'episode', 'chapter'
                ],
                'generic_terms': [
                    'girl', 'boy', 'woman', 'man', 'person', 'people',
                    'game', 'play', 'show', 'movie', 'anime', 'manga'
                ]
            }
            
            # Obtener videos con personajes detectados
            videos_with_characters = self.db.get_videos({'detected_characters': {'$ne': None}})
            
            cleaned_videos = []
            total_cleaned = 0
            
            for video in videos_with_characters:
                try:
                    detected_characters = video.get('detected_characters')
                    if not detected_characters:
                        continue
                    
                    # Parsear JSON si es string
                    if isinstance(detected_characters, str):
                        characters = json.loads(detected_characters)
                    else:
                        characters = detected_characters
                    
                    # Filtrar falsos positivos
                    original_count = len(characters)
                    cleaned_characters = []
                    
                    for char in characters:
                        char_name = char.get('name', '').lower()
                        is_false_positive = False
                        
                        # Verificar contra listas de falsos positivos
                        for category, fp_list in false_positives.items():
                            if char_name in fp_list:
                                is_false_positive = True
                                break
                        
                        # Verificar longitud mínima
                        if len(char_name) < 3:
                            is_false_positive = True
                        
                        if not is_false_positive:
                            cleaned_characters.append(char)
                    
                    # Actualizar BD si hubo cambios
                    if len(cleaned_characters) != original_count:
                        cleaned_count = original_count - len(cleaned_characters)
                        total_cleaned += cleaned_count
                        
                        # Actualizar video
                        update_data = {
                            'detected_characters': json.dumps(cleaned_characters) if cleaned_characters else None
                        }
                        self.db.update_video(video['id'], update_data)
                        
                        cleaned_videos.append({
                            'video_id': video['id'],
                            'video_name': video.get('file_name', 'Unknown'),
                            'original_count': original_count,
                            'cleaned_count': len(cleaned_characters),
                            'removed_count': cleaned_count
                        })
                        
                except Exception as e:
                    logger.warning(f"Error procesando video {video.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Limpieza completada: {total_cleaned} falsos positivos eliminados de {len(cleaned_videos)} videos")
            
            return {
                'success': True,
                'total_cleaned': total_cleaned,
                'videos_processed': len(cleaned_videos),
                'cleaned_videos': cleaned_videos[:10],  # Primeros 10 para no sobrecargar
                'false_positive_categories': list(false_positives.keys()),
                'message': f'Eliminados {total_cleaned} falsos positivos'
            }
            
        except Exception as e:
            logger.error(f"Error limpiando falsos positivos: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_creator_mappings(self, auto_detect: bool = True) -> Dict[str, Any]:
        """
        🔄 Actualizar mapeos de creadores basado en videos procesados
        
        Args:
            auto_detect: detectar automáticamente patrones
            
        Returns:
            Dict con resultado de la actualización
        """
        logger.info("🔄 Actualizando mapeos de creadores...")
        
        try:
            # Obtener videos con personajes detectados
            videos_with_characters = self.db.get_videos({'detected_characters': {'$ne': None}})
            
            # Analizar patrones creador -> personaje
            creator_patterns = {}
            
            for video in videos_with_characters:
                try:
                    creator = video.get('creator_name')
                    if not creator:
                        continue
                    
                    detected_characters = video.get('detected_characters')
                    if isinstance(detected_characters, str):
                        characters = json.loads(detected_characters)
                    else:
                        characters = detected_characters or []
                    
                    # Agregar al patrón
                    if creator not in creator_patterns:
                        creator_patterns[creator] = {}
                    
                    for char in characters:
                        char_name = char.get('name', 'Unknown')
                        if char_name not in creator_patterns[creator]:
                            creator_patterns[creator][char_name] = 0
                        creator_patterns[creator][char_name] += 1
                        
                except Exception as e:
                    logger.warning(f"Error procesando video {video.get('id', 'unknown')}: {e}")
                    continue
            
            # Generar mapeos automáticos
            suggested_mappings = {}
            
            for creator, characters in creator_patterns.items():
                # Encontrar personaje más frecuente
                if characters:
                    most_common_char = max(characters, key=characters.get)
                    frequency = characters[most_common_char]
                    total_videos = sum(characters.values())
                    confidence = frequency / total_videos
                    
                    # Solo sugerir si confianza > 60%
                    if confidence > 0.6:
                        suggested_mappings[creator] = {
                            'character': most_common_char,
                            'confidence': confidence,
                            'frequency': frequency,
                            'total_videos': total_videos
                        }
            
            # Cargar mapeos actuales
            mapping_file = Path('data/creator_character_mapping.json')
            if mapping_file.exists():
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    current_mappings = json.load(f)
            else:
                current_mappings = {'auto_detected': {}}
            
            # Actualizar mapeos si auto_detect está habilitado
            updated_mappings = 0
            if auto_detect:
                if 'auto_detected' not in current_mappings:
                    current_mappings['auto_detected'] = {}
                
                for creator, mapping in suggested_mappings.items():
                    current_mappings['auto_detected'][creator] = {
                        'character': mapping['character'],
                        'confidence': mapping['confidence'],
                        'platform': 'auto_detected',
                        'updated_date': datetime.now().isoformat()
                    }
                    updated_mappings += 1
                
                # Guardar mapeos actualizados
                with open(mapping_file, 'w', encoding='utf-8') as f:
                    json.dump(current_mappings, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Mapeos actualizados: {updated_mappings} creadores")
            
            return {
                'success': True,
                'analyzed_creators': len(creator_patterns),
                'suggested_mappings': len(suggested_mappings),
                'updated_mappings': updated_mappings,
                'suggestions': suggested_mappings,
                'auto_detect_enabled': auto_detect,
                'message': f'Analizados {len(creator_patterns)} creadores, {updated_mappings} mapeos actualizados'
            }
            
        except Exception as e:
            logger.error(f"Error actualizando mapeos: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_titles(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        📋 Analizar títulos de videos para detectar patrones
        
        Args:
            limit: límite de videos a analizar
            
        Returns:
            Dict con resultado del análisis
        """
        logger.info("📋 Analizando títulos de videos...")
        
        try:
            # Obtener videos
            videos = self.db.get_videos({'title': {'$ne': None}})
            
            if limit:
                videos = videos[:limit]
            
            # Analizar títulos
            title_patterns = {}
            character_mentions = {}
            word_frequency = {}
            
            for video in videos:
                try:
                    title = video.get('title', '')
                    if not title:
                        continue
                    
                    # Detectar personajes en título
                    detected_chars = self.character_intelligence.detect_characters(title)
                    
                    # Analizar palabras
                    words = title.lower().split()
                    for word in words:
                        # Limpiar palabra
                        clean_word = ''.join(c for c in word if c.isalnum())
                        if len(clean_word) >= 3:
                            word_frequency[clean_word] = word_frequency.get(clean_word, 0) + 1
                    
                    # Registrar menciones de personajes
                    for char in detected_chars:
                        # Verificar que char es un diccionario
                        if isinstance(char, dict):
                            char_name = char.get('name', 'Unknown')
                            confidence = char.get('confidence', 0)
                        elif isinstance(char, str):
                            char_name = char
                            confidence = 0
                        else:
                            char_name = str(char)
                            confidence = 0
                            
                        if char_name not in character_mentions:
                            character_mentions[char_name] = []
                        character_mentions[char_name].append({
                            'video_id': video['id'],
                            'title': title,
                            'confidence': confidence
                        })
                    
                    # Patrones de título
                    title_length = len(title)
                    if title_length not in title_patterns:
                        title_patterns[title_length] = 0
                    title_patterns[title_length] += 1
                    
                except Exception as e:
                    logger.warning(f"Error analizando título del video {video.get('id', 'unknown')}: {e}")
                    continue
            
            # Obtener top palabras
            top_words = sorted(word_frequency.items(), key=lambda x: x[1], reverse=True)[:20]
            
            # Obtener personajes más mencionados
            char_frequency = {char: len(mentions) for char, mentions in character_mentions.items()}
            top_characters = sorted(char_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Estadísticas de longitud de títulos
            title_lengths = list(title_patterns.keys())
            avg_title_length = sum(length * count for length, count in title_patterns.items()) / len(videos)
            
            logger.info(f"✅ Análisis completado: {len(videos)} títulos analizados")
            
            return {
                'success': True,
                'analyzed_videos': len(videos),
                'unique_words': len(word_frequency),
                'characters_mentioned': len(character_mentions),
                'top_words': top_words,
                'top_characters': top_characters,
                'title_stats': {
                    'avg_length': avg_title_length,
                    'min_length': min(title_lengths) if title_lengths else 0,
                    'max_length': max(title_lengths) if title_lengths else 0,
                    'length_distribution': title_patterns
                },
                'character_mentions': {char: len(mentions) for char, mentions in character_mentions.items()},
                'message': f'Analizados {len(videos)} títulos'
            }
            
        except Exception as e:
            logger.error(f"Error analizando títulos: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_character_images(self, character_name: Optional[str] = None, 
                                 game: Optional[str] = None, 
                                 limit: int = 10) -> Dict[str, Any]:
        """
        🖼️ Descargar imágenes de personajes para reconocimiento facial
        
        Args:
            character_name: nombre específico del personaje
            game: juego específico
            limit: límite de imágenes a descargar
            
        Returns:
            Dict con resultado de la descarga
        """
        logger.info(f"🖼️ Descargando imágenes de personajes...")
        
        try:
            # Determinar personajes a descargar
            characters_to_download = []
            
            if character_name and game:
                characters_to_download.append({'name': character_name, 'game': game})
            else:
                # Obtener personajes de la BD
                for game_key, game_data in self.character_intelligence.character_db.items():
                    if game and game_key != game.lower().replace(' ', '_'):
                        continue
                    
                    characters = game_data.get('characters', {})
                    for char_name in characters.keys():
                        if character_name and char_name.lower() != character_name.lower():
                            continue
                        
                        characters_to_download.append({
                            'name': char_name,
                            'game': game_key
                        })
            
            # Crear directorio de imágenes
            images_dir = Path('caras_conocidas')
            images_dir.mkdir(exist_ok=True)
            
            download_results = []
            total_downloaded = 0
            
            for char_info in characters_to_download[:limit]:
                try:
                    char_name = char_info['name']
                    game_name = char_info['game']
                    
                    # Crear directorio del juego
                    game_dir = images_dir / game_name
                    game_dir.mkdir(exist_ok=True)
                    
                    # Crear directorio del personaje
                    char_dir = game_dir / char_name
                    char_dir.mkdir(exist_ok=True)
                    
                    # Verificar si ya hay imágenes
                    existing_images = list(char_dir.glob('*.jpg'))
                    if len(existing_images) >= 3:
                        logger.info(f"⏩ {char_name} ya tiene {len(existing_images)} imágenes")
                        continue
                    
                    # Simular descarga (implementar API real según necesidades)
                    downloaded_count = self._download_character_images_mock(char_name, char_dir, limit=3)
                    
                    if downloaded_count > 0:
                        total_downloaded += downloaded_count
                        download_results.append({
                            'character': char_name,
                            'game': game_name,
                            'downloaded': downloaded_count,
                            'path': str(char_dir)
                        })
                        logger.info(f"✅ {char_name}: {downloaded_count} imágenes descargadas")
                    
                except Exception as e:
                    logger.warning(f"Error descargando imágenes para {char_info['name']}: {e}")
                    continue
            
            logger.info(f"✅ Descarga completada: {total_downloaded} imágenes")
            
            return {
                'success': True,
                'total_downloaded': total_downloaded,
                'characters_processed': len(download_results),
                'download_results': download_results,
                'images_directory': str(images_dir),
                'message': f'Descargadas {total_downloaded} imágenes para {len(download_results)} personajes'
            }
            
        except Exception as e:
            logger.error(f"Error descargando imágenes: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_character_detection_report(self, video_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        📊 Generar reporte de detección de personajes
        
        Args:
            video_ids: IDs específicos de videos o None para todos
            
        Returns:
            Dict con reporte de detección
        """
        try:
            # Obtener videos
            if video_ids:
                videos = []
                for video_id in video_ids:
                    video = self.db.get_video(video_id)
                    if video:
                        videos.append(video)
            else:
                videos = self.db.get_videos()
            
            # Analizar detecciones
            detection_stats = {
                'total_videos': len(videos),
                'videos_with_characters': 0,
                'videos_without_characters': 0,
                'character_frequency': {},
                'platform_stats': {},
                'creator_stats': {}
            }
            
            for video in videos:
                platform = video.get('platform', 'unknown')
                creator = video.get('creator_name', 'unknown')
                detected_characters = video.get('detected_characters')
                
                # Actualizar estadísticas de plataforma
                if platform not in detection_stats['platform_stats']:
                    detection_stats['platform_stats'][platform] = {
                        'total': 0,
                        'with_characters': 0
                    }
                detection_stats['platform_stats'][platform]['total'] += 1
                
                # Actualizar estadísticas de creador
                if creator not in detection_stats['creator_stats']:
                    detection_stats['creator_stats'][creator] = {
                        'total': 0,
                        'with_characters': 0,
                        'characters': {}
                    }
                detection_stats['creator_stats'][creator]['total'] += 1
                
                # Procesar personajes detectados
                if detected_characters:
                    try:
                        if isinstance(detected_characters, str):
                            characters = json.loads(detected_characters)
                        else:
                            characters = detected_characters
                        
                        if characters:
                            detection_stats['videos_with_characters'] += 1
                            detection_stats['platform_stats'][platform]['with_characters'] += 1
                            detection_stats['creator_stats'][creator]['with_characters'] += 1
                            
                            for char in characters:
                                # Verificar que char es un diccionario
                                if isinstance(char, dict):
                                    char_name = char.get('name', 'Unknown')
                                elif isinstance(char, str):
                                    char_name = char
                                else:
                                    char_name = str(char)
                                
                                # Frecuencia global
                                if char_name not in detection_stats['character_frequency']:
                                    detection_stats['character_frequency'][char_name] = 0
                                detection_stats['character_frequency'][char_name] += 1
                                
                                # Frecuencia por creador
                                if char_name not in detection_stats['creator_stats'][creator]['characters']:
                                    detection_stats['creator_stats'][creator]['characters'][char_name] = 0
                                detection_stats['creator_stats'][creator]['characters'][char_name] += 1
                        else:
                            detection_stats['videos_without_characters'] += 1
                    except Exception as e:
                        logger.warning(f"Error procesando personajes del video {video.get('id')}: {e}")
                        detection_stats['videos_without_characters'] += 1
                else:
                    detection_stats['videos_without_characters'] += 1
            
            # Calcular porcentajes
            total = detection_stats['total_videos']
            detection_stats['detection_rate'] = (detection_stats['videos_with_characters'] / total * 100) if total > 0 else 0
            
            # Top personajes
            top_characters = sorted(
                detection_stats['character_frequency'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Top creadores con personajes
            top_creators = sorted(
                [(creator, stats['with_characters']) for creator, stats in detection_stats['creator_stats'].items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                'success': True,
                'detection_stats': detection_stats,
                'top_characters': top_characters,
                'top_creators': top_creators,
                'summary': {
                    'total_videos': total,
                    'detection_rate': detection_stats['detection_rate'],
                    'unique_characters': len(detection_stats['character_frequency']),
                    'active_creators': len([c for c, s in detection_stats['creator_stats'].items() if s['with_characters'] > 0])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Métodos privados auxiliares
    
    def _download_character_images_mock(self, character_name: str, char_dir: Path, limit: int = 3) -> int:
        """Mock para descarga de imágenes (implementar API real)"""
        try:
            # Simular descarga creando archivos placeholder
            downloaded = 0
            for i in range(limit):
                placeholder_path = char_dir / f"{character_name}_{i+1}.jpg"
                if not placeholder_path.exists():
                    # Crear archivo placeholder
                    placeholder_path.write_text(f"Placeholder image for {character_name}")
                    downloaded += 1
            
            return downloaded
        except Exception as e:
            logger.warning(f"Error en mock download: {e}")
            return 0


# Funciones de conveniencia para compatibilidad
def show_character_stats() -> Dict[str, Any]:
    """Función de conveniencia para mostrar estadísticas"""
    ops = CharacterOperations()
    return ops.show_character_stats()

def add_custom_character(character_name: str, game: str, aliases: Optional[List[str]] = None) -> Dict[str, Any]:
    """Función de conveniencia para agregar personaje"""
    ops = CharacterOperations()
    return ops.add_custom_character(character_name, game, aliases)

def clean_false_positives(force: bool = False) -> Dict[str, Any]:
    """Función de conveniencia para limpiar falsos positivos"""
    ops = CharacterOperations()
    return ops.clean_false_positives(force)

def update_creator_mappings(auto_detect: bool = True) -> Dict[str, Any]:
    """Función de conveniencia para actualizar mapeos"""
    ops = CharacterOperations()
    return ops.update_creator_mappings(auto_detect)

def analyze_titles(limit: Optional[int] = None) -> Dict[str, Any]:
    """Función de conveniencia para analizar títulos"""
    ops = CharacterOperations()
    return ops.analyze_titles(limit)

def download_character_images(character_name: Optional[str] = None, 
                             game: Optional[str] = None, 
                             limit: int = 10) -> Dict[str, Any]:
    """Función de conveniencia para descargar imágenes"""
    ops = CharacterOperations()
    return ops.download_character_images(character_name, game, limit)

def get_character_detection_report(video_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """Función de conveniencia para reporte de detección"""
    ops = CharacterOperations()
    return ops.get_character_detection_report(video_ids)