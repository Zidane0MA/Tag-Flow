# Extracción de Fechas de Publicación de Posts

## Objetivo
Obtener tanto la **fecha real de publicación** del contenido original como la **fecha de descarga** para análisis temporal completo en Tag-Flow V2.

## Estado Actual por Plataforma

### ✅ **Plataformas con fechas completas**
| Plataforma | Fuente | Fecha Publicación | Fecha Descarga | Estado |
|------------|--------|------------------|----------------|--------|
| **YouTube** | 4K Video Downloader | ❌ (valor -1) | ✅ timestampNs | Requiere API |
| **TikTok** | 4K Tokkit | ✅ postingDate | ✅ recordingDate | ✅ Completo |
| **Instagram** | 4K Stogram | ❌ Sin fecha publicación | ✅ created_time | ⚠️ Requiere extracción |

### ⚠️ **Plataformas con limitaciones**
| Plataforma | Fuente | Fecha Publicación | Fecha Descarga | Estado |
|------------|--------|------------------|----------------|--------|
| **Bilibili** | 4K Video Downloader | ❌ (valor -1) | ✅ timestampNs | Requiere extracción |
| **Facebook** | 4K Video Downloader | ❌ (valor -1) | ✅ timestampNs | Requiere extracción |
| **Twitter/X** | 4K Video Downloader | ❌ (valor -1) | ✅ timestampNs | Requiere extracción |

## Métodos de Extracción Disponibles

### 1. **APIs Oficiales** 🏛️

#### **YouTube Data API v3**
- **Estado**: ✅ Ya configurado en Tag-Flow
- **Costo**: Gratuito hasta 10,000 requests/día
- **Datos**: `publishedAt`, `title`, `description`, `duration`, `statistics`
- **Limitación**: Requiere API key

#### **Twitter/X API v2** 
- **Estado**: ⚠️ Requiere configuración
- **Costo**: Gratuito hasta 500,000 tweets/mes (Basic)
- **Datos**: `created_at`, `text`, `public_metrics`
- **Limitación**: Requiere Bearer Token

#### **Bilibili Open API**
- **Estado**: ⚠️ No implementado
- **Costo**: 🆓 Gratuito
- **Datos**: `pubdate`, `title`, `desc`, `stat` (views, likes)
- **Limitación**: No requiere autenticación

#### **Facebook Graph API**
- **Estado**: ❌ Muy limitado
- **Costo**: Gratuito con limitaciones
- **Datos**: `created_time`, solo para contenido autorizado
- **Limitación**: Requiere permisos especiales del negocio

### 2. **Parsing sin API** 🔍

#### **Twitter Snowflake ID Extraction**
- **Método**: Decodificar timestamp del ID del tweet
- **Ejemplo**: `1692590883299029104` → `2023-08-18T20:15:23Z`
- **Ventaja**: 🆓 Sin API, máxima precisión
- **Implementación**: Algoritmo matemático simple

#### **URL Pattern Analysis**
- **Casos específicos**: Algunos IDs contienen timestamps
- **Ejemplo**: YouTube video IDs tienen patrones temporales
- **Limitación**: No universal, específico por plataforma

### 3. **Web Scraping** 🕸️

#### **Ventajas**
- ✅ **Sin límites de API** - No tokens requeridos
- ✅ **Contenido público completo** - Sin restricciones de permisos
- ✅ **Costo cero** - No hay límites de requests
- ✅ **Datos adicionales** - Views, likes, comentarios, etc.

#### **Desafíos**
- ⚠️ **Fragilidad** - Cambios HTML rompen scrapers
- ⚠️ **Rate limiting** - Posible bloqueo de IP
- ⚠️ **JavaScript** - Contenido dinámico requiere herramientas especiales
- ⚠️ **Anti-bot** - Detección Cloudflare, CAPTCHAs

#### **Herramientas recomendadas**
- **Contenido estático**: BeautifulSoup + requests
- **Contenido JavaScript**: Playwright o Selenium
- **Scraping masivo**: Scrapy framework
- **Anti-detección**: undetected-chromedriver

### 4. **Metadata Extraction** 📄

#### **HTML Meta Tags**
- `<meta property="video:release_date" content="...">`
- `<meta itemprop="datePublished" content="...">`
- `<meta name="pubdate" content="...">`

#### **JSON-LD Structured Data**
- Schema.org VideoObject
- OpenGraph meta properties
- Platform-specific embedded JSON

## Estrategia de Implementación Recomendada

### **Fase 1: APIs Prioritarias** 🎯
1. **YouTube Data API** - Extender implementación existente
2. **Bilibili API** - Implementación simple, sin auth
3. **Twitter Snowflake** - Parsing matemático, sin API

### **Fase 2: Web Scraping Selectivo** 🕷️
1. **Facebook** - API muy restrictivo
2. **Instagram** - Solo para verificación (ya tenemos created_time)
3. **Plataformas menores** - Sin APIs disponibles

### **Fase 3: Refinamiento** 🔧
1. **Caching inteligente** - Evitar requests repetidos
2. **Fallback robusto** - Múltiples métodos por plataforma
3. **Rate limiting** - Respeto a límites de servidor
4. **Error handling** - Degradación graceful

## Estructura de Datos Propuesta

### **Campos adicionales en BD**
```sql
-- Nuevos campos para videos table
ALTER TABLE videos ADD COLUMN publication_date INTEGER; -- Unix timestamp fecha real
ALTER TABLE videos ADD COLUMN publication_date_source TEXT; -- 'api', 'scraping', 'parsing', 'fallback'
ALTER TABLE videos ADD COLUMN publication_date_confidence INTEGER; -- 0-100 confiabilidad
```

