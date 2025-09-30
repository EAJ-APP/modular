import streamlit as st
from database.queries import (
    generar_query_consentimiento_basico,
    generar_query_consentimiento_por_dispositivo,
    generar_query_consentimiento_real
)
from visualization.cookies_visualizations import (
    mostrar_consentimiento_basico,
    mostrar_consentimiento_por_dispositivo,
    mostrar_consentimiento_real
)
from database.connection import run_query

def show_cookies_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Cookies con análisis de privacidad y consentimientos"""
    
    # Inicializar session_state para mantener datos y estado de expanders
    if 'cookies_basico_data' not in st.session_state:
        st.session_state.cookies_basico_data = None
    if 'cookies_basico_show' not in st.session_state:
        st.session_state.cookies_basico_show = False
    
    if 'cookies_dispositivo_data' not in st.session_state:
        st.session_state.cookies_dispositivo_data = None
    if 'cookies_dispositivo_show' not in st.session_state:
        st.session_state.cookies_dispositivo_show = False
    
    if 'cookies_real_data' not in st.session_state:
        st.session_state.cookies_real_data = None
    if 'cookies_real_show' not in st.session_state:
        st.session_state.cookies_real_show = False
    
    # Sección 1: Consentimiento Básico
    with st.expander("🛡️ Consentimiento Básico", expanded=st.session_state.cookies_basico_show):
        st.info("""
        **Análisis de consentimiento de cookies:**
        - Distribución de `analytics_storage` y `ads_storage`
        - Métricas por eventos, usuarios y sesiones
        - Cumplimiento GDPR básico
        """)
        
        if st.button("Ejecutar Análisis Básico", key="btn_consent_basic"):
            with st.spinner("Calculando consentimientos..."):
                query = generar_query_consentimiento_basico(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.cookies_basico_data = df
                st.session_state.cookies_basico_show = True
        
        # Mostrar resultados si existen
        if st.session_state.cookies_basico_show and st.session_state.cookies_basico_data is not None:
            mostrar_consentimiento_basico(st.session_state.cookies_basico_data)
    
    # Sección 2: Consentimiento por Dispositivo
    with st.expander("📱 Consentimiento por Dispositivo", expanded=st.session_state.cookies_dispositivo_show):
        st.info("""
        **Análisis cross-device de consentimientos:**
        - Comparativa entre Desktop, Mobile y Tablet
        - Tasas de consentimiento por tipo de dispositivo
        - Análisis separado de Analytics y Ads storage
        """)
        
        if st.button("Ejecutar Análisis por Dispositivo", key="btn_consent_device"):
            with st.spinner("Analizando dispositivos..."):
                query = generar_query_consentimiento_por_dispositivo(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.cookies_dispositivo_data = df
                st.session_state.cookies_dispositivo_show = True
        
        # Mostrar resultados si existen
        if st.session_state.cookies_dispositivo_show and st.session_state.cookies_dispositivo_data is not None:
            mostrar_consentimiento_por_dispositivo(st.session_state.cookies_dispositivo_data)
    
    # Sección 3: Porcentaje Real de Consentimiento
    with st.expander("🔍 Porcentaje Real de Consentimiento", expanded=st.session_state.cookies_real_show):
        st.info("""
        **Análisis preciso del consentimiento:**
        - Tasa real de eventos con consentimiento
        - Clasificación: Aceptado, Denegado, No Definido
        - Porcentaje de eventos sin consentimiento explícito
        - Vista global sobre todos los eventos del período
        """)
        
        if st.button("Calcular Consentimiento Real", key="btn_consent_real"):
            with st.spinner("Analizando todos los eventos..."):
                query = generar_query_consentimiento_real(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.cookies_real_data = df
                st.session_state.cookies_real_show = True
        
        # Mostrar resultados si existen
        if st.session_state.cookies_real_show and st.session_state.cookies_real_data is not None:
            mostrar_consentimiento_real(st.session_state.cookies_real_data)
    
    # Mensaje de completado
    st.success("✅ **Todas las consultas de Cookies y Privacidad están disponibles!**")
