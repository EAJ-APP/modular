def generar_query_consentimiento_basico(project, dataset, start_date, end_date):
    """Consulta básica de consentimiento"""
    return f"""
    SELECT
      privacy_info.analytics_storage AS analytics_storage_status,
      privacy_info.ads_storage AS ads_storage_status,
      COUNT(*) AS total_events,
      COUNT(DISTINCT user_pseudo_id) AS total_users,
      COUNT(DISTINCT CONCAT(user_pseudo_id, '-', 
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id'))) AS total_sessions
    FROM `{project}.{dataset}.events_*`
    WHERE _TABLE_SUFFIX BETWEEN '{start_date.strftime('%Y%m%d')}' AND '{end_date.strftime('%Y%m%d')}'
    GROUP BY 1, 2
    ORDER BY 3 DESC
    """

def generar_query_consentimiento_por_dispositivo(project, dataset, start_date, end_date):
    """Consulta optimizada que garantiza datos diferentes"""
    return f"""
    WITH base_data AS (
      SELECT
        device.category AS device_type,
        CASE
          WHEN privacy_info.analytics_storage IS NULL THEN 'null'
          WHEN LOWER(CAST(privacy_info.analytics_storage AS STRING)) IN ('true', 'yes', '1') THEN 'true'
          ELSE 'false'
        END AS analytics_status,
        CASE
          WHEN privacy_info.ads_storage IS NULL THEN 'null'
          WHEN LOWER(CAST(privacy_info.ads_storage AS STRING)) IN ('true', 'yes', '1') THEN 'true'
          ELSE 'false'
        END AS ads_status,
        user_pseudo_id,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date.strftime('%Y%m%d')}' AND '{end_date.strftime('%Y%m%d')}'
    )
    SELECT
      device_type,
      analytics_status,
      ads_status,
      COUNT(*) AS total_events,
      COUNT(DISTINCT user_pseudo_id) AS total_users,
      COUNT(DISTINCT CONCAT(user_pseudo_id, '-', session_id)) AS total_sessions
    FROM base_data
    GROUP BY 1, 2, 3
    ORDER BY device_type, total_events DESC
    """

def generar_query_consentimiento_real(project, dataset, start_date, end_date):
    """Nueva consulta para porcentaje real de consentimiento"""
    return f"""
    SELECT
        CASE
            WHEN privacy_info.analytics_storage IS NULL THEN 'No Definido'
            WHEN LOWER(CAST(privacy_info.analytics_storage AS STRING)) IN ('false', 'no', '0') THEN 'Denegado'
            ELSE 'Aceptado'
        END AS consent_status,
        COUNT(*) AS total_events,
        ROUND(COUNT(*) / SUM(COUNT(*)) OVER() * 100, 2) AS event_percentage
    FROM `{project}.{dataset}.events_*`
    WHERE _TABLE_SUFFIX BETWEEN '{start_date.strftime('%Y%m%d')}' AND '{end_date.strftime('%Y%m%d')}'
    GROUP BY 1
    ORDER BY total_events DESC
    """