### **Prioridad de fuentes** (mayor a menor confiabilidad)
1. **API oficial** - Confiabilidad 100%
2. **Snowflake/ID parsing** - Confiabilidad 95%
3. **Web scraping** - Confiabilidad 80%
4. **Metadata HTML** - Confiabilidad 70%
5. **Fecha descarga** - Confiabilidad 10% (fallback)

## Plan de Desarrollo

### **Inmediato**
- [ ] Extender YouTube API para extraer `publishedAt`
- [ ] Implementar Twitter Snowflake decoder
- [ ] Crear sistema de fallback con `timestampNs`

### **Corto plazo**
- [ ] Bilibili API integration
- [ ] Web scraping para Facebook
- [ ] Sistema de cache para evitar requests duplicados

### **Medio plazo**
- [ ] Scrapers robustos con anti-detección
- [ ] Rate limiting inteligente
- [ ] Métricas de confiabilidad y éxito

### **Largo plazo**
- [ ] ML para validación de fechas extraídas
- [ ] Auto-detección de cambios en estructura HTML
- [ ] Dashboard de monitoreo de extracción

## Casos de Uso

### **Análisis Temporal**
- **Trending detection**: Videos populares vs recientes
- **Content aging**: Rendimiento por antigüedad
- **Release patterns**: Horarios óptimos de publicación

### **Data Quality**
- **Verification**: Comparar fecha publicación vs descarga
- **Anomaly detection**: Videos con fechas inconsistentes  
- **Content freshness**: Identificar contenido obsoleto

### **User Experience**
- **Chronological sorting**: Orden real de publicación
- **Time-based filtering**: Contenido por rangos de fecha
- **Publication insights**: Estadísticas de creadores

## Extracción de Creadores

### **Problema identificado**
Algunas plataformas en 4K Video Downloader **no proporcionan información del creador**:

| Plataforma | Fuente | Creator Info | Estado |
|------------|--------|--------------|--------|
| **YouTube** | 4K Video Downloader | ✅ En metadata (type=0) | ✅ Completo |
| **TikTok** | 4K Tokkit | ✅ authorName | ✅ Completo |
| **Instagram** | 4K Stogram | ✅ ownerName | ✅ Completo |
| **Bilibili** | 4K Video Downloader | ❌ Sin datos creator | ⚠️ Requiere extracción |
| **Facebook** | 4K Video Downloader | ❌ Sin datos creator | ⚠️ Requiere extracción |

### **Métodos de extracción para creadores**

#### **1. Bilibili API** 🎯
```json
GET https://api.bilibili.com/x/web-interface/view?bvid=BV1s8eMzeEoj

Response:
{
  "data": {
    "owner": {
      "mid": 123456789,           // ID único del creador
      "name": "creador_nombre",   // Nombre display
      "face": "avatar_url"        // URL del avatar
    },
    "pubdate": 1692590883,        // Timestamp Unix publicación
    "title": "Video title"
  }
}
```

**URL del creador se arma como:**
```
https://space.bilibili.com/{owner.mid}
Ejemplo: https://space.bilibili.com/123456789
```

#### **2. Facebook Graph API** (Limitado)
- Requiere permisos especiales
- Solo funciona para páginas públicas verificadas
- No funciona para usuarios individuales

#### **3. Web Scraping** 🕷️
**Bilibili HTML parsing**:
- Buscar `<meta name="author" content="...">`
- Extraer de JSON embebido `window.__INITIAL_STATE__`
- Parsing del elemento creator en DOM

**Facebook scraping**:
- Más complejo debido a protecciones anti-bot
- Requiere herramientas como Playwright
- Buscar elementos de perfil en HTML

### **Implementación recomendada**

#### **Fase 1: APIs cuando disponibles**
1. **Bilibili API** - Gratuito, datos completos
2. **URL parsing** - Extraer username de URLs cuando sea posible

#### **Fase 2: Web scraping como fallback**
1. **HTML metadata** - Meta tags estándar
2. **DOM parsing** - Elementos específicos de plataforma
3. **JSON extraction** - Datos embebidos en JavaScript

#### **Estructura de datos propuesta**
```sql
-- Campos adicionales para creadores
ALTER TABLE videos ADD COLUMN creator_name_source TEXT; -- 'db', 'api', 'scraping', 'url_parsing'
ALTER TABLE videos ADD COLUMN creator_url TEXT; -- URL del perfil del creador
ALTER TABLE videos ADD COLUMN creator_id TEXT; -- ID único del creador en la plataforma
```

#### **URLs de creadores por plataforma**
| Plataforma | Patrón URL | Ejemplo |
|------------|------------|---------|
| **YouTube** | `https://www.youtube.com/@{username}` | `https://www.youtube.com/@MrBeast` |
| **TikTok** | `https://www.tiktok.com/@{authorName}` | `https://www.tiktok.com/@upminaa.cos` |
| **Instagram** | `https://www.instagram.com/{ownerName}` | `https://www.instagram.com/foggyneko` |
| **Bilibili** | `https://space.bilibili.com/{mid}` | `https://space.bilibili.com/123456789` |
| **Twitter/X** | `https://x.com/{username}` | `https://x.com/suzuR423` |

## Notas Técnicas

- **Rate Limits**: Implementar delays apropiados entre requests
- **Caching Strategy**: Cache por URL con TTL de 30 días mínimo
- **Error Handling**: Log detallado para debugging
- **Monitoring**: Métricas de éxito/fallo por método
- **Scalability**: Procesamiento asíncrono para lotes grandes
- **Creator Deduplication**: Normalizar nombres para evitar duplicados

---

**Estado del documento**: Versión inicial - Pendiente refinamiento tras ajustes de BD