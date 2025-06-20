# Documento de Diseño de Proyecto: Sistema Visual de Clasificación de Vídeos

**Versión:** 1.0  
**Fecha:** 20 de junio de 2025  
**Autor:** Zidane

## 1. Resumen del Proyecto

El objetivo es construir un sistema de dos componentes para clasificar y explorar una colección de vídeos en constante crecimiento. El sistema consistirá en:

1. **Un script de análisis (backend):** Un programa de línea de comandos en Python que procesará los vídeos para extraer metadatos automáticamente (creador, personajes, música) y permitirá al usuario añadir datos manualmente (dificultad de edición). Este script estará diseñado para ser escalable, procesando únicamente los vídeos nuevos que se añadan.

2. **Una aplicación visual (frontend):** Una aplicación web local, construida con Streamlit, que leerá los datos clasificados y ofrecerá una interfaz gráfica e interactiva para filtrar, buscar y visualizar los vídeos.

Este sistema transformará una estructura de carpetas de vídeos en una base de datos visual y consultable.

## 2. Objetivos Clave

- **Automatización:** Extraer automáticamente el nombre del creador, los personajes que aparecen y la música de cada vídeo.
- **Eficiencia en el Etiquetado Manual:** Facilitar un flujo de trabajo rápido para que el usuario asigne una "dificultad de edición".
- **Persistencia de Datos:** Almacenar toda la información de manera estructurada y persistente en un archivo CSV, que actuará como nuestra base de datos.
- **Visualización Interactiva:** Ofrecer una interfaz web con filtros múltiples para explorar la colección de vídeos de forma intuitiva.
- **Escalabilidad:** El sistema debe manejar eficientemente la adición de nuevos vídeos sin necesidad de reprocesar toda la colección.

## 3. Arquitectura y Tecnologías

- **Lenguaje:** Python 3.12

### Librerías Principales:
- `pandas`: Para la manipulación y almacenamiento de datos en formato tabular (DataFrame).
- `streamlit`: Para la construcción de la interfaz web visual.
- `face_recognition`: Para la detección y reconocimiento de personajes.
- `opencv-python`: Dependencia de face_recognition para el procesamiento de vídeo.
- `moviepy`: Para la extracción de clips de audio de los vídeos.
- `requests`: Para realizar llamadas a la API de reconocimiento de música.
- `python-dotenv`: Para gestionar de forma segura las claves de API.

### Servicios Externos:
- API de reconocimiento de música (ej. ACRCloud o AudD).

### Formato de Datos:
- **CSV (videos.csv):** Actuará como la base de datos centralizada.

## 4. Estructura de Archivos y Carpetas

Una estructura organizada es fundamental. El proyecto se organizará de la siguiente manera:

```
proyecto_clasificador/
├── .env                  # Archivo para guardar la clave de la API de música (secreto)
├── 1_script_analisis.py    # El script de backend para procesar y etiquetar vídeos
├── 2_app_visual.py         # El script de frontend de Streamlit
├── data/
│   └── videos.csv        # La base de datos con toda la información clasificada
├── caras_conocidas/
│   ├── personaje_uno.jpg
│   ├── personaje_dos.png
│   └── ...               # Imágenes de referencia para cada personaje
├── videos_a_procesar/      # Carpeta principal donde se añadirán los vídeos
│   ├── Creador_A/
│   │   ├── video_001.mp4
│   │   └── video_002.mp4
│   ├── Creador_B/
│   │   └── video_003.mp4
│   └── ...               # Se añadirán más carpetas de creadores aquí
└── requirements.txt        # Archivo con la lista de dependencias de Python
```

## 5. Flujo de Trabajo del Sistema

1. **Preparación Inicial:** El usuario añade las imágenes de los personajes en `caras_conocidas/` y su clave de API en el archivo `.env`.

2. **Añadir Vídeos:** El usuario copia nuevas carpetas de vídeos (organizadas por creador) dentro de `videos_a_procesar/`.

3. **Ejecutar el Análisis (Backend):** El usuario ejecuta `1_script_analisis.py` desde la terminal.
   - El script detecta automáticamente qué vídeos son nuevos.
   - Para cada vídeo nuevo, realiza el análisis de música y personajes.
   - Al final de cada análisis, pide al usuario que introduzca la dificultad.
   - Guarda la nueva información en `data/videos.csv`.

4. **Explorar los Datos (Frontend):** El usuario ejecuta `2_app_visual.py` desde la terminal (`streamlit run 2_app_visual.py`).
   - Se abre una aplicación en el navegador.
   - La aplicación muestra los vídeos y una barra lateral con filtros.
   - El usuario puede filtrar la colección por creador, personajes, dificultad, etc., y ver los resultados al instante.

## 6. Desarrollo Detallado por Módulos

### Módulo 1: Script de Análisis (1_script_analisis.py)

**Propósito:** Procesar vídeos de forma inteligente y poblar la base de datos.

#### Lógica Principal:

**Inicialización:**
- Cargar las dependencias (pandas, pathlib, face_recognition, etc.).
- Cargar la clave de API desde el archivo `.env`.
- Cargar las caras conocidas desde la carpeta `caras_conocidas/` en memoria.

**Carga de Datos Existentes:**
- Comprobar si `data/videos.csv` existe. Si no, crear un DataFrame vacío con las columnas correctas: `['ruta_absoluta', 'archivo', 'creador', 'personajes', 'musica', 'dificultad_edicion']`.
- Si existe, cargarlo en un DataFrame de pandas. La columna `ruta_absoluta` es clave para saber qué se ha procesado.

