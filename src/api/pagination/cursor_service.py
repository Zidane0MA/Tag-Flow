"""
Tag-Flow V2 - Cursor Pagination Service
Ultra-optimized cursor-based pagination to replace OFFSET system
"""

import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class CursorResult:
    """Resultado unificado de cursor pagination"""
    data: List[Dict[str, Any]]
    next_cursor: Optional[str]
    prev_cursor: Optional[str]
    has_more: bool
    total_estimated: Optional[int]
    performance_info: Dict[str, Any]

class CursorPaginationService:
    """
    Servicio unificado para cursor pagination
    Reemplaza el sistema OFFSET con performance O(1)
    """

    def __init__(self, db_connection, cursor_field: str = 'created_at', page_size: int = 50):
        self.db = db_connection
        self.cursor_field = cursor_field
        self.page_size = page_size
        self.max_page_size = 100

    def validate_cursor(self, cursor: str) -> bool:
        """Validar formato y rango de cursor (soporta cursor compuesto timestamp|id y cursor simple de ID)"""
        if not cursor:
            return True

        try:
            # Determinar si cursor field es ID
            cursor_column_name = self.cursor_field.split('.')[-1]

            # Si el cursor field es ID, validar como ID simple
            if cursor_column_name == 'id':
                try:
                    cursor_id = int(cursor)
                    if cursor_id <= 0:
                        logger.warning(f"Invalid cursor ID: {cursor_id}")
                        return False
                    return True
                except ValueError:
                    logger.warning(f"Invalid cursor ID format: {cursor}")
                    return False

            # Para timestamps: Separar cursor compuesto si existe (formato: timestamp|id)
            cursor_parts = cursor.split('|', 1)
            timestamp_part = cursor_parts[0]

            # Si hay ID, validarlo
            if len(cursor_parts) == 2:
                try:
                    id_part = int(cursor_parts[1])
                    if id_part <= 0:
                        logger.warning(f"Invalid cursor ID: {id_part}")
                        return False
                except ValueError:
                    logger.warning(f"Invalid cursor ID format: {cursor_parts[1]}")
                    return False

            # Validar timestamp
            timestamp = None

            # Formato ISO
            try:
                timestamp = datetime.fromisoformat(timestamp_part.replace('Z', '+00:00'))
            except ValueError:
                # Formato alternativo: YYYY-MM-DD HH:MM:SS
                try:
                    timestamp = datetime.strptime(timestamp_part, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass

            if timestamp is None:
                logger.warning(f"Invalid cursor timestamp format: {timestamp_part}")
                return False

            # Validar rango razonable (último año)
            one_year_ago = datetime.now() - timedelta(days=365)
            if timestamp < one_year_ago:
                logger.warning(f"Cursor timestamp too old: {timestamp_part}")
                return False

            return True
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid cursor format: {cursor}, error: {e}")
            return False

    def get_videos(
        self,
        filters: Dict[str, Any] = None,
        cursor: Optional[str] = None,
        direction: str = 'next',
        limit: Optional[int] = None,
        sort_order: str = 'desc'
    ) -> CursorResult:
        """
        Obtener videos con cursor pagination optimizada

        Args:
            filters: Filtros de búsqueda (creator_name, platform, etc.)
            cursor: Cursor de paginación (timestamp)
            direction: 'next' o 'prev'
            limit: Número de resultados (máximo 100)
        """
        start_time = time.time()

        # Validar parámetros
        if not self.validate_cursor(cursor):
            cursor = None  # Reset invalid cursor

        effective_limit = min(limit or self.page_size, self.max_page_size)

        try:
            # Construir query optimizada
            from .query_builder import OptimizedQueryBuilder
            builder = OptimizedQueryBuilder(self.cursor_field)

            select_fields, from_clause, where_conditions, params = builder.build_base_query(filters or {})

            # Añadir condición de cursor
            if cursor:
                cursor_condition, cursor_params = builder.build_cursor_condition(cursor, direction)
                if cursor_condition:
                    where_conditions.append(cursor_condition)
                    params.extend(cursor_params)

            where_clause = " AND ".join(where_conditions)

            # Query principal optimizada con ORDER BY configurable
            # Para direction=next: usar sort_order tal como viene
            # Para direction=prev: invertir la dirección
            if direction == "next":
                order_direction = sort_order.upper()
            else:
                order_direction = "ASC" if sort_order.lower() == "desc" else "DESC"

            query = f"""
                SELECT {', '.join(select_fields)}
                {from_clause}
                WHERE {where_clause}
                ORDER BY {self.cursor_field} {order_direction}, m.id {order_direction}
                LIMIT ?
            """

            params.append(effective_limit + 1)  # +1 para detectar has_more

            # Ejecutar query
            cursor_obj = self.db.execute(query, params)
            rows = cursor_obj.fetchall()

            # Convertir a diccionarios
            columns = [description[0] for description in cursor_obj.description]
            data = [dict(zip(columns, row)) for row in rows]

            # Detectar si hay más datos
            has_more = len(data) > effective_limit
            if has_more:
                data = data[:effective_limit]

            # Calcular cursors
            next_cursor = None
            prev_cursor = None

            if data:
                if direction == "next":
                    last_item = data[-1]
                    # Extraer nombre de columna sin alias (e.g., "m.id" -> "id")
                    cursor_column_name = self.cursor_field.split('.')[-1]
                    cursor_value = last_item[cursor_column_name]

                    # Si el cursor field es ID, usar solo el ID (no compuesto)
                    if cursor_column_name == 'id':
                        # SOLO generar next_cursor si realmente HAY más datos
                        if has_more:
                            next_cursor = str(cursor_value)
                        else:
                            next_cursor = None
                    else:
                        # Para timestamps, crear cursor compuesto con ID para manejar empates
                        # SOLO generar next_cursor si realmente HAY más datos
                        if has_more:
                            last_id = last_item['id']

                            if isinstance(cursor_value, str):
                                # Convertir a datetime y luego a ISO
                                try:
                                    dt = datetime.strptime(cursor_value, '%Y-%m-%d %H:%M:%S')
                                    timestamp_iso = dt.isoformat()
                                except ValueError:
                                    timestamp_iso = cursor_value  # Fallback si ya está en formato correcto
                            else:
                                timestamp_iso = str(cursor_value)

                            # Cursor compuesto: timestamp|id
                            next_cursor = f"{timestamp_iso}|{last_id}"
                        else:
                            next_cursor = None

                if direction == "next" and cursor:
                    prev_cursor = cursor
                elif direction == "prev" and data:
                    next_cursor = cursor
                    if len(data) == effective_limit:  # Puede haber más hacia atrás
                        cursor_column_name = self.cursor_field.split('.')[-1]
                        cursor_value = data[-1][cursor_column_name]
                        if isinstance(cursor_value, str):
                            try:
                                dt = datetime.strptime(cursor_value, '%Y-%m-%d %H:%M:%S')
                                prev_cursor = dt.isoformat()
                            except ValueError:
                                prev_cursor = cursor_value
                        else:
                            prev_cursor = str(cursor_value)

            # Total estimado (solo para primera página)
            total_estimated = None
            if not cursor:
                total_estimated = self._estimate_total(builder, filters or {})

            query_time = time.time() - start_time

            performance_info = {
                'query_time_ms': round(query_time * 1000, 2),
                'pagination_type': 'cursor',
                'cursor_field': self.cursor_field,
                'items_returned': len(data),
                'direction': direction,
                'has_more': has_more
            }

            return CursorResult(
                data=data,
                next_cursor=next_cursor,
                prev_cursor=prev_cursor,
                has_more=has_more,
                total_estimated=total_estimated,
                performance_info=performance_info
            )

        except Exception as e:
            logger.error(f"Error in cursor pagination: {e}")
            raise e

    def get_creator_videos(
        self,
        creator_name: str,
        platform: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None
    ) -> CursorResult:
        """Videos de creador con cursor pagination"""
        filters = {'creator_name': creator_name}
        if platform:
            filters['platform'] = platform

        return self.get_videos(filters, cursor, 'next', limit)

    def get_subscription_videos(
        self,
        subscription_type: str,
        subscription_id: int,
        cursor: Optional[str] = None,
        limit: Optional[int] = None
    ) -> CursorResult:
        """Videos de suscripción con cursor pagination"""
        filters = {
            'subscription_type': subscription_type,
            'subscription_id': subscription_id
        }

        return self.get_videos(filters, cursor, 'next', limit)

    def get_trash_videos(
        self,
        cursor: Optional[str] = None,
        limit: Optional[int] = None
    ) -> CursorResult:
        """Videos eliminados (papelera) con cursor pagination"""
        start_time = time.time()

        # Validar parámetros
        if not self.validate_cursor(cursor):
            cursor = None  # Reset invalid cursor

        effective_limit = min(limit or self.page_size, self.max_page_size)

        try:
            # Construir query optimizada para trash (solo videos eliminados)
            from .query_builder import OptimizedQueryBuilder
            builder = OptimizedQueryBuilder(self.cursor_field)

            select_fields, from_clause, where_conditions, params = builder.build_base_query({})

            # Modificar condiciones para solo videos eliminados
            where_conditions = [
                "m.is_primary = TRUE",
                "p.deleted_at IS NOT NULL"  # Solo videos eliminados
            ]
            params = []

            # Añadir condición de cursor
            if cursor:
                cursor_condition, cursor_params = builder.build_cursor_condition(cursor, 'next')
                if cursor_condition:
                    where_conditions.append(cursor_condition)
                    params.extend(cursor_params)

            where_clause = " AND ".join(where_conditions)

            # Query principal optimizada - ordenar por deleted_at DESC, luego por id
            query = f"""
                SELECT {', '.join(select_fields)}, p.deleted_at
                {from_clause}
                WHERE {where_clause}
                ORDER BY p.deleted_at DESC, m.id DESC
                LIMIT ?
            """

            params.append(effective_limit + 1)  # +1 para detectar has_more

            # Ejecutar query
            cursor_obj = self.db.execute(query, params)
            rows = cursor_obj.fetchall()

            # Convertir a diccionarios
            columns = [description[0] for description in cursor_obj.description]
            data = [dict(zip(columns, row)) for row in rows]

            # Detectar si hay más datos
            has_more = len(data) > effective_limit
            if has_more:
                data = data[:effective_limit]

            # Calcular cursors para trash (usar deleted_at como cursor field)
            next_cursor = None
            prev_cursor = None

            if data and has_more:
                # Crear cursor compuesto (deleted_at|id)
                last_item = data[-1]
                deleted_at_value = last_item['deleted_at']
                last_id = last_item['id']

                if isinstance(deleted_at_value, str):
                    # Convertir a datetime y luego a ISO
                    try:
                        dt = datetime.strptime(deleted_at_value, '%Y-%m-%d %H:%M:%S')
                        timestamp_iso = dt.isoformat()
                    except ValueError:
                        timestamp_iso = deleted_at_value  # Fallback
                else:
                    timestamp_iso = str(deleted_at_value)

                # Cursor compuesto: deleted_at|id
                next_cursor = f"{timestamp_iso}|{last_id}"

            # Total estimado para trash
            total_estimated = None
            if not cursor:
                total_estimated = self._estimate_trash_total()

            query_time = time.time() - start_time

            performance_info = {
                'query_time_ms': round(query_time * 1000, 2),
                'pagination_type': 'cursor_trash',
                'cursor_field': 'deleted_at',
                'items_returned': len(data),
                'direction': 'next',
                'has_more': has_more
            }

            return CursorResult(
                data=data,
                next_cursor=next_cursor,
                prev_cursor=prev_cursor,
                has_more=has_more,
                total_estimated=total_estimated,
                performance_info=performance_info
            )

        except Exception as e:
            logger.error(f"Error in trash cursor pagination: {e}")
            raise e

    def _estimate_trash_total(self) -> int:
        """Estimar total de videos eliminados"""
        try:
            count_query = """
                SELECT COUNT(DISTINCT m.id)
                FROM media m
                JOIN posts p ON m.post_id = p.id
                WHERE m.is_primary = TRUE AND p.deleted_at IS NOT NULL
            """

            cursor_obj = self.db.execute(count_query)
            return cursor_obj.fetchone()[0]
        except Exception as e:
            logger.warning(f"Could not estimate trash total: {e}")
            return None


    def _estimate_total(self, builder, filters: Dict[str, Any]) -> int:
        """Estimar total de registros (solo para primera página)"""
        try:
            select_fields, from_clause, where_conditions, params = builder.build_base_query(filters)
            where_clause = " AND ".join(where_conditions)

            count_query = f"""
                SELECT COUNT(DISTINCT m.id)
                {from_clause}
                WHERE {where_clause}
            """

            cursor_obj = self.db.execute(count_query, params)
            return cursor_obj.fetchone()[0]
        except Exception as e:
            logger.warning(f"Could not estimate total: {e}")
            return None

