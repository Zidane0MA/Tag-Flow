# Tag-Flow V2 - Database Context for AI Assistant

## Project Overview
Tag-Flow V2 es un sistema inteligente de gestión de videos para contenido TikTok/MMD/gaming que combina reconocimiento de personajes con IA, identificación musical y catalogación automatizada. El sistema está diseñado para funcionar localmente y procesar contenido descargado desde múltiples plataformas.

## Nueva Estructura de Base de Datos

### 1. Tabla Principal `videos`
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- File Information
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    thumbnail_path TEXT,
    file_size INTEGER,
    duration_seconds INTEGER,
    
    -- Content Information
    description TEXT,
    post_url TEXT,              -- URL del post original
    external_video_id TEXT,     -- ID del video en plataforma externa
    
    -- AI Recognition Results
    detected_music TEXT,
    detected_music_artist TEXT,
    detected_music_confidence REAL,
    detected_characters TEXT,   -- JSON array
    music_source TEXT CHECK(music_source IN ('youtube', 'spotify', 'acrcloud', 'manual')),
    
    -- Manual Editing
    final_music TEXT,
    final_music_artist TEXT,
    final_characters TEXT,      -- JSON array
    difficulty_level TEXT CHECK(difficulty_level IN ('bajo', 'medio', 'alto')),
    notes TEXT,
    
    -- Project States
    edit_status TEXT DEFAULT 'nulo' CHECK(edit_status IN ('nulo', 'en_proceso', 'hecho')),
    edited_video_path TEXT,
    processing_status TEXT DEFAULT 'pendiente' CHECK(processing_status IN ('pendiente', 'procesando', 'completado', 'error')),
    error_message TEXT,
    
    -- Soft Delete System
    deleted_at TIMESTAMP NULL,
    deleted_by TEXT,
    deletion_reason TEXT,
    
    -- Relaciones
    creator_id INTEGER REFERENCES creators(id),
    subscription_id INTEGER REFERENCES subscriptions(id)
);
```

### 2. Tabla `creators`
```sql
CREATE TABLE creators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,              -- Nombre unificado del creador
    display_name TEXT,               -- Nombre para mostrar en UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Tabla `creator_urls`
```sql
CREATE TABLE creator_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL REFERENCES creators(id),
    platform TEXT NOT NULL,         -- 'youtube', 'tiktok', 'instagram', 'facebook'
    url TEXT NOT NULL,              -- URL completa del perfil
    username TEXT,                  -- @username sin la URL base
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(creator_id, platform)
);
```

### 4. Tabla `subscriptions`
```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,             -- "Canal X", "Mi Playlist", "#hashtag", "cancion-nueva-cinco"
    type TEXT NOT NULL,             -- 'account', 'playlist', 'music', 'hashtag', 'location', 'saved'
    platform TEXT NOT NULL,        -- 'youtube', 'tiktok', 'instagram', 'facebook'
    creator_id INTEGER REFERENCES creators(id), -- NULL para listas sin creador específico
    
    -- URLs y metadata
    subscription_url TEXT,          -- URL de la lista/subscription
    external_id TEXT,              -- ID en la plataforma externa
    metadata TEXT,                 -- JSON con datos específicos por tipo
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Tabla `video_lists`
```sql
CREATE TABLE video_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL REFERENCES videos(id),
    list_type TEXT NOT NULL,       -- 'feed', 'liked', 'reels', 'stories', 'highlights', 'saved', 'favorites'
    source_path TEXT,              -- Ruta que indica la lista (ej: "\\name\\Liked\\")
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(video_id, list_type)
);
```

### 6. Tabla `downloader_mapping`
```sql
CREATE TABLE downloader_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL REFERENCES videos(id),
    download_item_id INTEGER,       -- ID en BD externa
    external_db_source TEXT,        -- '4k_video', '4k_tokkit', '4k_stogram'
    original_filename TEXT,
    creator_from_downloader TEXT,
    external_metadata TEXT,         -- JSON con metadata específica del downloader
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);
```

## Mapeo desde Bases de Datos Externas

### 4K Video Downloader (YouTube y otras plataformas)

**Tablas fuente:** `download_item`, `media_item_metadata`, `media_item_description`, `url_description`

**Mapeo para poblar:**
```python
# Obtener plataforma desde url_description.service_name
# Obtener URL del video desde url_description.url
# Obtener título desde media_item_description.title

# Para creators:
creator_name = metadata[type=0].value  # creator post
creator_url = f"http://www.youtube.com/@{creator_name}"  # si es YouTube

# Para subscriptions:
if metadata[type=3] exists:  # playlist name
    subscription = {
        'name': metadata[type=3].value,
        'type': 'playlist',
        'subscription_url': metadata[type=4].value  # url playlist
    }
else:
    subscription = {
        'name': creator_name,
        'type': 'account',
        'subscription_url': creator_url
    }

# Para video_lists:
list_type = 'playlist' if playlist else 'feed'
```

### 4K Tokkit (Solo TikTok)

**Tablas fuente:** `Subscriptions`, `MediaItems`, `SubscriptionsDownloadSettings`

**Mapeo para poblar:**
```python
# Para creators:
creator_name = MediaItems.authorName
creator_url = f"https://www.tiktok.com/@{creator_name}"

# Para subscriptions:
subscription_types = {
    1: 'account',    # cuenta
    2: 'hashtag',    # hashtag
    3: 'music'       # música
}

if subscription.type == 1:  # cuenta
    subscription_url = f"https://www.tiktok.com/@{subscription.name}"
elif subscription.type == 2:  # hashtag
    subscription_url = f"https://www.tiktok.com/tag/{subscription.name}"
elif subscription.type == 3:  # música
    clean_name = subscription.name.replace(' ', '-')
    subscription_url = f"https://www.tiktok.com/music/{clean_name}-{subscription.id}"

