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

    def __init__(self, db_connection, cursor_field: str = 'p.id', page_size: int = 50):
        self.db = db_connection
        self.cursor_field = cursor_field
        self.page_size = page_size
        self.max_page_size = 100

    def _get_cursor_field_type(self) -> str:
        """Infiere el tipo de dato del campo del cursor para un parseo correcto."""
        field_name = self.cursor_field.split('.')[-1]
        
        if field_name in ['title_post', 'file_name']:
            return 'string'
        
        if field_name == 'id':
            return 'id'
            
        # Por defecto, se asume numérico (timestamps, tamaños, duraciones)
        return 'numeric'

    def validate_cursor(self, cursor: str) -> bool:
        """
        Valida el formato y rango del cursor de forma consciente del tipo de dato.
        - 'id': simple (ej: '123')
        - 'string': compuesto (ej: 'some_string|123')
        - 'numeric': compuesto (ej: '1672531200|123' o 'NULL|123')
        """
        if not cursor:
            return True

        try:
            field_type = self._get_cursor_field_type()

            if field_type == 'id':
                try:
                    return int(cursor) > 0
                except (ValueError, TypeError):
                    logger.warning(f"Invalid cursor ID format: {cursor}")
                    return False

            # Para 'string' y 'numeric', el cursor debe ser compuesto.
            cursor_parts = cursor.split('|', 1)
            if len(cursor_parts) != 2:
                logger.warning(f"Invalid composite cursor format for type '{field_type}': {cursor}")
                return False
            
            primary_part, id_part = cursor_parts

            # El ID siempre debe ser un entero válido.
            try:
                if int(id_part) <= 0:
                    logger.warning(f"Invalid cursor ID part: {id_part}")
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Invalid cursor ID part format: {id_part}")
                return False

            # Para 'string', la validación del ID es suficiente.
            if field_type == 'string':
                return True

            # Para 'numeric', validar la parte primaria (timestamp o número).
            if field_type == 'numeric':
                if primary_part == 'NULL':
                    return True
                try:
                    # Simplemente verificar que se pueda convertir a entero/flotante.
                    float(primary_part)
                    return True
                except (ValueError, TypeError):
                    logger.warning(f"Invalid numeric cursor primary part: {primary_part}")
                    return False

            logger.warning(f"Unhandled field type in cursor validation: {field_type}")
            return False

        except Exception as e:
            logger.warning(f"Error validating cursor '{cursor}': {e}", exc_info=True)
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
                cursor_condition, cursor_params = builder.build_cursor_condition(cursor, direction, sort_order)
                if cursor_condition:
                    where_conditions.append(cursor_condition)
                    params.extend(cursor_params)

            where_clause = " AND ".join(where_conditions)

            # Query principal optimizada con ORDER BY configurable
            if direction == "next":
                order_direction = sort_order.upper()
            else:
                order_direction = "ASC" if sort_order.lower() == "desc" else "DESC"

            # Añadir COLLATE NOCASE para campos de texto para asegurar consistencia
            field_name = self.cursor_field.split('.')[-1]
            if field_name in ['title_post', 'file_name']:
                order_by_clause = f"ORDER BY {self.cursor_field} COLLATE NOCASE {order_direction}, m.id {order_direction}"
            else:
                order_by_clause = f"ORDER BY {self.cursor_field} {order_direction}, m.id {order_direction}"

            query = f"""
                SELECT {', '.join(select_fields)}
                {from_clause}
                WHERE {where_clause}
                {order_by_clause}
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
                # For 'next' direction, the next_cursor is based on the last item.
                if direction == "next" and has_more:
                    last_item = data[-1]
                    cursor_column_name = self.cursor_field.split('.')[-1]
                    
                    # If sorting by 'id', the cursor is simple (just the ID).
                    if cursor_column_name == 'id':
                        next_cursor = str(last_item['id'])
                    # For all other fields, create a composite cursor (value|id).
                    else:
                        cursor_value = last_item.get(cursor_column_name)
                        last_id = last_item['id']
                        
                        if cursor_value is None:
                            primary_part = "NULL"
                        else:
                            # The primary part can be a string (title), int (date), or float.
                            # str() handles all cases correctly for cursor creation.
                            primary_part = str(cursor_value)
                        
                        next_cursor = f"{primary_part}|{last_id}"

                # For 'prev' direction, the 'next_cursor' is the one we started with.
                elif direction == "prev":
                    next_cursor = cursor
                
                # The 'prev_cursor' is the current cursor when moving forward.
                if direction == "next" and cursor:
                    prev_cursor = cursor
                # For 'prev' direction, a new 'prev_cursor' is generated from the first item.
                elif direction == "prev" and has_more:
                    # Create a prev_cursor from the first item in the reversed result set.
                    first_item = data[0]
                    cursor_column_name = self.cursor_field.split('.')[-1]

                    if cursor_column_name == 'id':
                        prev_cursor = str(first_item['id'])
                    else:
                        cursor_value = first_item.get(cursor_column_name)
                        first_id = first_item['id']

                        if cursor_value is None:
                            primary_part = "NULL"
                        else:
                            primary_part = str(cursor_value)
                        
                        prev_cursor = f"{primary_part}|{first_id}"

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

