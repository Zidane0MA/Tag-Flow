# Analisis de Comandos

## Comando: `backup`

- **Problema:** El proceso de backup incluye archivos y directorios no deseados, como `CLAUDE.md` y el directorio `.claude/`.
- **Solución Sugerida:** Modificar la lógica de backup para que excluya explícitamente los directorios `.git`, `.claude` y el archivo `CLAUDE.md` de la copia de seguridad.

## Comando: `list-backups`

- **Problema:** El comando se ejecuta sin errores, pero no muestra la lista de backups existentes. No cumple su función de listar los backups.
- **Solución Sugerida:** Implementar la lógica para que el comando lea el contenido del directorio `backups/`, formatee los nombres de los directorios de backup y los muestre en la consola, ordenados por fecha (el más reciente primero).

