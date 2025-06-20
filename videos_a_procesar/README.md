# Videos a Procesar

Organiza tus videos aquí por creador para que Tag-Flow los procese automáticamente.

## 📁 Estructura recomendada:

```
videos_a_procesar/
├── NombreCreador1/
│   ├── video_aventura.mp4
│   ├── video_comedia.mp4
│   └── tutorial_especial.mov
├── NombreCreador2/
│   ├── gameplay_001.mp4
│   └── review_producto.mp4
└── CreadorFavorito/
    ├── vlog_viaje.mp4
    ├── receta_cocina.mp4
    └── entrevista.avi
```

## 🎯 Reglas importantes:

1. **Una carpeta por creador**
   - El nombre de la carpeta se usará como "Creador" automáticamente
   - Usa nombres sin espacios ni caracteres especiales

2. **Formatos de video soportados:**
   - MP4, MOV, AVI, MKV, WMV, FLV, WebM

3. **Organización flexible:**
   - Puedes tener subcarpetas dentro de cada creador
   - El sistema encontrará videos recursivamente

## 🚀 Para empezar:

1. Crea una carpeta con el nombre del creador
2. Coloca los videos dentro
3. Ejecuta `python 1_script_analisis.py`
4. ¡El sistema procesará automáticamente solo los videos nuevos!

## ⚡ Ejemplo práctico:

```
videos_a_procesar/
├── ElRubius/
│   ├── minecraft_survival_ep1.mp4
│   └── reaccion_trailer.mp4
└── TheGrefg/
    └── fortnite_highlights.mp4
```

Después del procesamiento, podrás filtrar por "ElRubius" o "TheGrefg" en la aplicación web.
