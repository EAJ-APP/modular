import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import Settings

def mostrar_low_converting_sessions(df):
    """Visualización para Low Converting Sessions Analysis"""
    st.subheader("🔍 Análisis de Sesiones con Baja Conversión")
    
    if df.empty:
        st.warning("No hay datos de sesiones sin conversión para el rango seleccionado")
        return
    
    # Métricas generales
    total_sessions = df['total_non_converting_sessions'].sum()
    total_users = df['unique_users'].sum()
    avg_duration = (df['avg_session_duration_seconds'] * df['total_non_converting_sessions']).sum() / total_sessions
    avg_page_views = (df['avg_page_views'] * df['total_non_converting_sessions']).sum() / total_sessions
    avg_bounce = (df['pct_bounced_sessions'] * df['total_non_converting_sessions']).sum() / total_sessions
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Sesiones Sin Conversión", f"{total_sessions:,}")
    with col2:
        st.metric("Usuarios Únicos", f"{total_users:,}")
    with col3:
        st.metric("Duración Media", f"{avg_duration:.0f}s")
    with col4:
        st.metric("Tasa Bounce Media", f"{avg_bounce:.1f}%")
    
    # Mostrar tabla con datos
    st.subheader("📊 Datos Detallados")
    
    # Crear columnas seleccionables para mostrar
    columnas_mostrar = st.multiselect(
        "Seleccionar columnas a mostrar:",
        options=list(df.columns),
        default=['session_source', 'session_medium', 'device_category', 
                 'total_non_converting_sessions', 'avg_page_views', 
                 'avg_session_duration_seconds', 'pct_bounced_sessions']
    )
    
    if columnas_mostrar:
        st.dataframe(df[columnas_mostrar].head(50).style.format({
            'total_non_converting_sessions': '{:,}',
            'unique_users': '{:,}',
            'avg_page_views': '{:.2f}',
            'avg_unique_events': '{:.2f}',
            'avg_session_duration_seconds': '{:.2f}',
            'avg_engagement_time_seconds': '{:.2f}',
            'pct_low_engagement': '{:.2f}%',
            'pct_bounced_sessions': '{:.2f}%'
        }))
    
    # Análisis por fuente de tráfico
    st.subheader("🌐 Análisis por Fuente de Tráfico")
    
    traffic_analysis = df.groupby(['session_source', 'session_medium']).agg({
        'total_non_converting_sessions': 'sum',
        'avg_page_views': 'mean',
        'pct_bounced_sessions': 'mean'
    }).reset_index().sort_values('total_non_converting_sessions', ascending=False).head(15)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras - Top fuentes sin conversión
        fig_sources = px.bar(
            traffic_analysis,
            x='total_non_converting_sessions',
            y='session_source',
            orientation='h',
            color='pct_bounced_sessions',
            title='Top 15 Fuentes con Más Sesiones Sin Conversión',
            labels={
                'total_non_converting_sessions': 'Sesiones',
                'session_source': 'Fuente',
                'pct_bounced_sessions': 'Bounce %'
            },
            color_continuous_scale='Reds'
        )
        fig_sources.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
        st.plotly_chart(fig_sources, use_container_width=True)
    
    with col2:
        # Scatter: Bounce vs Page Views
        fig_scatter = px.scatter(
            traffic_analysis,
            x='avg_page_views',
            y='pct_bounced_sessions',
            size='total_non_converting_sessions',
            color='session_medium',
            hover_name='session_source',
            title='Bounce Rate vs Page Views por Fuente',
            labels={
                'avg_page_views': 'Page Views Promedio',
                'pct_bounced_sessions': 'Bounce Rate (%)',
                'total_non_converting_sessions': 'Sesiones',
                'session_medium': 'Medio'
            }
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Análisis por dispositivo
    st.subheader("📱 Análisis por Dispositivo")
    
    device_analysis = df.groupby('device_category').agg({
        'total_non_converting_sessions': 'sum',
        'avg_session_duration_seconds': 'mean',
        'pct_bounced_sessions': 'mean',
        'avg_page_views': 'mean'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart - Distribución por dispositivo
        fig_device_pie = px.pie(
            device_analysis,
            values='total_non_converting_sessions',
            names='device_category',
            title='Distribución de Sesiones Sin Conversión por Dispositivo',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_device_pie, use_container_width=True)
    
    with col2:
        # Barras agrupadas - Métricas por dispositivo
        fig_device_metrics = go.Figure()
        
        fig_device_metrics.add_trace(go.Bar(
            x=device_analysis['device_category'],
            y=device_analysis['avg_session_duration_seconds'],
            name='Duración (seg)',
            marker_color='lightblue'
        ))
        
        fig_device_metrics.add_trace(go.Bar(
            x=device_analysis['device_category'],
            y=device_analysis['pct_bounced_sessions'],
            name='Bounce Rate (%)',
            marker_color='salmon',
            yaxis='y2'
        ))
        
        fig_device_metrics.update_layout(
            title='Métricas por Tipo de Dispositivo',
            xaxis_title='Dispositivo',
            yaxis=dict(title='Duración Sesión (seg)'),
            yaxis2=dict(title='Bounce Rate (%)', overlaying='y', side='right'),
            barmode='group'
        )
        
        st.plotly_chart(fig_device_metrics, use_container_width=True)
    
    # Análisis de Landing Pages problemáticas
    st.subheader("🚪 Landing Pages con Mayor Tasa de No Conversión")
    
    landing_analysis = df.groupby('landing_page').agg({
        'total_non_converting_sessions': 'sum',
        'avg_page_views': 'mean',
        'pct_bounced_sessions': 'mean',
        'avg_engagement_time_seconds': 'mean'
    }).reset_index().sort_values('total_non_converting_sessions', ascending=False).head(20)
    
    # Acortar URLs para mejor visualización
    landing_analysis['landing_page_short'] = landing_analysis['landing_page'].apply(
        lambda x: x[:50] + '...' if len(str(x)) > 50 else x
    )
    
    fig_landing = px.bar(
        landing_analysis.head(10),
        x='total_non_converting_sessions',
        y='landing_page_short',
        orientation='h',
        color='pct_bounced_sessions',
        title='Top 10 Landing Pages con Más Sesiones Sin Conversión',
        labels={
            'total_non_converting_sessions': 'Sesiones Sin Conversión',
            'landing_page_short': 'Landing Page',
            'pct_bounced_sessions': 'Bounce %'
        },
        color_continuous_scale='Oranges',
        hover_data={'landing_page': True}
    )
    fig_landing.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
    st.plotly_chart(fig_landing, use_container_width=True)
    
    # Análisis geográfico
    st.subheader("🌍 Análisis Geográfico")
    
    geo_analysis = df.groupby(['country', 'city']).agg({
        'total_non_converting_sessions': 'sum',
        'avg_page_views': 'mean',
        'pct_bounced_sessions': 'mean'
    }).reset_index().sort_values('total_non_converting_sessions', ascending=False).head(20)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top países
        country_stats = df.groupby('country').agg({
            'total_non_converting_sessions': 'sum'
        }).reset_index().sort_values('total_non_converting_sessions', ascending=False).head(10)
        
        fig_countries = px.bar(
            country_stats,
            x='country',
            y='total_non_converting_sessions',
            title='Top 10 Países con Sesiones Sin Conversión',
            labels={
                'country': 'País',
                'total_non_converting_sessions': 'Sesiones'
            },
            color='total_non_converting_sessions',
            color_continuous_scale='Reds'
        )
        fig_countries.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_countries, use_container_width=True)
    
    with col2:
        # Tabla de ciudades
        st.write("**Top 15 Ciudades:**")
        st.dataframe(geo_analysis.head(15).style.format({
            'total_non_converting_sessions': '{:,}',
            'avg_page_views': '{:.2f}',
            'pct_bounced_sessions': '{:.2f}%'
        }))
    
    # Insights y recomendaciones
    st.subheader("💡 Insights Clave")
    
    # Identificar problemas
    high_bounce = df[df['pct_bounced_sessions'] > 70].nlargest(5, 'total_non_converting_sessions')
    low_engagement = df[df['pct_low_engagement'] > 70].nlargest(5, 'total_non_converting_sessions')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🚨 Fuentes con Mayor Bounce Rate (>70%):**")
        if not high_bounce.empty:
            for _, row in high_bounce.iterrows():
                st.write(f"- **{row['session_source']}** / {row['session_medium']}: {row['pct_bounced_sessions']:.1f}% bounce ({row['total_non_converting_sessions']:,} sesiones)")
        else:
            st.write("✅ No hay fuentes con bounce rate crítico")
    
    with col2:
        st.write("**⏱️ Fuentes con Bajo Engagement (>70%):**")
        if not low_engagement.empty:
            for _, row in low_engagement.iterrows():
                st.write(f"- **{row['session_source']}** / {row['session_medium']}: {row['pct_low_engagement']:.1f}% bajo engagement")
        else:
            st.write("✅ No hay fuentes con engagement crítico")
    
    # Botón de descarga
    if st.button("📥 Descargar Datos CSV", key="download_low_converting"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name="low_converting_sessions.csv",
            mime="text/csv"
        )
