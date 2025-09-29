import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import Settings

def mostrar_session_path_analysis(df):
    """Visualización para Session Path Analysis"""
    st.subheader("🗺️ Análisis de Rutas de Navegación")
    
    if df.empty:
        st.warning("No hay datos de rutas de navegación para el rango seleccionado")
        return
    
    # Métricas generales
    total_paths = len(df)
    total_sessions = df['session_count'].sum()
    unique_pages = pd.concat([df['previous_page'], df['current_page'], df['next_page']]).nunique()
    avg_sessions_per_path = df['session_count'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rutas Únicas", f"{total_paths:,}")
    with col2:
        st.metric("Total Sesiones", f"{total_sessions:,}")
    with col3:
        st.metric("Páginas Únicas", f"{unique_pages}")
    with col4:
        st.metric("Sesiones/Ruta (Avg)", f"{avg_sessions_per_path:.1f}")
    
    # Acortar URLs para mejor visualización
    def shorten_url(url, max_length=40):
        if pd.isna(url) or url == '(entrance)' or url == '(exit)':
            return url
        return url[:max_length] + '...' if len(str(url)) > max_length else url
    
    df['previous_page_short'] = df['previous_page'].apply(shorten_url)
    df['current_page_short'] = df['current_page'].apply(shorten_url)
    df['next_page_short'] = df['next_page'].apply(shorten_url)
    
    # Crear columna de ruta completa
    df['full_path'] = df['previous_page_short'] + ' → ' + df['current_page_short'] + ' → ' + df['next_page_short']
    
    # Mostrar tabla con datos
    st.subheader("📊 Top Rutas de Navegación")
    
    # Opciones de filtrado
    col1, col2 = st.columns(2)
    with col1:
        min_sessions = st.slider(
            "Mínimo de sesiones por ruta:",
            min_value=1,
            max_value=int(df['session_count'].max()),
            value=10,
            key="path_min_sessions"
        )
    
    with col2:
        path_type = st.selectbox(
            "Filtrar por tipo de ruta:",
            ["Todas", "Solo entradas (entrance)", "Solo salidas (exit)", "Rutas internas"],
            key="path_type_filter"
        )
    
    # Aplicar filtros
    df_filtered = df[df['session_count'] >= min_sessions].copy()
    
    if path_type == "Solo entradas (entrance)":
        df_filtered = df_filtered[df_filtered['previous_page'] == '(entrance)']
    elif path_type == "Solo salidas (exit)":
        df_filtered = df_filtered[df_filtered['next_page'] == '(exit)']
    elif path_type == "Rutas internas":
        df_filtered = df_filtered[
            (df_filtered['previous_page'] != '(entrance)') & 
            (df_filtered['next_page'] != '(exit)')
        ]
    
    # Mostrar tabla
    st.dataframe(
        df_filtered[['previous_page', 'current_page', 'next_page', 'session_count']].head(50).style.format({
            'session_count': '{:,}'
        }),
        use_container_width=True,
        height=400
    )
    
    # Top 20 rutas más comunes
    st.subheader("🏆 Top 20 Rutas Más Comunes")
    
    top_paths = df_filtered.nlargest(20, 'session_count')
    
    fig_top_paths = px.bar(
        top_paths,
        x='session_count',
        y='full_path',
        orientation='h',
        title='Top 20 Rutas de Navegación',
        labels={'session_count': 'Sesiones', 'full_path': 'Ruta'},
        color='session_count',
        color_continuous_scale='Blues'
    )
    fig_top_paths.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=700,
        showlegend=False
    )
    st.plotly_chart(fig_top_paths, use_container_width=True)
    
    # Análisis de páginas de entrada
    st.subheader("🚪 Análisis de Páginas de Entrada")
    
    entrance_pages = df[df['previous_page'] == '(entrance)'].groupby('current_page').agg({
        'session_count': 'sum'
    }).reset_index().sort_values('session_count', ascending=False).head(15)
    
    entrance_pages['current_page_short'] = entrance_pages['current_page'].apply(shorten_url)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_entrance = px.bar(
            entrance_pages,
            x='session_count',
            y='current_page_short',
            orientation='h',
            title='Top 15 Páginas de Entrada',
            labels={'session_count': 'Sesiones', 'current_page_short': 'Página'},
            color='session_count',
            color_continuous_scale='Greens'
        )
        fig_entrance.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
        st.plotly_chart(fig_entrance, use_container_width=True)
    
    with col2:
        # Pie chart de distribución
        fig_entrance_pie = px.pie(
            entrance_pages.head(10),
            values='session_count',
            names='current_page_short',
            title='Distribución Top 10 Entradas'
        )
        st.plotly_chart(fig_entrance_pie, use_container_width=True)
    
    # Análisis de páginas de salida
    st.subheader("🚶 Análisis de Páginas de Salida")
    
    exit_pages = df[df['next_page'] == '(exit)'].groupby('current_page').agg({
        'session_count': 'sum'
    }).reset_index().sort_values('session_count', ascending=False).head(15)
    
    exit_pages['current_page_short'] = exit_pages['current_page'].apply(shorten_url)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_exit = px.bar(
            exit_pages,
            x='session_count',
            y='current_page_short',
            orientation='h',
            title='Top 15 Páginas de Salida',
            labels={'session_count': 'Sesiones', 'current_page_short': 'Página'},
            color='session_count',
            color_continuous_scale='Reds'
        )
        fig_exit.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
        st.plotly_chart(fig_exit, use_container_width=True)
    
    with col2:
        # Tabla de páginas de salida
        st.write("**Páginas con Mayor Abandono:**")
        st.dataframe(
            exit_pages[['current_page', 'session_count']].head(10).style.format({
                'session_count': '{:,}'
            }),
            use_container_width=True
        )
    
    # Análisis de flujo entre páginas
    st.subheader("🔄 Flujo de Navegación (Sankey Diagram)")
    
    # Preparar datos para Sankey (Top 30 rutas más comunes)
    sankey_data = df_filtered.nlargest(30, 'session_count')
    
    # Crear nodos únicos
    all_pages = pd.concat([
        sankey_data['previous_page_short'],
        sankey_data['current_page_short'],
        sankey_data['next_page_short']
    ]).unique()
    
    node_dict = {page: idx for idx, page in enumerate(all_pages)}
    
    # Crear links para el diagrama
    source_indices = sankey_data['previous_page_short'].map(node_dict).tolist()
    target_indices = sankey_data['current_page_short'].map(node_dict).tolist()
    values = sankey_data['session_count'].tolist()
    
    # Segunda parte del flujo (current -> next)
    source_indices_2 = sankey_data['current_page_short'].map(node_dict).tolist()
    target_indices_2 = sankey_data['next_page_short'].map(node_dict).tolist()
    values_2 = sankey_data['session_count'].tolist()
    
    # Combinar ambas partes
    all_sources = source_indices + source_indices_2
    all_targets = target_indices + target_indices_2
    all_values = values + values_2
    
    # Crear Sankey diagram
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=list(all_pages),
            color="lightblue"
        ),
        link=dict(
            source=all_sources,
            target=all_targets,
            value=all_values,
            color="rgba(0,0,255,0.2)"
        )
    )])
    
    fig_sankey.update_layout(
        title="Diagrama de Flujo de Navegación (Top 30 Rutas)",
        height=600,
        font=dict(size=10)
    )
    
    st.plotly_chart(fig_sankey, use_container_width=True)
    
    # Insights clave
    st.subheader("💡 Insights Clave")
    
    # Calcular métricas de insight
    entrance_rate = (df[df['previous_page'] == '(entrance)']['session_count'].sum() / total_sessions * 100)
    exit_rate = (df[df['next_page'] == '(exit)']['session_count'].sum() / total_sessions * 100)
    
    top_entrance = entrance_pages.iloc[0] if len(entrance_pages) > 0 else None
    top_exit = exit_pages.iloc[0] if len(exit_pages) > 0 else None
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📍 Páginas de Entrada:**")
        st.metric("% de Sesiones que Inician", f"{entrance_rate:.1f}%")
        if top_entrance is not None:
            st.write(f"**Página más común:** {top_entrance['current_page_short']}")
            st.write(f"**Sesiones:** {top_entrance['session_count']:,}")
    
    with col2:
        st.write("**🚪 Páginas de Salida:**")
        st.metric("% de Sesiones que Terminan", f"{exit_rate:.1f}%")
        if top_exit is not None:
            st.write(f"**Página más común:** {top_exit['current_page_short']}")
            st.write(f"**Sesiones:** {top_exit['session_count']:,}")
    
    # Rutas críticas
    st.write("**🎯 Rutas Críticas para Optimización:**")
    
    # Rutas con alta salida después de página actual
    critical_exits = df[
        (df['next_page'] == '(exit)') & 
        (df['previous_page'] != '(entrance)')
    ].nlargest(5, 'session_count')
    
    if not critical_exits.empty:
        st.write("*Usuarios que abandonan después de estas secuencias:*")
        for _, row in critical_exits.iterrows():
            st.write(f"- **{shorten_url(row['previous_page'])}** → **{shorten_url(row['current_page'])}** → (salida): {row['session_count']:,} sesiones")
    
    # Botón de descarga
    if st.button("📥 Descargar Datos CSV", key="download_session_paths"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name="session_path_analysis.csv",
            mime="text/csv"
        )

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
