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
    """Pestaña de Cookies con consultas separadas"""
    with st.expander("🛡️ Consentimiento Básico", expanded=True):
        if st.button("Ejecutar Análisis Básico", key="btn_consent_basic"):
            with st.spinner("Calculando consentimientos..."):
                query = generar_query_consentimiento_basico(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_consentimiento_basico(df)
    
    with st.expander("📱 Consentimiento por Dispositivo", expanded=True):
        if st.button("Ejecutar Análisis por Dispositivo", key="btn_consent_device"):
            with st.spinner("Analizando dispositivos..."):
                query = generar_query_consentimiento_por_dispositivo(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_consentimiento_por_dispositivo(df)
    
    with st.expander("🔍 Porcentaje Real de Consentimiento", expanded=True):
        if st.button("Calcular Consentimiento Real", key="btn_consent_real"):
            with st.spinner("Analizando todos los eventos..."):
                query = generar_query_consentimiento_real(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_consentimiento_real(df)