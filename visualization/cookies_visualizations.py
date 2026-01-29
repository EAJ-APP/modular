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

def mostrar_evolucion_temporal_consentimiento(df):
    """Visualización para evolución temporal del consentimiento"""
    st.subheader("📈 Evolución Temporal del Consentimiento")
    
    if df.empty:
        st.warning("No hay datos de evolución temporal para el rango seleccionado")
        return
    
    # Convertir fecha
    df['date'] = pd.to_datetime(df['date'])
    df['date_display'] = df['date'].dt.strftime('%d/%m/%Y')
    
    # Métricas generales del período
    avg_analytics_consent = df['analytics_granted_pct'].mean()
    avg_ads_consent = df['ads_granted_pct'].mean()
    avg_full_consent = df['full_consent_pct'].mean()
    
    # Tendencia (primera vs última semana)
    first_week = df.head(7)['analytics_granted_pct'].mean()
    last_week = df.tail(7)['analytics_granted_pct'].mean()
    trend = last_week - first_week
    
    # Mostrar métricas clave
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Analytics Consent (Promedio)", f"{avg_analytics_consent:.1f}%")
    with col2:
        st.metric("Ads Consent (Promedio)", f"{avg_ads_consent:.1f}%")
    with col3:
        st.metric("Consentimiento Completo", f"{avg_full_consent:.1f}%")
    with col4:
        st.metric("Tendencia (7 días)", f"{trend:+.1f}%", 
                 delta_color="normal" if trend >= 0 else "inverse")
    
    # Gráfico principal: Evolución de tasas de consentimiento
    st.subheader("📊 Tasas de Consentimiento por Día")
    
    fig_evolution = go.Figure()
    
    # Analytics Storage
    fig_evolution.add_trace(go.Scatter(
        x=df['date_display'],
        y=df['analytics_granted_pct'],
        name='Analytics Aceptado',
        mode='lines+markers',
        line=dict(color='#4CAF50', width=3),
        marker=dict(size=6),
        hovertemplate='%{x}<br>Analytics: %{y:.2f}%<extra></extra>'
    ))
    
    # Ads Storage
    fig_evolution.add_trace(go.Scatter(
        x=df['date_display'],
        y=df['ads_granted_pct'],
        name='Ads Aceptado',
        mode='lines+markers',
        line=dict(color='#2196F3', width=3),
        marker=dict(size=6),
        hovertemplate='%{x}<br>Ads: %{y:.2f}%<extra></extra>'
    ))
    
    # Consentimiento completo
    fig_evolution.add_trace(go.Scatter(
        x=df['date_display'],
        y=df['full_consent_pct'],
        name='Consentimiento Completo',
        mode='lines+markers',
        line=dict(color='#FF9800', width=2, dash='dash'),
        marker=dict(size=5),
        hovertemplate='%{x}<br>Completo: %{y:.2f}%<extra></extra>'
    ))
    
    fig_evolution.update_layout(
        title='Evolución de Tasas de Consentimiento',
        xaxis_title='Fecha',
        yaxis_title='Tasa de Consentimiento (%)',
        yaxis=dict(range=[0, 100]),
        hovermode='x unified',
        height=500,
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig_evolution, use_container_width=True)
    
    # Gráfico secundario: Volumen de eventos
    st.subheader("📊 Volumen de Eventos por Día")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Eventos totales
        fig_volume = px.bar(
            df,
            x='date_display',
            y='total_events',
            title='Total de Eventos por Día',
            labels={'total_events': 'Eventos', 'date_display': 'Fecha'},
            color='total_events',
            color_continuous_scale='Blues'
        )
        fig_volume.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig_volume, use_container_width=True)
    
    with col2:
        # Usuarios únicos
        fig_users = px.line(
            df,
            x='date_display',
            y='unique_users',
            title='Usuarios Únicos por Día',
            labels={'unique_users': 'Usuarios', 'date_display': 'Fecha'},
            markers=True
        )
        fig_users.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_users, use_container_width=True)
    
    # Análisis comparativo: Analytics vs Ads
    st.subheader("🔄 Comparativa: Analytics vs Ads Storage")
    
    # Calcular diferencia
    df['consent_gap'] = df['analytics_granted_pct'] - df['ads_granted_pct']
    avg_gap = df['consent_gap'].mean()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Gráfico de brecha
        fig_gap = go.Figure()
        
        fig_gap.add_trace(go.Bar(
            x=df['date_display'],
            y=df['consent_gap'],
            name='Diferencia',
            marker_color=df['consent_gap'].apply(
                lambda x: '#4CAF50' if x >= 0 else '#F44336'
            ),
            hovertemplate='%{x}<br>Gap: %{y:.2f}%<extra></extra>'
        ))
        
        # Línea de promedio
        fig_gap.add_hline(
            y=avg_gap,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"Promedio: {avg_gap:.1f}%"
        )
        
        fig_gap.update_layout(
            title='Brecha entre Analytics y Ads Consent (Analytics - Ads)',
            xaxis_title='Fecha',
            yaxis_title='Diferencia (%)',
            xaxis_tickangle=-45,
            height=400
        )
        
        st.plotly_chart(fig_gap, use_container_width=True)
    
    with col2:
        st.write("**Interpretación de la brecha:**")
        if avg_gap > 5:
            st.success(f"✅ Los usuarios aceptan más **Analytics** que **Ads** (+{avg_gap:.1f}%)")
            st.info("📊 Esto es típico: los usuarios confían más en analytics que en publicidad")
        elif avg_gap < -5:
            st.warning(f"⚠️ Los usuarios aceptan más **Ads** que **Analytics** ({avg_gap:.1f}%)")
            st.info("🔍 Esto es inusual. Verifica la configuración del banner")
        else:
            st.info(f"➡️ Ambas tasas son similares (diferencia: {avg_gap:.1f}%)")
    
    # Tabla de datos detallada
    st.subheader("📋 Datos Detallados")
    
    display_df = df[[
        'date_display', 'total_events', 'unique_users', 'unique_sessions',
        'analytics_granted_pct', 'analytics_denied_pct', 'analytics_undefined_pct',
        'ads_granted_pct', 'ads_denied_pct', 'ads_undefined_pct',
        'full_consent_pct'
    ]].copy()
    
    st.dataframe(display_df.style.format({
        'total_events': '{:,}',
        'unique_users': '{:,}',
        'unique_sessions': '{:,}',
        'analytics_granted_pct': '{:.2f}%',
        'analytics_denied_pct': '{:.2f}%',
        'analytics_undefined_pct': '{:.2f}%',
        'ads_granted_pct': '{:.2f}%',
        'ads_denied_pct': '{:.2f}%',
        'ads_undefined_pct': '{:.2f}%',
        'full_consent_pct': '{:.2f}%'
    }), height=400)

    # Botón de análisis con IA
    if st.button("🤖 Generar análisis con IA", key="btn_ia_evolucion"):
        from utils.llm_insights import generar_insight_tabla
        with st.spinner("Analizando datos con Claude..."):
            resultado = generar_insight_tabla(
                display_df,
                contexto="Evolución temporal diaria del consentimiento de cookies (GDPR) en un sitio web. "
                         "Los porcentajes indican qué proporción de eventos tienen consentimiento concedido, "
                         "denegado o sin definir, tanto para Analytics como para Ads."
            )
            if resultado:
                st.markdown("---")
                st.markdown("### 🤖 Análisis generado por IA")
                st.markdown(resultado)
                st.markdown("---")
            else:
                st.error("No se pudo generar el análisis. Verifica la API key de Anthropic en secrets.toml.")

    # Insights clave
    st.subheader("💡 Insights Clave")
    
    # Detectar cambios bruscos
    df['analytics_change'] = df['analytics_granted_pct'].diff().abs()
    big_changes = df[df['analytics_change'] > 10].sort_values('analytics_change', ascending=False)
    
    if not big_changes.empty:
        st.warning("🚨 **Cambios Bruscos Detectados:**")
        for _, row in big_changes.head(3).iterrows():
            st.write(f"- **{row['date_display']}**: Cambio de {row['analytics_change']:.1f}% en Analytics Consent")
        st.info("💡 Posibles causas: Actualización del banner, cambios legales, campañas específicas")
    else:
        st.success("✅ No se detectaron cambios bruscos en el consentimiento")
    
    # Mejor y peor día
    best_day = df.loc[df['analytics_granted_pct'].idxmax()]
    worst_day = df.loc[df['analytics_granted_pct'].idxmin()]
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**📈 Mejor Día:**")
        st.write(f"- Fecha: {best_day['date_display']}")
        st.write(f"- Analytics: {best_day['analytics_granted_pct']:.1f}%")
        st.write(f"- Ads: {best_day['ads_granted_pct']:.1f}%")
    
    with col2:
        st.write("**📉 Peor Día:**")
        st.write(f"- Fecha: {worst_day['date_display']}")
        st.write(f"- Analytics: {worst_day['analytics_granted_pct']:.1f}%")
        st.write(f"- Ads: {worst_day['ads_granted_pct']:.1f}%")

