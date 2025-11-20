# Estructura Final de Base de Datos y Frontend - Tag-Flow V2

## 📊 **Backend: Esquema de Base de Datos**

### **1. platforms** (Normalización)
```sql
CREATE TABLE platforms (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,        -- 'youtube', 'tiktok', 'instagram', 'bilibili', 'facebook', 'twitter'
    display_name TEXT NOT NULL,       -- 'YouTube', 'TikTok', 'Instagram', etc.
    base_url TEXT,                    -- 'https://www.youtube.com'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data inicial
INSERT INTO platforms (name, display_name, base_url) VALUES
('youtube', 'YouTube', 'https://www.youtube.com'),
('tiktok', 'TikTok', 'https://www.tiktok.com'),
('instagram', 'Instagram', 'https://www.instagram.com'),
('bilibili', 'Bilibili', 'https://www.bilibili.com'),
('facebook', 'Facebook', 'https://www.facebook.com'),
('twitter', 'Twitter/X', 'https://x.com');
```

### **2. creators** (Jerarquía y Mapeo)
```sql
CREATE TABLE creators (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    platform_id INTEGER REFERENCES platforms(id),
    
    -- Jerarquía de creadores (aliases)
    parent_creator_id INTEGER REFERENCES creators(id),
    is_primary BOOLEAN DEFAULT FALSE,
    alias_type TEXT CHECK(alias_type IN ('main', 'alias', 'variation')),
    
    -- IDs externos (conservados)
    platform_creator_id TEXT,        -- mid de Bilibili, etc.
    profile_url TEXT,                -- URL del perfil
    
    -- Metadata esencial
    creator_name_source TEXT CHECK(creator_name_source IN ('db', 'api', 'scraping', 'manual')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_creators_platform ON creators(platform_id);
CREATE INDEX idx_creators_parent ON creators(parent_creator_id);
CREATE UNIQUE INDEX idx_creators_platform_unique ON creators(platform_id, platform_creator_id) WHERE platform_creator_id IS NOT NULL;
```

### **3. subscriptions** (Fuentes de Contenido)
```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    platform_id INTEGER REFERENCES platforms(id),

    -- Tipo de suscripción (basado en 4K apps)
    subscription_type TEXT CHECK(subscription_type IN ('account', 'playlist', 'hashtag', 'location', 'music', 'search', 'liked', 'saved', 'folder')) NOT NULL,
    have_account BOOLEAN DEFAULT FALSE, -- TRUE para cuentas (contenido propio del creador)
    
    -- Referencias
    creator_id INTEGER REFERENCES creators(id), -- Para suscripciones de cuenta
    subscription_url TEXT,
    external_uuid TEXT, -- databaseId de 4K apps para recovery
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_platform ON subscriptions(platform_id);
CREATE INDEX idx_subscriptions_creator ON subscriptions(creator_id);
CREATE INDEX idx_subscriptions_type ON subscriptions(subscription_type);
CREATE INDEX idx_subscriptions_account ON subscriptions(have_account);
```

#### **Mapeo Correcto de 4K Apps a Subscriptions**

| App | External UUID | Subscription Type | Have Account | Category Type | Descripción |
|-----|--------------|------------------|------------|---------------|-------------|
| **4K YouTube** | type=5 | account | TRUE | videos/shorts | Contenido propio del creador |
| **4K YouTube** | type=3 | playlist | TRUE | videos/shorts | Listas del creador (Liked videos/Videos que me gustan, Watch Later/Ver más tarde) |
| **4K YouTube** | type=3 | search | FALSE | videos/shorts | Busqueda |
| **4K TikTok** | type=1 + downloadFeed=1 | account | TRUE | videos | Feed del creador |
| **4K TikTok** | type=1 + downloadLiked=1 | liked | TRUE | videos | Videos que le gustan al creador |
| **4K TikTok** | type=1 + downloadFavorites=1 | saved | TRUE | videos | Favoritos del creador |
| **4K TikTok** | type=2 | hashtag | FALSE | videos | Hashtag |
| **4K TikTok** | type=3 | music | FALSE | videos | Música |
| **4K Stogram** | type=1 | account | TRUE | feed/reels/stories/etc | Cuenta de Instagram |
| **4K Stogram** | type=2 | hashtag | FALSE | feed/reels | Hashtag |
| **4K Stogram** | type=3 | location | FALSE | feed/reels | Ubicación |
| **4K Stogram** | type=4 | saved | TRUE | feed/reels | Contenido guardado |

### **Estrategia de Vinculación de Creadores**

