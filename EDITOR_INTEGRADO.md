# ✏️ Editor Integrado de Tag-Flow

## 🎯 Nueva Funcionalidad: Editar Videos desde la Web

¡Tag-Flow ahora incluye un editor integrado que te permite modificar la información de tus videos directamente desde la aplicación web! Ya no necesitas reprocesar videos solo para corregir datos.

## 🚀 Cómo Usar el Editor

### 1. Activar el Modo de Edición

1. Abre la aplicación web: `streamlit run 2_app_visual.py`
2. En la **barra lateral izquierda**, busca la sección "✏️ Herramientas de Edición"
3. Marca la casilla **"🔧 Mostrar controles de edición"**
4. ¡Ahora verás botones de "✏️ Editar" en cada video!

### 2. Editar un Video

1. **Localiza el video** que quieres editar (usa filtros si es necesario)
2. **Haz clic en "✏️ Editar"** en la tarjeta del video
3. **El video entrará en modo de edición** con un formulario amarillo
4. **Modifica los campos** que necesites cambiar
5. **Haz clic en "💾 Guardar Cambios"** o "❌ Cancelar"

## 📝 Campos Editables

### ✅ Puedes editar:
- **👤 Creador**: Nombre del creador del video
- **🎭 Personajes**: Lista de personajes (separados por comas)
- **🎵 Música**: Descripción de música/sonidos
- **⚡ Dificultad**: Alto, medio o bajo

### ❌ No puedes editar:
- **📁 Archivo**: Nombre del archivo (solo lectura)
- **📍 Ruta**: Ubicación del archivo (se mantiene automáticamente)

## 🎯 Casos de Uso Típicos

### 🔧 Corrección de Errores
- **Problema**: El sistema detectó mal un personaje
- **Solución**: Edita el campo "Personajes" y corrige manualmente

### 📊 Ajuste de Dificultad
- **Problema**: Asignaste "alto" pero debería ser "medio"
- **Solución**: Cambia la dificultad en el selector desplegable

### 🎵 Información de Música
- **Problema**: La API no detectó la música correcta
- **Solución**: Edita el campo "Música" con la información correcta

### 👤 Cambio de Creador
- **Problema**: Moviste un video a la carpeta equivocada
- **Solución**: Edita el campo "Creador" sin mover el archivo

## ⚡ Características Avanzadas

### 🔄 Guardado Automático
- Los cambios se guardan **inmediatamente** en la base de datos
- **No necesitas** ejecutar el script de análisis otra vez
- La información se actualiza **en tiempo real**

### 📅 Historial de Ediciones
- Cada edición guarda automáticamente la **fecha y hora**
- Puedes ver cuándo fue la **última edición** en cada video
- El sistema mantiene tanto la fecha de **procesado original** como la de **última edición**

### ✅ Validación Inteligente
- **Campos obligatorios**: No puedes dejar vacío el creador
- **Dificultad válida**: Solo acepta "alto", "medio" o "bajo"
- **Mensajes de error**: Te avisa si hay algún problema

### 💾 Persistencia de Datos
- Los cambios se guardan en el archivo `data/videos.csv`
- **Backup automático**: El sistema mantiene la integridad de los datos
- **Compatible**: Los datos editados funcionan perfectamente con filtros y búsquedas

## 🛡️ Seguridad y Respaldos

### 🔒 Protección de Datos
- El editor **no puede modificar** la ubicación del archivo original
- Los cambios son **reversibles** - puedes editarlos de nuevo
- El sistema valida todos los datos antes de guardar

### 💡 Recomendaciones
1. **Haz respaldos** de `data/videos.csv` periódicamente
2. **Prueba en pocos videos** antes de hacer cambios masivos
3. **Usa nombres consistentes** para personajes y creadores

## 🎨 Interfaz Visual

### 🟡 Modo de Edición
- **Fondo amarillo**: Indica que estás editando
- **Formulario claro**: Todos los campos organizados
- **Botones grandes**: Guardar y Cancelar bien visibles

### ✅ Confirmaciones
- **Mensaje verde**: Aparece cuando guardas exitosamente
- **Errores rojos**: Te avisan si algo está mal
- **Información azul**: Consejos y ayuda

## 📋 Flujo de Trabajo Recomendado

### Para Colecciones Nuevas:
1. **Procesa videos** con `python 1_script_analisis.py`
2. **Revisa resultados** en la aplicación web
3. **Corrige errores** usando el editor integrado
4. **Aplica filtros** y disfruta tu colección organizada

### Para Mantenimiento:
1. **Añade videos nuevos** ocasionalmente
2. **Procesa solo los nuevos** con el script
3. **Usa el editor** para ajustes rápidos
4. **No reproceses** toda la colección

## 🚨 Solución de Problemas

### "No se pueden guardar los cambios"
- **Verificar permisos** de escritura en la carpeta `data/`
- **Cerrar** otros programas que usen el archivo CSV
- **Comprobar espacio** disponible en disco

### "Los cambios no aparecen"
- **Recargar la página** web (F5)
- **Verificar** que los datos se guardaron en el CSV
- **Revisar** si hay errores en la consola del navegador

### "El botón de editar no aparece"
- **Activar** "Mostrar controles de edición" en la barra lateral
- **Verificar** que hay videos en la vista actual
- **Aplicar filtros** para encontrar el video específico

## 🎉 ¡Disfruta Editando!

El editor integrado hace que Tag-Flow sea mucho más poderoso y fácil de usar. Ya no necesitas reprocesar videos completos solo para hacer pequeñas correcciones. 

**¡Tu colección de videos nunca había sido tan fácil de mantener! 🎬✨**

---

*¿Tienes sugerencias para mejorar el editor? ¡Nos encantaría saber qué funcionalidades adicionales te gustaría ver!*
