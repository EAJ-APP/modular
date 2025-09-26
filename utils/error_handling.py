import streamlit as st

def handle_bq_error(e, query=None):
    """Muestra errores de BigQuery de forma legible"""
    error_msg = f"""
    🚨 **Error en BigQuery**:
    ```python
    {str(e)}
    ```
    """
    if query:
        error_msg += f"\n**Consulta**:\n```sql\n{query}\n```"
    st.error(error_msg)
    st.stop()

def check_dependencies():
    """Verifica dependencias esenciales - Versión actualizada"""
    try:
        # Verificar las dependencias con versiones actualizadas
        import pandas
        import google.cloud.bigquery
        import plotly
        import db_dtypes
        import numpy
        import matplotlib
        import protobuf
        
        st.sidebar.success("✅ Todas las dependencias cargadas correctamente")
        
    except ImportError as e:
        st.error(f"❌ Error de dependencias: {str(e)}")
        st.info("Por favor, instala las dependencias: pip install -r requirements.txt")
        st.stop()
