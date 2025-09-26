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

__all__ = [
    'generar_query_consentimiento_basico',
    'generar_query_consentimiento_por_dispositivo',
    'generar_query_consentimiento_real',
    'generar_query_comparativa_eventos',
    'generar_query_ingresos_transacciones',
    'generar_query_productos_mas_vendidos',
    'generar_query_relacion_productos',
    'generar_query_funnel_por_producto'
]