#### **Poblado Automático (Conservador)**

**Reglas Automáticas:**
1. **Misma plataforma + mismo nombre exacto** → Auto-vinculación con `parent_creator_id`
   - Ejemplo: "MMDnoECCHY" (YouTube) → "MMDnoECCHY" (YouTube, canal secundario)
   - `alias_type = 'variation'`, `is_primary = FALSE`

2. **Cross-platform (diferentes plataformas)** → **NO auto-vincular**
   - Ejemplo: "MMD Archives Daily" (YouTube) + "gianfrancisyap" (TikTok) → Creadores independientes
   - Evita falsos positivos por nombres genéricos o similares

**Estructura Resultante:**
```sql
-- Ejemplo: Creadores independientes por plataforma
YouTube: "MMD Archives Daily" (ID: 123) → is_primary=TRUE, parent_creator_id=NULL
TikTok:  "gianfrancisyap" (ID: 456)     → is_primary=TRUE, parent_creator_id=NULL  
TikTok:  "gian.francis.yap" (ID: 789)   → is_primary=TRUE, parent_creator_id=NULL

-- Solo mismo nombre + misma plataforma se auto-vincula:
YouTube: "MMDnoECCHY" (ID: 100)        → is_primary=TRUE, parent_creator_id=NULL
YouTube: "MMDnoECCHY" (ID: 101)        → is_primary=FALSE, parent_creator_id=100, alias_type='variation'
```

#### **Sistema de Sugerencias (Frontend Manual)**

**Query para detectar posibles matches cross-platform:**
```sql
-- Encuentra creadores con nombres/handles similares en diferentes plataformas
SELECT c1.id, c1.name, c1.platform_id, c1.platform_creator_id, p1.name as platform1,
       c2.id, c2.name, c2.platform_id, c2.platform_creator_id, p2.name as platform2,
       -- Métricas de similitud
       CASE 
         WHEN LOWER(c1.platform_creator_id) = LOWER(c2.platform_creator_id) THEN 'exact_handle'
         WHEN LOWER(REPLACE(c1.platform_creator_id, '.', '')) = LOWER(REPLACE(c2.platform_creator_id, '.', '')) THEN 'similar_handle'
         WHEN LOWER(c1.name) = LOWER(c2.name) THEN 'exact_name'
         ELSE 'potential'
       END as match_confidence
FROM creators c1, creators c2, platforms p1, platforms p2
WHERE c1.platform_id != c2.platform_id
  AND c1.id < c2.id  -- Evitar duplicados
  AND c1.platform_id = p1.id AND c2.platform_id = p2.id
  AND c1.parent_creator_id IS NULL AND c2.parent_creator_id IS NULL  -- Solo principales
  AND (
    -- Handles muy similares (sin puntos/guiones)
    LOWER(REPLACE(REPLACE(c1.platform_creator_id, '.', ''), '-', '')) = 
    LOWER(REPLACE(REPLACE(c2.platform_creator_id, '.', ''), '-', ''))
    -- O nombres exactos
    OR LOWER(c1.name) = LOWER(c2.name)
  )
ORDER BY match_confidence, c1.name;
```

**Flujo de Vinculación Manual:**
1. **Algoritmo genera sugerencias** basado en similitud de nombres/handles
2. **Admin revisa en panel** con vista previa de ambos creadores
3. **Vinculación manual** mediante drag-and-drop o botón "Vincular"
4. **Resultado**: Jerarquía correcta sin falsos positivos

**Ventajas del Enfoque Conservador:**
- ✅ **Sin falsos positivos** durante el poblado automático
- ✅ **Poblado rápido** sin análisis complejo
- ✅ **Flexibilidad total** para correcciones manuales
- ✅ **Escalable** para grandes volúmenes de datos

