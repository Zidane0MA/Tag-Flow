"""
Tag-Flow V2 - Optimized Query Builder
Constructor de queries optimizado para cursor pagination con índices compuestos
"""

import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class OptimizedQueryBuilder:
    """Constructor de queries optimizado para cursor pagination"""

    def __init__(self, cursor_field: str):
        self.cursor_field = cursor_field

    def _get_cursor_field_type(self) -> str:
        """Infiere el tipo de dato del campo del cursor para un parseo correcto."""
        field_name = self.cursor_field.split('.')[-1]
        
        if field_name in ['title_post', 'file_name']:
            return 'string'
        
        if field_name == 'id':
            return 'id'
            
        # Por defecto, se asume numérico (timestamps, tamaños, duraciones)
        return 'numeric'

    def build_base_query(self, filters: Dict[str, Any]) -> Tuple[List[str], str, List[str], List[Any]]:
        """
        Construir query base con índices optimizados

        Returns:
            (select_fields, from_clause, where_conditions, params)
        """

        # SELECT optimizado con campos necesarios
        select_fields = [
            "m.id",
            "p.title_post",
            "m.file_path",
            "m.file_name",
            "m.thumbnail_path",
            "m.file_size",
            "m.duration_seconds",
            "c.name as creator_name",
            "pl.name as platform",
            "m.detected_music",
            "m.detected_music_artist",
            "m.detected_characters",
            "m.final_music",
            "m.final_music_artist",
            "m.final_characters",
            "m.difficulty_level",
            "m.edit_status",
            "m.processing_status",
            "m.notes",
            self.cursor_field,
            "m.last_updated",
            "p.post_url",
            "p.publication_date",
            "p.download_date",
            "p.is_carousel",
            "p.carousel_count",
            "s.id as subscription_id",
            "s.name as subscription_name",
            "s.subscription_type"
        ]

        # FROM con JOINs optimizados
        from_clause = """
            FROM media m
            JOIN posts p ON m.post_id = p.id
            LEFT JOIN creators c ON p.creator_id = c.id
            LEFT JOIN platforms pl ON p.platform_id = pl.id
            LEFT JOIN subscriptions s ON p.subscription_id = s.id
        """

        # WHERE base con índices compuestos
        where_conditions = [
            "m.is_primary = TRUE",
            "p.deleted_at IS NULL"
        ]
        params = []

        # Construir filtros optimizados
        where_conditions, params = self._build_filter_conditions(filters, where_conditions, params)

        return select_fields, from_clause, where_conditions, params

    def _build_filter_conditions(
        self,
        filters: Dict[str, Any],
        where_conditions: List[str],
        params: List[Any]
    ) -> Tuple[List[str], List[Any]]:
        """Construir condiciones de filtro optimizadas"""

        # Filtro por creador
        if filters.get('creator_name'):
            where_conditions.append("c.name = ?")
            params.append(filters['creator_name'])

        # Filtro por plataforma
        if filters.get('platform'):
            where_conditions.append("pl.name = ?")
            params.append(filters['platform'])

        # Filtro por estado de edición
        if filters.get('edit_status'):
            where_conditions.append("m.edit_status = ?")
            params.append(filters['edit_status'])

        # Filtro por estado de procesamiento
        if filters.get('processing_status'):
            where_conditions.append("m.processing_status = ?")
            params.append(filters['processing_status'])

        # Filtro por suscripción
        if filters.get('subscription_type') and filters.get('subscription_id'):
            where_conditions.append("s.subscription_type = ? AND s.id = ?")
            params.extend([filters['subscription_type'], filters['subscription_id']])

        # Búsqueda de texto optimizada
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            where_conditions.append(
                "(p.title_post LIKE ? OR m.file_name LIKE ? OR c.name LIKE ?)"
            )
            params.extend([search_term, search_term, search_term])

        # Filtro por dificultad
        if filters.get('difficulty_level'):
            where_conditions.append("m.difficulty_level = ?")
            params.append(filters['difficulty_level'])

        # Filtro por presencia de música
        if filters.get('has_music') is not None:
            if filters['has_music']:
                where_conditions.append("(m.detected_music IS NOT NULL OR m.final_music IS NOT NULL)")
            else:
                where_conditions.append("(m.detected_music IS NULL AND m.final_music IS NULL)")

        # Filtro por presencia de personajes
        if filters.get('has_characters') is not None:
            if filters['has_characters']:
                where_conditions.append(
                    "(m.detected_characters IS NOT NULL OR m.final_characters IS NOT NULL)"
                )
            else:
                where_conditions.append(
                    "(m.detected_characters IS NULL AND m.final_characters IS NULL)"
                )

        # Filtro por rango de duración
        if filters.get('min_duration'):
            where_conditions.append("m.duration_seconds >= ?")
            params.append(filters['min_duration'])

        if filters.get('max_duration'):
            where_conditions.append("m.duration_seconds <= ?")
            params.append(filters['max_duration'])

        # Filtro por rango de fechas
        if filters.get('date_from'):
            where_conditions.append(f"m.{self.cursor_field} >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_conditions.append(f"m.{self.cursor_field} <= ?")
            params.append(filters['date_to'])

        return where_conditions, params

    def build_cursor_condition(self, cursor: str, direction: str = 'next', sort_order: str = 'desc') -> Tuple[str, List[Any]]:
        """
        Construye una condición de cursor de tipo 'keyset pagination' que es consciente del tipo de dato.
        Maneja cursores simples (ID) y compuestos (valor|ID) para strings, números y NULLs.
        """
        if not cursor:
            return "", []

        try:
            field_type = self._get_cursor_field_type()
            
            # Determinar el operador de comparación basado en la dirección y el orden
            final_query_order = sort_order if direction == 'next' else ('asc' if sort_order == 'desc' else 'desc')
            op = '<' if final_query_order == 'desc' else '>'

            # --- Lógica de Paginación ---

            # Caso 1: Ordenación por 'id'. El cursor es simple (ej: "12345").
            if field_type == 'id':
                cursor_id = int(cursor)
                condition = f"m.id {op} ?"
                params = [cursor_id]
                return condition, params

            # Caso 2: Ordenación por otros campos. El cursor es compuesto (ej: "valor|12345").
            cursor_parts = cursor.split('|', 1)
            if len(cursor_parts) != 2:
                logger.warning(f"Invalid composite cursor format: {cursor}")
                return "", []

            primary_part, id_part = cursor_parts
            cursor_id = int(id_part)
            is_null_primary = primary_part == 'NULL'

            if is_null_primary:
                # Paginación dentro de un bloque de valores NULL. Solo se compara el ID.
                # La lógica compleja de transición entre NULL y no-NULL se simplifica
                # al depender del orden natural de SQL para los NULLs.
                condition = f"({self.cursor_field} IS NULL AND m.id {op} ?)"
                params = [cursor_id]
            else:
                # Paginación con valores no-NULL. Se usa comparación de tuplas.
                if field_type == 'string':
                    primary_value = primary_part
                    # Añadir COLLATE NOCASE para ordenación de texto consistente y correcta para Unicode.
                    condition = f"({self.cursor_field} COLLATE NOCASE, m.id) {op} (?, ?)"
                else:  # 'numeric'
                    primary_value = int(primary_part)
                    condition = f"({self.cursor_field}, m.id) {op} (?, ?)"

                params = [primary_value, cursor_id]

            return condition, params

        except Exception as e:
            logger.warning(f"Error building cursor condition for cursor '{cursor}': {e}", exc_info=True)
            return "", []

    def build_count_query(self, filters: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Construir query de conteo optimizada"""

        select_fields, from_clause, where_conditions, params = self.build_base_query(filters)
        where_clause = " AND ".join(where_conditions)

        count_query = f"""
            SELECT COUNT(DISTINCT m.id)
            {from_clause}
            WHERE {where_clause}
        """

        return count_query, params

    def get_performance_hints(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Obtener hints de performance para la query"""

        hints = {
            'recommended_indices': [],
            'query_complexity': 'low',
            'expected_performance': 'fast'
        }

        # Recomendar índices basado en filtros
        if filters.get('creator_name'):
            hints['recommended_indices'].append('idx_posts_creator_id')

        if filters.get('platform'):
            hints['recommended_indices'].append('idx_posts_platform_id')

        if filters.get('search'):
            hints['query_complexity'] = 'medium'
            hints['expected_performance'] = 'moderate'
            hints['recommended_indices'].append('idx_posts_title_fts')

        # Evaluar complejidad
        filter_count = len([k for k, v in filters.items() if v is not None])
        if filter_count > 3:
            hints['query_complexity'] = 'high'
        elif filter_count > 1:
            hints['query_complexity'] = 'medium'

        return hints