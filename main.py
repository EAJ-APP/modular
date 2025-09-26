import streamlit as st
from config.settings import Settings
from utils.helpers import setup_environment, check_dependencies
from database.connection import get_bq_client
from ui import render_sidebar, get_project_dataset_selection, show_cookies_tab, show_ecommerce_tab

def main():
    """Función principal de la aplicación"""
    # Configuración inicial
    check_dependencies()
    setup_environment()
    
    # Configuración de página
    st.set_page_config(
        page_title=Settings.APP_TITLE, 
        layout=Settings.PAGE_LAYOUT
    )
    st.title(Settings.APP_TITLE)

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
        st.error("Error al cargar proyectos y datasets")
        return

    # Tabs principales
    tab_titles = [
        "🍪 Cookies y Privacidad",
        "🛒 Ecommerce", 
        "📈 Adquisición",
        "🎯 Eventos",
        "👥 Usuarios",
        "🕒 Sesiones"
    ]
    tab_ids = ["cookies", "ecommerce", "acquisition", "events", "users", "sessions"]
    
    tabs = st.tabs(tab_titles)
    
    for tab, tab_id in zip(tabs, tab_ids):
        with tab:
            st.header(f"Análisis de {tab_id.capitalize()}")
            if tab_id == "cookies":
                show_cookies_tab(client, selected_project, selected_dataset, start_date, end_date)
            elif tab_id == "ecommerce":
                show_ecommerce_tab(client, selected_project, selected_dataset, start_date, end_date)
            else:
                st.info(f"🔧 Sección en desarrollo. Próximamente: consultas para {tab_id}")

if __name__ == "__main__":
    main()