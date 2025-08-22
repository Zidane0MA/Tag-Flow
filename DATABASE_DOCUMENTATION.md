# Base de Datos Tag-Flow V2 - Documentación Completa

## Resumen General

Tag-Flow V2 utiliza una base de datos SQLite centralizada para gestionar videos de TikTok/MMD/gaming con inteligencia artificial integrada para reconocimiento de caracteres, identificación musical y gestión automatizada de contenido.

**Ubicación:** `/data/videos.db`  
**Motor:** SQLite 3  
**Optimizaciones:** Índices compuestos, cache TTL, consultas por lotes  

---

## Estructura de Tablas

### 🎬 Tabla Principal: `videos`

**Propósito:** Almacena toda la información de videos con metadatos automatizados y manuales

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| **id** | INTEGER | PRIMARY KEY | Identificador único del video |
| **created_at** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Fecha de agregado al sistema |
| **file_path** | TEXT | NOT NULL, UNIQUE | Ruta absoluta del archivo de video |
| **file_name** | TEXT | NOT NULL | Nombre del archivo (incluye extensión) |
| **thumbnail_path** | TEXT | | Ruta del thumbnail generado automáticamente |
| **file_size** | INTEGER | | Tamaño del archivo en bytes |
| **duration_seconds** | INTEGER | | Duración del video en segundos |
| **title** | TEXT | | Título/descripción del contenido |
| **post_url** | TEXT | | URL original del post en la plataforma |
| **platform** | TEXT | DEFAULT 'tiktok' | Plataforma de origen: youtube, tiktok, instagram |
| **detected_music** | TEXT | | Música detectada automáticamente |
| **detected_music_artist** | TEXT | | Artista detectado automáticamente |
| **detected_music_confidence** | REAL | | Nivel de confianza de la detección (0.0-1.0) |
| **detected_characters** | TEXT | | JSON array de personajes detectados por IA |
| **music_source** | TEXT | CHECK | Fuente de detección musical: youtube, spotify, acrcloud, manual |
| **final_music** | TEXT | | Música final editada manualmente |
| **final_music_artist** | TEXT | | Artista final editado manualmente |
| **final_characters** | TEXT | | JSON array de personajes finales editados |
| **difficulty_level** | TEXT | CHECK | Nivel de dificultad: bajo, medio, alto |
| **edit_status** | TEXT | DEFAULT 'nulo' | Estado de edición: nulo, en_proceso, hecho |
| **edited_video_path** | TEXT | | Ruta del video editado |
| **notes** | TEXT | | Notas manuales del usuario |
| **processing_status** | TEXT | DEFAULT 'pendiente' | Estado de procesamiento: pendiente, procesando, completado, error |
| **error_message** | TEXT | | Mensaje de error si processing_status = 'error' |
| **last_updated** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Fecha de última actualización |
| **deleted_at** | TIMESTAMP | NULL | Fecha de eliminación (soft delete) |
| **deleted_by** | TEXT | | Usuario que eliminó el video |
| **deletion_reason** | TEXT | | Razón de la eliminación |
| **creator_id** | INTEGER | FOREIGN KEY | Referencia a tabla creators (nueva estructura) |
| **subscription_id** | INTEGER | FOREIGN KEY | Referencia a tabla subscriptions |

---

### 👤 Tabla: `creators`

**Propósito:** Gestión centralizada de creadores de contenido

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| **id** | INTEGER | PRIMARY KEY | Identificador único del creador |
| **name** | TEXT | NOT NULL | Nombre unificado del creador |
| **parent_creator_id** | INTEGER | FOREIGN KEY | ID del creador principal (NULL si es cuenta principal) |
| **is_primary** | BOOLEAN | DEFAULT TRUE | TRUE si es cuenta principal, FALSE si es secundaria |
| **alias_type** | TEXT | DEFAULT 'main' | Tipo de cuenta: main, secondary, collaboration, alias |
| **created_at** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Fecha de creación del registro |

---

### 🔗 Tabla: `creator_urls`

**Propósito:** URLs de creadores por plataforma

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| **id** | INTEGER | PRIMARY KEY | Identificador único |
| **creator_id** | INTEGER | NOT NULL, FOREIGN KEY | Referencia al creador |
| **platform** | TEXT | NOT NULL | Plataforma: youtube, tiktok, instagram, facebook |
| **url** | TEXT | NOT NULL | URL completa del perfil |
| **created_at** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Fecha de creación |

**Constraint:** UNIQUE(creator_id, platform)

---

### 📋 Tabla: `subscriptions`

