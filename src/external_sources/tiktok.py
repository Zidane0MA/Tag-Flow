"""
Tag-Flow V2 - TikTok Tokkit Handler
Specialized handler for TikTok videos from 4K Tokkit database
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from .base import DatabaseExtractor

import logging
logger = logging.getLogger(__name__)


class TikTokTokkitHandler(DatabaseExtractor):
    """Handler for TikTok videos from 4K Tokkit database"""
    
    def __init__(self, db_path: Optional[Path] = None, base_path: Optional[Path] = None):
        super().__init__(db_path)
        # Auto-derive base path from database path if not provided
        if base_path is None and db_path is not None:
            self.base_path = db_path.parent  # Database is in the same folder as downloaded content
        else:
            self.base_path = base_path
    
    def extract_videos(self, offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
        """Extraer videos de TikTok desde BD de 4K Tokkit con nueva estructura completa
        Solo incluye videos que han sido descargados (downloaded=1)
        """
        if limit is not None:
            self.logger.debug(f"Extrayendo videos de TikTok descargados (offset: {offset}, limit: {limit})...")
        else:
            self.logger.debug("Extrayendo videos de TikTok descargados...")
        videos = []

        if not self.is_available():
            return videos

        try:
            # Query completa con datos de suscripción según especificación
            if limit is not None:
                # Para asegurar integridad de carruseles de TikTok, primero obtenemos los base_ids únicos
                # con el límite aplicado, luego obtenemos todos los elementos de esos carruseles
                base_id_query = """
                SELECT DISTINCT 
                    CASE 
                        WHEN mi.id LIKE '%_index_%' THEN SUBSTR(mi.id, 1, INSTR(mi.id, '_index_') - 1)
                        ELSE mi.id
                    END as base_id
                FROM MediaItems mi
                WHERE mi.relativePath IS NOT NULL AND mi.downloaded = 1
                GROUP BY base_id
                ORDER BY MIN(mi.databaseId) DESC
                LIMIT ? OFFSET ?
                """
                base_ids = [row[0] for row in self._execute_query(base_id_query, (limit, offset))]
                
                if not base_ids:
                    rows = []
                else:
                    # Ahora obtenemos todos los elementos de esos carruseles/posts específicos
                    base_id_placeholders = ','.join(['?' for _ in base_ids])
                    query = f"""
                    SELECT 
                        mi.databaseId as media_id,
                        mi.subscriptionDatabaseId,
                        mi.id as tiktok_id,
                        mi.authorName,
                        mi.description as video_title,
                        mi.relativePath,
                        
                        s.type as subscription_type,
                        s.name as subscription_name,
                        s.id as subscription_external_id
                        
                    FROM MediaItems mi
                    LEFT JOIN Subscriptions s ON mi.subscriptionDatabaseId = s.databaseId
                    WHERE mi.relativePath IS NOT NULL AND mi.downloaded = 1
                    AND (
                        CASE 
                            WHEN mi.id LIKE '%_index_%' THEN SUBSTR(mi.id, 1, INSTR(mi.id, '_index_') - 1)
                            ELSE mi.id
                        END
                    ) IN ({base_id_placeholders})
                    ORDER BY mi.databaseId DESC
                    """
                    rows = self._execute_query(query, base_ids)
            else:
                # Sin límite: obtener todos los videos descargados
                query = """
                SELECT 
                    mi.databaseId as media_id,
                    mi.subscriptionDatabaseId,
                    mi.id as tiktok_id,
                    mi.authorName,
                    mi.description as video_title,
                    mi.relativePath,
                    
                    s.type as subscription_type,
                    s.name as subscription_name,
                    s.id as subscription_external_id
                    
                FROM MediaItems mi
                LEFT JOIN Subscriptions s ON mi.subscriptionDatabaseId = s.databaseId
                WHERE mi.relativePath IS NOT NULL AND mi.downloaded = 1
                ORDER BY mi.databaseId DESC
                """
                rows = self._execute_query(query)

            # Configurar base path para TikTok
            tiktok_base = self.base_path or Path(".")

            for row in rows:
                video_data = self._process_tokkit_row_with_structure(row, tiktok_base)
                if video_data:
                    videos.append(video_data)

            self.logger.info(f"Extraídos {len(videos)} videos de TikTok desde Tokkit")
            return videos

        except Exception as e:
            self.logger.error(f"Error extrayendo videos de TikTok desde Tokkit: {e}")
            return videos

    def _process_tokkit_row_with_structure(self, row, tiktok_base: Path) -> Optional[Dict]:
        """Procesar una fila de TikTok Tokkit con estructura completa"""
        try:
            relative_path = self._safe_str(row['relativePath'])
            if not relative_path:
                return None

            # Strip leading slash from relative path to properly join with base path
            clean_relative_path = relative_path.lstrip('/')
            file_path = tiktok_base / clean_relative_path
            if not file_path.exists():
                self.logger.debug(f"Archivo TikTok no encontrado: {file_path}")
                return None

            tiktok_id = self._safe_str(row['tiktok_id'])
            if not tiktok_id:
                return None

            # Determinar creador y suscripción usando la nueva lógica v2
            creator_subscription_data = self._determine_tokkit_creator_and_subscription_v2(row)

            # Construir estructura completa del video
            video_data = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'title': self._safe_str(row['video_title']) or file_path.stem,
                'platform': 'tiktok',
                'video_url': f"https://www.tiktok.com/@{creator_subscription_data.get('creator_name', 'unknown')}/video/{tiktok_id}",
                'source': 'db',

                # Información del creador y suscripción
                'creator_name': creator_subscription_data.get('creator_name'),
                'creator_url': creator_subscription_data.get('creator_url'),
                'subscription_name': creator_subscription_data.get('subscription_name'),
                'subscription_type': creator_subscription_data.get('subscription_type'),
                'subscription_url': creator_subscription_data.get('subscription_url'),

                # Metadatos específicos de TikTok
                'tiktok_id': tiktok_id,
                'media_id': self._safe_int(row['media_id']),

                # Información de archivo
                'file_size': file_path.stat().st_size if file_path.exists() else 0,
            }

            # Detectar si es parte de un carrusel
            carousel_order = self._extract_carousel_order(tiktok_id)
            if carousel_order is not None:
                video_data['carousel_order'] = carousel_order
                # Extraer base_id para carruseles
                if '_index_' in tiktok_id:
                    video_data['carousel_base_id'] = tiktok_id.split('_index_')[0]

            return video_data

        except Exception as e:
            self.logger.error(f"Error procesando fila de TikTok Tokkit: {e}")
            return None

    def _determine_tokkit_creator_and_subscription_v2(self, row) -> Dict:
        """Determinar creador y suscripción para TikTok Tokkit usando estructura v2"""
        result = {
            'creator_name': None,
            'creator_url': None,
            'subscription_name': None,
            'subscription_type': None,
            'subscription_url': None
        }

        try:
            # Información del creador individual del video
            author_name = self._safe_str(row['authorName'])
            
            # Información de la suscripción
            subscription_type_raw = self._safe_str(row['subscription_type'])
            subscription_name = self._safe_str(row['subscription_name'])
            subscription_external_id = self._safe_str(row['subscription_external_id'])

            # 🎯 ESTABLECER CREADOR DEL VIDEO (siempre el autor individual)
            if author_name:
                result['creator_name'] = author_name
                result['creator_url'] = f"https://www.tiktok.com/@{author_name}"

            # 🎯 ESTABLECER SUSCRIPCIÓN SEGÚN TIPO
            if subscription_name and subscription_type_raw:
                # Mapear tipos de suscripción de Tokkit
                subscription_type_map = {
                    '0': 'account',      # Cuenta de usuario
                    '1': 'hashtag',      # Hashtag
                    '2': 'search',       # Búsqueda
                    'account': 'account',
                    'hashtag': 'hashtag',
                    'search': 'search'
                }

                subscription_type = subscription_type_map.get(subscription_type_raw, 'unknown')

                if subscription_type == 'account':
                    # 🎯 SUSCRIPCIÓN TIPO CUENTA: Videos de un usuario específico
                    result['subscription_name'] = subscription_name
                    result['subscription_type'] = 'creator'
                    result['subscription_url'] = f"https://www.tiktok.com/@{subscription_name}" if subscription_name else None

                elif subscription_type == 'hashtag':
                    # 🎯 SUSCRIPCIÓN TIPO HASHTAG: Videos de un hashtag específico
                    result['subscription_name'] = subscription_name
                    result['subscription_type'] = 'hashtag'
                    result['subscription_url'] = f"https://www.tiktok.com/tag/{subscription_name}" if subscription_name else None

                elif subscription_type == 'search':
                    # 🎯 SUSCRIPCIÓN TIPO BÚSQUEDA: Videos de una búsqueda específica
                    result['subscription_name'] = subscription_name
                    result['subscription_type'] = 'search'
                    result['subscription_url'] = None

            # 🎯 FALLBACK: Si no hay suscripción clara, crear una basada en el creador
            if not result['subscription_name'] and result['creator_name']:
                result['subscription_name'] = result['creator_name']
                result['subscription_type'] = 'creator'
                result['subscription_url'] = result['creator_url']

            # 🎯 DETECTAR SUBLISTAS DE CUENTA (favoritos, etc.)
            relative_path = self._safe_str(row['relativePath'] if 'relativePath' in row.keys() else '')
            account_sublists = self._detect_account_sublists_tiktok(relative_path)
            if account_sublists:
                # Si hay sublistas, usar la primera como tipo de suscripción más específico
                result['subscription_type'] = 'playlist'
                result['subscription_name'] = f"{result['subscription_name']} - {account_sublists[0]}"

            return result

        except Exception as e:
            self.logger.error(f"Error determinando creador/suscripción TikTok v2: {e}")
            return result

    def _detect_account_sublists_tiktok(self, relative_path: str) -> List[str]:
        """Detectar sublistas de cuenta TikTok (favoritos, etc.) desde la ruta relativa"""
        sublists = []

        try:
            if not relative_path:
                return sublists

            # Patrones comunes para sublistas de TikTok
            sublist_patterns = {
                'favorites': ['favorites', 'favoritos', 'liked'],
                'private': ['private', 'privado'],
                'drafts': ['drafts', 'borradores'],
                'collection': ['collection', 'colección']
            }

            path_lower = relative_path.lower()

            for sublist_type, patterns in sublist_patterns.items():
                for pattern in patterns:
                    if pattern in path_lower:
                        sublists.append(sublist_type.title())
                        break

            return sublists

        except Exception as e:
            self.logger.error(f"Error detectando sublistas TikTok: {e}")
            return sublists

    def _extract_carousel_order(self, tiktok_id: str) -> Optional[int]:
        """Extraer el orden del carrusel desde el ID de TikTok"""
        try:
            if '_index_' in tiktok_id:
                # Formato: base_id_index_N
                parts = tiktok_id.split('_index_')
                if len(parts) == 2:
                    return self._safe_int(parts[1])
            return None

        except Exception as e:
            self.logger.error(f"Error extrayendo orden de carrusel: {e}")
            return None