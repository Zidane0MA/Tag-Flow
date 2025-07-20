Rediseña el frontend de una aplicación web existente, 'Tag-Flow'. El objetivo es modernizar la interfaz de usuario, mejorar la experiencia de usuario (UX) y la estética visual, manteniendo la funcionalidad actual.

**Contexto General de la Interfaz Actual:**
*   La aplicación presenta una interfaz funcional y directa.
*   La navegación es simple, con predominio de listados de elementos (miniaturas, texto) y formularios básicos.
*   El diseño actual se basa en estilos personalizados (CSS) y JavaScript para la interactividad.

**Tipos de Páginas y Contenido Visual/Funcional Actual:**

1.  **Diseño Base (Aplicado a todas las páginas):**
    *   **Elementos Comunes:**
        *   Una barra de navegación superior que incluye el título o logo de la aplicación y enlaces a las secciones principales: Galería, Administración, Mantenimiento y Papelera.
        *   Un área central donde se carga el contenido específico de cada página.
        *   Posiblemente un pie de página con información básica.

2.  **Página de Galería Principal:**
    *   **Propósito:** Mostrar una colección de videos o imágenes.
    *   **Disposición Visual:** Generalmente una cuadrícula o lista de miniaturas.
    *   **Elementos Existentes (HTML, CSS, JavaScript):**
        *   **Controles de Búsqueda, Filtro y Ordenación:**
            *   Un campo de entrada de texto para búsqueda general.
            *   Controles (selects) para filtrar por Creador, Plataforma, Estado de edicion, Dificutad de Edicion, Estado de procesamiento y Nombres de Personajes.
            *   Boton para ordenar los resultados (por fecha de descarga, ids, nombre) ascendente o descendente.
        *   **Controles de edicion Masiva:**
            *   Aparece al seleccionar los videos
            *   Boton de seleccionar todo
            *   Boton para reanalisis de video
            *   Boton de Mover a Papelera
            *   Boton Limpiar seleccion
            *   Boton de Editar seleccionados (modal)
                * Select de Estado de Edición, Dificutad de Edicion, Música, Artista, Personajes, Notas
                * Checks para limpiar musica, artista, personajes, notas y revertir analisis de video.
                * Boton de cancelar y aplicar cambios.
        *   **Estadísticas Rápidas:**
            *   Tarjetas con el número total de videos, con musica, con personajes y procesados.
        *   **Visualización de la Galería:**
            *   Un contenedor principal que organiza las miniaturas en una cuadrícula o lista.
            *   Cada miniatura de video/imagen incluye:
                *   Una imagen representativa (thumbnail).
                    * En la seccion del thumbnail se incluye:
                        * Checbox para seleccionar videos
                        * 3 Badgets: Dificutad de Edicion, Estado de procesamiento, Plataforma.
                        * Al pasar el cursor se muestran 5 botones (iconos): reproducir, editar, analizar, abrir carpeta y eliminar.
                *   Titulo del video.
                *   Descripcion del video
                *   Musica
                *   Personajes
                *   La duración del video, tamaño del video y fecha de descarga.
                *   La fecha de subida y 3 botones para el Estado de edicion.
             *   **Funcion Reproducir video:**
                * Abre una interfaz tipo tiktok, se tiene las siguientes caracteristicas:
                    * Boton de salir
                    * Video/imagen
                    * Contenido:
                        * Creador, descripcion, musica, personajes, tiempo de reproducion, plataforma, fecha de descarga.
                    * Botones de Dificutad de Edicion (Bajo, Medio, Alto), editar, eliminar, videos relacionados.
        *   **Controles de Paginación:**
            *   Enlaces para navegar entre las diferentes páginas de resultados (Anterior, Siguiente, números de página).

