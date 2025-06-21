# 📋 TAG-FLOW V2 - REFERENCIA COMPLETA DE COMANDOS

**Guía de referencia para todos los comandos disponibles en Tag-Flow V2**

---

## 🚀 COMANDOS PRINCIPALES

### `main.py` - Procesamiento de Videos

**Sintaxis:**
```bash
python main.py [límite] [plataforma]
```

**Ejemplos:**
```bash
# Procesamiento básico
python main.py                    # Todos los videos nuevos
python main.py 20                 # Máximo 20 videos

# Procesamiento por plataforma
python main.py 5 YT               # 5 videos de YouTube
python main.py 3 TT               # 3 videos de TikTok  
python main.py 2 IG               # 2 videos de Instagram
python main.py 10 O               # 10 videos de carpetas organizadas
```

**Códigos de Plataforma:**
- **YT**: YouTube (4K Video Downloader+)
- **TT**: TikTok (4K Tokkit)
- **IG**: Instagram (4K Stogram)
- **O**: Carpetas organizadas (`D:\4K All`)

### `app.py` - Interfaz Web

```bash
python app.py
```
- Lanza la interfaz web en http://localhost:5000
- Permite gestión visual y edición en tiempo real
- Filtros avanzados y búsqueda inteligente

---

## 🛠️ COMANDOS DE MANTENIMIENTO

### `maintenance.py` - Gestión del Sistema

**Sintaxis:**
```bash
python maintenance.py [acción] [opciones]
```

---

### 📊 **Estadísticas y Diagnóstico**

#### `show-stats` - Ver Estadísticas Completas
```bash
python maintenance.py show-stats
```
**Muestra:**
- Videos disponibles en fuentes externas
- Estado de la base de datos Tag-Flow
- Distribución por plataforma
- Conexiones a fuentes externas

---

### 📥 **Poblado de Base de Datos**

#### `populate-db` - Poblar Base de Datos

**Sintaxis:**
```bash
python maintenance.py populate-db [opciones]
```

**Opciones:**
- `--source {db|organized|all}`: Fuente de datos
  - `db`: Solo bases de datos externas
  - `organized`: Solo carpetas organizadas
  - `all`: Ambas fuentes (por defecto)
- `--platform {youtube|tiktok|instagram}`: Plataforma específica
- `--limit N`: Número máximo de videos a importar
- `--force`: Forzar reimportación de videos existentes

**Ejemplos:**
```bash
# Poblar desde todas las fuentes
python maintenance.py populate-db --source all

# Solo videos de YouTube
python maintenance.py populate-db --source db --platform youtube --limit 10

# Forzar actualización de Instagram
python maintenance.py populate-db --platform instagram --force

# Solo carpetas organizadas
python maintenance.py populate-db --source organized --limit 50
```

#### `clear-db` - Limpiar Base de Datos

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

#### `populate-thumbnails` - Generar Thumbnails

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

#### `clear-thumbnails` - Limpiar Thumbnails

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

### 🔧 **Mantenimiento del Sistema**

#### `backup` - Crear Backup Completo
```bash
python maintenance.py backup
```
**Incluye:**
- Base de datos completa
- Primeros 100 thumbnails
- Configuración (.env)
- Caras conocidas
- Manifiesto con metadatos

#### `verify` - Verificar Integridad del Sistema
```bash
python maintenance.py verify
```
**Verifica:**
- Integridad de la base de datos
- Archivos de video existentes
- Thumbnails faltantes
- Configuración crítica

#### `optimize-db` - Optimizar Base de Datos
```bash
python maintenance.py optimize-db
```
**Acciones:**
- VACUUM para compactar
- ANALYZE para optimizar consultas
- Estadísticas de tamaño post-optimización

#### `clean-thumbnails` - Limpiar Thumbnails Huérfanos
```bash
python maintenance.py clean-thumbnails [--force]
```
**Elimina:**
- Thumbnails sin video asociado en la BD
- Confirma antes de eliminar (a menos que use --force)

#### `regenerate-thumbnails` - Regenerar Todos los Thumbnails
```bash
python maintenance.py regenerate-thumbnails [--force]
```
**Regenera:**
- Thumbnails faltantes o corruptos
- Solo para videos existentes en disco

#### `report` - Generar Reporte del Sistema
```bash
python maintenance.py report
```
**Genera:**
- Archivo JSON con estadísticas completas
- Resumen en consola
- Información de configuración y archivos

---

## 🔧 COMANDOS DE UTILIDADES

### `verify_config.py` - Verificar Configuración

```bash
python verify_config.py
```
**Verifica:**
- Configuración de APIs
- Rutas de fuentes externas
- Directorios internos
- Conexiones a bases de datos externas

### `quickstart.py` - Configuración Guiada

```bash
python quickstart.py
```
**Proceso interactivo:**
- Instalación de dependencias
- Configuración de APIs
- Creación de directorios
- Datos de ejemplo

---

