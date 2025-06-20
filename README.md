# 🎬 Tag-Flow - Sistema de Clasificación de Videos

Sistema automatizado de dos componentes para clasificar y explorar colecciones de videos de manera visual e interactiva.

## 📋 Descripción

Tag-Flow transforma una estructura de carpetas de videos en una base de datos visual y consultable mediante:

- **🔍 Análisis automático**: Extrae creador, personajes y música de cada video
- **🏷️ Etiquetado manual**: Permite asignar dificultad de edición de forma eficiente  
- **📊 Visualización interactiva**: Interfaz web con filtros múltiples para explorar la colección
- **⚡ Escalabilidad**: Procesa solo videos nuevos, sin reprocesar la colección completa

## 🚀 Instalación Rápida

### 1. Crear entorno virtual (recomendado)
```bash
python -m venv tag-flow-env
tag-flow-env\Scripts\activate  # Windows
# source tag-flow-env/bin/activate  # Linux/Mac
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar API de música (opcional)
Edita el archivo `.env` y añade tu clave de API:
```
API_KEY_MUSICA="tu_clave_real_aqui"
```

**APIs de música recomendadas:**
- [ACRCloud](https://www.acrcloud.com/) - 500 consultas gratis/mes
- [AudD](https://audd.io/) - 1000 consultas gratis/mes

## 📁 Estructura del Proyecto

```
Tag-Flow/
├── 1_script_analisis.py     # 🔧 Backend - Procesamiento de videos
├── 2_app_visual.py          # 🌐 Frontend - Aplicación web
├── .env                     # 🔐 Configuración de API
├── requirements.txt         # 📦 Dependencias Python
│
├── data/
│   └── videos.csv          # 💾 Base de datos de videos
│
├── caras_conocidas/        # 👥 Fotos de referencia para reconocimiento
│   ├── personaje_1.jpg
│   ├── personaje_2.png
│   └── ...
│
└── videos_a_procesar/      # 📹 Videos organizados por creador
    ├── Creador_A/
    │   ├── video_001.mp4
    │   └── video_002.mp4
    ├── Creador_B/
    │   └── video_003.mp4
    └── ...
```

## 🎯 Guía de Uso

### Paso 1: Preparar reconocimiento de personajes
1. Coloca fotos claras de cada personaje en `caras_conocidas/`
2. Nombra los archivos como quieres que aparezca el personaje (ej: `Pedro.jpg`)
3. Usa fotos con una sola cara visible y buena calidad

### Paso 2: Organizar videos
1. Crea carpetas por creador dentro de `videos_a_procesar/`
2. Coloca los videos dentro de la carpeta correspondiente:
   ```
   videos_a_procesar/
   ├── MiCreadorFavorito/
   │   ├── video_aventura.mp4
   │   └── video_comedia.mp4
   └── OtroCreador/
       └── video_tutorial.mp4
   ```

### Paso 3: Procesar videos (Backend)
```bash
python 1_script_analisis.py
```
El script:
- ✅ Detecta automáticamente videos nuevos
- 🎵 Analiza la música (si tienes API configurada)
- 👥 Reconoce personajes usando las fotos de referencia
- 📝 Te pregunta la dificultad de edición para cada video
- 💾 Guarda todo en `data/videos.csv`

### Paso 4: Explorar videos (Frontend)
```bash
streamlit run 2_app_visual.py
```
Se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 🔧 Características Avanzadas

### Filtros Disponibles
- **👤 Creadores**: Filtra por quién hizo el video
- **⚡ Dificultad**: Alto, medio o bajo nivel de edición
- **🎭 Personajes**: Por personajes detectados automáticamente
- **🔤 Búsqueda libre**: Busca en nombres, música, personajes, etc.

### Funciones Inteligentes
- **🔄 Procesamiento incremental**: Solo analiza videos nuevos
- **💾 Guardado automático**: No pierdes progreso si interrumpes el proceso
- **📊 Estadísticas en tiempo real**: Ve métricas mientras filtras
- **📱 Responsive**: Funciona en móviles y tablets

## 🎵 Configuración Correcta de ACRCloud para Tag-Flow

### Paso 1: Crear Aplicación de Audio Recognition

1. **Ve a [ACRCloud Console](https://console.acrcloud.com/)**
2. **Haz clic en "Create Application"**
3. **Selecciona "Audio & Video Recognition"** (NO "Audio Bucket")
4. **Configura así:**
   ```
   Application Name: Tag-Flow-Music-Recognition
   Application Type: Audio & Video Recognition
   Audio Type: Music
   Platform: Other
   ```

### Paso 2: Obtener Credenciales Correctas

Después de crear la aplicación, tendrás:
- **Host**: `identify-eu-west-1.acrcloud.com` (o similar)
- **Access Key**: Tu clave de acceso
- **Access Secret**: Tu clave secreta

### Paso 3: Configurar .env

Tu archivo `.env` debe verse así:
```bash
# Configuración ACRCloud para reconocimiento de música
ACRCLOUD_HOST="identify-eu-west-1.acrcloud.com"
ACRCLOUD_ACCESS_KEY="tu_access_key_aqui"
ACRCLOUD_ACCESS_SECRET="tu_access_secret_aqui"

