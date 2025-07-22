# Analisis de Comandos

## Comando: `backup`

- **Problema:** El proceso de backup incluye archivos y directorios no deseados, como `CLAUDE.md` y el directorio `.claude/`.
Tampoco guarda el json data\character_database.json
- **Solución Sugerida:** Modificar la lógica de backup para que excluya explícitamente los directorios `.git`, `.claude` y el archivo `CLAUDE.md` de la copia de seguridad.

## Comando: `list-backups`

- **Problema:** El comando se ejecuta sin errores, pero no muestra la lista de backups existentes. No cumple su función de listar los backups.
- **Solución Sugerida:** Implementar la lógica para que el comando lea el contenido del directorio `backups/`, formatee los nombres de los directorios de backup y los muestre en la consola, ordenados por fecha (el más reciente primero).

## Comando: `restore`

- **Problema:** El comando no encuentra el archivo de backup, incluso cuando se proporciona una ruta absoluta. Devuelve "Backup no encontrado" tanto con rutas relativas como absolutas. Falta agregar data\character_database.json como parte del componente database.
Actualmente el comando no funciona pero crea una db vacia (puede ser confuso).
- **Solución Sugerida:** Investigar y corregir la lógica de manejo de rutas en el comando `restore`. Asegurarse de que pueda resolver correctamente tanto las rutas relativas (desde el directorio del proyecto) como las absolutas. Realizar pruebas adicionales para confirmar que la restauración de diferentes componentes (`database`, `thumbnails`, etc.) funciona como se espera una vez que se solucione el problema de la ruta.

## Comando: `cleanup-backups`

- **Problema:** El comando funciona correctamente para limpiar backups antiguos, pero no ofrece una opción para eliminar *todos* los backups de una sola vez. El intento de usar un flag `--force` resulta en un error de "unrecognized arguments".
- **Solución Sugerida:** Añadir el argumento `--force` al comando `cleanup-backups`. Cuando se use este flag, el comando debería eliminar todos los backups existentes en el directorio `backups/`, previa confirmación del usuario para evitar borrados accidentales.

## Comando: `verify`

- **Problema:**
    1.  **Falta de detalles:** El comando `verify` informa un número total de problemas pero no especifica cuáles son, lo que dificulta el diagnóstico.
    2.  **Detección incompleta:** No detecta problemas críticos, como videos en la base de datos que no tienen un thumbnail correspondiente.
    3.  **Mensaje confuso en `--fix-issues`:** Al usar la opción `--fix-issues`, el mensaje de salida informa sobre los problemas restantes en lugar de los que se han solucionado, lo que resulta engañoso.

- **Solución Sugerida:**
    1.  **Mejorar el informe de `verify`:** Modificar el comando para que liste detalladamente cada problema encontrado.
    2.  **Añadir verificación de thumbnails:** Implementar una comprobación para asegurar que cada video tenga su thumbnail.
    3.  **Clarificar el mensaje de `verify --fix-issues`:** Ajustar el mensaje final para que informe sobre las acciones de corrección realizadas (p. ej., "Se han solucionado X problemas").

## Comando: `verify-files`

- **Problema:** El argumento `--video-ids` es confuso. Aunque está en plural, solo acepta un único ID de video, y falla si se le intentan pasar varios. Esto puede llevar a errores de uso.
- **Solución Sugerida:** Renombrar el argumento a `--video-id` para reflejar con precisión que solo se espera un valor. Esto mejora la claridad y la usabilidad del comando.

## Comando: `integrity-report`

- **Problema:**
    1.  **Falta de detalles y recomendaciones:** El comando base indica que ha encontrado problemas y recomendaciones, pero no los muestra en la salida estándar, impidiendo al usuario saber qué acciones correctivas tomar.
    2.  **El flag `--include-details` no funciona:** Se espera que este flag genere un archivo JSON con un informe detallado, pero no lo hace. La salida en consola es idéntica a la del comando sin el flag, sin proporcionar información adicional ni generar el archivo.

