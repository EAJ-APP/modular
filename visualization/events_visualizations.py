import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import Settings

def mostrar_eventos_flatten(df):
    """Visualización para datos flattened de eventos"""
    st.subheader("Datos Completos de Eventos (Flattenizados)")
    
    if df.empty:
        st.warning("No hay datos de eventos para el rango seleccionado")
        return
    
    # Métricas generales
    total_rows = len(df)
    unique_events = df['event_name'].nunique() if 'event_name' in df.columns else 0
    unique_users = df['user_pseudo_id'].nunique() if 'user_pseudo_id' in df.columns else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Registros", f"{total_rows:,}")
    with col2:
        st.metric("Eventos Únicos", f"{unique_events}")
    with col3:
        st.metric("Usuarios Únicos", f"{unique_users}")
    
    # Información sobre las columnas
    st.subheader("Información del Dataset")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Total de Columnas:**", len(df.columns))
        st.write("**Columnas Principales:**")
        main_cols = ['event_name', 'user_pseudo_id', 'event_timestamp', 'ga_session_id']
        for col in main_cols:
            if col in df.columns:
                st.write(f"- {col}")
    
    with col2:
        st.write("**Categorías de Datos:**")
        st.write("- Event Parameters (param_*)")
        st.write("- User Properties (user_property_*)")
        st.write("- Items (item_*)")
        st.write("- Otros campos de GA4")
    
    # Selector de eventos para filtrar - CON SESSION STATE
    st.subheader("Explorador de Datos")
    
    if 'event_name' in df.columns:
        # Inicializar session_state
        if 'evento_flatten_selected' not in st.session_state:
            st.session_state.evento_flatten_selected = 'Todos'
        
        eventos_disponibles = ['Todos'] + sorted(df['event_name'].unique().tolist())
        
        evento_seleccionado = st.selectbox(
            "Filtrar por tipo de evento:",
            eventos_disponibles,
            index=eventos_disponibles.index(st.session_state.evento_flatten_selected) if st.session_state.evento_flatten_selected in eventos_disponibles else 0,
            key="evento_flatten_selector"
        )
        
        # Actualizar session_state
        st.session_state.evento_flatten_selected = evento_seleccionado
        
        if evento_seleccionado != 'Todos':
            df_filtrado = df[df['event_name'] == evento_seleccionado]
        else:
            df_filtrado = df
        
        st.write(f"**Mostrando {len(df_filtrado):,} registros**")
    else:
        df_filtrado = df
    
    # Mostrar tabla con opciones de descarga
    st.dataframe(
        df_filtrado.head(100), # Limitar a 100 filas para rendimiento
        use_container_width=True,
        height=400
    )
    
    st.info("ℹ Mostrando primeras 100 filas. La consulta está limitada a 1000 registros totales para optimizar el rendimiento.")
    
    # Botón de descarga
    if st.button("Descargar CSV completo (1000 filas)", key="download_flatten"):
        csv = df_filtrado.to_csv(index=False)
        st.download_button(
            label="Descargar datos",
            data=csv,
            file_name="eventos_ga4_flatten.csv",
            mime="text/csv"
        )

