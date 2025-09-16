"""
Tag-Flow V2 - Video Carousels Processing
Complex carousel logic for image/video grouping
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
    
    # Preparar título apropiado para el frontend usando nuevo esquema
    if video.get('platform') in ['tiktok', 'instagram'] and video.get('title_post'):
        if (video.get('platform') == 'instagram' and
            video.get('title_post') and
            video.get('title_post') != video.get('file_name', '').replace('.mp4', '')):
            video['display_title'] = video['title_post']
        elif video.get('platform') == 'tiktok':
            video['display_title'] = video['title_post']
        else:
            video['display_title'] = video['file_name']
    else:
        video['display_title'] = video.get('title_post') or video['file_name']
    
    # Procesar thumbnail_path para usar solo el nombre del archivo
    if video.get('thumbnail_path'):
        video['thumbnail_path'] = Path(video['thumbnail_path']).name
    
    return video


def process_image_carousels(db, videos, filters=None):
    """
    Procesa videos para agrupar imágenes de carrusel. 
    Busca TODOS los carruseles completos en la BD, no solo en esta página.
    """
    if not videos:
        return videos
    
    logger.info(f"🔍 CAROUSEL PROCESSING - Input videos: {len(videos)}")
    
    try:
        video_ids_in_page = [v['id'] for v in videos]
        
        # PASO 1: Obtener TODOS los carruseles completos de la BD usando nuevo esquema
        with db.get_connection() as conn:
            # Construir filtros WHERE si existen
            where_conditions = ["p.deleted_at IS NULL"]
            params = []

            if filters:
                if filters.get('creator_name'):
                    # 🚀 OPTIMIZADO: Usar JOIN con creators table
                    creator_names = [name.strip() for name in filters['creator_name'].split(',') if name.strip()]
                    if creator_names:
                        if len(creator_names) == 1:
                            where_conditions.append("c.name = ?")
                            params.append(creator_names[0])
                        else:
                            placeholders = ','.join(['?' for _ in creator_names])
                            where_conditions.append(f"c.name IN ({placeholders})")
                            params.extend(creator_names)
                if filters.get('platform'):
                    where_conditions.append("pl.name = ?")
                    params.append(filters['platform'])
                if filters.get('edit_status'):
                    where_conditions.append("m.edit_status = ?")
                    params.append(filters['edit_status'])
                if filters.get('processing_status'):
                    where_conditions.append("m.processing_status = ?")
                    params.append(filters['processing_status'])
                if filters.get('difficulty_level'):
                    where_conditions.append("m.difficulty_level = ?")
                    params.append(filters['difficulty_level'])
                if filters.get('search'):
                    where_conditions.append("(p.title_post LIKE ? OR m.file_name LIKE ? OR c.name LIKE ?)")
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term, search_term])

            where_clause = " AND ".join(where_conditions)

            # 🚀 OPTIMIZADO: Buscar SOLO los items de carrusel que están en esta página específica
            video_ids_str = ','.join(str(v['id']) for v in videos)
            query = f'''
                SELECT m.id, p.id as post_id, m.carousel_order
                FROM media m
                JOIN posts p ON m.post_id = p.id
                LEFT JOIN creators c ON p.creator_id = c.id
                LEFT JOIN platforms pl ON p.platform_id = pl.id
                WHERE m.id IN ({video_ids_str})
                AND p.is_carousel = TRUE
            '''
            
            cursor = conn.execute(query)

            page_carousel_groups = {}  # Carruseles que tienen videos en esta página

            for row in cursor:
                try:
                    media_id, post_id, carousel_order = row[0], row[1], row[2]

                    if post_id:  # Si tiene post_id y es carrusel, es parte de un carrusel
                        page_carousel_groups[post_id] = True
                except Exception as e:
                    logger.warning(f"Error procesando carrusel para media {row[0]}: {e}")
                    continue

            # Ahora obtener TODOS los items de los carruseles que están en esta página
            all_carousel_groups = {}  # {post_id: [items]}

            if page_carousel_groups:
                for post_id in page_carousel_groups.keys():
                    # 🚀 OPTIMIZADO: Usar columnas específicas con JOIN a creators
                    query = f'''
                        SELECT m.id, p.id as post_id, m.carousel_order
                        FROM media m
                        JOIN posts p ON m.post_id = p.id
                        LEFT JOIN creators c ON p.creator_id = c.id
                        LEFT JOIN platforms pl ON p.platform_id = pl.id
                        WHERE {where_clause}
                        AND p.id = ?
                        AND p.is_carousel = TRUE
                    '''

                    cursor = conn.execute(query, params + [post_id])

                    for row in cursor:
                        try:
                            media_id, post_id_result, carousel_order = row[0], row[1], row[2]

                            if post_id_result == post_id:
                                if post_id not in all_carousel_groups:
                                    all_carousel_groups[post_id] = []
                                all_carousel_groups[post_id].append({
                                    'video_id': media_id,
                                    'order': carousel_order or 0
                                })
                        except Exception as e:
                            logger.warning(f"Error procesando carrusel para media {row[0]}: {e}")
                            continue
        
        # Solo mantener carruseles con múltiples items
        complete_carousels = {
            post_id: items for post_id, items in all_carousel_groups.items()
            if len(items) > 1
        }

        logger.info(f"🔍 CAROUSEL PROCESSING - Found {len(complete_carousels)} complete carousels in this page")

        if not complete_carousels:
            logger.info(f"🔍 CAROUSEL PROCESSING - No carousels in this page, returning {len(videos)} original videos")
            return videos  # No hay carruseles, devolver originales

        # PASO 2: Procesar videos de esta página
        processed_videos = []
        carousel_processed = set()

        # Crear lookup: video_id → post_id
        video_to_carousel = {}
        for post_id, items in complete_carousels.items():
            for item in items:
                video_to_carousel[item['video_id']] = post_id

        # NUEVO: Pre-determinar qué video de cada carrusel debe ser el representante
        # Para evitar duplicados, el representante siempre debe ser el video con menor ID del carrusel completo
        carousel_representatives = {}
        for post_id, items in complete_carousels.items():
            videos_in_page = [item['video_id'] for item in items if item['video_id'] in video_ids_in_page]
            if videos_in_page:
                # El representante es SIEMPRE el video con menor ID del carrusel completo, no solo de esta página
                all_video_ids_in_carousel = [item['video_id'] for item in items]
                global_representative = min(all_video_ids_in_carousel)

                # Solo incluir este carrusel si el representante está en esta página
                if global_representative in video_ids_in_page:
                    carousel_representatives[post_id] = global_representative
                    logger.info(f"📍 CAROUSEL REP - post_id:{post_id}, representative:{global_representative}, videos_in_page:{videos_in_page}, all_videos:{all_video_ids_in_carousel}")
                else:
                    # El representante está en otra página, no incluir este carrusel aquí
                    logger.info(f"🚫 CAROUSEL SKIP - post_id:{post_id}, representative:{global_representative} not in current page, videos_in_page:{videos_in_page}")

        for video in videos:
            video_id = video['id']

            if video_id in carousel_processed:
                logger.info(f"⏭️ SKIPPING - video_id:{video_id} already processed as part of carousel")
                continue

            # Si este video es parte de un carrusel completo
            if video_id in video_to_carousel:
                post_id = video_to_carousel[video_id]

                # Solo procesar si el carrusel debe aparecer en esta página (su representante está aquí)
                if post_id in carousel_representatives and video_id == carousel_representatives[post_id]:
                    carousel_items = complete_carousels[post_id]
                    carousel_items.sort(key=lambda x: x['order'])

                    logger.info(f"🎠 CREATING CAROUSEL - post_id:{post_id}, representative:{video_id}, items:{len(carousel_items)}")

                    # Crear el carrusel usando el video actual como base
                    carousel_video = video.copy()
                    carousel_video['is_carousel'] = True
                    carousel_video['carousel_items'] = [
                        {
                            'id': item['video_id'],
                            'order': item['order']
                        } for item in carousel_items
                    ]
                    carousel_video['carousel_count'] = len(carousel_items)

                    # Marcar TODOS los videos del carrusel en esta página como procesados
                    for item in carousel_items:
                        if item['video_id'] in video_ids_in_page:
                            carousel_processed.add(item['video_id'])

                    processed_videos.append(carousel_video)

                else:
                    # Este video es parte de un carrusel, pero no es el representante o el representante no está en esta página
                    logger.info(f"⏭️ SKIPPING CAROUSEL MEMBER - video_id:{video_id}, post_id:{post_id}, not representative")
                    continue

            else:
                # Video individual (no es parte de un carrusel)
                processed_videos.append(video)
        
        logger.info(f"🔍 CAROUSEL PROCESSING - Output videos: {len(processed_videos)} (reduced from {len(videos)})")
        return processed_videos
        
    except Exception as e:
        logger.error(f"Error en process_image_carousels: {e}")
        return videos  # Fallback: devolver videos originales