**Propósito:** Gestión de suscripciones y listas de contenido

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| **id** | INTEGER | PRIMARY KEY | Identificador único |
| **name** | TEXT | NOT NULL | Nombre de la suscripción: "Canal X", "Mi Playlist" |
| **type** | TEXT | NOT NULL | Tipo: account, playlist, music, hashtag, location, saved, personal |
| **platform** | TEXT | NOT NULL | Plataforma de origen |
| **creator_id** | INTEGER | FOREIGN KEY | Referencia al creador (NULL para listas sin creador) |
| **subscription_url** | TEXT | | URL de la lista/suscripción |
| **external_id** | TEXT | | ID en la plataforma externa (no utilizado) |
| **metadata** | TEXT | | JSON con datos específicos por tipo (no utilizado) |
| **created_at** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Fecha de creación |

---

### 📝 Tabla: `video_lists`

**Propósito:** Clasificación de videos en listas específicas

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| **id** | INTEGER | PRIMARY KEY | Identificador único |
| **video_id** | INTEGER | NOT NULL, FOREIGN KEY | Referencia al video |
| **list_type** | TEXT | NOT NULL | Tipo: feed, liked, reels, stories, highlights, saved, favorites |
| **created_at** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Fecha de creación |

**Constraint:** UNIQUE(video_id, list_type)

---

### 📥 Tabla: `downloader_mapping`

**Propósito:** Mapeo con herramientas externas de descarga (4K Downloader+, 4K Tokkit, 4K Stogram)

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| **id** | INTEGER | PRIMARY KEY | Identificador único |
| **video_id** | INTEGER | NOT NULL, FOREIGN KEY | Referencia al databaseId del video |
| **download_item_id** | INTEGER | | ID en la BD externa del downloader |
| **external_db_source** | TEXT | | Fuente: 4k_video, 4k_tokkit, 4k_stogram |
| **original_filename** | TEXT | | Nombre original del archivo |
| **creator_from_downloader** | TEXT | | Nombre del creador según el downloader |
| **is_carousel_item** | BOOLEAN | | TRUE si es un item de carrusel |
| **carousel_order** | INTEGER | | Orden del item en el carrusel |
| **carousel_base_id** | TEXT | | ID base del carrusel |
| **created_at** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Fecha de creación |

---

## Funcionalidades de la Base de Datos

### 🔧 Clase Principal: `DatabaseManager`

**Ubicación:** `/src/database.py`

#### Métodos de Conexión y Configuración

- **`get_connection()`** - Crear conexión SQLite con row_factory
- **`init_database()`** - Inicializar todas las tablas e índices

#### Operaciones CRUD de Videos

- **`add_video(video_data)`** - Agregar video individual
- **`batch_insert_videos(videos_data, force=False)`** - Inserción masiva optimizada
- **`get_video(video_id, include_deleted=False)`** - Obtener video por ID
- **`get_video_by_path(file_path)`** - Buscar video por ruta
- **`get_videos(filters, limit, offset)`** - Búsqueda con filtros avanzados
- **`count_videos(filters)`** - Contar videos que coinciden con filtros
- **`update_video(video_id, updates)`** - Actualizar video individual
- **`batch_update_videos(video_updates)`** - Actualización masiva optimizada

#### Operaciones de Eliminación

- **`soft_delete_video(video_id, deleted_by, reason)`** - Eliminación suave
- **`restore_video(video_id)`** - Restaurar video eliminado
- **`permanent_delete_video(video_id)`** - Eliminación permanente (peligroso)
- **`bulk_delete_videos(video_ids)`** - Eliminación masiva
- **`get_deleted_videos()`** - Obtener videos en papelera

#### Operaciones de Creadores

- **`create_creator(name, display_name, parent_creator_id, is_primary, alias_type)`** - Crear nuevo creador (con soporte para jerarquías)
- **`get_creator_by_name(name)`** - Buscar creador por nombre
- **`get_creator_with_urls(creator_id)`** - Obtener creador con URLs
- **`add_creator_url(creator_id, platform, url)`** - Agregar URL a creador

#### Operaciones de Jerarquías (Cuentas Secundarias)

- **`link_creator_as_secondary(secondary_id, primary_id, alias_type)`** - Enlazar cuenta secundaria
- **`unlink_secondary_creator(secondary_id)`** - Desenlazar cuenta secundaria (independizarla)
- **`get_creator_with_secondaries(creator_id)`** - Obtener creador con todas sus cuentas secundarias
- **`get_primary_creator_for_video(video_id)`** - Obtener creador principal de un video
- **`search_creators_with_hierarchy(search_term)`** - Buscar creadores incluyendo jerarquía
- **`get_creator_hierarchy_stats(creator_id)`** - Estadísticas de jerarquía de un creador

