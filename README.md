# 🎬 Tag-Flow V2 - Sistema de Gestión de Videos TikTok/MMD

**Sistema completo para catalogar, analizar y gestionar videos de TikTok trends y MMDs de videojuegos con reconocimiento automático de música y personajes.**

## 🚀 Características Principales

- **Múltiples Fuentes de Datos**: Integración con 4K Video Downloader+, 4K Tokkit, 4K Stogram y carpetas organizadas
- **Reconocimiento Musical Híbrido**: YouTube API + Spotify API + ACRCloud
- **Reconocimiento Facial Avanzado**: Google Vision (famosos) + DeepFace GPU (personajes anime/gaming)
- **Interfaz Web Moderna**: Flask + Bootstrap 5 con edición en tiempo real
- **Procesamiento Específico**: Análisis por plataforma (YouTube, TikTok, Instagram)
- **Gestión Granular**: Poblado y mantenimiento de BD y thumbnails por fuente/plataforma
- **Thumbnails Automáticos**: Generación optimizada con watermarks
- **Gestión de Estados**: Seguimiento del progreso de edición de videos

## 📋 Requisitos

### Software Base
- **Python 3.12+**
- **FFmpeg** (para procesamiento de audio/video)
- **GPU NVIDIA** (opcional, para DeepFace acelerado)

