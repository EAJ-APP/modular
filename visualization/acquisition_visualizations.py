import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import Settings
from utils.helpers import safe_divide

def mostrar_canales_trafico(df):
    """Visualización para análisis de canales de tráfico"""
    st.subheader("Distribución de Canales de Tráfico")
    
    if df.empty:
        st.warning("No hay datos de tráfico para el rango seleccionado")
        return
    
    # Mostrar tabla con datos crudos
    st.dataframe(df.style.format({
        'session_count': '{:,}',
        'traffic_percentage': '{:.2f}%'
    }))
    
    # Calcular métricas generales
    total_sessions = df['session_count'].sum()
    unique_channels = len(df)
    
    # Mostrar métricas clave
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sesiones", f"{total_sessions:,}")
    with col2:
        st.metric("Canales Únicos", f"{unique_channels}")
    with col3:
        top_channel = df.iloc[0]['traffic_channel'] if not df.empty else "N/A"
        top_percentage = df.iloc[0]['traffic_percentage'] if not df.empty else 0
        st.metric("Canal Principal", f"{top_channel} ({top_percentage}%)")
    
    # Gráfico de torta - Distribución de canales
    fig_pie = px.pie(
        df, 
        names='traffic_channel', 
        values='session_count',
        title='Distribución de Sesiones por Canal de Tráfico',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Gráfico de barras horizontal - Ordenado por sesiones
    fig_bar = px.bar(
        df,
        y='traffic_channel',
        x='session_count',
        orientation='h',
        title='Sesiones por Canal de Tráfico',
        labels={'session_count': 'Número de Sesiones', 'traffic_channel': 'Canal'},
        color='session_count',
        color_continuous_scale='Blues'
    )
    fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Análisis de concentración
    st.subheader("Análisis de Concentración")
    
    # Calcular concentración (Top 5 canales)
    top_5_percentage = df.head(5)['traffic_percentage'].sum()
    top_3_percentage = df.head(3)['traffic_percentage'].sum()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Top 3 Canales", f"{top_3_percentage:.1f}%")
    with col2:
        st.metric("Top 5 Canales", f"{top_5_percentage:.1f}%")
    
    # Detectar canales emergentes (menos del 1% pero presentes)
    emerging_channels = df[df['traffic_percentage'] < 1.0]
    if not emerging_channels.empty:
        st.info("**Canales Emergentes** (menos del 1% pero con potencial):")
        for _, channel in emerging_channels.iterrows():
            st.write(f"- **{channel['traffic_channel']}**: {channel['session_count']} sesiones ({channel['traffic_percentage']}%)")

def mostrar_atribucion_marketing(df):
    """Visualización para análisis de atribución de marketing"""
    st.subheader("Atribución de Marketing por Canal UTM")
    
    if df.empty:
        st.warning("No hay datos de atribución para el rango seleccionado")
        return
    
    # Mostrar resumen ejecutivo
    total_sessions = df['sessions'].sum()
    total_conversions = df['conversions'].sum()
    total_revenue = df['revenue'].sum()
    overall_cr = (total_conversions / total_sessions * 100) if total_sessions > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sesiones", f"{total_sessions:,}")
    with col2:
        st.metric("Total Conversiones", f"{total_conversions:,}")
    with col3:
        st.metric("Ingresos Totales", f"€{total_revenue:,.2f}")
    with col4:
        st.metric("Tasa Conversión", f"{overall_cr:.2f}%")
    
    # Mostrar tabla de datos
    st.dataframe(df.style.format({
        'sessions': '{:,}',
        'conversions': '{:,}',
        'revenue': '€{:,.2f}',
        'conversion_rate': '{:.2f}%'
    }))
    
    # Análisis por medio
    st.subheader("Análisis por Medio de Marketing")
    
    medios_df = df.groupby('utm_medium').agg({
        'sessions': 'sum',
        'conversions': 'sum',
        'revenue': 'sum'
    }).reset_index()
    
    medios_df['conversion_rate'] = (medios_df['conversions'] / medios_df['sessions'] * 100).round(2)
    medios_df = medios_df.sort_values('revenue', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de ingresos por medio
        fig_ingresos = px.bar(
            medios_df,
            x='utm_medium',
            y='revenue',
            title='Ingresos por Medio de Marketing',
            labels={'utm_medium': 'Medio', 'revenue': 'Ingresos (€)'},
            color='revenue',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_ingresos, use_container_width=True)
    
    with col2:
        # Gráfico de tasas de conversión
        fig_conversion = px.bar(
            medios_df,
            x='utm_medium',
            y='conversion_rate',
            title='Tasa de Conversión por Medio',
            labels={'utm_medium': 'Medio', 'conversion_rate': 'Tasa (%)'},
            color='conversion_rate',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_conversion, use_container_width=True)
    
    # Top campañas por ROI
    st.subheader("Top Campañas por Performance")
    
    top_campanas = df.nlargest(10, 'revenue')
    
    fig_campanas = px.scatter(
        top_campanas,
        x='conversions',
        y='revenue',
        size='sessions',
        color='utm_medium',
        hover_name='utm_campaign',
        title='Performance de Campañas: Conversiones vs Ingresos',
        labels={
            'conversions': 'Conversiones',
            'revenue': 'Ingresos (€)',
            'sessions': 'Sesiones',
            'utm_medium': 'Medio'
        },
        size_max=30
    )
    st.plotly_chart(fig_campanas, use_container_width=True)
    
    # Análisis de eficiencia
    st.subheader("Eficiencia de Canales")
    
    # Calcular ROI aproximado (ingresos por sesión)
    df['revenue_per_session'] = (df['revenue'] / df['sessions']).round(2)
    
    eficiencia_df = df.nlargest(15, 'revenue_per_session')
    
    fig_eficiencia = px.bar(
        eficiencia_df,
        x='utm_source',
        y='revenue_per_session',
        color='utm_medium',
        title='Ingresos por Sesión por Fuente (Top 15)',
        labels={'utm_source': 'Fuente', 'revenue_per_session': 'Ingresos por Sesión (€)'}
    )
    fig_eficiencia.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_eficiencia, use_container_width=True)

    # Botón de análisis con IA
    if st.button("Generar análisis con IA", key="btn_ia_atribucion_marketing"):
        from utils.llm_insights import generar_insight_tabla
        with st.spinner("Generando con LLM (IA)..."):
            contexto = "Análisis de atribución de marketing por canal UTM en GA4. Incluye sesiones, conversiones, ingresos y tasas de conversión por fuente y medio."
            resultado = generar_insight_tabla(df, contexto=contexto)
            if resultado:
                st.markdown(resultado)
            else:
                st.error("No se pudo generar el análisis. Verifica la API key de Perplexity en secrets.toml.")

def mostrar_atribucion_multimodelo(df):
    """Visualización para análisis de atribución multi-modelo"""
    st.subheader("Atribución Multi-Modelo")
    
    if df.empty:
        st.warning("No hay datos de atribución multi-modelo para el rango seleccionado")
        return
    
    # Mostrar resumen por modelo
    st.subheader("Resumen por Modelo de Atribución")
    
    model_summary = df.groupby('attribution_model').agg({
        'sessions': 'sum',
        'conversions': 'sum',
        'revenue': 'sum',
        'attributed_conversions': 'sum',
        'attributed_revenue': 'sum'
    }).reset_index()
    
    # Métricas comparativas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_revenue = df['revenue'].sum() / 3 # Dividido por 3 modelos para evitar duplicación
        st.metric("Ingresos Totales", f"€{total_revenue:,.2f}")
    with col2:
        total_conversions = df['conversions'].sum() / 3
        st.metric("Conversiones Totales", f"{total_conversions:,.0f}")
    with col3:
        avg_attribution_rate = model_summary['attributed_conversions'].mean()
        st.metric("Tasa Atribución Promedio", f"{avg_attribution_rate:.1f}%")
    with col4:
        models_count = len(model_summary)
        st.metric("Modelos Analizados", f"{models_count}")
    
    # Gráfico comparativo entre modelos
    st.subheader("Comparativa entre Modelos")
    
    fig_comparison = px.bar(
        model_summary,
        x='attribution_model',
        y='attributed_revenue',
        title='Ingresos Atribuidos por Modelo',
        labels={'attribution_model': 'Modelo', 'attributed_revenue': 'Ingresos Atribuidos (€)'},
        color='attribution_model',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Análisis detallado por modelo
    st.subheader("Análisis Detallado por Modelo")
    
    for model in df['attribution_model'].unique():
        with st.expander(f"Modelo: {model}", expanded=False):
            model_data = df[df['attribution_model'] == model].nlargest(10, 'attributed_revenue')
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top canales por ingresos atribuidos
                fig_channels = px.bar(
                    model_data,
                    x='utm_source',
                    y='attributed_revenue',
                    title=f'Top Canales - {model}',
                    labels={'utm_source': 'Fuente', 'attributed_revenue': 'Ingresos Atribuidos (€)'},
                    color='utm_medium'
                )
                st.plotly_chart(fig_channels, use_container_width=True)
            
            with col2:
                # Scatter plot: sesiones vs conversiones atribuidas
                fig_scatter = px.scatter(
                    model_data,
                    x='sessions',
                    y='attributed_conversions',
                    size='attributed_revenue',
                    color='utm_medium',
                    hover_name='utm_campaign',
                    title=f'Eficiencia - {model}',
                    labels={
                        'sessions': 'Sesiones',
                        'attributed_conversions': 'Conversiones Atribuidas',
                        'attributed_revenue': 'Ingresos Atribuidos'
                    }
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Mostrar tabla detallada
            st.dataframe(model_data.style.format({
                'sessions': '{:,}',
                'conversions': '{:,}',
                'revenue': '€{:,.2f}',
                'attributed_conversions': '{:.2f}',
                'attributed_revenue': '€{:,.2f}',
                'attribution_rate': '{:.2f}%'
            }))
    
    # Análisis de diferencias entre modelos
    st.subheader("Diferencias entre Modelos")
    
    # Pivot para comparar modelos
    pivot_df = df.pivot_table(
        index=['utm_source', 'utm_medium'],
        columns='attribution_model',
        values='attributed_revenue',
        aggfunc='sum'
    ).reset_index().fillna(0)
    
    if len(pivot_df) > 0:
        # Calcular variación entre modelos
        if 'Last Click' in pivot_df.columns and 'First Click' in pivot_df.columns:
            pivot_df['diferencia_lc_fc'] = pivot_df['Last Click'] - pivot_df['First Click']
            
            st.write("**Canales con Mayor Diferencia entre Last Click y First Click:**")
            top_differences = pivot_df.nlargest(5, 'diferencia_lc_fc')
            st.dataframe(top_differences.style.format({
                'Last Click': '€{:,.2f}',
                'First Click': '€{:,.2f}',
                'Linear': '€{:,.2f}',
                'diferencia_lc_fc': '€{:,.2f}'
            }))

# REEMPLAZAR solo la función mostrar_atribucion_completa en acquisition_visualizations.py

def mostrar_atribucion_completa(df):
    """Visualización para análisis de atribución completa (7 modelos)"""
    st.subheader("Atribución Multi-Modelo Completa (7 Modelos)")
    
    if df.empty:
        st.warning("No hay datos de atribución completa para el rango seleccionado")
        return
    
    # Información sobre los modelos
    with st.expander("Información sobre los Modelos de Atribución", expanded=False):
        st.markdown("""
        **7 Modelos Implementados:**

        - **Last Click**: Atribuye el 100% al ultimo touchpoint antes de la conversion
        - **First Click**: Atribuye el 100% al primer touchpoint del usuario
        - **Linear**: Distribuye equitativamente entre todos los touchpoints
        - **Time Decay**: Mayor peso a los touchpoints mas recientes
        - **Position Based**: 40% primer click, 40% ultimo click, 20% intermedios
        - **Last Non-Direct**: Como Last Click pero ignora trafico directo
        - **Data Driven**: Combinacion algoritmica de multiples factores
        """)
    
    # Resumen ejecutivo
    st.subheader("Resumen Ejecutivo")
    
    total_models = df['attribution_model'].nunique()
    total_channels = df['utm_source'].nunique()
    
    # Calcular valores únicos por modelo
    model_summary = df.groupby('attribution_model').agg({
        'attributed_revenue': 'sum',
        'attributed_conversions': 'sum'
    }).reset_index()
    
    total_revenue = model_summary['attributed_revenue'].sum()
    total_conversions = model_summary['attributed_conversions'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Modelos de Atribución", total_models)
    with col2:
        st.metric("Canales Únicos", total_channels)
    with col3:
        st.metric("Ingresos Atribuidos", f"€{total_revenue:,.0f}")
    with col4:
        st.metric("Conversiones Atribuidas", f"{total_conversions:,.0f}")
    
    # Mostrar los modelos realmente detectados
    st.write(f"**Modelos analizados:** {', '.join(df['attribution_model'].unique())}")
    
    # Comparativa entre modelos
    st.subheader("Comparativa entre Modelos")
    
    model_comparison = df.groupby('attribution_model').agg({
        'attributed_revenue': 'sum',
        'attributed_conversions': 'sum',
        'conversion_rate': 'mean',
        'revenue_per_conversion': 'mean'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_revenue = px.bar(
            model_comparison,
            x='attribution_model',
            y='attributed_revenue',
            title='Ingresos Atribuidos por Modelo',
            labels={'attribution_model': 'Modelo', 'attributed_revenue': 'Ingresos (€)'},
            color='attributed_revenue',
            color_continuous_scale='Viridis'
        )
        fig_revenue.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with col2:
        fig_conversions = px.bar(
            model_comparison,
            x='attribution_model',
            y='attributed_conversions',
            title='Conversiones Atribuidas por Modelo',
            labels={'attribution_model': 'Modelo', 'attributed_conversions': 'Conversiones'},
            color='attributed_conversions',
            color_continuous_scale='Blues'
        )
        fig_conversions.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_conversions, use_container_width=True)
    
    # Análisis de diferencias entre modelos
    st.subheader("Análisis de Diferencias entre Modelos")
    
    # Pivot para comparación
    pivot_data = df.pivot_table(
        index=['utm_source', 'utm_medium'],
        columns='attribution_model',
        values='attributed_revenue',
        aggfunc='sum'
    ).fillna(0)
    
    if not pivot_data.empty:
        # Calcular desviación estándar entre modelos (variabilidad)
        pivot_data['std_deviation'] = pivot_data.std(axis=1)
        pivot_data['mean_revenue'] = pivot_data.mean(axis=1)
        pivot_data['variability'] = (pivot_data['std_deviation'] / pivot_data['mean_revenue']).round(3)
        
        st.write("**Canales con Mayor Variabilidad entre Modelos:**")
        high_variability = pivot_data.nlargest(10, 'variability')
        st.dataframe(high_variability[['mean_revenue', 'std_deviation', 'variability']].style.format({
            'mean_revenue': '€{:,.2f}',
            'std_deviation': '€{:,.2f}',
            'variability': '{:.3f}'
        }))
    
    # SOLUCIÓN DEFINITIVA: Usar on_change callback en lugar de monitorear cambios
    st.subheader("Análisis Detallado por Modelo")
    
    # Key único para el selectbox de esta función
    selectbox_key = 'attribution_complete_model_selector'
    
    # Inicializar session_state si no existe
    if selectbox_key not in st.session_state:
        st.session_state[selectbox_key] = df['attribution_model'].unique()[0] if len(df['attribution_model'].unique()) > 0 else ""
    
    # Función callback que se ejecuta ANTES del rerun
    def on_model_change():
        # Este callback se ejecuta antes del rerun, manteniendo el contexto
        pass
    
    # Selectbox con callback
    selected_model = st.selectbox(
        "Seleccionar modelo para análisis detallado:",
        options=list(df['attribution_model'].unique()),
        index=list(df['attribution_model'].unique()).index(st.session_state[selectbox_key]) if st.session_state[selectbox_key] in df['attribution_model'].unique() else 0,
        key=selectbox_key,
        on_change=on_model_change
    )
    
    if selected_model:
        model_data = df[df['attribution_model'] == selected_model].nlargest(15, 'attributed_revenue')
        
        if not model_data.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top canales por ingresos
                fig_top_channels = px.treemap(
                    model_data,
                    path=['utm_source', 'utm_medium'],
                    values='attributed_revenue',
                    title=f'Distribución de Ingresos - {selected_model}',
                    color='attributed_revenue',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_top_channels, use_container_width=True)
            
            with col2:
                # Eficiencia por canal
                fig_efficiency = px.scatter(
                    model_data.head(20),
                    x='touchpoints',
                    y='attributed_revenue',
                    size='conversion_rate',
                    color='utm_medium',
                    hover_name='utm_source',
                    title=f'Eficiencia por Canal - {selected_model}',
                    labels={
                        'touchpoints': 'Touchpoints',
                        'attributed_revenue': 'Ingresos Atribuidos (€)',
                        'conversion_rate': 'Tasa Conversión'
                    }
                )
                st.plotly_chart(fig_efficiency, use_container_width=True)
            
            # Tabla detallada
            st.dataframe(model_data.style.format({
                'touchpoints': '{:,}',
                'conversions': '{:,}',
                'revenue': '€{:,.2f}',
                'attributed_conversions': '{:.2f}',
                'attributed_revenue': '€{:,.2f}',
                'conversion_rate': '{:.2f}%',
                'revenue_per_conversion': '€{:,.2f}'
            }))
        else:
            st.warning(f"No hay datos para el modelo {selected_model}")
    
    # Análisis por dispositivo
    st.subheader("Análisis por Dispositivo")
    
    device_analysis = df.groupby(['attribution_model', 'device_type']).agg({
        'attributed_revenue': 'sum',
        'attributed_conversions': 'sum'
    }).reset_index()
    
    if not device_analysis.empty:
        fig_device = px.bar(
            device_analysis,
            x='attribution_model',
            y='attributed_revenue',
            color='device_type',
            barmode='group',
            title='Ingresos Atribuidos por Modelo y Dispositivo',
            labels={'attribution_model': 'Modelo', 'attributed_revenue': 'Ingresos (€)'}
        )
        fig_device.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_device, use_container_width=True)