def mostrar_consentimiento_por_geografia(df):
    """Visualización para consentimiento por geografía"""
    st.subheader("🌍 Consentimiento por Geografía")
    
    if df.empty:
        st.warning("No hay datos geográficos para el rango seleccionado")
        return
    
    # Métricas generales
    total_countries = df['country'].nunique()
    total_cities = df['city'].nunique()
    avg_consent_rate = df['full_consent_rate'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Países Únicos", f"{total_countries}")
    with col2:
        st.metric("Ciudades Únicas", f"{total_cities}")
    with col3:
        st.metric("Consent Rate Promedio", f"{avg_consent_rate:.1f}%")
    with col4:
        best_country = df.groupby('country')['full_consent_rate'].mean().idxmax()
        st.metric("País con Mayor Consent", best_country)
    
    # Análisis por país
    st.subheader("🌎 Análisis por País")
    
    country_stats = df.groupby('country').agg({
        'total_events': 'sum',
        'unique_users': 'sum',
        'analytics_consent_rate': 'mean',
        'ads_consent_rate': 'mean',
        'full_consent_rate': 'mean',
        'full_denial_rate': 'mean'
    }).reset_index().sort_values('total_events', ascending=False)
    
    # Top 20 países
    top_countries = country_stats.head(20)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mapa de barras - Consent rate por país
        fig_countries = px.bar(
            top_countries,
            x='country',
            y='full_consent_rate',
            color='full_consent_rate',
            title='Top 20 Países - Tasa de Consentimiento Completo',
            labels={'full_consent_rate': 'Consent Rate (%)', 'country': 'País'},
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        fig_countries.update_layout(xaxis_tickangle=-45, height=500)
        st.plotly_chart(fig_countries, use_container_width=True)
    
    with col2:
        # Scatter: Volumen vs Consent
        fig_scatter = px.scatter(
            top_countries,
            x='unique_users',
            y='full_consent_rate',
            size='total_events',
            color='full_consent_rate',
            hover_name='country',
            title='Volumen de Usuarios vs Tasa de Consentimiento',
            labels={
                'unique_users': 'Usuarios Únicos',
                'full_consent_rate': 'Consent Rate (%)',
                'total_events': 'Eventos'
            },
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Heatmap de consentimiento por país
    st.subheader("🔥 Comparativa: Analytics vs Ads por País")
    
    # Preparar datos para heatmap (Top 15 países)
    heatmap_data = top_countries.head(15)[['country', 'analytics_consent_rate', 'ads_consent_rate']].set_index('country')
    heatmap_data.columns = ['Analytics', 'Ads']
    
    fig_heatmap = px.imshow(
        heatmap_data.T,
        labels=dict(x="País", y="Tipo de Consentimiento", color="Tasa (%)"),
        title="Comparativa Analytics vs Ads por País (Top 15)",
        color_continuous_scale='RdYlGn',
        aspect="auto",
        range_color=[0, 100]
    )
    fig_heatmap.update_layout(height=400)
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Análisis por continente
    st.subheader("🌐 Análisis por Continente")
    
    continent_stats = df.groupby('continent').agg({
        'total_events': 'sum',
        'unique_users': 'sum',
        'analytics_consent_rate': 'mean',
        'ads_consent_rate': 'mean',
        'full_consent_rate': 'mean'
    }).reset_index().sort_values('total_events', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart por continente
        fig_continent_pie = px.pie(
            continent_stats,
            values='unique_users',
            names='continent',
            title='Distribución de Usuarios por Continente',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_continent_pie, use_container_width=True)
    
    with col2:
        # Barras comparativas por continente
        fig_continent_bars = go.Figure()
        
        fig_continent_bars.add_trace(go.Bar(
            x=continent_stats['continent'],
            y=continent_stats['analytics_consent_rate'],
            name='Analytics',
            marker_color='#4CAF50'
        ))
        
        fig_continent_bars.add_trace(go.Bar(
            x=continent_stats['continent'],
            y=continent_stats['ads_consent_rate'],
            name='Ads',
            marker_color='#2196F3'
        ))
        
        fig_continent_bars.update_layout(
            title='Tasas de Consentimiento por Continente',
            xaxis_title='Continente',
            yaxis_title='Tasa (%)',
            barmode='group',
            yaxis=dict(range=[0, 100])
        )
        
        st.plotly_chart(fig_continent_bars, use_container_width=True)
    
    # Análisis por ciudad (Top 20)
    st.subheader("🏙️ Top 20 Ciudades")
    
    city_stats = df.groupby(['country', 'city']).agg({
        'total_events': 'sum',
        'unique_users': 'sum',
        'full_consent_rate': 'mean'
    }).reset_index().sort_values('total_events', ascending=False).head(20)
    
    city_stats['city_country'] = city_stats['city'] + ', ' + city_stats['country']
    
    fig_cities = px.bar(
        city_stats,
        x='unique_users',
        y='city_country',
        orientation='h',
        color='full_consent_rate',
        title='Top 20 Ciudades por Volumen',
        labels={
            'unique_users': 'Usuarios Únicos',
            'city_country': 'Ciudad',
            'full_consent_rate': 'Consent Rate (%)'
        },
        color_continuous_scale='RdYlGn',
        range_color=[0, 100]
    )
    fig_cities.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
    st.plotly_chart(fig_cities, use_container_width=True)
    
    # Tabla detallada de países
    st.subheader("📋 Datos Detallados por País")
    
    display_df = country_stats.head(30)[[
        'country', 'total_events', 'unique_users',
        'analytics_consent_rate', 'ads_consent_rate',
        'full_consent_rate', 'full_denial_rate'
    ]]
    
    st.dataframe(display_df.style.format({
        'total_events': '{:,}',
        'unique_users': '{:,}',
        'analytics_consent_rate': '{:.2f}%',
        'ads_consent_rate': '{:.2f}%',
        'full_consent_rate': '{:.2f}%',
        'full_denial_rate': '{:.2f}%'
    }), height=400)
    
    # Insights geográficos
    st.subheader("💡 Insights Geográficos")
    
    # Países con mayor y menor consentimiento
    best_consent_countries = country_stats.nlargest(5, 'full_consent_rate')
    worst_consent_countries = country_stats.nsmallest(5, 'full_consent_rate')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**✅ Países con Mayor Consentimiento:**")
        for _, row in best_consent_countries.iterrows():
            st.write(f"- **{row['country']}**: {row['full_consent_rate']:.1f}% ({row['unique_users']:,} usuarios)")
    
    with col2:
        st.write("**⚠️ Países con Menor Consentimiento:**")
        for _, row in worst_consent_countries.iterrows():
            st.write(f"- **{row['country']}**: {row['full_consent_rate']:.1f}% ({row['unique_users']:,} usuarios)")
    
    # Detectar patrones regionales
    st.info("""
    **🔍 Análisis Regional:**
    - **Europa**: Típicamente tasas más bajas por regulación GDPR estricta
    - **Norteamérica**: Tasas variables según estado/provincia
    - **LATAM**: Generalmente tasas más altas, pero aumenta regulación (LGPD Brasil)
    - **Asia**: Gran variabilidad según país y cultura de privacidad
    """)
    
    # Estadísticas de compliance
    st.subheader("⚖️ Estadísticas de Compliance")
    
    # Países con regulación estricta (EU + UK + California aproximado)
    strict_countries = ['Spain', 'France', 'Germany', 'Italy', 'United Kingdom', 
                       'Netherlands', 'Belgium', 'Sweden', 'United States']
    
    strict_data = df[df['country'].isin(strict_countries)]
    other_data = df[~df['country'].isin(strict_countries)]
    
    if not strict_data.empty and not other_data.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            strict_consent = strict_data['full_consent_rate'].mean()
            st.metric("Consent Rate (Países Regulados)", f"{strict_consent:.1f}%")
        
        with col2:
            other_consent = other_data['full_consent_rate'].mean()
            st.metric("Consent Rate (Otros Países)", f"{other_consent:.1f}%")
        
        with col3:
            difference = other_consent - strict_consent
            st.metric("Diferencia", f"{difference:+.1f}%")
        
        if difference > 10:
            st.warning(f"⚠️ Los países regulados tienen **{difference:.1f}%** menos consentimiento que otros países")
            st.info("💡 **Recomendación**: Optimiza el banner de cookies específicamente para estos mercados")

def mostrar_consentimiento_por_fuente_trafico(df):
    """Visualización para consentimiento por fuente de tráfico"""
    st.subheader("📊 Consentimiento por Fuente de Tráfico")
    
    if df.empty:
        st.warning("No hay datos de consentimiento por fuente de tráfico")
        return
    
    # Métricas generales
    total_sources = df['utm_source'].nunique()
    avg_analytics_consent = df['analytics_consent_rate'].mean()
    avg_ads_consent = df['ads_consent_rate'].mean()
    avg_full_consent = df['full_consent_rate'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Fuentes Únicas", f"{total_sources}")
    with col2:
        st.metric("Analytics Consent (Avg)", f"{avg_analytics_consent:.1f}%")
    with col3:
        st.metric("Ads Consent (Avg)", f"{avg_ads_consent:.1f}%")
    with col4:
        st.metric("Consentimiento Completo", f"{avg_full_consent:.1f}%")
    
    # Análisis por Channel Group
    st.subheader("🎯 Consentimiento por Channel Group")
    
    channel_stats = df.groupby('channel_group').agg({
        'total_events': 'sum',
        'unique_users': 'sum',
        'unique_sessions': 'sum',
        'analytics_consent_rate': 'mean',
        'ads_consent_rate': 'mean',
        'full_consent_rate': 'mean',
        'no_consent_rate': 'mean'
    }).reset_index().sort_values('total_events', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Treemap de volumen por canal
        fig_treemap = px.treemap(
            channel_stats,
            path=['channel_group'],
            values='unique_users',
            color='full_consent_rate',
            title='Volumen de Usuarios por Canal (Coloreado por Consent Rate)',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100],
            hover_data={'full_consent_rate': ':.2f'}
        )
        fig_treemap.update_layout(height=500)
        st.plotly_chart(fig_treemap, use_container_width=True)
    
    with col2:
        # Barras comparativas por canal
        fig_channel_bars = go.Figure()
        
        fig_channel_bars.add_trace(go.Bar(
            x=channel_stats['channel_group'],
            y=channel_stats['analytics_consent_rate'],
            name='Analytics',
            marker_color='#4CAF50'
        ))
        
        fig_channel_bars.add_trace(go.Bar(
            x=channel_stats['channel_group'],
            y=channel_stats['ads_consent_rate'],
            name='Ads',
            marker_color='#2196F3'
        ))
        
        fig_channel_bars.add_trace(go.Bar(
            x=channel_stats['channel_group'],
            y=channel_stats['no_consent_rate'],
            name='Sin Consentimiento',
            marker_color='#F44336'
        ))
        
        fig_channel_bars.update_layout(
            title='Tasas de Consentimiento por Canal',
            xaxis_title='Canal',
            yaxis_title='Tasa (%)',
            barmode='group',
            yaxis=dict(range=[0, 100]),
            xaxis_tickangle=-45,
            height=500
        )
        
        st.plotly_chart(fig_channel_bars, use_container_width=True)
    
    # Scatter: Volumen vs Consent Rate
    st.subheader("💎 Volumen vs Calidad de Consentimiento")
    
    fig_scatter = px.scatter(
        channel_stats,
        x='unique_users',
        y='full_consent_rate',
        size='total_events',
        color='channel_group',
        hover_name='channel_group',
        title='Relación entre Volumen y Tasa de Consentimiento por Canal',
        labels={
            'unique_users': 'Usuarios Únicos',
            'full_consent_rate': 'Consent Rate (%)',
            'total_events': 'Eventos',
            'channel_group': 'Canal'
        },
        size_max=60
    )
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Top fuentes específicas
    st.subheader("🏆 Top Fuentes de Tráfico")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        selected_channel = st.selectbox(
            "Filtrar por canal:",
            ['Todos'] + sorted(df['channel_group'].unique().tolist()),
            key="consent_traffic_channel_filter"
        )
    
    with col2:
        min_users = st.slider(
            "Mínimo de usuarios:",
            min_value=10,
            max_value=int(df['unique_users'].max()) if len(df) > 0 else 1000,
            value=50,
            key="consent_traffic_min_users"
        )
    
    # Aplicar filtros
    df_filtered = df[df['unique_users'] >= min_users].copy()
    if selected_channel != 'Todos':
        df_filtered = df_filtered[df_filtered['channel_group'] == selected_channel]
    
    # Top 20 fuentes
    top_sources = df_filtered.nlargest(20, 'unique_users')
    
    if not top_sources.empty:
        # Crear etiqueta compuesta
        top_sources['source_label'] = (
            top_sources['utm_source'].fillna('(not set)') + ' / ' + 
            top_sources['utm_medium'].fillna('(none)')
        )
        
        fig_top_sources = px.bar(
            top_sources,
            x='unique_users',
            y='source_label',
            orientation='h',
            color='full_consent_rate',
            title=f'Top 20 Fuentes - {selected_channel}',
            labels={
                'unique_users': 'Usuarios Únicos',
                'source_label': 'Fuente / Medio',
                'full_consent_rate': 'Consent Rate (%)'
            },
            color_continuous_scale='RdYlGn',
            range_color=[0, 100],
            hover_data={
                'utm_campaign': True,
                'analytics_consent_rate': ':.2f',
                'ads_consent_rate': ':.2f'
            }
        )
        fig_top_sources.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=700
        )
        st.plotly_chart(fig_top_sources, use_container_width=True)
    else:
        st.warning("No hay fuentes que cumplan los filtros seleccionados")
    
    # Análisis por medio (utm_medium)
    st.subheader("🔍 Análisis por Medio de Adquisición")
    
    medium_stats = df.groupby('utm_medium').agg({
        'total_events': 'sum',
        'unique_users': 'sum',
        'analytics_consent_rate': 'mean',
        'ads_consent_rate': 'mean',
        'full_consent_rate': 'mean'
    }).reset_index().sort_values('unique_users', ascending=False).head(15)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución de usuarios por medio
        fig_medium_pie = px.pie(
            medium_stats.head(10),
            values='unique_users',
            names='utm_medium',
            title='Distribución de Usuarios por Medio (Top 10)',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_medium_pie, use_container_width=True)
    
    with col2:
        # Consent rate por medio
        fig_medium_consent = px.bar(
            medium_stats,
            x='utm_medium',
            y='full_consent_rate',
            title='Tasa de Consentimiento por Medio',
            labels={'full_consent_rate': 'Consent Rate (%)', 'utm_medium': 'Medio'},
            color='full_consent_rate',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        fig_medium_consent.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_medium_consent, use_container_width=True)
    
    # Tabla detallada
    st.subheader("📋 Datos Detallados")
    
    display_df = df_filtered.head(50)[[
        'channel_group', 'utm_source', 'utm_medium', 'utm_campaign',
        'unique_users', 'unique_sessions',
        'analytics_consent_rate', 'ads_consent_rate',
        'full_consent_rate', 'no_consent_rate'
    ]]
    
    st.dataframe(display_df.style.format({
        'unique_users': '{:,}',
        'unique_sessions': '{:,}',
        'analytics_consent_rate': '{:.2f}%',
        'ads_consent_rate': '{:.2f}%',
        'full_consent_rate': '{:.2f}%',
        'no_consent_rate': '{:.2f}%'
    }), height=400)
    
    # Insights de marketing
    st.subheader("💡 Insights de Marketing")
    
    # Identificar mejores y peores canales
    best_channels = channel_stats.nlargest(3, 'full_consent_rate')
    worst_channels = channel_stats.nsmallest(3, 'full_consent_rate')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**✅ Canales con Mayor Consentimiento:**")
        for _, row in best_channels.iterrows():
            st.write(f"- **{row['channel_group']}**: {row['full_consent_rate']:.1f}%")
            st.write(f"  ({row['unique_users']:,} usuarios)")
    
    with col2:
        st.write("**⚠️ Canales con Menor Consentimiento:**")
        for _, row in worst_channels.iterrows():
            st.write(f"- **{row['channel_group']}**: {row['full_consent_rate']:.1f}%")
            st.write(f"  ({row['unique_users']:,} usuarios)")
    
    # Análisis de ratio consent/denial
    st.subheader("⚖️ Ratio de Aceptación vs Rechazo")
    
    # Añadir columna de ratio
    channel_stats['consent_ratio'] = (
        channel_stats['full_consent_rate'] / 
        channel_stats['no_consent_rate'].replace(0, 0.1)  # Evitar división por cero
    )
    
    fig_ratio = px.bar(
        channel_stats.sort_values('consent_ratio', ascending=False),
        x='channel_group',
        y='consent_ratio',
        title='Ratio de Aceptación/Rechazo por Canal (Mayor es mejor)',
        labels={'consent_ratio': 'Ratio', 'channel_group': 'Canal'},
        color='consent_ratio',
        color_continuous_scale='RdYlGn'
    )
    fig_ratio.add_hline(
        y=1,
        line_dash="dash",
        line_color="gray",
        annotation_text="Equilibrio (1:1)"
    )
    fig_ratio.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_ratio, use_container_width=True)
    
    # Recomendaciones
    st.info("""
    **🎯 Recomendaciones Estratégicas:**
    
    - **Paid Traffic (Ads)**: Típicamente menor consentimiento → Optimiza landing pages
    - **Organic Search**: Mayor consentimiento → Usuarios más comprometidos
    - **Social Media**: Variable según red → Testea mensajes específicos
    - **Email**: Alto consentimiento → Audiencia ya comprometida
    - **Direct**: Consentimiento alto → Usuarios recurrentes y de confianza
    
    💡 **Acción clave**: Invierte más en canales con alto consentimiento Y alto volumen
    """)
    
    # Análisis de campañas específicas (si hay datos)
    if not df['utm_campaign'].isna().all():
        st.subheader("🎯 Top Campañas por Consentimiento")
        
        campaign_stats = df[df['utm_campaign'].notna()].groupby('utm_campaign').agg({
            'unique_users': 'sum',
            'full_consent_rate': 'mean'
        }).reset_index().sort_values('unique_users', ascending=False).head(15)
        
        if not campaign_stats.empty:
            fig_campaigns = px.scatter(
                campaign_stats,
                x='unique_users',
                y='full_consent_rate',
                size='unique_users',
                hover_name='utm_campaign',
                title='Campañas: Volumen vs Consent Rate',
                labels={
                    'unique_users': 'Usuarios',
                    'full_consent_rate': 'Consent Rate (%)'
                },
                size_max=40
            )
            st.plotly_chart(fig_campaigns, use_container_width=True)
