import streamlit as st
from database.queries import (
    generar_query_canales_trafico,
    generar_query_atribucion_marketing,
    generar_query_atribucion_completa
)
from visualization.acquisition_visualizations import (
    mostrar_canales_trafico,
    mostrar_atribucion_marketing,
    mostrar_atribucion_multimodelo,
    mostrar_atribucion_completa
)
from database.connection import run_query

def show_acquisition_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Adquisición con análisis de tráfico"""
    
    # Inicializar session_state para mantener datos y estado
    if 'attribution_data' not in st.session_state:
        st.session_state.attribution_data = None
    if 'show_attribution_results' not in st.session_state:
        st.session_state.show_attribution_results = False
    
    # Sección 1: Canales de Tráfico
    with st.expander("🌐 Análisis de Canales de Tráfico", expanded=False):
        st.info("Análisis de canales de marketing agrupados automáticamente")
        
        if st.button("Analizar Canales de Tráfico", key="btn_canales"):
            with st.spinner("Analizando distribución de canales..."):
                query = generar_query_canales_trafico(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_canales_trafico(df)
    
    # Sección 2: Atribución Básica
    with st.expander("🎯 Atribución de Marketing", expanded=False):
        st.info("Análisis de atribución por parámetros UTM")
        
        if st.button("Análisis Básico UTM", key="btn_basica"):
            with st.spinner("Calculando atribución básica..."):
                query = generar_query_atribucion_marketing(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_atribucion_marketing(df)
    
    # Sección 3: Atribución Multi-Modelo (3 modelos)
    with st.expander("🔄 Atribución Multi-Modelo", expanded=False):
        st.info("Análisis con 3 modelos de atribución")
        
        if st.button("Análisis 3 Modelos", key="btn_3modelos"):
            with st.spinner("Calculando atribución multi-modelo..."):
                query = generar_query_atribucion_marketing(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_atribucion_multimodelo(df)
    
    # Sección 4: Atribución Completa (7 modelos)
    with st.expander("🚀 Atribución Completa (7 Modelos)", expanded=st.session_state.show_attribution_results):
        st.info("""
        **Análisis completo con 7 modelos de atribución:**
        - Last Click, First Click, Linear
        - Time Decay, Position Based  
        - Last Non-Direct, Data Driven
        """)
        
        if st.button("Análisis 7 Modelos", key="btn_7modelos"):
            with st.spinner("Calculando atribución completa (puede tardar)..."):
                query = generar_query_atribucion_completa(project, dataset, start_date, end_date)
                df = run_query(client, query)
                
                # Guardar datos en session_state
                st.session_state.attribution_data = df
                st.session_state.show_attribution_results = True
        
        # Mostrar resultados si existen en session_state
        if st.session_state.show_attribution_results and st.session_state.attribution_data is not None:
            mostrar_atribucion_completa(st.session_state.attribution_data)
