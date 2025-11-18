"""
Tag-Flow V2 - Creators API Blueprint
API endpoints para gestión de creadores y suscripciones
"""

import json
from flask import Blueprint, request, jsonify
import logging
from src.api.performance.cache import cached, CacheManager

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