# 🔧 Sistema de Mantenimiento (`maintenance.py`)

Este documento detalla todos los comandos disponibles a través del script `maintenance.py`, diseñado para gestionar, mantener y verificar la integridad del ecosistema de Tag-Flow.

## Cómo Ejecutar Comandos

Para ejecutar cualquiera de los siguientes comandos, primero debes activar el entorno virtual de Python y luego ejecutar el script. Debido a la configuración de la consola en algunos sistemas, es recomendable usar el flag `-X utf8` para asegurar la correcta visualización de caracteres especiales.

```shell
# Activar el entorno virtual (en Windows)
tag-flow-env\Scripts\activate

# Sintaxis del comando
python -X utf8 maintenance.py [COMANDO] [OPCIONES]
```

---

## Comandos Disponibles

Los comandos se agrupan por funcionalidad:

### 📦 Operaciones de Backup

Gestiona la creación, restauración y limpieza de backups del sistema para salvaguardar la integridad de los datos.

- **`backup`**
  - **Función:** Crea un backup completo del sistema. Este proceso empaqueta los siguientes componentes en una carpeta o archivo ZIP:
    - **Base de datos:** `videos.db`
    - **Configuración:** Archivos como `config.py` y `.env`.
    - **Caras Conocidas:** El directorio `caras_conocidas`.
    - **Thumbnails:** Opcionalmente, una cantidad limitada de thumbnails para agilizar el proceso.
    - **Manifiesto:** Un archivo `manifest.json` que describe el contenido y la versión del backup.
  - **Opciones:**
    - `--compress`: Comprime la carpeta del backup en un único archivo `.zip` para un almacenamiento más eficiente.
    - `--no-thumbnails`: Excluye el directorio de thumbnails del backup para reducir su tamaño.
    - `--thumbnail-limit N`: Define el número máximo de thumbnails a incluir (por defecto: 100).
  - **Ejemplo:** `python -X utf8 maintenance.py backup --compress --thumbnail-limit 50`

- **`restore`**
  - **Función:** Restaura el sistema desde un archivo o carpeta de backup. Antes de sobrescribir los datos, crea automáticamente un **backup de seguridad** del estado actual (a menos que se use `--force`).
  - **Opciones:**
    - `--backup-path RUTA`: **(Obligatorio)** Especifica la ruta al archivo `.zip` o carpeta del backup a restaurar.
    - `--components [COMP...]`: Restaura solo componentes específicos. Los componentes válidos son: `database`, `thumbnails`, `configuration`, `known_faces`.
    - `--force`: Evita la creación del backup de seguridad previo y ejecuta la restauración directamente.
  - **Ejemplo:** `python -X utf8 maintenance.py restore --backup-path "backups/backup-2025-07-19.zip" --components database configuration`

- **`list-backups`**
  - **Función:** Muestra una lista de todos los backups `.zip` disponibles en el directorio `backups/`, ordenados del más reciente al más antiguo.
  - **Opciones:**
    - `--limit N`: Muestra solo los N backups más recientes.
  - **Ejemplo:** `python -X utf8 maintenance.py list-backups --limit 5`

- **`cleanup-backups`**
  - **Función:** Realiza una limpieza automática de backups antiguos para gestionar el espacio en disco. Por defecto, elimina los backups que cumplen cualquiera de estas condiciones:
    - Son más antiguos de **30 días**.
    - Hay más de **5 backups** en total (elimina los más viejos).
  - **Ejemplo:** `python -X utf8 maintenance.py cleanup-backups`

---

### 🔍 Operaciones de Integridad

Comandos diseñados para diagnosticar y reparar la salud de la base de datos, los archivos y la configuración del sistema.

- **`verify`**
  - **Función:** Realiza una revisión exhaustiva de la base de datos para detectar una amplia gama de inconsistencias, entre ellas:
    - **Corrupción de la base de datos:** Ejecuta una prueba `PRAGMA integrity_check`.
    - **Archivos de video faltantes:** Verifica que los videos referenciados en la BD existan en el disco.
    - **Rutas duplicadas:** Encuentra si varios registros de la BD apuntan al mismo archivo de video.
    - **Metadatos inválidos:** Busca videos sin información esencial como plataforma o creador.
    - **Thumbnails rotos:** Detecta tanto thumbnails referenciados pero no existentes (faltantes) como archivos de thumbnail que no corresponden a ningún video (huérfanos).
  - **Opciones:**
    - `--fix-issues`: Intenta corregir automáticamente ciertos problemas detectados, como la eliminación de thumbnails huérfanos y el relleno de metadatos básicos.
  - **Ejemplo:** `python -X utf8 maintenance.py verify --fix-issues`

- **`verify-files`**
  - **Función:** Se enfoca exclusivamente en verificar la existencia y accesibilidad de los archivos de video. Es útil para un diagnóstico rápido después de mover o eliminar archivos multimedia.
  - **Opciones:**
    - `--video-ids [ID...]`: Limita la verificación a una lista específica de IDs de video.
  - **Ejemplo:** `python -X utf8 maintenance.py verify-files`

