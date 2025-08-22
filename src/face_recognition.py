"""
Tag-Flow V2 - Reconocimiento Facial Mejorado
Híbrido: Google Vision API (famosos) + DeepFace GPU (personajes anime/gaming)
+ Inteligencia de Personajes (títulos + creadores)
"""

import os
import json
from typing import Dict, List, Optional
import logging
from pathlib import Path
import numpy as np
from PIL import Image
import io
from config import config

# Importar el nuevo sistema de inteligencia a través del service factory
from .service_factory import get_character_intelligence

# Configurar logger primero
logger = logging.getLogger(__name__)

# Google Vision API
try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    logger.warning("Google Vision API no disponible")

# DeepFace (local)
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    logger.warning("DeepFace no disponible")

class FaceRecognizer:
    """Reconocedor facial híbrido para TikTokers y personajes de anime/gaming"""
    
    def __init__(self):
        # Google Vision API
        self.vision_client = None
        if GOOGLE_VISION_AVAILABLE and config.GOOGLE_APPLICATION_CREDENTIALS:
            try:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GOOGLE_APPLICATION_CREDENTIALS
                self.vision_client = vision.ImageAnnotatorClient()
                logger.info("Google Vision API inicializada")
            except Exception as e:
                logger.error(f"Error inicializando Google Vision: {e}")
        
        # DeepFace configuración
        self.deepface_available = DEEPFACE_AVAILABLE
        self.deepface_model = config.DEEPFACE_MODEL
        self.known_faces_path = config.KNOWN_FACES_PATH
        self.known_faces_db = self._load_known_faces_db()
        
        logger.info(f"Reconocedor facial inicializado - Vision: {bool(self.vision_client)}, DeepFace: {self.deepface_available}")
    
    def _load_known_faces_db(self) -> Dict:
        """Cargar base de datos de caras conocidas de personajes"""
        db = {}        
        if not self.known_faces_path.exists():
            logger.warning(f"Directorio de caras conocidas no existe: {self.known_faces_path}")
            return db
        
        # Cargar caras conocidas por categorías
        for category_dir in self.known_faces_path.iterdir():
            if category_dir.is_dir():
                category_name = category_dir.name
                db[category_name] = []
                
                # Buscar imágenes en la categoría
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
                for image_file in category_dir.iterdir():
                    if image_file.suffix.lower() in image_extensions:
                        character_name = image_file.stem
                        db[category_name].append({
                            'name': character_name,
                            'image_path': str(image_file),
                            'category': category_name
                        })
                
                logger.info(f"Cargadas {len(db[category_name])} caras para {category_name}")
        
        return db
    
    def recognize_faces_intelligent(self, image_data: bytes, video_data: Dict = None) -> Dict:
        """Reconocimiento facial inteligente combinando todas las estrategias"""
        logger.info("Iniciando reconocimiento facial inteligente")
        
        results = {
            'detected_characters': [],
            'recognition_sources': [],
            'confidence_scores': [],
            'suggestions_from_title': [],
            'suggestions_from_creator': [],
            'error': None
        }
        
        # ESTRATEGIA 1: Análisis de título y creador (más rápido y confiable)
        if video_data:
            # Obtener sugerencias de título
            if video_data.get('title'):
                title = video_data['title']
                title_suggestions = get_character_intelligence().analyze_video_title(title)
                results['suggestions_from_title'] = title_suggestions
                
                for suggestion in title_suggestions:
                    results['detected_characters'].append(suggestion['name'])
                    results['confidence_scores'].append(suggestion['confidence'])
                    results['recognition_sources'].append(f"title_analysis_{suggestion['source']}")
                    logger.info(f"DEBUG: Personaje de título: {suggestion['name']} (confianza: {suggestion['confidence']:.1f})")
            else:
                logger.info("DEBUG: No hay título para analizar")
            
            # Obtener sugerencias de creador
            if video_data.get('creator_name'):
                creator_suggestion = get_character_intelligence().analyze_creator_name(video_data['creator_name'])
                if creator_suggestion:
                    results['suggestions_from_creator'] = [creator_suggestion]
                    results['detected_characters'].append(creator_suggestion['name'])
                    results['confidence_scores'].append(creator_suggestion['confidence'])
                    results['recognition_sources'].append(f"creator_analysis_{creator_suggestion['source']}")
                    logger.info(f"DEBUG: Personaje de creador: {creator_suggestion['name']}")
        
        # DEBUG: Mostrar resultados antes del análisis visual
        logger.info(f"DEBUG: Personajes antes de análisis visual: {len(results['detected_characters'])}")
        
        # Si ya tenemos resultados de alta confianza, no necesitamos análisis visual costoso
        high_confidence_results = [score for score in results['confidence_scores'] if score >= 0.8]
        if high_confidence_results:
            logger.info(f"Reconocimiento completado con alta confianza: {len(high_confidence_results)} personajes")
            return results
        
        # ESTRATEGIA 2: Reconocimiento visual (solo si no hay resultados de alta confianza)
        visual_results = self.recognize_faces(image_data)
        
        # Combinar resultados visuales
        if visual_results['detected_characters']:
            results['detected_characters'].extend(visual_results['detected_characters'])
            results['confidence_scores'].extend(visual_results['confidence_scores'])
            results['recognition_sources'].extend([visual_results['recognition_source']] * len(visual_results['detected_characters']))
        
        # Eliminar duplicados manteniendo la mayor confianza
        unique_results = self._deduplicate_results(results)
        
        logger.info(f"Reconocimiento inteligente completado: {len(unique_results['detected_characters'])} personajes únicos")
        return unique_results
    
    def _deduplicate_results(self, results: Dict) -> Dict:
        """Eliminar personajes duplicados manteniendo la mayor confianza"""
        if not results['detected_characters']:
            return results
        
        # Crear diccionario para trackear personajes únicos
        unique_characters = {}
        
        for i, character in enumerate(results['detected_characters']):
            confidence = results['confidence_scores'][i] if i < len(results['confidence_scores']) else 0.5
            source = results['recognition_sources'][i] if i < len(results['recognition_sources']) else 'unknown'
            
            # Normalizar nombre para comparación
            normalized_name = character.lower().strip()
            
            # Si es nuevo o tiene mayor confianza, mantener
            if (normalized_name not in unique_characters or 
                confidence > unique_characters[normalized_name]['confidence']):
                unique_characters[normalized_name] = {
                    'name': character,
                    'confidence': confidence,
                    'source': source
                }
        
        # Reconstruir listas
        deduplicated = {
            'detected_characters': [],
            'confidence_scores': [],
            'recognition_sources': [],
            'suggestions_from_title': results.get('suggestions_from_title', []),
            'suggestions_from_creator': results.get('suggestions_from_creator', []),
            'error': results.get('error')
        }
        
        for char_data in unique_characters.values():
            deduplicated['detected_characters'].append(char_data['name'])
            deduplicated['confidence_scores'].append(char_data['confidence'])
            deduplicated['recognition_sources'].append(char_data['source'])
        
        return deduplicated
    
    def recognize_faces(self, image_data: bytes) -> Dict:
        """Reconocer caras usando estrategia híbrida"""
        logger.info("Iniciando reconocimiento facial")
        
        results = {
            'detected_characters': [],
            'recognition_source': None,
            'confidence_scores': [],
            'error': None
        }
        
        # Estrategia 1: Google Vision API (para TikTokers famosos)
        if self.vision_client:
            try:
                vision_results = self._recognize_with_google_vision(image_data)
                if vision_results['detected_characters']:
                    results.update(vision_results)
                    results['recognition_source'] = 'google_vision'
                    logger.info(f"Caras detectadas con Google Vision: {len(results['detected_characters'])}")
                    return results
            except Exception as e:
                logger.warning(f"Error con Google Vision: {e}")
        
        # Estrategia 2: DeepFace local (para personajes anime/gaming)
        if self.deepface_available and self.known_faces_db:
            try:
                deepface_results = self._recognize_with_deepface(image_data)
                if deepface_results['detected_characters']:
                    results.update(deepface_results)
                    results['recognition_source'] = 'deepface'
                    logger.info(f"Personajes detectados con DeepFace: {len(results['detected_characters'])}")
                    return results
            except Exception as e:
                logger.warning(f"Error con DeepFace: {e}")
        
        logger.info("⚠️ No se detectaron caras o personajes conocidos")
        return results
    
    def _recognize_with_google_vision(self, image_data: bytes) -> Dict:
        """Reconocimiento con Google Vision API para TikTokers famosos - CON FILTROS ANTI-FALSOS POSITIVOS"""
        results = {
            'detected_characters': [],
            'confidence_scores': []
        }
        
        # 🚫 LISTA DE FILTROS PARA FALSOS POSITIVOS
        # Nombres que claramente no son relevantes para videos de baile/cosplay asiático
        false_positive_filters = {
            # Nombres que suenan como músicos/artistas occidentales no relevantes
            'sanju', 'rathod', 'shaky', 'g-spxrk', 'dj', 'mc', 'rapper',
            
            # Nombres genéricos que no son personas específicas
            'person', 'people', 'dancer', 'girl', 'woman', 'man', 'cosplayer',
            'tiktoker', 'influencer', 'creator', 'user', 'account',
            
            # Términos técnicos de Google Vision que no son nombres
            'entertainment', 'performance', 'music', 'dance', 'video', 'content',
            'fashion', 'style', 'beauty', 'makeup', 'hair', 'outfit',
            
            # Términos relacionados con apps/plataformas
            'tiktok', 'instagram', 'youtube', 'shorts', 'reels', 'story',
            'live', 'stream', 'broadcast', 'upload', 'post', 'share',
            
            # Palabras que indican ubicaciones o marcas, no personas
            'studio', 'stage', 'room', 'home', 'house', 'background',
            'brand', 'company', 'product', 'service', 'app', 'website'
        }
        
        # 🎯 PATRONES SOSPECHOSOS QUE INDICAN FALSOS POSITIVOS
        suspicious_patterns = [
            r'^[A-Z]-[A-Z]+$',  # Patrones como "G-SPXRK" (letra-guion-letras)
            r'^\w+\d+$',        # Nombres con números al final como "User123"
            r'^DJ\s+\w+',       # Nombres que empiezan con "DJ"
            r'^MC\s+\w+',       # Nombres que empiezan con "MC"
            r'^\w{1,2}$',       # Nombres muy cortos (1-2 caracteres)
            r'^\w+[._]\w+$',    # Nombres con puntos o guiones bajos (usernames)
        ]
        
        try:
            # Crear objeto imagen para Google Vision
            image = vision.Image(content=image_data)
            
            # Detectar caras famosas
            response = self.vision_client.face_detection(image=image)
            faces = response.face_annotations
            
            if faces:
                logger.info(f"Google Vision detectó {len(faces)} caras")
                
                # También intentar detección de celebridades si está disponible
                try:
                    web_response = self.vision_client.web_detection(image=image)
                    web_entities = web_response.web_detection.web_entities
                    
                    valid_detections = 0
                    filtered_detections = 0
                    
                    for entity in web_entities:
                        if entity.score > 0.5:  # Umbral de confianza
                            entity_name = entity.description.strip()
                            entity_name_lower = entity_name.lower()
                            
                            # 🚫 APLICAR FILTROS DE FALSOS POSITIVOS
                            
                            # Filtro 1: Lista de palabras prohibidas
                            is_filtered = False
                            for filter_word in false_positive_filters:
                                if filter_word in entity_name_lower:
                                    logger.debug(f"Filtrado por palabra prohibida '{filter_word}': {entity_name}")
                                    is_filtered = True
                                    break
                            
                            # Filtro 2: Patrones sospechosos
                            if not is_filtered:
                                import re
                                for pattern in suspicious_patterns:
                                    if re.match(pattern, entity_name):
                                        logger.debug(f"Filtrado por patrón sospechoso '{pattern}': {entity_name}")
                                        is_filtered = True
                                        break
                            
                            # Filtro 3: Verificar relevancia contextual
                            if not is_filtered:
                                # Solo aceptar nombres que parecen personas reales asiáticas o cosplayers conocidos
                                if self._is_likely_relevant_person(entity_name):
                                    results['detected_characters'].append(entity_name)
                                    results['confidence_scores'].append(entity.score)
                                    valid_detections += 1
                                    logger.info(f"✅ Detección válida: {entity_name} (confianza: {entity.score:.2f})")
                                else:
                                    logger.debug(f"Filtrado por irrelevancia contextual: {entity_name}")
                                    is_filtered = True
                            
                            if is_filtered:
                                filtered_detections += 1
                    
                    logger.info(f"Google Vision: {valid_detections} detecciones válidas, {filtered_detections} filtradas")
                    
                except Exception as e:
                    logger.debug(f"Web detection no disponible: {e}")
                
                # Si no hay entidades web válidas después del filtrado, NO agregar detección genérica
                # Esto evita agregar "Persona detectada" cuando las detecciones fueron filtradas por irrelevantes
                if not results['detected_characters']:
                    logger.info("No se encontraron detecciones válidas después del filtrado")
            
        except Exception as e:
            logger.error(f"Error en Google Vision: {e}")
        
        return results
    
    def _is_likely_relevant_person(self, name: str) -> bool:
        """Verificar si un nombre detectado es probablemente una persona relevante"""
        name_lower = name.lower().strip()
        
        # 🚫 RECHAZAR nombres claramente irrelevantes
        irrelevant_indicators = [
            # Términos genéricos
            'unknown', 'unnamed', 'anonymous', 'user', 'account', 'profile',
            'person', 'people', 'individual', 'someone', 'anybody', 'everybody',
            
            # Términos técnicos
            'algorithm', 'system', 'software', 'application', 'platform', 'service',
            'technology', 'digital', 'virtual', 'artificial', 'computer', 'machine',
            
            # Términos de contenido
            'content', 'media', 'video', 'audio', 'image', 'photo', 'picture',
            'clip', 'segment', 'scene', 'frame', 'shot', 'angle', 'view',
            
            # Términos de redes sociales
            'follower', 'subscriber', 'viewer', 'audience', 'fan', 'community',
            'channel', 'page', 'feed', 'timeline', 'story', 'post', 'update'
        ]
        
        for indicator in irrelevant_indicators:
            if indicator in name_lower:
                return False
        
        # ✅ ACEPTAR nombres que parecen personas reales
        relevant_indicators = [
            # Solo nombres que parecen personas reales con al menos 3 caracteres
            # y que no contienen caracteres especiales raros
        ]
        
        # Verificaciones básicas para nombres de personas reales
        # - Al menos 3 caracteres
        # - No más de 50 caracteres (evitar descripciones largas)
        # - Contiene solo letras, espacios, guiones, apostrofes básicos
        import re
        if (len(name) >= 3 and 
            len(name) <= 50 and 
            re.match(r"^[a-zA-Z\s\-'\.]+$", name)):
            return True
        
        return False
    
    def _recognize_with_deepface(self, image_data: bytes) -> Dict:
        """Reconocimiento con DeepFace para personajes anime/gaming"""
        results = {
            'detected_characters': [],
            'confidence_scores': []
        }
        
        try:
            # Convertir bytes a imagen PIL
            image = Image.open(io.BytesIO(image_data))
            
            # Convertir a array numpy
            image_array = np.array(image)
            
            # Buscar en cada categoría de personajes conocidos
            for category, characters in self.known_faces_db.items():
                for character in characters:
                    try:
                        # Comparar con cada personaje conocido
                        result = DeepFace.verify(
                            img1_path=image_array,
                            img2_path=character['image_path'],
                            model_name=self.deepface_model,
                            enforce_detection=False  # No fallar si no detecta cara
                        )
                        
                        # Si la verificación es positiva
                        if result['verified'] and result['distance'] < 0.6:  # Umbral de distancia
                            confidence = 1.0 - result['distance']  # Convertir distancia a confianza
                            
                            character_full_name = f"{character['name']} ({category})"
                            results['detected_characters'].append(character_full_name)
                            results['confidence_scores'].append(confidence)
                            
                            logger.info(f"Personaje detectado: {character_full_name} (confianza: {confidence:.2f})")
                            
                    except Exception as e:
                        # Es normal que falle en algunos casos
                        logger.debug(f"No match con {character['name']}: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Error en DeepFace: {e}")
        
        return results

# face_recognizer = FaceRecognizer()
