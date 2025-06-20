"""
Tag-Flow V2 - Generador de Imágenes de Ejemplo
Crea imágenes de placeholder para probar el reconocimiento facial
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import colorsys

def create_placeholder_character(name, category, size=(300, 300)):
    """Crear imagen placeholder para un personaje"""
    
    # Generar color basado en el nombre
    hash_val = hash(name) % 360
    h, s, l = hash_val / 360, 0.7, 0.5
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    bg_color = (int(r * 255), int(g * 255), int(b * 255))
    
    # Crear imagen
    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Intentar cargar fuente
    try:
        font_large = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Dibujar círculo para simular cara
    circle_size = min(size) // 3
    circle_center = (size[0] // 2, size[1] // 2 - 20)
    circle_bbox = [
        circle_center[0] - circle_size // 2,
        circle_center[1] - circle_size // 2,
        circle_center[0] + circle_size // 2,
        circle_center[1] + circle_size // 2
    ]
    
    # Color más claro para el círculo
    circle_h, circle_s, circle_l = h, s * 0.5, l + 0.3
    circle_r, circle_g, circle_b = colorsys.hls_to_rgb(circle_h, circle_l, circle_s)
    circle_color = (int(circle_r * 255), int(circle_g * 255), int(circle_b * 255))
    
    draw.ellipse(circle_bbox, fill=circle_color, outline=(255, 255, 255), width=2)
    
    # Dibujar "ojos"
    eye_size = 8
    left_eye = (circle_center[0] - 20, circle_center[1] - 10)
    right_eye = (circle_center[0] + 20, circle_center[1] - 10)
    
    draw.ellipse([left_eye[0] - eye_size//2, left_eye[1] - eye_size//2,
                  left_eye[0] + eye_size//2, left_eye[1] + eye_size//2], 
                 fill=(50, 50, 50))
    draw.ellipse([right_eye[0] - eye_size//2, right_eye[1] - eye_size//2,
                  right_eye[0] + eye_size//2, right_eye[1] + eye_size//2], 
                 fill=(50, 50, 50))
    
    # Dibujar "boca"
    mouth_center = (circle_center[0], circle_center[1] + 15)
    draw.arc([mouth_center[0] - 15, mouth_center[1] - 8,
              mouth_center[0] + 15, mouth_center[1] + 8], 
             0, 180, fill=(50, 50, 50), width=2)
    
    # Texto del nombre
    text_bbox = draw.textbbox((0, 0), name, font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (size[0] - text_width) // 2
    text_y = size[1] - 60
    
    # Sombra del texto
    draw.text((text_x + 1, text_y + 1), name, fill=(0, 0, 0), font=font_large)
    # Texto principal
    draw.text((text_x, text_y), name, fill=(255, 255, 255), font=font_large)
    
    # Categoría
    cat_bbox = draw.textbbox((0, 0), category, font=font_small)
    cat_width = cat_bbox[2] - cat_bbox[0]
    cat_x = (size[0] - cat_width) // 2
    cat_y = text_y + 25
    
    draw.text((cat_x + 1, cat_y + 1), category, fill=(0, 0, 0), font=font_small)
    draw.text((cat_x, cat_y), category, fill=(200, 200, 200), font=font_small)
    
    return img

def create_example_characters():
    """Crear personajes de ejemplo para demostración"""
    
    characters = {
        'genshin': [
            'Zhongli', 'Raiden_Shogun', 'Ganyu', 'Hu_Tao', 'Kazuha',
            'Ayaka', 'Venti', 'Diluc', 'Bennett', 'Xingqiu'
        ],
        'honkai': [
            'Kafka', 'Blade', 'Firefly', 'Dan_Heng_IL', 'Jingliu',
            'March_7th', 'Stelle', 'Bronya', 'Seele', 'Silver_Wolf'
        ]
    }
    
    base_path = Path('caras_conocidas')
    
    for category, char_list in characters.items():
        category_path = base_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Creando personajes de {category}...")
        
        for character in char_list:
            # Crear imagen
            img = create_placeholder_character(character, category.title())
            
            # Guardar
            filename = f"{character.lower()}.jpg"
            filepath = category_path / filename
            
            img.save(filepath, 'JPEG', quality=90)
            print(f"  ✅ {filename}")
    
    print(f"\n🎭 Creados {sum(len(chars) for chars in characters.values())} personajes de ejemplo")
    print("📝 Estos son placeholders para demostración.")
    print("   Reemplaza con imágenes reales de los personajes para mejor reconocimiento.")

def create_info_file():
    """Crear archivo de información sobre los placeholders"""
    
    info_content = """# Imágenes de Ejemplo - SOLO PARA DEMOSTRACIÓN

⚠️ **IMPORTANTE**: Estas son imágenes placeholder generadas automáticamente para demostrar la funcionalidad del sistema.

## 🎯 Propósito

Estas imágenes permiten:
- Probar el sistema de reconocimiento facial
- Verificar que la configuración funciona correctamente
- Demostrar cómo organizar las fotos de referencia

## 🔄 Reemplazar con Imágenes Reales

Para usar el reconocimiento facial efectivamente:

1. **Obtener imágenes reales** de los personajes desde:
   - Wikis oficiales
   - Arte promocional oficial
   - Screenshots del juego

2. **Formato recomendado**:
   - JPG, PNG, WebP
   - 200x200 a 500x500 píxeles
   - Rostro centrado y bien iluminado

3. **Reemplazar archivos**: 
   - Mantener los mismos nombres de archivo
   - O agregar nuevos personajes

## 🎮 Personajes Incluidos

### Genshin Impact
- zhongli.jpg, raiden_shogun.jpg, ganyu.jpg, hu_tao.jpg, kazuha.jpg
- ayaka.jpg, venti.jpg, diluc.jpg, bennett.jpg, xingqiu.jpg

### Honkai Star Rail  
- kafka.jpg, blade.jpg, firefly.jpg, dan_heng_il.jpg, jingliu.jpg
- march_7th.jpg, stelle.jpg, bronya.jpg, seele.jpg, silver_wolf.jpg

## 📖 Más Información

Ver README.md en cada carpeta de categoría para instrucciones detalladas.

---
*Generado automáticamente por Tag-Flow V2*
"""
    
    with open('caras_conocidas/README_PLACEHOLDERS.md', 'w', encoding='utf-8') as f:
        f.write(info_content)
    
    print("📖 Archivo de información creado: caras_conocidas/README_PLACEHOLDERS.md")

def main():
    """Función principal"""
    print("🎨 Tag-Flow V2 - Generador de Personajes de Ejemplo")
    print("="*55)
    
    # Verificar PIL
    try:
        from PIL import Image
    except ImportError:
        print("❌ Error: Pillow no está instalado")
        print("   Instalar con: pip install Pillow")
        return
    
    print("🎭 Creando personajes de ejemplo...")
    print("   (Estas son imágenes placeholder para demostración)")
    print()
    
    # Crear personajes
    create_example_characters()
    
    # Crear archivo de información
    create_info_file()
    
    print("\n✅ ¡Completado!")
    print("\n💡 Próximos pasos:")
    print("   1. Reemplaza los placeholders con imágenes reales")
    print("   2. Ejecuta: python main.py (para procesar videos)")
    print("   3. El sistema reconocerá personajes automáticamente")

if __name__ == "__main__":
    main()