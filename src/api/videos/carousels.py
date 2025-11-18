"""
Tag-Flow V2 - Video Processing for API
Simplified logic for the new post/media schema
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def process_video_data_for_api(video):
    """Procesa un video individual para la API"""
    # Procesar datos JSON
    if video.get('detected_characters'):
        try:
            video['detected_characters'] = json.loads(video['detected_characters'])
        except:
            video['detected_characters'] = []

    if video.get('final_characters'):
        try:
            video['final_characters'] = json.loads(video['final_characters'])
        except:
            video['final_characters'] = []
    else:
        video['final_characters'] = []

    if video.get('subscription_id') and video.get('subscription_name') and video.get('subscription_type'):
        video['subscription_info'] = {
            'id': video['subscription_id'],
            'name': video['subscription_name'],
            'type': video['subscription_type']
        }

    # Procesar thumbnail_path para usar solo el nombre del archivo
    if video.get('thumbnail_path'):
        video['thumbnail_path'] = Path(video['thumbnail_path']).name

    return video


def add_video_categories(db, videos):
    """Agrega información de post_categories a cada video"""
    if not videos:
        return videos

    video_ids = [v['id'] for v in videos if v.get('id')]
    if not video_ids:
        return videos

    try:
        # Obtener todas las categorías para estos videos en una sola query
        placeholders = ','.join(['?' for _ in video_ids])
        with db.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT m.id as media_id, pc.category_type
                FROM media m
                JOIN posts p ON m.post_id = p.id
                LEFT JOIN post_categories pc ON p.id = pc.post_id
                WHERE m.id IN ({placeholders}) AND pc.category_type IS NOT NULL
                ORDER BY m.id, pc.category_type
            """, video_ids)

            categories_data = cursor.fetchall()

        # Agrupar categorías por media ID (que es el ID que usa el frontend)
        categories_by_video = {}
        for media_id, category_type in categories_data:
            if media_id not in categories_by_video:
                categories_by_video[media_id] = []
            categories_by_video[media_id].append({
                'type': category_type
            })

        # Agregar categorías a cada video
        for video in videos:
            video_id = video.get('id')
            if video_id and video_id in categories_by_video:
                video['categories'] = categories_by_video[video_id]

        return videos

    except Exception as e:
        logger.warning(f"Error obteniendo categorías de videos: {e}")
        return videos


def process_image_carousels(db, videos, filters=None):
    """
    SIMPLIFICADO: En el nuevo esquema post/media, solo procesamos carruseles
    agregando información de carousel_items para videos marcados como carrusel.

    Con el filtro is_primary=TRUE en las queries principales, solo recibimos
    videos primarios, así que solo necesitamos agregar carousel_items.
    """
    if not videos:
        return videos

    logger.info(f"🔍 CAROUSEL PROCESSING SIMPLIFIED - Processing {len(videos)} videos")

    try:
        # Identificar videos que son carruseles (is_carousel=TRUE en posts)
        carousel_video_ids = []
        for video in videos:
            if video.get('is_carousel'):
                carousel_video_ids.append(video['id'])

        if not carousel_video_ids:
            logger.info("🔍 No carousel videos found, no processing needed")
            return videos

        # Obtener todos los items de carrusel para cada video carrusel
        with db.get_connection() as conn:
            placeholders = ','.join(['?' for _ in carousel_video_ids])
            query = f"""
                SELECT m_primary.id as primary_id, m_all.id as item_id,
                       m_all.carousel_order, m_all.file_path
                FROM media m_primary
                JOIN posts p ON m_primary.post_id = p.id
                JOIN media m_all ON m_all.post_id = p.id
                WHERE m_primary.id IN ({placeholders})
                AND m_primary.is_primary = TRUE
                AND p.is_carousel = TRUE
                ORDER BY m_primary.id, m_all.carousel_order
            """

            cursor = conn.execute(query, carousel_video_ids)
            carousel_items = {}

            for row in cursor.fetchall():
                primary_id, item_id, order, file_path = row
                if primary_id not in carousel_items:
                    carousel_items[primary_id] = []
                carousel_items[primary_id].append({
                    'id': item_id,
                    'order': order or 0,
                    'file_path': file_path
                })

        # Agregar carousel_items a los videos correspondientes
        for video in videos:
            if video['id'] in carousel_items:
                video['carousel_items'] = sorted(
                    carousel_items[video['id']],
                    key=lambda x: x['order']
                )
                logger.info(f"Added {len(video['carousel_items'])} items to carousel {video['id']}")

        logger.info(f"🔍 CAROUSEL PROCESSING SIMPLIFIED - Completed for {len(carousel_video_ids)} carousels")
        return videos

    except Exception as e:
        logger.error(f"Error en process_image_carousels: {e}")
        logger.info(f"🔍 CAROUSEL PROCESSING SIMPLIFIED - Error occurred, returning {len(videos)} original videos")
        return videos