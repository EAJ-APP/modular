import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import Settings

def mostrar_exit_pages_analysis(df):
    """Visualización para Most Frequent Exit Pages Analysis"""
    st.subheader("🚪 Análisis de Páginas de Salida")
    
    if df.empty:
        st.warning("No hay datos de páginas de salida para el rango seleccionado")
        return
    
    # Métricas generales
    total_sessions = df['sessions'].sum()
    unique_exit_pages = len(df)
    avg_sessions_per_page = df['sessions'].mean()
    top_exit_rate = df.iloc[0]['exit_percentage'] if len(df) > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sesiones", f"{total_sessions:,}")
    with col2:
        st.metric("Páginas de Salida Únicas", f"{unique_exit_pages}")
    with col3:
        st.metric("Sesiones/Página (Avg)", f"{avg_sessions_per_page:.0f}")
    with col4:
        st.metric("Mayor % Salida", f"{top_exit_rate:.1f}%")
    
    # Acortar URLs para mejor visualización
    def shorten_url(url, max_length=60):
        if pd.isna(url):
            return "(not set)"
        return url[:max_length] + '...' if len(str(url)) > max_length else url
    
    df['exit_page_short'] = df['exit_page_path'].apply(shorten_url)
    
    # Filtro por número mínimo de sesiones
    st.subheader("🔍 Filtros")
    
    col1, col2 = st.columns(2)
    with col1:
        min_sessions_filter = st.slider(
            "Mínimo de sesiones:",
            min_value=1,
            max_value=int(df['sessions'].max()) if len(df) > 0 else 100,
            value=10,
            key="exit_min_sessions"
        )
    
    with col2:
        top_n = st.selectbox(
            "Mostrar top:",
            [10, 20, 30, 50, 100],
            index=1,
            key="exit_top_n"
        )
    
    # Aplicar filtros
    df_filtered = df[df['sessions'] >= min_sessions_filter].head(top_n)
    
    if df_filtered.empty:
        st.warning("⚠️ No hay datos con los filtros seleccionados. Reduce el mínimo de sesiones.")
        return
    
    # Mostrar tabla con datos
    st.subheader("📊 Datos Detallados")
    
    st.dataframe(
        df_filtered[['exit_page_path', 'sessions', 'exit_percentage']].style.format({
            'sessions': '{:,}',
            'exit_percentage': '{:.2f}%'
        }),
        use_container_width=True,
        height=400
    )
    
    # Top páginas de salida
    st.subheader(f"🏆 Top {min(top_n, len(df_filtered))} Páginas de Salida")
    
    top_exits = df_filtered.head(top_n)
    
    fig_top_exits = px.bar(
        top_exits,
        x='sessions',
        y='exit_page_short',
        orientation='h',
        title=f'Top {min(top_n, len(top_exits))} Páginas con Mayor Abandono',
        labels={'sessions': 'Sesiones', 'exit_page_short': 'Página de Salida'},
        color='exit_percentage',
        color_continuous_scale='Reds',
        hover_data={'exit_page_path': True, 'exit_percentage': ':.2f'}
    )
    fig_top_exits.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=max(500, len(top_exits) * 25),
        showlegend=False
    )
    st.plotly_chart(fig_top_exits, use_container_width=True)
    
    # Distribución acumulativa
    st.subheader("📈 Análisis de Concentración")
    
    # Calcular porcentaje acumulativo
    df_sorted = df.sort_values('sessions', ascending=False).reset_index(drop=True)
    df_sorted['cumulative_sessions'] = df_sorted['sessions'].cumsum()
    df_sorted['cumulative_percentage'] = (df_sorted['cumulative_sessions'] / total_sessions * 100).round(2)
    
    # Gráfico de Pareto
    fig_pareto = go.Figure()
    
    fig_pareto.add_trace(go.Bar(
        x=list(range(1, len(df_sorted.head(30)) + 1)),
        y=df_sorted.head(30)['sessions'],
        name='Sesiones',
        marker_color='lightblue',
        yaxis='y'
    ))
    
    fig_pareto.add_trace(go.Scatter(
        x=list(range(1, len(df_sorted.head(30)) + 1)),
        y=df_sorted.head(30)['cumulative_percentage'],
        name='% Acumulado',
        mode='lines+markers',
        line=dict(color='red', width=2),
        yaxis='y2'
    ))
    
    fig_pareto.update_layout(
        title='Análisis de Pareto - Concentración de Salidas (Top 30)',
        xaxis_title='Páginas (ordenadas por sesiones)',
        yaxis=dict(title='Sesiones', side='left'),
        yaxis2=dict(title='% Acumulado', side='right', overlaying='y', range=[0, 100]),
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig_pareto, use_container_width=True)
    
    # Métricas de concentración
    top_10_pct = df_sorted.head(10)['exit_percentage'].sum()
    top_20_pct = df_sorted.head(20)['exit_percentage'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Top 10 Páginas", f"{top_10_pct:.1f}% de salidas")
    with col2:
        st.metric("Top 20 Páginas", f"{top_20_pct:.1f}% de salidas")
    with col3:
        # Calcular índice de concentración (cuántas páginas acumulan el 80%)
        pages_80pct = len(df_sorted[df_sorted['cumulative_percentage'] <= 80])
        st.metric("Páginas para 80% salidas", f"{pages_80pct}")
    
    # Distribución de páginas de salida
    st.subheader("📊 Distribución de Sesiones")
    
    # Crear rangos de sesiones
    df_filtered['session_range'] = pd.cut(
        df_filtered['sessions'],
        bins=[0, 50, 100, 500, 1000, float('inf')],
        labels=['1-50', '51-100', '101-500', '501-1000', '1000+']
    )
    
    range_dist = df_filtered.groupby('session_range', observed=True).size().reset_index(name='count')
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart de distribución por rango
        fig_dist = px.pie(
            range_dist,
            values='count',
            names='session_range',
            title='Distribución de Páginas por Rango de Sesiones',
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        # Histograma de sesiones
        fig_hist = px.histogram(
            df_filtered,
            x='sessions',
            nbins=30,
            title='Distribución de Sesiones por Página',
            labels={'sessions': 'Sesiones', 'count': 'Número de Páginas'},
            color_discrete_sequence=['steelblue']
        )
        fig_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Análisis de patrones en URLs
    st.subheader("🔍 Análisis de Patrones de URL")
    
    # Extraer secciones del sitio (primer nivel de path)
    df_filtered['section'] = df_filtered['exit_page_path'].str.extract(r'^/([^/]+)')[0].fillna('home')
    
    section_stats = df_filtered.groupby('section').agg({
        'sessions': 'sum',
        'exit_page_path': 'count'
    }).reset_index()
    section_stats.columns = ['section', 'total_sessions', 'page_count']
    section_stats = section_stats.sort_values('total_sessions', ascending=False).head(15)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sesiones por sección
        fig_sections = px.bar(
            section_stats,
            x='section',
            y='total_sessions',
            title='Sesiones de Salida por Sección del Sitio',
            labels={'section': 'Sección', 'total_sessions': 'Sesiones'},
            color='total_sessions',
            color_continuous_scale='Oranges'
        )
        fig_sections.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig_sections, use_container_width=True)
    
    with col2:
        # Tabla de secciones
        st.write("**Top Secciones con Más Salidas:**")
        st.dataframe(
            section_stats[['section', 'total_sessions', 'page_count']].style.format({
                'total_sessions': '{:,}',
                'page_count': '{:,}'
            }),
            use_container_width=True
        )
    
    # Insights y recomendaciones
    st.subheader("💡 Insights Clave")
    
    # Identificar páginas críticas
    top_exit = df_sorted.iloc[0] if len(df_sorted) > 0 else None
    high_exit_pages = df_sorted[df_sorted['exit_percentage'] > 5].head(10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🚨 Página con Mayor Abandono:**")
        if top_exit is not None:
            st.write(f"- **Página:** {shorten_url(top_exit['exit_page_path'], 50)}")
            st.write(f"- **Sesiones:** {top_exit['sessions']:,}")
            st.write(f"- **% del Total:** {top_exit['exit_percentage']:.2f}%")
    
    with col2:
        st.write("**⚠️ Páginas Críticas (>5% salidas):**")
        if not high_exit_pages.empty:
            for _, row in high_exit_pages.iterrows():
                st.write(f"- {shorten_url(row['exit_page_path'], 40)}: {row['exit_percentage']:.1f}%")
        else:
            st.write("✅ No hay páginas individuales con >5% de salidas")
    
    # Recomendaciones
    st.subheader("🎯 Recomendaciones")
    
    st.info(f"""
    **Plan de Acción para Reducir Abandonos:**
    
    🔍 **Priorizar optimización:**
    - Las top {pages_80pct} páginas concentran el 80% de las salidas
    - Enfoca esfuerzos en estas páginas para mayor impacto
    
    🎯 **Páginas críticas identificadas:**
    - {len(high_exit_pages)} páginas con >5% de tasa de salida
    - Requieren revisión urgente de UX y contenido
    
    ⚡ **Acciones recomendadas:**
    1. Analizar tiempo en página antes de salir
    2. Revisar llamadas a la acción (CTAs)
    3. Verificar errores técnicos o problemas de carga
    4. A/B testing en páginas con mayor abandono
    5. Agregar contenido relacionado o next steps claros
    
    💰 **Impacto potencial:**
    - Reducir un 10% las salidas de las top 10 páginas podría retener ~{int(df_sorted.head(10)['sessions'].sum() * 0.1):,} sesiones adicionales
    """)
    
    # Comparativa: Páginas de entrada vs salida
    st.subheader("🔄 Insight Adicional")
    
    # Identificar páginas que son tanto entrada como salida
    entrance_keywords = ['home', 'index', 'landing', 'categoria', 'product']
    potential_entrance_exits = df_filtered[
        df_filtered['exit_page_path'].str.contains('|'.join(entrance_keywords), case=False, na=False)
    ]
    
    if not potential_entrance_exits.empty:
        st.warning(f"""
        **⚠️ Páginas que pueden ser tanto entrada como salida:**
        
        Se detectaron {len(potential_entrance_exits)} páginas que parecen ser landing pages pero también tienen alta tasa de salida.
        
        Esto puede indicar:
        - Problemas de expectativas vs realidad
        - Falta de contenido relevante
        - Problemas técnicos en la primera interacción
        
        **Páginas a revisar:**
        """)
        
        for _, row in potential_entrance_exits.head(5).iterrows():
            st.write(f"- {shorten_url(row['exit_page_path'], 60)}: {row['sessions']:,} salidas ({row['exit_percentage']:.1f}%)")
    
    # Botón de descarga
    if st.button("📥 Descargar Datos CSV", key="download_exit_pages"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name="exit_pages_analysis.csv",
            mime="text/csv"
        )

def mostrar_hourly_sessions_performance(df):
    """Visualización para Hourly Sessions Ecommerce Performance"""
    st.subheader("⏰ Rendimiento de Sesiones por Hora")
    
    if df.empty:
        st.warning("No hay datos de rendimiento horario para el rango seleccionado")
        return
    
    # Convertir hora a entero para mejor ordenamiento
    df['hour_int'] = df['hour'].astype(int)
    
    # Métricas generales
    total_sessions = df['sessions'].sum()
    total_pageviews = df['pageviews'].sum()
    total_orders = df['order_sessions'].sum()
    avg_sessions_per_hour = df['sessions'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sesiones", f"{total_sessions:,}")
    with col2:
        st.metric("Total Pageviews", f"{total_pageviews:,}")
    with col3:
        st.metric("Total Compras", f"{total_orders:,}")
    with col4:
        st.metric("Sesiones/Hora (Avg)", f"{avg_sessions_per_hour:.0f}")
    
    # Calcular tasas de conversión por hora
    df['view_item_rate'] = (df['view_item_sessions'] / df['sessions'] * 100).round(2)
    df['add_to_cart_rate'] = (df['add_to_cart_sessions'] / df['sessions'] * 100).round(2)
    df['conversion_rate'] = (df['order_sessions'] / df['sessions'] * 100).round(2)
    
    # Agregar por hora del día (promedio de todas las fechas)
    hourly_avg = df.groupby('hour_int').agg({
        'sessions': 'mean',
        'pageviews': 'mean',
        'view_item_sessions': 'mean',
        'add_to_cart_sessions': 'mean',
        'order_sessions': 'mean',
        'view_item_rate': 'mean',
        'add_to_cart_rate': 'mean',
        'conversion_rate': 'mean'
    }).reset_index()
    
    hourly_avg['hour'] = hourly_avg['hour_int'].apply(lambda x: f'{x:02d}:00')
    
    # Análisis por hora del día
    st.subheader("📊 Distribución por Hora del Día")
    
    # Gráfico de líneas - Sesiones y eventos por hora
    fig_hourly = go.Figure()
    
    fig_hourly.add_trace(go.Scatter(
        x=hourly_avg['hour'],
        y=hourly_avg['sessions'],
        name='Sesiones',
        mode='lines+markers',
        line=dict(color='blue', width=3),
        yaxis='y'
    ))
    
    fig_hourly.add_trace(go.Scatter(
        x=hourly_avg['hour'],
        y=hourly_avg['view_item_sessions'],
        name='View Item',
        mode='lines+markers',
        line=dict(color='green', width=2),
        yaxis='y'
    ))
    
    fig_hourly.add_trace(go.Scatter(
        x=hourly_avg['hour'],
        y=hourly_avg['add_to_cart_sessions'],
        name='Add to Cart',
        mode='lines+markers',
        line=dict(color='orange', width=2),
        yaxis='y'
    ))
    
    fig_hourly.add_trace(go.Scatter(
        x=hourly_avg['hour'],
        y=hourly_avg['order_sessions'],
        name='Compras',
        mode='lines+markers',
        line=dict(color='red', width=2),
        yaxis='y2'
    ))
    
    fig_hourly.update_layout(
        title='Actividad por Hora del Día (Promedio)',
        xaxis_title='Hora del Día',
        yaxis=dict(title='Sesiones / Eventos'),
        yaxis2=dict(title='Compras', overlaying='y', side='right'),
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig_hourly, use_container_width=True)
    
    # Heatmap de actividad por hora y día de la semana
    st.subheader("🔥 Heatmap: Actividad por Día y Hora")
    
    # Preparar datos para heatmap
    heatmap_data = df.pivot_table(
        values='sessions',
        index='weekday',
        columns='hour_int',
        aggfunc='mean'
    )
    
    # Ordenar días de la semana correctamente
    weekday_order = ['0 - Sunday', '1 - Monday', '2 - Tuesday', '3 - Wednesday', 
                     '4 - Thursday', '5 - Friday', '6 - Saturday']
    
    # Filtrar solo los días que existen en los datos
    weekday_order = [day for day in weekday_order if day in heatmap_data.index]
    heatmap_data = heatmap_data.reindex(weekday_order)
    
    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x="Hora del Día", y="Día de la Semana", color="Sesiones"),
        title="Sesiones por Día de la Semana y Hora",
        color_continuous_scale='Blues',
        aspect="auto"
    )
    fig_heatmap.update_xaxes(side="bottom")
    fig_heatmap.update_layout(height=400)
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Análisis de conversión por hora
    st.subheader("💰 Tasas de Conversión por Hora")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de tasas de conversión
        fig_conversion = go.Figure()
        
        fig_conversion.add_trace(go.Bar(
            x=hourly_avg['hour'],
            y=hourly_avg['view_item_rate'],
            name='View Item Rate',
            marker_color='lightblue'
        ))
        
        fig_conversion.add_trace(go.Bar(
            x=hourly_avg['hour'],
            y=hourly_avg['add_to_cart_rate'],
            name='Add to Cart Rate',
            marker_color='lightgreen'
        ))
        
        fig_conversion.add_trace(go.Bar(
            x=hourly_avg['hour'],
            y=hourly_avg['conversion_rate'],
            name='Conversion Rate',
            marker_color='salmon'
        ))
        
        fig_conversion.update_layout(
            title='Tasas de Conversión por Hora',
            xaxis_title='Hora',
            yaxis_title='Tasa (%)',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig_conversion, use_container_width=True)
    
    with col2:
        # Scatter: Sesiones vs Conversión
        fig_scatter = px.scatter(
            hourly_avg,
            x='sessions',
            y='conversion_rate',
            size='order_sessions',
            color='hour_int',
            hover_data=['hour'],
            title='Volumen vs Conversión por Hora',
            labels={
                'sessions': 'Sesiones Promedio',
                'conversion_rate': 'Tasa Conversión (%)',
                'order_sessions': 'Compras',
                'hour_int': 'Hora'
            },
            color_continuous_scale='Viridis'
        )
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Análisis por día de la semana
    st.subheader("📅 Análisis por Día de la Semana")
    
    # Agregar por día de la semana
    weekday_avg = df.groupby('weekday').agg({
        'sessions': 'mean',
        'pageviews': 'mean',
        'view_item_sessions': 'mean',
        'add_to_cart_sessions': 'mean',
        'order_sessions': 'mean',
        'conversion_rate': 'mean'
    }).reset_index()
    
    # Reordenar días de la semana
    weekday_avg['weekday_sort'] = weekday_avg['weekday'].str.split(' - ').str[0].astype(int)
    weekday_avg = weekday_avg.sort_values('weekday_sort')
    weekday_avg['weekday_name'] = weekday_avg['weekday'].str.split(' - ').str[1]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sesiones por día de la semana
        fig_weekday_sessions = px.bar(
            weekday_avg,
            x='weekday_name',
            y='sessions',
            title='Sesiones Promedio por Día de la Semana',
            labels={'sessions': 'Sesiones', 'weekday_name': 'Día'},
            color='sessions',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_weekday_sessions, use_container_width=True)
    
    with col2:
        # Conversión por día de la semana
        fig_weekday_conv = px.bar(
            weekday_avg,
            x='weekday_name',
            y='conversion_rate',
            title='Tasa de Conversión por Día',
            labels={'conversion_rate': 'Conversión (%)', 'weekday_name': 'Día'},
            color='conversion_rate',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_weekday_conv, use_container_width=True)
    
    # Identificar mejores y peores horas
    st.subheader("💡 Insights: Mejores y Peores Horas")
    
    # Top 5 horas por sesiones
    top_hours_sessions = hourly_avg.nlargest(5, 'sessions')
    bottom_hours_sessions = hourly_avg.nsmallest(5, 'sessions')
    
    # Top 5 horas por conversión
    top_hours_conversion = hourly_avg.nlargest(5, 'conversion_rate')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**🚀 Top 5 Horas (Mayor Tráfico):**")
        for _, row in top_hours_sessions.iterrows():
            st.write(f"- **{row['hour']}**: {row['sessions']:.0f} sesiones")
    
    with col2:
        st.write("**😴 Top 5 Horas (Menor Tráfico):**")
        for _, row in bottom_hours_sessions.iterrows():
            st.write(f"- **{row['hour']}**: {row['sessions']:.0f} sesiones")
    
    with col3:
        st.write("**💰 Top 5 Horas (Mayor Conversión):**")
        for _, row in top_hours_conversion.iterrows():
            st.write(f"- **{row['hour']}**: {row['conversion_rate']:.2f}%")
    
    # Tabla detallada
    st.subheader("📋 Datos Detallados por Hora")
    
    display_df = hourly_avg[[
        'hour', 'sessions', 'pageviews', 'view_item_sessions', 
        'add_to_cart_sessions', 'order_sessions', 
        'view_item_rate', 'add_to_cart_rate', 'conversion_rate'
    ]].copy()
    
    st.dataframe(display_df.style.format({
        'sessions': '{:.0f}',
        'pageviews': '{:.0f}',
        'view_item_sessions': '{:.0f}',
        'add_to_cart_sessions': '{:.0f}',
        'order_sessions': '{:.0f}',
        'view_item_rate': '{:.2f}%',
        'add_to_cart_rate': '{:.2f}%',
        'conversion_rate': '{:.2f}%'
    }), use_container_width=True)
    
    # Recomendaciones
    st.subheader("🎯 Recomendaciones")
    
    peak_hour = top_hours_sessions.iloc[0]
    best_conversion_hour = top_hours_conversion.iloc[0]
    
    st.info(f"""
    **Optimización de Horarios:**
    
    - 🕐 **Hora pico de tráfico:** {peak_hour['hour']} con {peak_hour['sessions']:.0f} sesiones promedio
    - 💰 **Mejor hora para conversión:** {best_conversion_hour['hour']} con {best_conversion_hour['conversion_rate']:.2f}% de conversión
    - 📢 **Recomendación:** Programa campañas de marketing y promociones durante las horas pico
    - ⚡ **Consejo:** Asegura que el sitio esté optimizado durante las horas de mayor tráfico
    """)
    
    # Botón de descarga
    if st.button("📥 Descargar Datos CSV", key="download_hourly_performance"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name="hourly_sessions_performance.csv",
            mime="text/csv"
        )

def mostrar_session_path_analysis(df):
    """Visualización para Session Path Analysis - CON SANKEY MEJORADO"""
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
    
    # ========================================
    # SANKEY DIAGRAM MEJORADO
    # ========================================
    st.subheader("🔄 Flujo de Navegación (Sankey Diagram)")
    
    # Control de número de rutas a mostrar
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("💡 **Tip**: Reduce el número de rutas si el diagrama se ve sobrecargado")
    with col2:
        num_routes = st.selectbox(
            "Rutas a mostrar:",
            [10, 15, 20, 30, 50],
            index=2,  # Default: 20
            key="sankey_routes"
        )
    
    # Preparar datos para Sankey (Top N rutas más comunes)
    sankey_data = df_filtered.nlargest(num_routes, 'session_count')
    
    # Crear nodos únicos con prefijos para evitar colisiones
    # Estrategia: añadir sufijo _prev, _curr, _next a cada página según su posición
    prev_pages = sankey_data['previous_page_short'].unique()
    curr_pages = sankey_data['current_page_short'].unique()
    next_pages = sankey_data['next_page_short'].unique()
    
    # Crear diccionarios de mapeo con sufijos para evitar duplicados
    prev_dict = {page: f"{page} [entrada]" if page == '(entrance)' else f"{page} ←" for page in prev_pages}
    curr_dict = {page: f"{page} [página]" for page in curr_pages}
    next_dict = {page: f"{page} [salida]" if page == '(exit)' else f"{page} →" for page in next_pages}
    
    # Crear lista de todos los nodos únicos
    all_nodes = []
    all_nodes.extend(prev_dict.values())
    all_nodes.extend([node for node in curr_dict.values() if node not in all_nodes])
    all_nodes.extend([node for node in next_dict.values() if node not in all_nodes])
    
    # Crear mapeo de índices
    node_indices = {node: idx for idx, node in enumerate(all_nodes)}
    
    # Crear links para el diagrama - PARTE 1: previous → current
    source_indices_1 = []
    target_indices_1 = []
    values_1 = []
    
    for _, row in sankey_data.iterrows():
        prev_node = prev_dict[row['previous_page_short']]
        curr_node = curr_dict[row['current_page_short']]
        
        source_indices_1.append(node_indices[prev_node])
        target_indices_1.append(node_indices[curr_node])
        values_1.append(row['session_count'])
    
    # Crear links para el diagrama - PARTE 2: current → next
    source_indices_2 = []
    target_indices_2 = []
    values_2 = []
    
    for _, row in sankey_data.iterrows():
        curr_node = curr_dict[row['current_page_short']]
        next_node = next_dict[row['next_page_short']]
        
        source_indices_2.append(node_indices[curr_node])
        target_indices_2.append(node_indices[next_node])
        values_2.append(row['session_count'])
    
    # Combinar ambas partes
    all_sources = source_indices_1 + source_indices_2
    all_targets = target_indices_1 + target_indices_2
    all_values = values_1 + values_2
    
    # Colores personalizados para nodos
    node_colors = []
    for node in all_nodes:
        if '[entrada]' in node or '(entrance)' in node:
            node_colors.append('rgba(76, 175, 80, 0.8)')  # Verde para entradas
        elif '[salida]' in node or '(exit)' in node:
            node_colors.append('rgba(244, 67, 54, 0.8)')  # Rojo para salidas
        else:
            node_colors.append('rgba(33, 150, 243, 0.8)')  # Azul para páginas intermedias
    
    # Crear Sankey diagram MEJORADO
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color="white", width=2),
            label=all_nodes,
            color=node_colors,
            customdata=[node.replace(' [entrada]', '').replace(' [salida]', '').replace(' [página]', '').replace(' ←', '').replace(' →', '') for node in all_nodes],
            hovertemplate='%{customdata}<br>%{value} sesiones<extra></extra>'
        ),
        link=dict(
            source=all_sources,
            target=all_targets,
            value=all_values,
            color="rgba(0, 0, 0, 0.2)",
            hovertemplate='%{value} sesiones<extra></extra>'
        )
    )])
    
    fig_sankey.update_layout(
        title=f"Diagrama de Flujo de Navegación (Top {num_routes} Rutas)",
        height=800,
        font=dict(size=11, family="Arial"),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig_sankey, use_container_width=True)
    
    # Leyenda de colores
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🟢 **Verde**: Páginas de entrada")
    with col2:
        st.markdown("🔵 **Azul**: Páginas intermedias")
    with col3:
        st.markdown("🔴 **Rojo**: Páginas de salida")
    
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
