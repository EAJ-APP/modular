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
    
    # NUEVA SECCIÓN: Atribución de Marketing
    with st.expander("🎯 Atribución de Marketing", expanded=True):
        st.info("""
        **Análisis de atribución por parámetros UTM:**
        - 📊 **Sesiones y conversiones** por fuente/medio/campaña
        - 💰 **Ingresos atribuidos** a cada canal
        - 📈 **Tasas de conversión** comparativas
        - 🏆 **Performance** de campañas específicas
        - 📉 **Eficiencia** por sesión y conversión
        """)
        
        if st.button("Analizar Atribución UTM", key="btn_atribucion"):
            with st.spinner("Calculando atribución de marketing..."):
                query = generar_query_atribucion_marketing(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_atribucion_marketing(df)
