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
  - Las suscripciones de tipo playlist (lista de likes y otras listas) manejan: type(0=creator post, 1=url creator, 3=playlist name, 4=url playlist, 7=downloader_subscription_info(uuid))
  - Los creadores manejan: type(0=creator post, 1=url creator, 5=playlist name, 6=url playlist, 7=downloader_subscription_info(uuid))
  - Videos de youtube sueltos que no pertenecen a listas: type(0=creator post, 1=url creator)

media_item_description
  - download_item_id
  - title

url_description
  - media_item_description_id
  - service_name (Nombre de la plataforma)
  - url (url del video)

Nota:
- Los videos de otras plataformas no figuran en `media_item_metadata` por lo que no tienen informacion de `type` y `value`, crear los campos de todas formas, los campos faltantes se agregaran desde el frontend. (Facebook, bilibili, etc.) se debe soportar el autodescubrimiento de estas plataformas.
- Como la url del creador se puede armar como `http://www.youtube.com/@type(0)`


Problemas con el poblado de la base de datos:
- Videos sueltos como `D:\4K Video Downloader+\NOMBREDELVIDEO.mkv` que vienen de la app 4k video downloader, se poblan teniendo como suscripciones el nombre del creador en el caso de youtube y el nombre/titulo del video para otras plataformas. Quiero que todos estos videos sueltos se guarden en mi bd bajo la suscripcion de Single media y de type folder similar a instagram.

- En tiktok un creador sin contenido propio (no figura en la tabla de creadores), se le asiga un creador_id no relacionado.

- shorts de youtube, encontrar solucion.


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
  - databaseId
  - type (n=name)
  - name (1=cuenta, 2=hashtag, 3=musica)
  - id (para armar la url de la lista tipo musica)

  Notas:
  - url tipo cuenta se arman como `https://www.tiktok.com/@name`
  - url tipo hashtag se arman como `https://www.tiktok.com/tag/name`
  - url tipo musica se arman como `https://www.tiktok.com/music/name-Subscriptions.id`
    - Cuando es tipo musica el name puede tener espacios, se deben rellenar con "-"
    - Ejemplo "cancion nueva cinco" -> "cancion-nueva-cinco"

MediaItems
  - databaseId
  - subscriptionDatabaseId
  - MediaType(2=video, 3=imagen) (1=coverimg[ignorar])
  - id (para armar la url del post)
  - authorName
  - description (usar como titulo del post)
  - downloaded (1=si) (Importante para solo poblar los videos descargados y no generar errores)
  - relativePath

  Notas:
  - Links de los posts tipo video se arman como `https://www.tiktok.com/@authorName/video/MediaItems.id`
  - Links de los posts tipo imagen se arman como `https://www.tiktok.com/@authorName/photo/MediaItems.id(sin _index_n1_n2)`

### Objetivos
- Las Publicaciones sueltas seran listas al igual que las Suscripcion como Listas (`type` = 2,3).
- Las Publicaciones como cuenta (`type` = 1) seran subcripciones de tipo cuenta en mi bd y tendran tabs subtabs como "feed, Liked, Favorites".

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

2. photos
    - subscriptionId
    - web_url (url de la publicacion)
    - title (titulo/descripcion de la publicacion)
    - file (path relativo de la publicacion)
    - is_video (65=video, [0,2]=imagen)
    - state (4=descargado)
    - ownerName (Creador de la publicacion)

    Nota:
    - Como no se puede asociar la publicaciones con el tipo directamente desde la bd, se tendra que usar el campo `file` que los agrupa correctamente.
    - Para las imagenes no me fio de file por lo que sera mejor comprobar la extension desde `file`.
    - Como sabes instagram tambien maneja publicaciones tipo carrusel/múltiple, la unica forma de saber que imagenes son parte de una misma publicacion es con el campo `web_url`, para saber el orden solo tenemos photos.id de menor a mayor.

## Consideraciones:
1. `python -X utf8 main.py populate-db --source db --platform youtube --limit 5` debe extraer los videos de la app de 4k con plataforma youtube, sean de listas o individuales. 
`python -X utf8 main.py populate-db --source db --platform facebook --limit 5` debe extraer los videos de la app de 4k con plataforma facebook.
1. `python -X utf8 main.py process --source db --platform youtube --limit 5` cuando el limite es mayor a los videos de la bd se tiene una funcion de poblar bd, esta funcion debe soportar lo anterior.