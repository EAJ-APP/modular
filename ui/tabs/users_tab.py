import streamlit as st
from database.queries.users_queries import (
    generar_query_retencion_semanal,
    generar_query_clv_sesiones,
    generar_query_tiempo_primera_compra,
    generar_query_landing_page_attribution,
    generar_query_adquisicion_usuarios,
    generar_query_conversion_mensual
)
from visualization.users_visualizations import (
    mostrar_retencion_semanal,
    mostrar_clv_sesiones,
    mostrar_tiempo_primera_compra,
    mostrar_landing_page_attribution,
    mostrar_adquisicion_usuarios,
    mostrar_conversion_mensual
)
from database.connection import run_query

def show_users_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Usuarios con análisis avanzados"""
    
    # Inicializar session_state para cada sección
    if 'users_retention_data' not in st.session_state:
        st.session_state.users_retention_data = None
    if 'users_retention_show' not in st.session_state:
        st.session_state.users_retention_show = False
    
    if 'users_clv_data' not in st.session_state:
        st.session_state.users_clv_data = None
    if 'users_clv_show' not in st.session_state:
        st.session_state.users_clv_show = False
    
    if 'users_time_purchase_data' not in st.session_state:
        st.session_state.users_time_purchase_data = None
    if 'users_time_purchase_show' not in st.session_state:
        st.session_state.users_time_purchase_show = False
    
    if 'users_landing_data' not in st.session_state:
        st.session_state.users_landing_data = None
    if 'users_landing_show' not in st.session_state:
        st.session_state.users_landing_show = False
    
    if 'users_acquisition_data' not in st.session_state:
        st.session_state.users_acquisition_data = None
    if 'users_acquisition_show' not in st.session_state:
        st.session_state.users_acquisition_show = False
    
    if 'users_monthly_conv_data' not in st.session_state:
        st.session_state.users_monthly_conv_data = None
    if 'users_monthly_conv_show' not in st.session_state:
        st.session_state.users_monthly_conv_show = False
    
    # Sección 1: Retención Semanal
    with st.expander("📅 Retención Semanal de Usuarios", expanded=st.session_state.users_retention_show):
        st.info("""
        **Análisis de cohortes semanales:**
        - Trackea usuarios adquiridos cada semana (Semana 0)
        - Mide cuántos regresan en las semanas siguientes (1, 2, 3, 4)
        - Identifica patrones de retención y drop-off
        """)
        
        if st.button("Analizar Retención Semanal", key="btn_users_retention"):
            with st.spinner("Calculando retención semanal (esto puede tardar)..."):
                query = generar_query_retencion_semanal(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.users_retention_data = df
                st.session_state.users_retention_show = True
        
        # Mostrar resultados si existen
        if st.session_state.users_retention_show and st.session_state.users_retention_data is not None:
            mostrar_retencion_semanal(st.session_state.users_retention_data)
    
    # Sección 2: CLV y Sesiones
    with st.expander("💰 Customer Lifetime Value (CLV) y Sesiones", expanded=st.session_state.users_clv_show):
        st.info("""
        **Análisis de valor de usuario:**
        - Calcula el CLV de cada usuario
        - Correlaciona CLV con número de sesiones
        - Identifica usuarios de alto valor
        - Segmenta Buyers vs Non-Buyers
        """)
        
        if st.button("Analizar CLV y Sesiones", key="btn_users_clv"):
            with st.spinner("Calculando CLV y sesiones..."):
                query = generar_query_clv_sesiones(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.users_clv_data = df
                st.session_state.users_clv_show = True
        
        # Mostrar resultados si existen
        if st.session_state.users_clv_show and st.session_state.users_clv_data is not None:
            mostrar_clv_sesiones(st.session_state.users_clv_data)
    
    # Sección 3: Tiempo a Primera Compra
    with st.expander("⏱️ Tiempo desde Primera Visita hasta Compra", expanded=st.session_state.users_time_purchase_show):
        st.info("""
        **Análisis de velocidad de conversión:**
        - Mide días entre primera visita y primera compra
        - Agrupa por fuente de adquisición
        - Identifica canales de conversión rápida
        - Optimiza inversión en marketing
        """)
        
        if st.button("Analizar Tiempo a Compra", key="btn_users_time_purchase"):
            with st.spinner("Calculando tiempo a primera compra..."):
                query = generar_query_tiempo_primera_compra(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.users_time_purchase_data = df
                st.session_state.users_time_purchase_show = True
        
        # Mostrar resultados si existen
        if st.session_state.users_time_purchase_show and st.session_state.users_time_purchase_data is not None:
            mostrar_tiempo_primera_compra(st.session_state.users_time_purchase_data)
    
    # Sección 4: Landing Page Attribution
    with st.expander("🎯 Atribución por Primera Landing Page", expanded=st.session_state.users_landing_show):
        st.info("""
        **Análisis de primera landing page:**
        - Atribuye eventos clave a la primera página visitada
        - Métricas: views, add-to-cart, purchases, revenue
        - Identifica páginas de entrada más efectivas
        - Optimiza inversión en ads por landing page
        """)
        
        if st.button("Analizar Landing Pages", key="btn_users_landing"):
            with st.spinner("Calculando atribución por landing page..."):
                query = generar_query_landing_page_attribution(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.users_landing_data = df
                st.session_state.users_landing_show = True
        
        # Mostrar resultados si existen
        if st.session_state.users_landing_show and st.session_state.users_landing_data is not None:
            mostrar_landing_page_attribution(st.session_state.users_landing_data)
    
    # Sección 5: Adquisición de Usuarios
    with st.expander("📍 Adquisición de Usuarios por Fuente/Medio", expanded=st.session_state.users_acquisition_show):
        st.info("""
        **Análisis de canales de adquisición:**
        - Agrupa usuarios por fuente y medio
        - Channel grouping automático (Organic Search, Paid Social, etc.)
        - Métricas de performance por canal
        - Identifica mejores fuentes de usuarios
        """)
        
        if st.button("Analizar Adquisición", key="btn_users_acquisition"):
            with st.spinner("Calculando adquisición de usuarios..."):
                query = generar_query_adquisicion_usuarios(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.users_acquisition_data = df
                st.session_state.users_acquisition_show = True
        
        # Mostrar resultados si existen
        if st.session_state.users_acquisition_show and st.session_state.users_acquisition_data is not None:
            mostrar_adquisicion_usuarios(st.session_state.users_acquisition_data)
    
    # Sección 6: Conversión Mensual
    with st.expander("📅 Tasa de Conversión Mensual", expanded=st.session_state.users_monthly_conv_show):
        st.info("""
        **Análisis de conversión temporal:**
        - Tasa de conversión mes a mes
        - Tendencias estacionales
        - Revenue per user mensual
        - Identifica mejores y peores meses
        """)
        
        if st.button("Analizar Conversión Mensual", key="btn_users_monthly_conv"):
            with st.spinner("Calculando conversión mensual..."):
                query = generar_query_conversion_mensual(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.users_monthly_conv_data = df
                st.session_state.users_monthly_conv_show = True
        
        # Mostrar resultados si existen
        if st.session_state.users_monthly_conv_show and st.session_state.users_monthly_conv_data is not None:
            mostrar_conversion_mensual(st.session_state.users_monthly_conv_data)
