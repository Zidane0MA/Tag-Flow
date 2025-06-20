# ❓ Tag-Flow V2 - Preguntas Frecuentes (FAQ)

## 🐍 **INSTALACIÓN Y CONFIGURACIÓN**

### **¿Es necesario usar un entorno virtual?**
**❌ No es obligatorio**, pero sí recomendado:

- **✅ Sin entorno virtual**: Si tienes Python limpio o solo vas a usar Tag-Flow
- **✅ Con entorno virtual**: Si tienes otros proyectos Python o trabajo profesional

**Ver guía completa:** `INSTALACION_SIN_VENV.md`

### **¿Qué versión de Python necesito?**
- **Mínimo**: Python 3.10
- **Recomendado**: Python 3.12
- **Verificar**: `python --version`

### **¿FFmpeg es obligatorio?**
**Sí**, para procesamiento de video:
- **Windows**: Descargar de https://ffmpeg.org y agregar al PATH
- **Linux**: `sudo apt install ffmpeg`
- **Mac**: `brew install ffmpeg`

### **¿Las APIs son obligatorias?**
**No todas**:
- **Básico**: Solo ACRCloud (ya incluida clave de prueba)
- **Completo**: YouTube + Spotify + Google Vision
- **Sin APIs**: Sistema funciona solo con análisis local

---

## 💰 **COSTOS Y LÍMITES**

### **¿Cuánto cuesta usar Tag-Flow V2?**
- **Gratis**: YouTube API (10k/día) + Spotify API + DeepFace local
- **Opcional**: Google Vision ($1.50 por 1000 detecciones)
- **Total estimado**: $0-5/mes para uso normal

### **¿Hay límites en las APIs gratuitas?**
- **YouTube**: 10,000 consultas/día (muy generoso)
- **Spotify**: Rate limits amplios (rara vez se alcanzan)
- **ACRCloud**: 3,000 reconocimientos/mes (incluido)

---

## 🎬 **USO Y FUNCIONALIDADES**

### **¿Qué formatos de video soporta?**
- **Soportados**: MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V
- **Recomendado**: MP4 para mejor compatibilidad

### **¿Cuántos videos puede procesar?**
- **No hay límite técnico** en la base de datos
- **Rendimiento**: Depende de tu hardware
- **Recomendado**: Procesar en lotes de 50-100 videos

### **¿Funciona sin internet?**
- **Sí**, para análisis básico (metadatos, thumbnails)
- **No**, para reconocimiento de música y Google Vision
- **Parcial**: DeepFace funciona offline después de descargar modelos

### **¿Se pueden editar videos en el sistema?**
Tag-Flow **NO edita videos**, solo los cataloga y gestiona:
- ✅ **Hace**: Análisis, reconocimiento, gestión, organización
- ❌ **No hace**: Cortar, editar, aplicar efectos a videos

---

## 🔧 **PROBLEMAS TÉCNICOS**

### **Error: "Module not found" después de instalar**
```bash
# Solución 1: Reinstalar
pip install -r requirements.txt

# Solución 2: Entorno virtual
python -m venv tag-flow-env
tag-flow-env\Scripts\activate
pip install -r requirements.txt
```

### **Error: "FFmpeg not found"**
1. Instalar FFmpeg desde https://ffmpeg.org
2. Agregar al PATH del sistema
3. Reiniciar terminal/comando
4. Verificar: `ffmpeg -version`

### **No se detecta música en los videos**
**Posibles causas**:
- APIs no configuradas (verificar `.env`)
- Video sin audio o audio muy bajo
- Música no está en las bases de datos
- Límites de API alcanzados

### **La interfaz web no carga**
```bash
# Verificar que Flask está instalado
pip show flask

# Verificar puerto
python app.py
# Debería mostrar: Running on http://localhost:5000

# Puerto ocupado
python app.py --port 5001
```

