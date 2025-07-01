"""
Tag-Flow V2 - Inteligencia de Personajes
Sistema avanzado para reconocimiento automático de personajes mediante:
1. Análisis de títulos de videos
2. Mapeo de creadores → personajes  
3. Base de datos de personajes conocidos
4. Descarga automática de imágenes de referencia
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import requests
from urllib.parse import quote
import time

from config import config

logger = logging.getLogger(__name__)

class CharacterIntelligence:
    """Sistema inteligente para reconocimiento automático de personajes"""
    
    def __init__(self):
        self.character_db_path = config.DATA_DIR / 'character_database.json'
        self.creator_mapping_path = config.DATA_DIR / 'creator_character_mapping.json'
        self.known_faces_path = config.KNOWN_FACES_PATH
        
        # Cargar bases de datos
        self.character_db = self._load_character_database()
        self.creator_mapping = self._load_creator_mapping()
        
        # Patrones para extracción de nombres de títulos
        self.character_patterns = self._init_character_patterns()
        
        logger.info("Character Intelligence inicializado")
    
    def _load_character_database(self) -> Dict:
        """Cargar base de datos de personajes conocidos"""
        if self.character_db_path.exists():
            try:
                with open(self.character_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando character_database.json: {e}")
        
        # Base de datos inicial con personajes populares de MMD/TikTok
        return {
            "genshin_impact": {
                "characters": [
                    "Hutao", "Hu Tao", "胡桃",
                    "Raiden Shogun", "Raiden", "雷電将軍", "Ei",
                    "Zhongli", "鍾離",
                    "Childe", "Tartaglia", "タルタリヤ",
                    "Venti", "ウェンティ",
                    "Albedo", "アルベド",
                    "Ganyu", "甘雨",
                    "Xiao", "魈",
                    "Kazuha", "楓原万葉",
                    "Ayaka", "神里綾華",
                    "Yae Miko", "八重神子",
                    "Itto", "荒瀧一斗",
                    "Kokomi", "珊瑚宮心海",
                    "Fischl", "フィッシュル",
                    "Mona", "モナ",
                    "Keqing", "刻晴",
                    "Diluc", "ディルック"
                ],
                "aliases": {
                    "Hutao": ["Hu Tao", "胡桃", "HuTao"],
                    "Raiden": ["Raiden Shogun", "雷電将軍", "Ei", "Baal"],
                    "Childe": ["Tartaglia", "タルタリヤ", "Ajax"]
                }
            },
            "honkai_impact": {
                "characters": [
                    "Elysia", "エリシア", "愛莉希雅",
                    "Mobius", "メビウス", "莫比烏斯",
                    "Raiden Mei", "雷電芽衣",
                    "Kiana", "キアナ", "琪亞娜",
                    "Bronya", "ブロニア", "布洛妮娅",
                    "Seele", "ゼーレ", "希兒",
                    "Rita", "リタ", "丽塔",
                    "Durandal", "デュランダル", "幽蘭黛爾",
                    "Fu Hua", "符華",
                    "Theresa", "テレサ", "德麗莎"
                ]
            },
            "zenless_zone_zero": {
                "characters": [
                    "Belle", "ベル", "贝尔",
                    "Wise", "ワイズ", "怀斯", 
                    "Anby", "アンビー", "安比",
                    "Nicole", "ニコル", "妮可",
                    "Billy", "ビリー", "比利",
                    "Nekomata", "ネコマタ", "猫宮",
                    "Ellen", "エレン", "艾莲",
                    "Lycaon", "ライカオン", "萊卡恩",
                    "Grace", "グレース", "格蕾丝",
                    "Anton", "アントン", "安东"
                ]
            },
            "vocaloid": {
                "characters": [
                    "Hatsune Miku", "初音ミク", "初音未來",
                    "Kagamine Rin", "鏡音リン", "鏡音鈴",
                    "Kagamine Len", "鏡音レン", "鏡音連",
                    "Megurine Luka", "巡音ルカ", "巡音流歌",
                    "KAITO", "カイト",
                    "MEIKO", "メイコ"
                ]
            },
            "other_popular": {
                "characters": [
                    "Komi Shouko", "古見硝子",
                    "Nezuko", "禰豆子",
                    "Tanjiro", "炭治郎",
                    "Zero Two", "ゼロツー", "02",
                    "Rem", "レム",
                    "Ram", "ラム",
                    "Emilia", "エミリア",
                    "Aqua", "アクア",
                    "Megumin", "めぐみん",
                    "Raphtalia", "ラフタリア",
                    "Asuka", "アスカ",
                    "Rei", "レイ",
                    "Shinji", "シンジ"
                ]
            }
        }
    
    def _load_creator_mapping(self) -> Dict:
        """Cargar mapeo de creadores → personajes"""
        if self.creator_mapping_path.exists():
            try:
                with open(self.creator_mapping_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando creator_mapping.json: {e}")
        
        # Mapeo inicial de creadores conocidos que interpretan personajes
        return {
            "creator_to_character": {
                # Ejemplos de creadores de TikTok que siempre hacen el mismo personaje
                "hutao_cosplayer": "Hu Tao",
                "raiden_official": "Raiden Shogun",
                "miku_dancer": "Hatsune Miku",
                # Se irá poblando automáticamente
            },
            "character_to_creators": {
                # Mapeo inverso para encontrar creadores de un personaje
                "Hu Tao": ["hutao_cosplayer", "hutao_main"],
                "Raiden Shogun": ["raiden_official", "ei_cosplay"],
                "Hatsune Miku": ["miku_dancer", "miku_official"]
            },
            "auto_detected": {
                # Creadores detectados automáticamente
            }
        }
    
    def _init_character_patterns(self) -> List[Dict]:
        """Inicializar patrones dinámicos para reconocimiento en títulos basados en la BD completa"""
        patterns = []
        
        # Generar patrones dinámicos para TODOS los personajes en la base de datos
        for game, game_data in self.character_db.items():
            for character in game_data['characters']:
                # Crear patrón básico para el nombre del personaje
                # Escapar caracteres especiales y manejar espacios
                escaped_char = re.escape(character)
                pattern = rf'\b{escaped_char}\b'
                
                patterns.append({
                    'pattern': pattern,
                    'character': character,
                    'game': game,
                    'source': 'database_exact'
                })
                
                # Si el personaje tiene espacios, crear también versión sin espacios
                if ' ' in character:
                    no_space_version = character.replace(' ', '')
                    escaped_no_space = re.escape(no_space_version)
                    patterns.append({
                        'pattern': rf'\b{escaped_no_space}\b',
                        'character': character,
                        'game': game,
                        'source': 'database_nospace'
                    })
            
            # Agregar patrones para aliases si existen
            if 'aliases' in game_data:
                for main_character, aliases in game_data['aliases'].items():
                    for alias in aliases:
                        escaped_alias = re.escape(alias)
                        patterns.append({
                            'pattern': rf'\b{escaped_alias}\b',
                            'character': main_character,
                            'game': game,
                            'source': 'database_alias'
                        })
        
        # Patrones genéricos MEJORADOS - Solo para casos específicos y validados
        generic_patterns = [
            # DESHABILITADOS los patrones genéricos problemáticos
            # Solo mantener patrones muy específicos que ya estén en la base de datos
            
            # Patrón para hashtags de personajes específicos (solo si están en BD)
            {
                'pattern': r'#([A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]+)*)\s*(?:cos|cosplay|コスプレ)',
                'character': 'extract_hashtag_verified_only', 
                'game': 'unknown',
                'source': 'verified_hashtag_cosplay'
            },
            # Patrón para títulos claros con nombres conocidos
            {
                'pattern': r'\b([A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]+)*)\s*-\s*\w+',  # "Personaje - algo"
                'character': 'extract_title_prefix_verified_only',
                'game': 'unknown',
                'source': 'verified_title_prefix'
            }
            
            # COMENTAMOS los patrones problemáticos:
            # {
            #     'pattern': r'(\w{3,})\s*(cosplay|コスプレ|cos)\b',  # DEMASIADO GENÉRICO
            #     'character': 'extract_name',
            #     'game': 'unknown',
            #     'source': 'generic_cosplay'
            # },
            # {
            #     'pattern': r'#(\w{3,})(cos|cosplay|コスプレ)',  # CAPTURA FRAGMENTOS
            #     'character': 'extract_hashtag', 
            #     'game': 'unknown',
            #     'source': 'generic_hashtag'
            # },
            # {
            #     'pattern': r'(\w{4,})\s*(dance|ダンス|댄스)\b',  # CAPTURA "forte", "MaMaMa"
            #     'character': 'extract_name',
            #     'game': 'unknown', 
            #     'source': 'generic_dance'
            # },
            # {
            #     'pattern': r'(\w{4,})\s*(MMD|mmd)\b',  # CAPTURA JUEGOS 
            #     'character': 'extract_name',
            #     'game': 'unknown',
            #     'source': 'generic_mmd'
            # }
        ]
        
        # Combinar patrones específicos + genéricos
        all_patterns = patterns + generic_patterns
        
        logger.info(f"Patrones generados: {len(patterns)} específicos + {len(generic_patterns)} genéricos = {len(all_patterns)} total")
        return all_patterns
    
    def analyze_video_title(self, title: str) -> List[Dict]:
        """Analizar título de video para extraer personajes usando patrones dinámicos mejorados"""
        detected_characters = []
        
        if not title:
            return detected_characters

        logger.info(f"Analizando título con {len(self.character_patterns)} patrones: {title}")
        
        # Lista de palabras a excluir (no son nombres de personajes) - EXPANDIDA
        excluded_words = {
            # Palabras comunes de videos
            'mmd', 'dance', 'cosplay', 'cos', 'shorts', 'tiktok', 'video', 'compilation', 
            'trending', 'viral', 'new', 'best', 'top', 'epic', 'amazing', 'cool', 'random',
            'showcase', 'multiple', 'characters', 'with', 'and', 'the', 'for', 'from', 'by',
            'made', 'using', 'model', 'models', 'animation', 'edit', 'edited', 'original',
            'official', 'fanmade', 'fan', 'creator', 'artist', 'studio', 'team',
            
            # Nombres de juegos/franquicias
            'genshin', 'honkai', 'impact', 'zenless', 'zone', 'zero', 'star', 'rail',
            'hsr', 'hi3', 'zzz', 'genshinimpact', 'honkaiimpact', 'honkaistarrail',
            'zenlesszonezero', 'wuthering', 'waves', 'wutheringwaves', 'vocaloid',
            'mihoyo', 'hoyoverse', 'cognosphere',
            
            # Hashtags problemáticos y fragmentos 
            'animegamey', 'animegameycosplay', 'anime', 'game', 'gaming', 'gamecos',
            'gamecharacter', 'gamecosplay', 'animecos', 'animecosplay', 'otaku',
            'weeb', 'kawaii', 'manga', 'manhwa', 'manhua',
            
            # Palabras de baile/música comunes
            'forte', 'mamama', 'batte', 'dance', 'song', 'music', 'beat', 'rhythm',
            'choreo', 'choreography', 'cover', 'remix', 'version', 'ver', 'mv',
            'pv', 'theme', 'opening', 'ending', 'ost', 'bgm',
            
            # Términos técnicos
            'fps', '60fps', '4k', 'hd', 'uhd', 'quality', 'high', 'low', 'medium',
            'render', 'rendered', 'motion', 'capture', 'mocap', 'effect', 'effects',
            'shader', 'lighting', 'camera', 'angle', 'view',
            
            # Palabras de redes sociales
            'follow', 'like', 'subscribe', 'share', 'comment', 'hashtag', 'tag',
            'trending', 'fyp', 'foryou', 'foryoupage', 'viral', 'explore',
            
            # Términos generales adicionales
            'shogun', 'archon', 'element', 'electro', 'pyro', 'hydro', 'cryo', 'geo', 'anemo', 'dendro',
            'physical', 'quantum', 'ice', 'fire', 'wind', 'earth', 'water', 'lightning',
            'sword', 'bow', 'catalyst', 'claymore', 'polearm', 'weapon', 'weapons'
        }
        
        # Buscar patrones conocidos
        raw_detections = []
        for pattern_info in self.character_patterns:
            try:
                matches = re.finditer(pattern_info['pattern'], title, re.IGNORECASE)
                
                for match in matches:
                    character_name = None
                    game = pattern_info.get('game', 'unknown')
                    source_type = pattern_info.get('source', 'unknown')
                    
                    # Manejar diferentes tipos de patrones
                    if pattern_info['character'] == 'extract_name':
                        # Extraer nombre antes de palabras como "cosplay", "dance", "MMD"
                        character_name = match.group(1).strip()
                        
                        # Filtrar palabras excluidas
                        if character_name.lower() in excluded_words:
                            continue
                        
                        # Verificar si el nombre extraído está en nuestra base de datos
                        verified_character = self._verify_character_name(character_name)
                        if verified_character:
                            character_name = verified_character['name']
                            game = verified_character['game']
                            source_type = f"generic_verified_{source_type}"
                        else:
                            # Filtrar nombres cortos no verificados para reducir ruido
                            if len(character_name) < 4:
                                continue
                            source_type = f"generic_unverified_{source_type}"
                            
                    elif pattern_info['character'] == 'extract_hashtag':
                        # Extraer hashtag sin #
                        character_name = match.group(1).strip()
                        
                        # Filtrar palabras excluidas
                        if character_name.lower() in excluded_words:
                            continue
                        
                        # Verificar si el hashtag corresponde a un personaje conocido
                        verified_character = self._verify_character_name(character_name)
                        if verified_character:
                            character_name = verified_character['name']
                            game = verified_character['game']
                            source_type = f"hashtag_verified_{source_type}"
                        else:
                            # Solo aceptar hashtags largos no verificados
                            if len(character_name) < 5:
                                continue
                            source_type = f"hashtag_unverified_{source_type}"
                    
                    elif pattern_info['character'] == 'extract_hashtag_verified_only':
                        # NUEVO: Solo aceptar si está verificado en BD
                        character_name = match.group(1).strip()
                        
                        # Filtrar palabras excluidas
                        if character_name.lower() in excluded_words:
                            continue
                        
                        # OBLIGATORIO: Debe estar en la base de datos
                        verified_character = self._verify_character_name(character_name)
                        if verified_character:
                            character_name = verified_character['name']
                            game = verified_character['game']
                            source_type = f"hashtag_verified_strict_{source_type}"
                        else:
                            # Si no está verificado, rechazarlo completamente
                            continue
                    
                    elif pattern_info['character'] == 'extract_title_prefix_verified_only':
                        # NUEVO: Solo extraer prefijos de título si están verificados
                        character_name = match.group(1).strip()
                        
                        # Filtrar palabras excluidas
                        if character_name.lower() in excluded_words:
                            continue
                        
                        # OBLIGATORIO: Debe estar en la base de datos
                        verified_character = self._verify_character_name(character_name)
                        if verified_character:
                            character_name = verified_character['name']
                            game = verified_character['game'] 
                            source_type = f"title_verified_strict_{source_type}"
                        else:
                            # Si no está verificado, rechazarlo completamente
                            continue
                            
                    else:
                        # Patrón específico de la base de datos - ya está verificado
                        character_name = pattern_info['character']
                        
                        # Verificar que no esté en palabras excluidas
                        if character_name.lower() in excluded_words:
                            continue
                    
                    # Si tenemos un personaje válido, agregarlo
                    if character_name:
                        # Determinar nivel de confianza basado en el tipo de fuente
                        if source_type.startswith('database_'):
                            confidence = 0.9  # Alta confianza para matches directos de BD
                        elif 'verified' in source_type:
                            confidence = 0.8  # Buena confianza para extracciones verificadas
                        else:
                            confidence = 0.6  # Menor confianza para extracciones no verificadas
                        
                        raw_detections.append({
                            'name': character_name,
                            'game': game,
                            'confidence': confidence,
                            'source': source_type,
                            'match_text': match.group(0)
                        })
                
            except re.error as e:
                logger.warning(f"Error en patrón regex: {pattern_info['pattern']} - {e}")
                continue
            except Exception as e:
                logger.warning(f"Error procesando patrón: {e}")
                continue
        
        # DEDUPLICACIÓN MEJORADA: Priorizar detecciones de mayor confianza
        unique_characters = {}
        for detection in raw_detections:
            # Normalizar nombre para comparación (ignorar case y espacios)
            normalized_name = detection['name'].lower().strip().replace(' ', '')
            
            # Si no existe o la nueva detección tiene mayor confianza, usar la nueva
            if (normalized_name not in unique_characters or 
                detection['confidence'] > unique_characters[normalized_name]['confidence']):
                
                unique_characters[normalized_name] = detection
                logger.info(f"Personaje detectado: {detection['name']} ({detection['game']}) via {detection['source']}")
            else:
                logger.debug(f"Duplicado ignorado: {detection['name']} (menor confianza)")
        
        # Convertir de vuelta a lista
        detected_characters = list(unique_characters.values())
        
        # Ordenar por confianza (mayor primero)
        detected_characters.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"Análisis completado: {len(detected_characters)} personajes únicos detectados")
        return detected_characters
    
    def analyze_creator_name(self, creator_name: str) -> Optional[Dict]:
        """Analizar nombre del creador para mapear a personaje"""
        if not creator_name:
            return None
        
        # Buscar en mapeo directo
        if creator_name in self.creator_mapping['creator_to_character']:
            character_name = self.creator_mapping['creator_to_character'][creator_name]
            return {
                'name': character_name,
                'confidence': 0.9,
                'source': 'creator_mapping',
                'creator': creator_name
            }
        
        # Buscar patrones en el nombre del creador
        creator_lower = creator_name.lower()
        
        # Verificar si el nombre del creador contiene nombre de personaje
        for game, game_data in self.character_db.items():
            for character in game_data['characters']:
                if character.lower() in creator_lower:
                    # Auto-registrar este mapeo para el futuro
                    self._auto_register_creator_mapping(creator_name, character, game)
                    
                    return {
                        'name': character,
                        'game': game,
                        'confidence': 0.7,
                        'source': 'creator_name_analysis',
                        'creator': creator_name
                    }
        
        return None
    
    def _verify_character_name(self, name: str) -> Optional[Dict]:
        """Verificar si un nombre corresponde a un personaje conocido"""
        name_lower = name.lower().strip()
        
        for game, game_data in self.character_db.items():
            # Buscar en lista principal
            for character in game_data['characters']:
                if character.lower() == name_lower:
                    return {'name': character, 'game': game}
            
            # Buscar en alias si existen
            if 'aliases' in game_data:
                for main_name, aliases in game_data['aliases'].items():
                    if name_lower in [alias.lower() for alias in aliases]:
                        return {'name': main_name, 'game': game}
        
        return None
    
    def _auto_register_creator_mapping(self, creator: str, character: str, game: str):
        """Auto-registrar un mapeo creador → personaje detectado"""
        try:
            # Agregar al mapeo
            self.creator_mapping['creator_to_character'][creator] = character
            
            # Agregar al mapeo inverso
            if character not in self.creator_mapping['character_to_creators']:
                self.creator_mapping['character_to_creators'][character] = []
            if creator not in self.creator_mapping['character_to_creators'][character]:
                self.creator_mapping['character_to_creators'][character].append(creator)
            
            # Marcar como auto-detectado
            self.creator_mapping['auto_detected'][creator] = {
                'character': character,
                'game': game,
                'detected_at': time.time(),
                'confidence': 0.7
            }
            
            # Guardar cambios
            self._save_creator_mapping()
            
            logger.info(f"Auto-registrado mapeo: {creator} → {character} ({game})")
            
        except Exception as e:
            logger.error(f"Error auto-registrando mapeo {creator} → {character}: {e}")
    
    def get_character_suggestions(self, video_data: Dict) -> List[Dict]:
        """Obtener sugerencias de personajes para un video"""
        suggestions = []
        
        # Analizar título
        if video_data.get('title'):
            title_suggestions = self.analyze_video_title(video_data['title'])
            suggestions.extend(title_suggestions)
        
        # Analizar creador
        if video_data.get('creator_name'):
            creator_suggestion = self.analyze_creator_name(video_data['creator_name'])
            if creator_suggestion:
                suggestions.append(creator_suggestion)
        
        # Eliminar duplicados manteniendo la mayor confianza
        unique_suggestions = {}
        for suggestion in suggestions:
            name = suggestion['name']
            if name not in unique_suggestions or suggestion['confidence'] > unique_suggestions[name]['confidence']:
                unique_suggestions[name] = suggestion
        
        return list(unique_suggestions.values())
    
    def download_character_reference_image(self, character_name: str, game: str = None) -> Optional[Path]:
        """Descargar imagen de referencia para un personaje"""
        try:
            # Crear directorio para el juego si no existe
            if game and game in self.character_db:
                game_dir = self.known_faces_path / game.replace('_', ' ').title()
            else:
                game_dir = self.known_faces_path / 'Auto_Downloaded'
            
            game_dir.mkdir(parents=True, exist_ok=True)
            
            # Buscar imagen usando múltiples términos de búsqueda
            search_terms = [
                f"{character_name} cosplay",
                f"{character_name} character art",
                f"{character_name} anime"
            ]
            
            for search_term in search_terms:
                image_path = self._download_image_from_search(search_term, game_dir, character_name)
                if image_path:
                    logger.info(f"Imagen descargada para {character_name}: {image_path}")
                    return image_path
            
            logger.warning(f"No se pudo descargar imagen para {character_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error descargando imagen para {character_name}: {e}")
            return None
    
    def _download_image_from_search(self, search_term: str, save_dir: Path, character_name: str) -> Optional[Path]:
        """Descargar imagen usando API de búsqueda (placeholder - implementar con API real)"""
        # NOTA: Esta es una implementación básica
        # En producción, usar APIs como:
        # - Bing Image Search API
        # - Google Custom Search API
        # - Unsplash API
        # - O scraping cuidadoso de sitios apropiados
        
        try:
            # Simulación de descarga (reemplazar con API real)
            logger.info(f"Simulando descarga de '{search_term}' para {character_name}")
            
            # Aquí iría la lógica real de descarga
            # Por ahora, solo crear un archivo placeholder
            image_path = save_dir / f"{character_name}.jpg"
            
            # En implementación real:
            # 1. Hacer request a API de búsqueda de imágenes
            # 2. Filtrar resultados apropiados
            # 3. Descargar imagen de mayor calidad
            # 4. Validar que es una imagen válida
            # 5. Guardar en el directorio correcto
            
            return None  # Por ahora retornar None hasta implementar API real
            
        except Exception as e:
            logger.error(f"Error en descarga simulada: {e}")
            return None
    
    def add_custom_character(self, character_name: str, game: str, aliases: List[str] = None) -> bool:
        """Agregar un personaje personalizado a la base de datos"""
        try:
            if game not in self.character_db:
                self.character_db[game] = {'characters': [], 'aliases': {}}
            
            # Agregar personaje si no existe
            if character_name not in self.character_db[game]['characters']:
                self.character_db[game]['characters'].append(character_name)
            
            # Agregar aliases si se proporcionan
            if aliases:
                if 'aliases' not in self.character_db[game]:
                    self.character_db[game]['aliases'] = {}
                self.character_db[game]['aliases'][character_name] = aliases
            
            # Guardar cambios
            self._save_character_database()
            
            logger.info(f"Personaje personalizado agregado: {character_name} ({game})")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando personaje personalizado {character_name}: {e}")
            return False
    
    def _save_character_database(self):
        """Guardar base de datos de personajes"""
        try:
            with open(self.character_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.character_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando character_database.json: {e}")
    
    def _save_creator_mapping(self):
        """Guardar mapeo de creadores"""
        try:
            with open(self.creator_mapping_path, 'w', encoding='utf-8') as f:
                json.dump(self.creator_mapping, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando creator_mapping.json: {e}")
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del sistema de inteligencia de personajes"""
        total_characters = sum(len(game_data['characters']) for game_data in self.character_db.values())
        total_mappings = len(self.creator_mapping['creator_to_character'])
        auto_detected = len(self.creator_mapping.get('auto_detected', {}))
        
        return {
            'total_characters': total_characters,
            'total_games': len(self.character_db),
            'creator_mappings': total_mappings,
            'auto_detected_mappings': auto_detected,
            'database_file': str(self.character_db_path),
            'mapping_file': str(self.creator_mapping_path)
        }

# Instancia global
character_intelligence = CharacterIntelligence()
