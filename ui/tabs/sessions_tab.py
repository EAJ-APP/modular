import streamlit as st
from database.queries.sessions_queries import (
    generar_query_low_converting_sessions
)
from visualization.sessions_visualizations import (
    mostrar_low_converting_sessions
)
from database.connection import run_query

def show_sessions_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Sesiones con análisis avanzados"""
    
    # Inicializar session_state para cada sección
    if 'sessions_low_converting_data' not in st.session_state:
        st.session_state.sessions_low_converting_data = None
    if 'sessions_low_converting_show' not in st.session_state:
        st.session_state.sessions_low_converting_show = False
    
    # Sección 1: Low Converting Sessions Analysis
    with st.expander("🔍 Análisis de Sesiones con Baja Conversión", expanded=st.session_state.sessions_low_converting_show):
        st.info("""
        **Analiza sesiones que NO convirtieron para identificar:**
        - Fuentes de tráfico con alta tasa de no conversión
        - Dispositivos y navegadores problemáticos
        - Landing pages que no generan conversión
        - Patrones de comportamiento en sesiones sin compra
        - Oportunidades de optimización del funnel
        """)
        
        if st.button("Analizar Sesiones Sin Conversión", key="btn_sessions_low_converting"):
            with st.spinner("Analizando sesiones sin conversión (esto puede tardar)..."):
                query = generar_query_low_converting_sessions(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.sessions_low_converting_data = df
                st.session_state.sessions_low_converting_show = True
        
        # Mostrar resultados si existen
        if st.session_state.sessions_low_converting_show and st.session_state.sessions_low_converting_data is not None:
            mostrar_low_converting_sessions(st.session_state.sessions_low_converting_data)
    
    # Placeholder para próximas consultas
    st.info("🚧 **Próximamente:** Session Path Analysis, Session Behavior by Device, Hourly Sessions Performance, Exit Pages Analysis")