### **Reconocimiento facial no funciona**
**Posibles causas**:
- No hay fotos en `caras_conocidas/`
- Google Vision API no configurada
- DeepFace descargando modelos (primera vez)
- GPU no disponible (usar CPU como fallback)

---

## 🚀 **OPTIMIZACIÓN Y RENDIMIENTO**

### **¿Cómo acelerar el procesamiento?**
1. **GPU**: Configurar `USE_GPU_DEEPFACE=true`
2. **Paralelismo**: Aumentar `MAX_CONCURRENT_PROCESSING`
3. **SSD**: Usar disco SSD para thumbnails
4. **RAM**: 8GB+ recomendado para muchos videos

### **¿Cómo reducir el uso de APIs?**
1. Procesar videos en lotes grandes
2. Evitar reprocesar videos ya analizados
3. Usar solo APIs necesarias
4. Configurar límites en `config.py`

### **La base de datos se vuelve lenta**
```bash
# Optimizar base de datos
python maintenance.py optimize-db

# Verificar integridad
python maintenance.py verify

# Backup antes de limpiar
python maintenance.py backup
```

---

## 🛠️ **DESARROLLO Y PERSONALIZACIÓN**

### **¿Cómo agregar nuevos personajes?**
1. Agregar fotos a `caras_conocidas/categoria/`
2. Formato: JPG, PNG (200x200 - 500x500 px)
3. Nombrar: `nombre_personaje.jpg`
4. Reprocesar videos: `python main.py`

### **¿Cómo cambiar el diseño de la interfaz?**
- **CSS**: Editar `static/css/main.css` y `gallery.css`
- **HTML**: Modificar templates en `templates/`
- **JavaScript**: Cambiar `static/js/main.js` y `gallery.js`

### **¿Cómo agregar nuevas funcionalidades?**
1. **Backend**: Modificar archivos en `src/`
2. **API**: Agregar endpoints en `app.py`
3. **Frontend**: Actualizar templates y JavaScript
4. **BD**: Usar migrations en `migrate.py`

---

## 📊 **MIGRACIÓN Y BACKUP**

### **¿Cómo migrar desde Tag-Flow V1?**
```bash
python migrate.py
# Detecta automáticamente V1 y migra datos
```

### **¿Cómo hacer backup?**
```bash
# Backup completo automático
python maintenance.py backup

# Backup manual
# Copiar: .env, data/, caras_conocidas/
```

### **¿Se pueden perder datos?**
- **Configuración**: Respaldada en `.env`
- **Videos**: Solo se catalogan, archivos originales intactos
- **Base de datos**: Backup automático antes de migraciones
- **Thumbnails**: Se regeneran automáticamente si se pierden

---

## 🎯 **CASOS DE USO**

### **Para TikTokers/Content Creators**
- Catalogar videos propios
- Analizar música viral
- Organizar por dificultad/estado
- Seguimiento de trends

### **Para Equipos/Agencias**
- Gestión colaborativa
- Análisis de competencia
- Biblioteca de referencias
- Reportes de performance

### **Para Investigadores/Analistas**
- Estudios de tendencias
- Análisis de contenido
- Base de datos académica
- Estadísticas de uso

---

## 📞 **SOPORTE**

### **¿Dónde reportar bugs?**
1. Ejecutar: `python check_installation.py`
2. Revisar logs: `tag_flow_processing.log`
3. Abrir issue con información completa

### **¿Dónde está la documentación completa?**
- **README.md**: Guía principal
- **INSTALACION_RAPIDA.md**: Inicio en 5 minutos
- **INSTALACION_SIN_VENV.md**: Sin entorno virtual
- **PROYECTO_COMPLETO.md**: Resumen técnico

### **¿Hay comunidad o Discord?**
Actualmente es un proyecto individual, pero si hay interés se puede crear comunidad.

---

**💡 ¿No encuentras tu pregunta? Ejecuta `python check_installation.py` para diagnóstico automático.**