## PROMPT for 4K
Las apps de 4k permiten agrupar contenido bajo el nombre de suscripciones que no son mas que listas.

## CASO: 4k Video downloader (Maneja youtube y otras plataformas)
### BD 4k video downloader
download_item
- id
- filename
  - D:\4K Video Downloader+\value(type=3 o type=5)\NOMBREDELVIDEO.mp4
  - D:\4K Video Downloader+\NOMBREDELVIDEO.mkv
- timestampNs (BIGINT nanosegundos desde época Unix - momento exacto de descarga)

media_item_metadata
- download_item_id
- type (n=value)
- value

  Notas:
  - Solo hay videos de la plataforma de youtube (sea lista o no)
  - Las suscripciones de tipo playlist (lista de likes y otras listas) manejan: type(0=creator post, 1=url creator, 3=playlist name, 4=url playlist, 7=downloader_subscription_info(uuid))
  - Los suscripciones de tipo account manejan: type(0=creator post, 1=url creator, 5=playlist name, 6=url playlist, 7=downloader_subscription_info(uuid))
  - Videos de youtube sueltos que no pertenecen a suscripciones manejan: type(0=creator post, 1=url creator)

media_item_description
  - download_item_id
  - id
  - title
  - duration (para usar en duration_seconds)

url_description
  - media_item_description_id
  - service_name (Nombre de la plataforma)
  - url (url del video)

media_info
  - download_item_id
  - id

video_info
  - media_info_id
  - dimension 
  - resolution
  - fps

Nota:
- Los videos de otras plataformas no figuran en `media_item_metadata` por lo que no tienen informacion de `type` y `value`, crear los campos de todas formas, los campos faltantes se agregaran desde el frontend. (Facebook, bilibili, etc.) se debe soportar el autodescubrimiento de estas plataformas.
- Como la url del creador se puede armar como `http://www.youtube.com/@type(0)`
- Los videos deben ser registrados en video_lists.list_type, como (short o video) segun sus dimensiones.

Objetivos:
- Poblar los campos de mi base de datos con estos campos.

## CASO: 4k Tokkit (Solo Tiktok)
### Contexto
La app agrupa los videos de diferentes maneras:
- Publicaciones sueltas como: `\\Single videos\\video.mp4|imagen.jpg`, vistas desde la db en la tabla `MediaItems` y tienen `subscriptionDatabaseId` como NULL. Descargados como publicaciones individuales
- Suscripcion como cuenta (`type` = 1): Estas se registran como un grupo en la tabla `Subscriptions` (tienen un `type`) y sus publicaciones se registran en la tabla `MediaItems` donde llevan su respectivo `subscriptionDatabaseId` y `authorName`. Estas carpetas tienen la siguiente estructura:
  - Feed: `\\name\\video.mp4|imagen.jpg`
  - `\\name\\Liked`
  - `\\name\\Favorites`
  > Nota: Algunas suscripciones tendran el mismo name y type pero la app las guarda bajo la misma carpeta `\\name`.

- Suscripcion como Listas (`type` = 2,3): Estas se registran similar al anterior pero tienen sus particularidades:
  - `type` = 2: La carpeta de este tipo se guarda con un #.
      - `\\#name\\video.mp4|imagen.jpg`
  - `type` = 3: La carpeta de este tipo se guarda con un "(Subscriptions.id)".
      - `\\name(Subscriptions.id)\\video.mp4|imagen.jpg`

- Importante: 
  - Las imagenes se guardan como por ejemplo: `anxl3tii_1754166899_7534089319917735182_index_0_3.jpeg`
  - La MediaItems.id de las imagenes son como: `7534089319917735182_index_0_3`
  - Para armar la url e identificar las imagenes de un del post se necesita el campo MediaItems.id sin `_index_n1_n2`
  - Para el orden de las imagenes para el carrusel del frontend necesitamos de `_index_n1_n2` el valor n1 (en orden menor a mayor)

### BD Tokkit
Subscriptions
  - databaseId (BLOB, equivalente a UUID)
  - type (n=name)
  - name (1=cuenta, 2=hashtag, 3=musica)
  - id (para armar la url de la lista tipo musica)

  Notas:
  - url tipo cuenta se arman como `https://www.tiktok.com/@name`
  - url tipo hashtag se arman como `https://www.tiktok.com/tag/name`
  - url tipo musica se arman como `https://www.tiktok.com/music/name-Subscriptions.id`
    - Cuando es tipo musica el name puede tener espacios, se deben rellenar con "-"
    - Ejemplo "cancion nueva cinco" -> "cancion-nueva-cinco"

SubscriptionsDownloadSettings
  - subscriptionDatabaseId (BLOB)
  - downloadFeed (0 = FALSE, 1 = TRUE) (Mostrar como videos en mi bd)
  - downloadLiked (0 = FALSE, 1 = TRUE)
  - downloadFavorites (0 = FALSE, 1 = TRUE)