# Para video_lists (desde relativePath):
if 'Liked' in relativePath:
    list_types = ['liked']
elif 'Favorites' in relativePath:
    list_types = ['favorites']
else:
    list_types = ['feed']

# Para post_url:
post_url = f"https://www.tiktok.com/@{authorName}/video/{id}"
```

### 4K Stogram (Solo Instagram)

**Tablas fuente:** `subscriptions`, `photos`

**Mapeo para poblar:**
```python
# Para creators:
creator_name = photos.ownerName
creator_url = f"https://www.instagram.com/{creator_name}/"

# Para subscriptions:
subscription_types = {
    1: 'account',    # cuenta
    2: 'hashtag',    # hashtag
    3: 'location',   # location
    4: 'saved'       # guardados
}

# URLs de subscriptions:
if type == 1:  # account
    subscription_url = f"https://www.instagram.com/{display_name}/"
elif type == 4:  # saved
    subscription_url = f"https://www.instagram.com/{display_name}/saved/"

# Para video_lists (desde file path):
path_mapping = {
    'reels': 'reels',
    'story': 'stories', 
    'highlights': 'highlights',
    'tagged': 'tagged'
}

# Determinar list_types desde flags de subscription:
list_types = []
if downloadFeed: list_types.append('feed')
if downloadStories: list_types.append('stories')
if downloadHighlights: list_types.append('highlights')
if downloadTaggedPosts: list_types.append('tagged')
if downloadReels: list_types.append('reels')

# Para post_url:
post_url = photos.web_url
```

## Iconos por Tipo de Suscripción y Lista

### Iconos de Suscripciones
```javascript
const subscriptionIcons = {
    'account': '👤',
    'playlist': '📋', 
    'music': '🎵',
    'hashtag': '#️⃣',
    'location': '📍',
    'saved': '💾'
};
```

### Iconos de Listas
```javascript
const listIcons = {
    'feed': '📱',
    'liked': '❤️',
    'reels': '🎬',
    'stories': '📖',
    'highlights': '⭐',
    'tagged': '🏷️',
    'favorites': '💝',
    'playlist': '📋'
};
```

## Queries para Frontend

### Obtener videos de un creador con iconos
```sql
SELECT 
    v.*,
    c.name as creator_name,
    s.name as subscription_name,
    s.type as subscription_type,
    GROUP_CONCAT(vl.list_type) as list_types,
    GROUP_CONCAT(DISTINCT cu.platform) as creator_platforms
FROM videos v
JOIN creators c ON v.creator_id = c.id
JOIN subscriptions s ON v.subscription_id = s.id
LEFT JOIN video_lists vl ON v.id = vl.video_id
LEFT JOIN creator_urls cu ON c.id = cu.creator_id
WHERE c.name = ?
GROUP BY v.id;
```

### Obtener videos por suscripción específica
```sql
SELECT 
    v.*,
    s.name as subscription_name,
    s.type as subscription_type,
    s.subscription_url,
    GROUP_CONCAT(vl.list_type) as list_types
FROM videos v
JOIN subscriptions s ON v.subscription_id = s.id
LEFT JOIN video_lists vl ON v.id = vl.video_id
WHERE s.id = ?
GROUP BY v.id;
```

### Obtener estadísticas de plataformas
```sql
SELECT 
    s.platform,
    s.type as subscription_type,
    COUNT(v.id) as video_count,
    COUNT(DISTINCT s.id) as subscription_count
FROM subscriptions s
LEFT JOIN videos v ON s.id = v.subscription_id
GROUP BY s.platform, s.type
ORDER BY s.platform, video_count DESC;
```

## Estructura de Páginas Frontend

### 1. Página de Creador (`/creator/:creatorName`)
**Datos necesarios:**
- Videos del creador agrupados por plataforma
- Estructura de carpetas (subscriptions) por plataforma
- URLs del creador por plataforma

**Query principal:**
```sql
-- Videos agrupados por plataforma y subscription
SELECT platform, subscription_name, list_types, COUNT(*) as count
FROM [query anterior]
GROUP BY platform, subscription_name;
```

### 2. Página de Suscripción Cuenta (`/subscription/account/:accountName`)
**Datos necesarios:**
- Todos los videos de esa cuenta
- Estructura de listas disponibles
- Metadata de la cuenta

### 3. Página de Lista Especial (`/subscription/:type/:id`)
**Datos necesarios:**
- Videos de esa lista específica
- Información de la subscription (nombre, URL, tipo)
- Creador asociado (si aplica)

## Comandos Disponibles

### Obtener estadísticas de BDs externas
```bash
python main.py db-stats --external-sources
```

### Poblar BD desde fuente específica
```bash
# YouTube desde 4K Video Downloader
python main.py populate-db --source db --platform youtube --limit 5

# TikTok desde 4K Tokkit  
python main.py populate-db --source db --platform tiktok --limit 10

# Instagram desde 4K Stogram
python main.py populate-db --source db --platform instagram --limit 15

# Todas las plataformas disponibles
python main.py populate-db --source db --limit 50
```

## Consideraciones Técnicas

### Performance
- Mantener todos los índices existentes
- Agregar índices en `creator_id`, `subscription_id`
- Índices compuestos para queries de frontend

### Integridad de Datos
- Foreign keys con CASCADE DELETE
- Constraints para tipos válidos
- Validación de URLs en backend

### Escalabilidad
- Estructura preparada para nuevas plataformas
- Metadata JSON flexible por tipo de subscription
- Sistema de soft delete preservado

Esta estructura permite manejar la complejidad de múltiples plataformas mientras mantiene la funcionalidad existente del sistema de procesamiento IA y edición manual.