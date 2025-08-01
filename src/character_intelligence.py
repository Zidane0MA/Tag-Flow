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

# Importar detector optimizado
try:
    from .optimized_detector import OptimizedCharacterDetector
    OPTIMIZED_DETECTOR_AVAILABLE = True
except ImportError:
    OPTIMIZED_DETECTOR_AVAILABLE = False

logger = logging.getLogger(__name__)

# Instancia global para evitar múltiples inicializaciones
_character_intelligence_instance = None

class CharacterIntelligence:
    """Sistema inteligente para reconocimiento automático de personajes"""
    
    def __new__(cls):
        global _character_intelligence_instance
        if _character_intelligence_instance is None:
            _character_intelligence_instance = super().__new__(cls)
        return _character_intelligence_instance
    
    def __init__(self):
        # Evitar reinicialización si ya se ha inicializado
        if hasattr(self, '_initialized'):
            return
        
        self.character_db_path = config.DATA_DIR / 'character_database.json'
        self.known_faces_path = config.KNOWN_FACES_PATH
        
        # Cargar base de datos unificada
        self.character_db = self._load_character_database()
        self.creator_mapping = self._extract_creator_mapping_from_db()
        
        # Patrones para extracción de nombres de títulos (legacy)
        self.character_patterns = self._init_character_patterns()
        
        # NUEVO: Inicializar detector optimizado si está disponible
        self.optimized_detector = None
        if OPTIMIZED_DETECTOR_AVAILABLE:
            try:
                self.optimized_detector = OptimizedCharacterDetector(self.character_db)
                logger.info("Detector optimizado inicializado exitosamente")
            except Exception as e:
                logger.warning(f"Error inicializando detector optimizado: {e}")
                logger.info("Usando detector legacy como fallback")
        else:
            logger.info("Detector optimizado no disponible, usando detector legacy")
        
        logger.info("Character Intelligence inicializado")
        self._initialized = True
    
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
    
    def _extract_creator_mapping_from_db(self) -> Dict:
        """Extraer mapeo de creadores desde la base de datos unificada"""
        creator_mapping = {
            "creator_to_character": {},
            "character_to_creators": {},
            "auto_detected": {}
        }
        
        # Buscar mapeo_creador en la base de datos
        if 'mapeo_creador' in self.character_db:
            tiktoker_data = self.character_db['mapeo_creador']
            
            if isinstance(tiktoker_data.get('characters'), dict):
                # Nueva estructura
                for char_name, char_info in tiktoker_data['characters'].items():
                    # Buscar mapeo automático de creador
                    auto_creator = char_info.get('auto_detect_for_creator')
                    if auto_creator:
                        creator_mapping["creator_to_character"][auto_creator] = char_name
                        
                        # Mapeo inverso
                        if char_name not in creator_mapping["character_to_creators"]:
                            creator_mapping["character_to_creators"][char_name] = []
                        creator_mapping["character_to_creators"][char_name].append(auto_creator)
                        
                        # Marcar como auto-detectado
                        creator_mapping["auto_detected"][auto_creator] = {
                            "character": char_name,
                            "confidence": char_info.get('confidence', 0.9),
                            "platform": char_info.get('platform_specific', 'tiktok')
                        }
        
        return creator_mapping

    def _get_characters_compatible(self, game_data):
        """Wrapper para manejar ambas estructuras (nueva y antigua)"""
        if isinstance(game_data.get('characters'), dict):
            return list(game_data['characters'].keys())  # Nueva estructura
        elif isinstance(game_data.get('characters'), list):
            return game_data['characters']  # Estructura antigua
        else:
            return []

    def _get_aliases_compatible(self, game_data):
        """Wrapper para aliases/variants en ambas estructuras"""
        if isinstance(game_data.get('characters'), dict):
            # Nueva estructura: extraer de variants
            aliases = {}
            for canonical_name, char_data in game_data['characters'].items():
                variants = char_data.get('variants', {})
                all_variants = []
                for variant_type, variant_list in variants.items():
                    all_variants.extend(variant_list)
                # Filtrar el nombre canónico para evitar duplicados
                all_variants = [v for v in all_variants if v != canonical_name]
                if all_variants:
                    aliases[canonical_name] = all_variants
            return aliases
        elif 'aliases' in game_data:
            return game_data['aliases']  # Estructura antigua
        else:
            return {}

    def _init_character_patterns(self) -> List[Dict]:
        """ACTUALIZADO: Inicializar patrones dinámicos usando wrappers de compatibilidad"""
        patterns = []
        
        # Generar patrones dinámicos para TODOS los personajes en la base de datos
        for game, game_data in self.character_db.items():
            # CAMBIO CRÍTICO: Usar wrappers de compatibilidad
            characters = self._get_characters_compatible(game_data)
            aliases = self._get_aliases_compatible(game_data)
            
            for character in characters:
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
            
            # ACTUALIZADO: Agregar patrones para aliases usando wrapper de compatibilidad
            for main_character, alias_list in aliases.items():
                for alias in alias_list:
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
        """HÍBRIDO: Usar detector optimizado si disponible, fallback a legacy"""
        
        if not title:
            return []
        
        # Usar detector optimizado si está disponible
        if self.optimized_detector:
            try:
                logger.info(f"Usando detector optimizado para título: {title}")
                return self.optimized_detector.detect_in_title(title)
            except Exception as e:
                logger.error(f"Error en detector optimizado: {e}")
                logger.info("Fallback a detector legacy")
        
        # Fallback a detector legacy
        logger.info(f"Usando detector legacy para título: {title}")
        return self._analyze_video_title_legacy(title)
    
    def _analyze_video_title_legacy(self, title: str) -> List[Dict]:
        """Detector legacy para compatibilidad y fallback"""
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
        
        # 🆕 FILTRAR MENCIONES DE CUENTAS (@usuario) ANTES DE BUSCAR PATRONES
        # Esto evita falsos positivos como "@Kaiser" → "Michael Kaiser"
        title_normalized = re.sub(r'@\w+', ' ', title)
        title_normalized = re.sub(r'\s+', ' ', title_normalized.strip())
        
        logger.info(f"Título normalizado (sin menciones @): {title_normalized}")
        
        # Buscar patrones conocidos en el título normalizado (sin menciones @)
        raw_detections = []
        for pattern_info in self.character_patterns:
            try:
                matches = re.finditer(pattern_info['pattern'], title_normalized, re.IGNORECASE)
                
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
        """Analizar nombre del creador para mapear a personaje - VERSION CONSERVADORA"""
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
        
        # NUEVO: Verificar si es un TikToker con persona propia
        if 'mapeo_creador' in self.creator_mapping:
            if creator_name in self.creator_mapping['mapeo_creador']:
                tiktoker_info = self.creator_mapping['mapeo_creador'][creator_name]
                if tiktoker_info.get('auto_detect', False):
                    return {
                        'name': tiktoker_info['persona_name'],
                        'game': tiktoker_info['game'],
                        'confidence': tiktoker_info.get('confidence', 0.9),
                        'source': 'tiktoker_persona',
                        'creator': creator_name
                    }
        
        # 🚫 DESHABILITAR MAPEO AUTOMATICO AGRESIVO
        # Este código estaba causando falsos positivos como Tenshimaru-san → Aru
        # Comentamos esta sección para evitar mapeos incorrectos automáticos
        
        # Buscar patrones en el nombre del creador - SOLO SI ES MUY ESPECÍFICO
        # creator_lower = creator_name.lower()
        # 
        # # Verificar si el nombre del creador contiene nombre de personaje
        # for game, game_data in self.character_db.items():
        #     characters = self._get_characters_compatible(game_data)
        #     for character in characters:
        #         if character.lower() in creator_lower:
        #             # Auto-registrar este mapeo para el futuro
        #             self._auto_register_creator_mapping(creator_name, character, game)
        #             
        #             return {
        #                 'name': character,
        #                 'game': game,
        #                 'confidence': 0.7,
        #                 'source': 'creator_name_analysis',
        #                 'creator': creator_name
        #             }
        
        # NO HACER MAPEO AUTOMÁTICO - Solo retornar mapeos explícitos
        logger.debug(f"No se encontró mapeo explícito para creador: {creator_name}")
        return None
    
    def _normalize_character_name(self, name: str) -> str:
        """Normalizar nombre de personaje para mejor matching"""
        import re
        
        # Remover espacios extra
        name = re.sub(r'\s+', ' ', name.strip())
        
        # NUEVA FUNCIONALIDAD: Remover espacios en caracteres CJK (Chino, Japonés, Coreano)
        # "胡 桃" -> "胡桃", "八 重 神 子" -> "八重神子"
        name = re.sub(r'(?<=[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af])\s+(?=[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af])', '', name)
        
        return name
    
    def _verify_character_name(self, name: str) -> Optional[Dict]:
        """Verificar si un nombre corresponde a un personaje conocido"""
        # Normalizar nombre de entrada
        normalized_name = self._normalize_character_name(name)
        name_lower = normalized_name.lower().strip()
        
        for game, game_data in self.character_db.items():
            # ARREGLADO: Usar wrapper de compatibilidad para lista principal
            characters = self._get_characters_compatible(game_data)
            for character in characters:
                normalized_character = self._normalize_character_name(character)
                if normalized_character.lower() == name_lower:
                    return {'name': character, 'game': game}
            
            # Buscar en alias si existen (con normalización)
            if 'aliases' in game_data:
                for main_name, aliases in game_data['aliases'].items():
                    normalized_main = self._normalize_character_name(main_name)
                    if normalized_main.lower() == name_lower:
                        return {'name': main_name, 'game': game}
                    
                    # Verificar aliases normalizados
                    for alias in aliases:
                        normalized_alias = self._normalize_character_name(alias)
                        if normalized_alias.lower() == name_lower:
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
    
    def _generate_context_hints(self, game: str, character_name: str) -> List[str]:
        """Generar context_hints automáticamente basándose en el juego y personaje"""
        hints = []
        
        # Context hints por juego/franquicia
        game_hints = {
            'genshin_impact': ['genshin', 'impact', 'mihoyo', 'hoyoverse', 'teyvat'],
            'honkai_impact': ['honkai', 'impact', 'hi3', 'mihoyo', 'hoyoverse'],
            'honkai_star_rail': ['honkai', 'star', 'rail', 'hsr', 'mihoyo', 'hoyoverse'],
            'zenless_zone_zero': ['zenless', 'zone', 'zero', 'zzz', 'mihoyo', 'hoyoverse'],
            'wuthering_waves': ['wuthering', 'waves', 'kuro', 'games'],
            'blue_archive': ['blue', 'archive', 'ba', 'nexon'],
            'vocaloid': ['vocaloid', 'miku', 'virtual', 'singer', 'crypton'],
            'other_popular': ['anime', 'manga', 'character'],
            'mapeo_creador': ['cosplay', 'tiktok', 'dance', 'cos', 'tiktoker']
        }
        
        # Agregar hints específicos del juego
        if game in game_hints:
            hints.extend(game_hints[game])
        
        # Context hints adicionales basados en el nombre del personaje
        character_lower = character_name.lower()
        
        # Detectar elementos/tipos comunes en nombres
        element_hints = {
            'hydro': ['hydro', 'water', 'blue'],
            'pyro': ['pyro', 'fire', 'red'],
            'electro': ['electro', 'lightning', 'purple'],
            'anemo': ['anemo', 'wind', 'green'],
            'geo': ['geo', 'earth', 'yellow'],
            'cryo': ['cryo', 'ice', 'light blue'],
            'dendro': ['dendro', 'nature', 'green'],
            'archon': ['archon', 'god', 'ruler'],
            'shogun': ['shogun', 'general', 'leader'],
            'miko': ['miko', 'shrine', 'priestess'],
            'dancer': ['dance', 'performer', 'artist'],
            'cosplay': ['cosplay', 'costume', 'performance']
        }
        
        for element, element_hints_list in element_hints.items():
            if element in character_lower:
                hints.extend(element_hints_list)
        
        # Context hints para TikTokers
        if game == 'mapeo_creador' or 'cos' in character_lower:
            hints.extend(['cosplay', 'cosplayer', 'costume', 'performance', 'creator'])
        
        # Hints generales para personajes de anime/gaming
        if game in ['genshin_impact', 'honkai_impact', 'honkai_star_rail', 'zenless_zone_zero']:
            hints.extend(['mmd', 'dance', 'character'])
        
        # Remover duplicados y retornar
        return list(set(hints))
    
    def add_custom_character(self, character_name: str, game: str, aliases: List[str] = None) -> bool:
        """Agregar un personaje personalizado a la base de datos con estructura jerárquica optimizada"""
        try:
            # Inicializar juego si no existe con estructura jerárquica
            if game not in self.character_db:
                self.character_db[game] = {
                    'characters': {}  # Nueva estructura jerárquica
                }
            
            # Asegurar que el juego tiene la estructura jerárquica
            game_data = self.character_db[game]
            if not isinstance(game_data.get('characters'), dict):
                # Migrar de estructura legacy a jerárquica si es necesario
                legacy_chars = game_data.get('characters', [])
                legacy_aliases = game_data.get('aliases', {})
                
                # Convertir a estructura jerárquica
                game_data['characters'] = {}
                for char in legacy_chars:
                    game_data['characters'][char] = {
                        'canonical_name': char,
                        'priority': 1,
                        'variants': {
                            'exact': [char],
                            'common': [char]
                        },
                        'detection_weight': 0.85
                    }
                    
                    # Agregar aliases de la estructura legacy
                    if char in legacy_aliases:
                        char_aliases = legacy_aliases[char]
                        game_data['characters'][char]['variants']['exact'].extend(char_aliases)
                
                # Limpiar estructura legacy
                if 'aliases' in game_data:
                    del game_data['aliases']
            
            # Agregar personaje con estructura jerárquica optimizada
            if character_name not in game_data['characters']:
                # Generar context_hints automáticamente basándose en el juego
                context_hints = self._generate_context_hints(game, character_name)
                
                # Crear entrada jerárquica completa
                character_entry = {
                    'canonical_name': character_name,
                    'priority': 1,  # Prioridad alta para personajes agregados manualmente
                    'variants': {
                        'exact': [character_name],  # Solo el nombre canónico en exact
                        'common': [character_name]  # También en common para flexibilidad
                    },
                    'detection_weight': 0.95,  # Alta confianza para personajes agregados manualmente
                    'context_hints': context_hints,
                    'manually_added': True,  # Marcar como agregado manualmente
                    'added_timestamp': time.time()
                }
                
                # Agregar variantes automáticas
                if ' ' in character_name:
                    # Versión sin espacios
                    no_space_version = character_name.replace(' ', '')
                    character_entry['variants']['joined'] = [no_space_version]
                
                # Agregar aliases personalizados si se proporcionan - MEJORADO
                if aliases:
                    for alias in aliases:
                        # Categorizar alias de forma más inteligente
                        if len(alias) <= 3:
                            # Aliases muy cortos van a abbreviations
                            if 'abbreviations' not in character_entry['variants']:
                                character_entry['variants']['abbreviations'] = []
                            character_entry['variants']['abbreviations'].append(alias)
                        elif alias == character_name:
                            # Skip si es igual al nombre canónico (ya está en exact)
                            continue
                        else:
                            # CORREGIDO: Aliases van a "common" en lugar de "exact"
                            character_entry['variants']['common'].append(alias)
                
                # Agregar al juego
                game_data['characters'][character_name] = character_entry
                
                # Regenerar patrones en el detector optimizado si existe
                if self.optimized_detector:
                    try:
                        self.optimized_detector.reload_patterns(self.character_db)
                        logger.info("Patrones del detector optimizado actualizados")
                    except Exception as e:
                        logger.warning(f"Error recargando patrones optimizados: {e}")
                
                # Actualizar patrones legacy para compatibilidad
                self.character_patterns = self._init_character_patterns()
                
                logger.info(f"Personaje agregado con estructura jerárquica: {character_name} ({game})")
                logger.info(f"Context hints generados: {context_hints}")
                logger.info(f"Variantes generadas: {character_entry['variants']}")
            else:
                # Personaje ya existe, actualizar aliases y context_hints si se proporcionan
                existing_character = game_data['characters'][character_name]
                
                if aliases:
                    for alias in aliases:
                        # Agregar a common si no existe (CORREGIDO)
                        if 'common' not in existing_character['variants']:
                            existing_character['variants']['common'] = [character_name]
                        
                        if alias not in existing_character['variants']['common'] and alias != character_name:
                            if len(alias) <= 3:
                                # Alias corto va a abbreviations
                                if 'abbreviations' not in existing_character['variants']:
                                    existing_character['variants']['abbreviations'] = []
                                if alias not in existing_character['variants']['abbreviations']:
                                    existing_character['variants']['abbreviations'].append(alias)
                            else:
                                # CORREGIDO: Alias normal va a common
                                existing_character['variants']['common'].append(alias)
                
                # Actualizar context_hints si no existen o están vacíos
                if not existing_character.get('context_hints'):
                    existing_character['context_hints'] = self._generate_context_hints(game, character_name)
                    logger.info(f"Context hints actualizados: {existing_character['context_hints']}")
                
                logger.info(f"Personaje existente actualizado: {character_name}")
                logger.info(f"Variantes actualizadas: {existing_character['variants']}")
            
            # Guardar cambios
            self._save_character_database()
            
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
        """Guardar mapeo de creadores en la base de datos unificada"""
        try:
            # Los mapeos ahora se guardan integrados en character_database.json
            # No necesitamos archivo separado
            self._save_character_database()
            logger.info("Mapeos de creadores guardados en character_database.json")
        except Exception as e:
            logger.error(f"Error guardando creator_mapping.json: {e}")
    
    def get_stats(self) -> Dict:
        """ACTUALIZADO: Obtener estadísticas del sistema usando wrappers de compatibilidad"""
        total_characters = 0
        
        # Usar wrapper de compatibilidad para contar personajes
        for game_data in self.character_db.values():
            characters = self._get_characters_compatible(game_data)
            total_characters += len(characters)
        
        total_mappings = len(self.creator_mapping['creator_to_character'])
        auto_detected = len(self.creator_mapping.get('auto_detected', {}))
        
        stats = {
            'total_characters': total_characters,
            'total_games': len(self.character_db),
            'creator_mappings': total_mappings,
            'auto_detected_mappings': auto_detected,
            'database_file': str(self.character_db_path),
            'mapping_file': 'Integrado en character_database.json',  # Ya no existe archivo separado
            'detector_type': 'optimized' if self.optimized_detector else 'legacy'
        }
        
        # Agregar estadísticas del detector optimizado si está disponible
        if self.optimized_detector:
            performance_stats = self.optimized_detector.get_performance_stats()
            stats.update({
                'optimized_patterns': performance_stats['total_patterns'],
                'cache_hit_rate': performance_stats['cache_hit_rate'],
                'avg_detection_time_ms': performance_stats['avg_detection_time_ms'],
                'pattern_distribution': performance_stats['pattern_distribution']
            })
        
        return stats
    
    def get_performance_report(self) -> Dict:
        """Obtener reporte detallado de rendimiento"""
        if not self.optimized_detector:
            return {"error": "Detector optimizado no disponible"}
        
        return self.optimized_detector.get_performance_stats()
    
    def clear_detection_cache(self):
        """Limpiar cache de detección si existe"""
        if self.optimized_detector:
            self.optimized_detector.clear_cache()
            logger.info("Cache del detector optimizado limpiado")
        else:
            logger.info("No hay cache que limpiar (detector legacy)")
    
    # 🚀 MIGRADO: Procesamiento avanzado de hashtags de optimized_detector.py
    
    def extract_hashtag_content_advanced(self, title: str) -> str:
        """
        🚀 OPTIMIZADO: Extracción inteligente de contenido de hashtags
        
        Funcionalidades:
        - Separación de palabras camelCase: "EvelynChevalier" → "Evelyn Chevalier"
        - Separación avanzada: "HuTaodance" → "HuTao dance"
        - Detección de sufijos comunes (dance, cosplay, mmd, etc.)
        - Filtrado de menciones (@usuario)
        
        Args:
            title: Título con hashtags a procesar
            
        Returns:
            Título procesado con hashtags expandidos
        """
        import re
        
        def extract_hashtag_content(match):
            hashtag = match.group(0)
            content = hashtag[1:]  # Quitar el #
            
            # Agregar el contenido original
            result = f" {content} "
            
            # Separar palabras camelCase (EvelynChevalier -> Evelyn Chevalier)
            if any(c.isupper() for c in content[1:]):  # Skip first char
                camel_separated = re.sub(r'([a-z])([A-Z])', r'\1 \2', content)
                result += f" {camel_separated} "
            
            # 🆕 Separar palabras si hay transiciones lowercase->uppercase seguidas de lowercase
            # Esto maneja casos como "HuTaodance" -> "HuTao dance"
            # Buscar patrones como "TaoD" donde la D inicia una nueva palabra
            advanced_separated = re.sub(r'([A-Z][a-z]+)([A-Z][a-z])', r'\1 \2', content)
            if advanced_separated != content:
                result += f" {advanced_separated} "
            
            # 🆕 Intentar separar por palabras comunes al final
            common_suffixes = ['dance', 'cosplay', 'mmd', 'edit', 'video', 'tiktok', 'short']
            for suffix in common_suffixes:
                if content.lower().endswith(suffix.lower()) and len(content) > len(suffix):
                    base = content[:-len(suffix)]
                    result += f" {base} {suffix} "
                    # También separar camelCase en la base
                    if any(c.isupper() for c in base[1:]):
                        base_separated = re.sub(r'([a-z])([A-Z])', r'\1 \2', base)
                        result += f" {base_separated} {suffix} "
                    break
            
            return result
        
        # Extraer hashtags con lógica mejorada
        normalized = re.sub(r'#\w+', extract_hashtag_content, title, flags=re.IGNORECASE)
        
        # Remover otros marcadores de video
        video_markers = [
            r'\[.*?\]',  # [4K], [MMD], [60FPS]
            r'【.*?】',   # 【Genshin Impact MMD】
            r'^\d+\.',   # 501., 502. (numeración)
        ]
        
        for pattern in video_markers:
            normalized = re.sub(pattern, ' ', normalized, flags=re.IGNORECASE)
        
        # 🆕 FILTRAR MENCIONES DE CUENTAS (@usuario) para evitar falsos positivos
        normalized = re.sub(r'@\w+', ' ', normalized)
        
        # Limpiar conectores
        connectors = [' - ', ' x ', ' & ', ' and ', ' with ', ' feat ', ' ft ']
        for connector in connectors:
            normalized = normalized.replace(connector, ' ')
        
        # Normalizar espacios múltiples
        normalized = re.sub(r'\\s+', ' ', normalized.strip())
        
        return normalized
    
    def preprocess_title_for_detection(self, title: str) -> str:
        """
        🚀 OPTIMIZADO: Preprocesamiento completo de título para detección
        
        Combina todas las optimizaciones de normalización de texto
        
        Args:
            title: Título original
            
        Returns:
            Título optimizado para detección de personajes
        """
        if not title:
            return ""
        
        # Aplicar procesamiento avanzado de hashtags
        processed = self.extract_hashtag_content_advanced(title)
        
        # Normalización adicional para mejorar detección
        processed = processed.lower().strip()
        
        return processed

# ⚠️ DEPRECATED: Instancia global removida para eliminar dependencias circulares
# Usar ServiceFactory.get_service('character_intelligence') o get_character_intelligence() desde service_factory