- **`integrity-report`**
  - **Función:** Genera un informe consolidado que evalúa la salud general del sistema. Ejecuta todas las verificaciones (base de datos, archivos, thumbnails y configuración) y asigna una **puntuación de 0 a 100** a cada componente y una puntuación general. Lo más importante es que genera **recomendaciones** con los comandos exactos que puedes ejecutar para solucionar los problemas encontrados.
  - **Opciones:**
    - `--include-details`: Agrega al informe los resultados completos en formato JSON de cada módulo de verificación.
  - **Ejemplo:** `python -X utf8 maintenance.py integrity-report`

---

### 🖼️ Operaciones de Thumbnails

Administra la generación, limpieza y estadísticas de las miniaturas de los videos. Estos comandos están optimizados para un alto rendimiento.

- **`regenerate-thumbnails`**
  - **Función:** Inicia un proceso de regeneración inteligente y optimizado. Identifica videos con thumbnails faltantes o corruptos y los vuelve a generar. Para mayor eficiencia, prioriza los videos donde ya se han detectado personajes.
  - **Opciones:**
    - `--force`: Vuelve a generar los thumbnails para todos los videos, incluso si ya tienen uno válido.
  - **Ejemplo:** `python -X utf8 maintenance.py regenerate-thumbnails --force`

- **`populate-thumbnails`**
  - **Función:** Es el comando principal para crear thumbnails faltantes de forma masiva. Utiliza procesamiento en paralelo para generar las imágenes rápidamente.
  - **Opciones:**
    - `--platform PLATAFORMA`: Limita la operación a una plataforma específica (ej. `youtube`).
      - `youtube`, `tiktok`, `instagram`: Plataformas principales
      - `NOMBRE`: Plataforma específica por nombre (auto-detectada)
      - `other`: Solo plataformas adicionales (no principales)
      - `all-platforms`: Todas las plataformas (principales + adicionales)
    - `--limit N`: Establece un número máximo de thumbnails a generar.
    - `--force`: Genera thumbnails incluso para videos que ya los tienen.
  - **Ejemplo:** `python -X utf8 maintenance.py populate-thumbnails --platform youtube --limit 50`

- **`clean-thumbnails`**
  - **Función:** Busca y elimina archivos de imagen en la carpeta de thumbnails que no están asociados a ningún video en la base de datos (huérfanos). Es útil para liberar espacio en disco.
  - **Opciones:**
    - `--force`: Ejecuta la eliminación directamente. Sin este flag, el comando solo mostrará los archivos que se eliminarían, sin borrarlos.
  - **Ejemplo:** `python -X utf8 maintenance.py clean-thumbnails --force`

- **`thumbnail-stats`**
  - **Función:** Muestra un resumen estadístico del estado de los thumbnails, incluyendo el porcentaje de cobertura (videos con thumbnail), el número de archivos válidos, corruptos y faltantes.
  - **Ejemplo:** `python -X utf8 maintenance.py thumbnail-stats`

---

### 🗃️ Operaciones de Base de Datos

Comandos para poblar, optimizar, limpiar y obtener estadísticas de la base de datos principal.

- **`populate-db`**
  - **Función:** Importa videos a la base de datos desde las fuentes de datos externas (como las bases de datos de las aplicaciones de descarga de 4K) o desde las carpetas organizadas. El proceso está altamente optimizado:
    1.  **Filtra duplicados:** Comprueba qué videos ya existen en la base de datos para evitar trabajo redundante.
    2.  **Extrae metadatos en paralelo:** Procesa múltiples videos a la vez para obtener su información.
    3.  **Inserta en lotes:** Agrega los nuevos videos a la base de datos en grupos grandes para mayor eficiencia.
  - **Opciones:**
    - `--source {db,organized,all}`: Define el origen de los datos
      - `db`: Solo bases de datos externas (4K Apps)
      - `organized`: Solo carpetas organizadas (`ORGANIZED_BASE_PATH`)
      - `all`: Ambas fuentes (por defecto)
    - `--platform PLATFORM`: Limita la importación a una plataforma específica (ej. `tiktok`).
      - `youtube`, `tiktok`, `instagram`: Plataformas principales
      - `NOMBRE`: Plataforma específica por nombre (auto-detectada)
      - `other`: Solo plataformas adicionales (no principales)
      - `all-platforms`: Todas las plataformas (principales + adicionales)
    - `--limit N`: Importa como máximo N videos nuevos.
    - `--force`: Vuelve a importar y sobrescribe la información de videos que ya están en la base de datos.
    - `--file-path RUTA`: Importa únicamente el archivo de video especificado.
  - **Ejemplo:** `python -X utf8 maintenance.py populate-db --source all --platform tiktok`

