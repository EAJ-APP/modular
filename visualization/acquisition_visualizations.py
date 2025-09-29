# REEMPLAZAR solo la función mostrar_atribucion_completa en acquisition_visualizations.py

def mostrar_atribucion_completa(df):
    """Visualización para análisis de atribución completa (7 modelos)"""
    st.subheader("🎯 Atribución Multi-Modelo Completa (7 Modelos)")
    
    if df.empty:
        st.warning("No hay datos de atribución completa para el rango seleccionado")
        return
    
    # Información sobre los modelos
    with st.expander("📚 Información sobre los Modelos de Atribución", expanded=False):
        st.markdown("""
        **7 Modelos Implementados:**
        
        - **🎯 Last Click**: Atribuye el 100% al último touchpoint antes de la conversión
        - **🚀 First Click**: Atribuye el 100% al primer touchpoint del usuario
        - **📊 Linear**: Distribuye equitativamente entre todos los touchpoints
        - **⏰ Time Decay**: Mayor peso a los touchpoints más recientes
        - **⚖️ Position Based**: 40% primer click, 40% último click, 20% intermedios
        - **🔍 Last Non-Direct**: Como Last Click pero ignora tráfico directo
        - **🤖 Data Driven**: Combinación algorítmica de múltiples factores
        """)
    
    # Resumen ejecutivo
    st.subheader("📈 Resumen Ejecutivo")
    
    total_models = df['attribution_model'].nunique()
    total_channels = df['utm_source'].nunique()
    
    # Calcular valores únicos por modelo
    model_summary = df.groupby('attribution_model').agg({
        'attributed_revenue': 'sum',
        'attributed_conversions': 'sum'
    }).reset_index()
    
    total_revenue = model_summary['attributed_revenue'].sum()
    total_conversions = model_summary['attributed_conversions'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Modelos de Atribución", total_models)
    with col2:
        st.metric("Canales Únicos", total_channels)
    with col3:
        st.metric("Ingresos Atribuidos", f"€{total_revenue:,.0f}")
    with col4:
        st.metric("Conversiones Atribuidas", f"{total_conversions:,.0f}")
    
    # Mostrar los modelos realmente detectados
    st.write(f"**Modelos analizados:** {', '.join(df['attribution_model'].unique())}")
    
    # Comparativa entre modelos
    st.subheader("📊 Comparativa entre Modelos")
    
    model_comparison = df.groupby('attribution_model').agg({
        'attributed_revenue': 'sum',
        'attributed_conversions': 'sum',
        'conversion_rate': 'mean',
        'revenue_per_conversion': 'mean'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_revenue = px.bar(
            model_comparison,
            x='attribution_model',
            y='attributed_revenue',
            title='Ingresos Atribuidos por Modelo',
            labels={'attribution_model': 'Modelo', 'attributed_revenue': 'Ingresos (€)'},
            color='attributed_revenue',
            color_continuous_scale='Viridis'
        )
        fig_revenue.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with col2:
        fig_conversions = px.bar(
            model_comparison,
            x='attribution_model',
            y='attributed_conversions',
            title='Conversiones Atribuidas por Modelo',
            labels={'attribution_model': 'Modelo', 'attributed_conversions': 'Conversiones'},
            color='attributed_conversions',
            color_continuous_scale='Blues'
        )
        fig_conversions.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_conversions, use_container_width=True)
    
    # Análisis de diferencias entre modelos
    st.subheader("🔄 Análisis de Diferencias entre Modelos")
    
    # Pivot para comparación
    pivot_data = df.pivot_table(
        index=['utm_source', 'utm_medium'],
        columns='attribution_model',
        values='attributed_revenue',
        aggfunc='sum'
    ).fillna(0)
    
    if not pivot_data.empty:
        # Calcular desviación estándar entre modelos (variabilidad)
        pivot_data['std_deviation'] = pivot_data.std(axis=1)
        pivot_data['mean_revenue'] = pivot_data.mean(axis=1)
        pivot_data['variability'] = (pivot_data['std_deviation'] / pivot_data['mean_revenue']).round(3)
        
        st.write("**Canales con Mayor Variabilidad entre Modelos:**")
        high_variability = pivot_data.nlargest(10, 'variability')
        st.dataframe(high_variability[['mean_revenue', 'std_deviation', 'variability']].style.format({
            'mean_revenue': '€{:,.2f}',
            'std_deviation': '€{:,.2f}',
            'variability': '{:.3f}'
        }))
    
    # SOLUCIÓN DEFINITIVA: Usar on_change callback en lugar de monitorear cambios
    st.subheader("🔍 Análisis Detallado por Modelo")
    
    # Key único para el selectbox de esta función
    selectbox_key = 'attribution_complete_model_selector'
    
    # Inicializar session_state si no existe
    if selectbox_key not in st.session_state:
        st.session_state[selectbox_key] = df['attribution_model'].unique()[0] if len(df['attribution_model'].unique()) > 0 else ""
    
    # Función callback que se ejecuta ANTES del rerun
    def on_model_change():
        # Este callback se ejecuta antes del rerun, manteniendo el contexto
        pass
    
    # Selectbox con callback
    selected_model = st.selectbox(
        "Seleccionar modelo para análisis detallado:",
        options=list(df['attribution_model'].unique()),
        index=list(df['attribution_model'].unique()).index(st.session_state[selectbox_key]) if st.session_state[selectbox_key] in df['attribution_model'].unique() else 0,
        key=selectbox_key,
        on_change=on_model_change
    )
    
    if selected_model:
        model_data = df[df['attribution_model'] == selected_model].nlargest(15, 'attributed_revenue')
        
        if not model_data.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top canales por ingresos
                fig_top_channels = px.treemap(
                    model_data,
                    path=['utm_source', 'utm_medium'],
                    values='attributed_revenue',
                    title=f'Distribución de Ingresos - {selected_model}',
                    color='attributed_revenue',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_top_channels, use_container_width=True)
            
            with col2:
                # Eficiencia por canal
                fig_efficiency = px.scatter(
                    model_data.head(20),
                    x='touchpoints',
                    y='attributed_revenue',
                    size='conversion_rate',
                    color='utm_medium',
                    hover_name='utm_source',
                    title=f'Eficiencia por Canal - {selected_model}',
                    labels={
                        'touchpoints': 'Touchpoints',
                        'attributed_revenue': 'Ingresos Atribuidos (€)',
                        'conversion_rate': 'Tasa Conversión'
                    }
                )
                st.plotly_chart(fig_efficiency, use_container_width=True)
            
            # Tabla detallada
            st.dataframe(model_data.style.format({
                'touchpoints': '{:,}',
                'conversions': '{:,}',
                'revenue': '€{:,.2f}',
                'attributed_conversions': '{:.2f}',
                'attributed_revenue': '€{:,.2f}',
                'conversion_rate': '{:.2f}%',
                'revenue_per_conversion': '€{:,.2f}'
            }))
        else:
            st.warning(f"No hay datos para el modelo {selected_model}")
    
    # Análisis por dispositivo
    st.subheader("📱 Análisis por Dispositivo")
    
    device_analysis = df.groupby(['attribution_model', 'device_type']).agg({
        'attributed_revenue': 'sum',
        'attributed_conversions': 'sum'
    }).reset_index()
    
    if not device_analysis.empty:
        fig_device = px.bar(
            device_analysis,
            x='attribution_model',
            y='attributed_revenue',
            color='device_type',
            barmode='group',
            title='Ingresos Atribuidos por Modelo y Dispositivo',
            labels={'attribution_model': 'Modelo', 'attributed_revenue': 'Ingresos (€)'}
        )
        fig_device.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_device, use_container_width=True)
