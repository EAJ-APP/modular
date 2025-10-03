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
    """Visualización SIMPLIFICADA para ingresos y transacciones"""
    st.subheader("💰 Ingresos y Transacciones")
    
    if df.empty:
        st.warning("No hay datos de transacciones para el rango seleccionado")
        return
    
    # Convertir la fecha
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df['fecha_formateada'] = df['date'].dt.strftime('%d/%m/%Y')
    
    # Mostrar tabla
    st.dataframe(df)
    
    # Métricas
    total_purchases = df['total_purchase_events'].sum()
    total_revenue = df['purchase_revenue'].sum()
    avg_transaction_value = safe_divide(total_revenue, total_purchases)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Compras", f"{total_purchases:,}")
    with col2:
        st.metric("Ingresos Totales", f"€{total_revenue:,.2f}")
    with col3:
        st.metric("Ticket Medio", f"€{avg_transaction_value:,.2f}")
    
    # GRÁFICO SIMPLIFICADO - Solo ingresos
    try:
        fig = px.line(df, x='fecha_formateada', y='purchase_revenue', 
                     title='Ingresos por Día', labels={'purchase_revenue': 'Ingresos (€)'})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error creando gráfico: {e}")
        st.info("Mostrando datos en tabla expandida:")
        st.dataframe(df)

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

