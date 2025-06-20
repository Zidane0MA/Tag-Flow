"""
Tag-Flow V2 - Generador de Datos de Demostración
Crea datos de ejemplo para mostrar la funcionalidad del sistema
"""

import sys
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

# Agregar src al path
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config
from src.database import db

class DemoDataGenerator:
    """Generador de datos de demostración para Tag-Flow V2"""
    
    def __init__(self):
        self.demo_creators = [
            'bella_poarch', 'charlidamelio', 'addisonre', 'zachking', 'lorengray',
            'spencerx', 'michaelle', 'riyaz.14', 'avani', 'dixiedamelio',
            'jamescharles', 'willsmith', 'kylijenner', 'selenagomez', 'justinbieber'
        ]
        
        self.demo_music = [
            ('Cupid', 'FIFTY FIFTY'),
            ('Flowers', 'Miley Cyrus'),
            ('Anti-Hero', 'Taylor Swift'),
            ('As It Was', 'Harry Styles'),
            ('Heat Waves', 'Glass Animals'),
            ('Levitating', 'Dua Lipa'),
            ('Peaches', 'Justin Bieber'),
            ('Positions', 'Ariana Grande'),
            ('Blinding Lights', 'The Weeknd'),
            ('Watermelon Sugar', 'Harry Styles'),
            ('Good 4 U', 'Olivia Rodrigo'),
            ('Stay', 'The Kid LAROI & Justin Bieber'),
            ('Industry Baby', 'Lil Nas X & Jack Harlow'),
            ('Shivers', 'Ed Sheeran'),
            ('Ghost', 'Justin Bieber')
        ]
        
        self.demo_characters = [
            # Genshin Impact
            'Zhongli', 'Raiden Shogun', 'Ganyu', 'Hu Tao', 'Kazuha',
            'Ayaka', 'Venti', 'Diluc', 'Childe', 'Albedo',
            # Honkai Star Rail  
            'Kafka', 'Blade', 'Firefly', 'Dan Heng IL', 'Jingliu',
            'March 7th', 'Stelle', 'Bronya', 'Seele', 'Silver Wolf',
            # Otros personajes populares
            'Miku Hatsune', 'Zero Two', 'Nezuko', 'Rem', 'Asuka'
        ]
        
        self.platforms = ['tiktok', 'instagram', 'youtube']
        self.difficulty_levels = ['bajo', 'medio', 'alto']
        self.edit_statuses = ['nulo', 'en_proceso', 'hecho']
    
    def generate_demo_videos(self, count: int = 50):
        """Generar videos de demostración"""
        print(f"🎬 Generando {count} videos de demostración...")
        
        demo_videos = []
        
        for i in range(count):
            # Seleccionar datos aleatorios
            creator = random.choice(self.demo_creators)
            platform = random.choice(self.platforms)
            music, artist = random.choice(self.demo_music)
            
            # Algunos videos no tendrán música detectada
            has_music = random.random() > 0.2
            
            # Algunos videos tendrán personajes
            has_characters = random.random() > 0.6
            characters = []
            if has_characters:
                num_chars = random.randint(1, 3)
                characters = random.sample(self.demo_characters, num_chars)
            
            # Generar nombre de archivo realista
            timestamp = datetime.now() - timedelta(days=random.randint(0, 365))
            file_name = f"{creator}_{platform}_{timestamp.strftime('%Y%m%d')}_{i+1:03d}.mp4"
            file_path = str(config.VIDEOS_BASE_PATH / creator / file_name)
            
            # Crear datos del video
            video_data = {
                'file_path': file_path,
                'file_name': file_name,
                'creator_name': creator.replace('_', ' ').title(),
                'platform': platform,
                'file_size': random.randint(5000000, 50000000),  # 5MB - 50MB
                'duration_seconds': random.randint(15, 180),  # 15s - 3min
                
                # Música (si aplica)
                'detected_music': music if has_music else None,
                'detected_music_artist': artist if has_music else None,
                'detected_music_confidence': random.uniform(0.7, 0.95) if has_music else None,
                'music_source': random.choice(['youtube', 'spotify', 'acrcloud']) if has_music else None,
                
                # Personajes
                'detected_characters': characters if characters else [],
                
                # Estado de edición
                'edit_status': random.choice(self.edit_statuses),
                'difficulty_level': random.choice(self.difficulty_levels) if random.random() > 0.3 else None,
                'notes': self.generate_demo_notes() if random.random() > 0.7 else None,
                
                'processing_status': 'completado'
            }
            
            # Algunos videos tendrán edición manual
            if random.random() > 0.8:
                video_data['final_music'] = f"Versión editada de {music}"
                video_data['final_music_artist'] = artist
                video_data['final_characters'] = characters + ['Personaje adicional']
            
            demo_videos.append(video_data)
        
        return demo_videos
    
    def generate_demo_notes(self):
        """Generar notas de ejemplo"""
        notes_examples = [
            "Excelente coreografía, fácil de seguir",
            "Necesita más práctica en los movimientos",
            "Muy viral, replicar pronto",
            "Buena sincronización con la música",
            "Efectos especiales interesantes",
            "Tendencia emergente, monitorear",
            "Dificultad alta, para dancers experimentados",
            "Concept único, vale la pena estudiar",
            "Perfecto para contenido de fin de semana",
            "Requiere espacio amplio para ejecutar"
        ]
        
        return random.choice(notes_examples)
    
    def insert_demo_data(self, videos):
        """Insertar datos de demostración en la base de datos"""
        print("💾 Insertando datos en la base de datos...")
        
        success_count = 0
        error_count = 0
        
        for video_data in videos:
            try:
                video_id = db.add_video(video_data)
                success_count += 1
                
                if success_count % 10 == 0:
                    print(f"  ✓ {success_count} videos insertados...")
                    
            except Exception as e:
                error_count += 1
                print(f"  ✗ Error insertando video: {e}")
        
        print(f"✅ Inserción completada: {success_count} exitosos, {error_count} errores")
        return success_count
    
    def create_demo_thumbnails(self, count: int = 10):
        """Crear thumbnails de demostración"""
        print(f"🖼️ Creando {count} thumbnails de demostración...")
        
        from src.thumbnail_generator import ThumbnailGenerator
        from PIL import Image, ImageDraw, ImageFont
        import colorsys
        
        # Asegurar que el directorio existe
        config.THUMBNAILS_PATH.mkdir(parents=True, exist_ok=True)
        
        created_count = 0
        
        for i in range(count):
            try:
                # Generar imagen de placeholder
                size = config.THUMBNAIL_SIZE
                
                # Color aleatorio
                hue = random.random()
                saturation = 0.7
                lightness = 0.5
                rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
                bg_color = tuple(int(c * 255) for c in rgb)
                
                # Crear imagen
                img = Image.new('RGB', size, bg_color)
                draw = ImageDraw.Draw(img)
                
                # Añadir texto
                try:
                    font = ImageFont.truetype("arial.ttf", 24)
                except:
                    font = ImageFont.load_default()
                
                text = f"Demo {i+1}"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (size[0] - text_width) // 2
                y = (size[1] - text_height) // 2
                
                # Sombra
                draw.text((x+2, y+2), text, fill=(0, 0, 0), font=font)
                # Texto principal
                draw.text((x, y), text, fill=(255, 255, 255), font=font)
                
                # Guardar
                thumbnail_path = config.THUMBNAILS_PATH / f"demo_video_{i+1:03d}_thumb.jpg"
                img.save(thumbnail_path, 'JPEG', quality=85)
                
                created_count += 1
                
            except Exception as e:
                print(f"  ✗ Error creando thumbnail {i+1}: {e}")
        
        print(f"✅ {created_count} thumbnails creados")
        return created_count
    
    def generate_statistics_report(self):
        """Generar reporte de estadísticas después de la demo"""
        print("📊 Generando reporte de estadísticas...")
        
        try:
            stats = db.get_stats()
            creators = db.get_unique_creators()
            music_tracks = db.get_unique_music()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'demo_data': True,
                'statistics': {
                    'total_videos': stats['total_videos'],
                    'videos_by_status': stats['by_status'],
                    'videos_by_platform': stats['by_platform'],
                    'videos_with_music': stats['with_music'],
                    'videos_with_characters': stats['with_characters'],
                    'unique_creators': len(creators),
                    'unique_music_tracks': len(music_tracks)
                },
                'top_creators': creators[:10],
                'top_music': music_tracks[:10]
            }
            
            # Guardar reporte
            report_path = f"demo_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Reporte guardado: {report_path}")
            
            # Mostrar resumen en consola
            print("\n📈 ESTADÍSTICAS DE DEMOSTRACIÓN")
            print("-" * 40)
            print(f"Videos totales: {stats['total_videos']}")
            print(f"Con música: {stats['with_music']}")
            print(f"Con personajes: {stats['with_characters']}")
            print(f"Creadores únicos: {len(creators)}")
            print(f"Tracks musicales: {len(music_tracks)}")
            
            if stats['by_status']:
                print("\nPor estado:")
                for status, count in stats['by_status'].items():
                    print(f"  {status}: {count}")
            
            if stats['by_platform']:
                print("\nPor plataforma:")
                for platform, count in stats['by_platform'].items():
                    print(f"  {platform}: {count}")
            
            return report
            
        except Exception as e:
            print(f"❌ Error generando reporte: {e}")
            return None
    
    def run_demo_generation(self, video_count: int = 50):
        """Ejecutar generación completa de demostración"""
        print("🎭 Tag-Flow V2 - Generador de Datos de Demostración")
        print("=" * 55)
        
        # Verificar base de datos
        try:
            config.ensure_directories()
            
            # Verificar si ya hay datos
            existing_stats = db.get_stats()
            if existing_stats['total_videos'] > 0:
                print(f"⚠️  Ya existen {existing_stats['total_videos']} videos en la base de datos")
                overwrite = input("¿Añadir datos de demostración de todas formas? [Y/n]: ").lower()
                if overwrite == 'n':
                    print("❌ Operación cancelada")
                    return
            
            # Generar datos
            print(f"\n1️⃣  Generando {video_count} videos de demostración...")
            demo_videos = self.generate_demo_videos(video_count)
            
            print("\n2️⃣  Insertando en base de datos...")
            inserted_count = self.insert_demo_data(demo_videos)
            
            print("\n3️⃣  Creando thumbnails de demostración...")
            self.create_demo_thumbnails(min(inserted_count, 20))
            
            print("\n4️⃣  Generando reporte estadístico...")
            self.generate_statistics_report()
            
            print("\n" + "✅" + "=" * 53 + "✅")
            print("   ¡DATOS DE DEMOSTRACIÓN GENERADOS EXITOSAMENTE!")
            print("✅" + "=" * 53 + "✅")
            
            print("\n🎯 Próximos pasos:")
            print("   1. Lanzar interfaz web: python app.py")
            print("   2. Abrir: http://localhost:5000")
            print("   3. Explorar la galería con datos de ejemplo")
            print("   4. Probar filtros y funciones de edición")
            
            print("\n💡 Nota:")
            print("   • Estos son datos de demostración (archivos de video no existen)")
            print("   • Para uso real, procesa videos reales con: python main.py")
            print("   • Los thumbnails son placeholders para mostrar la interfaz")
            
            return True
            
        except Exception as e:
            print(f"❌ Error durante generación de demo: {e}")
            return False

def main():
    """Función principal"""
    generator = DemoDataGenerator()
    
    print("🎬 ¿Cuántos videos de demostración quieres generar?")
    print("   Recomendado: 50 videos (buena variedad)")
    print("   Rápido: 20 videos (demo básica)")
    print("   Completo: 100 videos (demo extensa)")
    
    try:
        count_input = input("\nCantidad [50]: ").strip()
        count = int(count_input) if count_input else 50
        
        if count <= 0 or count > 500:
            print("❌ Cantidad inválida (1-500)")
            return
            
    except ValueError:
        print("❌ Cantidad inválida")
        return
    
    # Ejecutar generación
    success = generator.run_demo_generation(count)
    
    if not success:
        print("\n❌ Generación de demo falló")
        print("   Verificar: python check_installation.py")

if __name__ == "__main__":
    main()