- **`optimize-db`**
  - **Función:** Realiza un mantenimiento esencial sobre el archivo de la base de datos (`videos.db`). Ejecuta dos comandos clave de SQLite:
    - **`VACUUM`**: Reconstruye la base de datos para defragmentarla y reducir su tamaño en disco.
    - **`ANALYZE`**: Recolecta estadísticas sobre las tablas y los índices para que el motor de consultas pueda tomar decisiones más inteligentes y rápidas.
    - **Asegura Índices**: Verifica y crea los índices necesarios para acelerar las búsquedas comunes.
  - **Ejemplo:** `python -X utf8 maintenance.py optimize-db`

- **`clear-db`**
  - **Función:** Elimina registros de videos de la base de datos. Si no se especifica una plataforma, **eliminará todos los videos** y reseteará el contador de IDs.
  - **Opciones:**
    - `--platform PLATAFORMA`: Elimina únicamente los registros de la plataforma especificada.
      - `youtube`, `tiktok`, `instagram`: Plataformas principales
      - `NOMBRE`: Plataforma específica por nombre (auto-detectada)
      - `other`: Solo plataformas adicionales (no principales)
      - `all-platforms`: Todas las plataformas (principales + adicionales)
    - `--force`: Ejecuta la eliminación sin pedir confirmación.
  - **Ejemplo:** `python -X utf8 maintenance.py clear-db --platform tiktok --force`

- **`db-stats`**
  - **Función:** Proporciona un informe detallado con estadísticas clave sobre la base de datos, incluyendo:
    - Número total de videos.
    - Distribución de videos por plataforma.
    - Estado (cuántos tienen thumbnails, personajes, etc.).
    - Estadísticas de tamaño de archivos (promedio, máximo, mínimo).
    - Información del archivo de la base de datos (tamaño, versión).
  - **Ejemplo:** `python -X utf8 maintenance.py db-stats`

---

### 👤 Operaciones de Personajes

Comandos centrados en la gestión de la base de datos de personajes y la inteligencia de detección.

- **`character-stats`**
  - **Función:** Muestra un resumen completo del sistema de `Character Intelligence`. Proporciona estadísticas clave como el número total de personajes y juegos, el tipo de detector que se está utilizando y la cantidad de mapeos de creadores.
  - **Ejemplo:** `python -X utf8 maintenance.py character-stats`

- **`add-character`**
  - **Función:** Permite añadir un nuevo personaje personalizado a la base de datos (`character_database.json`). Esto es crucial para que el sistema pueda reconocer a nuevos personajes en los títulos de los videos.
  - **Opciones:**
    - `--character NOMBRE`: **(Obligatorio)** El nombre del personaje.
    - `--game JUEGO`: **(Obligatorio)** El juego o franquicia a la que pertenece.
    - `--aliases [ALIAS...]`: Nombres alternativos o apodos para el personaje.
  - **Ejemplo:** `python -X utf8 maintenance.py add-character --character "Jane Doe" --game "Zenless Zone Zero" --aliases "JD" "Doe"`

- **`clean-false-positives`**
  - **Función:** Revisa todos los videos y elimina las detecciones de personajes que son claramente incorrectas. Utiliza una lista interna de palabras comunes y genéricas (como "and", "the", "girl") para limpiar los datos y mejorar la precisión.
  - **Ejemplo:** `python -X utf8 maintenance.py clean-false-positives`

- **`update-creator-mappings`**
  - **Función:** Analiza los videos de cada creador para identificar con qué personaje o juego están más asociados. Si un creador sube contenido de un personaje específico con una confianza superior al 60%, se crea un mapeo automático para mejorar futuras detecciones.
  - **Ejemplo:** `python -X utf8 maintenance.py update-creator-mappings`

- **`analyze-titles`**
  - **Función:** Procesa los títulos de los videos para extraer patrones, como las palabras más frecuentes y los personajes más mencionados. Es una herramienta útil para entender las tendencias en los datos.
  - **Opciones:**
    - `--limit N`: Limita el análisis a los N videos más recientes.
  - **Ejemplo:** `python -X utf8 maintenance.py analyze-titles --limit 1000`

- **`download-character-images`**
  - **Función:** (Actualmente en modo de simulación) Descarga imágenes para los personajes en la base de datos y las guarda en la carpeta `caras_conocidas`. El objetivo de esta función es preparar el sistema para un futuro reconocimiento facial.
  - **Opciones:**
    - `--character NOMBRE`: Descarga imágenes para un personaje específico.
    - `--game JUEGO`: Limita la descarga a un juego o franquicia.
  - **Ejemplo:** `python -X utf8 maintenance.py download-character-images --character "Firefly"`

- **`character-detection-report`**
  - **Función:** Genera un informe detallado sobre el rendimiento de la detección de personajes. Muestra estadísticas como la tasa de detección general, los personajes más detectados y los creadores con más detecciones.
  - **Ejemplo:** `python -X utf8 maintenance.py character-detection-report`
