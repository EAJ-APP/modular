import streamlit as st
from database.queries.events_queries import (
    generar_query_eventos_flatten,
    generar_query_eventos_resumen,
    generar_query_eventos_por_fecha,
    generar_query_parametros_eventos,
    generar_query_metricas_diarias
)
from visualization.events_visualizations import (
    mostrar_eventos_flatten,
    mostrar_eventos_resumen,
    mostrar_eventos_por_fecha,
    mostrar_parametros_evento,
    mostrar_metricas_diarias
)
from database.connection import run_query

def show_events_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Eventos con análisis completo"""
    
    # Inicializar session_state para mantener datos y estado de expanders
    if 'events_resumen_data' not in st.session_state:
        st.session_state.events_resumen_data = None
    if 'events_resumen_show' not in st.session_state:
        st.session_state.events_resumen_show = False
    
    if 'events_fecha_data' not in st.session_state:
        st.session_state.events_fecha_data = None
    if 'events_fecha_show' not in st.session_state:
        st.session_state.events_fecha_show = False
    
    if 'events_flatten_data' not in st.session_state:
        st.session_state.events_flatten_data = None
    if 'events_flatten_show' not in st.session_state:
        st.session_state.events_flatten_show = False
    
    if 'events_params_data' not in st.session_state:
        st.session_state.events_params_data = None
    if 'events_params_show' not in st.session_state:
        st.session_state.events_params_show = False
    if 'events_params_name' not in st.session_state:
        st.session_state.events_params_name = ""
    
    if 'events_metricas_data' not in st.session_state:
        st.session_state.events_metricas_data = None
    if 'events_metricas_show' not in st.session_state:
        st.session_state.events_metricas_show = False
    
    # Sección 1: Métricas Diarias (NUEVA - la pongo primera porque es muy útil)
    with st.expander("📊 Métricas Diarias de Rendimiento", expanded=st.session_state.events_metricas_show):
        st.info("Dashboard completo con métricas diarias: sesiones, usuarios, engagement, conversiones")
        
        if st.button("Analizar Métricas Diarias", key="btn_metricas_diarias"):
            with st.spinner("Calculando métricas diarias..."):
                query = generar_query_metricas_diarias(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.events_metricas_data = df
                st.session_state.events_metricas_show = True
        
        # Mostrar resultados si existen
        if st.session_state.events_metricas_show and st.session_state.events_metricas_data is not None:
            mostrar_metricas_diarias(st.session_state.events_metricas_data)
    
    # Sección 2: Resumen de Eventos
    with st.expander("📊 Resumen de Eventos", expanded=st.session_state.events_resumen_show):
        st.info("Vista general de todos los tipos de eventos registrados")
        
        if st.button("Analizar Eventos", key="btn_eventos_resumen"):
            with st.spinner("Analizando eventos..."):
                query = generar_query_eventos_resumen(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.events_resumen_data = df
                st.session_state.events_resumen_show = True
        
        # Mostrar resultados si existen
        if st.session_state.events_resumen_show and st.session_state.events_resumen_data is not None:
            mostrar_eventos_resumen(st.session_state.events_resumen_data)
    
    # Sección 3: Evolución Temporal
    with st.expander("📅 Evolución Temporal de Eventos", expanded=st.session_state.events_fecha_show):
        st.info("Análisis de la evolución de eventos a lo largo del tiempo")
        
        if st.button("Analizar Evolución", key="btn_eventos_fecha"):
            with st.spinner("Calculando evolución temporal..."):
                query = generar_query_eventos_por_fecha(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.events_fecha_data = df
                st.session_state.events_fecha_show = True
        
        # Mostrar resultados si existen
        if st.session_state.events_fecha_show and st.session_state.events_fecha_data is not None:
            mostrar_eventos_por_fecha(st.session_state.events_fecha_data)
    
    # Sección 4: Datos Completos Flattenizados
    with st.expander("🔍 Explorador de Datos Completo (Flattenizado)", expanded=st.session_state.events_flatten_show):
        st.warning("⚠️ Esta consulta puede tardar varios segundos. Limitada a 1000 registros.")
        st.info("Acceso completo a todos los campos de eventos, parámetros, propiedades de usuario e items")
        
        if st.button("Cargar Datos Completos", key="btn_eventos_flatten"):
            with st.spinner("Cargando datos completos (esto puede tardar)..."):
                query = generar_query_eventos_flatten(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.events_flatten_data = df
                st.session_state.events_flatten_show = True
        
        # Mostrar resultados si existen
        if st.session_state.events_flatten_show and st.session_state.events_flatten_data is not None:
            mostrar_eventos_flatten(st.session_state.events_flatten_data)
    
    # Sección 5: Parámetros de Evento Específico
    with st.expander("🎯 Análisis de Parámetros por Evento", expanded=st.session_state.events_params_show):
        st.info("Analiza los parámetros de un evento específico")
        
        # Input para nombre del evento
        evento_especifico = st.text_input(
            "Nombre del evento a analizar:",
            placeholder="Ej: page_view, purchase, add_to_cart",
            key="evento_especifico_input",
            value=st.session_state.events_params_name
        )
        
        if st.button("Analizar Parámetros", key="btn_parametros_evento"):
            if evento_especifico:
                with st.spinner(f"Analizando parámetros de '{evento_especifico}'..."):
                    query = generar_query_parametros_eventos(
                        project, dataset, start_date, end_date, evento_especifico
                    )
                    df = run_query(client, query)
                    st.session_state.events_params_data = df
                    st.session_state.events_params_name = evento_especifico
                    st.session_state.events_params_show = True
            else:
                st.error("⚠️ Por favor, introduce el nombre de un evento")
        
        # Mostrar resultados si existen
        if st.session_state.events_params_show and st.session_state.events_params_data is not None:
            mostrar_parametros_evento(
                st.session_state.events_params_data, 
                st.session_state.events_params_name
            )
