# Arquitectura de Suscripciones - Tag Flow V2

## 📋 Resumen del Problema

El sistema actual presenta varios desafíos arquitectónicos relacionados con la gestión de suscripciones y agrupación de contenido:

1. **Fragmentación de suscripciones similares** (ej: YouTube likes en múltiples suscripciones)
2. **Single Videos multiplataforma confusos** en el frontend
3. **Falta de jerarquía playlist-cuenta** 
4. **Inconsistencias entre fuentes de datos** (4K Apps vs carpetas organizadas)

## 🔍 Análisis Detallado de Problemas

### 1. Fragmentación de Suscripciones (YouTube Likes)

**Problema identificado:**
- "liked videos" (desde 4K Video Downloader)
- "videos que me gustan" (desde 4K Video Downloader) 
- Videos movidos a carpetas organizadas
- **Resultado:** 3 suscripciones para el mismo concepto

**Información adicional pendiente de investigar:**
- ✅ **Confirmado:** Misma UUID en BD de YouTube para ambos nombres
- ✅ **Confirmado:** Se guardan bajo la misma carpeta `//liked videos//`
- 🔍 **Por investigar:** Patrones exactos de nomenclatura en BD externa
- 🔍 **Por investigar:** Otros casos similares (Watch Later, Created Playlists, etc.)

### 2. Single Videos Multiplataforma

**Problema actual:**
```
Suscripciones en BD:
- "Single videos" (YouTube)
- "Single videos" (Facebook) 
- "Single videos" (Bilibili)
- "Single videos" (Twitter)
```

**Confusión en frontend:**
- Múltiples suscripciones con el mismo nombre
- No se distingue la plataforma sin filtros adicionales
- Mezcla conceptos diferentes (videos de apps vs organizados)

### 3. Carpetas Organizadas - Oportunidades JSON

**Estructura actual:**
```
D:\4K All\
├── Youtube\
│   ├── MrBeast\
│   │   ├── video1.mp4
│   │   └── video2.mp4
│   └── liked videos\
│       └── video_like.mp4
├── Tiktok\
└── Instagram\
```

**Propuesta de mejora con JSON:**
```
D:\4K All\
├── Plataforma\
│   ├── MrBeast\
│   │   ├── ???.json        # Metadata del creador
│   │   ├── media.json      # Metadata de los videos
│   │   ├── video1.mp4
│   │   └── video2.mp4
│   └── liked videos\
│       ├── ???.json        # Metadata de la lista
│       ├── media.json      # Metadata de los videos
│       └── MrBeast\
│           ├── ???.json    # Metadata del creador
│           └── video_like.mp4
```

**Tipos de Json**
- `???.json`
- `???.json`
- `media.json`

### 4. Jerarquía Playlist-Cuenta

**Contenido de archivos JSON (propuesta):**
```json
// creator.json
{
  "creator_name": "MrBeast",
  "platform": "youtube",
  "urls": {
    "main": "https://www.youtube.com/@MrBeast"
  },
  "subscription_type": "none",  // "subscription_type": "account"
  "metadata": {
  }
}

// playlist.json (para liked videos, playlists, etc.)
{
  "subscription_name": "Liked Videos",
  "subscription_type": "List",
  "platform": "youtube", 
  "creator_id": "MrBeast_or_UUID",
  "list_types": ["liked"],
  "merge_with_existing": {
    "uuid": "same_uuid_from_4k_app",
    "names": ["liked videos", "videos que me gustan"]
  }
}
```

## 🔧 Arquitectura Actual (Base de Datos)

### Tablas Relevantes:

```sql
-- Creadores
CREATE TABLE creators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_creator_id INTEGER REFERENCES creators(id),
    is_primary BOOLEAN DEFAULT TRUE,
    alias_type TEXT DEFAULT 'main'
);

-- Suscripciones
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,             -- "Canal X", "Mi Playlist", "#hashtag"
    type TEXT NOT NULL,             -- 'account', 'playlist', 'music', 'hashtag', 'location', 'saved', 'personal', 'folder'
    platform TEXT NOT NULL,        -- 'youtube', 'tiktok', 'instagram', 'facebook'
    creator_id INTEGER REFERENCES creators(id), -- Para jerarquías
    subscription_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Listas por video
CREATE TABLE video_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL REFERENCES videos(id),
    list_type TEXT NOT NULL,       -- 'feed', 'liked', 'reels', 'stories', 'single', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Limitaciones Identificadas:

1. **Sin normalización de nombres similares**
2. **Sin campo para UUID externa** (para linking con 4K Apps)
3. **Sin jerarquía parent-child** para suscripciones
4. **Sin identificación de fuente** (4K App vs Organizado vs Manual)

## 💡 Opciones de Solución Evaluadas

### Para Single Videos:

| Opción | Descripción | Pros | Contras | Recomendación |
|--------|-------------|------|---------|---------------|
| **A** | Eliminar Single Videos | Simplifica frontend, usa filtros de galería | Pierde agrupación semántica | ⭐⭐⭐ |
| **B** | Single Videos unificado | Una sola suscripción | Mezcla plataformas | ⭐⭐ |
| **C** | Por plataforma con nombres únicos | Diferenciación clara | Múltiples suscripciones | ⭐⭐ |
| **D** | Campo source_app | Máxima flexibilidad | Cambio mayor de esquema | ⭐⭐⭐⭐ |

### Para Jerarquía Playlist-Cuenta:

**Solución recomendada:** Usar `creator_id` existente en tabla `subscriptions`

```sql
-- Ejemplo de jerarquía:
-- Cuenta principal
INSERT INTO subscriptions (name, type, platform, creator_id, subscription_url) 
VALUES ('MrBeast', 'account', 'youtube', 123, 'https://youtube.com/@MrBeast');

