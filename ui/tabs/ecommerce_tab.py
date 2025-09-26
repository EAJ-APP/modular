import streamlit as st
from database.queries import (
    generar_query_comparativa_eventos,
    generar_query_ingresos_transacciones,
    generar_query_productos_mas_vendidos,
    generar_query_relacion_productos,
    generar_query_funnel_por_producto
)
from visualization.ecommerce_visualizations import (
    mostrar_comparativa_eventos,
    mostrar_ingresos_transacciones,
    mostrar_productos_mas_vendidos,
    mostrar_relacion_productos,
    mostrar_funnel_por_producto
)
from database.connection import run_query

def show_ecommerce_tab(client, project, dataset, start_date, end_date):
    """Pestaña de Ecommerce con análisis de eventos"""
    with st.expander("📊 Funnel de Conversión", expanded=True):
        if st.button("Ejecutar Análisis de Funnel", key="btn_funnel"):
            with st.spinner("Analizando funnel de conversión..."):
                query = generar_query_comparativa_eventos(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_comparativa_eventos(df)
    
    with st.expander("💰 Ingresos y Transacciones", expanded=True):
        if st.button("Analizar Ingresos y Transacciones", key="btn_ingresos"):
            with st.spinner("Calculando ingresos y transacciones..."):
                query = generar_query_ingresos_transacciones(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_ingresos_transacciones(df)
    
    with st.expander("🏆 Productos Más Vendidos", expanded=True):
        if st.button("Analizar Performance de Productos", key="btn_productos"):
            with st.spinner("Analizando productos más vendidos..."):
                query = generar_query_productos_mas_vendidos(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_productos_mas_vendidos(df)
    
    with st.expander("🔍 Relación ID vs Nombre de Productos", expanded=True):
        if st.button("Analizar Relación Productos", key="btn_relacion"):
            with st.spinner("Analizando relación ID vs Nombre..."):
                query = generar_query_relacion_productos(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_relacion_productos(df)
    
    with st.expander("📈 Funnel de Conversión por Producto", expanded=True):
        if st.button("Analizar Funnel por Producto", key="btn_funnel_producto"):
            with st.spinner("Analizando funnel por producto..."):
                query = generar_query_funnel_por_producto(project, dataset, start_date, end_date)
                df = run_query(client, query)
                mostrar_funnel_por_producto(df)