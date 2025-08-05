## PROMPT
Bien, como sabes ciertos comandos tienen la caracteristica de autodescubrir plataformas, me he dado cuenta que la app 4k video downloader puede descargar desde mas plataformas, aunque tiene preferencia por youtube, dando del creador, tambien ofrece mas datos si es una playlist como los likes.
Es una situacion muy compleja, por ejemplo si ingreso `python -X utf8 main.py populate-db --source db --platform youtube --limit 5`, actualmente se extraen todos los videos incluso de otras plataformas.
Necesito un saber que plataformas estan disponibles desde un comando:`python -X utf8 main.py db-stats`.

Las apps de 4k permiten agrupar contenido bajo el nombre de suscripciones que no son mas que listas.
Al final lo que quiero agregar a mi db es: url del post (imagen/video), url del creador, la lista que pertenece el post, link de la lista.
Los creadores pueden estar en multiples plataformas por lo que se tiene que manejar la url del creador de alguna forma. El algunos casos se pueden armar desde el frontend dependiendo de la plataforma, en otros casos no.

## CASO: 4k Video downloader (Maneja youtube y otras plataformas)
### BD 4k video downloader
download_item
- filename
  - D:\4K Video Downloader+\playlist name\NOMBREDELVIDEO.mp4
  - D:\4K Video Downloader+\NOMBREDELVIDEO.mkv

media_item_metadata
- download_item_id
- type (n=value)
- value

  Notas:
  - Solo hay videos de la plataforma de youtube (sea lista o no)
  - Las lista de likes y otras listas manejan: type(0=creator post, 1=url creator, 3=playlist name, 4=url playlist, 7=downloader_subscription_info(uuid))
  - Los creadores manejan: type(0=creator post, 1=url creator, 5=playlist name, 6=url playlist, 7=downloader_subscription_info(uuid))
  - Videos de youtube sueltos que no pertenecen a listas: type(0=creator post, 1=url creator)

media_item_description
  - download_item_id
  - title

url_description
  - media_item_description_id
  - service_name (Nombre de la plataforma)
  - url (link del video)

Nota:
- Los videos de otras plataformas no figuran en `media_item_metadata` por lo que no tienen informacion de `type` y `value`, crear los campos de todas formas, los campos faltantes se agregaran desde el frontend.
- Como la url del creador se puede armar como `http://www.youtube.com/@type(0)`

## CASO: 4k Tokkit (Solo Tiktok)
### BD Tokkit
Subscriptions
  - databaseId
  - type (n=name)
  - name (1=cuenta, 2=hashtag, 3=musica)
  - id (para armar la url de la lista tipo musica)

  Notas:
  - url tipo cuenta se arman como `https://www.tiktok.com/@name`
  - url tipo hashtag se arman como `https://www.tiktok.com/tag/name`
  - url tipo musica se arman como `https://www.tiktok.com/music/name-id`
    - Cuando es tipo musica el name puede tener espacios, se deben rellenar con "-"
    - Ejemplo "cancion nueva cinco" -> "cancion-nueva-cinco"

MediaItems
  - databaseId
  - subscriptionDatabaseId
  - id (para armar la url del post)
  - authorName
  - description (usar como titulo del post)
  - relativePath
    - \name\video.mp4
    - \name\Liked\video.mp4
    - \name\Favorites\video.mp4

  Notas:
  - Links de los posts se arman como `https://www.tiktok.com/@authorName/video/id`

SubscriptionsDownloadSettings
  - subscriptionDatabaseId
  - downloadFeed (0,1)
  - downloadLiked (0,1)
  - downloadFavorites (0,1)

Nota:
- `downloadFavorites` Son los favoritos de tu cuenta
- Sabiendo lo anterior entonces las combinaciones posibles son:
  - downloadFeed y downloadLiked ambos pueden ser 0 o 1 por lo que se tendra que manejar el nombre de la lista.
  - downloadFavorites es incompatible con los anteriores por lo que no hay problemas.
- Se puede usar esto o la informacion del relativePath.

