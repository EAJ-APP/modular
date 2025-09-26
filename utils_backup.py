# utils.py (archivo temporal en raíz)
import warnings
import streamlit as st

def setup_environment():
    warnings.filterwarnings("ignore", category=FutureWarning)

def check_dependencies():
    try:
        import db_dtypes, pandas, google.cloud.bigquery, plotly
    except ImportError as e:
        st.error(f"❌ Error: {str(e)}")
        st.stop()

def handle_bq_error(e, query=None):
    error_msg = f"🚨 Error en BigQuery: {str(e)}"
    if query:
        error_msg += f"\nConsulta: {query}"
    st.error(error_msg)
    st.stop()
