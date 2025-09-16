"""
Tag-Flow V2 - Creators API Blueprint
API endpoints para gestión de creadores y suscripciones
"""

import json
from flask import Blueprint, request, jsonify
import logging
from src.api.performance.cache import cached, CacheManager

# Import carousel processing function
from .videos import process_image_carousels, process_video_data_for_api

logger = logging.getLogger(__name__)

creators_bp = Blueprint('creators', __name__, url_prefix='/api')

@cached(ttl=300, key_func=lambda limit=None: f"top_creators:{limit}")  # Cache por 5 minutos
def get_top_creators_cached(limit=None):
    """Obtener top creadores cacheados"""
    from src.service_factory import get_database
    db = get_database()

    with db.get_connection() as conn:
        query = """
            SELECT
                c.id,
                c.name,
                pl.name as platform,
                COUNT(DISTINCT p.id) as post_count
            FROM creators c
            LEFT JOIN posts p ON c.id = p.creator_id AND p.deleted_at IS NULL
            LEFT JOIN platforms pl ON c.platform_id = pl.id
            GROUP BY c.id, c.name, pl.name
            HAVING post_count > 0
            ORDER BY post_count DESC, c.name, pl.name
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor = conn.execute(query)
        return cursor.fetchall()

@creators_bp.route('/creators')
def api_get_creators():
    """API endpoint para obtener lista de creadores con sus plataformas y suscripciones"""
    try:
        # Usar datos cacheados
        rows = get_top_creators_cached()

        # Agrupar por creador
        creators_dict = {}
        for row in rows:
            creator_id, creator_name, platform, post_count = row

            if creator_name not in creators_dict:
                creators_dict[creator_name] = {
                    'id': creator_id,
                    'name': creator_name,
                    'displayName': creator_name,
                    'platforms': {}
                }

            if platform:
                platforms = creators_dict[creator_name]['platforms']
                if platform not in platforms:
                    # Mapear URLs específicas por plataforma
                    platform_urls = {
                        'youtube': f'https://www.youtube.com/@{creator_name.lower().replace(" ", "")}',
                        'tiktok': f'https://www.tiktok.com/@{creator_name.lower().replace(" ", "")}',
                        'instagram': f'https://www.instagram.com/{creator_name.lower().replace(" ", "")}',
                        'facebook': f'https://www.facebook.com/{creator_name.lower().replace(" ", "")}',
                        'twitter': f'https://twitter.com/{creator_name.lower().replace(" ", "")}',
                        'twitch': f'https://www.twitch.tv/{creator_name.lower().replace(" ", "")}',
                        'discord': f'https://discord.gg/{creator_name.lower().replace(" ", "")}',
                        'vimeo': f'https://vimeo.com/{creator_name.lower().replace(" ", "")}'
                    }
                    
                    # Mapear tipos de suscripción por plataforma
                    subscription_types = {
                        'youtube': ('channel', 'Canal'),
                        'tiktok': ('feed', 'Feed'),
                        'instagram': ('feed', 'Feed'),
                        'facebook': ('account', 'Página'),
                        'twitter': ('account', 'Cuenta'),
                        'twitch': ('channel', 'Canal'),
                        'discord': ('account', 'Servidor'),
                        'vimeo': ('channel', 'Canal')
                    }
                    
                    sub_type, sub_name = subscription_types.get(platform, ('feed', 'Feed'))
                    
                    platforms[platform] = {
                        'url': platform_urls.get(platform, f'https://{platform}.com/{creator_name.lower().replace(" ", "")}'),
                        'postCount': post_count,
                        'subscriptions': [
                            {
                                'type': sub_type,
                                'id': f'{creator_name.lower().replace(" ", "_")}_{platform}_main',
                                'name': f'{sub_name} Principal'
                            }
                        ]
                    }
                else:
                    platforms[platform]['postCount'] = post_count

        creators_data = list(creators_dict.values())
        
        return jsonify({
            'success': True,
            'creators': creators_data
        })
        
    except Exception as e:
        logger.error(f"Error en API creators: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@creators_bp.route('/creator/<creator_name>')
def api_get_creator(creator_name):
    """API endpoint para obtener información detallada de un creador"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Verificar que el creador existe
        videos = db.get_videos({'creator_name': creator_name}, limit=4000)
        if not videos:
            return jsonify({'success': False, 'error': 'Creator not found'}), 404
        
        # Agrupar por plataforma y construir estructura
        platforms = {}
        for video in videos:
            platform = video['platform']
            if platform not in platforms:
                # Mapear URLs específicas por plataforma
                platform_urls = {
                    'youtube': f'https://www.youtube.com/@{creator_name.lower().replace(" ", "")}',
                    'tiktok': f'https://www.tiktok.com/@{creator_name.lower().replace(" ", "")}',
                    'instagram': f'https://www.instagram.com/{creator_name.lower().replace(" ", "")}',
                    'facebook': f'https://www.facebook.com/{creator_name.lower().replace(" ", "")}',
                    'twitter': f'https://twitter.com/{creator_name.lower().replace(" ", "")}',
                    'twitch': f'https://www.twitch.tv/{creator_name.lower().replace(" ", "")}',
                    'discord': f'https://discord.gg/{creator_name.lower().replace(" ", "")}',
                    'vimeo': f'https://vimeo.com/{creator_name.lower().replace(" ", "")}'
                }
                
                # Mapear tipos de suscripción por plataforma
                subscription_types = {
                    'youtube': ('channel', 'Canal'),
                    'tiktok': ('feed', 'Feed'),
                    'instagram': ('feed', 'Feed'),
                    'facebook': ('account', 'Página'),
                    'twitter': ('account', 'Cuenta'),
                    'twitch': ('channel', 'Canal'),
                    'discord': ('account', 'Servidor'),
                    'vimeo': ('channel', 'Canal')
                }
                
                sub_type, sub_name = subscription_types.get(platform, ('feed', 'Feed'))
                
                platforms[platform] = {
                    'url': platform_urls.get(platform, f'https://{platform}.com/{creator_name.lower().replace(" ", "")}'),
                    'postCount': 0,
                    'subscriptions': [
                        {
                            'type': sub_type,
                            'id': f'{creator_name.lower().replace(" ", "_")}_{platform}_main',
                            'name': f'{sub_name} Principal'
                        }
                    ]
                }
            platforms[platform]['postCount'] += 1
        
        creator_data = {
            'name': creator_name,
            'displayName': creator_name,
            'platforms': platforms
        }
        
        return jsonify({
            'success': True,
            'creator': creator_data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo creador {creator_name}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@creators_bp.route('/creator/<creator_name>/videos')
def api_get_creator_videos(creator_name):
    """API endpoint para obtener videos de un creador específico"""
    try:
        from src.service_factory import get_database
        db = get_database()

        # Obtener parámetros opcionales
        platform = request.args.get('platform')
        subscription_id = request.args.get('subscription_id')
        limit = int(request.args.get('limit', 0))  # 0 = sin límite
        offset = int(request.args.get('offset', 0))

        with db.get_connection() as conn:
            # Construir query con el nuevo esquema
            query = """
                SELECT
                    m.id,
                    p.title_post,
                    m.file_path,
                    m.file_name,
                    m.thumbnail_path,
                    m.file_size,
                    m.duration_seconds,
                    c.name as creator_name,
                    pl.name as platform,
                    m.detected_music,
                    m.detected_music_artist,
                    m.detected_characters,
                    m.final_music,
                    m.final_music_artist,
                    m.final_characters,
                    m.difficulty_level,
                    m.edit_status,
                    m.processing_status,
                    m.notes,
                    m.created_at,
                    m.last_updated,
                    p.post_url,
                    p.publication_date,
                    p.download_date,
                    p.deleted_at,
                    p.is_carousel,
                    p.carousel_count,
                    s.id as subscription_id,
                    s.name as subscription_name,
                    s.subscription_type
                FROM media m
                JOIN posts p ON m.post_id = p.id
                LEFT JOIN creators c ON p.creator_id = c.id
                LEFT JOIN platforms pl ON p.platform_id = pl.id
                LEFT JOIN subscriptions s ON p.subscription_id = s.id
                WHERE p.deleted_at IS NULL AND c.name = ?
            """

            params = [creator_name]

            # Agregar filtros
            if platform and platform != 'all':
                query += " AND pl.name = ?"
                params.append(platform)

            if subscription_id:
                query += " AND s.id = ?"
                params.append(subscription_id)

            # Orden y límite
            query += " ORDER BY m.created_at DESC"
            if limit > 0:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            # Obtener videos
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            # Convertir a formato de videos
            videos = []
            for row in rows:
                video = {
                    'id': row[0],
                    'title_post': row[1],
                    'file_path': row[2],
                    'file_name': row[3],
                    'thumbnail_path': row[4],
                    'file_size': row[5],
                    'duration_seconds': row[6],
                    'creator_name': row[7] or 'Unknown',
                    'platform': row[8] or 'unknown',
                    'detected_music': row[9],
                    'detected_music_artist': row[10],
                    'detected_characters': row[11],
                    'final_music': row[12],
                    'final_music_artist': row[13],
                    'final_characters': row[14],
                    'difficulty_level': row[15] or 'low',
                    'edit_status': row[16] or 'pendiente',
                    'processing_status': row[17] or 'pending',
                    'notes': row[18],
                    'created_at': row[19],
                    'last_updated': row[20],
                    'post_url': row[21],
                    'publication_date': row[22],
                    'download_date': row[23],
                    'deleted_at': row[24],
                    'is_carousel': row[25],
                    'carousel_count': row[26],
                    'subscription_id': row[27],
                }

                # Agregar información de suscripción si está disponible
                if row[27]:  # subscription_id
                    video['subscription_info'] = {
                        'id': row[27],
                        'name': row[28],
                        'type': row[29]
                    }

                videos.append(video)

            # Obtener total count
            count_query = """
                SELECT COUNT(DISTINCT m.id)
                FROM media m
                JOIN posts p ON m.post_id = p.id
                LEFT JOIN creators c ON p.creator_id = c.id
                LEFT JOIN platforms pl ON p.platform_id = pl.id
                WHERE p.deleted_at IS NULL AND c.name = ?
            """
            count_params = [creator_name]

            if platform and platform != 'all':
                count_query += " AND pl.name = ?"
                count_params.append(platform)

            if subscription_id:
                count_query += " AND s.id = ?"
                count_params.append(subscription_id)

            cursor = conn.execute(count_query, count_params)
            total_videos = cursor.fetchone()[0]
        
        # Procesar cada video para la API usando función helper
        for video in videos:
            process_video_data_for_api(video)

        # Procesar carruseles de imágenes
        try:
            processed_videos = process_image_carousels(db, videos, {})
        except:
            # Si falla el procesado de carruseles, usar videos sin procesar
            processed_videos = videos
        
        # Calcular has_more correctamente considerando la consolidación de carruseles
        original_count = len(videos)
        processed_count = len(processed_videos)
        
        # Cálculo simple y directo de has_more
        if limit > 0:
            # Verificar si hay más contenido en el siguiente offset normal
            next_offset = offset + original_count
            has_more = next_offset < total_videos
            logger.info(f"📊 CREATOR HAS_MORE - offset:{offset}, original_count:{original_count}, next_offset:{next_offset}, total:{total_videos}, has_more:{has_more}")
        else:
            # Sin límite, no hay más
            has_more = False
        
        return jsonify({
            'success': True,
            'videos': processed_videos,
            'total': total_videos,
            'creator': creator_name,
            'platform': platform,
            'subscription_id': subscription_id,
            'has_more': has_more,
            'returned_count': len(processed_videos),
            'original_count': original_count
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo videos de creador {creator_name}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@creators_bp.route('/subscriptions')
def api_get_subscriptions():
    """API endpoint para obtener lista de suscripciones especiales (hashtags, música, etc.)"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Obtener todas las suscripciones reales de la BD usando nuevo esquema
        with db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT s.id, s.name, s.subscription_type, pl.name as platform, s.subscription_url,
                       COUNT(DISTINCT p.id) as post_count
                FROM subscriptions s
                LEFT JOIN posts p ON p.subscription_id = s.id AND p.deleted_at IS NULL
                LEFT JOIN platforms pl ON s.platform_id = pl.id
                GROUP BY s.id, s.name, s.subscription_type, pl.name, s.subscription_url
                ORDER BY post_count DESC, s.name
            ''')
            subscriptions_data = []
            for row in cursor.fetchall():
                subscriptions_data.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'platform': row[3],
                    'url': row[4],
                    'postCount': row[5]
                })
        
        return jsonify({
            'success': True,
            'subscriptions': subscriptions_data
        })
        
    except Exception as e:
        logger.error(f"Error en API subscriptions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@creators_bp.route('/subscription/<subscription_type>/<subscription_id>')
def api_get_subscription_info(subscription_type, subscription_id):
    """API endpoint para obtener información de una suscripción específica"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Obtener información de la suscripción usando nuevo esquema
        with db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT s.id, s.name, s.subscription_type, pl.name as platform, s.subscription_url, s.creator_id,
                       COUNT(DISTINCT p.id) as post_count
                FROM subscriptions s
                LEFT JOIN platforms pl ON s.platform_id = pl.id
                LEFT JOIN posts p ON p.subscription_id = s.id AND p.deleted_at IS NULL
                WHERE s.id = ? AND s.subscription_type = ?
                GROUP BY s.id, s.name, s.subscription_type, pl.name, s.subscription_url, s.creator_id
            ''', (subscription_id, subscription_type))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'success': False, 'error': 'Subscription not found'}), 404
            
            subscription_info = {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'platform': row[3],
                'url': row[4],
                'creator_id': row[5],
                'postCount': row[6]
            }
            
            # Si tiene creator_id, obtener información del creador
            if subscription_info['creator_id']:
                cursor = conn.execute('SELECT name FROM creators WHERE id = ?', (subscription_info['creator_id'],))
                creator_row = cursor.fetchone()
                if creator_row:
                    subscription_info['creator'] = creator_row[0]
                    subscription_info['creatorDisplayName'] = creator_row[0]  # Usar name como display_name
        
        return jsonify({
            'success': True,
            'subscription': subscription_info
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo subscription {subscription_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@creators_bp.route('/subscription/<subscription_type>/<subscription_id>/stats')
def api_get_subscription_stats(subscription_type, subscription_id):
    """API endpoint para obtener estadísticas de una suscripción específica"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Obtener conteo total de posts/media de la suscripción usando nuevo esquema
        with db.get_connection() as conn:
            # Conteo total
            cursor = conn.execute('''
                SELECT COUNT(DISTINCT p.id) as total
                FROM posts p
                JOIN subscriptions s ON p.subscription_id = s.id
                WHERE s.id = ? AND s.subscription_type = ? AND p.deleted_at IS NULL
            ''', (subscription_id, subscription_type))
            total_count = cursor.fetchone()[0]

            # Conteo por tipo de categoría (usando post_categories)
            cursor = conn.execute('''
                SELECT pc.category_type, COUNT(DISTINCT p.id) as count
                FROM posts p
                JOIN subscriptions s ON p.subscription_id = s.id
                LEFT JOIN post_categories pc ON pc.post_id = p.id
                WHERE s.id = ? AND s.subscription_type = ? AND p.deleted_at IS NULL
                GROUP BY pc.category_type
            ''', (subscription_id, subscription_type))

            category_counts = {}
            for row in cursor.fetchall():
                category_type = row[0] or 'videos'  # Si no hay tipo, asumir 'videos'
                category_counts[category_type] = row[1]

            # Si no hay conteos específicos, todo va a 'videos'
            if not category_counts and total_count > 0:
                category_counts['videos'] = total_count
        
        return jsonify({
            'success': True,
            'total': total_count,
            'category_counts': category_counts
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de subscription {subscription_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@creators_bp.route('/subscription/<subscription_type>/<subscription_id>/videos')
def api_get_subscription_videos(subscription_type, subscription_id):
    """API endpoint para obtener videos de una suscripción específica"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Obtener parámetros opcionales
        list_filter = request.args.get('list')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Construir filtros para videos de la suscripción usando nuevo esquema
        query = '''
            SELECT
                m.id,
                p.title_post,
                m.file_path,
                m.file_name,
                m.thumbnail_path,
                m.file_size,
                m.duration_seconds,
                c.name as creator_name,
                pl.name as platform,
                m.detected_music,
                m.detected_music_artist,
                m.detected_characters,
                m.final_music,
                m.final_music_artist,
                m.final_characters,
                m.difficulty_level,
                m.edit_status,
                m.processing_status,
                m.notes,
                m.created_at,
                m.last_updated,
                p.post_url,
                p.publication_date,
                p.download_date,
                p.deleted_at,
                p.is_carousel,
                p.carousel_count,
                s.id as subscription_id,
                s.name as subscription_name,
                s.subscription_type
            FROM media m
            JOIN posts p ON m.post_id = p.id
            JOIN subscriptions s ON p.subscription_id = s.id
            LEFT JOIN creators c ON p.creator_id = c.id
            LEFT JOIN platforms pl ON p.platform_id = pl.id
            WHERE s.id = ? AND s.subscription_type = ? AND p.deleted_at IS NULL
        '''
        params = [subscription_id, subscription_type]

        # Filtrar por categoría específica si se proporciona
        if list_filter and list_filter != 'all':
            query += '''
                AND EXISTS (
                    SELECT 1 FROM post_categories pc
                    WHERE pc.post_id = p.id AND pc.category_type = ?
                )
            '''
            params.append(list_filter)
        
        query += ' ORDER BY m.created_at DESC'

        if limit > 0:
            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])

        with db.get_connection() as conn:
            cursor = conn.execute(query, params)
            videos = [dict(row) for row in cursor.fetchall()]

            # Contar total
            count_query = '''
                SELECT COUNT(DISTINCT m.id)
                FROM media m
                JOIN posts p ON m.post_id = p.id
                JOIN subscriptions s ON p.subscription_id = s.id
                LEFT JOIN creators c ON p.creator_id = c.id
                LEFT JOIN platforms pl ON p.platform_id = pl.id
                WHERE s.id = ? AND s.subscription_type = ? AND p.deleted_at IS NULL
            '''
            count_params = [subscription_id, subscription_type]

            if list_filter and list_filter != 'all':
                count_query += '''
                    AND EXISTS (
                        SELECT 1 FROM post_categories pc
                        WHERE pc.post_id = p.id AND pc.category_type = ?
                    )
                '''
                count_params.append(list_filter)

            cursor = conn.execute(count_query, count_params)
            total_videos = cursor.fetchone()[0]
        
        # Procesar cada video para la API usando función helper
        for video in videos:
            process_video_data_for_api(video)
            
            # Agregar subscription_info (ya disponible en los datos)
            if video.get('subscription_id'):
                video['subscription_info'] = {
                    'id': video['subscription_id'],
                    'name': video.get('subscription_name'),
                    'type': video.get('subscription_type'),
                    'platform': video.get('platform'),
                    'url': None  # URL no está disponible en esta consulta
                }

            # Agregar post_categories (reemplazo de video_lists)
            try:
                cursor = conn.execute('''
                    SELECT pc.category_type
                    FROM post_categories pc
                    WHERE pc.post_id = (
                        SELECT m2.post_id FROM media m2 WHERE m2.id = ?
                    )
                ''', (video['id'],))
                category_rows = cursor.fetchall()
                if category_rows:
                    video['post_categories'] = [
                        {
                            'type': row[0],
                            'name': row[0].replace('_', ' ').title()
                        } for row in category_rows
                    ]
                # Mantener compatibilidad con frontend existente
                video['video_lists'] = video.get('post_categories', [])
            except Exception as e:
                logger.warning(f"Error obteniendo categorías para media {video['id']}: {e}")
                video['post_categories'] = []
                video['video_lists'] = []
            
            # Procesar thumbnail_path
            if video.get('thumbnail_path'):
                from pathlib import Path
                video['thumbnail_path'] = Path(video['thumbnail_path']).name
        
        # ✅ NUEVO: Procesar carruseles de imágenes para suscripciones
        processed_videos = process_image_carousels(db, videos, {})
        
        # Calcular has_more correctamente considerando la consolidación de carruseles
        original_count = len(videos)
        processed_count = len(processed_videos)
        
        # Cálculo simple y directo de has_more
        if limit > 0:
            # Verificar si hay más contenido en el siguiente offset normal
            next_offset = offset + original_count
            has_more = next_offset < total_videos
            logger.info(f"📊 SUBSCRIPTION HAS_MORE - offset:{offset}, original_count:{original_count}, next_offset:{next_offset}, total:{total_videos}, has_more:{has_more}")
        else:
            # Sin límite, no hay más
            has_more = False
        
        return jsonify({
            'success': True,
            'videos': processed_videos,
            'total': total_videos,
            'subscription_id': subscription_id,
            'subscription_type': subscription_type,
            'list_filter': list_filter,
            'has_more': has_more,
            'returned_count': len(processed_videos),
            'original_count': original_count
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo videos de subscription {subscription_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================================
# 🆕 ENDPOINTS PARA GESTIÓN DE CUENTAS SECUNDARIAS
# ========================================

@creators_bp.route('/creator/<int:creator_id>/link-secondary', methods=['POST'])
def api_link_secondary_account(creator_id):
    """API endpoint para enlazar cuenta secundaria a creador principal"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        secondary_creator_id = data.get('secondary_creator_id')
        alias_type = data.get('alias_type', 'secondary')
        
        if not secondary_creator_id:
            return jsonify({'success': False, 'error': 'secondary_creator_id is required'}), 400
        
        # Validar que el alias_type sea válido
        valid_types = ['secondary', 'collaboration', 'alias']
        if alias_type not in valid_types:
            return jsonify({'success': False, 'error': f'alias_type must be one of: {valid_types}'}), 400
        
        # Verificar que el creador secundario existe
        secondary_creator = db.get_creator_by_name("")  # Usar método alternativo
        with db.get_connection() as conn:
            cursor = conn.execute('SELECT id, name FROM creators WHERE id = ?', (secondary_creator_id,))
            secondary_creator = cursor.fetchone()
            if not secondary_creator:
                return jsonify({'success': False, 'error': 'Secondary creator not found'}), 404
        
        # Enlazar
        if db.link_creator_as_secondary(secondary_creator_id, creator_id, alias_type):
            return jsonify({
                'success': True, 
                'message': f'Creator {secondary_creator[1]} linked as {alias_type} account'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to link accounts'}), 400
        
    except Exception as e:
        logger.error(f"Error linking secondary account: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@creators_bp.route('/creator/<int:creator_id>/unlink-secondary', methods=['POST'])
def api_unlink_secondary_account(creator_id):
    """API endpoint para desenlazar cuenta secundaria (convertirla en independiente)"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Verificar que el creador existe y es secundario
        with db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT id, name, parent_creator_id, is_primary 
                FROM creators WHERE id = ?
            ''', (creator_id,))
            creator = cursor.fetchone()
            
            if not creator:
                return jsonify({'success': False, 'error': 'Creator not found'}), 404
            
            if creator[3]:  # is_primary = True
                return jsonify({'success': False, 'error': 'Cannot unlink primary creator'}), 400
            
            if not creator[2]:  # parent_creator_id = None
                return jsonify({'success': False, 'error': 'Creator is already independent'}), 400
        
        # Desenlazar
        if db.unlink_secondary_creator(creator_id):
            return jsonify({
                'success': True, 
                'message': f'Creator {creator[1]} is now independent'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to unlink account'}), 400
        
    except Exception as e:
        logger.error(f"Error unlinking secondary account: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@creators_bp.route('/creator/<int:creator_id>/hierarchy')
def api_get_creator_hierarchy(creator_id):
    """API endpoint para obtener jerarquía completa de un creador"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        creator_data = db.get_creator_with_secondaries(creator_id)
        if not creator_data:
            return jsonify({'success': False, 'error': 'Creator not found'}), 404
        
        return jsonify({
            'success': True,
            'creator': creator_data
        })
        
    except Exception as e:
        logger.error(f"Error getting creator hierarchy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@creators_bp.route('/creator/<int:creator_id>/hierarchy/stats')
def api_get_creator_hierarchy_stats(creator_id):
    """API endpoint para obtener estadísticas de jerarquía de un creador"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        stats = db.get_creator_hierarchy_stats(creator_id)
        if not stats:
            return jsonify({'success': False, 'error': 'Creator not found'}), 404
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting creator hierarchy stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@creators_bp.route('/creators/search-hierarchy')
def api_search_creators_with_hierarchy():
    """API endpoint para buscar creadores incluyendo jerarquía"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        search_term = request.args.get('q', '')
        if not search_term:
            return jsonify({'success': False, 'error': 'Search term required'}), 400
        
        creators = db.search_creators_with_hierarchy(search_term)
        
        return jsonify({
            'success': True,
            'creators': creators,
            'count': len(creators)
        })
        
    except Exception as e:
        logger.error(f"Error searching creators with hierarchy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@creators_bp.route('/video/<int:video_id>/primary-creator')
def api_get_video_primary_creator(video_id):
    """API endpoint para obtener el creador principal de un video"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        creator_info = db.get_primary_creator_for_video(video_id)
        if not creator_info:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        return jsonify({
            'success': True,
            'creator_info': creator_info
        })
        
    except Exception as e:
        logger.error(f"Error getting primary creator for video: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500