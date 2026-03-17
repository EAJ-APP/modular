import streamlit as st
import sys
import os

# Añadir el path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar componentes de autenticación
from auth import SessionManager, AuthConfig
from ui.login_screen import show_login_screen

# Importar resto de componentes (solo si está autenticado)
def import_app_components():
    """Importa componentes de la app solo cuando sea necesario"""
    global Settings, check_dependencies, setup_environment
    global render_sidebar, get_project_dataset_selection
    global show_cookies_tab, show_ecommerce_tab, show_acquisition_tab
    global show_events_tab, show_users_tab, show_sessions_tab, show_monitoring_tab

    from config.settings import Settings
    from utils import setup_environment, check_dependencies
    from ui import (
        render_sidebar,
        get_project_dataset_selection,
        show_cookies_tab,
        show_ecommerce_tab,
        show_acquisition_tab,
        show_events_tab,
        show_users_tab,
        show_sessions_tab,
        show_monitoring_tab
    )

def main():
    """Función principal de la aplicación"""

    # Inicializar sesión
    SessionManager.initialize_session()

    # Verificar si el usuario está autenticado
    if not SessionManager.is_authenticated():
        # Mostrar pantalla de login
        show_login_screen()
        return

    # Usuario autenticado - cargar la aplicación principal
    show_main_app()

def show_main_app():
    """Muestra la aplicación principal (después de autenticación)"""

    # Importar componentes
    import_app_components()

    # Configuración inicial
    check_dependencies()
    setup_environment()

    # Configuración de página
    st.set_page_config(
        page_title="BigQuery Shield | FLAT 101",
        layout=Settings.PAGE_LAYOUT,
        page_icon="",
        initial_sidebar_state="expanded"
    )

    # Refrescar credenciales OAuth si es necesario
    if SessionManager.get_auth_method() == 'oauth':
        SessionManager.refresh_oauth_credentials()

    # Renderizar sidebar y obtener configuración PRIMERO
    development_mode, start_date, end_date = render_sidebar()

    # Obtener cliente de BigQuery desde la sesión
    client = SessionManager.get_bigquery_client()

    if not client:
        st.error(" Error: No hay cliente de BigQuery disponible")
        if st.button(" Reiniciar sesión"):
            SessionManager.logout()
            st.rerun()
        return

    # Selectores de proyecto y dataset
    try:
        selected_project, selected_dataset = get_project_dataset_selection(client)
    except Exception as e:
        st.error(f"Error al cargar proyectos y datasets: {e}")
        return

    # Detectar cambio de proyecto y resetear costes
    if 'current_billing_project' not in st.session_state:
        st.session_state.current_billing_project = selected_project
    elif st.session_state.current_billing_project != selected_project:
        # Proyecto cambió - resetear monitoring data
        st.session_state.monitoring_data = []
        st.session_state.current_billing_project = selected_project

    # Header con usuario, billing y logout (DESPUÉS de obtener proyecto)
    render_header(selected_project)

    # Línea divisoria
    st.divider()

    # Mostrar info de dataset seleccionado de forma compacta
    with st.expander("Información del Proyecto", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Proyecto", selected_project)
        with col2:
            st.metric("Dataset", selected_dataset)
        with col3:
            days_range = (end_date - start_date).days
            st.metric("Período", f"{days_range} días")

    # Tabs principales
    tab_titles = [
        " Cookies",
        " Ecommerce",
        " Adquisición",
        " Eventos",
        " Usuarios",
        " Sesiones",
        " Monitorización"
    ]
    tab_ids = ["cookies", "ecommerce", "acquisition", "events", "users", "sessions", "monitoring"]

    tabs = st.tabs(tab_titles)

    for tab, tab_id in zip(tabs, tab_ids):
        with tab:
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
                show_monitoring_tab(client, selected_project)

    # Footer profesional
    st.divider()
    footer_col1, footer_col2, footer_col3 = st.columns([2, 2, 1])
    with footer_col1:
        st.caption("© 2025 FLAT 101 Digital Business | BigQuery Shield")
    with footer_col2:
        st.caption(f" Analizando: {selected_project}.{selected_dataset}")
    with footer_col3:
        st.caption(f"v1.0.0")

def render_header(selected_project=None):
    """Renderiza el header con información del usuario, billing y logout"""
    from utils.billing_info import BillingCalculator

    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        try:
            st.image("assets/logo.png", width=150)
        except:
            st.markdown("### FLAT 101")

    with col2:
        st.title(" BigQuery Shield")
        st.markdown("**Plataforma de análisis avanzado para Google Analytics 4**")

    with col3:
        # Mostrar info del usuario
        user_info = SessionManager.get_user_info()
        auth_method = SessionManager.get_auth_method()

        # Mostrar nombre del usuario
        if user_info.get('name'):
            st.markdown(f"** {user_info['name']}**")

        # Mostrar método de autenticación
        method_labels = {
            'oauth': ' OAuth',
            'json': ' JSON',
            'secrets': ' Secrets'
        }
        st.caption(f"Método: {method_labels.get(auth_method, auth_method)}")

        # Botón de logout
        if st.button(" Cerrar Sesión", type="secondary", use_container_width=True):
            SessionManager.logout()
            st.rerun()

    # Nueva fila para Billing (debajo del header)
    st.markdown("---")

    billing_col1, billing_col2, billing_col3, billing_col4 = st.columns(4)

    with billing_col1:
        st.markdown("** Billing**")

    with billing_col2:
        # Proyecto facturado
        billing_project = BillingCalculator.get_billing_project(selected_project)
        st.caption(f" Factura a: **{billing_project}**")

    with billing_col3:
        # Información de última query
        last_query = BillingCalculator.get_last_query_info()
        if last_query:
            st.caption(f" Última Query: **{last_query['gb_used']:.3f} GB** • **${last_query['cost']:.6f}**")
        else:
            st.caption(" Última Query: **N/A**")

    with billing_col4:
        # Total de sesión
        session_info = BillingCalculator.get_session_total_info()
        if session_info['query_count'] > 0:
            st.caption(f" Total Sesión: **${session_info['total_cost']:.6f}** • **{session_info['total_gb']:.3f} GB**")
        else:
            st.caption(" Total Sesión: **$0.000000** • **0.000 GB**")

if __name__ == "__main__":
    main()
