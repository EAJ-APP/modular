import streamlit as st
from database.queries import (
    generar_query_comparativa_eventos,
    generar_query_ingresos_transacciones,
    generar_query_productos_mas_vendidos,
    generar_query_relacion_productos,
    generar_query_combos_cross_selling
)
from visualization.ecommerce_visualizations import (
    mostrar_comparativa_eventos,
    mostrar_ingresos_transacciones,
    mostrar_productos_mas_vendidos,
    mostrar_relacion_productos,
    mostrar_combos_cross_selling
)
from database.connection import run_query

def show_ecommerce_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Ecommerce con análisis completo de eventos y productos"""
    
    # Inicializar session_state para mantener datos y estado de expanders
    if 'ecommerce_funnel_data' not in st.session_state:
        st.session_state.ecommerce_funnel_data = None
    if 'ecommerce_funnel_show' not in st.session_state:
        st.session_state.ecommerce_funnel_show = False
    
    if 'ecommerce_ingresos_data' not in st.session_state:
        st.session_state.ecommerce_ingresos_data = None
    if 'ecommerce_ingresos_show' not in st.session_state:
        st.session_state.ecommerce_ingresos_show = False
    
    if 'ecommerce_productos_data' not in st.session_state:
        st.session_state.ecommerce_productos_data = None
    if 'ecommerce_productos_show' not in st.session_state:
        st.session_state.ecommerce_productos_show = False
    
    if 'ecommerce_relacion_data' not in st.session_state:
        st.session_state.ecommerce_relacion_data = None
    if 'ecommerce_relacion_show' not in st.session_state:
        st.session_state.ecommerce_relacion_show = False

    if 'ecommerce_combos_data' not in st.session_state:
        st.session_state.ecommerce_combos_data = None
    if 'ecommerce_combos_show' not in st.session_state:
        st.session_state.ecommerce_combos_show = False
    
    # Sección 1: Funnel de Conversión
    with st.expander(" Funnel de Conversión", expanded=st.session_state.ecommerce_funnel_show):
        st.info("""
        **Análisis completo del funnel de ecommerce:**
        - 5 etapas: page_view → view_item → add_to_cart → begin_checkout → purchase
        - Tasas de conversión entre etapas
        - Identificación de puntos de fuga
        - Métricas de usuarios únicos por evento
        """)
        
        if st.button("Ejecutar Análisis de Funnel", key="btn_funnel"):
            with st.spinner("Analizando funnel de conversión..."):
                query = generar_query_comparativa_eventos(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.ecommerce_funnel_data = df
                st.session_state.ecommerce_funnel_show = True
        
        # Mostrar resultados si existen
        if st.session_state.ecommerce_funnel_show and st.session_state.ecommerce_funnel_data is not None:
            mostrar_comparativa_eventos(st.session_state.ecommerce_funnel_data)
    
    # Sección 2: Ingresos y Transacciones
    with st.expander(" Ingresos y Transacciones", expanded=st.session_state.ecommerce_ingresos_show):
        st.info("""
        **Análisis de revenue y transacciones:**
        - Evolución temporal de ingresos
        - Número de transacciones únicas
        - Ticket medio (AOV - Average Order Value)
        - Tendencias de compra por fecha
        - Identificación de picos de ventas
        """)
        
        if st.button("Analizar Ingresos y Transacciones", key="btn_ingresos"):
            with st.spinner("Calculando ingresos y transacciones..."):
                query = generar_query_ingresos_transacciones(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.ecommerce_ingresos_data = df
                st.session_state.ecommerce_ingresos_show = True
        
        # Mostrar resultados si existen
        if st.session_state.ecommerce_ingresos_show and st.session_state.ecommerce_ingresos_data is not None:
            mostrar_ingresos_transacciones(st.session_state.ecommerce_ingresos_data)
    
    # Sección 3: Productos Más Vendidos
    with st.expander(" Productos Más Vendidos [IA]", expanded=st.session_state.ecommerce_productos_show):
        st.info("""
        **Performance de productos por ingresos:**
        - Top productos ordenados por revenue
        - Cantidad total vendida por producto
        - Número de compras (transacciones)
        - Análisis de correlación cantidad vs ingresos
        - Identificación de productos estrella
        - Productos con nombre normalizado (item_name)
        """)
        
        if st.button("Analizar Performance de Productos", key="btn_productos"):
            with st.spinner("Analizando productos más vendidos..."):
                query = generar_query_productos_mas_vendidos(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.ecommerce_productos_data = df
                st.session_state.ecommerce_productos_show = True
        
        # Mostrar resultados si existen
        if st.session_state.ecommerce_productos_show and st.session_state.ecommerce_productos_data is not None:
            mostrar_productos_mas_vendidos(st.session_state.ecommerce_productos_data)
    
    # Sección 4: Relación ID vs Nombre de Productos
    with st.expander(" Relación ID vs Nombre de Productos", expanded=st.session_state.ecommerce_relacion_show):
        st.info("""
        **Análisis de consistencia de datos:**
        - Validación de relación item_id ↔ item_name
        - Detección de productos con múltiples nombres
        - Detección de nombres con múltiples IDs
        - Identificación de ineficiencias en el tracking
        - Recomendaciones de limpieza de datos
        """)
        
        if st.button("Analizar Relación Productos", key="btn_relacion"):
            with st.spinner("Analizando relación ID vs Nombre..."):
                query = generar_query_relacion_productos(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.ecommerce_relacion_data = df
                st.session_state.ecommerce_relacion_show = True
        
        # Mostrar resultados si existen
        if st.session_state.ecommerce_relacion_show and st.session_state.ecommerce_relacion_data is not None:
            mostrar_relacion_productos(st.session_state.ecommerce_relacion_data)

    # ==========================================
    # SECCIÓN 5: Análisis de Combos y Cross-Selling (NUEVO)
    # ==========================================
    with st.expander(" Análisis de Combos y Cross-Selling", 
                     expanded=st.session_state.ecommerce_combos_show):
        st.info("""
        **Market Basket Analysis:**
        - Identificar productos que se compran juntos frecuentemente
        - Calcular Lift, Confidence y Support de cada combo
        - Optimizar estrategia de cross-selling y bundles
        - Aumentar AOV (Average Order Value) mediante recomendaciones
        """)
        
        if st.button("Analizar Combos y Cross-Selling", key="btn_combos"):
            with st.spinner("Analizando combos de productos (esto puede tardar)..."):
                query = generar_query_combos_cross_selling(project, dataset, start_date, end_date)
                df = run_query(client, query)
                st.session_state.ecommerce_combos_data = df
                st.session_state.ecommerce_combos_show = True
        
        # Mostrar resultados si existen
        if st.session_state.ecommerce_combos_show and st.session_state.ecommerce_combos_data is not None:
            mostrar_combos_cross_selling(st.session_state.ecommerce_combos_data)
    # Mensaje de completado
    st.success(" **Todas las consultas de Ecommerce están disponibles!**")