#### Operaciones de Suscripciones

- **`create_subscription(name, type, platform)`** - Crear suscripción
- **`get_subscription_by_name_and_platform(name, platform)`** - Buscar suscripción
- **`get_subscriptions_by_creator(creator_id)`** - Suscripciones de un creador

#### Operaciones de Listas

- **`add_video_to_list(video_id, list_type)`** - Agregar video a lista
- **`get_video_lists(video_id)`** - Listas de un video
- **`get_videos_by_list_type(list_type)`** - Videos por tipo de lista

#### Operaciones Optimizadas (Performance)

- **`get_existing_paths_only()`** - Solo obtener rutas para verificación O(1)
- **`check_videos_exist_batch(file_paths)`** - Verificar existencia por lotes
- **`get_pending_videos_filtered(platform, source, limit)`** - Videos pendientes optimizados
- **`get_videos_by_paths_batch(file_paths)`** - Obtener múltiples videos por rutas

#### Métricas y Estadísticas

- **`get_stats()`** - Estadísticas generales del sistema
- **`get_creator_stats(creator_id)`** - Estadísticas de un creador
- **`get_performance_report()`** - Reporte de rendimiento de consultas
- **`log_performance_summary()`** - Log resumen de performance

---

### 🛠️ Clase: `DatabaseOperations`

**Ubicación:** `/src/maintenance/database_ops.py`

#### Operaciones de Mantenimiento

- **`populate_database(source, platform, limit, force)`** - Poblar BD desde fuentes externas
- **`optimize_database()`** - VACUUM y ANALYZE para optimización
- **`clear_database(platform, force)`** - Limpiar videos por plataforma
- **`backup_database(backup_path)`** - Crear backup con verificación de integridad
- **`restore_database(backup_path, force)`** - Restaurar desde backup
- **`migrate_database(target_version)`** - Migrar esquema a nueva versión
- **`get_database_stats()`** - Estadísticas detalladas completas

---

## Índices de Optimización

### Índices Básicos
- `idx_videos_creator` - Búsqueda por creador
- `idx_videos_platform` - Filtrado por plataforma
- `idx_videos_status` - Filtrado por estado de edición
- `idx_videos_file_path` - Búsqueda por ruta
- `idx_videos_deleted` - Filtrado de eliminados

### Índices Compuestos Optimizados
- `idx_videos_file_path_name` - Verificación de duplicados 10x más rápida
- `idx_videos_platform_status` - Filtros frecuentes 5x más rápido
- `idx_videos_status_platform_created` - Filtrado avanzado con fecha
- `idx_videos_creator_platform` - Queries del frontend
- `idx_videos_subscription_platform` - Queries de suscripciones

### Índices de Relaciones
- `idx_creator_urls_creator_id` - URLs por creador
- `idx_video_lists_video_id` - Listas por video
- `idx_subscriptions_platform_type` - Suscripciones por plataforma y tipo

### Índices de Jerarquías (Cuentas Secundarias)
- `idx_creators_parent` - Búsqueda por creador padre
- `idx_creators_is_primary` - Filtro por cuenta principal/secundaria
- `idx_creators_alias_type` - Filtro por tipo de cuenta

---

## Sistema de Cache Inteligente

### Cache TTL (Time To Live)
- **Duración:** 5 minutos por defecto
- **Tipo:** LRU (Least Recently Used) eviction
- **Categorías:** Rutas de archivos, videos pendientes, estadísticas

### Métricas de Performance
- **Hit Rate:** Porcentaje de aciertos en cache
- **Query Times:** Tiempo promedio por tipo de consulta
- **Performance Grade:** EXCELLENT, GOOD, AVERAGE, NEEDS_IMPROVEMENT

---

## Flujo de Datos y Procesamiento

### 1. Importación desde Fuentes Externas
```
4K Downloader+ → external_sources.py → DatabaseOperations.populate_database()
    ↓
Verificación de duplicados (get_existing_paths_only)
    ↓
Creación de creadores y suscripciones
    ↓
Inserción masiva optimizada (batch_insert_videos)
```

### 2. Procesamiento de Videos
```
Nuevo video → processing_status: 'pendiente'
    ↓
video_analyzer.py → Detección de personajes/música
    ↓
processing_status: 'completado' + metadatos actualizados
```

