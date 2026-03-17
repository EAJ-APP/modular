import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

def show_monitoring_tab(client=None, project=None):
    """Pestaña de Monitorización de Consultas BigQuery"""
    
    st.title(" Monitorización de Consultas BigQuery")
    
    st.markdown("""
    Esta pestaña muestra información sobre las consultas ejecutadas en la sesión actual,
    incluyendo duración, consumo de datos y estado de ejecución.
    """)
    
    # Resto del código igual...
    
    # Verificar si hay datos de monitorización
    if 'monitoring_data' not in st.session_state:
        st.session_state.monitoring_data = []
    
    monitoring_data = st.session_state.monitoring_data
    
    if not monitoring_data:
        st.info(" No hay consultas registradas aún. Ejecuta algunas consultas en otros tabs para ver estadísticas aquí.")
        return
    
    # Métricas generales
    st.subheader(" Métricas Generales de la Sesión")
    
    total_queries = len(monitoring_data)
    successful_queries = sum(1 for q in monitoring_data if q['status'] == 'Success')
    failed_queries = sum(1 for q in monitoring_data if q['status'] == 'Error')
    total_duration = sum(q['duration'] for q in monitoring_data)
    total_gb = sum(q['gb_used'] for q in monitoring_data)
    avg_duration = total_duration / total_queries if total_queries > 0 else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Consultas", f"{total_queries}")
    
    with col2:
        st.metric("Exitosas", f"{successful_queries}", delta=f"{(successful_queries/total_queries*100):.1f}%" if total_queries > 0 else "0%")
    
    with col3:
        st.metric("Con Errores", f"{failed_queries}", delta=f"{(failed_queries/total_queries*100):.1f}%" if total_queries > 0 else "0%", delta_color="inverse")
    
    with col4:
        st.metric("Tiempo Total", f"{total_duration:.2f}s")
    
    with col5:
        st.metric("GB Procesados", f"{total_gb:.3f}")
    
    st.divider()
    
    # Duración de consultas
    st.subheader("⏱ Duración de Consultas")
    
    # Crear DataFrame para análisis
    df_monitoring = pd.DataFrame(monitoring_data)
    
    if not df_monitoring.empty:
        # Gráfico de duración por consulta
        fig_duration = px.bar(
            df_monitoring,
            x=df_monitoring.index,
            y='duration',
            color='status',
            title='Duración de Cada Consulta',
            labels={'index': 'Número de Consulta', 'duration': 'Duración (segundos)', 'status': 'Estado'},
            color_discrete_map={'Success': '#4CAF50', 'Error': '#F44336'},
            hover_data=['query_name']
        )
        fig_duration.update_layout(showlegend=True, height=400)
        st.plotly_chart(fig_duration, use_container_width=True)
        
        # Estadísticas de duración
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Duración Promedio", f"{avg_duration:.2f}s")
        
        with col2:
            max_duration = df_monitoring['duration'].max()
            st.metric("Más Lenta", f"{max_duration:.2f}s")
        
        with col3:
            min_duration = df_monitoring['duration'].min()
            st.metric("Más Rápida", f"{min_duration:.2f}s")
        
        with col4:
            median_duration = df_monitoring['duration'].median()
            st.metric("Duración Mediana", f"{median_duration:.2f}s")
    
    st.divider()
    
    # GB usados por query
    st.subheader(" GB Usados por Consulta")
    
    if monitoring_data:
        # Ordenar por GB usados descendente
        sorted_by_gb = sorted(monitoring_data, key=lambda x: x['gb_used'], reverse=True)
        
        # Mostrar top 10 consultas con más GB
        st.write("**Top 10 Consultas por Consumo de GB:**")
        
        for i, query in enumerate(sorted_by_gb[:10], 1):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Nombre de la consulta (truncado si es muy largo)
                query_name = query['query_name'][:60] + '...' if len(query['query_name']) > 60 else query['query_name']
                st.write(f"**{i}.** {query_name}")
            
            with col2:
                st.metric("GB Usados", f"{query['gb_used']:.3f}")
            
            with col3:
                st.metric("Duración", f"{query['duration']:.2f}s")
        
        # Resumen estadístico
        st.divider()
        
        total_gb = sum(q['gb_used'] for q in monitoring_data)
        avg_gb = total_gb / len(monitoring_data) if monitoring_data else 0
        max_gb_query = max(monitoring_data, key=lambda x: x['gb_used'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total GB (Sesión)", f"{total_gb:.3f} GB")
        
        with col2:
            st.metric("Promedio por Query", f"{avg_gb:.3f} GB")
        
        with col3:
            st.metric("Consulta Más Pesada", f"{max_gb_query['gb_used']:.3f} GB")
        
        st.caption(f"Consulta más pesada: {max_gb_query['query_name'][:50]}...")
    else:
        st.info("No hay datos de consumo GB en esta sesión")
    
    st.divider()
    
    # Distribución de estados
    st.subheader(" Estado de las Consultas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart de estados
        status_counts = df_monitoring['status'].value_counts()
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title='Distribución de Estados',
            color=status_counts.index,
            color_discrete_map={'Success': '#4CAF50', 'Error': '#F44336'}
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        # Métricas de rendimiento
        st.write("** Indicadores de Rendimiento:**")
        
        success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
        
        if success_rate >= 95:
            st.success(f" Tasa de éxito: {success_rate:.1f}% - Excelente")
        elif success_rate >= 80:
            st.info(f"ℹ Tasa de éxito: {success_rate:.1f}% - Bueno")
        else:
            st.warning(f" Tasa de éxito: {success_rate:.1f}% - Necesita atención")
        
        # Promedio de GB por consulta
        avg_gb_per_query = total_gb / total_queries if total_queries > 0 else 0
        
        if avg_gb_per_query < 0.5:
            st.success(f" Consumo promedio: {avg_gb_per_query:.3f} GB - Eficiente")
        elif avg_gb_per_query < 2.0:
            st.info(f"ℹ Consumo promedio: {avg_gb_per_query:.3f} GB - Moderado")
        else:
            st.warning(f" Consumo promedio: {avg_gb_per_query:.3f} GB - Alto consumo")
        
        # Tiempo promedio
        if avg_duration < 5:
            st.success(f" Tiempo promedio: {avg_duration:.2f}s - Rápido")
        elif avg_duration < 15:
            st.info(f"ℹ Tiempo promedio: {avg_duration:.2f}s - Normal")
        else:
            st.warning(f" Tiempo promedio: {avg_duration:.2f}s - Lento")
    
    st.divider()
    
    # Tabla completa de consultas
    st.subheader(" Tabla Completa de Consultas")
    
    if monitoring_data:
        # Preparar datos para la tabla
        table_data = []
        for query in monitoring_data:
            table_data.append({
                'Nombre de Consulta': query['query_name'],
                'Fecha y Hora': query['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'Duración (s)': round(query['duration'], 2),
                'GB Usados': round(query['gb_used'], 3),
                'Estado': query['status']
            })
        
        # Crear DataFrame
        df_queries = pd.DataFrame(table_data)
        
        # Ordenar por fecha descendente (más reciente primero)
        df_queries = df_queries.sort_values('Fecha y Hora', ascending=False)
        
        # Aplicar estilo condicional
        def highlight_status(row):
            if row['Estado'] == 'Success':
                return ['background-color: #d4edda'] * len(row)
            elif row['Estado'] == 'Error':
                return ['background-color: #f8d7da'] * len(row)
            else:
                return [''] * len(row)
        
        # Mostrar tabla con formato
        st.dataframe(
            df_queries.style.apply(highlight_status, axis=1).format({
                'Duración (s)': '{:.2f}',
                'GB Usados': '{:.3f}'
            }),
            height=600,
            use_container_width=True
        )
        
        # Información adicional
        st.caption(f"""
         **Total de consultas en sesión:** {len(monitoring_data)} | 
         **Exitosas:** {sum(1 for q in monitoring_data if q['status'] == 'Success')} | 
         **Con errores:** {sum(1 for q in monitoring_data if q['status'] == 'Error')}
        """)
        
        # Botón para exportar
        col1, col2 = st.columns([1, 4])
        with col1:
            csv_queries = df_queries.to_csv(index=False)
            st.download_button(
                label=" Descargar CSV",
                data=csv_queries,
                file_name=f"consultas_bigquery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No hay consultas registradas en esta sesión")
    
    st.divider()
    
    # Timeline de consultas
    st.subheader(" Timeline de Consultas")
    
    if not df_monitoring.empty and 'timestamp' in df_monitoring.columns:
        # Convertir timestamp a formato legible
        df_monitoring['time_str'] = df_monitoring['timestamp'].dt.strftime('%H:%M:%S')
        
        fig_timeline = px.scatter(
            df_monitoring,
            x='timestamp',
            y='duration',
            color='status',
            size='gb_used',
            title='Timeline de Ejecución de Consultas',
            labels={
                'timestamp': 'Hora de Ejecución',
                'duration': 'Duración (segundos)',
                'status': 'Estado',
                'gb_used': 'GB Usados'
            },
            color_discrete_map={'Success': '#4CAF50', 'Error': '#F44336'},
            hover_data=['query_name', 'gb_used']
        )
        fig_timeline.update_layout(height=400)
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    st.divider()
    
    # Recomendaciones
    st.subheader(" Recomendaciones")
    
    recommendations = []
    
    # Análisis de errores
    if failed_queries > 0:
        error_rate = (failed_queries / total_queries * 100)
        recommendations.append(f" Tienes {failed_queries} consultas con errores ({error_rate:.1f}%). Revisa los logs para identificar problemas.")
    
    # Análisis de duración
    if avg_duration > 20:
        recommendations.append(f" El tiempo promedio de consulta es {avg_duration:.2f}s. Considera optimizar las consultas más lentas o reducir el rango de fechas.")
    
    # Análisis de GB
    if avg_gb > 1.0:
        recommendations.append(f" El consumo promedio por consulta es {avg_gb:.3f} GB. Intenta filtrar más datos o usar particiones.")
    
    # Consultas específicas lentas
    slow_queries = [q for q in monitoring_data if q['duration'] > 30]
    if slow_queries:
        recommendations.append(f"⏱ Tienes {len(slow_queries)} consultas que tardaron más de 30 segundos. Considera optimizarlas.")
    
    # Consultas pesadas en GB
    heavy_queries = [q for q in monitoring_data if q['gb_used'] > 2.0]
    if heavy_queries:
        recommendations.append(f" Tienes {len(heavy_queries)} consultas que procesaron más de 2 GB. Revisa si puedes reducir el volumen de datos.")
    
    if recommendations:
        for rec in recommendations:
            st.warning(rec)
    else:
        st.success(" ¡Excelente! Todas las métricas están en rangos óptimos.")
    
    st.divider()
    
    # Botón para limpiar monitorización
    st.subheader(" Gestión de Datos")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button(" Limpiar Historial", type="secondary"):
            st.session_state.monitoring_data = []
            st.success(" Historial de consultas limpiado")
            st.rerun()
    
    with col2:
        st.caption("Limpia el historial de consultas de la sesión actual. Esto no afecta a los datos en BigQuery.")
