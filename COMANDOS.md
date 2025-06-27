# 📋 TAG-FLOW V2 - REFERENCIA COMPLETA DE COMANDOS

**Guía de referencia actualizada para todos los comandos disponibles en Tag-Flow V2, incluyendo las nuevas funcionalidades de Inteligencia de Personajes**

---

## 🚀 COMANDOS PRINCIPALES

### `main.py` - Procesamiento Inteligente de Videos

**Sintaxis:**
```bash
python main.py [límite] [plataforma]
```

**Ejemplos:**
```bash
# Procesamiento básico con IA mejorada
python main.py                    # Todos los videos nuevos con análisis inteligente
python main.py 20                 # Máximo 20 videos con detección de personajes

# Procesamiento específico por plataforma
python main.py 5 YT               # 5 videos de YouTube con análisis completo
python main.py 3 TT               # 3 videos de TikTok con mapeo de creadores
python main.py 2 IG               # 2 videos de Instagram con reconocimiento facial
python main.py 10 O               # 10 videos de carpetas organizadas
```

**Códigos de Plataforma:**
- **YT**: YouTube (4K Video Downloader+)
- **TT**: TikTok (4K Tokkit)
- **IG**: Instagram (4K Stogram)
- **O**: Carpetas organizadas (`D:\4K All`)

**Nuevo Procesamiento Inteligente:**
- ✅ **Análisis de títulos**: Detecta personajes por nombres en títulos
- ✅ **Mapeo de creadores**: Conecta automáticamente creadores con personajes
- ✅ **Reconocimiento visual**: DeepFace + Google Vision como respaldo
- ✅ **Priorización inteligente**: Análisis textual rápido antes que visual costoso

### `app.py` - Interfaz Web Mejorada

```bash
python app.py
```
- Lanza la interfaz web en http://localhost:5000
- **NUEVO**: Muestra personajes detectados automáticamente
- **NUEVO**: Filtros por personajes y fuente de detección
- Permite gestión visual y edición en tiempo real
- Dashboard con estadísticas de personajes y música

---

## 🛠️ COMANDOS DE MANTENIMIENTO EXPANDIDOS

### `maintenance.py` - Sistema de Gestión Avanzado

**Sintaxis:**
```bash
python maintenance.py [acción] [opciones]
```

---

### 📊 **Estadísticas y Diagnóstico**

#### `show-stats` - Estadísticas Completas de Fuentes
```bash
python maintenance.py show-stats
```
**Muestra:**
- Videos disponibles en todas las fuentes externas (1,244+ total)
- Estado de la base de datos Tag-Flow (234 videos procesados)
- Distribución por plataforma (YouTube: 506, TikTok: 417, Instagram: 92)
- Conexiones a fuentes externas y directorios

#### `character-stats` - 🆕 Estadísticas del Sistema de IA
```bash
python maintenance.py character-stats
```
**Muestra:**
- **141 personajes conocidos** en 6 juegos/series
- **7 mapeos directos** + **4 auto-detectados**
- Distribución por juego (Genshin: 38, Honkai: 28, ZZZ: 31, etc.)
- Mapeos automáticos recientes con confianza

---

### 📥 **Poblado de Base de Datos**

#### `populate-db` - Importación Inteligente de Videos

**Sintaxis:**
```bash
python maintenance.py populate-db [opciones]
```

**Opciones:**
- `--source {db|organized|all}`: Fuente de datos
  - `db`: Solo bases de datos externas (4K Apps)
  - `organized`: Solo carpetas organizadas (`D:\4K All`)
  - `all`: Ambas fuentes (por defecto)
- `--platform {youtube|tiktok|instagram}`: Plataforma específica
- `--limit N`: Número máximo de videos a importar
- `--force`: Forzar reimportación de videos existentes

**Ejemplos:**
```bash
# Poblar desde todas las fuentes disponibles
python maintenance.py populate-db --source all

# Solo videos de YouTube (máximo 10)
python maintenance.py populate-db --source db --platform youtube --limit 10

# Forzar actualización completa de Instagram
python maintenance.py populate-db --platform instagram --force

# Solo desde carpetas organizadas (50 elementos)
python maintenance.py populate-db --source organized --limit 50
```

#### `clear-db` - Limpieza Selectiva de Base de Datos

**Sintaxis:**
```bash
python maintenance.py clear-db [opciones]
```

**Opciones:**
- `--platform {youtube|tiktok|instagram}`: Plataforma específica
- `--force`: Sin confirmación