### 3. Gestión de Carruseles (Instagram)
```
external_metadata JSON → process_image_carousels()
    ↓
Agrupación de imágenes relacionadas
    ↓
Presentación unificada en frontend
```

---

## Configuración y Ubicaciones

### Rutas Principales
- **Base de datos:** `/data/videos.db`
- **Thumbnails:** `/data/thumbnails/`
- **Backups:** `/backups/`
- **Configuración:** `config.py`

### Variables de Entorno
- `DATABASE_PATH` - Ruta de la base de datos
- `USE_OPTIMIZED_DATABASE=true` - Habilitar optimizaciones
- `ENABLE_PERFORMANCE_METRICS=true` - Métricas de rendimiento
- `DATABASE_CACHE_TTL=300` - TTL del cache en segundos
- `DATABASE_CACHE_SIZE=1000` - Tamaño máximo del cache

---

## Refactorización Planificada

### Cambios Programados (Ver DATABASE_REFACTORING_PLAN.md)

#### Alta Prioridad
1. **`creator_name` → `creator_id`** - Normalización de creadores
2. **`external_metadata` → Columnas específicas** - Optimización de carruseles

#### Media Prioridad
3. **Eliminar `external_video_id`** - Redundante con post_url
4. **Limpiar tabla subscriptions** - Eliminar campos no utilizados

#### Baja Prioridad
5. **Eliminar `display_name`** - Duplicado de name
6. **Eliminar `source_path`** - No utilizado
7. **Eliminar `username`** - Extraíble de URLs

---

## Herramientas de Monitoreo

### Comandos de Administración
```bash
# Estadísticas de rendimiento
python main.py maintenance database-stats

# Backup automático
python main.py maintenance backup

# Optimización de BD
python main.py maintenance optimize-db

# Verificación de integridad
python main.py maintenance verify
```

### Métricas Disponibles
- Total de videos por plataforma
- Videos con música/personajes detectados
- Estadísticas de archivos (tamaño, duración)
- Rendimiento de consultas
- Estado del cache

---

## Seguridad y Backup

### Eliminación Suave (Soft Delete)
- Campo `deleted_at` para marcar eliminación
- Videos eliminados ocultos de consultas normales
- Posibilidad de restauración
- Papelera accesible desde admin

### Sistema de Backup
- Backups automáticos antes de operaciones críticas
- Verificación de integridad con PRAGMA integrity_check
- Backup pre-restauración automático
- Compresión y timestamp en nombres

### Validación de Datos
- Constraints CHECK en campos críticos
- Verificación de foreign keys
- Validación de JSON en campos de caracteres
- Índices UNIQUE para prevenir duplicados

---

## 👥 Sistema de Cuentas Secundarias

### Propósito
Permite a los creadores gestionar múltiples canales/cuentas bajo una identidad principal, ideal para:
- **Cuentas especializadas:** Gaming, música, tutoriales
- **Colaboraciones:** Videos con otros creadores
- **Aliases:** Nombres alternativos del mismo creador

### Estructura Jerárquica
```
Creador Principal (is_primary=TRUE, parent_creator_id=NULL)
├── Cuenta Gaming (is_primary=FALSE, parent_creator_id=1, alias_type='secondary')
├── Cuenta Música (is_primary=FALSE, parent_creator_id=1, alias_type='secondary')  
├── Colaboración (is_primary=FALSE, parent_creator_id=1, alias_type='collaboration')
└── Alias (is_primary=FALSE, parent_creator_id=1, alias_type='alias')
```

### Tipos de Cuentas
- **`main`** - Cuenta principal del creador
- **`secondary`** - Cuenta secundaria especializada (gaming, música, etc.)
- **`collaboration`** - Cuenta para colaboraciones con otros creadores
- **`alias`** - Nombre alternativo del mismo creador

### Funcionalidades
1. **Enlace Automático:** Los videos se pueden asignar a cuentas secundarias
2. **Resolución Inteligente:** El sistema siempre puede encontrar el creador principal
3. **Estadísticas Unificadas:** Las métricas se pueden agrupar por creador principal
4. **Búsqueda Jerárquica:** Buscar en cuenta principal o secundarias
5. **Gestión Flexible:** Enlazar/desenlazar cuentas dinámicamente

### Ejemplos de Uso

#### Crear Cuenta Secundaria
```python
# Crear cuenta principal
primary_id = db.create_creator("CreatorName")

# Crear cuenta gaming
gaming_id = db.create_creator(
    name="CreatorName_Gaming", 
    parent_creator_id=primary_id,
    is_primary=False,
    alias_type='secondary'
)
```

