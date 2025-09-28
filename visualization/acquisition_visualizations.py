import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import Settings
from utils.helpers import safe_divide

def mostrar_canales_trafico(df):
    """Visualización para análisis de canales de tráfico"""
    st.subheader("📊 Distribución de Canales de Tráfico")
    
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
    st.subheader("📈 Análisis de Concentración")
    
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
        st.info("🚀 **Canales Emergentes** (menos del 1% pero con potencial):")
        for _, channel in emerging_channels.iterrows():
            st.write(f"- **{channel['traffic_channel']}**: {channel['session_count']} sesiones ({channel['traffic_percentage']}%)")

def mostrar_atribucion_marketing(df):
    """Visualización para análisis de atribución de marketing"""
    st.subheader("🎯 Atribución de Marketing por Canal UTM")
    
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
    st.subheader("📊 Análisis por Medio de Marketing")
    
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
    st.subheader("🏆 Top Campañas por Performance")
    
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
    st.subheader("📈 Eficiencia de Canales")
    
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
