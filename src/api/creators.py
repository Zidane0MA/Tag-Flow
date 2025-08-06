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
            videos = db.get_videos({'creator_name': creator_name}, limit=1000)
            
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
        videos = db.get_videos({'creator_name': creator_name}, limit=1000)
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
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Construir filtros
        filters = {'creator_name': creator_name}
        if platform:
            filters['platform'] = platform
        
        videos = db.get_videos(filters=filters, limit=limit, offset=offset)
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
        # Por ahora devolver estructura básica
        # TODO: Implementar cuando tengamos sistema completo de suscripciones
        special_subscriptions = [
            {
                'type': 'hashtag',
                'id': 'mmd',
                'name': 'MMD Videos',
                'platform': 'youtube',
                'postCount': 0,
                'url': 'https://youtube.com/results?search_query=mmd'
            },
            {
                'type': 'music',
                'id': 'lofi_beats',
                'name': 'Lofi Beats',
                'platform': 'tiktok',
                'postCount': 0,
                'url': 'https://tiktok.com/music/lofi-beats'
            }
        ]
        
        return jsonify({
            'success': True,
            'subscriptions': special_subscriptions
        })
        
    except Exception as e:
        logger.error(f"Error en API subscriptions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500