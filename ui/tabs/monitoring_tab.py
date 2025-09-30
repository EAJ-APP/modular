import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.bq_monitoring import (
    get_project_usage_last_days,
    get_current_month_usage,
    check_free_tier_limit,
    bytes_to_readable
)

def show_monitoring_tab(client, project):
    """Pestaña de Monitorización de Consumo BigQuery"""
    
    st.subheader("📊 Monitorización de Consumo BigQuery")
    
    # Sección 1: Uso del Mes Actual
    st.markdown("### 📅 Uso del Mes Actual")
    
    with st.spinner("Calculando uso mensual..."):
        month_usage = get_current_month_usage(client, project)
    
    if month_usage['success']:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Consultas", f"{month_usage['total_queries']:,}")
        
        with col2:
            st.metric("Datos Procesados", month_usage['total_bytes_readable'])
        
        with col3:
            st.metric("Costo Estimado (USD)", f"${month_usage['estimated_cost_usd']:.2f}")
        
        with col4:
            st.metric("Costo Estimado (EUR)", f"€{month_usage['estimated_cost_eur']:.2f}")
        
        # Verificar free tier
        st.markdown("---")
        st.markdown("### 🎁 Estado del Free Tier")
        
        free_tier = check_free_tier_limit(month_usage['total_gb'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "GB Usados / Free Tier", 
                f"{free_tier['used_gb']:.2f} GB / {free_tier['free_tier_gb']} GB"
            )
            
            # Barra de progreso
            progress_value = min(free_tier['percentage_used'] / 100, 1.0)
            st.progress(progress_value)
            
            if free_tier['within_free_tier']:
                st.success(f"✅ Dentro del free tier. Quedan {free_tier['remaining_gb']:.2f} GB gratis")
            else:
                excess_gb = abs(free_tier['remaining_gb'])
                excess_cost = excess_gb * 0.005
                st.warning(f"⚠️ Has excedido el free tier por {excess_gb:.2f} GB (≈${excess_cost:.2f})")
        
        with col2:
            # Gráfico de gauge
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=free_tier['percentage_used'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "% Free Tier Usado"},
                delta={'reference': 100},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgreen"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "orange"},
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 100
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
    
    else:
        st.error(f"❌ Error al obtener uso mensual: {month_usage.get('error', 'Error desconocido')}")
    
    # Sección 2: Uso de los Últimos 7 Días
    st.markdown("---")
    st.markdown("### 📈 Uso de los Últimos 7 Días")
    
    days_to_show = st.selectbox("Días a mostrar:", [7, 14, 30], index=0, key="monitoring_days")
    
    with st.spinner(f"Cargando datos de los últimos {days_to_show} días..."):
        usage_df = get_project_usage_last_days(client, project, days=days_to_show)
    
    if not usage_df.empty:
        # Agrupar por fecha para vista diaria
        daily_usage = usage_df.groupby('date').agg({
            'total_queries': 'sum',
            'total_bytes_processed': 'sum',
            'total_gb_processed': 'sum',
            'estimated_cost_usd': 'sum'
        }).reset_index().sort_values('date')
        
        # Agregar columnas legibles
        daily_usage['total_bytes_readable'] = daily_usage['total_bytes_processed'].apply(bytes_to_readable)
        
        # Gráfico de evolución de GB procesados
        col1, col2 = st.columns(2)
        
        with col1:
            fig_gb = px.line(
                daily_usage,
                x='date',
                y='total_gb_processed',
                title='GB Procesados por Día',
                labels={'total_gb_processed': 'GB', 'date': 'Fecha'},
                markers=True
            )
            fig_gb.update_layout(hovermode='x unified')
            st.plotly_chart(fig_gb, use_container_width=True)
        
        with col2:
            fig_queries = px.bar(
                daily_usage,
                x='date',
                y='total_queries',
                title='Número de Consultas por Día',
                labels={'total_queries': 'Consultas', 'date': 'Fecha'},
                color='total_queries',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig_queries, use_container_width=True)
        
        # Gráfico de costo acumulado
        daily_usage['cumulative_cost'] = daily_usage['estimated_cost_usd'].cumsum()
        
        fig_cost = go.Figure()
        fig_cost.add_trace(go.Scatter(
            x=daily_usage['date'],
            y=daily_usage['estimated_cost_usd'],
            name='Costo Diario',
            mode='lines+markers',
            line=dict(color='orange')
        ))
        fig_cost.add_trace(go.Scatter(
            x=daily_usage['date'],
            y=daily_usage['cumulative_cost'],
            name='Costo Acumulado',
            mode='lines+markers',
            line=dict(color='red', dash='dash')
        ))
        fig_cost.update_layout(
            title='Evolución de Costos (USD)',
            xaxis_title='Fecha',
            yaxis_title='Costo (USD)',
            hovermode='x unified'
        )
        st.plotly_chart(fig_cost, use_container_width=True)
        
        # Tabla detallada
        st.markdown("#### 📋 Datos Detallados")
        st.dataframe(
            daily_usage[['date', 'total_queries', 'total_bytes_readable', 'total_gb_processed', 'estimated_cost_usd']].style.format({
                'total_queries': '{:,}',
                'total_gb_processed': '{:.2f}',
                'estimated_cost_usd': '${:.4f}'
            }),
            use_container_width=True
        )
        
        # Si hay datos por usuario, mostrarlos
        if 'user_email' in usage_df.columns:
            st.markdown("---")
            st.markdown("### 👥 Uso por Usuario")
            
            user_usage = usage_df.groupby('user_email').agg({
                'total_queries': 'sum',
                'total_bytes_processed': 'sum',
                'total_gb_processed': 'sum',
                'estimated_cost_usd': 'sum'
            }).reset_index().sort_values('total_gb_processed', ascending=False)
            
            user_usage['total_bytes_readable'] = user_usage['total_bytes_processed'].apply(bytes_to_readable)
            
            # Top 10 usuarios por consumo
            top_users = user_usage.head(10)
            
            fig_users = px.bar(
                top_users,
                x='total_gb_processed',
                y='user_email',
                orientation='h',
                title='Top 10 Usuarios por GB Procesados',
                labels={'total_gb_processed': 'GB', 'user_email': 'Usuario'},
                color='total_gb_processed',
                color_continuous_scale='Reds'
            )
            fig_users.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
            st.plotly_chart(fig_users, use_container_width=True)
            
            # Tabla de usuarios
            st.dataframe(
                user_usage[['user_email', 'total_queries', 'total_bytes_readable', 'total_gb_processed', 'estimated_cost_usd']].style.format({
                    'total_queries': '{:,}',
                    'total_gb_processed': '{:.2f}',
                    'estimated_cost_usd': '${:.4f}'
                }),
                use_container_width=True
            )
    
    else:
        st.warning("⚠️ No se encontraron datos de uso. Esto puede deberse a permisos insuficientes o a que no hay consultas en el período seleccionado.")
    
    # Sección 3: Historial de Consultas de esta Sesión
    st.markdown("---")
    st.markdown("### 🔄 Historial de Consultas (Sesión Actual)")
    
    if 'query_history' in st.session_state and len(st.session_state.query_history) > 0:
        history_df = pd.DataFrame(st.session_state.query_history)
        
        # Calcular totales de la sesión
        total_session_bytes = history_df['bytes_processed'].sum()
        total_session_cost = history_df['cost_usd'].sum()
        cache_hits = history_df['cache_hit'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Consultas en Sesión", len(history_df))
        with col2:
            st.metric("Datos Procesados", bytes_to_readable(total_session_bytes))
        with col3:
            st.metric("Costo Sesión", f"${total_session_cost:.6f}")
        with col4:
            st.metric("Cache Hits", f"{cache_hits}/{len(history_df)}")
        
        # Gráfico de consumo por consulta
        history_df['query_number'] = range(1, len(history_df) + 1)
        history_df['gb_processed'] = history_df['bytes_processed'] / (1024 ** 3)
        
        fig_session = px.bar(
            history_df,
            x='query_number',
            y='gb_processed',
            title='Consumo por Consulta en esta Sesión',
            labels={'gb_processed': 'GB Procesados', 'query_number': 'Consulta #'},
            color='cache_hit',
            color_discrete_map={True: 'green', False: 'blue'}
        )
        st.plotly_chart(fig_session, use_container_width=True)
        
        # Mostrar tabla
        st.dataframe(
            history_df[['timestamp', 'bytes_readable', 'cache_hit', 'cost_usd']].style.format({
                'cost_usd': '${:.6f}'
            }),
            use_container_width=True
        )
        
        # Botón para limpiar historial
        if st.button("🗑️ Limpiar Historial de Sesión"):
            st.session_state.query_history = []
            st.rerun()
    
    else:
        st.info("ℹ️ No hay consultas en esta sesión todavía. Ejecuta algunas consultas para ver el historial.")
    
    # Información adicional
    st.markdown("---")
    st.markdown("### ℹ️ Información sobre Costos")
    
    with st.expander("💰 Precios de BigQuery", expanded=False):
        st.markdown("""
        **Modelo On-Demand (Pago por Uso):**
        - **$5 por TB** procesado ($0.005 por GB)
        - **1 TB gratis** al mes (1024 GB)
        - El almacenamiento es gratuito hasta 10 GB
        
        **Optimizaciones para Reducir Costos:**
        - ✅ **Usar SELECT específico**: No usar `SELECT *`, especificar columnas
        - ✅ **Filtrar con WHERE**: Limitar datos con condiciones
        - ✅ **Particionar tablas**: Usar `_TABLE_SUFFIX` en eventos_*
        - ✅ **Aprovechar caché**: Las consultas idénticas usan caché (gratis)
        - ✅ **Limitar con LIMIT**: Solo consultar los datos necesarios
        - ✅ **Evitar JOINs grandes**: Optimizar joins y agregaciones
        
        **Estimación de Consultas:**
        - Esta herramienta estima el costo ANTES de ejecutar (dry run)
        - Los costos reales pueden variar ligeramente
        - Las consultas servidas desde caché son completamente gratis
        
        **Más información:**
        - [Precios de BigQuery](https://cloud.google.com/bigquery/pricing)
        - [Mejores prácticas](https://cloud.google.com/bigquery/docs/best-practices-costs)
        """)
    
    with st.expander("🎯 Consejos para Optimizar", expanded=False):
        st.markdown("""
        **Para esta herramienta BigQuery Shield:**
        
        1. **Reduce el rango de fechas**: Menos días = menos datos procesados
        2. **Usa filtros específicos**: Filtra por canales, dispositivos, etc.
        3. **Ejecuta consultas por partes**: No ejecutes todas las tabs a la vez
        4. **Revisa el historial**: Ve qué consultas consumen más en esta sesión
        5. **Aprovecha el caché**: Ejecutar la misma consulta dos veces usa caché
        
        **Consultas más pesadas en esta app:**
        - 🔴 **Eventos Flatten**: Puede procesar varios GB (limitada a 1000 filas)
        - 🟡 **Atribución Completa (7 modelos)**: Procesa bastantes datos
        - 🟡 **Session Path Analysis**: Depende del volumen de sesiones
        - 🟢 **Cookies y Ecommerce**: Generalmente ligeras
        """)
