import sqlite3
from pathlib import Path

def compare_by_unique_id():
    """
    Compares the databases using the unique database ID to definitively find
    which media files have not been populated.
    """
    # --- Configuration ---
    main_db_path = Path("D:/Tag-Flow/data/videos.db")
    tokkit_db_path = Path("D:/4K Tokkit/data.sqlite")
    tokkit_base_path = tokkit_db_path.parent # Base path for Tokkit downloads

    print("--- Verificador Definitivo por ID Único ---")
    print(f"BD Principal: {main_db_path}")
    print(f"BD Tokkit:    {tokkit_db_path}\n")

    try:
        # --- 1. Get all populated download_item_ids from the main database ---
        main_conn = sqlite3.connect(main_db_path)
        main_cursor = main_conn.cursor()
        main_cursor.execute("SELECT download_item_id FROM downloader_mapping WHERE external_db_source = '4k_tokkit'")
        populated_ids = {row[0] for row in main_cursor.fetchall()}
        
        # Get existing platform_post_ids from the posts table
        main_cursor.execute("SELECT platform_post_id FROM posts WHERE platform_id = (SELECT id FROM platforms WHERE name = 'tiktok')")
        existing_post_ids = {row[0] for row in main_cursor.fetchall() if row[0] is not None}
        
        main_conn.close()
        print(f"1. IDs poblados en BD principal (media): {len(populated_ids)}")
        print(f"   IDs de posts existentes en BD principal: {len(existing_post_ids)}\n")

        # --- 2. Get all valid media item records from the Tokkit database ---
        tokkit_conn = sqlite3.connect(tokkit_db_path)
        tokkit_cursor = tokkit_conn.cursor()
        tokkit_cursor.execute("""
            SELECT databaseId, relativePath, id, authorName, description, mediaType
            FROM MediaItems
            WHERE downloaded = 1
              AND relativePath IS NOT NULL
              AND mediaType IN (2, 3)
        """)
        tokkit_records = tokkit_cursor.fetchall()
        tokkit_conn.close()
        print(f"2. IDs válidos en BD Tokkit: {len(tokkit_records)}\n")

        # --- 3. Compare the two sets of IDs and check disk presence and post existence ---
        print("3. Comparando por ID único y buscando archivos no poblados...")
        unpopulated_records = []
        path_chars_to_strip = '/' + chr(92) # For path normalization

        for record in tokkit_records:
            database_id, relative_path, tiktok_id, author, description, media_type = record
            
            # Only consider videos for the 35 missing ones
            if media_type == 3: # Image
                continue # Skip images, as we know they match

            if database_id not in populated_ids:
                # Check disk presence
                expected_path = tokkit_base_path / relative_path.lstrip(path_chars_to_strip)
                disk_exists = expected_path.exists()
                
                # Check if post ID already exists
                post_id_exists = str(tiktok_id) in existing_post_ids

                unpopulated_records.append({
                    "database_id": database_id,
                    "relative_path": relative_path,
                    "tiktok_id": tiktok_id,
                    "author": author,
                    "description": description,
                    "disk_exists": disk_exists,
                    "post_id_exists": post_id_exists
                })

        # --- 4. Report the results ---
        if not unpopulated_records:
            print("\n🎉 ¡Éxito! Todos los archivos de Tokkit han sido poblados.")
        else:
            print(f"\n🚨 Se encontraron {len(unpopulated_records)} videos que están en la BD de Tokkit pero no en la BD principal:")
            for i, record in enumerate(unpopulated_records, 1):
                print(f"\n--- Video No Poblado #{i} ---")
                print(f"  Nombre:      {Path(record['relative_path']).name}")
                print(f"  Autor:       {record['author']}")
                print(f"  TikTok ID:   {record['tiktok_id']}")
                print(f"  Tokkit DB ID: {record['database_id']}")
                print(f"  Estado en disco: {'✅ EXISTE' if record['disk_exists'] else '❌ NO ENCONTRADO'}")
                print(f"  Post ID existe: {'✅ SÍ' if record['post_id_exists'] else '❌ NO'}")

    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    compare_by_unique_id()
