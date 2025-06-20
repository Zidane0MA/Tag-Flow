# 🚀 TAG-FLOW V2 - GUÍA DE INSTALACIÓN RÁPIDA

## ⏱️ INSTALACIÓN EN 5 MINUTOS

### 1️⃣ **Requisitos Previos**
```bash
# Python 3.10+ (recomendado 3.12)
python --version

# FFmpeg (para procesamiento de video)
# Windows: Descargar de https://ffmpeg.org
# Agregar al PATH del sistema
```

### 2️⃣ **Configuración Automática**
```bash
# Clonar/descargar el proyecto
cd Tag-Flow-V2

# Activar entorno virtual
python -m venv tag-flow-env
tag-flow-env\Scripts\activate

# Instalación y configuración automática
python quickstart.py
```

**El script quickstart.py hará todo automáticamente:**
- ✅ Instalar dependencias
- ✅ Configurar APIs paso a paso
- ✅ Crear estructura de directorios
- ✅ Verificar instalación
- ✅ Generar datos de demostración

### 3️⃣ **Primera Ejecución**
```bash
# Generar datos de ejemplo para probar
python generate_demo.py

# Lanzar interfaz web
python app.py
```

**➜ Abrir:** http://localhost:5000

---

## 🔧 CONFIGURACIÓN MANUAL (ALTERNATIVA)

### APIs Requeridas (5 min de configuración)

#### YouTube Data API (Gratis)
1. Ir a: https://console.developers.google.com/
2. Crear proyecto → Habilitar "YouTube Data API v3"
3. Crear credenciales (API Key)

#### Spotify Web API (Gratis)  
1. Ir a: https://developer.spotify.com/dashboard/
2. Crear aplicación
3. Copiar Client ID y Client Secret

#### Google Vision API (Opcional - $1.50/1000 consultas)
1. Ir a: https://console.cloud.google.com/
2. Habilitar "Vision API"
3. Crear cuenta de servicio → Descargar JSON

### Configurar .env
```env
YOUTUBE_API_KEY="tu_clave_aqui"
SPOTIFY_CLIENT_ID="tu_client_id"
SPOTIFY_CLIENT_SECRET="tu_client_secret"
GOOGLE_APPLICATION_CREDENTIALS="config/gcp_credentials.json"
VIDEOS_BASE_PATH="D:/Videos_TikTok"
```

---

## 🎯 USO BÁSICO

### Procesar Videos Reales
```bash
# 1. Copiar videos a la carpeta configurada
# 2. Procesar automáticamente
python main.py

# 3. Ver resultados en la web
python app.py
```

### Comandos Útiles
```bash
# Verificar instalación
python check_installation.py

# Crear backup
python maintenance.py backup

# Migrar desde Tag-Flow V1
python migrate.py
```

---

## ❓ SOLUCIÓN DE PROBLEMAS

### Error: "Module not found"
```bash
pip install -r requirements.txt
```

### Error: "FFmpeg not found"
- Descargar FFmpeg
- Agregar al PATH del sistema
- Reiniciar terminal

### Error: API Keys
- Verificar que las claves están en .env
- Confirmar que las APIs están habilitadas
- Revisar límites de cuota

### No se procesan videos
- Verificar ruta en VIDEOS_BASE_PATH
- Formatos soportados: MP4, AVI, MOV, MKV, WebM
- Revisar logs: tag_flow_processing.log

---

## 🎉 ¡LISTO!

**Tag-Flow V2 está funcionando si puedes:**
- ✅ Abrir http://localhost:5000
- ✅ Ver la galería de videos
- ✅ Editar información de videos
- ✅ Usar filtros y búsqueda

**Para soporte completo ver:** README.md

---

**💡 Tip:** Ejecuta `python generate_demo.py` primero para ver el sistema funcionando con datos de ejemplo.