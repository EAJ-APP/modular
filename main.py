import streamlit as st
import sys
import os

# Configuración básica inicial
st.set_page_config(page_title="GA4 Explorer", layout="wide")
st.title("📊 Análisis Exploratorio GA4")

# Verificar dependencias críticas
try:
    import google.cloud.bigquery
    st.success("✅ google-cloud-bigquery importado correctamente")
except ImportError:
    st.error("❌ google-cloud-bigquery no está instalado")
    st.info("""
    **Solución:**
    1. Ejecuta: `pip install google-cloud-bigquery==3.20.1`
    2. O usa el requirements.txt simplificado
    """)
    st.stop()

try:
    import pandas as pd
    st.success("✅ pandas importado correctamente")
except ImportError:
    st.error("❌ pandas no está instalado")
    st.stop()

try:
    import plotly
    st.success("✅ plotly importado correctamente")
except ImportError:
    st.error("❌ plotly no está instalado")
    st.stop()

# Ahora intentar imports modulares
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from config.settings import Settings
    from utils import setup_environment, check_dependencies
    from database.connection import get_bq_client
    from ui import render_sidebar, get_project_dataset_selection, show_cookies_tab, show_ecommerce_tab
    
    st.success("✅ Todos los módulos importados correctamente")
    
except ImportError as e:
    st.error(f"❌ Error de importación modular: {e}")
    st.info("Usando modo de compatibilidad...")
    
    # Modo de compatibilidad - definir funciones básicas localmente
    def setup_environment():
        import warnings
        warnings.filterwarnings("ignore")
    
    def check_dependencies():
        pass  # Ya verificamos arriba

# Función principal
def main():
    setup_environment()
    check_dependencies()

    # Sidebar básico
    with st.sidebar:
        st.header("🔧 Configuración")
        development_mode = st.toggle("Modo desarrollo (usar JSON local)")
        
        if development_mode:
            creds_file = st.file_uploader("Sube credenciales JSON", type=["json"])
            if creds_file:
                with open("temp_creds.json", "wb") as f:
                    f.write(creds_file.getvalue())
                st.session_state.creds = "temp_creds.json"
        elif "gcp_service_account" not in st.secrets:
            st.error("⚠️ Configura los Secrets en Streamlit Cloud")
            st.stop()

        st.header("📅 Rango de Fechas")
        start_date = st.date_input("Fecha inicio", value=pd.to_datetime("2023-01-01"))
        end_date = st.date_input("Fecha fin", value=pd.to_datetime("today"))

    # Conexión a BigQuery
    try:
        client = get_bq_client(
            st.session_state.creds if development_mode and "creds" in st.session_state else None
        )
        st.sidebar.success("✅ Conectado a BigQuery")
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return

    # Selectores de proyecto y dataset
    try:
        projects = [p.project_id for p in client.list_projects()]
        selected_project = st.sidebar.selectbox("Proyecto", projects)
        datasets = [d.dataset_id for d in client.list_datasets(selected_project)]
        selected_dataset = st.sidebar.selectbox("Dataset GA4", datasets)
        
        st.sidebar.success(f"✅ Proyecto: {selected_project}, Dataset: {selected_dataset}")
    except Exception as e:
        st.error(f"❌ Error cargando proyectos: {e}")
        return

    # Tabs principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🍪 Cookies y Privacidad", "🛒 Ecommerce", "📈 Adquisición", 
        "🎯 Eventos", "👥 Usuarios", "🕒 Sesiones"
    ])
    
    with tab1:
        st.header("Análisis de Cookies")
        show_cookies_tab(client, selected_project, selected_dataset, start_date, end_date)
    
    with tab2:
        st.header("Análisis de Ecommerce")
        show_ecommerce_tab(client, selected_project, selected_dataset, start_date, end_date)
    
    with tab3:
        st.info("🔧 Sección en desarrollo. Próximamente: Adquisición")
    
    with tab4:
        st.info("🔧 Sección en desarrollo. Próximamente: Eventos")
    
    with tab5:
        st.info("🔧 Sección en desarrollo. Próximamente: Usuarios")
    
    with tab6:
        st.info("🔧 Sección en desarrollo. Próximamente: Sesiones")

if __name__ == "__main__":
    main()