**Ejemplos:**
```bash
# Limpiar toda la base de datos (con confirmación)
python maintenance.py clear-db

# Limpiar solo videos de TikTok
python maintenance.py clear-db --platform tiktok

# Limpiar YouTube sin confirmación
python maintenance.py clear-db --platform youtube --force
```

---

### 🖼️ **Gestión de Thumbnails**

#### `populate-thumbnails` - Generación Masiva de Thumbnails

**Sintaxis:**
```bash
python maintenance.py populate-thumbnails [opciones]
```

**Opciones:**
- `--platform {youtube|tiktok|instagram}`: Plataforma específica
- `--limit N`: Número máximo de thumbnails a generar
- `--force`: Regenerar thumbnails existentes

**Ejemplos:**
```bash
# Generar todos los thumbnails faltantes
python maintenance.py populate-thumbnails

# Solo thumbnails de YouTube (máximo 20)
python maintenance.py populate-thumbnails --platform youtube --limit 20

# Regenerar todos los thumbnails de Instagram
python maintenance.py populate-thumbnails --platform instagram --force
```

#### `clear-thumbnails` - Limpieza Selectiva de Thumbnails

**Sintaxis:**
```bash
python maintenance.py clear-thumbnails [opciones]
```

**Opciones:**
- `--platform {youtube|tiktok|instagram}`: Plataforma específica
- `--force`: Sin confirmación

**Ejemplos:**
```bash
# Limpiar todos los thumbnails (con confirmación)
python maintenance.py clear-thumbnails

# Limpiar solo thumbnails de Instagram
python maintenance.py clear-thumbnails --platform instagram --force
```

---

## 🎭 **NUEVOS COMANDOS DE INTELIGENCIA DE PERSONAJES**

### `add-character` - 🆕 Agregar Personajes Personalizados

**Sintaxis:**
```bash
python maintenance.py add-character --character NOMBRE --game JUEGO [--aliases ALIAS1 ALIAS2 ...]
```

**Ejemplos:**
```bash
# Agregar personaje básico
python maintenance.py add-character --character "Nahida" --game "genshin_impact"

# Agregar con nombres alternativos
python maintenance.py add-character --character "Hu Tao" --game "genshin_impact" --aliases "HuTao" "胡桃" "Walnut"

# Agregar personaje de nuevo juego
python maintenance.py add-character --character "Stelle" --game "honkai_star_rail" --aliases "Trailblazer" "Caelus"
```

### `analyze-titles` - 🆕 Análisis Inteligente de Títulos Existentes

**Sintaxis:**
```bash
python maintenance.py analyze-titles [--limit N]
```

**Funcionalidad:**
- Analiza títulos de videos sin personajes detectados
- Aplica patrones de reconocimiento mejorados
- Actualiza automáticamente la base de datos
- Muestra estadísticas de detección

**Ejemplos:**
```bash
# Analizar todos los títulos pendientes
python maintenance.py analyze-titles

# Analizar los primeros 50 videos
python maintenance.py analyze-titles --limit 50
```

### `update-creator-mappings` - 🆕 Actualización Automática de Mapeos

**Sintaxis:**
```bash
python maintenance.py update-creator-mappings [--limit N]
```

**Funcionalidad:**
- Analiza patrones de creadores y personajes detectados
- Sugiere mapeos automáticos basados en estadísticas
- Identifica creadores especializados en personajes específicos
- Genera reportes de sugerencias para mapeo manual

**Ejemplos:**
```bash
# Analizar todos los creadores
python maintenance.py update-creator-mappings

# Analizar los últimos 100 videos
python maintenance.py update-creator-mappings --limit 100
```

### `download-character-images` - 🆕 Descarga de Imágenes de Referencia

**Sintaxis:**
```bash
python maintenance.py download-character-images [--character NOMBRE] [--game JUEGO] [--limit N]
```

**Funcionalidad:**
- Descarga imágenes de referencia para reconocimiento facial
- Busca automáticamente personajes sin imágenes
- Organiza por juego en `caras_conocidas/`
- Requiere configuración de APIs de búsqueda de imágenes

**Ejemplos:**
```bash
# Descargar imagen para personaje específico
python maintenance.py download-character-images --character "Raiden Shogun" --game "genshin_impact"

# Buscar imágenes para personajes sin referencia (máximo 10)
python maintenance.py download-character-images --limit 10

# Procesar todos los personajes sin imagen
python maintenance.py download-character-images
```

---

### 🔧 **Comandos de Mantenimiento del Sistema**

