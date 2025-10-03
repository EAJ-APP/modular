import streamlit as st
from database.queries import (
    generar_query_consentimiento_basico,
    generar_query_consentimiento_por_dispositivo,
    generar_query_consentimiento_real,
    generar_query_evolucion_temporal_consentimiento,
    generar_query_consentimiento_por_geografia,
    generar_query_consentimiento_por_fuente_trafico
)
from visualization.cookies_visualizations import (
    mostrar_consentimiento_basico,
    mostrar_consentimiento_por_dispositivo,
    mostrar_consentimiento_real,
    mostrar_evolucion_temporal_consentimiento,
    mostrar_consentimiento_por_geografia,
    mostrar_consentimiento_por_fuente_trafico
)
from database.connection import run_query

def show_cookies_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Cookies con análisis de privacidad y consentimientos"""
    
    # Inicializar session_state para cada sección
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
    
    # NUEVOS - Session state para las 3 nuevas consultas
    if 'cookies_evolucion_data' not in st.session_state:
        st.session_state.cookies_evolucion_data = None
    if 'cookies_evolucion_show' not in st.session_state:
        st.session_state.cookies_evolucion_show = False
    
    if 'cookies_geografia_data' not in st.session_state:
        st.session_state.cookies_geografia_data = None
    if 'cookies_geografia_show' not in st.session_state:
        st.session_state.cookies_geografia_show = False
    
    if 'cookies_trafico_data' not in st.session_state:
        st.session_state.cookies_trafico_data = None
    if 'cookies_trafico_show' not in st.session_state:
        st.session_state.cookies_trafico_show = False
    
    # ==========================================
    # SECCIÓN 1: Evolución Temporal (NUEVO)
    # ==========================================
    with st.expander("📈 Evolución Temporal del Consentimiento", 
                     expanded=st.session_state.cookies_evolucion_show):
        st.info("""
        **Análisis de tendencias día a día:**
        - Evolución de tasas de consentimiento Analytics y Ads
        - Detectar cambios tras actualizaciones del banner
        - Identificar patrones temporales y estacionales
        - Medir impacto de cambios en política de privacidad
        """)
        
        if st.button("Analizar Evolución Temporal", key="btn_evolucion_temporal"):
            with st.spinner("Analizando evolución temporal del consentimiento..."):
                query = generar_query_evolucion_temporal_consentimiento(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.cookies_evolucion_data = df
                st.session_state.cookies_evolucion_show = True
        
        # Mostrar resultados si existen
        if st.session_state.cookies_evolucion_show and st.session_state.cookies_evolucion_data is not None:
            mostrar_evolucion_temporal_consentimiento(st.session_state.cookies_evolucion_data)
    
    # ==========================================
    # SECCIÓN 2: Consentimiento Básico (ORIGINAL)
    # ==========================================
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
    
    # ==========================================
    # SECCIÓN 3: Consentimiento por Dispositivo (ORIGINAL)
    # ==========================================
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
    
    # ==========================================
    # SECCIÓN 4: Consentimiento por Geografía (NUEVO)
    # ==========================================
    with st.expander("🌍 Consentimiento por Geografía", 
                     expanded=st.session_state.cookies_geografia_show):
        st.info("""
        **Análisis geográfico de consentimientos:**
        - Tasas de consentimiento por país y ciudad
        - Detectar diferencias culturales en privacidad
        - Compliance regional (GDPR en EU, LGPD en Brasil)
        - Optimizar estrategia por región
        """)
        
        if st.button("Analizar por Geografía", key="btn_geografia"):
            with st.spinner("Analizando consentimiento por geografía..."):
                query = generar_query_consentimiento_por_geografia(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.cookies_geografia_data = df
                st.session_state.cookies_geografia_show = True
        
        # Mostrar resultados si existen
        if st.session_state.cookies_geografia_show and st.session_state.cookies_geografia_data is not None:
            mostrar_consentimiento_por_geografia(st.session_state.cookies_geografia_data)
    
    # ==========================================
    # SECCIÓN 5: Consentimiento por Fuente de Tráfico (NUEVO)
    # ==========================================
    with st.expander("📊 Consentimiento por Fuente de Tráfico", 
                     expanded=st.session_state.cookies_trafico_show):
        st.info("""
        **Análisis por canal de marketing:**
        - Tasas de consentimiento según utm_source, utm_medium, utm_campaign
        - Identificar campañas que generan usuarios "privacy-conscious"
        - Optimizar inversión en canales con mejor consentimiento
        - Channel grouping automático
        """)
        
        if st.button("Analizar por Fuente de Tráfico", key="btn_trafico"):
            with st.spinner("Analizando consentimiento por fuente de tráfico..."):
                query = generar_query_consentimiento_por_fuente_trafico(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st
                st.session_state.cookies_trafico_data = df
                st.session_state.cookies_trafico_show = True
        
        # Mostrar resultados si existen
        if st.session_state.cookies_trafico_show and st.session_state.cookies_trafico_data is not None:
            mostrar_consentimiento_por_fuente_trafico(st.session_state.cookies_trafico_data)
    
    # ==========================================
    # SECCIÓN 6: Porcentaje Real de Consentimiento (ORIGINAL)
    # ==========================================
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
    
    # Información adicional sobre GDPR y privacidad
    with st.expander("ℹ️ Información sobre GDPR y Compliance", expanded=False):
        st.markdown("""
        ### 📚 Guía de Cumplimiento GDPR
        
        **Requisitos básicos del GDPR para cookies:**
        
        1. **Consentimiento explícito**: Los usuarios deben dar consentimiento activo (no pre-marcado)
        2. **Granularidad**: Permitir aceptar/rechazar cookies por categorías
        3. **Fácil revocación**: Debe ser tan fácil retirar el consentimiento como darlo
        4. **Información clara**: Explicar qué cookies se usan y para qué
        5. **Sin penalización**: No penalizar a usuarios que rechazan cookies no esenciales
        
        **Mejores prácticas:**
        
        - ✅ Banner con opciones claras de "Aceptar" y "Rechazar"
        - ✅ Opción de "Configurar" para consentimiento granular
        - ✅ Link visible a política de privacidad
        - ✅ Gestión de consentimiento accesible desde cualquier página
        - ✅ Registrar el consentimiento con timestamp
        
        **Tasas de consentimiento típicas:**
        
        - 🇪🇺 **Europa (GDPR)**: 40-60% aceptación
        - 🇺🇸 **Norteamérica**: 60-80% aceptación (menos regulación)
        - 🌎 **LATAM**: 70-85% aceptación (regulación emergente)
        - 🌏 **Asia**: 50-70% aceptación (muy variable por país)
        
        **Señales de alerta:**
        
        - 🚨 Tasa de consentimiento < 30% → Revisar UX del banner
        - 🚨 Tasa de bounce > 70% tras banner → Banner demasiado intrusivo
        - 🚨 Diferencia Analytics vs Ads > 30% → Revisar configuración
        - 🚨 Caída brusca en consentimiento → Investigar causa inmediatamente
        
        **Recursos útiles:**
        
        - [GDPR Official Text](https://gdpr-info.eu/)
        - [Google Consent Mode](https://support.google.com/analytics/answer/9976101)
        - [IAB Transparency Framework](https://iabeurope.eu/transparency-consent-framework/)
        """)
