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
