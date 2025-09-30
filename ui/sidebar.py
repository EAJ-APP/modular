import streamlit as st
import pandas as pd
from config.settings import Settings
from database.connection import get_bq_client
from utils.error_handling import handle_bq_error

def render_sidebar():
    """Renderiza la barra lateral con configuración"""
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
        start_date = st.date_input("Fecha inicio", value=Settings.DEFAULT_START_DATE, key="global_start_date")
        end_date = st.date_input("Fecha fin", value=Settings.DEFAULT_END_DATE, key="global_end_date")
    
    return development_mode, start_date, end_date

def get_project_dataset_selection(client):
    """Obtiene la selección de proyecto y dataset - Versión silenciosa"""
    try:
        projects = [p.project_id for p in client.list_projects()]
        selected_project = st.sidebar.selectbox("Proyecto", projects)
        datasets = [d.dataset_id for d in client.list_datasets(selected_project)]
        selected_dataset = st.sidebar.selectbox("Dataset GA4", datasets)
        
        # REMOVED: st.sidebar.success(f"✅ {selected_project}.{selected_dataset}")
        
        return selected_project, selected_dataset
    except Exception as e:
        handle_bq_error(e)