def mostrar_eventos_resumen(df):
    """Visualización para resumen de eventos"""
    st.subheader("Resumen de Eventos")
    
    if df.empty:
        st.warning("No hay datos de eventos para el rango seleccionado")
        return
    
    # Métricas totales
    total_events = df['total_events'].sum()
    total_users = df['unique_users'].sum()
    total_sessions = df['unique_sessions'].sum() if 'unique_sessions' in df.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Eventos", f"{total_events:,}")
    with col2:
        st.metric("Usuarios Únicos", f"{total_users:,}")
    with col3:
        st.metric("Sesiones Únicas", f"{total_sessions:,}")
    with col4:
        st.metric("Tipos de Eventos", f"{len(df)}")
    
    # Tabla con formato
    st.dataframe(df.style.format({
        'total_events': '{:,}',
        'unique_users': '{:,}',
        'unique_sessions': '{:,}'
    }))
    
    # Gráfico de barras - Top 20 eventos
    top_20 = df.head(20)
    
    fig_bar = px.bar(
        top_20,
        x='total_events',
        y='event_name',
        orientation='h',
        title='Top 20 Eventos por Volumen',
        labels={'total_events': 'Total de Eventos', 'event_name': 'Nombre del Evento'},
        color='total_events',
        color_continuous_scale='Viridis'
    )
    fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Gráfico de dispersión: Eventos vs Usuarios
    fig_scatter = px.scatter(
        df.head(30),
        x='unique_users',
        y='total_events',
        size='unique_sessions',
        color='event_name',
        hover_name='event_name',
        title='Relación: Usuarios vs Volumen de Eventos',
        labels={
            'unique_users': 'Usuarios Únicos',
            'total_events': 'Total de Eventos',
            'unique_sessions': 'Sesiones'
        },
        size_max=40
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Análisis de concentración
    st.subheader("Análisis de Concentración de Eventos")
    
    top_5_pct = (df.head(5)['total_events'].sum() / total_events * 100)
    top_10_pct = (df.head(10)['total_events'].sum() / total_events * 100)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Top 5 Eventos", f"{top_5_pct:.1f}% del total")
    with col2:
        st.metric("Top 10 Eventos", f"{top_10_pct:.1f}% del total")

def mostrar_eventos_por_fecha(df):
    """Visualización para evolución temporal de eventos"""
    st.subheader("Evolución Temporal de Eventos")
    
    if df.empty:
        st.warning("No hay datos de eventos por fecha")
        return
    
    # Convertir fecha
    df['event_date'] = pd.to_datetime(df['event_date'], format='%Y%m%d')
    df['fecha_formateada'] = df['event_date'].dt.strftime('%d/%m/%Y')
    
    # Inicializar session_state para el multiselect
    if 'eventos_fecha_selected' not in st.session_state:
        st.session_state.eventos_fecha_selected = ['Todos']
    
    # Selector de eventos para filtrar
    eventos_disponibles = ['Todos'] + sorted(df['event_name'].unique().tolist())
    
    eventos_seleccionados = st.multiselect(
        "Seleccionar eventos a visualizar:",
        eventos_disponibles,
        default=st.session_state.eventos_fecha_selected,
        key="eventos_fecha_multiselect"
    )
    
    # Actualizar session_state
    st.session_state.eventos_fecha_selected = eventos_seleccionados if eventos_seleccionados else ['Todos']
    
    if 'Todos' not in eventos_seleccionados and len(eventos_seleccionados) > 0:
        df_filtrado = df[df['event_name'].isin(eventos_seleccionados)]
    else:
        df_filtrado = df
    
    # Agrupar por fecha
    df_agregado = df_filtrado.groupby(['event_date', 'fecha_formateada']).agg({
        'total_events': 'sum',
        'unique_users': 'sum'
    }).reset_index().sort_values('event_date')
    
    # Gráfico de línea - Evolución temporal
    fig_line = px.line(
        df_agregado,
        x='fecha_formateada',
        y='total_events',
        title='Evolución de Eventos en el Tiempo',
        labels={'total_events': 'Total de Eventos', 'fecha_formateada': 'Fecha'},
        markers=True
    )
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Gráfico por tipo de evento (si hay filtros)
    if 'Todos' not in eventos_seleccionados and len(eventos_seleccionados) > 1:
        df_por_evento = df_filtrado.groupby(['event_date', 'fecha_formateada', 'event_name']).agg({
            'total_events': 'sum'
        }).reset_index().sort_values('event_date')
        
        fig_multi = px.line(
            df_por_evento,
            x='fecha_formateada',
            y='total_events',
            color='event_name',
            title='Comparativa de Eventos Seleccionados',
            labels={'total_events': 'Total de Eventos', 'fecha_formateada': 'Fecha'},
            markers=True
        )
        st.plotly_chart(fig_multi, use_container_width=True)
    
    # Mostrar tabla
    st.dataframe(df_agregado.style.format({
        'total_events': '{:,}',
        'unique_users': '{:,}'
    }))

    # Sección de análisis con IA
    st.markdown("""
    <div style="border-left: 4px solid #6366f1; background: linear-gradient(90deg, rgba(99, 102, 241, 0.1) 0%, transparent 100%); padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0 0.5rem 0;">
        <span style="color: #6366f1; font-weight: 600; font-size: 0.9rem;">Analisis con IA disponible</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Generar análisis con IA", key="btn_ia_eventos_fecha"):
        from utils.llm_insights import generar_insight_tabla
        with st.spinner("Generando con LLM (IA)..."):
            contexto = "Análisis de evolución temporal de eventos en GA4. Muestra tendencias de eventos y usuarios únicos a lo largo del tiempo."
            resultado = generar_insight_tabla(df_agregado, contexto=contexto)
            if resultado:
                st.markdown(resultado)
            else:
                st.error("No se pudo generar el análisis. Verifica la API key de Perplexity en secrets.toml.")

def mostrar_parametros_evento(df, event_name):
    """Visualización para parámetros de un evento específico"""
    st.subheader(f" Parámetros del Evento: {event_name}")
    
    if df.empty:
        st.warning(f"No hay datos de parámetros para el evento '{event_name}'")
        return
    
    # Métricas
    total_params = len(df)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Parámetros Únicos", f"{total_params}")
    with col2:
        st.metric("Usos Totales", f"{df['parameter_count'].sum():,}")
    
    # Tabla de parámetros
    st.dataframe(df.style.format({
        'parameter_count': '{:,}',
        'unique_string_values': '{:,}',
        'unique_int_values': '{:,}'
    }))
    
    # Gráfico de barras
    fig = px.bar(
        df.head(20),
        x='parameter_count',
        y='parameter_name',
        orientation='h',
        title=f'Parámetros más usados en {event_name}',
        labels={'parameter_count': 'Frecuencia', 'parameter_name': 'Parámetro'},
        color='parameter_count',
        color_continuous_scale='Blues'
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
    st.plotly_chart(fig, use_container_width=True)

def mostrar_metricas_diarias(df):
    """Visualización para métricas diarias completas"""
    st.subheader("Métricas Diarias de Rendimiento")
    
    if df.empty:
        st.warning("No hay datos de métricas diarias para el rango seleccionado")
        return
    
    # Convertir fecha y formatear
    df['date_formatted'] = pd.to_datetime(df['date_formatted'])
    df['fecha_display'] = df['date_formatted'].dt.strftime('%d/%m/%Y')
    
    # Métricas totales
    total_sessions = df['sessions'].sum()
    total_users = df['totalUsers'].sum()
    total_new_users = df['NewUsers'].sum()
    total_purchases = df['Purchases'].sum()
    total_revenue = df['purchaseRevenue'].sum()
    avg_session_duration = df['averageSessionDuration_seconds'].mean()
    avg_engagement_rate = df['engagementRate_percent'].mean()
    
    # Mostrar métricas clave en cards
    st.subheader("Resumen del Período")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sesiones", f"{total_sessions:,}")
        st.metric("Usuarios Totales", f"{total_users:,}")
    with col2:
        st.metric("Nuevos Usuarios", f"{total_new_users:,}")
        st.metric("Tasa Engagement", f"{avg_engagement_rate:.2f}%")
    with col3:
        st.metric("Total Compras", f"{total_purchases:,}")
        st.metric("Ingresos Totales", f"€{total_revenue:,.2f}")
    with col4:
        st.metric("Duración Media Sesión", f"{avg_session_duration:.0f}s")
        revenue_per_session = total_revenue / total_sessions if total_sessions > 0 else 0
        st.metric("Ingresos/Sesión", f"€{revenue_per_session:.2f}")
    
    # Mostrar tabla completa
    st.subheader("Tabla de Datos")
    st.dataframe(df.style.format({
        'sessions': '{:,}',
        'averageSessionDuration_seconds': '{:.2f}',
        'totalUsers': '{:,}',
        'NewUsers': '{:,}',
        'Purchases': '{:,}',
        'purchaseRevenue': '€{:,.2f}',
        'screenPageViews': '{:,}',
        'engagedSessions': '{:,}',
        'engagementRate_percent': '{:.2f}%',
        'eventCount': '{:,}'
    }))
    
    # Gráficos de evolución
    st.subheader("Evolución Temporal")
    
    # Selector de métrica a visualizar
    if 'metricas_diarias_selected_metric' not in st.session_state:
        st.session_state.metricas_diarias_selected_metric = 'sessions'
    
    metricas_disponibles = {
        'sessions': 'Sesiones',
        'totalUsers': 'Usuarios Totales',
        'NewUsers': 'Nuevos Usuarios',
        'Purchases': 'Compras',
        'purchaseRevenue': 'Ingresos (€)',
        'screenPageViews': 'Page Views',
        'engagedSessions': 'Sesiones Comprometidas',
        'engagementRate_percent': 'Tasa de Engagement (%)',
        'averageSessionDuration_seconds': 'Duración Media Sesión (s)'
    }
    
    col1, col2 = st.columns([2, 1])
    with col1:
        metrica_seleccionada = st.selectbox(
            "Seleccionar métrica a visualizar:",
            options=list(metricas_disponibles.keys()),
            format_func=lambda x: metricas_disponibles[x],
            index=list(metricas_disponibles.keys()).index(st.session_state.metricas_diarias_selected_metric),
            key="metricas_diarias_selector"
        )
        st.session_state.metricas_diarias_selected_metric = metrica_seleccionada
    
    # Gráfico de línea para la métrica seleccionada
    fig_line = px.line(
        df,
        x='fecha_display',
        y=metrica_seleccionada,
        title=f'Evolución de {metricas_disponibles[metrica_seleccionada]}',
        labels={
            metrica_seleccionada: metricas_disponibles[metrica_seleccionada],
            'fecha_display': 'Fecha'
        },
        markers=True
    )
    fig_line.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Gráficos de comparación
    st.subheader("Comparativas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Comparativa Usuarios vs Sesiones
        fig_users_sessions = go.Figure()
        fig_users_sessions.add_trace(go.Scatter(
            x=df['fecha_display'],
            y=df['totalUsers'],
            name='Usuarios Totales',
            mode='lines+markers'
        ))
        fig_users_sessions.add_trace(go.Scatter(
            x=df['fecha_display'],
            y=df['sessions'],
            name='Sesiones',
            mode='lines+markers'
        ))
        fig_users_sessions.update_layout(
            title='Usuarios vs Sesiones',
            xaxis_title='Fecha',
            yaxis_title='Cantidad',
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_users_sessions, use_container_width=True)
    
    with col2:
        # Comparativa Engagement
        fig_engagement = go.Figure()
        fig_engagement.add_trace(go.Scatter(
            x=df['fecha_display'],
            y=df['engagementRate_percent'],
            name='Tasa de Engagement',
            mode='lines+markers',
            line=dict(color='green')
        ))
        fig_engagement.update_layout(
            title='Evolución del Engagement',
            xaxis_title='Fecha',
            yaxis_title='Tasa (%)',
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_engagement, use_container_width=True)
    
    # Análisis de conversión (si hay compras)
    if total_purchases > 0:
        st.subheader("Análisis de Conversión")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Evolución de compras e ingresos
            fig_commerce = go.Figure()
            fig_commerce.add_trace(go.Bar(
                x=df['fecha_display'],
                y=df['Purchases'],
                name='Compras',
                yaxis='y'
            ))
            fig_commerce.add_trace(go.Scatter(
                x=df['fecha_display'],
                y=df['purchaseRevenue'],
                name='Ingresos (€)',
                mode='lines+markers',
                yaxis='y2',
                line=dict(color='orange')
            ))
            fig_commerce.update_layout(
                title='Compras e Ingresos',
                xaxis_title='Fecha',
                yaxis=dict(title='Número de Compras'),
                yaxis2=dict(title='Ingresos (€)', overlaying='y', side='right'),
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_commerce, use_container_width=True)
        
        with col2:
            # Tasa de conversión
            df['conversion_rate'] = (df['Purchases'] / df['sessions'] * 100).round(2)
            fig_conversion = px.line(
                df,
                x='fecha_display',
                y='conversion_rate',
                title='Tasa de Conversión (%)',
                labels={'conversion_rate': 'Tasa (%)', 'fecha_display': 'Fecha'},
                markers=True
            )
            fig_conversion.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_conversion, use_container_width=True)
    
    # Botón de descarga
    if st.button("Descargar Datos CSV", key="download_metricas_diarias"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name="metricas_diarias_ga4.csv",
            mime="text/csv"
        )
