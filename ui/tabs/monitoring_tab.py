import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.bq_monitoring import bytes_to_readable

def show_monitoring_tab(client, project):
    """
    Pestaña de Monitorización de Consumo BigQuery
    VERSIÓN LIMITADA: Solo monitoriza sesión actual (no requiere permisos especiales)
    """
    
    st.subheader("📊 Monitorización de Consumo BigQuery")
    
    # Aviso sobre permisos
    st.info("""
    ℹ️ **Monitorización en Modo Básico**
    
    Esta cuenta no tiene permisos para acceder al historial completo de BigQuery.
    Mostrando solo las consultas de **esta sesión**.
    
    **Para habilitar monitorización completa**, el administrador de GCP debe otorgar:
    - Rol: `BigQuery Job User` o `BigQuery Admin`
    - Permiso: `bigquery.jobs.list`
    """)
    
    # Sección 1: Historial de Consultas de esta Sesión
    st.markdown("---")
    st.markdown("### 🔄 Historial de Consultas (Sesión Actual)")
    
    if 'query_history' in st.session_state and len(st.session_state.query_history) > 0:
        history_df = pd.DataFrame(st.session_state.query_history)
        
        # Calcular totales de la sesión
        total_session_bytes = history_df['bytes_processed'].sum()
        total_session_gb = total_session_bytes / (1024 ** 3)
        total_session_cost = history_df['cost_usd'].sum()
        cache_hits = history_df['cache_hit'].sum()
        cache_rate = (cache_hits / len(history_df) * 100) if len(history_df) > 0 else 0
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Consultas Ejecutadas", len(history_df))
        with col2:
            st.metric("Datos Procesados", bytes_to_readable(total_session_bytes))
        with col3:
            st.metric("Costo Sesión (USD)", f"${total_session_cost:.6f}")
        with col4:
            st.metric("Tasa Caché", f"{cache_rate:.1f}%")
        
        # Información sobre el Free Tier
        st.markdown("---")
        st.markdown("### 🎁 Información del Free Tier de BigQuery")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Info del free tier
            FREE_TIER_GB = 1024  # 1 TB
            percentage_used_session = (total_session_gb / FREE_TIER_GB) * 100
            
            st.info(f"""
            **Free Tier de BigQuery:**
            - **1 TB (1024 GB) gratis al mes**
            - Se reinicia el día 1 de cada mes
            - Las consultas en caché NO cuentan
            
            **En esta sesión has usado:**
            - {total_session_gb:.4f} GB ({percentage_used_session:.2f}% del free tier)
            - {cache_hits} de {len(history_df)} consultas fueron desde caché (gratis)
            """)
        
        with col2:
            # Gauge del free tier proyectado
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=total_session_gb,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"GB Usados (Sesión)<br><sub>Free Tier: {FREE_TIER_GB} GB/mes</sub>"},
                gauge={
                    'axis': {'range': [None, 10]},  # Escala de 0 a 10 GB
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 5], 'color': "lightgreen"},
                        {'range': [5, 8], 'color': "yellow"},
                        {'range': [8, 10], 'color': "orange"},
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 10
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Gráfico de consumo por consulta
        st.markdown("---")
        st.markdown("### 📊 Análisis de Consultas")
        
        history_df['query_number'] = range(1, len(history_df) + 1)
        history_df['gb_processed'] = history_df['bytes_processed'] / (1024 ** 3)
        history_df['mb_processed'] = history_df['bytes_processed'] / (1024 ** 2)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de barras: consumo por consulta
            fig_session = px.bar(
                history_df,
                x='query_number',
                y='mb_processed',
                title='Consumo por Consulta (MB)',
                labels={'mb_processed': 'MB Procesados', 'query_number': 'Consulta #'},
                color='cache_hit',
                color_discrete_map={True: 'green', False: 'blue'},
                hover_data=['bytes_readable', 'cost_usd']
            )
            fig_session.update_layout(showlegend=True)
            st.plotly_chart(fig_session, use_container_width=True)
        
        with col2:
            # Pie chart: caché vs no caché
            cache_data = pd.DataFrame({
                'tipo': ['Desde Caché (gratis)', 'Procesadas'],
                'cantidad': [cache_hits, len(history_df) - cache_hits]
            })
            
            fig_cache = px.pie(
                cache_data,
                values='cantidad',
                names='tipo',
                title='Consultas: Caché vs Procesadas',
                color='tipo',
                color_discrete_map={
                    'Desde Caché (gratis)': 'green',
                    'Procesadas': 'blue'
                }
            )
            st.plotly_chart(fig_cache, use_container_width=True)
        
        # Top consultas más pesadas
        st.markdown("### 🔝 Top 10 Consultas Más Pesadas")
        
        top_queries = history_df.nlargest(10, 'bytes_processed')
        
        fig_top = px.bar(
            top_queries,
            x='query_number',
            y='gb_processed',
            title='Top 10 Consultas por GB Procesados',
            labels={'gb_processed': 'GB', 'query_number': 'Consulta #'},
            color='gb_processed',
            color_continuous_scale='Reds',
            hover_data=['bytes_readable', 'cost_usd', 'cache_hit']
        )
        st.plotly_chart(fig_top, use_container_width=True)
        
        # Estadísticas detalladas
        st.markdown("### 📋 Estadísticas Detalladas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_bytes = history_df['bytes_processed'].mean()
            st.metric("Promedio por Consulta", bytes_to_readable(avg_bytes))
        
        with col2:
            max_bytes = history_df['bytes_processed'].max()
            st.metric("Consulta Más Grande", bytes_to_readable(max_bytes))
        
        with col3:
            min_bytes = history_df[history_df['bytes_processed'] > 0]['bytes_processed'].min() if len(history_df[history_df['bytes_processed'] > 0]) > 0 else 0
            st.metric("Consulta Más Pequeña", bytes_to_readable(min_bytes))
        
        # Tabla completa
        st.markdown("---")
        st.markdown("### 📄 Tabla Completa de Consultas")
        
        # Preparar DataFrame para mostrar
        display_df = history_df[['query_number', 'timestamp', 'bytes_readable', 'cache_hit', 'cost_usd']].copy()
        display_df['cache_hit'] = display_df['cache_hit'].map({True: '✅ Caché', False: '🔄 Procesada'})
        
        st.dataframe(
            display_df.style.format({
                'cost_usd': '${:.6f}',
                'timestamp': lambda x: x.strftime('%H:%M:%S') if hasattr(x, 'strftime') else str(x)
            }),
            use_container_width=True,
            height=400
        )
        
        # Botones de acción
        col1, col2 = st.columns(2)
        
        with col1:
            # Descargar historial
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar Historial CSV",
                data=csv,
                file_name="bq_query_history.csv",
                mime="text/csv"
            )
        
        with col2:
            # Limpiar historial
            if st.button("🗑️ Limpiar Historial", type="secondary"):
                st.session_state.query_history = []
                st.rerun()
    
    else:
        st.info("ℹ️ No hay consultas en esta sesión todavía. Ejecuta algunas consultas para ver el historial.")
        
        # Mostrar ejemplo de cómo se verá
        st.markdown("### 📊 Vista Previa")
        st.markdown("""
        Cuando ejecutes consultas en las otras tabs, aquí verás:
        - 📊 Cuántos GB procesa cada consulta
        - 💰 Costo estimado de cada consulta
        - ✅ Qué consultas se sirvieron desde caché (gratis)
        - 📈 Gráficos de evolución de consumo
        - 🏆 Top consultas más pesadas
        """)
    
    # Información adicional
    st.markdown("---")
    st.markdown("### ℹ️ Información sobre Costos y Optimización")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("💰 Precios de BigQuery", expanded=False):
            st.markdown("""
            **Modelo On-Demand (Pago por Uso):**
            - **$5 por TB** procesado ($0.005 por GB)
            - **1 TB gratis** al mes (1024 GB)
            - El almacenamiento es gratuito hasta 10 GB
            - Las consultas en caché son **completamente gratis**
            
            **Cómo se calcula el costo:**
            ```
            Costo = (GB procesados) × $0.005
            ```
            
            **Ejemplo:**
            - Consulta de 10 GB = $0.05
            - Consulta de 100 GB = $0.50
            - Consulta de 1 TB = $5.00
            
            **Free Tier:**
            - Primeros 1024 GB al mes: **$0**
            - GB adicionales: $0.005 por GB
            - Se reinicia el 1 de cada mes
            
            **Más información:**
            - [Precios de BigQuery](https://cloud.google.com/bigquery/pricing)
            """)
    
    with col2:
        with st.expander("🎯 Consejos para Optimizar", expanded=False):
            st.markdown("""
            **Para esta herramienta BigQuery Shield:**
            
            1. **Reduce el rango de fechas**: 
               - Menos días = menos datos procesados
               - 7 días suele ser suficiente para análisis
            
            2. **Usa filtros específicos**: 
               - Filtra por canales, dispositivos, etc.
               - Usa los sliders y selectores de cada tab
            
            3. **Ejecuta consultas por partes**: 
               - No ejecutes todas las tabs a la vez
               - Analiza primero las más importantes
            
            4. **Revisa el historial**: 
               - Ve qué consultas consumen más
               - Identifica patrones de uso
            
            5. **Aprovecha el caché**: 
               - Ejecutar la misma consulta dos veces usa caché
               - El caché dura 24 horas
               - Las consultas en caché son **gratis** ✅
            
            **Consultas más pesadas en esta app:**
            - 🔴 **Eventos Flatten**: Puede procesar varios GB
            - 🟡 **Atribución Completa (7 modelos)**: Procesa bastantes datos
            - 🟡 **Session Path Analysis**: Depende del volumen
            - 🟢 **Cookies y Ecommerce**: Generalmente ligeras
            
            **Tip Pro:**
            Si una consulta procesa muchos GB, reduce el rango de fechas
            y vuelve a ejecutar. Verás una reducción proporcional en el consumo.
            """)
    
    # Calculadora de costos
    st.markdown("---")
    st.markdown("### 🧮 Calculadora de Costos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        calc_gb = st.number_input(
            "GB a procesar:",
            min_value=0.0,
            max_value=10000.0,
            value=10.0,
            step=0.1,
            key="calc_gb"
        )
    
    with col2:
        calc_cost_usd = calc_gb * 0.005
        st.metric("Costo (USD)", f"${calc_cost_usd:.4f}")
    
    with col3:
        calc_cost_eur = calc_cost_usd * 0.92
        st.metric("Costo (EUR)", f"€{calc_cost_eur:.4f}")
    
    # Comparación de escenarios
    if calc_gb > 0:
        st.info(f"""
        **Comparación de escenarios:**
        - **1 mes** con {calc_gb} GB/día = **{calc_gb * 30:.2f} GB** = **${calc_gb * 30 * 0.005:.2f}** USD
        - **1 año** con {calc_gb} GB/día = **{calc_gb * 365:.2f} GB** = **${calc_gb * 365 * 0.005:.2f}** USD
        
        💡 **Tip**: Los primeros 1024 GB al mes son gratis. Si tu uso diario es {calc_gb} GB:
        - Días gratis: **{1024 / calc_gb:.0f} días** (aprox {1024 / calc_gb / 30:.1f} meses)
        """)
