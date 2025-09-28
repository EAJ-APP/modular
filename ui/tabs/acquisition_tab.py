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
# Añade esta importación para el debug
from database.queries.debug_queries import debug_query_modelos

def show_acquisition_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Adquisición con análisis de tráfico"""
    
    # SECCIÓN DEBUG - Para diagnosticar problemas
# En la sección DEBUG, añade esto:
with st.expander("🔧 DEBUG - Diagnóstico de Consultas", expanded=False):
    st.warning("Esta sección es solo para debugging - eliminar en producción")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Probar Conexión Básica", key="debug_basic"):
            with st.spinner("Probando conexión..."):
                query = debug_query_modelos(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.success("✅ Conexión exitosa")
                st.dataframe(df)
    
    with col2:
        if st.button("Debug 7 Modelos", key="debug_7"):
            with st.spinner("Verificando modelos..."):
                query = debug_query_7_modelos(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.dataframe(df)
    
    with col3:
        if st.button("Ver Consulta 7 Modelos", key="debug_sql"):
            query = generar_query_atribucion_completa(project, dataset, start_date, end_date)
            st.code(query, language="sql")
    
    # ... el resto de tu código actual ...
    
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
    
    # Sección 4: Atribución Completa (7 modelos) - CORREGIDO
    with st.expander("🚀 Atribución Completa (7 Modelos)", expanded=False):
        st.info("""
        **Análisis completo con 7 modelos de atribución:**
        - Last Click, First Click, Linear
        - Time Decay, Position Based  
        - Last Non-Direct, Data Driven
        """)
        
        if st.button("Análisis 7 Modelos", key="btn_7modelos"):
            with st.spinner("Calculando atribución completa (puede tardar)..."):
                # CORRECCIÓN CRÍTICA: Usar la consulta correcta para 7 modelos
                query = generar_query_atribucion_completa(project, dataset, start_date, end_date)
                df = run_query(client, query)
                
                # DEBUG: Mostrar información sobre los datos recibidos
                st.write(f"📊 **Debug Info:** {len(df)} filas, {df['attribution_model'].nunique()} modelos únicos")
                st.write(f"🔍 **Modelos encontrados:** {', '.join(df['attribution_model'].unique())}")
                
                mostrar_atribucion_completa(df)
