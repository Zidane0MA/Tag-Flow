# 🎬 Tag-Flow V2 - Sistema de Gestión de Videos TikTok/MMD

**Sistema completo para catalogar, analizar y gestionar videos de TikTok trends y MMDs de videojuegos con reconocimiento automático de música y personajes.**

## 🚀 Características Principales

- **Reconocimiento Musical Híbrido**: YouTube API + Spotify API + ACRCloud
- **Reconocimiento Facial Avanzado**: Google Vision (famosos) + DeepFace GPU (personajes anime/gaming)
- **Interfaz Web Moderna**: Flask + Bootstrap 5 con edición en tiempo real
- **Integración 4K Downloader**: Importa automáticamente metadatos de creadores
- **Thumbnails Automáticos**: Generación optimizada con watermarks
- **Gestión de Estados**: Seguimiento del progreso de edición de videos
- **Filtros Avanzados**: Búsqueda inteligente y filtrado en tiempo real

## 📋 Requisitos

### Software Base
- **Python 3.12+**
- **FFmpeg** (para procesamiento de audio/video)
- **GPU NVIDIA** (opcional, para DeepFace acelerado)

### APIs Requeridas (Gratuitas)
- **YouTube Data API v3** - [Obtener clave](https://console.developers.google.com/)
- **Spotify Web API** - [Crear app](https://developer.spotify.com/dashboard/)
- **Google Vision API** - [Configurar proyecto](https://console.cloud.google.com/)

## 🛠️ Instalación

### 🚀 Opción 1: Instalación Automática (Recomendada)

```bash
cd Tag-Flow-V2

# Instalación completamente automática
python quickstart.py
```

**El script te preguntará:**
- ¿Crear entorno virtual? (Recomendado: sí)
- Configuración de APIs paso a paso
- Creación de datos de ejemplo

### ⚡ Opción 2: Sin Entorno Virtual (Más Simple)

Si tienes Python limpio y quieres máxima simplicidad:

```bash
cd Tag-Flow-V2
pip install -r requirements.txt
python setup.py          # Configurar APIs
python generate_demo.py  # Datos de ejemplo
python app.py            # Lanzar interfaz
```

**➜ Abrir:** http://localhost:5000

### 🔧 Opción 3: Manual Completa

```bash
cd Tag-Flow-V2

# Crear entorno virtual (recomendado)
python -m venv tag-flow-env
tag-flow-env\Scripts\activate  # Windows
# source tag-flow-env/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar APIs

**Automático:**
```bash
python setup.py  # Configuración guiada interactiva
```

**Manual:**
Edita el archivo `.env` con tus claves de API:

```env
# YouTube Data API (GRATIS - 10k consultas/día)
YOUTUBE_API_KEY="tu_clave_youtube_aqui"

# Google Vision API  
GOOGLE_APPLICATION_CREDENTIALS="config/gcp_credentials.json"

# Spotify API (GRATIS)
SPOTIFY_CLIENT_ID="tu_spotify_client_id"
SPOTIFY_CLIENT_SECRET="tu_spotify_client_secret"

# Rutas de trabajo (actualizar según tu configuración)
VIDEOS_BASE_PATH="D:/Videos_TikTok"
DOWNLOADER_DB_PATH="C:/Users/tuuser/AppData/Local/4kdownload.com/..."
```

### 4. Configurar caras conocidas (opcional)

Añade fotos de referencia de personajes en:
```
caras_conocidas/
├── genshin/
│   ├── zhongli.jpg
│   └── raiden.jpg
└── honkai/
    ├── firefly.jpg
    └── blade.jpg
```

## 🎯 Uso

### Procesamiento de Videos

1. **Analizar videos nuevos:**
```bash
python main.py
```

Este comando:
- Escanea carpetas configuradas
- Extrae metadatos de videos
- Genera thumbnails automáticos
- Reconoce música con múltiples APIs
- Detecta personajes/caras conocidas
- Actualiza la base de datos

### Interfaz Web

2. **Lanzar aplicación web:**
```bash
python app.py
```

Accede a: http://localhost:5000

### Funcionalidades Web

- **Galería Visual**: Vista en grid con thumbnails y filtros
- **Edición Inline**: Click para editar música, personajes, estado
- **Filtros Avanzados**: Por creador, plataforma, estado, dificultad
- **Búsqueda Inteligente**: Texto libre en múltiples campos
- **Gestión de Estados**: Marcar como pendiente/en proceso/completado
- **Abrir Carpetas**: Botón para abrir la ubicación del video

## 📊 Estructura del Proyecto

```
Tag-Flow-V2/
├── config.py                    # Configuración central
├── main.py                      # Script de procesamiento
├── app.py                       # Aplicación Flask
├── requirements.txt             # Dependencias
├── .env                         # Configuración de APIs
│
├── src/                         # Código fuente
│   ├── database.py              # Gestión SQLite
│   ├── video_processor.py       # Procesamiento videos
│   ├── music_recognition.py     # APIs musicales
│   ├── face_recognition.py      # Reconocimiento facial
│   ├── thumbnail_generator.py   # Generación thumbnails
│   └── downloader_integration.py # 4K Downloader
│
├── templates/                   # Templates HTML
│   ├── base.html               # Template base
│   ├── gallery.html            # Galería principal
│   └── error.html              # Páginas de error
│
├── static/                     # Archivos estáticos
│   ├── css/                    # Estilos CSS
│   ├── js/                     # JavaScript
│   └── icons/                  # Iconos
│
├── data/                       # Datos de la aplicación
│   ├── videos.db              # Base de datos principal
│   └── thumbnails/            # Thumbnails generados
│
├── caras_conocidas/           # Fotos de referencia
│   ├── genshin/               # Personajes Genshin Impact
│   └── honkai/                # Personajes Honkai Star Rail
│
└── videos_procesados/         # Videos organizados (salida)
```

## 🎛️ Configuración Avanzada

### Variables de Entorno Disponibles

```env
# Procesamiento
THUMBNAIL_SIZE="320x180"              # Tamaño de thumbnails
MAX_CONCURRENT_PROCESSING=3           # Videos en paralelo
USE_GPU_DEEPFACE=true                 # Usar GPU para DeepFace
DEEPFACE_MODEL="ArcFace"              # Modelo de reconocimiento

# Flask
FLASK_ENV="development"               # Modo de desarrollo
FLASK_DEBUG=true                      # Debug activado
FLASK_HOST="localhost"                # Host de la aplicación
FLASK_PORT=5000                       # Puerto de la aplicación

# Rutas personalizadas
VIDEOS_BASE_PATH="D:/Videos_TikTok"   # Carpeta de videos a analizar
THUMBNAILS_PATH="D:/Tag-Flow/data/thumbnails"
PROCESSED_VIDEOS_PATH="D:/Tag-Flow/videos_procesados"
```

### Integración con 4K Video Downloader

Para usar la integración automática:

1. Instala 4K Video Downloader
2. Encuentra la ruta de su base de datos SQLite
3. Configura `DOWNLOADER_DB_PATH` en `.env`
4. Los creadores y metadatos se importarán automáticamente

Rutas típicas:
- **Windows**: `C:/Users/username/AppData/Local/4kdownload.com/...`
- **macOS**: `~/Library/Application Support/4kdownload.com/...`

## 🧪 Testing y Desarrollo

### Verificar Configuración

```bash
python -c "from config import config; print('✅ Configuración cargada correctamente')"
```

### Probar APIs

```bash
# Probar reconocimiento musical
python -c "from src.music_recognition import music_recognizer; print('✅ APIs musicales:', music_recognizer.youtube is not None)"

# Probar reconocimiento facial  
python -c "from src.face_recognition import face_recognizer; print('✅ APIs faciales:', face_recognizer.vision_client is not None)"
```

### Logs de Debugging

Los logs se guardan en:
- `tag_flow_processing.log` - Procesamiento de videos
- Consola de Flask - Aplicación web

## 📈 Costos y Límites

### APIs Gratuitas
- **YouTube API**: 10,000 consultas/día (GRATIS)
- **Spotify API**: Rate limits generosos (GRATIS)
- **ACRCloud**: 3,000 consultas/mes (GRATIS)

### APIs de Pago
- **Google Vision**: $1.50 por 1,000 detecciones
- **Estimado mensual**: $3-5 para 200 videos/mes

### Hardware Local (GRATIS)
- **DeepFace**: Usa tu GPU local
- **SQLite**: Base de datos local
- **FFmpeg**: Procesamiento local

## 🔧 Solución de Problemas

### Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Error: "YouTube API key invalid"
1. Verifica que la clave esté en `.env`
2. Confirma que YouTube Data API v3 esté habilitada
3. Revisa los límites de cuota

### Error: "Google Vision credentials"
1. Descarga el archivo JSON de credenciales
2. Guárdalo en `config/gcp_credentials.json`
3. Verifica la variable `GOOGLE_APPLICATION_CREDENTIALS`

### Error: "DeepFace model download"
- Los modelos se descargan automáticamente en el primer uso
- Requiere conexión a internet estable
- Se guardan en `data/deepface_models/`

### Rendimiento Lento
- Reduce `MAX_CONCURRENT_PROCESSING`
- Desactiva `USE_GPU_DEEPFACE` si hay problemas con GPU
- Usa SSD para mejor rendimiento de thumbnails

## 🚧 Desarrollo Futuro

### Funcionalidades Planeadas
- [ ] Exportación a Excel/CSV
- [ ] API REST completa
- [ ] Dashboard de estadísticas
- [ ] Backup automático de base de datos
- [ ] Reconocimiento de música offline
- [ ] Integración con más plataformas
- [ ] Sistema de etiquetas personalizadas
- [ ] Análisis de tendencias

### Contribuir
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🤝 Soporte

- **Documentación**: Este README
- **Issues**: Abre un issue en GitHub
- **Logs**: Revisa `tag_flow_processing.log`

---

**¡Disfruta gestionando tus videos de TikTok y MMDs con Tag-Flow V2! 🎬✨**