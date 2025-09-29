from .cookies_queries import (
    generar_query_consentimiento_basico,
    generar_query_consentimiento_por_dispositivo,
    generar_query_consentimiento_real
)

from .ecommerce_queries import (
    generar_query_comparativa_eventos,
    generar_query_ingresos_transacciones,
    generar_query_productos_mas_vendidos,
    generar_query_relacion_productos,
    generar_query_funnel_por_producto
)

from .acquisition_queries import (
    generar_query_canales_trafico,
    generar_query_atribucion_marketing,
    generar_query_atribucion_completa
)

from .events_queries import (
    generar_query_eventos_flatten,
    generar_query_eventos_resumen,
    generar_query_eventos_por_fecha,
    generar_query_parametros_eventos,
    generar_query_metricas_diarias
)

from .users_queries import (
    generar_query_retencion_semanal,
    generar_query_clv_sesiones,
    generar_query_tiempo_primera_compra,
    generar_query_landing_page_attribution,
    generar_query_adquisicion_usuarios,
    generar_query_conversion_mensual
)

from .sessions_queries import (
    generar_query_low_converting_sessions,
    generar_query_session_path_analysis,
    generar_query_hourly_sessions_performance,
    generar_query_exit_pages
)

__all__ = [
    # Cookies
    'generar_query_consentimiento_basico',
    'generar_query_consentimiento_por_dispositivo',
    'generar_query_consentimiento_real',
    # Ecommerce
    'generar_query_comparativa_eventos',
    'generar_query_ingresos_transacciones',
    'generar_query_productos_mas_vendidos',
    'generar_query_relacion_productos',
    'generar_query_funnel_por_producto',
    # Acquisition
    'generar_query_canales_trafico',
    'generar_query_atribucion_marketing',
    'generar_query_atribucion_completa',
    # Events
    'generar_query_eventos_flatten',
    'generar_query_eventos_resumen',
    'generar_query_eventos_por_fecha',
    'generar_query_parametros_eventos',
    'generar_query_metricas_diarias',
    # Users
    'generar_query_retencion_semanal',
    'generar_query_clv_sesiones',
    'generar_query_tiempo_primera_compra',
    'generar_query_landing_page_attribution',
    'generar_query_adquisicion_usuarios',
    'generar_query_conversion_mensual',
    # Sessions
    'generar_query_low_converting_sessions',
    'generar_query_session_path_analysis',
    'generar_query_hourly_sessions_performance',
    'generar_query_exit_pages'
]
