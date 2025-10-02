from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st
from utils.error_handling import handle_bq_error
from utils.bq_monitoring import get_query_statistics, bytes_to_readable

def get_bq_client(credentials_path=None):
    """
    FUNCIÓN DEPRECADA - Mantener por compatibilidad
    Usar SessionManager.get_bigquery_client() en su lugar
    """
    # Esta función ya no se usa en el flujo principal
    # Se mantiene por si algún código legacy la llama
    try:
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            return bigquery.Client(credentials=credentials)
        else:
            # Intentar obtener de secrets (compatibilidad)
            creds_dict = dict(st.secrets["gcp_service_account"])
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            return bigquery.Client(credentials=credentials, project=creds_dict.get("project_id"))
    except Exception as e:
        handle_bq_error(e)

def run_query(client, query, timeout=30, show_stats=False):
    """
    Ejecuta consulta en BigQuery - Con monitorización de consumo
    
    Args:
        client: Cliente de BigQuery (obtenido de SessionManager)
        query: Consulta SQL a ejecutar
        timeout: Timeout en segundos (default: 30)
        show_stats: Si True, muestra estadísticas de consumo (default: False)
        
    Returns:
        DataFrame con los resultados
    """
    from concurrent.futures import TimeoutError
    
    try:
        # Ejecutar consulta
        query_job = client.query(query)
        
        # Obtener resultados
        result_df = query_job.result(timeout=timeout).to_dataframe()
        
        # Obtener estadísticas de la consulta
        stats = get_query_statistics(query_job)
        
        # Guardar estadísticas en session_state para historial
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        st.session_state.query_history.append({
            'timestamp': query_job.created,
            'bytes_processed': stats['total_bytes_processed'],
            'bytes_readable': stats['total_bytes_readable'],
            'cache_hit': stats['cache_hit'],
            'cost_usd': stats['estimated_cost_usd']
        })
        
        # Mantener solo las últimas 50 consultas
        if len(st.session_state.query_history) > 50:
            st.session_state.query_history = st.session_state.query_history[-50:]
        
        # Mostrar estadísticas si se solicita
        if show_stats:
            if stats['cache_hit']:
                st.success(f"✅ Consulta servida desde caché (0 bytes procesados)")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Datos procesados", stats['total_bytes_readable'])
                with col2:
                    st.metric("Datos facturados", stats['total_billed_readable'])
                with col3:
                    cost_display = f"${stats['estimated_cost_usd']:.6f}"
                    st.metric("Costo estimado", cost_display)
        
        return result_df
        
    except TimeoutError:
        handle_bq_error("⏳ Timeout: La consulta tardó demasiado. Filtra más datos.", query)
    except Exception as e:
        handle_bq_error(e, query)

def run_query_with_estimate(client, query, timeout=30):
    """
    Ejecuta consulta mostrando PRIMERO la estimación de consumo
    
    Args:
        client: Cliente de BigQuery (obtenido de SessionManager)
        query: Consulta SQL a ejecutar
        timeout: Timeout en segundos (default: 30)
        
    Returns:
        DataFrame con los resultados
    """
    from utils.bq_monitoring import estimate_query_cost
    
    # Primero, estimar el costo
    estimate = estimate_query_cost(client, query)
    
    if estimate['success']:
        # Mostrar estimación en un expander
        with st.expander("📊 Estimación de Consumo", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Datos a procesar", estimate['total_bytes_readable'])
            with col2:
                st.metric("GB estimados", f"{estimate['total_gb']} GB")
            with col3:
                st.metric("Costo estimado", f"${estimate['estimated_cost_usd']:.6f}")
            
            # Alerta si es una consulta grande
            if estimate['total_gb'] > 10:
                st.warning(f"⚠️ Esta consulta procesará {estimate['total_gb']:.2f} GB de datos")
            elif estimate['total_gb'] > 50:
                st.error(f"🚨 Consulta muy grande: {estimate['total_gb']:.2f} GB. Considera filtrar más datos.")
    
    # Ejecutar la consulta con estadísticas
    return run_query(client, query, timeout=timeout, show_stats=True)
