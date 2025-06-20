"""
Tag-Flow V2 - Reconocimiento Facial
Híbrido: Google Vision API (famosos) + DeepFace GPU (personajes anime/gaming)
"""

import os
import json
from typing import Dict, List, Optional
import logging
from pathlib import Path
import numpy as np
from PIL import Image
import io

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

from config import config

logger = logging.getLogger(__name__)

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
        
        logger.info("No se detectaron caras o personajes conocidos")
        return results    
    def _recognize_with_google_vision(self, image_data: bytes) -> Dict:
        """Reconocimiento con Google Vision API para TikTokers famosos"""
        results = {
            'detected_characters': [],
            'confidence_scores': []
        }
        
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
                    
                    for entity in web_entities:
                        if entity.score > 0.5:  # Umbral de confianza
                            results['detected_characters'].append(entity.description)
                            results['confidence_scores'].append(entity.score)
                            
                except Exception as e:
                    logger.debug(f"Web detection no disponible: {e}")
                
                # Si no hay entidades web, al menos sabemos que hay caras
                if not results['detected_characters'] and faces:
                    results['detected_characters'].append("Persona detectada")
                    results['confidence_scores'].append(0.8)
            
        except Exception as e:
            logger.error(f"Error en Google Vision: {e}")
        
        return results
    
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

# Instancia global del reconocedor facial
face_recognizer = FaceRecognizer()