### APIs Requeridas (Gratuitas)
- **YouTube Data API v3** - [Obtener clave](https://console.developers.google.com/)
- **Spotify Web API** - [Crear app](https://developer.spotify.com/dashboard/)
- **Google Vision API** - [Configurar proyecto](https://console.cloud.google.com/)

### Fuentes de Datos Soportadas
- **4K Video Downloader+**: Videos de YouTube
- **4K Tokkit**: Videos de TikTok
- **4K Stogram**: Contenido de Instagram
- **Carpetas Organizadas**: `D:\4K All\{Youtube|Tiktok|Instagram}\{Creador}\`

## 🛠️ Instalación

### 🚀 Instalación Rápida (Recomendada)

```bash
cd Tag-Flow

# Instalación completamente automática
python quickstart.py
```

### ⚡ Instalación Manual

```bash
cd Tag-Flow
pip install -r requirements.txt

# Copiar plantilla de configuración
copy .env.example .env

# Editar .env con tus claves de API
# Ver COMANDOS.md para configuración detallada
```

### 🛡️ Instalacion Segura Con Entorno Virtual
```bash
cd Tag-Flow
python -m venv tag-flow-env
tag-flow-env\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python main.py
python app.py
```

## 🎯 Uso Básico

### Comandos Principales

```bash
# Ver estadísticas de todas las fuentes
python maintenance.py show-stats

# Poblar BD desde fuentes externas
python maintenance.py populate-db --source all --limit 10

# Generar thumbnails
python maintenance.py populate-thumbnails

# Procesar videos específicos por plataforma
python main.py 5 YT    # 5 videos de YouTube
python main.py 3 TT    # 3 videos de TikTok
python main.py 2 IG    # 2 videos de Instagram

# Lanzar interfaz web
python app.py
```

### Códigos de Plataforma

- **YT**: YouTube (4K Video Downloader+)
- **TT**: TikTok (4K Tokkit)
- **IG**: Instagram (4K Stogram)
- **O**: Carpetas organizadas (`D:\4K All`)

## 📊 Flujo de Trabajo Recomendado

### 1️⃣ Configuración Inicial
```bash
# 1. Ver fuentes disponibles
python maintenance.py show-stats

# 2. Poblar con algunos videos de prueba
python maintenance.py populate-db --source db --platform youtube --limit 10

# 3. Generar thumbnails
python maintenance.py populate-thumbnails --platform youtube
```

### 2️⃣ Uso Diario
```bash
# Procesar videos nuevos por plataforma
python main.py 10 YT

# Gestionar en interfaz web
python app.py  # → http://localhost:5000
```

### 3️⃣ Mantenimiento
```bash
# Backup periódico
python maintenance.py backup

# Optimizar base de datos
python maintenance.py optimize-db
```

## 📂 Estructura del Proyecto

```
Tag-Flow-V2/
├── 📄 DOCUMENTACIÓN
│   ├── README.md                      # Esta guía
│   ├── PROYECTO_ESTADO.md             # Estado y roadmap
│   ├── COMANDOS.md                    # Referencia completa de comandos
│   └── .env.example                   # Plantilla de configuración
│
├── 🚀 SCRIPTS PRINCIPALES
│   ├── main.py                        # Procesamiento de videos
│   ├── app.py                         # Interfaz web Flask
│   └── maintenance.py                 # Herramientas de mantenimiento
│
├── 🧠 CÓDIGO FUENTE
│   └── src/
│       ├── __init__.py                # Inicialización del paquete
│       ├── database.py                # Gestión SQLite
│       ├── downloader_integration.py  # Integración con 4K Video Downloader+
│       ├── external_sources.py        # Fuentes externas (NUEVO)
│       ├── video_processor.py         # Procesamiento videos
│       ├── music_recognition.py       # APIs musicales
│       ├── face_recognition.py        # Reconocimiento facial
│       └── thumbnail_generator.py     # Generación thumbnails
│
├── 🌐 INTERFAZ WEB
│   ├── templates/                     # HTML templates
│   └── static/                        # CSS, JS, iconos
│
├── 💾 DATOS
│   └── data/
│       ├── videos.db                  # Base de datos SQLite
│       └── thumbnails/                # Thumbnails generados
│
└── 🎭 RECONOCIMIENTO FACIAL
    └── caras_conocidas/               # Fotos de referencia por categoría
```

## ⚙️ Configuración

### Variables de Entorno Principales

Copia `.env.example` a `.env` y configura:

```env
# APIs (obligatorias)
YOUTUBE_API_KEY="tu_clave_aqui"
SPOTIFY_CLIENT_ID="tu_client_id"
SPOTIFY_CLIENT_SECRET="tu_client_secret"

# Fuentes externas (automáticas)
EXTERNAL_YOUTUBE_DB="C:/Users/.../4K Video Downloader+/.../xxx.sqlite"
EXTERNAL_TIKTOK_DB="D:/4K Tokkit/data.sqlite"
EXTERNAL_INSTAGRAM_DB="D:/4K Stogram/.stogram.sqlite"
ORGANIZED_BASE_PATH="D:/4K All"
```

## 📈 Costos y Límites

### APIs Gratuitas
- **YouTube API**: 10,000 consultas/día
- **Spotify API**: Rate limits generosos
- **ACRCloud**: 3,000 consultas/mes

### APIs de Pago (Opcionales)
- **Google Vision**: $1.50 por 1,000 detecciones
- **Estimado mensual**: $0-5 para uso moderado

## 🔧 Solución de Problemas

### Verificar Configuración
```bash
python verify_config.py
```

### Problemas Comunes

**Error: "ModuleNotFoundError"**
```bash
pip install -r requirements.txt
```

**No se encuentran videos**
- Verifica que las rutas en `.env` sean correctas
- Usa `python maintenance.py show-stats` para verificar fuentes

**APIs no funcionan**
- Verifica claves en `.env`
- Confirma que las APIs estén habilitadas en sus respectivas consolas

## 📚 Documentación Adicional

- **[COMANDOS.md](COMANDOS.md)**: Referencia completa de todos los comandos
- **[PROYECTO_ESTADO.md](PROYECTO_ESTADO.md)**: Estado actual y roadmap del proyecto

## 🤝 Soporte

- **Documentación**: Ver archivos .md en el proyecto
- **Logs**: Revisa `tag_flow_processing.log` para errores
- **Configuración**: Usa `python verify_config.py` para diagnosticar

---

**¡Disfruta gestionando tus videos de TikTok y MMDs con Tag-Flow V2! 🎬✨**