#### Enlazar Cuenta Existente
```python
# Enlazar cuenta existente como secundaria
db.link_creator_as_secondary(
    secondary_creator_id=gaming_id,
    primary_creator_id=primary_id,
    alias_type='secondary'
)
```

#### Obtener Jerarquía Completa
```python
# Obtener creador con todas sus cuentas secundarias
creator_data = db.get_creator_with_secondaries(primary_id)
print(f"Creador principal: {creator_data['name']}")
for secondary in creator_data['secondary_accounts']:
    print(f"  └── {secondary['name']} ({secondary['alias_type']})")
```

### APIs para Frontend

#### Enlazar Cuentas
```bash
POST /api/creator/{creator_id}/link-secondary
Content-Type: application/json

{
  "secondary_creator_id": 123,
  "alias_type": "secondary"
}
```

#### Obtener Jerarquía
```bash
GET /api/creator/{creator_id}/hierarchy

Response:
{
  "success": true,
  "creator": {
    "id": 1,
    "name": "CreatorName",
    "is_primary": true,
    "secondary_accounts": [
      {
        "id": 2,
        "name": "CreatorName_Gaming",
        "alias_type": "secondary",
        "is_primary": false
      }
    ]
  }
}
```

#### Buscar con Jerarquía
```bash
GET /api/creators/search-hierarchy?q=CreatorName

Response:
{
  "success": true,
  "creators": [
    {
      "id": 1,
      "name": "CreatorName",
      "is_primary": true,
      "secondary_count": 3
    },
    {
      "id": 2,
      "name": "CreatorName_Gaming", 
      "is_primary": false,
      "primary_name": "CreatorName"
    }
  ]
}
```

#### Estadísticas de Jerarquía
```bash
GET /api/creator/{creator_id}/hierarchy/stats

Response:
{
  "success": true,
  "stats": {
    "primary_creator_id": 1,
    "total_accounts": 4,
    "total_videos": 150,
    "accounts": [
      {
        "id": 1,
        "name": "CreatorName",
        "alias_type": "main",
        "is_primary": true,
        "video_count": 120,
        "youtube_videos": 80,
        "tiktok_videos": 40
      },
      {
        "id": 2,
        "name": "CreatorName_Gaming",
        "alias_type": "secondary", 
        "is_primary": false,
        "video_count": 30,
        "youtube_videos": 25,
        "tiktok_videos": 5
      }
    ]
  }
}
```

---

## APIs y Endpoints

### Videos API (`/api/videos`)
- `GET /videos` - Lista paginada con filtros
- `GET /video/<id>` - Detalles de video individual
- `POST /video/<id>/update` - Actualizar metadatos
- `DELETE /video/<id>` - Eliminación suave
- `GET /video/<id>/stream` - Streaming de video

### Filtros Disponibles
- `creator_name` - Por creador (múltiples separados por comas)
- `platform` - Por plataforma
- `edit_status` - Por estado de edición
- `processing_status` - Por estado de procesamiento
- `difficulty_level` - Por nivel de dificultad
- `has_music` - Con/sin música detectada
- `search` - Búsqueda libre en múltiples campos

---

## Rendimiento y Optimizaciones

### Mejoras Implementadas
- **10x más rápido:** Verificación de rutas existentes
- **5x más rápido:** Filtros frecuentes con índices compuestos
- **2-3x más rápido:** Detección de caracteres optimizada
- **O(1) lookups:** Verificación de duplicados con sets
- **Batch operations:** Inserción/actualización masiva

### Monitoreo de Performance
- Tiempo de ejecución por tipo de consulta
- Grading automático de rendimiento
- Cache hit rate monitoring
- Alertas de consultas lentas (>100ms)

---

## Consideraciones Técnicas

### Limitaciones Actuales
- SQLite: Límite de ~1000 parámetros por consulta (solucionado con batching)
- Sin transacciones distribuidas (no necesario para uso local)
- Cache en memoria (se pierde al reiniciar aplicación)

### Escalabilidad
- Índices optimizados para crecimiento
- Operaciones por lotes para grandes volúmenes
- Estructura preparada para migración a PostgreSQL si necesario

### Mantenimiento
- VACUUM automático en optimización
- ANALYZE para actualizar estadísticas de consultas
- Limpieza automática de registros huérfanos
- Verificación de integridad en backups

---

**Última actualización:** Agosto 2025  
**Versión del esquema:** 1.0  
**Estado:** Producción con optimizaciones completas