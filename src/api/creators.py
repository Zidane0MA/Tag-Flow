"""
Tag-Flow V2 - Creators API Blueprint
API endpoints para gestión de creadores y suscripciones
"""

import json
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

creators_bp = Blueprint('creators', __name__, url_prefix='/api')

@creators_bp.route('/creators')
def api_get_creators():
    """API endpoint para obtener lista de creadores con sus plataformas y suscripciones"""
    try:
        from src.service_factory import get_database
        db = get_database()
        
        # Obtener todos los creadores únicos desde videos
        unique_creators = db.get_unique_creators()
        
        creators_data = []
        
        for creator_name in unique_creators:
            # Obtener videos del creador para extraer plataformas
            videos = db.get_videos({'creator_name': creator_name}, limit=4000)
            
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
        
        # Procesar videos para JSON (similar al endpoint principal de videos)
        for video in videos:
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
            
            # Preparar título apropiado para el frontend
            if video.get('platform') in ['tiktok', 'instagram'] and video.get('title'):
                if (video.get('platform') == 'instagram' and 
                    video.get('title') and 
                    video.get('title') != video.get('file_name', '').replace('.mp4', '')):
                    video['display_title'] = video['title']
                elif video.get('platform') == 'tiktok':
                    video['display_title'] = video['title']
                else:
                    video['display_title'] = video['file_name']
            else:
                video['display_title'] = video['file_name']
            
            # Procesar thumbnail_path para usar solo el nombre del archivo
            if video.get('thumbnail_path'):
                from pathlib import Path
                video['thumbnail_path'] = Path(video['thumbnail_path']).name
        
        return jsonify({
            'success': True,
            'videos': videos,
            'total': total_videos,
            'creator': creator_name,
            'platform': platform,
            'subscription_id': subscription_id
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
                cursor = conn.execute('SELECT name, display_name FROM creators WHERE id = ?', (subscription_info['creator_id'],))
                creator_row = cursor.fetchone()
                if creator_row:
                    subscription_info['creator'] = creator_row[0]
                    subscription_info['creatorDisplayName'] = creator_row[1]
        
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
        
        return jsonify({
            'success': True,
            'videos': videos,
            'total': total_videos,
            'subscription_id': subscription_id,
            'subscription_type': subscription_type,
            'list_filter': list_filter
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo videos de subscription {subscription_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500