### **4. posts** (Publicaciones)
```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    
    -- Identificación
    platform_id INTEGER REFERENCES platforms(id) NOT NULL,
    platform_post_id TEXT,          -- ID del post en la plataforma original
    post_url TEXT,                  -- URL original del post
    
    -- Contenido
    title_post TEXT,                 -- Título/descripción del post
    use_filename BOOLEAN DEFAULT FALSE,  -- Indicates if title_post was populated using filename
    
    -- Creador y suscripción
    creator_id INTEGER REFERENCES creators(id),
    subscription_id INTEGER REFERENCES subscriptions(id),
    
    -- Fechas
    publication_date INTEGER,        -- Unix timestamp - fecha real de publicación
    publication_date_source TEXT CHECK(publication_date_source IN ('4k_bd', 'api', 'scraping', 'parsing', 'fallback')),
    publication_date_confidence INTEGER CHECK(publication_date_confidence BETWEEN 0 AND 100),
    
    download_date INTEGER,           -- Unix timestamp - fecha de descarga
    
    -- Carrusel handling
    is_carousel BOOLEAN DEFAULT FALSE,
    carousel_count INTEGER DEFAULT 1,
    
    -- Sistema
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    deleted_by TEXT,
    deletion_reason TEXT
);

CREATE INDEX idx_posts_platform ON posts(platform_id);
CREATE INDEX idx_posts_creator ON posts(creator_id);
CREATE INDEX idx_posts_subscription ON posts(subscription_id);
CREATE INDEX idx_posts_publication_date ON posts(publication_date);
CREATE INDEX idx_posts_download_date ON posts(download_date);
CREATE INDEX idx_posts_deleted ON posts(deleted_at);
-- REMOVED: Unique constraint on platform_post_id to allow same video in multiple lists/downloads
-- This enables same TikTok video to exist in multiple folders (Liked, Feed, etc.)
```

### **5. media** (Datos técnicos de archivos)
```sql
CREATE TABLE media (
    id INTEGER PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) NOT NULL,
    
    -- Files
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    thumbnail_path TEXT,
    file_size INTEGER,
    duration_seconds INTEGER,
    
    -- Media específico
    media_type TEXT CHECK(media_type IN ('video', 'image', 'audio')) NOT NULL,
    resolution_width INTEGER,
    resolution_height INTEGER,
    fps INTEGER,
    
    -- Carrusel
    carousel_order INTEGER DEFAULT 0, -- Orden en carrusel (0 = único/primero)
    is_primary BOOLEAN DEFAULT TRUE,   -- Primer item del carrusel
    
    -- AI Recognition
    detected_music TEXT,
    detected_music_artist TEXT,
    detected_music_confidence REAL,
    detected_characters TEXT,          -- JSON array
    music_source TEXT CHECK(music_source IN ('youtube', 'spotify', 'acrcloud', 'manual')),
    
    -- Manual editing
    final_music TEXT,
    final_music_artist TEXT,
    final_characters TEXT,             -- JSON array
    difficulty_level TEXT CHECK(difficulty_level IN ('low', 'medium', 'high')),
    edit_status TEXT CHECK(edit_status IN ('pendiente', 'en_proceso', 'completado', 'descartado')) DEFAULT 'pendiente',
    edited_video_path TEXT,
    notes TEXT,
    processing_status TEXT CHECK(processing_status IN ('pending', 'processing', 'completed', 'failed', 'skipped')) DEFAULT 'pending',
    
    -- Sistema
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_media_post ON media(post_id);
CREATE INDEX idx_media_type ON media(media_type);
CREATE INDEX idx_media_carousel ON media(post_id, carousel_order);
CREATE INDEX idx_media_primary ON media(is_primary);
CREATE INDEX idx_media_edit_status ON media(edit_status);
CREATE INDEX idx_media_processing_status ON media(processing_status);
```

### **6. post_categories** (Tipos de contenido - simplificado)
```sql
CREATE TABLE post_categories (
    id INTEGER PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) NOT NULL,
    category_type TEXT CHECK(category_type IN ('videos', 'shorts', 'feed', 'reels', 'stories', 'highlights', 'tagged')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_post_categories_post ON post_categories(post_id);
CREATE INDEX idx_post_categories_type ON post_categories(category_type);
CREATE UNIQUE INDEX idx_post_categories_unique ON post_categories(post_id, category_type);
```

#### **Categorías por plataforma**

| Plataforma | Category Types | Lógica de Asignación |
|------------|----------------|---------------------|
| **YouTube** | videos, shorts | Dimensiones + duración: >60s=videos, ≤60s+vertical=shorts |
| **TikTok** | videos | Todos son videos (TikTok no tiene shorts) |
| **Instagram** | feed, reels, stories, highlights, tagged | Por ruta de archivo: `/reels/`, `/stories/`, etc. |
| **Bilibili** | videos, shorts | Similar a YouTube |
| **Facebook** | videos | Principalmente videos |
| **Twitter** | videos | Videos de Twitter/X |

### **7. downloader_mapping** (Solo esencial)
```sql
CREATE TABLE downloader_mapping (
    id INTEGER PRIMARY KEY,
    media_id INTEGER REFERENCES media(id) NOT NULL,
    
    -- Mapping a BD externa (solo esencial)
    download_item_id INTEGER,
    external_db_source TEXT NOT NULL, -- '4k_youtube', '4k_tokkit', '4k_stogram'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_downloader_mapping_media ON downloader_mapping(media_id);
CREATE INDEX idx_downloader_mapping_source ON downloader_mapping(external_db_source);
CREATE INDEX idx_downloader_mapping_download_item ON downloader_mapping(download_item_id, external_db_source);
```

