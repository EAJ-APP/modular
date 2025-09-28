import streamlit as st
from database.queries import (
    generar_query_canales_trafico,
    generar_query_atribucion_marketing  # NUEVO
)
from visualization.acquisition_visualizations import (
    mostrar_canales_trafico,
    mostrar_atribucion_marketing  # NUEVO
)
from database.connection import run_query

def show_acquisition_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Adquisición con análisis de tráfico"""
    
    with st.expander("🌐 Análisis de Canales de Tráfico", expanded=True):
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
        
        if st.button("Analizar Canales de Tráfico", key="btn_canales_trafico"):
            with st.spinner("Analizando distribución de canales..."):
                query = generar_query_canales_trafico(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_canales_trafico(df)
    
    # En la sección de atribución, actualizar el botón y la llamada:
with st.expander("🎯 Atribución de Marketing", expanded=True):
    st.info("""
    **Análisis de atribución multi-modelo:**
    - 🎯 **3 Modelos de Atribución:** Last Click, First Click, Linear
    - 📊 **Comparativa** entre diferentes modelos
    - 💰 **Ingresos atribuidos** por modelo y canal
    - 🔄 **Diferencias** entre modelos de atribución
    - 📈 **Eficiencia** por sesión y conversión
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Análisis Básico UTM", key="btn_atribucion_basica"):
            with st.spinner("Calculando atribución básica..."):
                query = generar_query_atribucion_marketing(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_atribucion_marketing(df)
    
    with col2:
        if st.button("Análisis Multi-Modelo", key="btn_atribucion_multimodelo"):
            with st.spinner("Calculando atribución multi-modelo..."):
                query = generar_query_atribucion_marketing(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_atribucion_multimodelo(df)
