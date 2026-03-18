import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import Settings

def mostrar_retencion_semanal(df):
    """Visualización para Weekly User Retention Analysis"""
    st.subheader("Análisis de Retención Semanal de Usuarios")
    
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
    st.subheader("Tabla de Retención por Cohorte")
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
        st.subheader("Heatmap de Retención")
        
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
    st.subheader("Análisis de Drop-off")
    avg_drop_week1 = 100 - avg_week1_retention
    avg_drop_week4 = avg_week1_retention - avg_week4_retention
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Drop-off Semana 0→1", f"{avg_drop_week1:.1f}%")
    with col2:
        st.metric("Drop-off Semana 1→4", f"{avg_drop_week4:.1f}%")

def mostrar_clv_sesiones(df):
    """Visualización para Customer Lifetime Value with Sessions"""
    st.subheader("Customer Lifetime Value (CLV) y Sesiones")
    
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
    st.subheader("Distribución de Usuarios")
    
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
    st.subheader("Top Usuarios por CLV")
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
    st.subheader("Relación: Sesiones vs CLV")
    
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
    st.subheader("Distribución del CLV")
    
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
    st.subheader("Tiempo desde Primera Visita hasta Compra")
    
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
    st.subheader("Top Fuentes por Velocidad de Conversión")
    
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
    st.subheader("Volumen de Compradores vs Velocidad")
    
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
    st.subheader("Análisis por Medio de Adquisición")
    
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
    st.subheader("Insights Clave")
    
    fast_sources = df[df['avg_days_to_purchase'] < 7]
    slow_sources = df[df['avg_days_to_purchase'] > 30]
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Fuentes Rápidas (< 7 días):**")
        st.write(f"- {len(fast_sources)} fuentes")
        st.write(f"- {fast_sources['users_with_purchase'].sum():,} compradores")
    
    with col2:
        st.write("**Fuentes Lentas (> 30 días):**")
        st.write(f"- {len(slow_sources)} fuentes")
        st.write(f"- {slow_sources['users_with_purchase'].sum():,} compradores")