## CASO: 4k Strogram (Solo Instagram)
### Contexto
La app agrupa los videos de diferentes maneras:
- Publicaciones sueltas como: `\\Single media\\video.mp4|imagen.jpg`, vistas desde la db en la tabla `photos` y tienen `subscriptionId` como NULL. Descargados como publicaciones individuales
- Resto de Publicaciones como: `\\display_name`, Estas se registran como un grupo en la tabla `subscriptions` (tienen un `type`) y sus publicaciones se registran en la tabla `photos` que llevan su respectivo `subscriptionId` y `ownerName`. Estas carpetas tienen la siguiente estructura:
  - `\\display_name\\imagen.jpg`
  - `\\display_name\\highlights`
  - `\\display_name\\reels`
  - `\\display_name\\story`
  - `\\display_name\\tagged`

### Tabla de tipos de suscripciones y flags

| display_name | type | downloadPhotos | downloadVideos | downloadFeed | downloadStories | downloadHighlights | downloadTaggedPosts | downloadReels |
|--------------|------|----------------|----------------|--------------|-----------------|--------------------|---------------------|---------------|
| cuenta       | 1    | 1              | 1              | 1            | 1               | 1                  | 0                   | 0             |
| hashtag      | 2    | 1              | 1              | 1            | 1               | 1                  | 0                   | 0             |
| location     | 3    | 1              | 1              | 1            | 1               | 1                  | 0                   | 0             |
| saved        | 4    | 1              | 1              | 1            | 0               | 0                  | 0                   | 0             |

### Objetivo futuro
1. Para el caso de instagram en el frontend la card de una publicacion tendra un apartado de listas que al presionar me muestre los videos de esas listas. Se tendran:
    - Publicaciones guardadas (saved) de un display_name
    - Publicaciones etiquetadas (tagged) de un display_name
    - Publicaciones de historias (story) de un display_name
    - Publicaciones de reels (reels) de un display_name
    - Publicaciones de highlights (Highlights) de un display_name
    - Publicaciones por hashtag de un display_name
    - Publicaciones por location de un display_name
    - Publicaciones por cuenta de un display_name
2. Para el caso de las imagenes que pertenecen a una misma publicacion se necesitara crear una interfaz de carrusel/múltiple [tipo tiktok], se tendra info como [n/m].

### BD Strogram
1. subscriptions
    - id (formato: BLOB)
    - type (n=display_name)
    - display_name  (1=cuenta, 2=hashtag, 3=location, 4=guardados de la cuenta)
    - downloadPhotos (0,1)
    - downloadVideos (0,1)
    - downloadFeed (0,1)
    - downloadStories (0,1)
    - downloadHighlights (0,1)
    - downloadTaggedPosts (0,1)
    - downloadReels (0,1)

    Nota: Las listas seran usando las siguientes combinaciones:
      - `display_name` sera usado para estos casos:
        - Cuenta
        - Mis publicaciones guardadas (saved)
        - hashtags
        - location
      - `downloadFeed` para:
        - reels (video)
        - fuente (imagen)
      - `downloadStories` para:
        - historias
      - `downloadHighlights` para:
        - destacados (Highlights)
      - `downloadTaggedPosts` para:
        - etiquetado
      - `downloadReels` para:
        - reels
      - Links de la lista se arman como:
        - `https://www.instagram.com/display_name/`
        - `https://www.instagram.com/display_name/saved/` 
        - `https://www.instagram.com/display_name/reels/`
        - `https://www.instagram.com/display_name/tagged/`

2. photos
    - subscriptionId
    - web_url (url de la publicacion)
    - title (titulo/descripcion de la publicacion)
    - file (path relativo de la publicacion)
    - is_video (65=video, [0,2]=imagen)
    - ownerName (Creador de la publicacion)

    Nota:
    - Como no se puede asociar la publicaciones con el tipo directamente desde la bd, se tendra que usar el campo `file` que los agrupa correctamente.
    - Para las imagenes no me fio de file por lo que sera mejor comprobar la extension desde `file`.
    - Como sabes instagram tambien maneja publicaciones tipo carrusel/múltiple, la unica forma de saber que imagenes son parte de una misma publicacion es con el campo `web_url`.

## Consideraciones:
1. `python -X utf8 main.py populate-db --source db --platform youtube --limit 5` debe extraer los videos de la app de 4k con plataforma youtube, sean de listas o individuales. 
`python -X utf8 main.py populate-db --source db --platform facebook --limit 5` debe extraer los videos de la app de 4k con plataforma facebook.
1. `python -X utf8 main.py process --source db --platform youtube --limit 5` cuando el limite es mayor a los videos de la bd se tiene una funcion de poblar bd, esta funcion debe soportar lo anterior.