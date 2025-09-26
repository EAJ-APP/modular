import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import Settings
from utils.helpers import safe_divide

def mostrar_comparativa_eventos(df):
    """Visualización para comparativa completa de eventos (con funnel como antes)"""
    st.subheader("📊 Funnel de Ecommerce")
    
    if df.empty:
        st.warning("No hay datos disponibles para el rango seleccionado")
        return
    
    # Mostrar tabla con datos crudos
    st.dataframe(df.style.format({
        'total_events': '{:,}',
        'unique_users': '{:,}'
    }))
    
    # Agregar datos por tipo de evento (suma total)
    event_totals = df.groupby('event_name').agg({
        'total_events': 'sum',
        'unique_users': 'sum'
    }).reset_index()
    
    # Crear datos para el funnel
    funnel_data = []
    for event_type in Settings.FUNNEL_EVENTS:
        event_data = event_totals[event_totals['event_name'] == event_type]
        if not event_data.empty:
            funnel_data.append({
                'event_name': event_type,
                'total_events': event_data['total_events'].values[0],
                'unique_users': event_data['unique_users'].values[0]
            })
        else:
            funnel_data.append({
                'event_name': event_type,
                'total_events': 0,
                'unique_users': 0
            })
    
    funnel_df = pd.DataFrame(funnel_data)
    
    # Calcular tasas de conversión con manejo de zeros
    page_views = funnel_df[funnel_df['event_name'] == 'page_view']['total_events'].values[0]
    view_items = funnel_df[funnel_df['event_name'] == 'view_item']['total_events'].values[0]
    add_to_cart = funnel_df[funnel_df['event_name'] == 'add_to_cart']['total_events'].values[0]
    begin_checkout = funnel_df[funnel_df['event_name'] == 'begin_checkout']['total_events'].values[0]
    purchases = funnel_df[funnel_df['event_name'] == 'purchase']['total_events'].values[0]
    
    # Mostrar métricas de conversión
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        view_item_rate = safe_divide(view_items, page_views) * 100
        st.metric("Tasa View Item", f"{view_item_rate:.2f}%")
    with col2:
        add_to_cart_rate = safe_divide(add_to_cart, view_items) * 100
        st.metric("Tasa Add to Cart", f"{add_to_cart_rate:.2f}%")
    with col3:
        checkout_rate = safe_divide(begin_checkout, view_items) * 100
        st.metric("Tasa Checkout", f"{checkout_rate:.2f}%")
    with col4:
        purchase_rate = safe_divide(purchases, view_items) * 100
        st.metric("Tasa Compra", f"{purchase_rate:.2f}%")
    
    # Gráfico de funnel (solo mostrar eventos con datos)
    funnel_events = []
    funnel_values = []
    event_labels = {
        'page_view': 'Page Views',
        'view_item': 'View Item', 
        'add_to_cart': 'Add to Cart',
        'begin_checkout': 'Begin Checkout',
        'purchase': 'Purchase'
    }
    
    for event_type in Settings.FUNNEL_EVENTS:
        event_value = funnel_df[funnel_df['event_name'] == event_type]['total_events'].values[0]
        if event_value > 0:
            funnel_events.append(event_labels[event_type])
            funnel_values.append(event_value)
    
    if funnel_values:
        fig_funnel = go.Figure(go.Funnel(
            y=funnel_events,
            x=funnel_values,
            textinfo="value+percent initial",
            opacity=0.8,
            marker={"color": list(Settings.CHART_COLORS.values())[:len(funnel_events)]}
        ))
        
        fig_funnel.update_layout(title="Funnel de Conversión de Ecommerce")
        st.plotly_chart(fig_funnel, use_container_width=True)

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
    
    # Gráfico combinado (ingresos + transacciones)
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
    
    # Configurar layout con doble eje Y
    fig.update_layout(
        title='Ingresos vs Compras',
        xaxis=dict(title='Fecha', tickangle=45),
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

def mostrar_productos_mas_vendidos(df):
    """Performance de productos por ingresos (CON NOMBRE)"""
    st.subheader("🏆 Productos Más Vendidos por Ingresos")
    
    if df.empty:
        st.warning("No hay datos de productos vendidos para el rango seleccionado")
        return
    
    # Mostrar tabla con datos crudos
    st.dataframe(df.style.format({
        'total_quantity_sold': '{:,}',
        'total_purchases': '{:,}',
        'total_revenue': '€{:,.2f}'
    }))
    
    # Calcular métricas generales
    total_revenue = df['total_revenue'].sum()
    total_quantity = df['total_quantity_sold'].sum()
    avg_revenue_per_product = safe_divide(total_revenue, len(df))
    
    # Mostrar métricas clave
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ingresos Totales Productos", f"€{total_revenue:,.2f}")
    with col2:
        st.metric("Cantidad Total Vendida", f"{total_quantity:,}")
    with col3:
        st.metric("Ingreso Promedio por Producto", f"€{avg_revenue_per_product:,.2f}")
    
    # Gráfico de barras - Top 10 productos por ingresos
    top_products = df.head(10).copy()
    
    fig_bar = px.bar(
        top_products,
        y='item_name',
        x='total_revenue',
        orientation='h',
        title='Top 10 Productos por Ingresos',
        labels={'total_revenue': 'Ingresos (€)', 'item_name': 'Nombre del Producto'},
        color='total_revenue',
        color_continuous_scale='Viridis',
        hover_data=['item_id']
    )
    
    fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Gráfico de dispersión: Cantidad vs Ingresos
    fig_scatter = px.scatter(
        df.head(20),
        x='total_quantity_sold',
        y='total_revenue',
        size='total_purchases',
        color='total_revenue',
        hover_name='item_name',
        hover_data=['item_id'],
        title='Relación: Cantidad Vendida vs Ingresos',
        labels={
            'total_quantity_sold': 'Cantidad Total Vendida',
            'total_revenue': 'Ingresos Totales (€)',
            'total_purchases': 'Número de Compras'
        },
        size_max=30
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)

def mostrar_relacion_productos(df):
    """Relación ID vs Nombre de productos"""
    st.subheader("🔍 Relación ID vs Nombre de Productos")
    
    if df.empty:
        st.warning("No hay datos de productos para el rango seleccionado")
        return
    
    # Identificar ineficiencias
    df_ineficiencias = df[
        (df['nombres_por_producto'] > 1) | (df['ids_por_nombre'] > 1)
    ].copy()
    
    # Aplicar formato condicional para resaltar ineficiencias
    def highlight_inefficiencies(row):
        styles = [''] * len(row)
        if row['nombres_por_producto'] > 1 or row['ids_por_nombre'] > 1:
            styles = ['background-color: #ffcccc' for _ in row]
        return styles
    
    # Mostrar tabla completa con resaltado
    st.write("**Tabla completa de relación ID vs Nombre:**")
    styled_df = df.style.format({
        'nombres_por_producto': '{:,}',
        'ids_por_nombre': '{:,}'
    }).apply(highlight_inefficiencies, axis=1)
    
    st.dataframe(styled_df)
    
    # Resumen de ineficiencias
    if not df_ineficiencias.empty:
        st.warning("🚨 **Se detectaron posibles ineficiencias:**")
        
        # Productos con múltiples nombres
        productos_multi_nombre = df_ineficiencias[df_ineficiencias['nombres_por_producto'] > 1]
        if not productos_multi_nombre.empty:
            st.write("**Productos con múltiples nombres:**")
            for _, row in productos_multi_nombre.head(5).iterrows():
                st.write(f"- ID `{row['item_id']}` tiene {int(row['nombres_por_producto'])} nombres diferentes")
        
        # Nombres con múltiples IDs
        nombres_multi_id = df_ineficiencias[df_ineficiencias['ids_por_nombre'] > 1]
        if not nombres_multi_id.empty:
            st.write("**Nombres con múltiples IDs:**")
            for _, row in nombres_multi_id.head(5).iterrows():
                st.write(f"- Nombre `{row['item_name']}` tiene {int(row['ids_por_nombre'])} IDs diferentes")
        
        # Métricas de ineficiencia
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Productos con ineficiencias", len(df_ineficiencias))
        with col2:
            st.metric("% de ineficiencia", f"{(len(df_ineficiencias) / len(df) * 100):.1f}%")
    else:
        st.success("✅ No se detectaron ineficiencias en la relación ID vs Nombre")

def mostrar_funnel_por_producto(df):
    """Funnel de conversión por producto"""
    st.subheader("📊 Funnel de Conversión por Producto")
    
    if df.empty:
        st.warning("No hay datos de funnel por producto para el rango seleccionado")
        return
    
    # Mostrar tabla con datos crudos
    st.dataframe(df.style.format({
        'view_item': '{:,}',
        'add_to_cart': '{:,}',
        'begin_checkout': '{:,}',
        'purchase': '{:,}',
        'add_to_cart_rate': '{:.2f}%',
        'begin_checkout_rate': '{:.2f}%',
        'purchase_rate': '{:.2f}%'
    }))
    
    # Calcular métricas generales
    total_view_items = df['view_item'].sum()
    total_purchases = df['purchase'].sum()
    overall_conversion_rate = safe_divide(total_purchases, total_view_items) * 100
    
    # Mostrar métricas clave
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Visualizaciones", f"{total_view_items:,}")
    with col2:
        st.metric("Total Compras", f"{total_purchases:,}")
    with col3:
        st.metric("Tasa Conversión Global", f"{overall_conversion_rate:.2f}%")
    
    # Top 10 productos por conversión
    top_products = df.head(10).copy()
    
    # Gráfico de funnel por producto (Top 5)
    top_5_products = top_products.head(5)
    
    if not top_5_products.empty:
        # Preparar datos para el gráfico de funnel
        funnel_data = []
        for _, product in top_5_products.iterrows():
            funnel_data.extend([
                {'Producto': product['item_name'], 'Etapa': 'View Item', 'Usuarios': product['view_item']},
                {'Producto': product['item_name'], 'Etapa': 'Add to Cart', 'Usuarios': product['add_to_cart']},
                {'Producto': product['item_name'], 'Etapa': 'Begin Checkout', 'Usuarios': product['begin_checkout']},
                {'Producto': product['item_name'], 'Etapa': 'Purchase', 'Usuarios': product['purchase']}
            ])
        
        funnel_df = pd.DataFrame(funnel_data)
        
        # Gráfico de barras agrupadas
        fig = px.bar(
            funnel_df,
            x='Producto',
            y='Usuarios',
            color='Etapa',
            barmode='group',
            title='Funnel de Conversión por Producto (Top 5)',
            labels={'Usuarios': 'Número de Usuarios', 'Producto': 'Producto'},
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        
        fig.update_layout(xaxis_tickangle=-45, height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de tasas de conversión (Heatmap)
    rates_df = top_products[['item_name', 'add_to_cart_rate', 'begin_checkout_rate', 'purchase_rate']].copy()
    rates_df = rates_df.set_index('item_name')
    
    # Crear heatmap de tasas de conversión
    fig_heatmap = px.imshow(
        rates_df.T,
        labels=dict(x="Producto", y="Tasa de Conversión", color="Porcentaje"),
        title="Tasas de Conversión por Producto (Top 10)",
        aspect="auto",
        color_continuous_scale="Blues"
    )
    
    fig_heatmap.update_layout(height=400)
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Análisis de mejores conversores
    st.subheader("🏅 Productos con Mejor Conversión")
    
    # Producto con mejor tasa de compra
    best_converter = df.loc[df['purchase_rate'].idxmax()] if not df.empty else None
    if best_converter is not None:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Mejor Conversor", best_converter['item_name'])
        with col2:
            st.metric("Tasa de Compra", f"{best_converter['purchase_rate']}%")
        with col3:
            st.metric("Visualizaciones → Compras", f"{best_converter['view_item']} → {best_converter['purchase']}")