- **Solución Sugerida:**
    1.  **Mostrar recomendaciones:** Modificar el comando para que imprima en la consola las recomendaciones encontradas.
    2.  **Implementar la exportación a JSON:** Corregir la funcionalidad del flag `--include-details` para que genere correctamente el archivo `integrity_report.json` con todos los detalles de la verificación.

## Comando: `clean-thumbnails`

- **Problema:** El comando está completamente roto. Falla con un `AttributeError` porque intenta acceder a `config.THUMBNAILS_PATH`, una variable de configuración que ya no existe. Esto impide que el comando realice su función de identificar y eliminar thumbnails huérfanos.
Nota: THUMBNAILS_PATH se encuentra definido en mi archivo .env.
- **Solución Sugerida:** Actualizar el código para que utilice el método correcto y actual para obtener la ruta del directorio de thumbnails. Una vez solucionado el error, verificar que la lógica de simulación (sin `--force`) y de borrado (con `--force`) funcionen como se espera.

## Comando: `thumbnail-stats`

- **Problema:** El comando se ejecuta correctamente pero no produce ninguna salida. No muestra el resumen estadístico esperado sobre la cobertura de thumbnails, ni el recuento de archivos válidos, corruptos o faltantes.
- **Solución Sugerida:** Implementar la lógica para calcular y mostrar las estadísticas de los thumbnails. La salida debe incluir, como mínimo: el porcentaje de videos que tienen un thumbnail, el número total de thumbnails, y un desglose de cuántos están faltantes o corruptos.

## Comando: `populate-db`

- **Problema:** El comando funcional pero es inestable y presenta múltiples errores críticos.
    1.  **Error fatal (`TypeError`):** El comando falla con un error `TypeError: '<' not supported between instances of 'str' and 'int'` cuando se utiliza con `--source all`, `--source db` sin especificar una plataforma o cuando no se especifica `--source`. Aunque no son combinaciones tan importantes de importación, estaria bien solucionarlos.
    2.  **Fuente `db` no operativa:** La opción `--source db --platform all-platforms` se ejecuta pero no encuentra ningún video para importar, a pesar de que debería hacerlo.
    3.  **Funcionalidad a eliminar:** El comando acepta los argumentos `--file-path` y `--file`, que ya no se requieren para (`populate-db`).
    4.  **Funcionalidad a agregar:** Para la flag `--platform` una opcion para solo aceptar plataformas principales (`youtube`, `tiktok`, `instagram`).

- **Solución Sugerida:**
    1.  **Corregir el `TypeError`:** Depurar y solucionar el error de comparación de tipos que ocurre en la lógica de importación.
    2.  **Reparar la fuente `db`:** Arreglar la lógica de extracción de videos de las bases de datos externas para que `populate-db --source db` funcione como se espera.
    3.  **Eliminar Funcionalidades:** Quitar la capacidad de usar `--file-path` y `--file` en este comando.

## Comando: `optimize-db`

- **Problema:** El comando emite advertencias de `no such column` porque intenta crear índices en las columnas `is_deleted` y `upload_date`, que ya no existen en el esquema de la base de datos después de la refactorización.
- **Solución Sugerida:** Eliminar de la lógica de optimización los intentos de crear índices para estas columnas obsoletas. El comando debe ejecutarse sin advertencias.

## Comando: `db-stats`

- **Problema:** El comando falla con un error fatal (`no such column: is_deleted`). Al igual que `optimize-db`, hace referencia a una columna que ya no existe en la base de datos, lo que impide por completo la obtención de estadísticas.
- **Solución Sugerida:** Actualizar la consulta SQL dentro de la función de `db-stats` para que sea compatible con el esquema de base de datos actual, eliminando la referencia a la columna `is_deleted`.

## Comando: `character-stats`

- **Problema:** El comando falla con un `AttributeError` porque intenta llamar a un método (`get_performance_stats`) que ya no existe en el objeto `CharacterIntelligence`. El mensaje de error sugiere que el método correcto podría ser `get_performance_report`.
- **Solución Sugerida:** Actualizar el código para que llame al método correcto (`get_performance_report`) en el objeto `CharacterIntelligence`.

