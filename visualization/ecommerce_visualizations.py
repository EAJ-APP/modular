def mostrar_ingresos_transacciones(df):
    """Visualización CORREGIDA para ingresos y transacciones"""
    st.subheader("💰 Ingresos y Transacciones")
    
    if df.empty:
        st.warning("No hay datos de transacciones para el rango seleccionado")
        return
    
    # Convertir la fecha a formato legible
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df['fecha_formateada'] = df['date'].dt.strftime('%d/%m/%Y')
    
    # Mostrar tabla con datos crudos
    st.dataframe(df.style.format({
        'total_purchase_events': '{:,}',
        'unique_transactions': '{:,}',
        'purchase_revenue': '€{:,.2f}',
        'unique_buyers': '{:,}'
    }))
    
    # Calcular métricas totales
    total_purchases = df['total_purchase_events'].sum()
    total_revenue = df['purchase_revenue'].sum()
    avg_transaction_value = safe_divide(total_revenue, total_purchases)
    
    # Mostrar métricas clave
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Compras", f"{total_purchases:,}")
    with col2:
        st.metric("Ingresos Totales", f"€{total_revenue:,.2f}")
    with col3:
        st.metric("Ticket Medio", f"€{avg_transaction_value:,.2f}")
    
    # Gráfico combinado (ingresos + transacciones) - VERSIÓN CORREGIDA
    fig = go.Figure()
    
    # Añadir ingresos (línea, eje izquierdo)
    fig.add_trace(go.Scatter(
        x=df['fecha_formateada'], 
        y=df['purchase_revenue'],
        name='Ingresos (€)',
        line=dict(color=Settings.CHART_COLORS['success'], width=3),
        yaxis='y'
    ))
    
    # Añadir compras (barras, eje derecho)
    fig.add_trace(go.Bar(
        x=df['fecha_formateada'],
        y=df['total_purchase_events'],
        name='Compras',
        marker_color=Settings.CHART_COLORS['info'],
        opacity=0.6,
        yaxis='y2'
    ))
    
    # CONFIGURACIÓN CORREGIDA - Sintaxis simplificada
    fig.update_layout(
        title='Ingresos vs Compras',
        xaxis=dict(
            title='Fecha',
            tickangle=45
        ),
        yaxis=dict(
            title='Ingresos (€)',
            titlefont=dict(color=Settings.CHART_COLORS['success']),
            tickfont=dict(color=Settings.CHART_COLORS['success']),
            side='left'
        ),
        yaxis2=dict(
            title='Compras',
            titlefont=dict(color=Settings.CHART_COLORS['info']),
            tickfont=dict(color=Settings.CHART_COLORS['info']),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        legend=dict(x=0.02, y=0.98),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
