# Estructura Final de Base de Datos - Tag-Flow V2

## 📊 **Esquema Limpio y Optimizado**

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

### **2. creators** (Simplificado pero funcional)
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

### **3. subscriptions** (Simplificado)
```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    platform_id INTEGER REFERENCES platforms(id),
    
    -- Tipo de suscripción (basado en 4K apps)
    subscription_type TEXT CHECK(subscription_type IN ('account', 'playlist', 'hashtag', 'location', 'music', 'search', 'liked', 'saved', 'folder')) NOT NULL,
    is_account BOOLEAN DEFAULT FALSE, -- TRUE para cuentas (contenido propio del creador)
    
    -- Referencias
    creator_id INTEGER REFERENCES creators(id), -- Para suscripciones de cuenta
    subscription_url TEXT,
    external_uuid TEXT,              -- databaseId de 4K apps para recovery
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_platform ON subscriptions(platform_id);
CREATE INDEX idx_subscriptions_creator ON subscriptions(creator_id);
CREATE INDEX idx_subscriptions_type ON subscriptions(subscription_type);
CREATE INDEX idx_subscriptions_account ON subscriptions(is_account);
```

#### **Mapeo Correcto de 4K Apps a Subscriptions**

| App | External UUID | Subscription Type | Is Account | Category Type | Descripción |
|-----|--------------|------------------|------------|---------------|-------------|
| **4K YouTube** | type=5 | account | TRUE | videos/shorts | Contenido propio del creador |
| **4K YouTube** | type=3 | playlist | FALSE | videos/shorts | Listas del creador (Liked, Watch Later) |
| **4K TikTok** | type=1 + downloadFeed=1 | account | TRUE | videos | Feed del creador |
| **4K TikTok** | type=1 + downloadLiked=1 | liked | FALSE | videos | Videos que le gustan al creador |
| **4K TikTok** | type=1 + downloadFavorites=1 | saved | FALSE | videos | Favoritos del creador |
| **4K TikTok** | type=2 | hashtag | FALSE | videos | Hashtag |
| **4K TikTok** | type=3 | music | FALSE | videos | Música |
| **4K Stogram** | type=1 | account | TRUE | feed/reels/stories | Cuenta de Instagram |
| **4K Stogram** | type=2 | hashtag | FALSE | feed/reels | Hashtag |
| **4K Stogram** | type=4 | saved | FALSE | feed/reels | Contenido guardado |

### **4. posts** (Concepto principal - limpio)
```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    
    -- Identificación
    platform_id INTEGER REFERENCES platforms(id) NOT NULL,
    platform_post_id TEXT,          -- ID del post en la plataforma original
    post_url TEXT,                  -- URL original del post
    
    -- Contenido
    title_post TEXT,                 -- Título/descripción del post
    
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
CREATE UNIQUE INDEX idx_posts_platform_unique ON posts(platform_id, platform_post_id) WHERE platform_post_id IS NOT NULL;
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

## 🎯 **Ventajas del Diseño Final**

### **Frontend Performance**
1. **Una query para carrusel completo**: `SELECT * FROM posts JOIN media WHERE post_id = ? ORDER BY carousel_order`
2. **Filtros eficientes**: Índices optimizados para todas las búsquedas comunes
3. **Joins mínimos**: Estructura normalizada pero no sobre-normalizada

### **Lógica de Negocio Clara**
1. **Posts = Publicaciones** reales de redes sociales
2. **Media = Archivos técnicos** (videos/imágenes del post)
3. **Categorías = Tipo de contenido** (videos, shorts, reels, etc.)
4. **Subscriptions = Agrupación** (account vs listas vs hashtags)

### **Mapeo 4K Apps Correcto**
```sql
-- ✅ CORRECTO: TikTok "Liked" es una suscripción, no categoría
subscription_type = 'liked'
category_type = 'videos'  -- El contenido sigue siendo video

-- ✅ CORRECTO: Instagram Reels es categoría de contenido
subscription_type = 'account'  
category_type = 'reels'   -- Tipo específico de contenido
```

### **Queries Optimizadas**
```sql
-- Posts de un creador con media
SELECT p.*, m.* FROM posts p 
JOIN media m ON p.id = m.post_id 
WHERE p.creator_id = ? 
ORDER BY p.publication_date DESC;

-- Posts por suscripción y categoría
SELECT p.* FROM posts p
JOIN post_categories pc ON p.id = pc.post_id
WHERE p.subscription_id = ? AND pc.category_type = ?;

