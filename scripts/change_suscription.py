
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'videos_procesados', 'data.sqlite')
video_filename_part = 'huyh_anhh03_1740707658_7476282426872859922'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Get the databaseId for the 'Favorites' subscription (des_un_named with type 1)
    cursor.execute("SELECT databaseId FROM Subscriptions WHERE name = 'des_un_named' AND earliestFavoritesMediaReached = TRUE")
    result = cursor.fetchone()

    if result:
        favorites_db_id = result[0]

        # Update the MediaItems table
        update_query = """
        UPDATE MediaItems 
        SET 
            subscriptionDatabaseId = ?,
            relativePath = REPLACE(relativePath, 'Liked', 'Favorites'), 
            coverRelativePath = REPLACE(coverRelativePath, 'Liked', 'Favorites'),
            sourceType = 5
        WHERE 
            id = ?;
        """
        video_id = video_filename_part.split('_')[-1]  # Extract the ID from the filename
        cursor.execute(update_query, (favorites_db_id, video_id))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"Successfully updated video record for {video_filename_part} in MediaItems.")
        else:
            print(f"Could not find video record for {video_filename_part} in MediaItems.")
    else:
        print("Could not find the 'Favorites' subscription.")

except sqlite3.Error as e:
    print(f"An error occurred: {e}")
finally:
    conn.close()

# Self-delete
# os.remove(__file__)
