#!/usr/bin/env python3
"""
Tag-Flow - Script de Análisis con ACRCloud
Versión con integración completa de ACRCloud para reconocimiento de música
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

# Importar módulo de ACRCloud
try:
    from acrcloud_recognizer import ACRCloudRecognizer, test_acrcloud_connection
    ACRCLOUD_AVAILABLE = True
except ImportError:
    ACRCLOUD_AVAILABLE = False

class TagFlowAnalyzerWithMusic:
    def __init__(self):
        """Inicializar el analizador de Tag-Flow con reconocimiento de música"""
        self.load_config()
        self.setup_paths()
        self.setup_music_recognition()
        self.load_existing_data()
        
    def load_config(self):
        """Cargar configuración desde .env"""
        load_dotenv()
        
        # Configuración ACRCloud
        self.acrcloud_host = os.getenv('ACRCLOUD_HOST')
        self.acrcloud_access_key = os.getenv('ACRCLOUD_ACCESS_KEY')
        self.acrcloud_access_secret = os.getenv('ACRCLOUD_ACCESS_SECRET')
        
        # Otras configuraciones
        self.frames_interval = int(os.getenv('PROCESAR_CADA_N_FRAMES', 30))
        self.audio_duration = int(os.getenv('DURACION_CLIP_AUDIO', 15))
        
        # Verificar configuración ACRCloud
        if not all([self.acrcloud_host, self.acrcloud_access_key, self.acrcloud_access_secret]):
            print("⚠️  ADVERTENCIA: Configuración ACRCloud incompleta.")
            print("   Configura ACRCLOUD_HOST, ACRCLOUD_ACCESS_KEY y ACRCLOUD_ACCESS_SECRET en .env")
            print("   Ver CONFIGURAR_ACRCLOUD.md para instrucciones")
            self.acrcloud_configured = False
        elif any(cred in ["tu_access_key_aqui", "tu_access_secret_aqui"] 
                for cred in [self.acrcloud_access_key, self.acrcloud_access_secret]):
            print("⚠️  ADVERTENCIA: Credenciales ACRCloud no configuradas.")
            print("   Edita el archivo .env con tus credenciales reales")
            self.acrcloud_configured = False
        else:
            self.acrcloud_configured = True
            print("✅ Configuración ACRCloud detectada")
    
    def setup_paths(self):
        """Configurar rutas del proyecto"""
        self.project_root = Path(__file__).parent
        self.data_dir = self.project_root / "data"
        self.faces_dir = self.project_root / "caras_conocidas"
        self.videos_dir = self.project_root / "videos_a_procesar"
        self.csv_path = self.data_dir / "videos.csv"
        
        # Crear directorios si no existen
        self.data_dir.mkdir(exist_ok=True)
        
    def setup_music_recognition(self):
        """Configurar reconocimiento de música"""
        if not ACRCLOUD_AVAILABLE:
            print("⚠️  Módulo ACRCloud no disponible")
            self.music_recognizer = None
            return
            
        if not self.acrcloud_configured:
            self.music_recognizer = None
            return
            
        try:
            # Probar conexión
            print("🔌 Probando conexión con ACRCloud...")
            if test_acrcloud_connection(self.acrcloud_host, self.acrcloud_access_key, self.acrcloud_access_secret):
                self.music_recognizer = ACRCloudRecognizer(
                    self.acrcloud_host, 
                    self.acrcloud_access_key, 
                    self.acrcloud_access_secret
                )
                print("✅ Conexión exitosa con ACRCloud")
            else:
                print("❌ Error de conexión con ACRCloud - revisa credenciales")
                self.music_recognizer = None
        except Exception as e:
            print(f"❌ Error configurando ACRCloud: {e}")
            self.music_recognizer = None
        
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
        """Reconocer música en el video usando ACRCloud"""
        if not self.music_recognizer:
            return "ACRCloud no configurado"
        
        temp_audio = None
        video = None
        audio_clip = None
        
        try:
            print(f"  🎵 Analizando música con ACRCloud...")
            
            # Extraer clip de audio
            temp_audio = self.project_root / "temp_audio.wav"
            
            # Verificar que el archivo de video existe y es accesible
            if not video_path.exists():
                return "Error: Archivo de video no encontrado"
            
            try:
                # Cargar video con MoviePy
                print(f"    📼 Cargando video...")
                video = VideoFileClip(str(video_path))
                
                # Verificar que el video tiene audio
                if video.audio is None:
                    return "Sin audio en el video"
                
                # Verificar duración del video
                video_duration = getattr(video, 'duration', 0)
                if video_duration < 5:
                    return "Video demasiado corto para análisis"
                
                print(f"    ⏱️ Duración del video: {video_duration:.1f}s")
                
                # Tomar clip del medio del video
                start_time = max(0, video_duration / 2 - self.audio_duration / 2)
                end_time = min(video_duration, start_time + self.audio_duration)
                
                print(f"    ✂️ Extrayendo audio ({start_time:.1f}s - {end_time:.1f}s)...")
                
                # Intentar diferentes métodos para extraer subclip
                try:
                    # Método CORRECTO según StackOverflow: subclipped()
                    if hasattr(video, 'subclipped'):
                        video_clip = video.subclipped(start_time, end_time)
                        audio_clip = video_clip.audio
                        print(f"    ✅ Usando video.subclipped() - método correcto")
                    # Método alternativo: subclip() (versiones más antiguas)
                    elif hasattr(video, 'subclip'):
                        video_clip = video.subclip(start_time, end_time)
                        audio_clip = video_clip.audio
                        print(f"    ✅ Usando video.subclip() - método legacy")
                    else:
                        # Método directo en audio
                        if hasattr(video.audio, 'subclipped'):
                            audio_clip = video.audio.subclipped(start_time, end_time)
                            print(f"    ✅ Usando audio.subclipped()")
                        elif hasattr(video.audio, 'subclip'):
                            audio_clip = video.audio.subclip(start_time, end_time)
                            print(f"    ✅ Usando audio.subclip()")
                        else:
                            return "Error: No se pudo extraer subclip de audio"
                    
                except Exception as subclip_error:
                    print(f"    ⚠️ Error con subclip, intentando método alternativo: {subclip_error}")
                    # Método alternativo: extraer todo el audio
                    audio_clip = video.audio
                    print(f"    ℹ️ Usando audio completo como fallback")
                
                if audio_clip is None:
                    return "Error: No se pudo extraer audio"
                
                # Escribir archivo de audio temporal
                print(f"    💾 Guardando audio temporal...")
                
                # Llamada compatible con todas las versiones de MoviePy
                try:
                    # Método 1: Con parámetros completos (versiones nuevas)
                    audio_clip.write_audiofile(
                        str(temp_audio), 
                        verbose=False, 
                        logger=None
                    )
                except TypeError:
                    try:
                        # Método 2: Sin verbose (versiones que no lo soportan)
                        audio_clip.write_audiofile(str(temp_audio), logger=None)
                    except TypeError:
                        # Método 3: Solo ruta (máxima compatibilidad)
                        audio_clip.write_audiofile(str(temp_audio))
                
                print(f"    🔍 Enviando a ACRCloud...")
                
                # Reconocer música con ACRCloud
                result = self.music_recognizer.recognize_audio_file(str(temp_audio))
                
                # Procesar resultado
                if result['status'] == 'success':
                    music_info = result['formatted']
                    confidence = result.get('confidence', 0)
                    print(f"    ✅ Música identificada: {music_info} (confianza: {confidence})")
                    return music_info
                elif result['status'] == 'no_match':
                    print(f"    ℹ️ No se encontró música conocida")
                    return "Música no identificada"
                else:
                    error = result.get('error', 'Error desconocido')
                    print(f"    ❌ Error ACRCloud: {error}")
                    return f"Error ACRCloud: {error}"
                    
            except Exception as video_error:
                print(f"    ❌ Error procesando video: {video_error}")
                return f"Error procesando video: {str(video_error)}"
                    
        except Exception as e:
            print(f"    ❌ Error general en reconocimiento de música: {e}")
            return f"Error: {str(e)}"
            
        finally:
            # Limpiar recursos
            try:
                if audio_clip:
                    audio_clip.close()
                if video:
                    video.close()
            except Exception:
                pass
                
            # Limpiar archivos temporales
            try:
                if temp_audio and temp_audio.exists():
                    temp_audio.unlink()
                    
                # Limpiar archivo temporal de MoviePy
                temp_moviepy = self.project_root / "temp_audiofile.wav"
                if temp_moviepy.exists():
                    temp_moviepy.unlink()
            except Exception:
                pass  # No importa si no se puede limpiar
    
    def recognize_characters_basic(self, video_path: Path) -> List[str]:
        """Reconocimiento básico sin face_recognition"""
        print(f"  👥 Analizando personajes... (modo básico)")
        
        # Lista de personajes conocidos desde archivos
        known_characters = []
        if self.faces_dir.exists():
            face_files = list(self.faces_dir.glob("*.jpg")) + list(self.faces_dir.glob("*.png")) + list(self.faces_dir.glob("*.jpeg"))
            known_characters = [f.stem for f in face_files]
        
        if not known_characters:
            print(f"    ℹ️ No hay personajes conocidos configurados")
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
    
    def process_video(self, video_path: Path) -> Optional[Dict]:
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
        print("🚀 Iniciando Tag-Flow Analyzer con Reconocimiento de Música")
        print("="*60)
        
        if self.music_recognizer:
            print("🎵 Reconocimiento de música: ACTIVADO (ACRCloud)")
        else:
            print("⚠️  Reconocimiento de música: DESACTIVADO")
            
        print("👥 Reconocimiento de personajes: MANUAL")
        print("="*60)
        
        # Encontrar videos nuevos
        new_videos = self.find_new_videos()
        
        if not new_videos:
            print("✅ No hay videos nuevos para procesar")
            return
        
        print(f"📋 Videos a procesar: {len(new_videos)}")
        
        # Procesar cada video
        processed_count = 0
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
                processed_count += 1
                
                # Guardar cada 3 videos
                if processed_count % 3 == 0:
                    self.save_data()
                    print(f"💾 Progreso guardado ({processed_count} videos procesados)")
                    
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
        print(f"✨ Videos procesados en esta sesión: {processed_count}")

def main():
    """Función principal"""
    try:
        analyzer = TagFlowAnalyzerWithMusic()
        analyzer.run()
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
