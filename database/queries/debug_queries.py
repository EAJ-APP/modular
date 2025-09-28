def debug_query_modelos(project, dataset, start_date, end_date):
    """Consulta simple para debug - contar modelos disponibles"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Consulta de DEBUG para ver qué modelos se están generando
    WITH events AS (
      SELECT
        user_pseudo_id,
        traffic_source.source AS utm_source,
        traffic_source.medium AS utm_medium,
        traffic_source.name AS utm_campaign,
        event_name
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name IN ('session_start', 'purchase')
      LIMIT 10
    )
    SELECT 
      'DEBUG - Tabla events tiene datos' as status,
      COUNT(*) as total_events,
      COUNT(DISTINCT utm_source) as unique_sources,
      COUNT(DISTINCT utm_medium) as unique_mediums
    FROM events
    """
