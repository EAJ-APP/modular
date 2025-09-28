import streamlit as st
from database.queries import generar_query_canales_trafico
from visualization.acquisition_visualizations import mostrar_canales_trafico
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
