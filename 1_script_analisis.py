#!/usr/bin/env python3
"""
Tag-Flow - Script de Análisis de Videos
Autor: Sistema Tag-Flow
Versión: 1.0

Este script procesa videos automáticamente para extraer:
- Creador (basado en la carpeta)
- Música (usando API de reconocimiento)
- Personajes (usando reconocimiento facial)
- Dificultad de edición (input manual)
"""

import os
import sys
import pandas as pd
import face_recognition
import cv2
import numpy as np
from pathlib import Path
from moviepy.editor import VideoFileClip
import requests
import time
from dotenv import load_dotenv
from typing import List, Dict, Tuple, Optional

class TagFlowAnalyzer:
    def __init__(self):
        """Inicializar el analizador de Tag-Flow"""
        self.load_config()
        self.setup_paths()
        self.load_known_faces()
        self.load_existing_data()
        
    def load_config(self):
        """Cargar configuración desde .env"""
        load_dotenv()
        self.api_key = os.getenv('API_KEY_MUSICA')
        self.frames_interval = int(os.getenv('PROCESAR_CADA_N_FRAMES', 30))
        self.audio_duration = int(os.getenv('DURACION_CLIP_AUDIO', 15))
        
        if not self.api_key or self.api_key == "tu_clave_de_api_aqui":
            print("⚠️  ADVERTENCIA: No se ha configurado una clave de API válida.")
            print("   El reconocimiento de música será limitado.")
            self.api_key = None
    
    def setup_paths(self):
        """Configurar rutas del proyecto"""
        self.project_root = Path(__file__).parent
        self.data_dir = self.project_root / "data"
        self.faces_dir = self.project_root / "caras_conocidas"
        self.videos_dir = self.project_root / "videos_a_procesar"
        self.csv_path = self.data_dir / "videos.csv"
        
        # Crear directorios si no existen
        self.data_dir.mkdir(exist_ok=True)
        
    def load_known_faces(self):
        """Cargar y codificar caras conocidas"""
        self.known_faces = {}
        self.known_encodings = []
        self.known_names = []
        
        print("🔍 Cargando caras conocidas...")
        
        if not self.faces_dir.exists():
            print(f"⚠️  Carpeta de caras no encontrada: {self.faces_dir}")
            return
            
        face_files = list(self.faces_dir.glob("*.jpg")) + list(self.faces_dir.glob("*.png")) + list(self.faces_dir.glob("*.jpeg"))
        
        if not face_files:
            print("⚠️  No se encontraron archivos de caras en la carpeta 'caras_conocidas'")
            print("   Coloca imágenes de personajes conocidos en esa carpeta para habilitarE el reconocimiento")
            return
            
        for face_file in face_files:
            try:
                # Cargar imagen
                image = face_recognition.load_image_file(str(face_file))
                # Obtener codificación facial
                encodings = face_recognition.face_encodings(image)
                
                if encodings:
                    name = face_file.stem  # Nombre del archivo sin extensión
                    self.known_faces[name] = encodings[0]
                    self.known_encodings.append(encodings[0])
                    self.known_names.append(name)
                    print(f"  ✅ Cargada cara: {name}")
                else:
                    print(f"  ❌ No se detectó cara en: {face_file.name}")
                    
            except Exception as e:
                print(f"  ❌ Error cargando {face_file.name}: {e}")
        
        print(f"✅ Total de caras conocidas cargadas: {len(self.known_faces)}")
    
    def load_existing_data(self):
        """Cargar datos existentes desde CSV"""
        if self.csv_path.exists():
            try:
                self.df = pd.read_csv(self.csv_path)
                print(f"✅ Datos existentes cargados: {len(self.df)} videos procesados")
            except Exception as e:
                print(f"❌ Error cargando datos existentes: {e}")
                self.df = self.create_empty_dataframe()
        else:
            self.df = self.create_empty_dataframe()
            print("📝 Creando nueva base de datos")
    
    def create_empty_dataframe(self) -> pd.DataFrame:
        """Crear DataFrame vacío con las columnas correctas"""
        return pd.DataFrame(columns=[
            'ruta_absoluta', 'archivo', 'creador', 'personajes', 
            'musica', 'dificultad_edicion', 'fecha_procesado', 'fecha_editado'
        ])
    
    def find_new_videos(self) -> List[Path]:
        """Encontrar videos nuevos que no han sido procesados"""
        if not self.videos_dir.exists():
            print(f"❌ Carpeta de videos no encontrada: {self.videos_dir}")
            return []
        
        # Extensiones de video soportadas
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}
        
        # Encontrar todos los videos
        all_videos = []
        for ext in video_extensions:
            all_videos.extend(self.videos_dir.rglob(f"*{ext}"))
            all_videos.extend(self.videos_dir.rglob(f"*{ext.upper()}"))
        
        # Filtrar solo los nuevos
        processed_paths = set(self.df['ruta_absoluta'].tolist()) if not self.df.empty else set()
        new_videos = [v for v in all_videos if str(v.absolute()) not in processed_paths]
        
        print(f"📊 Videos encontrados: {len(all_videos)}, Nuevos: {len(new_videos)}")
        return new_videos
    
    def extract_creator(self, video_path: Path) -> str:
        """Extraer el nombre del creador desde la estructura de carpetas"""
        # El creador es el nombre de la carpeta padre del video
        return video_path.parent.name
    
    def recognize_music(self, video_path: Path) -> str:
        """Reconocer música en el video usando API"""
        if not self.api_key:
            return "API no configurada"
        
        try:
            print(f"  🎵 Analizando música...")
            
            # Extraer clip de audio
            with VideoFileClip(str(video_path)) as video:
                # Tomar clip del medio del video
                start_time = max(0, video.duration / 2 - self.audio_duration / 2)
                end_time = min(video.duration, start_time + self.audio_duration)
                
                audio_clip = video.subclip(start_time, end_time).audio
                temp_audio = self.project_root / "temp_audio.wav"
                
                audio_clip.write_audiofile(str(temp_audio), verbose=False, logger=None)
                audio_clip.close()
            
            # Aquí iría la llamada a la API de música
            # Por ahora retornamos un placeholder
            music_result = "Música no identificada (API pendiente)"
            
            # Limpiar archivo temporal
            if temp_audio.exists():
                temp_audio.unlink()
                
            return music_result
            
        except Exception as e:
            print(f"    ❌ Error en reconocimiento de música: {e}")
            return f"Error: {str(e)}"
    
    def recognize_characters(self, video_path: Path) -> List[str]:
        """Reconocer personajes en el video"""
        if not self.known_faces:
            return []
        
        try:
            print(f"  👥 Analizando personajes...")
            
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps == 0:
                fps = 30  # Fallback
                
            found_characters = set()
            frames_to_process = range(0, frame_count, self.frames_interval)
            
            for frame_num in frames_to_process:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Convertir BGR a RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Encontrar caras en el frame
                face_locations = face_recognition.face_locations(rgb_frame)
                if face_locations:
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    
                    for encoding in face_encodings:
                        matches = face_recognition.compare_faces(self.known_encodings, encoding, tolerance=0.6)
                        
                        if True in matches:
                            match_index = matches.index(True)
                            name = self.known_names[match_index]
                            found_characters.add(name)
            
            cap.release()
            characters_list = list(found_characters)
            print(f"    ✅ Personajes encontrados: {characters_list}")
            return characters_list
            
        except Exception as e:
            print(f"    ❌ Error en reconocimiento de personajes: {e}")
            return []
    
    def get_difficulty_input(self, video_info: Dict) -> str:
        """Solicitar al usuario la dificultad de edición"""
        print("\n" + "="*50)
        print("📹 INFORMACIÓN DEL VIDEO:")
        print("="*50)
        print(f"Archivo: {video_info['archivo']}")
        print(f"Creador: {video_info['creador']}")
        print(f"Música: {video_info['musica']}")
        print(f"Personajes: {video_info['personajes']}")
        print("="*50)
        
        while True:
            difficulty = input("¿Cuál es la dificultad de edición? (alto/medio/bajo): ").lower().strip()
            if difficulty in ['alto', 'medio', 'bajo']:
                return difficulty
            print("❌ Por favor ingresa: 'alto', 'medio' o 'bajo'")
    
    def process_video(self, video_path: Path) -> Dict:
        """Procesar un video completo"""
        print(f"\n🎬 Procesando: {video_path.name}")
        
        # Extraer información básica
        video_info = {
            'ruta_absoluta': str(video_path.absolute()),
            'archivo': video_path.name,
            'creador': self.extract_creator(video_path),
            'fecha_procesado': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Reconocimiento de música
        video_info['musica'] = self.recognize_music(video_path)
        
        # Reconocimiento de personajes
        characters = self.recognize_characters(video_path)
        video_info['personajes'] = ', '.join(characters) if characters else 'Ninguno detectado'
        
        # Input manual de dificultad
        video_info['dificultad_edicion'] = self.get_difficulty_input(video_info)
        
        return video_info
    
    def save_data(self):
        """Guardar datos al CSV"""
        try:
            self.df.to_csv(self.csv_path, index=False)
            print(f"💾 Datos guardados en: {self.csv_path}")
        except Exception as e:
            print(f"❌ Error guardando datos: {e}")
    
    def run(self):
        """Ejecutar el proceso completo de análisis"""
        print("🚀 Iniciando Tag-Flow Analyzer")
        print("="*50)
        
        # Encontrar videos nuevos
        new_videos = self.find_new_videos()
        
        if not new_videos:
            print("✅ No hay videos nuevos para procesar")
            return
        
        print(f"📋 Videos a procesar: {len(new_videos)}")
        
        # Procesar cada video
        for i, video_path in enumerate(new_videos, 1):
            try:
                print(f"\n[{i}/{len(new_videos)}]", end=" ")
                video_info = self.process_video(video_path)
                
                # Añadir al DataFrame
                self.df = pd.concat([self.df, pd.DataFrame([video_info])], ignore_index=True)
                
                # Guardar cada 5 videos (para no perder progreso)
                if i % 5 == 0:
                    self.save_data()
                    print(f"💾 Progreso guardado ({i}/{len(new_videos)})")
                    
            except KeyboardInterrupt:
                print("\n⏹️  Proceso interrumpido por el usuario")
                self.save_data()
                break
            except Exception as e:
                print(f"\n❌ Error procesando {video_path.name}: {e}")
                continue
        
        # Guardar datos finales
        self.save_data()
        print(f"\n🎉 ¡Procesamiento completado!")
        print(f"📊 Total de videos en la base de datos: {len(self.df)}")

def main():
    """Función principal"""
    try:
        analyzer = TagFlowAnalyzer()
        analyzer.run()
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
