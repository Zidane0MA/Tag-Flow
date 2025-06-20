#!/usr/bin/env python3
"""
Tag-Flow - Script de Análisis (Versión Sin Face Recognition)
Versión alternativa que funciona sin reconocimiento facial
"""

import os
import sys
import pandas as pd
import cv2
import numpy as np
from pathlib import Path
from moviepy import VideoFileClip
import requests
import time
from dotenv import load_dotenv
from typing import List, Dict, Tuple, Optional

class TagFlowAnalyzerBasic:
    def __init__(self):
        """Inicializar el analizador básico de Tag-Flow"""
        self.load_config()
        self.setup_paths()
        self.load_existing_data()
        
    def load_config(self):
        """Cargar configuración desde .env"""
        load_dotenv()
        self.api_key = os.getenv('API_KEY_MUSICA')
        print(repr(os.getenv("PROCESAR_CADA_N_FRAMES")))

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
        
    def load_existing_data(self):
        """Cargar datos existentes desde CSV"""
        if self.csv_path.exists():
            try:
                self.df = pd.read_csv(self.csv_path)
                
                # Limpiar duplicados si existen
                initial_count = len(self.df)
                self.df = self.df.drop_duplicates(subset=['ruta_absoluta'], keep='last')
                final_count = len(self.df)
                
                if initial_count != final_count:
                    print(f"🧹 Limpiados {initial_count - final_count} duplicados del CSV")
                    self.save_data()  # Guardar CSV limpio
                
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
        
        # Normalizar rutas para comparación
        all_video_paths = {str(v.absolute()) for v in all_videos}
        
        # Filtrar solo los nuevos
        if not self.df.empty:
            processed_paths = set(self.df['ruta_absoluta'].tolist())
            new_video_paths = all_video_paths - processed_paths
            new_videos = [Path(p) for p in new_video_paths]
        else:
            new_videos = all_videos
        
        print(f"📊 Videos encontrados: {len(all_videos)}, Nuevos: {len(new_videos)}")
        return new_videos
    
    def extract_creator(self, video_path: Path) -> str:
        """Extraer el nombre del creador desde la estructura de carpetas"""
        return video_path.parent.name
    
    def recognize_music(self, video_path: Path) -> str:
        """Reconocer música en el video usando API"""
        if not self.api_key:
            return "API no configurada"
        
        try:
            print(f"  🎵 Analizando música...")
            # Aquí iría la lógica de API real
            return "Música no identificada (API pendiente)"
        except Exception as e:
            print(f"    ❌ Error en reconocimiento de música: {e}")
            return f"Error: {str(e)}"
    
    def recognize_characters_basic(self, video_path: Path) -> List[str]:
        """Reconocimiento básico sin face_recognition"""
        print(f"  👥 Analizando personajes... (modo básico)")
        
        # Lista de personajes conocidos desde archivos
        known_characters = []
        if self.faces_dir.exists():
            face_files = list(self.faces_dir.glob("*.jpg")) + list(self.faces_dir.glob("*.png"))
            known_characters = [f.stem for f in face_files]
        
        if not known_characters:
            return []
        
        print(f"    ℹ️ Personajes conocidos: {known_characters}")
        print(f"    ⚠️ Sin face_recognition - requiere confirmación manual")
        
        # Permitir selección manual
        while True:
            print(f"\n¿Qué personajes aparecen en este video?")
            print(f"Personajes disponibles: {', '.join(known_characters)}")
            print(f"Escribe los nombres separados por comas (o 'ninguno' si no hay):")
            
            user_input = input("Personajes: ").strip()
            
            if user_input.lower() == 'ninguno':
                return []
            
            if not user_input:
                return []
            
            selected = [name.strip() for name in user_input.split(',')]
            
            # Validar que existan
            valid_characters = []
            for char in selected:
                if char in known_characters:
                    valid_characters.append(char)
                else:
                    print(f"⚠️ '{char}' no está en la lista de personajes conocidos")
            
            if valid_characters or not selected:
                return valid_characters
    
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
        
        # Verificar que el video no esté ya en el DataFrame
        absolute_path = str(video_path.absolute())
        if not self.df.empty and absolute_path in self.df['ruta_absoluta'].values:
            print(f"  ⚠️ Este video ya está procesado, saltando...")
            return None
        
        # Extraer información básica
        video_info = {
            'ruta_absoluta': absolute_path,
            'archivo': video_path.name,
            'creador': self.extract_creator(video_path),
            'fecha_procesado': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"  📁 Ruta: {absolute_path}")
        print(f"  👤 Creador: {video_info['creador']}")
        
        # Reconocimiento de música
        video_info['musica'] = self.recognize_music(video_path)
        
        # Reconocimiento de personajes (modo básico)
        characters = self.recognize_characters_basic(video_path)
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
        print("🚀 Iniciando Tag-Flow Analyzer (Modo Básico)")
        print("="*50)
        print("ℹ️  Funcionando sin face_recognition - reconocimiento manual de personajes")
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
                
                # Si el video ya estaba procesado, continuar
                if video_info is None:
                    print(f"  ⭐ Video ya procesado, continuando...")
                    continue
                
                # Añadir al DataFrame
                new_row_df = pd.DataFrame([video_info])
                self.df = pd.concat([self.df, new_row_df], ignore_index=True)
                
                # Verificar que no hay duplicados
                if self.df['ruta_absoluta'].duplicated().any():
                    print(f"  ⚠️ Duplicado detectado, eliminando...")
                    self.df = self.df.drop_duplicates(subset=['ruta_absoluta'], keep='last')
                
                print(f"  ✅ Video añadido correctamente")
                
                # Guardar cada 5 videos
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
        analyzer = TagFlowAnalyzerBasic()
        analyzer.run()
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
