#!/usr/bin/env python3
"""
Tag-Flow - Aplicación Visual con Editor Integrado
Autor: Sistema Tag-Flow
Versión: 1.1

Aplicación web interactiva para explorar, filtrar y EDITAR la colección de videos.
Ejecutar con: streamlit run 2_app_visual.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import os
from typing import List, Dict, Optional
import time

# Configuración de la página
st.set_page_config(
    page_title="Tag-Flow - Explorador de Videos",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

class TagFlowViewer:
    def __init__(self):
        """Inicializar el visualizador de Tag-Flow"""
        self.setup_paths()
        self.apply_custom_css()
        self.initialize_session_state()
        
    def setup_paths(self):
        """Configurar rutas del proyecto"""
        self.project_root = Path(__file__).parent
        self.csv_path = self.project_root / "data" / "videos.csv"
        
    def initialize_session_state(self):
        """Inicializar estado de sesión de Streamlit"""
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = {}
        if 'show_success' not in st.session_state:
            st.session_state.show_success = {}
        if 'data_version' not in st.session_state:
            st.session_state.data_version = 0
        
    def apply_custom_css(self):
        """Aplicar estilos CSS minimalistas"""
        st.markdown("""
        <style>
        /* Estilo minimalista general */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        
        /* Contenedor principal de video - sin bordes ni padding extra */
        .video-container {
            margin: 8px 0;
        }
        
        /* Hacer que las columnas tengan la misma altura */
        .row-widget.stColumns > div {
            height: 100%;
        }
        
        .row-widget.stColumns > div > div {
            height: 100%;
        }
        
        /* Contenedor de información que coincide con altura del video */
        .info-section {
            background-color: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 12px;
            height: 100%;
            display: flex;
            flex-direction: column;
            min-height: 400px;
        }
        
        /* Métricas minimalistas */
        .metric-item {
            background-color: #f5f5f5;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 8px 10px;
            margin: 4px 0;
            font-size: 0.9em;
        }
        
        .metric-item .label {
            font-weight: 600;
            color: #424242;
            font-size: 0.85em;
            margin-bottom: 2px;
        }
        
        .metric-item .value {
            color: #616161;
            line-height: 1.2;
        }
        
        /* Dificultad con colores simples */
        .difficulty-alto {
            background-color: #ffebee;
            border-color: #f44336;
        }
        
        .difficulty-medio {
            background-color: #fff8e1;
            border-color: #ff9800;
        }
        
        .difficulty-bajo {
            background-color: #e8f5e8;
            border-color: #4caf50;
        }
        
        /* Header simple */
        .app-header {
            background-color: #f5f5f5;
            padding: 16px;
            border-radius: 6px;
            text-align: center;
            margin-bottom: 20px;
            border: 1px solid #e0e0e0;
        }
        
        .app-header h1 {
            margin: 0;
            color: #424242;
            font-size: 1.8em;
            font-weight: 600;
        }
        
        .app-header h3 {
            margin: 8px 0 0 0;
            color: #757575;
            font-size: 1em;
            font-weight: 400;
        }
        
        /* Estadísticas compactas */
        .stat-card {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 12px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 1.5em;
            font-weight: 600;
            color: #424242;
            margin: 0;
        }
        
        .stat-label {
            font-size: 0.85em;
            color: #757575;
            margin: 4px 0 0 0;
        }
        
        /* Filtros minimalistas */
        .filter-header {
            background-color: #f5f5f5;
            color: #424242;
            padding: 12px;
            border-radius: 4px;
            text-align: center;
            margin-bottom: 16px;
            border: 1px solid #e0e0e0;
            font-weight: 600;
        }
        
        /* Botones simples */
        .edit-btn {
            background-color: #f5f5f5;
            border: 1px solid #e0e0e0;
            color: #424242;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 0.9em;
            width: 100%;
            margin-bottom: 12px;
        }
        
        /* Modo de edición simple */
        .edit-mode {
            background-color: #fff8e1;
            border: 2px solid #ff9800;
            border-radius: 6px;
            padding: 16px;
            margin: 12px 0;
        }
        
        /* Mensajes simples */
        .success-msg {
            background-color: #e8f5e8;
            border: 1px solid #4caf50;
            color: #2e7d32;
            padding: 8px 12px;
            border-radius: 4px;
            margin: 8px 0;
            text-align: center;
            font-size: 0.9em;
        }
        
        .info-msg {
            background-color: #e3f2fd;
            border: 1px solid #2196f3;
            color: #1565c0;
            padding: 16px;
            border-radius: 6px;
            margin: 16px 0;
            text-align: center;
        }
        
        /* Título de sección compacto */
        .section-title {
            color: #424242;
            font-weight: 600;
            font-size: 1em;
            margin-bottom: 8px;
            padding-bottom: 4px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        /* Separadores minimalistas */
        hr {
            border: none;
            height: 1px;
            background-color: #e0e0e0;
            margin: 16px 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    @st.cache_data
    def load_data(_self) -> pd.DataFrame:
        """Cargar datos desde CSV con cache para mejor rendimiento"""
        if not _self.csv_path.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(_self.csv_path)
            return df
        except Exception as e:
            st.error(f"Error cargando datos: {e}")
            return pd.DataFrame()
    
    def parse_characters(self, characters_str: str) -> List[str]:
        """Parsear la cadena de personajes en una lista"""
        if pd.isna(characters_str) or characters_str == 'Ninguno detectado':
            return []
        return [char.strip() for char in str(characters_str).split(',') if char.strip()]
    
    def get_all_characters(self, df: pd.DataFrame) -> List[str]:
        """Obtener lista única de todos los personajes"""
        all_characters = set()
        for chars_str in df['personajes'].dropna():
            characters = self.parse_characters(chars_str)
            all_characters.update(characters)
        return sorted(list(all_characters))
    
    def save_data_to_csv(self, df: pd.DataFrame) -> bool:
        """Guardar DataFrame actualizado al CSV"""
        try:
            df.to_csv(self.csv_path, index=False)
            # Incrementar versión de datos para forzar recarga
            st.session_state.data_version += 1
            # Limpiar cache
            self.load_data.clear()
            return True
        except Exception as e:
            st.error(f"Error guardando datos: {e}")
            return False
    
    def validate_edit_data(self, data: Dict) -> bool:
        """Validar datos editados"""
        # Validar que campos obligatorios no estén vacíos
        required_fields = ['archivo', 'creador']
        for field in required_fields:
            if not data.get(field, '').strip():
                st.error(f"El campo '{field}' no puede estar vacío")
                return False
        
        # Validar dificultad
        if data.get('dificultad_edicion', '').lower() not in ['alto', 'medio', 'bajo']:
            st.error("La dificultad debe ser: alto, medio o bajo")
            return False
        
        return True
    
    def update_video_data(self, df: pd.DataFrame, index: int, new_data: Dict) -> pd.DataFrame:
        """Actualizar datos de un video específico"""
        updated_df = df.copy()
        
        # Actualizar cada campo
        for column, value in new_data.items():
            if column in updated_df.columns:
                updated_df.at[index, column] = value
        
        # Agregar timestamp de edición
        updated_df.at[index, 'fecha_editado'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return updated_df
    
    def create_edit_interface(self, row: pd.Series, row_index: int) -> Optional[Dict]:
        """Crear interfaz de edición para un video"""
        st.markdown('<div class="edit-header">✏️ Modo de Edición</div>', unsafe_allow_html=True)
        
        # Crear formulario de edición
        with st.form(key=f"edit_form_{row_index}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📝 Información Básica")
                
                # Archivo (solo lectura)
                st.markdown("**📁 Archivo:**")
                st.markdown(f'<div class="readonly-field">{row["archivo"]}</div>', 
                           unsafe_allow_html=True)
                
                # Creador (editable)
                new_creador = st.text_input(
                    "👤 Creador:",
                    value=row.get('creador', ''),
                    help="Nombre del creador del video"
                )
                
                # Dificultad (editable)
                current_difficulty = row.get('dificultad_edicion', 'medio')
                difficulty_options = ['bajo', 'medio', 'alto']
                current_index = difficulty_options.index(current_difficulty) if current_difficulty in difficulty_options else 1
                
                new_difficulty = st.selectbox(
                    "⚡ Dificultad de Edición:",
                    options=difficulty_options,
                    index=current_index,
                    help="Nivel de dificultad de edición del video"
                )
            
            with col2:
                st.subheader("🎭 Contenido")
                
                # Personajes (editable)
                new_personajes = st.text_area(
                    "🎭 Personajes:",
                    value=row.get('personajes', ''),
                    height=100,
                    help="Personajes que aparecen en el video (separados por comas)"
                )
                
                # Música (editable)
                new_musica = st.text_area(
                    "🎵 Música:",
                    value=row.get('musica', ''),
                    height=100,
                    help="Música o sonidos del video"
                )
            
            # Botones de acción
            col_save, col_cancel = st.columns(2)
            
            with col_save:
                save_clicked = st.form_submit_button(
                    "💾 Guardar Cambios",
                    type="primary",
                    use_container_width=True
                )
            
            with col_cancel:
                cancel_clicked = st.form_submit_button(
                    "❌ Cancelar",
                    use_container_width=True
                )
            
            # Procesar acciones
            if save_clicked:
                new_data = {
                    'creador': new_creador.strip(),
                    'personajes': new_personajes.strip(),
                    'musica': new_musica.strip(),
                    'dificultad_edicion': new_difficulty,
                    'archivo': row['archivo']  # Mantener archivo original
                }
                
                if self.validate_edit_data(new_data):
                    return new_data
            
            elif cancel_clicked:
                return "CANCEL"
        
        return None
    
    def filter_dataframe(self, df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
        """Aplicar filtros al DataFrame"""
        filtered_df = df.copy()
        
        # Filtro por creador
        if filters['creadores']:
            filtered_df = filtered_df[filtered_df['creador'].isin(filters['creadores'])]
        
        # Filtro por dificultad
        if filters['dificultades']:
            filtered_df = filtered_df[filtered_df['dificultad_edicion'].isin(filters['dificultades'])]
        
        # Filtro por personajes
        if filters['personajes']:
            mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
            for _, row in filtered_df.iterrows():
                row_characters = self.parse_characters(row['personajes'])
                if any(char in row_characters for char in filters['personajes']):
                    mask[row.name] = True
            filtered_df = filtered_df[mask]
        
        # Filtro de texto libre
        if filters['texto_busqueda']:
            search_text = filters['texto_busqueda'].lower()
            mask = (
                filtered_df['archivo'].str.lower().str.contains(search_text, na=False) |
                filtered_df['musica'].str.lower().str.contains(search_text, na=False) |
                filtered_df['personajes'].str.lower().str.contains(search_text, na=False) |
                filtered_df['creador'].str.lower().str.contains(search_text, na=False)
            )
            filtered_df = filtered_df[mask]
        
        return filtered_df
    
    def create_sidebar_filters(self, df: pd.DataFrame) -> Dict:
        """Crear la barra lateral con filtros minimalistas"""
        st.sidebar.markdown('<div class="filter-header">🔍 Filtros</div>', 
                           unsafe_allow_html=True)
        
        filters = {}
        
        # Filtro de creadores
        st.sidebar.subheader("👤 Creadores")
        all_creators = sorted(df['creador'].unique()) if 'creador' in df.columns else []
        filters['creadores'] = st.sidebar.multiselect(
            "Seleccionar:",
            options=all_creators,
            default=[]
        )
        
        # Filtro de dificultad
        st.sidebar.subheader("⚡ Dificultad")
        difficulty_options = ['alto', 'medio', 'bajo']
        filters['dificultades'] = st.sidebar.multiselect(
            "Seleccionar:",
            options=difficulty_options,
            default=[]
        )
        
        # Filtro de personajes
        st.sidebar.subheader("🎭 Personajes")
        all_characters = self.get_all_characters(df)
        filters['personajes'] = st.sidebar.multiselect(
            "Seleccionar:",
            options=all_characters,
            default=[]
        )
        
        # Búsqueda de texto libre
        st.sidebar.subheader("🔤 Búsqueda")
        filters['texto_busqueda'] = st.sidebar.text_input(
            "Buscar texto:",
            placeholder="archivo, música, etc."
        )
        
        # Botón para limpiar filtros
        if st.sidebar.button("🗑️ Limpiar", use_container_width=True):
            st.experimental_rerun()
        
        st.sidebar.divider()
        
        # Modo de edición
        st.sidebar.subheader("✏️ Edición")
        
        show_edit_mode = st.sidebar.checkbox(
            "Activar modo edición",
            value=False,
            help="Muestra botones de edición en cada video"
        )
        
        filters['show_edit_mode'] = show_edit_mode
        
        return filters
    
    def display_statistics(self, df: pd.DataFrame, filtered_df: pd.DataFrame):
        """Mostrar estadísticas generales"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="stat-card">
                <p class="stat-number">{}</p>
                <p class="stat-label">📹 Total Videos</p>
            </div>
            """.format(len(df)), unsafe_allow_html=True)
        
        with col2:
            percentage = (len(filtered_df) / len(df) * 100) if len(df) > 0 else 0
            st.markdown("""
            <div class="stat-card">
                <p class="stat-number">{}</p>
                <p class="stat-label">🔍 Filtrados ({:.0f}%)</p>
            </div>
            """.format(len(filtered_df), percentage), unsafe_allow_html=True)
        
        with col3:
            creators_count = len(df['creador'].unique()) if 'creador' in df.columns else 0
            st.markdown("""
            <div class="stat-card">
                <p class="stat-number">{}</p>
                <p class="stat-label">👤 Creadores</p>
            </div>
            """.format(creators_count), unsafe_allow_html=True)
        
        with col4:
            characters_count = len(self.get_all_characters(df))
            st.markdown("""
            <div class="stat-card">
                <p class="stat-number">{}</p>
                <p class="stat-label">🎭 Personajes</p>
            </div>
            """.format(characters_count), unsafe_allow_html=True)
    
    def display_video_card(self, row: pd.Series, row_index: int, show_edit_mode: bool = False):
        """Mostrar una tarjeta de video individual con capacidades de edición"""
        video_path = Path(row['ruta_absoluta'])
        
        # Verificar si el archivo existe
        if not video_path.exists():
            st.error(f"❌ Archivo no encontrado: {video_path}")
            return
        
        # Verificar si está en modo de edición
        is_editing = st.session_state.edit_mode.get(row_index, False)
        
        # Mostrar mensaje de éxito si existe
        if st.session_state.show_success.get(row_index, False):
            st.markdown('<div class="success-msg">✅ Cambios guardados</div>', 
                       unsafe_allow_html=True)
            st.session_state.show_success[row_index] = False
        
        if is_editing:
            # Modo de edición
            st.markdown('<div class="edit-mode">', unsafe_allow_html=True)
            
            edit_result = self.create_edit_interface(row, row_index)
            
            if edit_result == "CANCEL":
                # Cancelar edición
                st.session_state.edit_mode[row_index] = False
                st.experimental_rerun()
            
            elif edit_result is not None:
                # Guardar cambios
                current_df = self.load_data()
                updated_df = self.update_video_data(current_df, row_index, edit_result)
                
                if self.save_data_to_csv(updated_df):
                    st.session_state.edit_mode[row_index] = False
                    st.session_state.show_success[row_index] = True
                    st.experimental_rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            # Layout: video a la izquierda, información a la derecha - misma altura
            col1, col2 = st.columns([2.5, 1.5])
            
            with col1:
                # Mostrar video
                try:
                    st.video(str(video_path))
                except Exception as e:
                    st.error(f"Error cargando video: {e}")
            
            with col2:
                # Contenedor de información con altura igual al video
                st.markdown('<div class="info-section">', unsafe_allow_html=True)
                
                # Botón de edición (si está habilitado)
                if show_edit_mode:
                    if st.button(f"✏️ Editar", key=f"edit_{row_index}", type="secondary", use_container_width=True):
                        st.session_state.edit_mode[row_index] = True
                        st.experimental_rerun()
                    st.markdown('<hr>', unsafe_allow_html=True)
                
                # Métricas compactas
                st.markdown(f"""
                <div class="metric-item">
                    <div class="label">📁 Archivo</div>
                    <div class="value">{row['archivo']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="metric-item">
                    <div class="label">👤 Creador</div>
                    <div class="value">{row['creador']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="metric-item">
                    <div class="label">🎵 Música</div>
                    <div class="value">{row['musica']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="metric-item">
                    <div class="label">🎭 Personajes</div>
                    <div class="value">{row['personajes']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Dificultad con colores sutiles
                difficulty = row['dificultad_edicion'].lower()
                difficulty_icons = {
                    'alto': '❌',
                    'medio': '⚠️', 
                    'bajo': '✅'
                }
                difficulty_icon = difficulty_icons.get(difficulty, '⚪')
                difficulty_class = f"metric-item difficulty-{difficulty}"
                
                st.markdown(f"""
                <div class="{difficulty_class}">
                    <div class="label">⚡ Dificultad</div>
                    <div class="value">{difficulty_icon} {row['dificultad_edicion'].title()}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Fechas compactas
                if 'fecha_procesado' in row and pd.notna(row['fecha_procesado']):
                    st.markdown(f"""
                    <div class="metric-item">
                        <div class="label">📅 Procesado</div>
                        <div class="value">{row['fecha_procesado']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Cerrar contenedor de información
                st.markdown('</div>', unsafe_allow_html=True)
    
    def display_video_list(self, df: pd.DataFrame, show_edit_mode: bool = False):
        """Mostrar lista de videos"""
        if df.empty:
            st.info("📝 No hay videos que coincidan con los filtros seleccionados.")
            return
        
        # Opciones de ordenamiento
        sort_col1, sort_col2 = st.columns(2)
        with sort_col1:
            sort_by = st.selectbox(
                "📊 Ordenar por:",
                options=['archivo', 'creador', 'dificultad_edicion', 'fecha_procesado'],
                index=0
            )
        
        with sort_col2:
            sort_ascending = st.selectbox(
                "📈 Orden:",
                options=[True, False],
                format_func=lambda x: "Ascendente" if x else "Descendente",
                index=0
            )
        
        # Ordenar DataFrame
        if sort_by in df.columns:
            df_sorted = df.sort_values(by=sort_by, ascending=sort_ascending)
        else:
            df_sorted = df
        
        # Paginación
        videos_per_page = st.selectbox("📄 Videos por página:", [5, 10, 20, 50], index=1)
        total_pages = max(1, (len(df_sorted) + videos_per_page - 1) // videos_per_page)
        
        if total_pages > 1:
            page = st.number_input(
                f"Página (1-{total_pages}):",
                min_value=1,
                max_value=total_pages,
                value=1
            )
        else:
            page = 1
        
        # Calcular rango de videos para mostrar
        start_idx = (page - 1) * videos_per_page
        end_idx = min(start_idx + videos_per_page, len(df_sorted))
        
        # Mostrar videos de la página actual
        st.markdown(f"### 🎬 Videos {start_idx + 1}-{end_idx} de {len(df_sorted)}")
        
        if show_edit_mode:
            st.info("✏️ **Modo de edición activado** - Puedes editar la información de cualquier video")
        
        for idx, (original_idx, row) in enumerate(df_sorted.iloc[start_idx:end_idx].iterrows()):
            with st.container():
                self.display_video_card(row, original_idx, show_edit_mode)
                if idx < end_idx - start_idx - 1:  # No mostrar divisor después del último elemento
                    st.divider()
    
    def show_help_section(self):
        """Mostrar sección de ayuda"""
        with st.expander("ℹ️ Ayuda y Uso"):
            st.markdown("""
            ### 🚀 Cómo usar Tag-Flow
            
            **Para añadir videos:**
            1. Coloca los videos en carpetas por creador dentro de `videos_a_procesar/`
            2. Ejecuta `python 1_script_analisis.py` en la terminal
            3. Recarga esta página para ver los nuevos videos
            
            **Filtros disponibles:**
            - **Creadores:** Filtra por quién creó el video
            - **Dificultad:** Filtra por nivel de edición (alto/medio/bajo)
            - **Personajes:** Filtra por personajes detectados automáticamente
            - **Búsqueda:** Busca texto en nombres, música, personajes, etc.
            
            **✨ NUEVO: Editor integrado:**
            - Activa "Mostrar controles de edición" en la barra lateral
            - Haz clic en "✏️ Editar" en cualquier video
            - Modifica creador, personajes, música y dificultad
            - Los cambios se guardan automáticamente
            
            **Reconocimiento automático:**
            - 👥 **Personajes:** Coloca fotos de referencia en `caras_conocidas/`
            - 🎵 **Música:** Configura tu API key en el archivo `.env`
            
            **Comandos útiles:**
            - `streamlit run 2_app_visual.py` - Ejecutar esta aplicación
            - `python 1_script_analisis.py` - Procesar nuevos videos
            """)
    
    def run(self):
        """Ejecutar la aplicación principal"""
        # Header minimalista
        st.markdown("""
        <div class="app-header">
            <h1>🎬 Tag-Flow</h1>
            <h3>Sistema de Clasificación de Videos</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Cargar datos
        df = self.load_data()
        
        if df.empty:
            st.markdown("""
            <div class="info-msg">
                <h3>📋 No hay datos disponibles</h3>
                <p><strong>Para empezar:</strong></p>
                <p>📁 Añade videos a <code>videos_a_procesar/</code></p>
                <p>⚙️ Ejecuta <code>python 1_script_analisis.py</code></p>
                <p>🔄 Recarga esta página</p>
            </div>
            """, unsafe_allow_html=True)
            self.show_help_section()
            return
        
        # Crear filtros en la barra lateral
        filters = self.create_sidebar_filters(df)
        
        # Aplicar filtros
        filtered_df = self.filter_dataframe(df, filters)
        
        # Mostrar estadísticas
        self.display_statistics(df, filtered_df)
        
        st.divider()
        
        # Mostrar videos
        self.display_video_list(filtered_df, filters['show_edit_mode'])
        
        # Sección de ayuda
        self.show_help_section()

def main():
    """Función principal"""
    try:
        viewer = TagFlowViewer()
        viewer.run()
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {e}")
        st.info("🔄 Intenta recargar la página")

if __name__ == "__main__":
    main()