**Detección de Vídeos Nuevos:**
- Escanear recursivamente la carpeta `videos_a_procesar/` para obtener una lista de todas las rutas de vídeo (.mp4, .mov, etc.).
- Comparar esta lista con la columna `ruta_absoluta` del DataFrame para identificar los vídeos que aún no han sido procesados.

**Bucle de Procesamiento (solo para vídeos nuevos):**

Para cada `ruta_video_nuevo`:

a. **Extraer Creador:** El nombre del creador se extrae del nombre de la carpeta padre de la ruta del vídeo (pathlib es ideal para esto).

b. **Identificar Música:**
   - Extraer un clip de audio de 15 segundos con moviepy.
   - Enviar el clip a la API de música.
   - Manejar posibles errores (música no encontrada, error de API). Guardar el resultado.

c. **Identificar Personajes:**
   - Abrir el vídeo con opencv.
   - Procesar 1 fotograma por segundo para ser eficiente (no cada fotograma).
   - En cada fotograma procesado, usar face_recognition para encontrar caras y compararlas con las caras conocidas.
   - Almacenar una lista de nombres únicos de los personajes encontrados en el vídeo.

d. **Input Manual de Dificultad:**
   - Imprimir en la consola toda la información encontrada (creador, música, personajes).
   - Solicitar al usuario que introduzca la dificultad (alto, medio, bajo) mediante un `input()`. Incluir validación.

e. **Guardar Resultados:**
   - Añadir una nueva fila al DataFrame con toda la información recopilada.
   - **Importante:** Después de procesar cada vídeo (o en lotes de 5, por ejemplo), guardar el DataFrame actualizado de nuevo en `data/videos.csv`. Esto evita la pérdida de datos si el script se interrumpe.

### Módulo 2: Aplicación Visual (2_app_visual.py)

**Propósito:** Proveer una interfaz de usuario rica e interactiva para la exploración de datos.

#### Lógica Principal:

**Configuración de la App:**
- Importar streamlit y pandas.
- Configurar el título de la página y el layout (`st.set_page_config(layout="wide")`).

**Carga de Datos:**
- Definir una función para cargar `data/videos.csv` y decorarla con `@st.cache_data`. Esto asegura que los datos solo se carguen una vez y la app sea muy rápida al aplicar filtros.
- Manejar el caso en que el archivo CSV no exista, mostrando un mensaje de ayuda.

**Barra Lateral de Filtros (`st.sidebar`):**
- Crear un `st.header` para los filtros.
- **Filtro de Creador:** Usar `st.multiselect` con la lista de creadores únicos del DataFrame.
- **Filtro de Dificultad:** Usar `st.multiselect` con las opciones `['alto', 'medio', 'bajo']`.
- **Filtro de Personajes:** Obtener una lista de todos los personajes únicos de la columna 'personajes' y usar `st.multiselect`.
- **Filtro de Música/Texto:** Usar `st.text_input` para permitir una búsqueda de texto libre en la columna de música o en el nombre del archivo.

**Lógica de Filtrado:**
- Tomar el DataFrame original.
- Aplicar cada filtro seleccionado por el usuario de forma secuencial. Por ejemplo, si se selecciona un creador, filtrar el DataFrame por ese creador. Luego, sobre el resultado, aplicar el filtro de dificultad, y así sucesivamente.

**Visualización de Resultados:**
- En el área principal, mostrar un contador de resultados: `st.write(f"{len(df_filtrado)} vídeos encontrados")`.
- Iterar sobre el DataFrame filtrado.
- Para cada fila (cada vídeo), usar `st.video()` para mostrar el reproductor de vídeo directamente en la app.
- Debajo de cada vídeo, mostrar sus metadatos de forma clara usando `st.metric` o `st.markdown` (ej: Creador, Música, Personajes, Dificultad).
- Usar `st.divider()` para separar las entradas de cada vídeo.

## 7. Estrategia de Escalabilidad

El punto más crítico para la escalabilidad es evitar el reprocesamiento. El diseño del `1_script_analisis.py` aborda esto directamente al:

1. Leer primero el estado actual de la "base de datos" (el CSV).
2. Comparar los archivos en disco con los ya procesados.
3. Procesar únicamente el delta (los archivos nuevos).

Esto garantiza que, aunque la colección crezca a miles de vídeos, ejecutar el script de análisis seguirá siendo rápido, ya que solo trabajará sobre los nuevos añadidos.

## 8. Próximos Pasos y Mejoras Futuras

- **Paginación:** Si la lista de resultados filtrados es muy larga, añadir paginación en la app de Streamlit.
- **Base de Datos Real:** Si el CSV se vuelve demasiado grande y lento (> 100,000 entradas), migrar la lógica de guardado a una base de datos ligera como SQLite, que ya viene con Python.
- **Edición de Datos:** Añadir una función en la app de Streamlit para poder editar o corregir un dato directamente desde la interfaz.
- **Procesamiento en Lote:** Permitir que el script de análisis se ejecute sin intervención manual (por ejemplo, asignando una dificultad "por defecto" y etiquetándola para revisión posterior).

## 9. Guía de Puesta en Marcha

1. Clonar o crear la estructura de carpetas del proyecto.
2. Crear y activar un entorno virtual de Python.
3. Instalar las dependencias: `pip install -r requirements.txt`.
4. Crear el archivo `.env` y añadir la clave de API: `API_KEY_MUSICA="tu_clave_aqui"`.
5. Poblar `caras_conocidas/` y `videos_a_procesar/`.
6. Ejecutar el script de análisis: `python 1_script_analisis.py`.
7. Lanzar la aplicación visual: `streamlit run 2_app_visual.py`.