#### `backup` - Backup Completo con Datos de IA
```bash
python maintenance.py backup
```
**Incluye:**
- Base de datos completa con personajes detectados
- Primeros 100 thumbnails
- **NUEVO**: Base de datos de personajes (`character_database.json`)
- **NUEVO**: Mapeos de creadores (`creator_character_mapping.json`)
- Configuración (.env)
- Caras conocidas para reconocimiento facial

#### `verify` - Verificación de Integridad Expandida
```bash
python maintenance.py verify
```
**Verifica:**
- Integridad de la base de datos principal
- **NUEVO**: Consistencia de la base de datos de personajes
- **NUEVO**: Validez de mapeos de creadores
- Archivos de video existentes
- Thumbnails faltantes o corruptos
- Configuración crítica de APIs

#### `optimize-db` - Optimización Avanzada
```bash
python maintenance.py optimize-db
```
**Acciones:**
- VACUUM para compactar la base de datos principal
- ANALYZE para optimizar consultas
- **NUEVO**: Optimización de índices de personajes
- **NUEVO**: Limpieza de mapeos duplicados
- Estadísticas de tamaño post-optimización

#### `clean-thumbnails` - Limpieza Avanzada de Thumbnails
```bash
python maintenance.py clean-thumbnails [--force]
```
**Elimina:**
- Thumbnails sin video asociado en la BD
- Archivos corruptos o de tamaño cero
- **NUEVO**: Thumbnails de videos eliminados
- Confirma antes de eliminar (a menos que use --force)

#### `regenerate-thumbnails` - Regeneración Selectiva
```bash
python maintenance.py regenerate-thumbnails [--force]
```
**Regenera:**
- Thumbnails faltantes o corruptos
- Solo para videos existentes en disco
- **NUEVO**: Prioriza videos con personajes detectados
- Actualiza metadatos de thumbnails

#### `report` - Reporte Completo del Sistema con IA
```bash
python maintenance.py report
```
**Genera:**
- Archivo JSON con estadísticas completas
- **NUEVO**: Estadísticas de detección de personajes
- **NUEVO**: Análisis de efectividad de mapeos
- **NUEVO**: Tendencias de personajes más detectados
- Resumen en consola
- Información de configuración y rendimiento

---

## 🔧 COMANDOS DE UTILIDADES

### `verify_config.py` - Verificación Completa de Configuración

```bash
python verify_config.py
```
**Verifica:**
- Configuración de APIs (YouTube, Spotify, Google Vision)
- Rutas de fuentes externas (4K Apps)
- Directorios internos (data/, thumbnails/, caras_conocidas/)
- **NUEVO**: Integridad del sistema de personajes
- **NUEVO**: Validez de mapeos de creadores
- Conexiones a bases de datos externas

### `quickstart.py` - Configuración Automática Mejorada

```bash
python quickstart.py
```
**Proceso interactivo mejorado:**
- Instalación de dependencias con verificación
- Configuración guiada de APIs
- **NUEVO**: Configuración del sistema de personajes
- **NUEVO**: Importación de personajes básicos
- Creación de directorios con estructura optimizada
- Datos de ejemplo y verificación del sistema

---

## 📖 EJEMPLOS DE FLUJOS DE TRABAJO ACTUALIZADOS

### **Flujo Inicial - Configuración Completa**
```bash
# 1. Configuración automática con IA
python quickstart.py

# 2. Verificar configuración completa
python verify_config.py

# 3. Ver estadísticas de fuentes y personajes
python maintenance.py show-stats
python maintenance.py character-stats
```

### **Flujo de Importación Inteligente - YouTube**
```bash
# 1. Poblar con videos de YouTube
python maintenance.py populate-db --source db --platform youtube --limit 20

# 2. Generar thumbnails
python maintenance.py populate-thumbnails --platform youtube --limit 20

# 3. Procesar videos con IA avanzada
python main.py 10 YT

# 4. Analizar títulos para detectar más personajes
python maintenance.py analyze-titles --limit 20

# 5. Ver resultados en interfaz web
python app.py
```

### **Flujo de Gestión Avanzada de Personajes**
```bash
# 1. Ver estadísticas actuales
python maintenance.py character-stats

# 2. Agregar personajes personalizados
python maintenance.py add-character --character "Nilou" --game "genshin_impact" --aliases "Nilou_Dancer"

# 3. Analizar títulos con nuevos personajes
python maintenance.py analyze-titles --limit 50

# 4. Actualizar mapeos de creadores
python maintenance.py update-creator-mappings

# 5. Procesar videos con patrones actualizados
python main.py 15
```

