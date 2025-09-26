import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import Settings

def mostrar_consentimiento_basico(df):
    """Visualización para consulta básica de consentimiento con porcentajes"""
    st.subheader("📋 Datos Crudos")
    
    # Calcular totales para porcentajes
    total_eventos = df['total_events'].sum()
    total_usuarios = df['total_users'].sum()
    total_sesiones = df['total_sessions'].sum()
    
    # Crear copia del DataFrame para no modificar el original
    df_mostrar = df.copy()
    
    # Calcular porcentajes
    df_mostrar['% eventos'] = (df_mostrar['total_events'] / total_eventos * 100).round(2).astype(str) + '%'
    df_mostrar['% usuarios'] = (df_mostrar['total_users'] / total_usuarios * 100).round(2).astype(str) + '%'
    df_mostrar['% sesiones'] = (df_mostrar['total_sessions'] / total_sesiones * 100).round(2).astype(str) + '%'
    
    # Reordenar columnas
    columnas = ['analytics_storage_status', 'ads_storage_status', 
                'total_events', '% eventos',
                'total_users', '% usuarios',
                'total_sessions', '% sesiones']
    
    st.dataframe(df_mostrar[columnas].style.format({
        'total_events': '{:,}',
        'total_users': '{:,}',
        'total_sessions': '{:,}'
    }))
    
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.pie(df, names='analytics_storage_status', 
                     values='total_events', title='Eventos por Consentimiento Analytics')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = px.bar(df, x='ads_storage_status', y='total_users',
                     title='Usuarios Únicos por Consentimiento Ads')
        st.plotly_chart(fig2, use_container_width=True)

def mostrar_consentimiento_por_dispositivo(df):
    """Visualización corregida que muestra datos diferentes en cada pestaña"""
    st.subheader("📱 Consentimiento por Dispositivo (Detallado)")
    
    if df.empty:
        st.warning("No hay datos disponibles para el rango seleccionado")
        return
    
    # Preprocesamiento
    df['device_type'] = df['device_type'].str.capitalize()
    consent_map = Settings.CONSENT_MAPPING
    
    # Orden de dispositivos por eventos totales
    device_order = df.groupby('device_type')['total_events'].sum().sort_values(ascending=False).index
    
    tab1, tab2 = st.tabs(["Analytics Storage", "Ads Storage"])
    
    with tab1:
        df_analytics = df[['device_type', 'analytics_status', 'total_events']].copy()
        df_analytics['consent_status'] = df_analytics['analytics_status'].map(consent_map)
        
        df_analytics_grouped = df_analytics.groupby(['device_type', 'consent_status'])['total_events'].sum().reset_index()
        
        fig_analytics = px.bar(
            df_analytics_grouped,
            x='device_type',
            y='total_events',
            color='consent_status',
            category_orders={"device_type": list(device_order)},
            barmode='stack',
            title='Consentimiento Analytics por Dispositivo',
            labels={'device_type': 'Dispositivo', 'total_events': 'Eventos'},
            color_discrete_map={
                'Consentido': Settings.CHART_COLORS['success'],
                'No Consentido': Settings.CHART_COLORS['error'],
                'No Definido': Settings.CHART_COLORS['secondary']
            }
        )
        st.plotly_chart(fig_analytics, use_container_width=True)
        
        st.dataframe(df_analytics_grouped.pivot(index='device_type', columns='consent_status', values='total_events'))
    
    with tab2:
        df_ads = df[['device_type', 'ads_status', 'total_events']].copy()
        df_ads['consent_status'] = df_ads['ads_status'].map(consent_map)
        
        df_ads_grouped = df_ads.groupby(['device_type', 'consent_status'])['total_events'].sum().reset_index()
        
        fig_ads = px.bar(
            df_ads_grouped,
            x='device_type',
            y='total_events',
            color='consent_status',
            category_orders={"device_type": list(device_order)},
            barmode='stack',
            title='Consentimiento Ads por Dispositivo',
            labels={'device_type': 'Dispositivo', 'total_events': 'Eventos'},
            color_discrete_map={
                'Consentido': Settings.CHART_COLORS['success'],
                'No Consentido': Settings.CHART_COLORS['error'],
                'No Definido': Settings.CHART_COLORS['secondary']
            }
        )
        st.plotly_chart(fig_ads, use_container_width=True)
        
        st.dataframe(df_ads_grouped.pivot(index='device_type', columns='consent_status', values='total_events'))
    
    # Estadísticas comparativas
    st.subheader("📊 Comparativa de Consentimientos")
    col1, col2 = st.columns(2)
    
    with col1:
        analytics_true = df[df['analytics_status'] == 'true']['total_events'].sum()
        st.metric("Eventos con Consentimiento Analytics", f"{analytics_true:,}")
    
    with col2:
        ads_true = df[df['ads_status'] == 'true']['total_events'].sum()
        st.metric("Eventos con Consentimiento Ads", f"{ads_true:,}")

def mostrar_consentimiento_real(df):
    """Nueva visualización para porcentaje real de consentimiento"""
    st.subheader("🔍 Porcentaje Real de Consentimiento (Todos los Eventos)")
    
    # Mapeo de estados a colores
    status_colors = {
        'Aceptado': Settings.CHART_COLORS['success'],
        'Denegado': Settings.CHART_COLORS['error'],
        'No Definido': Settings.CHART_COLORS['warning']
    }
    
    # Gráfico de torta
    fig = px.pie(df, 
                 names='consent_status', 
                 values='total_events',
                 color='consent_status',
                 color_discrete_map=status_colors,
                 title='Distribución Real del Consentimiento')
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar tabla con datos crudos
    st.dataframe(df.style.format({
        'total_events': '{:,}',
        'event_percentage': '{:.2f}%'
    }))
    
    # Calcular y mostrar el % de eventos SIN consentimiento (Denegado + No Definido)
    denied_pct = df[df['consent_status'].isin(['Denegado', 'No Definido'])]['event_percentage'].sum()
    st.metric("📉 Eventos sin consentimiento (Real)", f"{denied_pct:.2f}%")