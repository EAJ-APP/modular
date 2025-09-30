import streamlit as st
import pandas as pd
from config.settings import Settings
from database.connection import get_bq_client
from utils.error_handling import handle_bq_error

def render_sidebar():
    """Renderiza la barra lateral con configuración - Versión profesional"""
    with st.sidebar:
        # Logo en sidebar
        try:
            st.image("assets/logo.png", width=120)
        except:
            st.markdown("### 🛡️ BigQuery Shield")
        
        st.divider()
        
        # Configuración de credenciales (colapsado por defecto)
        with st.expander("🔐 Configuración de Acceso", expanded=False):
            development_mode = st.toggle("Modo desarrollo (usar JSON local)")
            
            if development_mode:
                creds_file = st.file_uploader("Sube credenciales JSON", type=["json"])
                if creds_file:
                    with open("temp_creds.json", "wb") as f:
                        f.write(creds_file.getvalue())
                    st.session_state.creds = "temp_creds.json"
                    st.success("✓ Credenciales cargadas")
            elif "gcp_service_account" not in st.secrets:
                st.error("⚠️ Configura los Secrets en Streamlit Cloud")
                st.stop()
        
        # Rango de fechas más visible
        st.markdown("### 📅 Período de Análisis")
        start_date = st.date_input(
            "Fecha inicio", 
            value=Settings.DEFAULT_START_DATE, 
            key="global_start_date",
            help="Selecciona la fecha de inicio del análisis"
        )
        end_date = st.date_input(
            "Fecha fin", 
            value=Settings.DEFAULT_END_DATE, 
            key="global_end_date",
            help="Selecciona la fecha de fin del análisis"
        )
        
        # Mostrar duración del período
        days_diff = (end_date - start_date).days
        if days_diff > 0:
            st.info(f"📊 Analizando **{days_diff} días** de datos")
        elif days_diff == 0:
            st.warning("⚠️ Selecciona un rango de fechas válido")
        else:
            st.error("❌ La fecha de inicio debe ser anterior a la fecha de fin")
        
        st.divider()
        
        # Links útiles
        with st.expander("🔗 Enlaces Útiles", expanded=False):
            st.markdown("""
            - [📖 Documentación GA4](https://support.google.com/analytics)
            - [💡 Guía BigQuery](https://cloud.google.com/bigquery/docs)
            - [🎯 FLAT 101 Digital](https://flat101.es)
            """)
        
        # Información de versión al final
        st.caption("---")
        st.caption("**BigQuery Shield v1.0**")
        st.caption("Powered by FLAT 101")
    
    return development_mode, start_date, end_date

def get_project_dataset_selection(client):
    """Obtiene la selección de proyecto y dataset - Versión mejorada"""
    try:
        st.sidebar.markdown("### 🗄️ Fuente de Datos")
        
        projects = [p.project_id for p in client.list_projects()]
        selected_project = st.sidebar.selectbox(
            "Proyecto GCP", 
            projects,
            help="Selecciona el proyecto de Google Cloud Platform"
        )
        
        datasets = [d.dataset_id for d in client.list_datasets(selected_project)]
        selected_dataset = st.sidebar.selectbox(
            "Dataset GA4", 
            datasets,
            help="Selecciona el dataset de Google Analytics 4"
        )
        
        # Indicador visual de conexión exitosa
        st.sidebar.success("✓ Conectado correctamente")
        
        return selected_project, selected_dataset
    except Exception as e:
        handle_bq_error(e)
