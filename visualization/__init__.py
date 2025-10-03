from .cookies_visualizations import (
    mostrar_consentimiento_basico,
    mostrar_consentimiento_por_dispositivo,
    mostrar_consentimiento_real,
    mostrar_evolucion_temporal_consentimiento,       
    mostrar_consentimiento_por_geografia,             
    mostrar_consentimiento_por_fuente_trafico         
)

from .ecommerce_visualizations import (
    mostrar_comparativa_eventos,
    mostrar_ingresos_transacciones,
    mostrar_productos_mas_vendidos,
    mostrar_relacion_productos,
    mostrar_funnel_por_producto
)

from .acquisition_visualizations import (
    mostrar_canales_trafico,
    mostrar_atribucion_marketing,
    mostrar_atribucion_multimodelo,
    mostrar_atribucion_completa
)

from .events_visualizations import (
    mostrar_eventos_flatten,
    mostrar_eventos_resumen,
    mostrar_eventos_por_fecha,
    mostrar_parametros_evento,
    mostrar_metricas_diarias
)

from .users_visualizations import (
    mostrar_retencion_semanal,
    mostrar_clv_sesiones,
    mostrar_tiempo_primera_compra,
    mostrar_landing_page_attribution,
    mostrar_adquisicion_usuarios,
    mostrar_conversion_mensual
)

from .sessions_visualizations import (
    mostrar_low_converting_sessions,
    mostrar_session_path_analysis,
    mostrar_hourly_sessions_performance,
    mostrar_exit_pages_analysis
)

from .common_charts import (
    create_pie_chart,
    create_bar_chart,
    create_funnel_chart
)

__all__ = [
    # Cookies
    'mostrar_consentimiento_basico',
    'mostrar_consentimiento_por_dispositivo', 
    'mostrar_consentimiento_real',
    # Ecommerce
    'mostrar_comparativa_eventos',
    'mostrar_ingresos_transacciones',
    'mostrar_productos_mas_vendidos',
    'mostrar_relacion_productos',
    'mostrar_funnel_por_producto',
    # Acquisition
    'mostrar_canales_trafico',
    'mostrar_atribucion_marketing',
    'mostrar_atribucion_multimodelo',
    'mostrar_atribucion_completa',
    # Events
    'mostrar_eventos_flatten',
    'mostrar_eventos_resumen',
    'mostrar_eventos_por_fecha',
    'mostrar_parametros_evento',
    'mostrar_metricas_diarias',
    # Users
    'mostrar_retencion_semanal',
    'mostrar_clv_sesiones',
    'mostrar_tiempo_primera_compra',
    'mostrar_landing_page_attribution',
    'mostrar_adquisicion_usuarios',
    'mostrar_conversion_mensual',
    # Sessions
    'mostrar_low_converting_sessions',
    'mostrar_session_path_analysis',
    'mostrar_hourly_sessions_performance',
    'mostrar_exit_pages_analysis',
    # Common
    'create_pie_chart',
    'create_bar_chart',
    'create_funnel_chart'
]
