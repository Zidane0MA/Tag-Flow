"""
Tag-Flow V2 - TikTok Tokkit Handler
Specialized handler for TikTok videos from 4K Tokkit database
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from .base import DatabaseExtractor
import subprocess

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
        """Procesar una fila de 4K Tokkit con nueva estructura completa según especificación"""
        # Construir ruta completa del archivo
        relative_path = row['relativePath']
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        if relative_path.startswith('\\'):
            relative_path = relative_path[1:]
            
        file_path = tiktok_base / relative_path
        
        # ✅ Verificar que el archivo exista ANTES de verificar tipo
        if not file_path.exists():
            self.logger.debug(f"⚠️ Archivo no existe (eliminado manualmente?): {file_path}")
            self.logger.debug(f"   📍 URL: https://www.tiktok.com/@{row['authorName']}/video/{row['tiktok_id']}")
            return None
            
        # Aceptar tanto videos como imágenes (para carruseles de TikTok)
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        is_video = file_path.suffix.lower() in video_extensions
        is_image = file_path.suffix.lower() in image_extensions
        
        if not (is_video or is_image):
            return None
        
        # Construir URL del post según especificación
        tiktok_id_clean = row['tiktok_id']
        if '_index_' in str(tiktok_id_clean):
            # Para imágenes: remover _index_n1_n2 del ID
            tiktok_id_clean = tiktok_id_clean.split('_index_')[0]
        
        # URLs según especificación
        if is_video:
            post_url = f"https://www.tiktok.com/@{row['authorName']}/video/{tiktok_id_clean}"
        else:
            post_url = f"https://www.tiktok.com/@{row['authorName']}/photo/{tiktok_id_clean}"
        
        # Datos básicos del video
        video_data = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'title': row['video_title'] or file_path.stem,  # Usar description como título
            'post_url': post_url,  # URL del post según especificación
            'platform': 'tiktok',
            'content_type': 'video' if is_video else 'image',
            'source': 'db',
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            
            # Datos del downloader - CRÍTICO para batch_insert_videos
            'downloader_mapping': {
                'download_item_id': row['media_id'],
                'external_db_source': '4k_tokkit',
                'creator_from_downloader': row['authorName'],
                'is_carousel_item': '_index_' in str(row['tiktok_id']),
                'carousel_order': self._extract_carousel_order(str(row['tiktok_id'])) if '_index_' in str(row['tiktok_id']) else None,
                'carousel_base_id': str(row['tiktok_id']).split('_index_')[0] if '_index_' in str(row['tiktok_id']) else None
            }
        }
        
        # Determinar creador y suscripción según especificación
        creator_info = self._determine_tokkit_creator_and_subscription_v2(row)
        video_data.update(creator_info)
        
        return video_data

    def _determine_tokkit_creator_and_subscription_v2(self, row) -> Dict:
        """Determinar creador y suscripción para TikTok según especificación exacta"""
        result = {
            'creator_name': row['authorName'],
            'creator_url': f"https://www.tiktok.com/@{row['authorName']}",
            'subscription_name': None,
            'subscription_type': None,
            'subscription_url': None,
            'list_types': ['single']  # Por defecto para publicaciones sueltas
        }
        
        # CASO 1: Publicaciones sueltas (subscriptionDatabaseId = NULL)
        if not row['subscriptionDatabaseId']:
            # Videos sin suscripción - no crear suscripción
            result['subscription_name'] = None
            result['subscription_type'] = None
            result['subscription_url'] = None
            result['list_types'] = []  # Sin listas específicas
            return result
        
        # CASO 2: Suscripciones con subscription_type
        subscription_types = {
            1: 'account',    # cuenta - tipo 1
            2: 'hashtag',    # hashtag - tipo 2 
            3: 'music'       # música - tipo 3
        }
        
        if row['subscription_type'] in subscription_types:
            sub_type = subscription_types[row['subscription_type']]
            result['subscription_type'] = sub_type
            subscription_name = row['subscription_name']
            result['subscription_name'] = subscription_name
            
            # Construir URL de suscripción según especificación
            if sub_type == 'account':
                result['subscription_url'] = f"https://www.tiktok.com/@{subscription_name}"
                # Para cuentas, detectar sub-listas desde relativePath y modificar nombre si es necesario
                detected_sublists = self._detect_account_sublists_tiktok(row['relativePath'])
                result['list_types'] = detected_sublists
                
                # Si es una sublista específica, modificar el nombre de suscripción para distinguirlas
                if detected_sublists == ['liked']:
                    result['subscription_name'] = f"{subscription_name} - Liked"
                elif detected_sublists == ['favorites']:
                    result['subscription_name'] = f"{subscription_name} - Favorites"
            elif sub_type == 'hashtag':
                result['subscription_url'] = f"https://www.tiktok.com/tag/{subscription_name}"
                result['list_types'] = ['hashtag']  # Los hashtags son listas simples
            elif sub_type == 'music':
                # Música: "cancion nueva cinco" -> "cancion-nueva-cinco"
                clean_name = subscription_name.replace(' ', '-')
                result['subscription_url'] = f"https://www.tiktok.com/music/{clean_name}-{row['subscription_external_id']}"
                result['list_types'] = ['music']  # Las músicas son listas simples
        else:
            # Tipo desconocido - tratar como cuenta
            result['subscription_type'] = 'account'
            subscription_name = row['subscription_name'] or row['authorName']
            result['subscription_url'] = f"https://www.tiktok.com/@{subscription_name}"
            
            # Detectar sublistas y modificar nombre si es necesario
            detected_sublists = self._detect_account_sublists_tiktok(row['relativePath'])
            result['list_types'] = detected_sublists
            
            if detected_sublists == ['liked']:
                result['subscription_name'] = f"{subscription_name} - Liked"
            elif detected_sublists == ['favorites']:
                result['subscription_name'] = f"{subscription_name} - Favorites"  
            else:
                result['subscription_name'] = subscription_name
        
        return result

    def _detect_account_sublists_tiktok(self, relative_path: str) -> List[str]:
        """Detectar sublistas para cuentas TikTok según estructura de carpetas"""
        if not relative_path:
            return ['feed']
            
        # Normalizar separadores
        path_normalized = relative_path.replace('\\', '/').lower()
        
        if '/liked/' in path_normalized or '/liked' in path_normalized:
            return ['liked']
        elif '/favorites/' in path_normalized or '/favorites' in path_normalized:
            return ['favorites']
        else:
            return ['feed']  # Por defecto: feed principal

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