# Configuraciones opcionales (mantener como están)
PROCESAR_CADA_N_FRAMES=30
DURACION_CLIP_AUDIO=15
```

## 🔗 Enlaces Útiles

- **ACRCloud Console**: https://console.acrcloud.com/
- **Documentación API**: https://docs.acrcloud.com/
- **Límites gratuitos**: 500 identificaciones/mes

### Formatos de video soportados
- MP4, MOV, AVI, MKV, WMV, FLV, WebM

### Formatos de imagen para caras
- JPG, PNG, JPEG

## 🐛 Solución de Problemas

### Error: "face_recognition no funciona"
```bash
# Windows: Instalar Visual C++ Build Tools
# Luego reinstalar:
pip uninstall face_recognition
pip install face_recognition
```

### Error: "No se puede cargar el video"
- Verifica que la ruta no tenga caracteres especiales
- Prueba mover el video a una carpeta con ruta más corta
- Asegúrate de que el formato sea compatible

### Videos no aparecen en la aplicación
1. Ejecuta primero `python 1_script_analisis.py`
2. Verifica que se haya creado `data/videos.csv`
3. Recarga la página web de Streamlit

### API de música no funciona
- Verifica que la clave API en `.env` sea correcta
- Comprueba que no hayas superado tu límite de consultas
- El sistema funciona sin API, solo mostrará "API no configurada"

## ✨ Nuevas Características

- [x] **✏️ Editor integrado**: Modifica datos directamente desde la web (¡YA DISPONIBLE!)
  - Edita creador, personajes, música y dificultad sin reprocesar
  - Validación inteligente y guardado automático
  - Historial de ediciones con timestamps
  - Ver [EDITOR_INTEGRADO.md](EDITOR_INTEGRADO.md) para guía completa

## 📈 Mejoras Futuras

- [ ] **Exportación**: Generar reportes en PDF/Excel
- [ ] **Análisis de sentimientos**: Detectar emociones en videos
- [ ] **Tags personalizados**: Sistema de etiquetas libres
- [ ] **Comparación de creadores**: Análisis estadístico avanzado

## 🤝 Contribuir

¿Ideas para mejorar Tag-Flow? 
1. Crea un issue con tu sugerencia
2. Fork el proyecto
3. Crea tu feature branch
4. Envía un pull request

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🆘 Soporte

Si tienes problemas:
1. Revisa esta documentación
2. Verifica la sección de solución de problemas
3. Crea un issue con detalles del error

---
**¡Disfruta clasificando y explorando tu colección de videos con Tag-Flow! 🎬✨**
