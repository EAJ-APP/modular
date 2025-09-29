import streamlit as st
from database.queries.sessions_queries import (
    generar_query_low_converting_sessions,
    generar_query_session_path_analysis,
    generar_query_hourly_sessions_performance,
    generar_query_exit_pages
)
from visualization.sessions_visualizations import (
    mostrar_low_converting_sessions,
    mostrar_session_path_analysis,
    mostrar_hourly_sessions_performance,
    mostrar_exit_pages_analysis
)
from database.connection import run_query

def show_sessions_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Sesiones con análisis avanzados"""
    
    # Inicializar session_state para cada sección
    if 'sessions_low_converting_data' not in st.session_state:
        st.session_state.sessions_low_converting_data = None
    if 'sessions_low_converting_show' not in st.session_state:
        st.session_state.sessions_low_converting_show = False
    
    if 'sessions_path_data' not in st.session_state:
        st.session_state.sessions_path_data = None
    if 'sessions_path_show' not in st.session_state:
        st.session_state.sessions_path_show = False
    
    if 'sessions_hourly_data' not in st.session_state:
        st.session_state.sessions_hourly_data = None
    if 'sessions_hourly_show' not in st.session_state:
        st.session_state.sessions_hourly_show = False
    
    if 'sessions_exit_data' not in st.session_state:
        st.session_state.sessions_exit_data = None
    if 'sessions_exit_show' not in st.session_state:
        st.session_state.sessions_exit_show = False
    
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
    
    # Sección 2: Session Path Analysis
    with st.expander("🗺️ Análisis de Rutas de Navegación", expanded=st.session_state.sessions_path_show):
        st.info("""
        **Analiza los caminos de navegación de los usuarios:**
        - Páginas de entrada más comunes (landing pages)
        - Páginas de salida más frecuentes (exit pages)
        - Flujos de navegación: página anterior → actual → siguiente
        - Patrones de comportamiento en la navegación
        - Identificación de rutas críticas para optimización
        - Diagrama de flujo visual (Sankey)
        """)
        
        if st.button("Analizar Rutas de Navegación", key="btn_sessions_path"):
            with st.spinner("Analizando rutas de navegación (esto puede tardar)..."):
                query = generar_query_session_path_analysis(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.sessions_path_data = df
                st.session_state.sessions_path_show = True
        
        # Mostrar resultados si existen
        if st.session_state.sessions_path_show and st.session_state.sessions_path_data is not None:
            mostrar_session_path_analysis(st.session_state.sessions_path_data)
    
    # Sección 3: Hourly Sessions Performance
    with st.expander("⏰ Rendimiento de Sesiones por Hora", expanded=st.session_state.sessions_hourly_show):
        st.info("""
        **Analiza el rendimiento de sesiones por hora del día:**
        - Distribución de sesiones por hora y día de la semana
        - Heatmap de actividad temporal
        - Métricas de ecommerce por hora: view_item, add_to_cart, purchases
        - Tasas de conversión por franja horaria
        - Identificación de horas pico y horas valle
        - Recomendaciones para optimización de campañas
        """)
        
        if st.button("Analizar Rendimiento Horario", key="btn_sessions_hourly"):
            with st.spinner("Analizando rendimiento por hora (esto puede tardar)..."):
                query = generar_query_hourly_sessions_performance(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.sessions_hourly_data = df
                st.session_state.sessions_hourly_show = True
        
        # Mostrar resultados si existen
        if st.session_state.sessions_hourly_show and st.session_state.sessions_hourly_data is not None:
            mostrar_hourly_sessions_performance(st.session_state.sessions_hourly_data)
    
    # Sección 4: Exit Pages Analysis
    with st.expander("🚪 Análisis de Páginas de Salida", expanded=st.session_state.sessions_exit_show):
        st.info("""
        **Identifica las páginas donde los usuarios abandonan:**
        - Top páginas con mayor tasa de abandono
        - Porcentaje de salidas por página
        - Análisis de concentración (Pareto)
        - Patrones de URL en páginas de salida
        - Distribución por secciones del sitio
        - Páginas críticas que requieren optimización
        - Recomendaciones accionables para reducir abandonos
        """)
        
        if st.button("Analizar Páginas de Salida", key="btn_sessions_exit"):
            with st.spinner("Analizando páginas de salida..."):
                query = generar_query_exit_pages(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.sessions_exit_data = df
                st.session_state.sessions_exit_show = True
        
        # Mostrar resultados si existen
        if st.session_state.sessions_exit_show and st.session_state.sessions_exit_data is not None:
            mostrar_exit_pages_analysis(st.session_state.sessions_exit_data)
    
    # Mensaje de completado
    st.success("✅ **Todas las consultas de Sesiones están disponibles!**")

                st.session_state.sessions_hourly_data = df
                st.session_state.sessions_hourly_show = True
        
        # Mostrar resultados si existen
        if st.session_state.sessions_hourly_show and st.session_state.sessions_hourly_data is not None:
            mostrar_hourly_sessions_performance(st.session_state.sessions_hourly_data)
    
    # Placeholder para próximas consultas
    st.info("🚧 **Próximamente:** Session Behavior by Device, Exit Pages Analysis")