### **Flujo de Mantenimiento Semanal Avanzado**
```bash
# 1. Backup completo del sistema
python maintenance.py backup

# 2. Verificar integridad expandida
python maintenance.py verify

# 3. Optimizar bases de datos
python maintenance.py optimize-db

# 4. Analizar títulos pendientes
python maintenance.py analyze-titles

# 5. Limpiar thumbnails huérfanos
python maintenance.py clean-thumbnails --force

# 6. Generar reporte completo
python maintenance.py report
```

### **Flujo de Expansión del Sistema de IA**
```bash
# 1. Agregar múltiples personajes nuevos
python maintenance.py add-character --character "Furina" --game "genshin_impact" --aliases "Focalors" "Hydro_Archon"
python maintenance.py add-character --character "Xianyun" --game "genshin_impact" --aliases "Cloud_Retainer"

# 2. Descargar imágenes de referencia (si configurado)
python maintenance.py download-character-images --limit 5

# 3. Reanalizar colección completa
python maintenance.py analyze-titles
python maintenance.py update-creator-mappings

# 4. Procesar videos con sistema expandido
python main.py 50

# 5. Ver estadísticas actualizadas
python maintenance.py character-stats
```

### **Flujo de Análisis Específico por Plataforma**
```bash
# Instagram - Enfoque en reconocimiento visual
python maintenance.py populate-db --platform instagram
python maintenance.py populate-thumbnails --platform instagram  
python main.py 5 IG

# TikTok - Enfoque en mapeo de creadores
python maintenance.py populate-db --platform tiktok --limit 15
python maintenance.py update-creator-mappings --limit 50
python main.py 10 TT

# Carpetas organizadas - Análisis de títulos
python maintenance.py populate-db --source organized --limit 30
python maintenance.py analyze-titles --limit 30
python main.py 20 O
```

---

## ⚙️ VARIABLES DE ENTORNO ACTUALIZADAS

### **Configuración de APIs**
```env
# APIs de reconocimiento
YOUTUBE_API_KEY="tu_clave_youtube"
SPOTIFY_CLIENT_ID="tu_spotify_id" 
SPOTIFY_CLIENT_SECRET="tu_spotify_secret"
GOOGLE_APPLICATION_CREDENTIALS="config/gcp_credentials.json"

# 🆕 APIs opcionales para descarga de imágenes
BING_IMAGE_SEARCH_API_KEY="tu_clave_bing"  # Opcional
UNSPLASH_ACCESS_KEY="tu_clave_unsplash"     # Opcional
```

### **Configuración de Fuentes Externas**
```env
# Rutas detectadas automáticamente
EXTERNAL_YOUTUBE_DB="C:/Users/.../4K Video Downloader+/.../xxx.sqlite"
EXTERNAL_TIKTOK_DB="D:/4K Tokkit/data.sqlite" 
EXTERNAL_INSTAGRAM_DB="D:/4K Stogram/.stogram.sqlite"
ORGANIZED_BASE_PATH="D:/4K All"
```

### **Configuración de Procesamiento Mejorado**
```env
# Configuración de thumbnails
THUMBNAIL_SIZE="320x180"
THUMBNAIL_QUALITY=85

# Configuración de procesamiento
MAX_CONCURRENT_PROCESSING=3
VIDEO_PROCESSING_TIMEOUT=30

# 🆕 Configuración de IA de personajes
CHARACTER_DETECTION_ENABLED=true
AUTO_CREATOR_MAPPING=true
TITLE_ANALYSIS_ENABLED=true
CONFIDENCE_THRESHOLD=0.7

# Configuración de DeepFace
USE_GPU_DEEPFACE=true
DEEPFACE_MODEL="ArcFace"
FACE_DETECTION_CONFIDENCE=0.8
```

### **Configuración de Flask Mejorada**
```env
# Configuración web
FLASK_ENV="development"
FLASK_DEBUG=true
FLASK_HOST="localhost"
FLASK_PORT=5000

# 🆕 Configuración de interfaz
SHOW_CHARACTER_STATS=true
ENABLE_BATCH_EDITING=true
DEFAULT_PAGE_SIZE=50
```

---

## 🚨 SOLUCIÓN DE PROBLEMAS ACTUALIZADA

### **Comandos de Diagnóstico Expandidos**
```bash
# Verificar configuración completa del sistema
python verify_config.py

# Ver logs detallados con información de IA
python maintenance.py verify

# Estadísticas completas de todas las fuentes
python maintenance.py show-stats

# Estadísticas específicas del sistema de personajes
python maintenance.py character-stats

# Generar reporte completo para análisis
python maintenance.py report
```

