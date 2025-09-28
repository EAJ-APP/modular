import streamlit as st
from database.queries import (
    generar_query_canales_trafico,
    generar_query_atribucion_marketing
)
from visualization.acquisition_visualizations import (
    mostrar_canales_trafico,
    mostrar_atribucion_marketing,
    mostrar_atribucion_multimodelo
)
from database.connection import run_query

def show_acquisition_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Adquisición con análisis de tráfico"""
    
    # Sección 1: Análisis de Canales de Tráfico
    with st.expander("🌐 Análisis de Canales de Tráfico", expanded=False):
        st.info("""
        **Análisis de canales de marketing agrupados por:**
        - 🎯 **AI Traffic** - Tráfico desde herramientas de IA
        - 🔍 **Organic Search** - Búsqueda orgánica
        - 💰 **Paid Search** - Búsqueda de pago
        - 📱 **Social** - Redes sociales (orgánico y pagado)
        - 🛒 **Shopping** - Plataformas de ecommerce
        - 📧 **Email** - Campañas de email
        - 🔗 **Referral** - Sitios referidores
        - Y más...
        """)
        
        # Usar form para mantener el estado
        with st.form(key="form_canales_trafico"):
            if st.form_submit_button("Analizar Canales de Tráfico", use_container_width=True):
                with st.spinner("Analizando distribución de canales..."):
                    query = generar_query_canales_trafico(project, dataset, start_date, end_date)
                    df = run_query(client, query)
                    mostrar_canales_trafico(df)
    
    # Sección 2: Atribución de Marketing
    with st.expander("🎯 Atribución de Marketing", expanded=False):
        st.info("""
        **Análisis de atribución por parámetros UTM:**
        - 📊 **Sesiones y conversiones** por fuente/medio/campaña
        - 💰 **Ingresos atribuidos** a cada canal
        - 📈 **Tasas de conversión** comparativas
        - 🏆 **Performance** de campañas específicas
        """)
        
        # Form para atribución básica
        with st.form(key="form_atribucion_basica"):
            if st.form_submit_button("Análisis Básico UTM", use_container_width=True):
                with st.spinner("Calculando atribución básica..."):
                    query = generar_query_atribucion_marketing(project, dataset, start_date, end_date)
                    df = run_query(client, query)
                    mostrar_atribucion_marketing(df)
    
    # Sección 3: Atribución Multi-Modelo (NUEVA)
    with st.expander("🔄 Atribución Multi-Modelo", expanded=False):
        st.info("""
        **Análisis de atribución con múltiples modelos:**
        - 🎯 **3 Modelos de Atribución:** Last Click, First Click, Linear
        - 📊 **Comparativa** entre diferentes modelos
        - 💰 **Ingresos atribuidos** por modelo y canal
        - 🔄 **Diferencias** entre modelos de atribución
        """)
        
        # Form para atribución multi-modelo
        with st.form(key="form_atribucion_multimodelo"):
            if st.form_submit_button("Análisis Multi-Modelo", use_container_width=True):
                with st.spinner("Calculando atribución multi-modelo..."):
                    query = generar_query_atribucion_marketing(project, dataset, start_date, end_date)
                    df = run_query(client, query)
                    mostrar_atribucion_multimodelo(df)
