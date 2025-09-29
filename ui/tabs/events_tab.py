import streamlit as st
from database.queries.events_queries import (
    generar_query_eventos_flatten,
    generar_query_eventos_resumen,
    generar_query_eventos_por_fecha,
    generar_query_parametros_eventos
)
from visualization.events_visualizations import (
    mostrar_eventos_flatten,
    mostrar_eventos_resumen,
    mostrar_eventos_por_fecha,
    mostrar_parametros_evento
)
from database.connection import run_query

def show_events_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Eventos con análisis completo"""
    
    # Sección 1: Resumen de Eventos
    with st.expander("📊 Resumen de Eventos", expanded=True):
        st.info("Vista general de todos los tipos de eventos registrados")
        
        if st.button("Analizar Eventos", key="btn_eventos_resumen"):
            with st.spinner("Analizando eventos..."):
                query = generar_query_eventos_resumen(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_eventos_resumen(df)
    
    # Sección 2: Evolución Temporal
    with st.expander("📅 Evolución Temporal de Eventos", expanded=False):
        st.info("Análisis de la evolución de eventos a lo largo del tiempo")
        
        if st.button("Analizar Evolución", key="btn_eventos_fecha"):
            with st.spinner("Calculando evolución temporal..."):
                query = generar_query_eventos_por_fecha(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_eventos_por_fecha(df)
    
    # Sección 3: Datos Completos Flattenizados
    with st.expander("🔍 Explorador de Datos Completo (Flattenizado)", expanded=False):
        st.warning("⚠️ Esta consulta puede tardar varios segundos. Limitada a 1000 registros.")
        st.info("Acceso completo a todos los campos de eventos, parámetros, propiedades de usuario e items")
        
        if st.button("Cargar Datos Completos", key="btn_eventos_flatten"):
            with st.spinner("Cargando datos completos (esto puede tardar)..."):
                query = generar_query_eventos_flatten(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_eventos_flatten(df)
    
    # Sección 4: Parámetros de Evento Específico
    with st.expander("🎯 Análisis de Parámetros por Evento", expanded=False):
        st.info("Analiza los parámetros de un evento específico")
        
        # Input para nombre del evento
        evento_especifico = st.text_input(
            "Nombre del evento a analizar:",
            placeholder="Ej: page_view, purchase, add_to_cart",
            key="evento_especifico_input"
        )
        
        if st.button("Analizar Parámetros", key="btn_parametros_evento"):
            if evento_especifico:
                with st.spinner(f"Analizando parámetros de '{evento_especifico}'..."):
                    query = generar_query_parametros_eventos(
                        project, dataset, start_date, end_date, evento_especifico
                    )
                    df = run_query(client, query)
                    mostrar_parametros_evento(df, evento_especifico)
            else:
                st.error("⚠️ Por favor, introduce el nombre de un evento")
