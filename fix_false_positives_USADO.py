#!/usr/bin/env python3
"""
Script para limpiar falsos positivos del sistema de reconocimiento de personajes
"""

import json
import sqlite3
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
DB_PATH = Path("D:/Tag-Flow/data/videos.db")

# Lista de falsos positivos conocidos que deben ser eliminados
FALSE_POSITIVES = {
    'animegamey',
    'zenlesszonezero', 
    'forte',
    'mamama',
    'batte',
    'genshin',
    'honkai',
    'impact',
    'zenless',
    'zone', 
    'zero',
    'star',
    'rail',
    'hsr',
    'hi3',
    'zzz',
    'genshinimpact',
    'honkaiimpact',
    'honkaistarrail',
    'wuthering',
    'waves',
    'anime',
    'game',
    'gaming',
    'mmd',
    'dance',
    'cosplay',
    'cos',
    'shorts',
    'tiktok'
}

def clean_detected_characters(character_list_str):
    """Limpiar lista de personajes detectados eliminando falsos positivos"""
    if not character_list_str:
        return character_list_str
    
    try:
        # Parsear JSON
        characters = json.loads(character_list_str)
        
        # Filtrar falsos positivos (case insensitive)
        cleaned_characters = []
        removed_characters = []
        
        for char in characters:
            char_lower = char.lower().strip()
            if char_lower not in FALSE_POSITIVES:
                cleaned_characters.append(char)
            else:
                removed_characters.append(char)
        
        if removed_characters:
            logger.info(f"Removiendo falsos positivos: {removed_characters}")
        
        # Retornar JSON limpio o None si está vacío
        if cleaned_characters:
            return json.dumps(cleaned_characters)
        else:
            return None
            
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Error parseando personajes: {character_list_str} - {e}")
        return character_list_str

def main():
    """Función principal para limpiar falsos positivos"""
    
    if not DB_PATH.exists():
        logger.error(f"Base de datos no encontrada: {DB_PATH}")
        return
    
    logger.info("Iniciando limpieza de falsos positivos...")
    
    # Conectar a la base de datos
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Obtener todos los videos con personajes detectados
        cursor.execute("""
            SELECT id, file_name, detected_characters 
            FROM videos 
            WHERE detected_characters IS NOT NULL AND detected_characters != ''
        """)
        
        videos = cursor.fetchall()
        logger.info(f"Procesando {len(videos)} videos con personajes detectados...")
        
        updates_made = 0
        total_false_positives_removed = 0
        
        for video_id, file_name, detected_characters in videos:
            original_chars = detected_characters
            cleaned_chars = clean_detected_characters(detected_characters)
            
            # Si hay cambios, actualizar la base de datos
            if cleaned_chars != original_chars:
                cursor.execute("""
                    UPDATE videos 
                    SET detected_characters = ?, 
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (cleaned_chars, video_id))
                
                updates_made += 1
                
                # Contar falsos positivos removidos
                if original_chars:
                    try:
                        original_list = json.loads(original_chars)
                        cleaned_list = json.loads(cleaned_chars) if cleaned_chars else []
                        removed_count = len(original_list) - len(cleaned_list)
                        total_false_positives_removed += removed_count
                        
                        logger.info(f"Video {video_id}: {removed_count} falsos positivos removidos")
                        logger.debug(f"  Archivo: {file_name}")
                        logger.debug(f"  Antes: {original_chars}")
                        logger.debug(f"  Después: {cleaned_chars}")
                        
                    except json.JSONDecodeError:
                        pass
        
        # Confirmar cambios
        conn.commit()
        
        logger.info(f"✅ Limpieza completada:")
        logger.info(f"   - Videos actualizados: {updates_made}")
        logger.info(f"   - Falsos positivos removidos: {total_false_positives_removed}")
        
        # Mostrar estadísticas post-limpieza
        cursor.execute("""
            SELECT COUNT(*) FROM videos 
            WHERE detected_characters IS NOT NULL AND detected_characters != ''
        """)
        videos_with_chars = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM videos")
        total_videos = cursor.fetchone()[0]
        
        logger.info(f"📊 Estadísticas post-limpieza:")
        logger.info(f"   - Total videos: {total_videos}")
        logger.info(f"   - Videos con personajes: {videos_with_chars}")
        logger.info(f"   - Tasa de detección: {videos_with_chars/total_videos*100:.1f}%")
        
    except Exception as e:
        logger.error(f"Error durante la limpieza: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