-- Playlists de esa cuenta  
INSERT INTO subscriptions (name, type, platform, creator_id, subscription_url)
VALUES ('Challenge Videos', 'playlist', 'youtube', 123, 'https://youtube.com/playlist?list=...');
```

## 🚀 Plan de Implementación Propuesto

### Fase 1: Immediate Fix (Próxima sesión)
- [ ] **Eliminar "Single Videos" confusos**
  - Modificar lógica en `external_sources.py`
  - Videos de 4K Downloader sin suscripción especial → usar filtros de galería
  
### Fase 2: Consolidación de Duplicados (Investigación requerida)
- [ ] **Investigar UUID matching en YouTube BD**
  - Extraer UUIDs de BD externa de 4K Video Downloader
  - Mapear nombres similares a UUID canónico
  - Crear tabla de aliases/normalización
  
- [ ] **Script de consolidación**
  - Detectar suscripciones duplicadas por UUID
  - Migrar videos a suscripción canónica
  - Eliminar duplicados

### Fase 3: Sistema JSON para Carpetas Organizadas (Mediano plazo)
- [ ] **Definir estructura JSON estándar**
  - `creator.json` para metadatos de creador
  - `playlist.json` para listas especiales
  - `merge_config.json` para linking con BD existente
  
- [ ] **Implementar detector JSON**
  - Modificar `extract_organized_videos()` 
  - Leer JSON cuando esté disponible
  - Fallback a comportamiento actual

### Fase 4: Jerarquía Completa (Largo plazo)
- [ ] **Extender esquema BD**
  ```sql
  ALTER TABLE subscriptions ADD COLUMN parent_subscription_id INTEGER REFERENCES subscriptions(id);
  ALTER TABLE subscriptions ADD COLUMN external_uuid TEXT; -- Para linking con 4K Apps
  ALTER TABLE subscriptions ADD COLUMN subscription_source TEXT; -- '4k_app', 'organized', 'user_created'
  ```
  
- [ ] **Frontend jerárquico**
  - Vista principal: Cuentas/Creadores
  - Vista cuenta: Playlists asociadas + feed
  - Vista filtros: Por plataforma (reemplaza Single Videos)

## 🔍 Investigación Pendiente

### Información a confirmar:

1. **YouTube BD Structure (4K Video Downloader):**
   - [ ] Estructura exacta de UUIDs para liked videos
   - [ ] Otros casos de duplicación (Watch Later, etc.)
   - [ ] Patrón de nomenclatura en diferentes idiomas
   
2. **Carpetas Organizadas:**
   - [ ] Estructura actual completa de `D:\4K All`
   - [ ] Casos especiales (videos movidos manualmente)
   - [ ] Viabilidad de sistema JSON propuesto
   
3. **Frontend Requirements:**
   - [ ] UX esperada para jerarquía playlist-cuenta
   - [ ] Comportamiento deseado para "videos sin organizar"
   - [ ] Filtros y búsquedas necesarias

### Preguntas abiertas:

1. **¿Conservar Single Videos temporalmente** hasta implementar filtros mejorados?
2. **¿Priorizar consolidación UUID** o implementar JSON system primero?
3. **¿Migración automática** de datos existentes o proceso manual controlado?
4. **¿Impacto en React frontend** actual durante transición?

## 📝 Decisiones Pendientes

- [ ] **Estrategia para Single Videos:** Eliminar vs Reformular vs Mantener
- [ ] **Esquema de migración:** Automático vs Manual vs Híbrido  
- [ ] **Orden de implementación:** UUID consolidation vs JSON system vs Frontend changes
- [ ] **Backward compatibility:** Mantener APIs existentes durante transición

## 🎯 Próximos Pasos Inmediatos

1. **Investigar BD de 4K Video Downloader** para confirmar estructura UUID
2. **Revisar carpetas organizadas actuales** para validar propuesta JSON
3. **Decidir estrategia definitiva** para Single Videos
4. **Implementar primer fix** (eliminar confusión actual)

---

**Última actualización:** 2025-08-13  
**Estado:** En investigación y diseño  
**Prioridad:** Alta (afecta UX del frontend React)