-- TikTok: Videos "liked" de un creador
SELECT p.* FROM posts p
JOIN subscriptions s ON p.subscription_id = s.id
WHERE s.creator_id = ? AND s.subscription_type = 'liked';
```

---

## 📱 **Frontend: Navegación y Tabs**

### **Concepto de Navegación**

#### **1. CREADORES** (Gestión interna de Tag-Flow)
```javascript
// URL: /creator/MrBeast
// Vista: Página completa del creador con todos sus datos y estadísticas
const creatorTabs = {
  youtube: ['All', 'Videos', 'Shorts', 'Listas'],
  tiktok: ['All', 'Videos', 'Lista Saved', 'Lista Liked'],
  instagram: ['All', 'Reels', 'Stories', 'Highlights', 'Tagged', 'Lista Saved'],
  other_platforms: ['All', 'Videos', 'Shorts']
}
```

#### **2. SUSCRIPCIONES TIPO CUENTA** (Simulación de 4K Apps)
```javascript
// URL: /subscription/youtube-mrbeast-account
// Vista: Simula la experiencia de suscripción en las apps 4K
// MISMOS TABS que creadores (replica la funcionalidad de la app original)
const accountSubscriptionTabs = {
  youtube: ['All', 'Videos', 'Shorts', 'Listas'],        // Simula 4K Video Downloader
  tiktok: ['All', 'Videos', 'Lista Saved', 'Lista Liked'], // Simula 4K Tokkit  
  instagram: ['All', 'Reels', 'Stories', 'Highlights', 'Tagged', 'Lista Saved'], // Simula 4K Stogram
  other_platforms: ['All', 'Videos', 'Shorts']
}
```

#### **3. SUSCRIPCIONES TIPO LISTA/TEMA** (Sin tabs)
```javascript
// URL: /subscription/tiktok-hashtag-dance
// URL: /subscription/youtube-search-mmd
// Vista: Lista simple de contenido, sin tabs adicionales
const listSubscriptions = {
  playlist: /* Lista simple de videos */,
  hashtag: /* Lista simple de videos por hashtag */,
  music: /* Lista simple de videos por música */,
  location: /* Lista simple de posts por ubicación */,
  search: /* Lista simple de resultados de búsqueda */
}
```

### **Estructura de Sidebar**

```javascript
const sidebarStructure = {
  creators: [
    {
      name: "MrBeast", 
      platform: "YouTube",
      url: "/creator/mrbeast-youtube",
      tabs: ['All', 'Videos', 'Shorts', 'Listas']
    },
    {
      name: "upminaa.cos",
      platform: "TikTok", 
      url: "/creator/upminaa-tiktok",
      tabs: ['All', 'Videos', 'Lista Saved', 'Lista Liked']
    }
  ],
  
  subscriptions: {
    accounts: [
      {
        name: "MrBeast (YouTube)",
        url: "/subscription/youtube-mrbeast-account",
        tabs: ['All', 'Videos', 'Shorts', 'Listas'], // Simula 4K Video Downloader
        type: "account"
      },
      {
        name: "upminaa.cos (TikTok)",
        url: "/subscription/tiktok-upminaa-account", 
        tabs: ['All', 'Videos', 'Lista Saved', 'Lista Liked'], // Simula 4K Tokkit
        type: "account"
      }
    ],
    
    lists: [
      {
        name: "#dance",
        platform: "TikTok",
        url: "/subscription/tiktok-hashtag-dance",
        tabs: null, // Lista simple sin tabs
        type: "hashtag"
      },
      {
        name: "Phonk Music",
        platform: "TikTok", 
        url: "/subscription/tiktok-music-phonk",
        tabs: null, // Lista simple sin tabs
        type: "music"
      },
      {
        name: "Search: MMD",
        platform: "YouTube",
        url: "/subscription/youtube-search-mmd", 
        tabs: null, // Lista simple sin tabs
        type: "search"
      }
    ]
  }
}
```

### **Queries por Tipo de Vista**

#### **Creadores (Vista completa)**
```sql
-- Contenido completo del creador (propio + listas)
SELECT p.*, pc.category_type FROM posts p
JOIN post_categories pc ON p.id = pc.post_id
JOIN subscriptions s ON p.subscription_id = s.id
WHERE s.creator_id = ? 
AND s.subscription_type IN ('account', 'liked', 'saved', 'playlist')
ORDER BY p.publication_date DESC;
```

#### **Suscripciones tipo Cuenta (Simula 4K Apps)**
```sql
-- Simula lo que verías en 4K Video Downloader suscrito a MrBeast
SELECT p.*, pc.category_type FROM posts p
JOIN post_categories pc ON p.id = pc.post_id  
WHERE p.subscription_id = ?
AND subscription_type = 'account'
AND is_account = TRUE
ORDER BY p.publication_date DESC;
```

#### **Suscripciones tipo Lista (Vista simple)**
```sql
-- Lista simple de contenido por hashtag/música/búsqueda
SELECT p.*, pc.category_type FROM posts p
JOIN post_categories pc ON p.id = pc.post_id
WHERE p.subscription_id = ?
AND subscription_type IN ('hashtag', 'music', 'search', 'location')
AND is_account = FALSE
ORDER BY p.publication_date DESC;
```

### **Frontend Component Logic**

```javascript
// Determinar si mostrar tabs o lista simple
function shouldShowTabs(subscriptionType, isAccount) {
  if (subscriptionType === 'account' && isAccount === true) {
    return true; // Suscripciones tipo cuenta tienen tabs
  }
  return false; // Listas/hashtags/música son listas simples
}

// Construir tabs dinámicamente
function buildTabs(platform, subscriptionType, isAccount) {
  if (!shouldShowTabs(subscriptionType, isAccount)) {
    return null; // Sin tabs, lista simple
  }
  
  // Tabs para cuentas (tanto creadores como suscripciones tipo cuenta)
  const platformTabs = {
    youtube: ['All', 'Videos', 'Shorts', 'Listas'],
    tiktok: ['All', 'Videos', 'Lista Saved', 'Lista Liked'],
    instagram: ['All', 'Reels', 'Stories', 'Highlights', 'Tagged', 'Lista Saved'],
    default: ['All', 'Videos', 'Shorts']
  };
  
  return platformTabs[platform] || platformTabs.default;
}
```

**¿Esta estructura final te parece sólida para implementar mañana?**