def mostrar_combos_cross_selling(df):
    """Visualización para análisis de combos y cross-selling"""
    st.subheader("🔄 Análisis de Combos y Cross-Selling")
    
    if df.empty:
        st.warning("No hay datos de combos para el rango seleccionado")
        return
    
    # CREAR combo_label al inicio
    df['combo_label'] = df['product_a'] + ' + ' + df['product_b']
    df['combo_label_short'] = df['combo_label'].apply(
        lambda x: x[:60] + '...' if len(x) > 60 else x
    )
    
    # Información educativa sobre Market Basket Analysis
    with st.expander("📚 ¿Qué es Market Basket Analysis?", expanded=False):
        st.markdown("""
        **Market Basket Analysis** identifica productos que frecuentemente se compran juntos.
        
        **Métricas clave:**
        
        - **Lift**: Mide la sinergia entre productos
          - Lift = 1: No hay relación (independientes)
          - Lift > 1: Comprar A aumenta probabilidad de comprar B ✅
          - Lift < 1: Comprar A reduce probabilidad de comprar B ❌
        
        - **Confidence A→B**: De los que compraron A, ¿qué % también compró B?
          - Ejemplo: 60% = 6 de cada 10 compradores de A también compraron B
        
        - **Support**: ¿Qué % del total de transacciones incluyen ambos productos?
          - Indica qué tan común es el combo
        
        - **Combo Strength Score**: Métrica combinada para ranking (0-10+)
          - Combina lift, confidence y frecuencia en una sola métrica
        
        **Aplicaciones prácticas:**
        - Crear bundles estratégicos
        - Optimizar recomendaciones "Quién compró X también compró Y"
        - Layout de productos en tienda física/online
        - Cross-selling en checkout
        """)
    
    # Métricas generales
    total_combos = len(df)
    avg_lift = df['lift'].mean()
    avg_confidence = df['confidence_a_to_b'].mean()
    best_combo = df.iloc[0] if len(df) > 0 else None
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Combos Identificados", f"{total_combos}")
    with col2:
        st.metric("Lift Promedio", f"{avg_lift:.2f}")
    with col3:
        st.metric("Confidence Promedio", f"{avg_confidence:.1f}%")
    with col4:
        if best_combo is not None:
            st.metric("Mejor Combo Score", f"{best_combo['combo_strength_score']:.1f}")
    
    # Filtros interactivos
    st.subheader("🔍 Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_lift = st.slider(
            "Lift mínimo:",
            min_value=1.0,
            max_value=float(df['lift'].max()) if len(df) > 0 else 5.0,
            value=1.0,
            step=0.1,
            key="combo_min_lift",
            help="Lift > 1 significa sinergia positiva"
        )
    
    with col2:
        min_confidence = st.slider(
            "Confidence mínima (%):",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=5.0,
            key="combo_min_confidence",
            help="% de compradores de A que también compraron B"
        )
    
    with col3:
        min_frequency = st.slider(
            "Compras juntas mínimas:",
            min_value=1,
            max_value=int(df['times_bought_together'].max()) if len(df) > 0 else 50,
            value=3,
            key="combo_min_frequency",
            help="Número mínimo de co-ocurrencias"
        )
    
    # Aplicar filtros
    df_filtered = df[
        (df['lift'] >= min_lift) &
        (df['confidence_a_to_b'] >= min_confidence) &
        (df['times_bought_together'] >= min_frequency)
    ].copy()
    
    if df_filtered.empty:
        st.warning("⚠️ No hay combos que cumplan los filtros. Intenta reducir los valores.")
        return
    
    st.info(f"📊 Mostrando **{len(df_filtered)}** combos que cumplen los filtros")
    
    # Top 20 combos por Strength Score
    st.subheader("🏆 Top 20 Combos Más Fuertes")
    
    top_combos = df_filtered.head(20).copy()
    
    fig_top_combos = px.bar(
        top_combos,
        x='combo_strength_score',
        y='combo_label_short',
        orientation='h',
        color='lift',
        title='Top 20 Combos por Strength Score',
        labels={
            'combo_strength_score': 'Combo Strength Score',
            'combo_label_short': 'Combo de Productos',
            'lift': 'Lift'
        },
        color_continuous_scale='Viridis',
        hover_data={
            'times_bought_together': True,
            'confidence_a_to_b': ':.1f',
            'avg_basket_value': ':$.2f'
        }
    )
    fig_top_combos.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=700
    )
    st.plotly_chart(fig_top_combos, use_container_width=True)
    
    # Scatter Plot: Lift vs Confidence
    st.subheader("💎 Matriz: Frecuencia vs Valor del Carrito")
    
    fig_scatter = px.scatter(
        df_filtered.head(100),
        x='times_bought_together',
        y='avg_basket_value',
        size='combo_strength_score',
        color='lift',
        hover_data={
            'product_a': True,
            'product_b': True,
            'confidence_a_to_b': ':.1f'
        },
        title='Relación entre Frecuencia y Valor del Carrito (Top 100 combos)',
        labels={
            'times_bought_together': 'Veces Comprados Juntos',
            'avg_basket_value': 'Valor Promedio Carrito (€)',
            'lift': 'Lift',
            'combo_strength_score': 'Strength Score'
        },
        color_continuous_scale='RdYlGn',
        size_max=60
    )
    
    # Añadir cuadrantes
    median_freq = df_filtered['times_bought_together'].median()
    median_value = df_filtered['avg_basket_value'].median()
    
    fig_scatter.add_vline(
        x=median_freq,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Freq. Mediana: {median_freq:.0f}"
    )
    fig_scatter.add_hline(
        y=median_value,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Valor Mediano: €{median_value:.0f}"
    )
    
    fig_scatter.update_layout(height=600)
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Interpretación de cuadrantes
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🌟 Combos ESTRELLA (Alta freq + Alto valor):**")
        star_combos = df_filtered[
            (df_filtered['times_bought_together'] > median_freq) &
            (df_filtered['avg_basket_value'] > median_value)
        ].head(5)
        
        if not star_combos.empty:
            for _, row in star_combos.iterrows():
                st.write(f"- **{row['product_a']}** + **{row['product_b']}**")
                st.write(f"  Comprados juntos: {row['times_bought_together']} veces | Valor: €{row['avg_basket_value']:.2f}")
        else:
            st.write("No hay combos en esta categoría con los filtros actuales")
    
    with col2:
        st.write("**💎 Combos PREMIUM (Bajo volumen + Alto valor):**")
        premium_combos = df_filtered[
            (df_filtered['times_bought_together'] <= median_freq) &
            (df_filtered['avg_basket_value'] > median_value)
        ].head(5)
        
        if not premium_combos.empty:
            for _, row in premium_combos.iterrows():
                st.write(f"- **{row['product_a']}** + **{row['product_b']}**")
                st.write(f"  Comprados juntos: {row['times_bought_together']} veces | Valor: €{row['avg_basket_value']:.2f}")
            st.info("💡 Productos premium con menor frecuencia pero alto valor.")
        else:
            st.write("No hay combos en esta categoría con los filtros actuales")
    
    # Análisis por valor de basket
    st.subheader("💰 Análisis por Valor de Basket")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top combos por valor de basket
        top_value = df_filtered.nlargest(15, 'avg_basket_value')
        
        fig_value = px.bar(
            top_value,
            x='avg_basket_value',
            y='combo_label_short',
            orientation='h',
            title='Top 15 Combos por Valor Promedio del Carrito',
            labels={
                'avg_basket_value': 'Valor Promedio (€)',
                'combo_label_short': 'Combo'
            },
            color='avg_basket_value',
            color_continuous_scale='Greens'
        )
        fig_value.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
        st.plotly_chart(fig_value, use_container_width=True)
    
    with col2:
        # Top por frecuencia
        top_freq = df_filtered.nlargest(15, 'times_bought_together')
        
        fig_freq = px.bar(
            top_freq,
            x='times_bought_together',
            y='combo_label_short',
            orientation='h',
            title='Top 15 Combos Más Frecuentes',
            labels={
                'times_bought_together': 'Veces Comprados Juntos',
                'combo_label_short': 'Combo'
            },
            color='times_bought_together',
            color_continuous_scale='Blues'
        )
        fig_freq.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
        st.plotly_chart(fig_freq, use_container_width=True)
    
    # Análisis por dispositivo
    st.subheader("📱 Análisis por Dispositivo")
    
    # Calcular totales
    total_desktop = df_filtered['desktop_purchases'].sum()
    total_mobile = df_filtered['mobile_purchases'].sum()
    total_tablet = df_filtered['tablet_purchases'].sum()
    total_purchases = total_desktop + total_mobile + total_tablet
    
    if total_purchases > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Desktop", f"{total_desktop:,}", f"{total_desktop/total_purchases*100:.1f}%")
        with col2:
            st.metric("Mobile", f"{total_mobile:,}", f"{total_mobile/total_purchases*100:.1f}%")
        with col3:
            st.metric("Tablet", f"{total_tablet:,}", f"{total_tablet/total_purchases*100:.1f}%")
        
        # Gráfico de distribución por dispositivo
        device_data = pd.DataFrame({
            'Dispositivo': ['Desktop', 'Mobile', 'Tablet'],
            'Compras': [total_desktop, total_mobile, total_tablet]
        })
        
        fig_device = px.pie(
            device_data,
            values='Compras',
            names='Dispositivo',
            title='Distribución de Combos por Dispositivo',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_device, use_container_width=True)
    else:
        st.info("No hay datos de dispositivo disponibles")
    
    # Top productos en combos
    st.subheader("🎯 Productos Más Presentes en Combos")
    
    # Contar apariciones de cada producto
    product_counts = {}
    for _, row in df_filtered.iterrows():
        product_counts[row['product_a']] = product_counts.get(row['product_a'], 0) + 1
        product_counts[row['product_b']] = product_counts.get(row['product_b'], 0) + 1
    
    top_products = pd.DataFrame([
        {'Producto': prod, 'Apariciones': count}
        for prod, count in sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    ])
    
    if not top_products.empty:
        fig_products = px.bar(
            top_products,
            x='Apariciones',
            y='Producto',
            orientation='h',
            title='Top 15 Productos Más Presentes en Combos (Productos Ancla)',
            labels={'Apariciones': 'Número de Combos', 'Producto': 'Producto'},
            color='Apariciones',
            color_continuous_scale='Purples'
        )
        fig_products.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
        st.plotly_chart(fig_products, use_container_width=True)
        
        st.info("""
        **💡 Productos Ancla:**
        - Generan muchas ventas adicionales
        - Ideales para promociones "gateway"
        - Colócalos estratégicamente en el sitio
        - Úsalos como punto de entrada en bundles
        """)
    
    # Tabla detallada de combos
    st.subheader("📋 Tabla Detallada de Combos")
    
    display_df = df_filtered.head(50)[[
        'product_a', 'product_b', 'times_bought_together',
        'avg_basket_value', 'combo_strength_score'
    ]]
    
    st.dataframe(display_df.style.format({
        'times_bought_together': '{:,}',
        'avg_basket_value': '€{:,.2f}',
        'combo_strength_score': '{:.2f}'
    }), height=600)
    
    # Recomendaciones accionables
    st.subheader("🎯 Recomendaciones Accionables")
    
    # Identificar mejores oportunidades
    best_bundles = df_filtered.nlargest(5, 'combo_strength_score')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("**✅ Crear Estos Bundles YA:**")
        if not best_bundles.empty:
            for _, row in best_bundles.iterrows():
                st.write(f"**Bundle:** {row['product_a']} + {row['product_b']}")
                st.write(f"- Comprados juntos: {row['times_bought_together']} veces")
                st.write(f"- Valor promedio: €{row['avg_basket_value']:.2f}")
                st.write(f"- Score: {row['combo_strength_score']:.1f}")
                st.divider()
        else:
            st.write("Ajusta los filtros para encontrar bundles óptimos")
    
    with col2:
        st.info("**💡 Cómo Implementar Cross-Selling:**")
        st.markdown("""
        **En la página de producto:**
        - "Quién compró esto también compró..."
        - Mostrar productos del combo
        
        **En el carrito:**
        - "Completa tu compra con..."
        - Ofrecer productos relacionados
        
        **Crear bundles físicos:**
        - Pack productos más vendidos juntos
        - Descuento 10-15% vs compra individual
        
        **Email marketing:**
        - "Basado en tu compra de X, te recomendamos Y"
        - Usar combos frecuentes
        
        **Layout de tienda:**
        - Colocar productos relacionados cerca
        - Secciones de "Combos populares"
        """)
    
    # Estimación de impacto
    st.subheader("💰 Estimación de Impacto")
    
    top_10_combos = df_filtered.head(10)
    
    current_combo_sales = top_10_combos['times_bought_together'].sum()
    avg_combo_value = top_10_combos['avg_basket_value'].mean()
    
    # Escenario: aumentar ventas de combos en 20%
    potential_new_combos = current_combo_sales * 0.20
    potential_revenue = potential_new_combos * avg_combo_value
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Combos Actuales (Top 10)", f"{int(current_combo_sales)}")
    with col2:
        st.metric("Valor Promedio", f"€{avg_combo_value:.2f}")
    with col3:
        st.metric("Potencial +20%", f"+{int(potential_new_combos)} combos")
    
    st.success(f"""
    **💰 Revenue Adicional Estimado:**
    - **{int(potential_new_combos)} combos adicionales/mes**
    - **€{potential_revenue:,.0f}/mes** en ventas adicionales
    - **€{potential_revenue * 12:,.0f}/año** en revenue incremental
    
    *Asumiendo un aumento del 20% mediante cross-selling efectivo*
    """)
    
    # Exportar datos
    st.subheader("📥 Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV completo
        csv_full = df_filtered.to_csv(index=False)
        st.download_button(
            label="📥 Descargar Todos los Combos (CSV)",
            data=csv_full,
            file_name="combos_cross_selling_completo.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # CSV top combos
        csv_top = df_filtered.head(20).to_csv(index=False)
        st.download_button(
            label="⭐ Descargar Top 20 Combos (CSV)",
            data=csv_top,
            file_name="combos_top_20.csv",
            mime="text/csv",
            use_container_width=True
        )
