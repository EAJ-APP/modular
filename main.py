import streamlit as st
import sys
import os

# Añadir el path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config.settings import Settings
    from utils import setup_environment, check_dependencies
    from database.connection import get_bq_client
    from ui import (
        render_sidebar, 
        get_project_dataset_selection, 
        show_cookies_tab, 
        show_ecommerce_tab, 
        show_acquisition_tab,
        show_events_tab,
        show_users_tab,
        show_sessions_tab,
        show_monitoring_tab  # NUEVO
    )
    
except ImportError as e:
    st.error(f"❌ Error de importación: {e}")
    st.stop()

def main():
    """Función principal de la aplicación"""
    # Configuración inicial
    check_dependencies()
    setup_environment()
    
    # Configuración de página
    st.set_page_config(
        page_title="BigQuery Shield | FLAT 101", 
        layout=Settings.PAGE_LAYOUT,
        page_icon="🛡️",
        initial_sidebar_state="expanded"
    )
    
    # Header con logo y título
    col1, col2 = st.columns([1, 4])
    with col1:
        # Intenta cargar el logo desde archivo local o URL
        try:
            st.image("assets/logo.png", width=150)
        except:
            # Si no existe el archivo, usar un placeholder o texto
            st.markdown("### FLAT 101")
    
    with col2:
        st.title("🛡️ BigQuery Shield")
        st.markdown("**Plataforma de análisis avanzado para Google Analytics 4**")
    
    # Línea divisoria
    st.divider()

    # Renderizar sidebar y obtener configuración
    development_mode, start_date, end_date = render_sidebar()

    # Conexión a BigQuery
    client = get_bq_client(
        st.session_state.creds if development_mode and "creds" in st.session_state else None
    )

    # Selectores de proyecto y dataset
    try:
        selected_project, selected_dataset = get_project_dataset_selection(client)
    except Exception as e:
        st.error(f"Error al cargar proyectos y datasets: {e}")
        return
    
    # Mostrar info de dataset seleccionado de forma compacta
    with st.expander("ℹ️ Información del Proyecto", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Proyecto", selected_project)
        with col2:
            st.metric("Dataset", selected_dataset)
        with col3:
            days_range = (end_date - start_date).days
            st.metric("Período", f"{days_range} días")

    # Tabs principales - AÑADIDO MONITORING
    tab_titles = [
        "🍪 Cookies",
        "🛒 Ecommerce", 
        "📈 Adquisición",
        "🎯 Eventos",
        "👥 Usuarios",
        "🕒 Sesiones",
        "📊 Monitorización"  # NUEVO
    ]
    tab_ids = ["cookies", "ecommerce", "acquisition", "events", "users", "sessions", "monitoring"]
    
    tabs = st.tabs(tab_titles)
    
    for tab, tab_id in zip(tabs, tab_ids):
        with tab:
            # Título más compacto dentro de cada tab
            if tab_id == "cookies":
                show_cookies_tab(client, selected_project, selected_dataset, start_date, end_date)
            elif tab_id == "ecommerce":
                show_ecommerce_tab(client, selected_project, selected_dataset, start_date, end_date)
            elif tab_id == "acquisition":
                show_acquisition_tab(client, selected_project, selected_dataset, start_date, end_date)
            elif tab_id == "events":
                show_events_tab(client, selected_project, selected_dataset, start_date, end_date)
            elif tab_id == "users":
                show_users_tab(client, selected_project, selected_dataset, start_date, end_date)
            elif tab_id == "sessions":
                show_sessions_tab(client, selected_project, selected_dataset, start_date, end_date)
            elif tab_id == "monitoring":
                show_monitoring_tab(client, selected_project)  # NUEVO
    
    # Footer profesional
    st.divider()
    footer_col1, footer_col2, footer_col3 = st.columns([2, 2, 1])
    with footer_col1:
        st.caption("© 2025 FLAT 101 Digital Business | BigQuery Shield")
    with footer_col2:
        st.caption(f"📊 Analizando: {selected_project}.{selected_dataset}")
    with footer_col3:
        st.caption(f"v1.0.0")

if __name__ == "__main__":
    main()