def mostrar_landing_page_attribution(df):
    """Visualización para First Landing Page Attribution"""
    st.subheader("Atribución por Primera Landing Page")
    
    if df.empty:
        st.warning("No hay datos de landing pages para el rango seleccionado")
        return
    
    # Métricas generales
    total_users = df['unique_users'].sum()
    total_revenue = df['total_revenue'].sum()
    total_purchases = df['total_purchases'].sum()
    top_page = df.iloc[0] if len(df) > 0 else None
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Usuarios", f"{total_users:,}")
    with col2:
        st.metric("Total Compras", f"{total_purchases:,}")
    with col3:
        st.metric("Revenue Total", f"€{total_revenue:,.2f}")
    with col4:
        if top_page is not None:
            st.metric("Top Landing Page", f"{top_page['unique_users']:,} usuarios")
    
    # Tabla de datos
    st.dataframe(df.style.format({
        'unique_users': '{:,}',
        'total_page_views': '{:,}',
        'total_view_items': '{:,}',
        'total_add_to_cart': '{:,}',
        'total_begin_checkout': '{:,}',
        'total_purchases': '{:,}',
        'total_revenue': '€{:,.2f}',
        'conversion_rate': '{:.2f}%',
        'revenue_per_user': '€{:.2f}'
    }))
    
    # Top 10 Landing Pages por Revenue
    st.subheader("Top 10 Landing Pages por Revenue")
    
    top_10_revenue = df.head(10)
    
    fig_revenue = px.bar(
        top_10_revenue,
        x='total_revenue',
        y='first_landing_page',
        orientation='h',
        color='conversion_rate',
        title='Top 10 Landing Pages por Revenue',
        labels={
            'total_revenue': 'Revenue Total (€)',
            'first_landing_page': 'Landing Page',
            'conversion_rate': 'Tasa Conversión (%)'
        },
        color_continuous_scale='Viridis'
    )
    fig_revenue.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
    st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Funnel de conversión promedio
    st.subheader("Funnel de Conversión Agregado")
    
    funnel_data = {
        'Etapa': ['Page Views', 'View Items', 'Add to Cart', 'Begin Checkout', 'Purchases'],
        'Total': [
            df['total_page_views'].sum(),
            df['total_view_items'].sum(),
            df['total_add_to_cart'].sum(),
            df['total_begin_checkout'].sum(),
            df['total_purchases'].sum()
        ]
    }
    
    fig_funnel = go.Figure(go.Funnel(
        y=funnel_data['Etapa'],
        x=funnel_data['Total'],
        textinfo="value+percent initial"
    ))
    fig_funnel.update_layout(title='Funnel Agregado de Todas las Landing Pages')
    st.plotly_chart(fig_funnel, use_container_width=True)
    
    # Scatter: Usuarios vs Revenue
    st.subheader("Relación: Volumen de Usuarios vs Revenue")
    
    fig_scatter = px.scatter(
        df.head(30),
        x='unique_users',
        y='total_revenue',
        size='total_purchases',
        color='conversion_rate',
        hover_name='first_landing_page',
        title='Usuarios vs Revenue por Landing Page',
        labels={
            'unique_users': 'Usuarios Únicos',
            'total_revenue': 'Revenue Total (€)',
            'total_purchases': 'Compras',
            'conversion_rate': 'Conversión (%)'
        },
        color_continuous_scale='RdYlGn'
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Botón de análisis con IA
    if st.button("Generar análisis con IA", key="btn_ia_landing_attribution"):
        from utils.llm_insights import generar_insight_tabla
        with st.spinner("Generando con LLM (IA)..."):
            contexto = "Análisis de atribución por primera landing page en GA4. Incluye usuarios únicos, conversiones, revenue y tasas de conversión por página de entrada."
            resultado = generar_insight_tabla(df, contexto=contexto)
            if resultado:
                st.markdown(resultado)
            else:
                st.error("No se pudo generar el análisis. Verifica la API key de Perplexity en secrets.toml.")

def mostrar_adquisicion_usuarios(df):
    """Visualización para User Acquisition by Source/Medium"""
    st.subheader("Adquisición de Usuarios por Fuente y Medio")
    
    if df.empty:
        st.warning("No hay datos de adquisición para el rango seleccionado")
        return
    
    # Métricas generales
    total_users = df['total_users'].sum()
    total_revenue = df['total_revenue'].sum()
    overall_conversion = (df['total_purchases'].sum() / total_users * 100) if total_users > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Usuarios", f"{total_users:,}")
    with col2:
        st.metric("Sesiones Totales", f"{df['total_sessions'].sum():,}")
    with col3:
        st.metric("Revenue Total", f"€{total_revenue:,.2f}")
    with col4:
        st.metric("Conversión Global", f"{overall_conversion:.2f}%")
    
    # Tabla de datos
    st.dataframe(df.style.format({
        'total_users': '{:,}',
        'total_sessions': '{:,}',
        'total_purchases': '{:,}',
        'total_revenue': '€{:,.2f}',
        'avg_sessions_per_user': '{:.2f}',
        'conversion_rate': '{:.2f}%',
        'revenue_per_user': '€{:.2f}'
    }))
    
    # Análisis por Channel Group
    st.subheader("Performance por Channel Group")
    
    channel_stats = df.groupby('channel_group').agg({
        'total_users': 'sum',
        'total_revenue': 'sum',
        'total_purchases': 'sum'
    }).reset_index().sort_values('total_users', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución de usuarios por canal
        fig_pie = px.pie(
            channel_stats,
            values='total_users',
            names='channel_group',
            title='Distribución de Usuarios por Canal',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Revenue por canal
        fig_channel_revenue = px.bar(
            channel_stats,
            x='channel_group',
            y='total_revenue',
            title='Revenue por Channel Group',
            labels={'total_revenue': 'Revenue (€)', 'channel_group': 'Canal'},
            color='total_revenue',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig_channel_revenue, use_container_width=True)
    
    # Top fuentes
    st.subheader("Top Fuentes de Adquisición")
    
    top_sources = df.nlargest(15, 'total_users')
    
    fig_sources = px.bar(
        top_sources,
        x='total_users',
        y='first_source',
        orientation='h',
        color='channel_group',
        title='Top 15 Fuentes por Volumen de Usuarios',
        labels={'total_users': 'Usuarios', 'first_source': 'Fuente'},
        hover_data=['first_medium', 'conversion_rate', 'revenue_per_user']
    )
    fig_sources.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
    st.plotly_chart(fig_sources, use_container_width=True)
    
    # Scatter: Volumen vs Calidad
    st.subheader("Análisis de Volumen vs Calidad")
    
    fig_quality = px.scatter(
        df.head(50),
        x='total_users',
        y='revenue_per_user',
        size='total_revenue',
        color='channel_group',
        hover_name='first_source',
        title='Volumen de Usuarios vs Revenue per User',
        labels={
            'total_users': 'Total Usuarios',
            'revenue_per_user': 'Revenue per User (€)',
            'total_revenue': 'Revenue Total',
            'channel_group': 'Canal'
        },
        size_max=40
    )
    st.plotly_chart(fig_quality, use_container_width=True)

def mostrar_conversion_mensual(df):
    """Visualización para Monthly User Conversion Rate"""
    st.subheader("Tasa de Conversión Mensual de Usuarios")
    
    if df.empty:
        st.warning("No hay datos de conversión mensual para el rango seleccionado")
        return
    
    # Ordenar por mes
    df = df.sort_values('month')
    
    # Convertir el mes a formato datetime para mejor manejo
    df['month_date'] = pd.to_datetime(df['month'] + '-01')
    df['month_display'] = df['month_date'].dt.strftime('%B %Y') # Formato: "Junio 2025"
    
    # Cambiar locale para español (intentar, si falla usar inglés)
    try:
        import locale
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        df['month_display'] = df['month_date'].dt.strftime('%B %Y')
    except:
        # Si falla, usar nombres de meses en español manualmente
        meses_es = {
            'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
            'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
            'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
            'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
        }
        df['month_display'] = df['month_date'].dt.strftime('%B %Y')
        for eng, esp in meses_es.items():
            df['month_display'] = df['month_display'].str.replace(eng, esp)
    
    # Métricas generales
    avg_conversion = df['conversion_rate'].mean()
    best_month_row = df.loc[df['conversion_rate'].idxmax()]
    worst_month_row = df.loc[df['conversion_rate'].idxmin()]
    total_revenue = df['total_revenue'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Conversión Promedio", f"{avg_conversion:.2f}%")
    with col2:
        st.metric("Mejor Mes", f"{best_month_row['month_display']}: {best_month_row['conversion_rate']:.2f}%")
    with col3:
        st.metric("Peor Mes", f"{worst_month_row['month_display']}: {worst_month_row['conversion_rate']:.2f}%")
    with col4:
        st.metric("Revenue Total", f"€{total_revenue:,.2f}")
    
    # Tabla de datos
    display_df = df[['month_display', 'total_users', 'converted_users', 'conversion_rate', 
                      'total_revenue', 'total_transactions', 'avg_revenue_per_converter', 
                      'avg_revenue_per_user']].copy()
    
    st.dataframe(display_df.style.format({
        'total_users': '{:,}',
        'converted_users': '{:,}',
        'conversion_rate': '{:.2f}%',
        'total_revenue': '€{:,.2f}',
        'total_transactions': '{:,}',
        'avg_revenue_per_converter': '€{:.2f}',
        'avg_revenue_per_user': '€{:.2f}'
    }))
    
    # Gráfico de evolución de conversión
    st.subheader("Evolución de la Tasa de Conversión")
    
    fig_conversion = go.Figure()
    fig_conversion.add_trace(go.Scatter(
        x=df['month_display'],
        y=df['conversion_rate'],
        mode='lines+markers',
        name='Tasa de Conversión',
        line=dict(color='blue', width=3),
        marker=dict(size=10)
    ))
    fig_conversion.update_layout(
        title='Evolución de la Tasa de Conversión Mensual',
        xaxis_title='Mes',
        yaxis_title='Tasa de Conversión (%)',
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_conversion, use_container_width=True)
    
    # Comparativa: Usuarios vs Conversores
    st.subheader("Usuarios Totales vs Conversores")
    
    fig_users = go.Figure()
    fig_users.add_trace(go.Bar(
        x=df['month_display'],
        y=df['total_users'],
        name='Total Usuarios',
        marker_color='lightblue'
    ))
    fig_users.add_trace(go.Bar(
        x=df['month_display'],
        y=df['converted_users'],
        name='Usuarios Conversores',
        marker_color='green'
    ))
    fig_users.update_layout(
        title='Comparativa Mensual: Total Usuarios vs Conversores',
        xaxis_title='Mes',
        yaxis_title='Usuarios',
        barmode='group',
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_users, use_container_width=True)
    
    # Revenue analysis
    st.subheader("Análisis de Revenue")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Revenue mensual
        fig_revenue = px.line(
            df,
            x='month_display',
            y='total_revenue',
            title='Revenue Mensual',
            labels={'total_revenue': 'Revenue (€)', 'month_display': 'Mes'},
            markers=True
        )
        fig_revenue.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with col2:
        # Revenue per user
        fig_rpu = px.line(
            df,
            x='month_display',
            y='avg_revenue_per_user',
            title='Revenue Promedio por Usuario',
            labels={'avg_revenue_per_user': 'Revenue/Usuario (€)', 'month_display': 'Mes'},
            markers=True,
            line_shape='spline'
        )
        fig_rpu.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_rpu, use_container_width=True)