## 📖 EJEMPLOS DE FLUJOS DE TRABAJO

### **Flujo Inicial - Configuración**
```bash
# 1. Configuración guiada (primera vez)
python quickstart.py

# 2. Verificar configuración
python verify_config.py

# 3. Ver fuentes disponibles
python maintenance.py show-stats
```

### **Flujo de Importación - YouTube**
```bash
# 1. Poblar con videos de YouTube
python maintenance.py populate-db --source db --platform youtube --limit 20

# 2. Generar thumbnails
python maintenance.py populate-thumbnails --platform youtube --limit 20

# 3. Procesar videos
python main.py 10 YT

# 4. Ver resultados
python app.py
```

### **Flujo de Mantenimiento Semanal**
```bash
# 1. Backup del sistema
python maintenance.py backup

# 2. Verificar integridad
python maintenance.py verify

# 3. Optimizar base de datos
python maintenance.py optimize-db

# 4. Limpiar thumbnails huérfanos
python maintenance.py clean-thumbnails --force
```

### **Flujo de Limpieza y Repoblado**
```bash
# 1. Backup antes de limpiar
python maintenance.py backup

# 2. Limpiar sistema
python maintenance.py clear-db --force
python maintenance.py clear-thumbnails --force

# 3. Repoblar con datos selectos
python maintenance.py populate-db --source all --limit 100

# 4. Regenerar thumbnails
python maintenance.py populate-thumbnails --limit 100

# 5. Procesar videos nuevos
python main.py 50
```

### **Flujo de Análisis Específico por Plataforma**
```bash
# Instagram
python maintenance.py populate-db --platform instagram
python maintenance.py populate-thumbnails --platform instagram  
python main.py 5 IG

# TikTok
python maintenance.py populate-db --platform tiktok --limit 10
python main.py 3 TT

# Carpetas organizadas
python maintenance.py populate-db --source organized
python main.py 15 O
```

---

## ⚙️ VARIABLES DE ENTORNO

### **Configuración de APIs**
```env
YOUTUBE_API_KEY="tu_clave_youtube"
SPOTIFY_CLIENT_ID="tu_spotify_id" 
SPOTIFY_CLIENT_SECRET="tu_spotify_secret"
GOOGLE_APPLICATION_CREDENTIALS="config/gcp_credentials.json"
```

### **Configuración de Fuentes Externas**
```env
EXTERNAL_YOUTUBE_DB="C:/Users/.../4K Video Downloader+/.../xxx.sqlite"
EXTERNAL_TIKTOK_DB="D:/4K Tokkit/data.sqlite" 
EXTERNAL_INSTAGRAM_DB="D:/4K Stogram/.stogram.sqlite"
ORGANIZED_BASE_PATH="D:/4K All"
```

### **Configuración de Procesamiento**
```env
THUMBNAIL_SIZE="320x180"
MAX_CONCURRENT_PROCESSING=3
USE_GPU_DEEPFACE=true
DEEPFACE_MODEL="ArcFace"
```

### **Configuración de Flask**
```env
FLASK_ENV="development"
FLASK_DEBUG=true
FLASK_HOST="localhost"
FLASK_PORT=5000
```

---

## 🚨 SOLUCIÓN DE PROBLEMAS

### **Comandos de Diagnóstico**
```bash
# Verificar configuración completa
python verify_config.py

# Ver logs detallados
python maintenance.py verify

# Estadísticas de fuentes
python maintenance.py show-stats

# Generar reporte completo
python maintenance.py report
```

### **Recuperación de Errores**
```bash
# Si la BD está corrupta
python maintenance.py backup
python maintenance.py optimize-db

# Si hay thumbnails problemáticos
python maintenance.py clean-thumbnails --force
python maintenance.py regenerate-thumbnails --force

# Si las fuentes no se detectan
python verify_config.py
# Revisar rutas en .env
```

### **Reset Completo**
```bash
# CUIDADO: Esto borra todo
python maintenance.py backup                    # Backup antes
python maintenance.py clear-db --force         # Limpiar BD
python maintenance.py clear-thumbnails --force # Limpiar thumbnails
python maintenance.py populate-db --limit 10   # Repoblar con pocos datos
```

---

## 📚 NOTAS ADICIONALES

### **Rendimiento**
- Use `--limit` para pruebas rápidas
- El procesamiento paralelo está limitado por `MAX_CONCURRENT_PROCESSING`
- Los thumbnails consumen espacio; use `clean-thumbnails` periódicamente

### **Seguridad**
- Los backups no incluyen claves de API
- Use `.env` para credenciales, nunca código fuente
- Los thumbnails pueden contener información personal

### **Compatibilidad**
- Todos los comandos funcionan en Windows, Linux y macOS
- Las rutas se adaptan automáticamente al sistema operativo
- Los comandos están optimizados para consolas UTF-8

---

*Referencia actualizada: Junio 21, 2025*  
*Para más información: README.md y PROYECTO_ESTADO.md*
