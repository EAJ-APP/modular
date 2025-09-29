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
    'generar_query_metricas_diarias'
]