### **Problemas Específicos del Sistema de IA**

**No se detectan personajes**
```bash
# Verificar base de datos de personajes
python maintenance.py character-stats

# Analizar títulos existentes
python maintenance.py analyze-titles --limit 10

# Agregar personajes manualmente
python maintenance.py add-character --character "Ejemplo" --game "juego_ejemplo"
```

**Mapeos de creadores no funcionan**
```bash
# Verificar mapeos existentes
python maintenance.py character-stats

# Actualizar mapeos automáticamente
python maintenance.py update-creator-mappings --limit 50

# Editar manualmente: data/creator_character_mapping.json
```

**Reconocimiento facial limitado**
```bash
# Verificar carpeta de caras conocidas
ls caras_conocidas/

# Descargar imágenes automáticamente (si configurado)
python maintenance.py download-character-images --limit 5

# Agregar imágenes manualmente a caras_conocidas/[juego]/[personaje].jpg
```

### **Recuperación de Errores del Sistema**
```bash
# Si hay problemas con la BD de personajes
python maintenance.py backup
python maintenance.py optimize-db

# Si los mapeos están corruptos
# Editar manualmente: data/creator_character_mapping.json
python maintenance.py character-stats  # Verificar

# Si las detecciones son inconsistentes
python maintenance.py analyze-titles   # Reanalizar
python main.py 5                       # Reprocesar algunos videos
```

### **Reset Completo del Sistema de IA**
```bash
# CUIDADO: Esto reinicia el sistema de personajes
python maintenance.py backup                           # Backup obligatorio
rm data/character_database.json                        # Eliminar BD de personajes  
rm data/creator_character_mapping.json                 # Eliminar mapeos
python maintenance.py character-stats                  # Recrear con datos por defecto
python maintenance.py add-character --character "Test" --game "test"  # Agregar ejemplo
```

---

## 📚 NOTAS ADICIONALES ACTUALIZADAS

### **Rendimiento del Sistema de IA**
- **Análisis de títulos**: Instantáneo, sin límites de API
- **Mapeo de creadores**: Rápido, se mejora automáticamente con uso
- **Reconocimiento visual**: 2-8 segundos por video, depende de GPU
- Use `--limit` para pruebas y optimización de rendimiento

### **Gestión de la Base de Datos de Personajes**
- **Archivo**: `data/character_database.json` (141+ personajes incluidos)
- **Expansión**: Fácil agregado de nuevos personajes y juegos
- **Mapeos**: `data/creator_character_mapping.json` (aprende automáticamente)
- **Backup**: Incluido automáticamente en `python maintenance.py backup`

### **Compatibilidad y Escalabilidad**
- **Volumen**: Probado con 1,000+ videos, sin límites conocidos
- **Plataformas**: Windows, Linux, macOS (rutas se adaptan automáticamente)
- **Idiomas**: Soporte nativo para personajes en japonés, chino, coreano, inglés
- **Memoria**: Optimizado para colecciones grandes, uso mínimo de RAM

### **Seguridad y Privacidad**
- **APIs**: Las claves se almacenan localmente en `.env`
- **Datos**: Todo el procesamiento es local, no se envían videos a APIs externas
- **Backups**: No incluyen claves de API por seguridad
- **Thumbnails**: Pueden contener información personal, usar `clean-thumbnails` periódicamente

---

## 🎯 **COMANDOS ESENCIALES PARA NUEVOS USUARIOS**

### **Setup Inicial (Primera vez)**
```bash
python quickstart.py                           # Configuración automática
python maintenance.py show-stats               # Ver fuentes disponibles
python maintenance.py character-stats          # Ver sistema de IA
```

### **Uso Diario (Workflow típico)**
```bash
python maintenance.py populate-db --limit 10   # Importar videos nuevos
python main.py 10                             # Procesar con IA
python app.py                                 # Ver resultados
```

### **Mantenimiento Semanal**
```bash
python maintenance.py backup                  # Backup de seguridad
python maintenance.py analyze-titles          # Detectar más personajes
python maintenance.py optimize-db             # Optimizar rendimiento
```

### **Expansión del Sistema**
```bash
python maintenance.py add-character --character "Nuevo" --game "juego"  # Agregar personajes
python maintenance.py update-creator-mappings  # Mejorar mapeos
python maintenance.py download-character-images --limit 5              # Imágenes de referencia
```

---

*Referencia actualizada: Junio 27, 2025*  
*Versión: Tag-Flow V2 con Sistema de Inteligencia de Personajes*  
*Para más información: README.md y PROYECTO_ESTADO.md*