3.  **Página de Panel de Administración:**
    *   **Propósito:** Ofrecer una interfaz para la gestión de datos y configuraciones de la aplicación.
    *   **Disposición Visual:** Predominan los paneles de control, formularios y áreas de visualización de logs.
    *   **Elementos Existentes (HTML, CSS, JavaScript):**
        *   **Header del Dashboard:** Título y subtítulo de la página.
        *   **Estadísticas Rápidas:**
            *   Tarjetas con el número total de videos, videos en papelera, videos procesados y videos pendientes.
        *   **Estado del Sistema:**
            *   Indicadores visuales para el estado de la Base de Datos, API, Cache y Thumbnails.
        *   **Comandos de Gestión:**
            *   **Gestión de Base de Datos:**
                *   **Poblar Base de Datos:**
                    *   Controles para seleccionar la fuente (Todas, DBs externas, Carpetas organizadas, Archivo específico).
                    *   Controles para seleccionar la plataforma (Principales, Adicionales, Todas, Personalizada).
                    *   Campo para limitar la cantidad de videos a importar.
                    *   Opción para forzar la reimportación.
                    *   Botón para ejecutar la acción.
                    *   Campos condicionales para plataforma personalizada y ruta de archivo específica.
                    *   Barra de progreso.
                *   **Análisis de Videos:**
                    *   Controles para seleccionar la fuente (Todas, DBs externas, Carpetas organizadas).
                    *   Controles para seleccionar la plataforma.
                    *   Campo para limitar la cantidad de videos a analizar.
                    *   Opción para forzar el re-análisis.
                    *   Botón para ejecutar el análisis.
                    *   Campo condicional para plataforma personalizada.
                    *   Barra de progreso.
                *   **Generación de Thumbnails:**
                    *   Controles para seleccionar la plataforma.
                    *   Campo para limitar la cantidad de thumbnails a generar.
                    *   Botón para generar thumbnails.
            *   **Mantenimiento del Sistema:**
                *   Botones para ejecutar acciones rápidas: Crear Backup, Optimizar BD, Verificar Sistema, Limpiar Cache.
            *   **Zona de Peligro:**
                *   Advertencia de acciones irreversibles.
                *   Botones para Vaciar Papelera y Reset Completo BD.
        *   **Terminal de Salida:**
            *   Área para mostrar la salida de los comandos ejecutados.
            *   Botón para limpiar la terminal.
        *   **Logs Recientes:**
            *   Área para mostrar logs del sistema.
            *   Botón para actualizar los logs.
        *   **Modal de Confirmación:** Un modal genérico para confirmar acciones antes de ejecutarlas.

4.  **Página de Papelera:**
    *   **Propósito:** Gestionar elementos que han sido marcados para eliminación.
    *   **Disposición Visual:** Una coleccion de elementos eliminados.
    *   **Información Visible por Elemento:**
        *   Título del elemento.
        *   Fecha de eliminación.
    *   **Funcionalidades Interactivas:**
        *   Opciones para restaurar elementos a su ubicación original.
        *   Opciones para eliminar elementos de forma permanente.

**Objetivo del Rediseño para la Herramienta de IA:**
*   Proponer un diseño moderno, limpio y visualmente atractivo.
*   Mejorar la usabilidad y la navegación entre las diferentes secciones.
*   Optimizar la presentación de la información en cada página para una mejor legibilidad y comprensión.
*   Sugerir un enfoque responsivo para asegurar una buena experiencia en diferentes dispositivos (escritorio, tablet, móvil).
*   Proporcionar ideas para microinteracciones o animaciones sutiles que mejoren la experiencia sin sobrecargar.

**Formato de Salida Deseado de la Herramienta de IA:**
*   Descripciones detalladas del nuevo diseño propuesto para cada una de las páginas mencionadas.
*   Sugerencias de paletas de colores, tipografías y estilos de iconos.
*   Posibles estructuras de componentes o patrones de diseño para la interfaz.
*   Recomendaciones sobre cómo mejorar la interactividad y el flujo de usuario.
*   (Opcional: Si es posible, descripciones de wireframes o maquetas de alto nivel para cada página, detallando la disposición de los elementos clave).