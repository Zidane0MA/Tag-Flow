"""
Tag-Flow V2 - Efficient Pagination System
Sistema de paginación optimizado para grandes conjuntos de datos
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class PaginationMeta:
    """Metadatos de paginación"""
    current_page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int]
    prev_page: Optional[int]
    start_item: int
    end_item: int

@dataclass
class PaginatedResult:
    """Resultado paginado con datos y metadatos"""
    data: List[Any]
    meta: PaginationMeta
    performance_info: Dict[str, Any]

class BasePaginator(ABC):
    """Clase base para paginadores"""

    def __init__(self, per_page: int = 50, max_per_page: int = 100):
        self.per_page = min(per_page, max_per_page)
        self.max_per_page = max_per_page

    @abstractmethod
    def paginate(self, query_params: Dict[str, Any], page: int) -> PaginatedResult:
        """Método abstracto para paginación"""
        pass

    def _create_meta(self, page: int, total_items: int) -> PaginationMeta:
        """Crear metadatos de paginación"""
        total_pages = math.ceil(total_items / self.per_page) if total_items > 0 else 1
        page = max(1, min(page, total_pages))

        has_next = page < total_pages
        has_prev = page > 1
        next_page = page + 1 if has_next else None
        prev_page = page - 1 if has_prev else None

        start_item = (page - 1) * self.per_page + 1
        end_item = min(page * self.per_page, total_items)

        return PaginationMeta(
            current_page=page,
            per_page=self.per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
            next_page=next_page,
            prev_page=prev_page,
            start_item=start_item,
            end_item=end_item
        )

class CursorPaginator(BasePaginator):
    """
    Paginador basado en cursor para mejor rendimiento en grandes datasets
    Usa un campo ordenado (como timestamp) en lugar de OFFSET
    """

    def __init__(self, cursor_field: str = 'created_at', per_page: int = 50):
        super().__init__(per_page)
        self.cursor_field = cursor_field

    def paginate(self, query_params: Dict[str, Any], page: int) -> PaginatedResult:
        """Implementación del método abstracto - redirige a paginate_posts"""
        # Este método es requerido por la clase abstracta pero usamos paginate_posts
        raise NotImplementedError("Use paginate_posts() instead")

    def paginate_posts(self, db_connection, filters: Dict[str, Any],
                      cursor: Optional[str] = None, direction: str = 'next') -> PaginatedResult:
        """
        Paginar posts usando cursor-based pagination

        Args:
            db_connection: Conexión a la base de datos
            filters: Filtros de búsqueda
            cursor: Cursor de paginación (timestamp)
            direction: 'next' o 'prev'
        """
        import time
        start_time = time.time()

        # Construir WHERE clause
        where_conditions = ["p.deleted_at IS NULL"]
        params = []

        # Filtros comunes
        if filters.get('creator_name'):
            where_conditions.append("c.name = ?")
            params.append(filters['creator_name'])

        if filters.get('platform'):
            where_conditions.append("pl.name = ?")
            params.append(filters['platform'])

        if filters.get('edit_status'):
            where_conditions.append("m.edit_status = ?")
            params.append(filters['edit_status'])

        if filters.get('processing_status'):
            where_conditions.append("m.processing_status = ?")
            params.append(filters['processing_status'])

        if filters.get('search'):
            where_conditions.append("(p.title_post LIKE ? OR m.file_name LIKE ? OR c.name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term, search_term])

        # Cursor condition
        if cursor:
            if direction == 'next':
                where_conditions.append(f"m.{self.cursor_field} < ?")
            else:
                where_conditions.append(f"m.{self.cursor_field} > ?")
            params.append(cursor)

        where_clause = " AND ".join(where_conditions)

        # Query principal optimizada
        query = f"""
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
                m.{self.cursor_field},
                m.last_updated,
                p.post_url,
                p.publication_date,
                p.download_date,
                p.is_carousel,
                p.carousel_count
            FROM media m
            JOIN posts p ON m.post_id = p.id
            LEFT JOIN creators c ON p.creator_id = c.id
            LEFT JOIN platforms pl ON p.platform_id = pl.id
            WHERE {where_clause}
            ORDER BY m.{self.cursor_field} DESC
            LIMIT ?
        """

        params.append(self.per_page + 1)  # +1 para detectar si hay más

        cursor_obj = db_connection.execute(query, params)
        rows = cursor_obj.fetchall()

        # Convertir a diccionarios
        columns = [description[0] for description in cursor_obj.description]
        data = [dict(zip(columns, row)) for row in rows]

        # Detectar si hay más datos
        has_more = len(data) > self.per_page
        if has_more:
            data = data[:self.per_page]

        # Obtener nuevo cursor
        next_cursor = None
        if data and has_more:
            next_cursor = str(data[-1][self.cursor_field])

        # Calcular total aproximado (solo para primera página)
        total_items = None
        if not cursor:
            count_query = f"""
                SELECT COUNT(DISTINCT m.id)
                FROM media m
                JOIN posts p ON m.post_id = p.id
                LEFT JOIN creators c ON p.creator_id = c.id
                LEFT JOIN platforms pl ON p.platform_id = pl.id
                WHERE {where_clause.replace(f"m.{self.cursor_field} < ?", "1=1")}
            """
            count_params = [p for p in params if p != cursor][:-1]  # Remover cursor y limit
            cursor_obj = db_connection.execute(count_query, count_params)
            total_items = cursor_obj.fetchone()[0]

        query_time = time.time() - start_time

        # Crear metadatos simplificados para cursor pagination
        meta = PaginationMeta(
            current_page=1,  # No aplica en cursor pagination
            per_page=self.per_page,
            total_items=total_items or len(data),
            total_pages=1,  # No aplica en cursor pagination
            has_next=has_more,
            has_prev=cursor is not None,
            next_page=None,
            prev_page=None,
            start_item=1,
            end_item=len(data)
        )

        performance_info = {
            'query_time_ms': round(query_time * 1000, 2),
            'pagination_type': 'cursor',
            'cursor_field': self.cursor_field,
            'next_cursor': next_cursor,
            'items_returned': len(data)
        }

        return PaginatedResult(data=data, meta=meta, performance_info=performance_info)

class OffsetPaginator(BasePaginator):
    """
    Paginador tradicional basado en OFFSET para compatibilidad
    Optimizado para consultas pequeñas y medianas
    """

    def paginate(self, query_params: Dict[str, Any], page: int) -> PaginatedResult:
        """Implementación del método abstracto - redirige a paginate_posts"""
        # Este método es requerido por la clase abstracta pero usamos paginate_posts
        raise NotImplementedError("Use paginate_posts() instead")

    def paginate_posts(self, db_connection, filters: Dict[str, Any],
                      page: int = 1) -> PaginatedResult:
        """Paginar posts usando OFFSET traditional pagination"""
        import time
        start_time = time.time()

        page = max(1, page)
        offset = (page - 1) * self.per_page

        # Construir WHERE clause (similar al cursor paginator)
        where_conditions = ["p.deleted_at IS NULL"]
        params = []

        # Aplicar filtros
        if filters.get('creator_name'):
            where_conditions.append("c.name = ?")
            params.append(filters['creator_name'])

        if filters.get('platform'):
            where_conditions.append("pl.name = ?")
            params.append(filters['platform'])

        if filters.get('edit_status'):
            where_conditions.append("m.edit_status = ?")
            params.append(filters['edit_status'])

        if filters.get('processing_status'):
            where_conditions.append("m.processing_status = ?")
            params.append(filters['processing_status'])

        if filters.get('search'):
            where_conditions.append("(p.title_post LIKE ? OR m.file_name LIKE ? OR c.name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term, search_term])

        where_clause = " AND ".join(where_conditions)

        # Consulta de datos
        data_query = f"""
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
                p.is_carousel,
                p.carousel_count
            FROM media m
            JOIN posts p ON m.post_id = p.id
            LEFT JOIN creators c ON p.creator_id = c.id
            LEFT JOIN platforms pl ON p.platform_id = pl.id
            WHERE {where_clause}
            ORDER BY m.created_at DESC
            LIMIT ? OFFSET ?
        """

        # Consulta de conteo optimizada
        count_query = f"""
            SELECT COUNT(DISTINCT m.id)
            FROM media m
            JOIN posts p ON m.post_id = p.id
            LEFT JOIN creators c ON p.creator_id = c.id
            LEFT JOIN platforms pl ON p.platform_id = pl.id
            WHERE {where_clause}
        """

        # Ejecutar consultas en paralelo (simulated)
        count_start = time.time()
        cursor_obj = db_connection.execute(count_query, params)
        total_items = cursor_obj.fetchone()[0]
        count_time = time.time() - count_start

        data_start = time.time()
        cursor_obj = db_connection.execute(data_query, params + [self.per_page, offset])
        rows = cursor_obj.fetchall()
        data_time = time.time() - data_start

        # Convertir a diccionarios
        columns = [description[0] for description in cursor_obj.description]
        data = [dict(zip(columns, row)) for row in rows]

        total_time = time.time() - start_time

        # Crear metadatos
        meta = self._create_meta(page, total_items)

        performance_info = {
            'query_time_ms': round(total_time * 1000, 2),
            'count_time_ms': round(count_time * 1000, 2),
            'data_time_ms': round(data_time * 1000, 2),
            'pagination_type': 'offset',
            'offset': offset,
            'items_returned': len(data)
        }

        return PaginatedResult(data=data, meta=meta, performance_info=performance_info)

class SmartPaginator:
    """
    Paginador inteligente que elige automáticamente la mejor estrategia
    """

    def __init__(self):
        self.cursor_paginator = CursorPaginator(per_page=50)
        self.offset_paginator = OffsetPaginator(per_page=50)
        self.offset_threshold = 1000  # Cambiar a cursor después de 1000 items

    def paginate_posts(self, db_connection, filters: Dict[str, Any],
                      page: Optional[int] = None, cursor: Optional[str] = None) -> PaginatedResult:
        """
        Paginar posts usando la estrategia óptima

        Args:
            db_connection: Conexión a la base de datos
            filters: Filtros de búsqueda
            page: Número de página (para offset pagination)
            cursor: Cursor (para cursor pagination)
        """

        # Si se proporciona cursor, usar cursor pagination
        if cursor:
            return self.cursor_paginator.paginate_posts(db_connection, filters, cursor)

        # Si page es muy alta, usar cursor pagination
        if page and page * 50 > self.offset_threshold:
            logger.info(f"Switching to cursor pagination for page {page} (offset > {self.offset_threshold})")
            return self.cursor_paginator.paginate_posts(db_connection, filters)

        # Para páginas pequeñas, usar offset pagination
        return self.offset_paginator.paginate_posts(db_connection, filters, page or 1)

# Instancia global del paginador inteligente
smart_paginator = SmartPaginator()

def get_pagination_strategy(dataset_size: int, page: int = 1) -> str:
    """Determinar la mejor estrategia de paginación"""
    offset = (page - 1) * 50

    if dataset_size > 10000 and offset > 1000:
        return "cursor"
    elif dataset_size > 5000 and offset > 500:
        return "cursor_recommended"
    else:
        return "offset"