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
    """Verifica dependencias esenciales - Versión simplificada"""
    try:
        # Solo verificar las esenciales para que funcione
        import pandas
        import google.cloud.bigquery
        import plotly
        
        # Opcional: verificar protobuf pero no fallar si no está
        try:
            import protobuf
        except ImportError:
            st.sidebar.warning("⚠️ protobuf no instalado (opcional)")
            
        st.sidebar.success("✅ Dependencias principales OK")
        
    except ImportError as e:
        st.error(f"❌ Error de dependencias: {str(e)}")
        st.info("Ejecuta: pip install -r requirements.txt")
        st.stop()
