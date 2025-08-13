"""
Tag-Flow V2 - Creators API Blueprint
API endpoints para gestión de creadores y suscripciones
"""

import json
from flask import Blueprint, request, jsonify
import logging

# Import carousel processing function
from .videos import process_image_carousels, process_video_data_for_api

logger = logging.getLogger(__name__)

creators_bp = Blueprint('creators', __name__, url_prefix='/api')

@creators_bp.route('/creators')
def api_get_creators():
    """API endpoint para obtener lista de creadores con sus plataformas y suscripciones"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Usar método más eficiente: obtener creadores únicos directamente
        unique_creators = db.get_unique_creators()
        
        creators_data = []
        
        for creator_name in unique_creators:
            # Obtener una muestra de videos para detectar plataformas (más eficiente)
            videos = db.get_videos({'creator_name': creator_name}, limit=100)
            # Agrupar por plataforma
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
            
            creators_data.append(creator_data)
        
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
        
        # Construir filtros - usar exact match para creator_name
        filters = {'creator_name_exact': creator_name}
        if platform:
            filters['platform'] = platform
        
        # Solo aplicar límite si es mayor a 0
        if limit > 0:
            videos = db.get_videos(filters=filters, limit=limit, offset=offset)
        else:
            videos = db.get_videos(filters=filters, offset=offset)
        total_videos = db.count_videos(filters=filters)
        
        # Procesar cada video para la API usando función helper
        for video in videos:
            process_video_data_for_api(video)
            
            # ✅ NUEVO: Agregar información real de suscripción desde la BD
            if video.get('subscription_id'):
                try:
                    with db.get_connection() as conn:
                        cursor = conn.execute('''
                            SELECT s.name, s.type, s.platform, s.subscription_url 
                            FROM subscriptions s 
                            WHERE s.id = ?
                        ''', (video['subscription_id'],))
                        sub_row = cursor.fetchone()
                        if sub_row:
                            video['subscription_info'] = {
                                'id': video['subscription_id'],
                                'name': sub_row[0],
                                'type': sub_row[1], 
                                'platform': sub_row[2],
                                'url': sub_row[3]
                            }
                except Exception as e:
                    logger.warning(f"Error obteniendo subscription para video {video['id']}: {e}")
            
            # ✅ NUEVO: Agregar información real de listas desde la BD
            try:
                with db.get_connection() as conn:
                    cursor = conn.execute('''
                        SELECT vl.list_type, vl.source_path 
                        FROM video_lists vl 
                        WHERE vl.video_id = ?
                    ''', (video['id'],))
                    list_rows = cursor.fetchall()
                    if list_rows:
                        video['video_lists'] = [
                            {
                                'type': row[0],
                                'name': row[0].replace('_', ' ').title(),
                                'source_path': row[1]
                            } for row in list_rows
                        ]
            except Exception as e:
                logger.warning(f"Error obteniendo listas para video {video['id']}: {e}")
        
        # ✅ NUEVO: Procesar carruseles de imágenes
        processed_videos = process_image_carousels(db, videos, filters)
        
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
        
        # Obtener todas las suscripciones reales de la BD
        with db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT s.id, s.name, s.type, s.platform, s.subscription_url,
                       COUNT(v.id) as video_count
                FROM subscriptions s
                LEFT JOIN videos v ON v.subscription_id = s.id AND v.deleted_at IS NULL
                GROUP BY s.id, s.name, s.type, s.platform, s.subscription_url
                ORDER BY video_count DESC, s.name
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
        
        # Obtener información de la suscripción
        with db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT s.id, s.name, s.type, s.platform, s.subscription_url, s.creator_id,
                       COUNT(v.id) as video_count
                FROM subscriptions s
                LEFT JOIN videos v ON v.subscription_id = s.id AND v.deleted_at IS NULL
                WHERE s.id = ? AND s.type = ?
                GROUP BY s.id, s.name, s.type, s.platform, s.subscription_url, s.creator_id
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
        
        # Obtener conteo total de videos de la suscripción
        with db.get_connection() as conn:
            # Conteo total
            cursor = conn.execute('''
                SELECT COUNT(*) as total
                FROM videos v
                JOIN subscriptions s ON v.subscription_id = s.id
                WHERE s.id = ? AND s.type = ? AND v.deleted_at IS NULL
            ''', (subscription_id, subscription_type))
            total_count = cursor.fetchone()[0]
            
            # Conteo por tipo de lista
            cursor = conn.execute('''
                SELECT vl.list_type, COUNT(*) as count
                FROM videos v
                JOIN subscriptions s ON v.subscription_id = s.id
                LEFT JOIN video_lists vl ON vl.video_id = v.id
                WHERE s.id = ? AND s.type = ? AND v.deleted_at IS NULL
                GROUP BY vl.list_type
            ''', (subscription_id, subscription_type))
            
            list_counts = {}
            for row in cursor.fetchall():
                list_type = row[0] or 'feed'  # Si no hay tipo, asumir 'feed'
                list_counts[list_type] = row[1]
            
            # Si no hay conteos específicos, todo va a 'feed'
            if not list_counts and total_count > 0:
                list_counts['feed'] = total_count
        
        return jsonify({
            'success': True,
            'total': total_count,
            'list_counts': list_counts
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
        
        # Construir filtros para videos de la suscripción
        query = '''
            SELECT v.* FROM videos v
            JOIN subscriptions s ON v.subscription_id = s.id
            WHERE s.id = ? AND s.type = ? AND v.deleted_at IS NULL
        '''
        params = [subscription_id, subscription_type]
        
        # Filtrar por lista específica si se proporciona
        if list_filter and list_filter != 'all':
            query += '''
                AND EXISTS (
                    SELECT 1 FROM video_lists vl 
                    WHERE vl.video_id = v.id AND vl.list_type = ?
                )
            '''
            params.append(list_filter)
        
        query += ' ORDER BY v.created_at DESC'
        
        if limit > 0:
            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])
        
        with db.get_connection() as conn:
            cursor = conn.execute(query, params)
            videos = [dict(row) for row in cursor.fetchall()]
            
            # Contar total
            count_query = query.replace('SELECT v.*', 'SELECT COUNT(*)').split(' ORDER BY')[0]
            count_params = params[:-2] if limit > 0 else params
            cursor = conn.execute(count_query, count_params)
            total_videos = cursor.fetchone()[0]
        
        # Procesar videos (similar al endpoint principal)
        for video in videos:
            # Procesar characters
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
            
            # Agregar subscription_info
            if video.get('subscription_id'):
                try:
                    cursor = conn.execute('''
                        SELECT s.name, s.type, s.platform, s.subscription_url 
                        FROM subscriptions s 
                        WHERE s.id = ?
                    ''', (video['subscription_id'],))
                    sub_row = cursor.fetchone()
                    if sub_row:
                        video['subscription_info'] = {
                            'id': video['subscription_id'],
                            'name': sub_row[0],
                            'type': sub_row[1], 
                            'platform': sub_row[2],
                            'url': sub_row[3]
                        }
                except Exception as e:
                    logger.warning(f"Error obteniendo subscription para video {video['id']}: {e}")
            
            # Agregar video_lists
            try:
                cursor = conn.execute('''
                    SELECT vl.list_type, vl.source_path 
                    FROM video_lists vl 
                    WHERE vl.video_id = ?
                ''', (video['id'],))
                list_rows = cursor.fetchall()
                if list_rows:
                    video['video_lists'] = [
                        {
                            'type': row[0],
                            'name': row[0].replace('_', ' ').title(),
                            'source_path': row[1]
                        } for row in list_rows
                    ]
            except Exception as e:
                logger.warning(f"Error obteniendo listas para video {video['id']}: {e}")
            
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