---

## 📱 **Frontend: Estructuras de Datos y Navegación**

Esta sección describe las interfaces de TypeScript y los conceptos de navegación que el frontend utilizará para interactuar con la data del backend.

### **1. Interfaces Principales de TypeScript (`types.ts`)**

#### **`Creator` Interface**
Representa a un creador de contenido.

```typescript
export interface Creator {
    id: number;
    name: string;
    displayName: string;
    platforms: Partial<Record<string, CreatorPlatformInfo>>; // Clave es platform.name
}
```

#### **`CreatorPlatformInfo` Interface**
Detalles de un creador en una plataforma específica.

```typescript
export interface CreatorPlatformInfo {
  url: string;
  postCount: number;
  subscriptions: Subscription[];
}
```

#### **`Subscription` Interface**
Fuente de contenido básica, siempre ligada a un creador.

```typescript
export interface Subscription {
  id: number;
}
```

#### **`SubscriptionInfo` Interface**
Vista detallada para páginas de suscripción, incluyendo suscripciones "especiales" (hashtags, música).

```typescript
export interface SubscriptionInfo {
    id: number;
    name: string;
    type: string;
    platform: string; // platform.name
    url?: string;
    postCount: number;
}
```

#### **`Post` y `Media` Interfaces**
Representan una publicación y sus archivos multimedia asociados.

```typescript
export interface Post {
  id: number;
  platformName: string;
  postUrl: string;
  title: string;
  creatorName: string;
  subscriptionId: number;
  publicationDate: string; // ISO 8601
  downloadDate: string;    // ISO 8601
  media: Media[];
}

export interface Media {
    id: number;
    filePath: string;
    thumbnailPath?: string;
    type: 'video' | 'image';
    resolution: string; // e.g., "1920x1080"
    duration: number; // en segundos
}
```

### **2. Concepto de Navegación y Tabs**

La navegación del frontend se basa en si se visualiza un `Creator` o una `Subscription` y el tipo de esta.

#### **Páginas de Creador (`/creator/:creatorName`)**
Muestran una vista agregada de todo el contenido de un creador a través de sus plataformas y suscripciones. Los tabs permiten filtrar por tipo de contenido.

```typescript
// Ejemplo de tabs para la página de un creador
const creatorTabs = {
  youtube: ['All', 'Videos', 'Shorts', 'Listas'],
  tiktok: ['All', 'Videos', 'Lista Saved', 'Liked'],
  instagram: ['All', 'Reels', 'Stories', 'Highlights', 'Tagged', 'Saved'],
};
```

#### **Páginas de Suscripción (`/subscription/:type/:id`)**
La vista depende del tipo de suscripción:

1.  **Suscripciones de Cuenta (`have_account: true`)**: Replican la experiencia de la app original (ej. 4K Tokkit) y tienen tabs para filtrar contenido.
    ```typescript
    // URL: /subscription/account/mrbeast-youtube
    const accountSubscriptionTabs = {
      youtube: ['All', 'Videos', 'Shorts'],
      tiktok: ['All', 'Videos'],
      instagram: ['All', 'Feed', 'Reels', 'Stories'],
    };
    ```

2.  **Suscripciones de Lista/Tema (`have_account: false`)**: Son listas simples de contenido (ej. por hashtag, música) y no tienen tabs.
    ```typescript
    // URL: /subscription/hashtag/dance-tiktok
    // URL: /subscription/music/phonk-tiktok

    ```

### **3. Lógica de Componentes en Frontend**

```typescript
// Lógica para determinar si se muestran tabs
function shouldShowTabs(subscriptionType: string, isAccount: boolean): boolean {
  return subscriptionType === 'account' && isAccount;
}

  if (!shouldShowTabs(subscriptionType, isAccount)) {
function buildTabs(platform: string, subscriptionType: string, isAccount: boolean): string[] | null {
  if (!shouldShowTabs(subscriptionType, isAccount)) {
    return null; // Sin tabs para listas simples
  }

  const platformTabs: { [key: string]: string[] } = {
    youtube: ['All', 'Videos', 'Shorts'],
    tiktok: ['All', 'Videos'],
  };
    default: ['All', 'Videos'],
  return platformTabs[platform] || platformTabs.default;
}
```