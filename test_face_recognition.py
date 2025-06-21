"""
Script de prueba para reconocimiento facial híbrido (Google Vision + DeepFace)
Uso: python test_face_recognition.py <ruta_imagen>
"""

import sys
import logging
from pathlib import Path
import os

from src.face_recognition import FaceRecognizer

# Ocultar logs de TensorFlow y Keras
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

logging.basicConfig(level=logging.INFO)

if len(sys.argv) < 2:
    print("Uso: python test_face_recognition.py <ruta_imagen>")
    sys.exit(1)

image_path = Path(sys.argv[1])
if not image_path.exists():
    print(f"Imagen no encontrada: {image_path}")
    sys.exit(1)

with open(image_path, "rb") as f:
    image_data = f.read()

recognizer = FaceRecognizer()

print("\n--- Prueba de reconocimiento facial ---\n")

results = recognizer.recognize_faces(image_data)

print(f"Fuente de reconocimiento: {results.get('recognition_source')}")
print(f"Caras/personajes detectados: {results.get('detected_characters')}")
print(f"Confianza: {results.get('confidence_scores')}")
if results.get('error'):
    print(f"Error: {results['error']}")

print("\nRevisa los logs para detalles adicionales de errores o advertencias.")
