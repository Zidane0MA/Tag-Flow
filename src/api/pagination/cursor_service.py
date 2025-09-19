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
        """Validar formato y rango de cursor"""
        if not cursor:
            return True

        try:
            # Intentar formatos múltiples
            timestamp = None

            # Formato ISO
            try:
                timestamp = datetime.fromisoformat(cursor.replace('Z', '+00:00'))
            except ValueError:
                # Formato alternativo: YYYY-MM-DD HH:MM:SS
                try:
                    timestamp = datetime.strptime(cursor, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass

            if timestamp is None:
                logger.warning(f"Invalid cursor format: {cursor}")
                return False

            # Validar rango razonable (último año)
            one_year_ago = datetime.now() - timedelta(days=365)
            if timestamp < one_year_ago:
                logger.warning(f"Cursor timestamp too old: {cursor}")
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
        limit: Optional[int] = None
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

            # Query principal optimizada
            order_direction = "DESC" if direction == "next" else "ASC"
            query = f"""
                SELECT {', '.join(select_fields)}
                {from_clause}
                WHERE {where_clause}
                ORDER BY m.{self.cursor_field} {order_direction}
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
                if direction == "next" and has_more:
                    # Asegurar formato ISO para cursor
                    cursor_value = data[-1][self.cursor_field]
                    if isinstance(cursor_value, str):
                        # Convertir a datetime y luego a ISO
                        try:
                            dt = datetime.strptime(cursor_value, '%Y-%m-%d %H:%M:%S')
                            next_cursor = dt.isoformat()
                        except ValueError:
                            next_cursor = cursor_value  # Fallback si ya está en formato correcto
                    else:
                        next_cursor = str(cursor_value)

                if direction == "next" and cursor:
                    prev_cursor = cursor
                elif direction == "prev" and data:
                    next_cursor = cursor
                    if len(data) == effective_limit:  # Puede haber más hacia atrás
                        cursor_value = data[-1][self.cursor_field]
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
            # Fallback a query simple
            return self._fallback_query(filters, effective_limit, start_time)

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

    def _fallback_query(self, filters, limit, start_time):
        """Query de fallback en caso de error"""
        try:
            query = """
                SELECT m.id, m.file_name, m.created_at, p.title_post, c.name as creator_name
                FROM media m
                JOIN posts p ON m.post_id = p.id
                LEFT JOIN creators c ON p.creator_id = c.id
                WHERE m.is_primary = TRUE AND p.deleted_at IS NULL
                ORDER BY m.created_at DESC
                LIMIT ?
            """

            cursor_obj = self.db.execute(query, [limit])
            rows = cursor_obj.fetchall()
            columns = [description[0] for description in cursor_obj.description]
            data = [dict(zip(columns, row)) for row in rows]

            query_time = time.time() - start_time

            return CursorResult(
                data=data,
                next_cursor=None,
                prev_cursor=None,
                has_more=False,
                total_estimated=len(data),
                performance_info={
                    'query_time_ms': round(query_time * 1000, 2),
                    'pagination_type': 'fallback',
                    'items_returned': len(data),
                    'error': 'Used fallback query'
                }
            )
        except Exception as e:
            logger.error(f"Fallback query failed: {e}")
            return CursorResult(
                data=[],
                next_cursor=None,
                prev_cursor=None,
                has_more=False,
                total_estimated=0,
                performance_info={
                    'query_time_ms': round((time.time() - start_time) * 1000, 2),
                    'pagination_type': 'error',
                    'items_returned': 0,
                    'error': str(e)
                }
            )