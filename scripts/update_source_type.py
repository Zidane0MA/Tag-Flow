import sqlite3
import os

# Base de datos de 4K Tokkit
db_path = "D:/4K Tokkit/data.sqlite"
video_id = "7476282426872859922"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Primero verificar el estado actual
    cursor.execute("SELECT sourceType FROM MediaItems WHERE id = ?", (video_id,))
    current = cursor.fetchone()
    
    if current:
        print(f"Estado actual - sourceType: {current[0]}")
        
        # Realizar la actualización
        update_query = """
        UPDATE MediaItems 
        SET sourceType = 5
        WHERE id = ?
        """
        cursor.execute(update_query, (video_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"¡Actualización exitosa! sourceType actualizado a 5 para el video {video_id}")
            
            # Verificar el nuevo estado
            cursor.execute("SELECT sourceType FROM MediaItems WHERE id = ?", (video_id,))
            new_state = cursor.fetchone()
            print(f"Nuevo estado - sourceType: {new_state[0]}")
        else:
            print("No se pudo actualizar el registro")
    else:
        print(f"No se encontró el registro con id {video_id}")

except sqlite3.Error as e:
    print(f"Error de SQLite: {e}")
finally:
    conn.close()