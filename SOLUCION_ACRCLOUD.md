# 🎵 CONFIGURACIÓN ACRCLOUD - GUÍA COMPLETA

## ❌ Tu Problema Actual

Tienes un token de **"read-audios"** para bucket de audio, pero para reconocimiento de música necesitas crear una **aplicación de Audio Recognition**.

## ✅ SOLUCIÓN PASO A PASO

### Paso 1: Crear Aplicación Correcta en ACRCloud

1. **Ve a [ACRCloud Console](https://console.acrcloud.com/)**
2. **Haz clic en "Create Application"** (botón azul)
3. **IMPORTANTE: Selecciona "Audio & Video Recognition"** 
   - ❌ NO selecciones "Audio Bucket" o "Audio Storage"
   - ✅ SÍ selecciona "Audio & Video Recognition"

4. **Configurar la aplicación:**
   ```
   Application Name: Tag-Flow-Music-Recognition
   Application Type: Audio & Video Recognition
   Audio Type: Music (seleccionar Music, no Speech)
   Platform: Other
   Description: Para reconocimiento de música en videos
   ```

5. **Hacer clic en "Create"**

### Paso 2: Obtener Credenciales Correctas

Después de crear la aplicación, verás una página con **3 valores importantes**:

- **Host**: algo como `identify-eu-west-1.acrcloud.com`
- **Access Key**: una clave larga (ej: `a1b2c3d4e5f6g7h8`)
- **Access Secret**: otra clave larga (ej: `x1y2z3a4b5c6d7e8`)

### Paso 3: Configurar .env

Edita tu archivo `.env` y reemplaza con tus valores reales:

```bash
# Configuración ACRCloud para reconocimiento de música
ACRCLOUD_HOST="identify-eu-west-1.acrcloud.com"    # Tu host real
ACRCLOUD_ACCESS_KEY="tu_access_key_real_aqui"      # Tu access key real
ACRCLOUD_ACCESS_SECRET="tu_access_secret_real_aqui" # Tu access secret real

# Configuraciones opcionales (dejar como están)
PROCESAR_CADA_N_FRAMES=30
DURACION_CLIP_AUDIO=15
```

### Paso 4: Probar Configuración

```bash
# Probar que la configuración funciona
python probar_acrcloud.py
```

**Deberías ver:**
```
✅ Host: identify-eu-west-1.acrcloud.com
✅ Access Key: a1b2c3d4...h8j9
✅ Access Secret: x1y2z3a4...e8f9
✅ Módulo ACRCloud importado correctamente
🔌 Probando conexión con ACRCloud...
✅ ¡Conexión exitosa con ACRCloud!
🎉 Tu configuración está correcta
```

### Paso 5: Usar el Script con Música

```bash
# Usar script con reconocimiento de música
python 1_script_analisis_con_musica.py
```

## 🚨 ERRORES COMUNES

### "Authentication failed"
- **Problema**: Las credenciales están mal
- **Solución**: Verifica que copiaste exactamente Host, Access Key y Access Secret

### "No application found"
- **Problema**: Creaste un "Audio Bucket" en lugar de "Audio & Video Recognition"
- **Solución**: Crear nueva aplicación del tipo correcto

### "API quota exceeded"
- **Problema**: Superaste las 500 consultas gratuitas del mes
- **Solución**: Esperar al próximo mes o actualizar plan

## 📊 LÍMITES GRATUITOS

- **500 identificaciones por mes**
- **Duración máxima por clip: 12 segundos**
- **Formatos soportados**: MP3, WAV, M4A, FLAC, AAC

## 🔗 ENLACES ÚTILES

- **ACRCloud Console**: https://console.acrcloud.com/
- **Documentación**: https://docs.acrcloud.com/
- **Soporte**: support@acrcloud.com

## 🎯 VERIFICACIÓN FINAL

Tu configuración está **CORRECTA** cuando:

1. ✅ Tienes una aplicación "Audio & Video Recognition" (no bucket)
2. ✅ El archivo .env tiene los 3 valores reales (no los placeholders)
3. ✅ `python probar_acrcloud.py` dice "Conexión exitosa"
4. ✅ En el CSV aparece música real en lugar de "API pendiente"

---

**¡Una vez configurado correctamente, Tag-Flow identificará automáticamente la música en tus videos! 🎵✨**
