import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import Settings

def mostrar_retencion_semanal(df):
    """Visualización para Weekly User Retention Analysis"""
    st.subheader("📅 Análisis de Retención Semanal de Usuarios")
    
    if df.empty:
        st.warning("No hay datos de retención semanal para el rango seleccionado")
        return
    
    # Convertir cohort_week a formato legible
    df['cohort_week'] = pd.to_datetime(df['cohort_week'])
    df['cohort_display'] = df['cohort_week'].dt.strftime('%d/%m/%Y')
    
    # Métricas generales
    total_cohorts = len(df)
    avg_week1_retention = df['week_1_retention_pct'].mean()
    avg_week4_retention = df['week_4_retention_pct'].mean()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cohortes Analizadas", f"{total_cohorts}")
    with col2:
        st.metric("Retención Semana 1 (Promedio)", f"{avg_week1_retention:.1f}%")
    with col3:
        st.metric("Retención Semana 4 (Promedio)", f"{avg_week4_retention:.1f}%")
    
    # Tabla de retención
    st.subheader("📊 Tabla de Retención por Cohorte")
    display_df = df[[
        'cohort_display', 'cohort_size', 'week_0_users', 'week_1_users', 
        'week_2_users', 'week_3_users', 'week_4_users',
        'week_1_retention_pct', 'week_2_retention_pct', 
        'week_3_retention_pct', 'week_4_retention_pct'
    ]].copy()
    
    st.dataframe(display_df.style.format({
        'cohort_size': '{:,}',
        'week_0_users': '{:,}',
        'week_1_users': '{:,}',
        'week_2_users': '{:,}',
        'week_3_users': '{:,}',
        'week_4_users': '{:,}',
        'week_1_retention_pct': '{:.2f}%',
        'week_2_retention_pct': '{:.2f}%',
        'week_3_retention_pct': '{:.2f}%',
        'week_4_retention_pct': '{:.2f}%'
    }))
    
    # Gráfico de líneas - Curva de retención promedio
    retention_cols = ['week_1_retention_pct', 'week_2_retention_pct', 
                     'week_3_retention_pct', 'week_4_retention_pct']
    avg_retention = [df[col].mean() for col in retention_cols]
    
    fig_curve = go.Figure()
    fig_curve.add_trace(go.Scatter(
        x=['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4'],
        y=avg_retention,
        mode='lines+markers',
        name='Retención Promedio',
        line=dict(color='blue', width=3),
        marker=dict(size=10)
    ))
    fig_curve.update_layout(
        title='Curva de Retención Promedio',
        xaxis_title='Semana',
        yaxis_title='Tasa de Retención (%)',
        yaxis=dict(range=[0, 100])
    )
    st.plotly_chart(fig_curve, use_container_width=True)
    
    # Heatmap de retención por cohorte
    if len(df) > 1:
        st.subheader("🔥 Heatmap de Retención")
        
        heatmap_data = df[['cohort_display'] + retention_cols].set_index('cohort_display')
        heatmap_data.columns = ['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4']
        
        fig_heatmap = px.imshow(
            heatmap_data.T,
            labels=dict(x="Cohorte", y="Semana", color="Retención (%)"),
            title="Retención por Cohorte y Semana",
            color_continuous_scale='RdYlGn',
            aspect="auto"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Análisis de drop-off
    st.subheader("📉 Análisis de Drop-off")
    avg_drop_week1 = 100 - avg_week1_retention
    avg_drop_week4 = avg_week1_retention - avg_week4_retention
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Drop-off Semana 0→1", f"{avg_drop_week1:.1f}%")
    with col2:
        st.metric("Drop-off Semana 1→4", f"{avg_drop_week4:.1f}%")

def mostrar_clv_sesiones(df):
    """Visualización para Customer Lifetime Value with Sessions"""
    st.subheader("💰 Customer Lifetime Value (CLV) y Sesiones")
    
    if df.empty:
        st.warning("No hay datos de CLV para el rango seleccionado")
        return
    
    # Métricas generales
    total_users = len(df)
    buyers = len(df[df['user_type'] == 'Buyer'])
    non_buyers = len(df[df['user_type'] == 'Non-Buyer'])
    total_clv = df['customer_lifetime_value'].sum()
    avg_clv = df[df['customer_lifetime_value'] > 0]['customer_lifetime_value'].mean()
    avg_sessions = df['total_sessions'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Usuarios", f"{total_users:,}")
    with col2:
        st.metric("Compradores", f"{buyers:,} ({buyers/total_users*100:.1f}%)")
    with col3:
        st.metric("CLV Total", f"€{total_clv:,.2f}")
    with col4:
        st.metric("CLV Promedio (Buyers)", f"€{avg_clv:,.2f}")
    
    # Distribución Buyers vs Non-Buyers
    st.subheader("👥 Distribución de Usuarios")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart
        user_counts = df['user_type'].value_counts()
        fig_pie = px.pie(
            values=user_counts.values,
            names=user_counts.index,
            title='Distribución Buyers vs Non-Buyers',
            color_discrete_map={'Buyer': '#4CAF50', 'Non-Buyer': '#FF9800'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Métricas comparativas
        buyers_df = df[df['user_type'] == 'Buyer']
        non_buyers_df = df[df['user_type'] == 'Non-Buyer']
        
        st.write("**Sesiones Promedio:**")
        st.write(f"- Buyers: {buyers_df['total_sessions'].mean():.1f} sesiones")
        st.write(f"- Non-Buyers: {non_buyers_df['total_sessions'].mean():.1f} sesiones")
        
        st.write("**Revenue por Sesión:**")
        if len(buyers_df) > 0:
            st.write(f"- Buyers: €{buyers_df['revenue_per_session'].mean():.2f}")
    
    # Top usuarios por CLV
    st.subheader("🏆 Top Usuarios por CLV")
    top_users = df.nlargest(20, 'customer_lifetime_value')
    
    fig_top = px.bar(
        top_users.head(20),
        x='user_pseudo_id',
        y='customer_lifetime_value',
        color='total_sessions',
        title='Top 20 Usuarios por CLV',
        labels={
            'customer_lifetime_value': 'CLV (€)',
            'user_pseudo_id': 'Usuario',
            'total_sessions': 'Sesiones'
        },
        color_continuous_scale='Viridis'
    )
    fig_top.update_layout(xaxis_tickangle=-45, showlegend=False)
    st.plotly_chart(fig_top, use_container_width=True)
    
    # Scatter: Sesiones vs CLV
    st.subheader("📊 Relación: Sesiones vs CLV")
    
    buyers_only = df[df['customer_lifetime_value'] > 0]
    fig_scatter = px.scatter(
        buyers_only.head(200),
        x='total_sessions',
        y='customer_lifetime_value',
        size='total_transactions',
        color='revenue_per_session',
        title='Correlación entre Sesiones y CLV (Solo Compradores)',
        labels={
            'total_sessions': 'Total de Sesiones',
            'customer_lifetime_value': 'CLV (€)',
            'total_transactions': 'Transacciones',
            'revenue_per_session': 'Revenue/Sesión'
        },
        color_continuous_scale='Turbo'
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Histograma de distribución de CLV
    st.subheader("📈 Distribución del CLV")
    
    clv_buyers = df[df['customer_lifetime_value'] > 0]['customer_lifetime_value']
    fig_hist = px.histogram(
        clv_buyers,
        x='customer_lifetime_value',
        nbins=50,
        title='Distribución de CLV (Solo Compradores)',
        labels={'customer_lifetime_value': 'CLV (€)'}
    )
    st.plotly_chart(fig_hist, use_container_width=True)

def mostrar_tiempo_primera_compra(df):
    """Visualización para Time from First Visit to Purchase"""
    st.subheader("⏱️ Tiempo desde Primera Visita hasta Compra")
    
    if df.empty:
        st.warning("No hay datos de tiempo a compra para el rango seleccionado")
        return
    
    # Métricas generales
    total_buyers = df['users_with_purchase'].sum()
    overall_avg_days = (df['avg_days_to_purchase'] * df['users_with_purchase']).sum() / total_buyers
    fastest_source = df.loc[df['avg_days_to_purchase'].idxmin()]
    slowest_source = df.loc[df['avg_days_to_purchase'].idxmax()]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Compradores", f"{total_buyers:,}")
    with col2:
        st.metric("Tiempo Promedio Global", f"{overall_avg_days:.1f} días")
    with col3:
        st.metric("Fuente Más Rápida", f"{fastest_source['first_source']} ({fastest_source['avg_days_to_purchase']:.1f}d)")
    
    # Tabla de datos
    st.dataframe(df.style.format({
        'users_with_purchase': '{:,}',
        'avg_days_to_purchase': '{:.2f}',
        'min_days_to_purchase': '{:,}',
        'max_days_to_purchase': '{:,}',
        'median_days_to_purchase': '{:.2f}'
    }))
    
    # Gráfico de barras - Top fuentes por velocidad
    st.subheader("🚀 Top Fuentes por Velocidad de Conversión")
    
    top_fastest = df.nsmallest(15, 'avg_days_to_purchase')
    
    fig_fastest = px.bar(
        top_fastest,
        y='first_source',
        x='avg_days_to_purchase',
        orientation='h',
        color='users_with_purchase',
        title='Top 15 Fuentes Más Rápidas (Menor tiempo a compra)',
        labels={
            'avg_days_to_purchase': 'Días Promedio a Compra',
            'first_source': 'Fuente',
            'users_with_purchase': 'Compradores'
        },
        color_continuous_scale='Greens'
    )
    fig_fastest.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_fastest, use_container_width=True)
    
    # Scatter plot: Volumen vs Velocidad
    st.subheader("📊 Volumen de Compradores vs Velocidad")
    
    fig_scatter = px.scatter(
        df.head(30),
        x='users_with_purchase',
        y='avg_days_to_purchase',
        size='users_with_purchase',
        color='first_medium',
        hover_name='first_source',
        title='Relación entre Volumen y Tiempo de Conversión',
        labels={
            'users_with_purchase': 'Compradores',
            'avg_days_to_purchase': 'Días Promedio a Compra',
            'first_medium': 'Medio'
        },
        size_max=40
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Análisis por medio
    st.subheader("🎯 Análisis por Medio de Adquisición")
    
    medio_stats = df.groupby('first_medium').agg({
        'users_with_purchase': 'sum',
        'avg_days_to_purchase': 'mean'
    }).reset_index().sort_values('users_with_purchase', ascending=False)
    
    fig_medio = px.bar(
        medio_stats.head(10),
        x='first_medium',
        y='users_with_purchase',
        color='avg_days_to_purchase',
        title='Compradores y Tiempo Promedio por Medio',
        labels={
            'first_medium': 'Medio',
            'users_with_purchase': 'Total Compradores',
            'avg_days_to_purchase': 'Días a Compra'
        },
        color_continuous_scale='RdYlGn_r'
    )
    st.plotly_chart(fig_medio, use_container_width=True)
    
    # Insights de velocidad
    st.subheader("💡 Insights Clave")
    
    fast_sources = df[df['avg_days_to_purchase'] < 7]
    slow_sources = df[df['avg_days_to_purchase'] > 30]
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**🚀 Fuentes Rápidas (< 7 días):**")
        st.write(f"- {len(fast_sources)} fuentes")
        st.write(f"- {fast_sources['users_with_purchase'].sum():,} compradores")
    
    with col2:
        st.write("**🐌 Fuentes Lentas (> 30 días):**")
        st.write(f"- {len(slow_sources)} fuentes")
        st.write(f"- {slow_sources['users_with_purchase'].sum():,} compradores")
