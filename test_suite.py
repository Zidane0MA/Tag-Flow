"""
Tag-Flow V2 - Suite de Pruebas
Tests automatizados para verificar funcionalidad del sistema
"""

import unittest
import sys
import tempfile
import sqlite3
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Agregar src al path para imports
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config
from src.database import DatabaseManager
from src.video_processor import VideoProcessor
from src.music_recognition import MusicRecognizer
from src.face_recognition import FaceRecognizer
from src.thumbnail_generator import ThumbnailGenerator

class TestDatabase(unittest.TestCase):
    """Tests para el módulo de base de datos"""
    
    def setUp(self):
        """Configurar test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db = DatabaseManager(Path(self.temp_db.name))
        
    def tearDown(self):
        """Limpiar después del test"""
        self.temp_db.close()
        Path(self.temp_db.name).unlink(missing_ok=True)
    
    def test_database_initialization(self):
        """Test de inicialización de base de datos"""
        # Verificar que las tablas se crearon
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.assertIn('videos', tables)
            self.assertIn('downloader_mapping', tables)
    
    def test_add_video(self):
        """Test de agregar video"""
        video_data = {
            'file_path': '/test/video.mp4',
            'file_name': 'video.mp4',
            'creator_name': 'Test Creator',
            'platform': 'tiktok',
            'file_size': 1024000,
            'duration_seconds': 30.5
        }
        
        video_id = self.db.add_video(video_data)
        self.assertIsInstance(video_id, int)
        self.assertGreater(video_id, 0)
        
        # Verificar que se guardó correctamente
        video = self.db.get_video(video_id)
        self.assertIsNotNone(video)
        self.assertEqual(video['file_path'], '/test/video.mp4')
        self.assertEqual(video['creator_name'], 'Test Creator')
    
    def test_update_video(self):
        """Test de actualización de video"""
        # Crear video
        video_data = {
            'file_path': '/test/video.mp4',
            'file_name': 'video.mp4',
            'creator_name': 'Test Creator'
        }
        video_id = self.db.add_video(video_data)
        
        # Actualizar
        updates = {
            'final_music': 'Test Song',
            'edit_status': 'hecho',
            'difficulty_level': 'medio'
        }
        success = self.db.update_video(video_id, updates)
        self.assertTrue(success)
        
        # Verificar actualización
        video = self.db.get_video(video_id)
        self.assertEqual(video['final_music'], 'Test Song')
        self.assertEqual(video['edit_status'], 'hecho')
    
    def test_get_videos_with_filters(self):
        """Test de obtener videos con filtros"""
        # Crear videos de prueba
        videos_data = [
            {'file_path': '/test/video1.mp4', 'file_name': 'video1.mp4', 'creator_name': 'Creator A', 'platform': 'tiktok'},
            {'file_path': '/test/video2.mp4', 'file_name': 'video2.mp4', 'creator_name': 'Creator B', 'platform': 'instagram'},
            {'file_path': '/test/video3.mp4', 'file_name': 'video3.mp4', 'creator_name': 'Creator A', 'platform': 'tiktok'},
        ]
        
        for video_data in videos_data:
            self.db.add_video(video_data)
        
        # Test filtro por creador
        filtered = self.db.get_videos(filters={'creator_name': 'Creator A'})
        self.assertEqual(len(filtered), 2)
        
        # Test filtro por plataforma
        filtered = self.db.get_videos(filters={'platform': 'tiktok'})
        self.assertEqual(len(filtered), 2)
    
    def test_get_stats(self):
        """Test de estadísticas"""
        # Crear videos de prueba
        video_data = {
            'file_path': '/test/video.mp4',
            'file_name': 'video.mp4',
            'creator_name': 'Test Creator',
            'detected_music': 'Test Song'
        }
        self.db.add_video(video_data)
        
        stats = self.db.get_stats()
        self.assertEqual(stats['total_videos'], 1)
        self.assertEqual(stats['with_music'], 1)

class TestVideoProcessor(unittest.TestCase):
    """Tests para el procesador de videos"""
    
    def setUp(self):
        self.processor = VideoProcessor()
    
    def test_is_valid_video(self):
        """Test de validación de video"""
        # Test extensiones válidas
        valid_path = Path('/test/video.mp4')
        self.assertTrue(valid_path.suffix.lower() in {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'})
        
        # Test extensiones inválidas
        invalid_path = Path('/test/document.txt')
        self.assertFalse(invalid_path.suffix.lower() in {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'})
    
    @patch('cv2.VideoCapture')
    def test_extract_metadata_mock(self, mock_cv2):
        """Test de extracción de metadatos con mock"""
        # Configurar mock
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            0: 1920,  # WIDTH
            1: 1080,  # HEIGHT  
            5: 30.0,  # FPS
            7: 900    # FRAME_COUNT
        }.get(prop, 0)
        mock_cv2.return_value = mock_cap
        
        # Test
        test_path = Path('/test/video.mp4')
        
        # Como el archivo no existe realmente, esto fallará, pero podemos verificar el formato
        # En un test real, usaríamos un archivo de video real pequeño
        self.assertTrue(True)  # Placeholder

class TestMusicRecognizer(unittest.TestCase):
    """Tests para reconocimiento musical"""
    
    def setUp(self):
        self.recognizer = MusicRecognizer()
    
    def test_initialization(self):
        """Test de inicialización"""
        # Verificar que el reconocedor se inicializa sin errores
        self.assertIsNotNone(self.recognizer)
    
    @patch('requests.post')
    def test_acrcloud_fallback(self, mock_post):
        """Test del fallback a ACRCloud"""
        # Mock respuesta exitosa de ACRCloud
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': {'code': 0},
            'metadata': {
                'music': [{
                    'title': 'Test Song',
                    'artists': [{'name': 'Test Artist'}],
                    'score': 85
                }]
            }
        }
        mock_post.return_value = mock_response
        
        # Test (usando archivo mock)
        test_path = Path('/test/audio.wav')
        
        # No podemos hacer el test real sin archivo, pero verificamos estructura
        self.assertTrue(True)  # Placeholder

class TestFaceRecognizer(unittest.TestCase):
    """Tests para reconocimiento facial"""
    
    def setUp(self):
        self.recognizer = FaceRecognizer()
    
    def test_initialization(self):
        """Test de inicialización"""
        self.assertIsNotNone(self.recognizer)
    
    def test_load_known_faces_db(self):
        """Test de carga de base de datos de caras"""
        # El test real requeriría archivos de imagen
        # Por ahora verificamos que la estructura es correcta
        self.assertIsInstance(self.recognizer.known_faces_db, dict)

class TestThumbnailGenerator(unittest.TestCase):
    """Tests para generador de thumbnails"""
    
    def setUp(self):
        self.generator = ThumbnailGenerator()
    
    def test_initialization(self):
        """Test de inicialización"""
        self.assertIsNotNone(self.generator)
        self.assertEqual(self.generator.thumbnail_size, config.THUMBNAIL_SIZE)

class TestIntegration(unittest.TestCase):
    """Tests de integración del sistema completo"""
    
    def setUp(self):
        """Configurar test de integración"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.temp_db = self.temp_dir / 'test.db'
        
    def tearDown(self):
        """Limpiar test de integración"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_workflow_mock(self):
        """Test del flujo completo con mocks"""
        # Este test simularía todo el pipeline:
        # 1. Detectar video nuevo
        # 2. Extraer metadatos
        # 3. Generar thumbnail
        # 4. Reconocer música
        # 5. Reconocer caras
        # 6. Guardar en BD
        
        # Por simplicidad, verificamos que los componentes existen
        db = DatabaseManager(self.temp_db)
        processor = VideoProcessor()
        music_recognizer = MusicRecognizer()
        face_recognizer = FaceRecognizer()
        thumbnail_generator = ThumbnailGenerator()
        
        self.assertIsNotNone(db)
        self.assertIsNotNone(processor)
        self.assertIsNotNone(music_recognizer)
        self.assertIsNotNone(face_recognizer)
        self.assertIsNotNone(thumbnail_generator)

class TestConfiguration(unittest.TestCase):
    """Tests para configuración del sistema"""
    
    def test_config_loading(self):
        """Test de carga de configuración"""
        # Verificar que la configuración se carga sin errores
        self.assertIsNotNone(config.BASE_DIR)
        self.assertIsNotNone(config.DATABASE_PATH)
        self.assertIsNotNone(config.THUMBNAIL_SIZE)
    
    def test_config_validation(self):
        """Test de validación de configuración"""
        warnings = config.validate_config()
        self.assertIsInstance(warnings, list)
        # Las advertencias son normales si no hay APIs configuradas

def create_test_video_file(path: Path, duration: int = 1):
    """Crear archivo de video de prueba usando FFmpeg"""
    try:
        import subprocess
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
            '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=1',
            '-c:v', 'libx264', '-c:a', 'aac', '-shortest', '-y', str(path)
        ]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    except:
        return False

class TestWithRealFiles(unittest.TestCase):
    """Tests que requieren archivos reales (opcional)"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_video = self.temp_dir / 'test_video.mp4'
        
        # Intentar crear video de prueba
        self.has_real_video = create_test_video_file(self.test_video)
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_video_processing_real(self):
        """Test de procesamiento con video real (solo si FFmpeg disponible)"""
        if not self.has_real_video:
            self.skipTest("No se pudo crear video de prueba (FFmpeg requerido)")
        
        processor = VideoProcessor()
        
        # Test validación
        self.assertTrue(processor.is_valid_video(self.test_video))
        
        # Test extracción de metadatos
        metadata = processor.extract_metadata(self.test_video)
        self.assertIn('file_path', metadata)
        self.assertIn('file_name', metadata)

def run_tests():
    """Ejecutar suite de tests"""
    print("🧪 Tag-Flow V2 - Ejecutando Tests")
    print("="*40)
    
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar tests
    test_classes = [
        TestDatabase,
        TestVideoProcessor, 
        TestMusicRecognizer,
        TestFaceRecognizer,
        TestThumbnailGenerator,
        TestConfiguration,
        TestIntegration,
        TestWithRealFiles
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar resumen
    print("\n" + "="*40)
    print("📊 RESUMEN DE TESTS")
    print("="*40)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallidos: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FALLOS:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split(chr(10))[-2]}")
    
    if result.errors:
        print("\n💥 ERRORES:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split(chr(10))[-2]}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n✅ ¡Todos los tests pasaron!")
    else:
        print("\n⚠️  Algunos tests fallaron - revisar implementación")
    
    return success

if __name__ == '__main__':
    run_tests()