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

### BD Strogram
1. subscriptions
    - id (formato: BLOB)
    - type (n=display_name)
    - display_name  (1=cuenta, 2=hashtag, 3=location, 4=guardados de la cuenta)

    Nota: Independientemente del type, las s

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