MediaItems
  - databaseId (BLOB)
  - subscriptionDatabaseId (BLOB)
  - MediaType(2=video, 3=imagen) (1=coverimg[ignorar])
  - id (para armar la url del post)
  - authorName
  - description (usar como titulo del post)
  - postingDate (INT segundos Unix - fecha de publicación en TikTok)
  - recordingDate (INT segundos Unix - fecha de descarga/procesamiento por 4K Tokkit)
  - downloaded (1=si) (Importante para solo poblar los videos descargados y no generar errores)
  - relativePath
  - height 
  - width 

  Notas:
  - Links de los posts tipo video se arman como `https://www.tiktok.com/@authorName/video/MediaItems.id`
  - Links de los posts tipo imagen se arman como `https://www.tiktok.com/@authorName/photo/MediaItems.id(sin _index_n1_n2)`

## CASO: 4k Strogram (Solo Instagram | ver. gratuita)
### Contexto
La app agrupa los videos de diferentes maneras:
- Publicaciones sueltas como: `\\Single media\\video.mp4|imagen.jpg`, vistas desde la db en la tabla `photos` y tienen `subscriptionId` como NULL. Descargados como publicaciones individuales
- Resto de Publicaciones como: `\\display_name`, Estas se registran como un grupo en la tabla `subscriptions` (tienen un `type`) y sus publicaciones se registran en la tabla `photos` que llevan su respectivo `subscriptionId` y `ownerName`. Estas carpetas tienen la siguiente estructura:
  - `\\display_name\\imagen.jpg` (feed)
  - `\\display_name\\highlights`
  - `\\display_name\\reels`
  - `\\display_name\\story`
  - `\\display_name\\tagged`

### BD Strogram
1. subscriptions
    - id (formato: BLOB)
    - type (n=display_name)
    - display_name  (1=cuenta, 2=hashtag, 3=location, 4=saved)

2. photos
    - subscriptionId
    - web_url (url de la publicacion)
    - title (titulo/descripcion de la publicacion)
    - file (path relativo de la publicacion)
    - is_video (65=video, [!65]=imagen)
    - state (4=descargado)
    - ownerName (Creador de la publicacion)
    - ownerId (Identificador del creador)
    - created_time (INTEGER segundos Unix - fecha de creación del post original, coincide exactamente con fecha del archivo)

    Nota:
    - Como no se puede asociar la publicaciones con el tipo directamente desde la bd, se tendra que usar el campo `file` que los agrupa correctamente.
    - Como sabes instagram tambien maneja publicaciones tipo carrusel/múltiple, la unica forma de saber que imagenes son parte de una misma publicacion es con el campo `web_url`, para saber el orden solo tenemos photos.id de menor a mayor.

### TIMESTAMPS COMPARACIÓN
| BD                  | Campo          | Formato        | Propósito                           | Precisión  |
|---------------------|----------------|----------------|-------------------------------------|------------|
| 4K Video Downloader| timestampNs    | BIGINT (ns)    | Momento exacto de descarga          | ⭐⭐⭐⭐⭐ |
| 4K Tokkit          | postingDate    | INT (s)        | Fecha publicación TikTok            | ⭐⭐⭐    |
| 4K Tokkit          | recordingDate  | INT (s)        | Fecha descarga/procesamiento        | ⭐⭐⭐⭐  |
| 4K Stogram         | created_time   | INT (s)        | Fecha creación post (coincide archivo) | ⭐⭐⭐⭐⭐ |

**Recomendaciones:**
- Usar `timestampNs` para orden cronológico de importación 
- `recordingDate` coincide con fecha del archivo (confirmado como descarga)
- `created_time` más preciso para cronología de posts originales


## PROMPT for Carpetas Organizadas
Debido al limite de plataformas de las apps de 4k, se considero integrar wfdownloader en mi sistema para obtener datos importantes para el poblado del contenido de estas carpetas. Esto debe coexistir con las carpetas que no son parte de la nueva estructura.

### ESTRUCTURA DE CARPETAS (en fase de desarrollo)

```
D:\4K All\
├── Plataforma\
│   ├── Suscripcion tipo Cuenta | Creador\
│   │   ├── folfer.json        # Metadata del folder
│   │   ├── video1.mp4
│   │   └── video2.mp4
│   └── Suscripcion tipo lista\
│       ├── folder.json        # Metadata de la lista
│       └── MrBeast\
│           ├── folder.json    # Metadata del creador
│           └── video_like.mp4
```

- Para el caso de Suscripcion tipo Cuenta | Creador, folder.json determina si es una suscripcion o no.
- Suscripcion tipo lista siempre es una suscripcion.

### Tipos de descarga en wfdownloader
El programa maneja suscripciones para links que sean de tipo cuenta o lista, las cuales se pueden abordar de diferentes maneras, investigando encontre que para obtener los datos debo crear 2 suscripciones en wfdownloader.

https://x.com/suzuR423/status/1692590883299029104

armar la url del creador: https://x.com/`nombre de la carpeta`

El nombre del archivo debe ser de este tipo: 1692590637256958031_1.mp4
- Para armar la url del crea

Para un suscripcion tipo cuenta | creador: https://x.com/ImmortalsNine, debido a que con una sola sucrip

necesito 2 capertas:
- D:\4K All\X\ImmortalsNine.data, que es usad


### JSON wfdownloader
La app wfdownloader, me permite extraer datos que necesito de la siguiente forma, por ejemplo para la plataforma X (Twitter):

#### Creado

```json

```

### JSON OTHER
El json folder.json


        "has_media": "true",

        "is_retweet": "false",
        "is_quoted_tweet": "true",
        "is_reply_tweet": "false",