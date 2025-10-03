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

def generar_query_evolucion_temporal_consentimiento(project, dataset, start_date, end_date):
    """
    Consulta para análisis de evolución temporal del consentimiento
    Muestra la tendencia día a día de tasas de consentimiento
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Evolución Temporal del Consentimiento
    WITH daily_consent AS (
      SELECT
        PARSE_DATE('%Y%m%d', event_date) AS date,
        -- Conteo de eventos por estado de consentimiento
        COUNT(*) AS total_events,
        
        -- Analytics Storage
        COUNTIF(
          privacy_info.analytics_storage IS NOT NULL 
          AND LOWER(CAST(privacy_info.analytics_storage AS STRING)) IN ('true', 'yes', '1')
        ) AS analytics_granted,
        COUNTIF(
          privacy_info.analytics_storage IS NOT NULL 
          AND LOWER(CAST(privacy_info.analytics_storage AS STRING)) IN ('false', 'no', '0')
        ) AS analytics_denied,
        COUNTIF(privacy_info.analytics_storage IS NULL) AS analytics_undefined,
        
        -- Ads Storage
        COUNTIF(
          privacy_info.ads_storage IS NOT NULL 
          AND LOWER(CAST(privacy_info.ads_storage AS STRING)) IN ('true', 'yes', '1')
        ) AS ads_granted,
        COUNTIF(
          privacy_info.ads_storage IS NOT NULL 
          AND LOWER(CAST(privacy_info.ads_storage AS STRING)) IN ('false', 'no', '0')
        ) AS ads_denied,
        COUNTIF(privacy_info.ads_storage IS NULL) AS ads_undefined,
        
        -- Usuarios y sesiones únicos
        COUNT(DISTINCT user_pseudo_id) AS unique_users,
        COUNT(DISTINCT CONCAT(
          user_pseudo_id, '-',
          CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
        )) AS unique_sessions
        
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
      GROUP BY date
    )
    
    SELECT
      date,
      total_events,
      unique_users,
      unique_sessions,
      
      -- Analytics Storage
      analytics_granted,
      analytics_denied,
      analytics_undefined,
      ROUND(SAFE_DIVIDE(analytics_granted, total_events) * 100, 2) AS analytics_granted_pct,
      ROUND(SAFE_DIVIDE(analytics_denied, total_events) * 100, 2) AS analytics_denied_pct,
      ROUND(SAFE_DIVIDE(analytics_undefined, total_events) * 100, 2) AS analytics_undefined_pct,
      
      -- Ads Storage
      ads_granted,
      ads_denied,
      ads_undefined,
      ROUND(SAFE_DIVIDE(ads_granted, total_events) * 100, 2) AS ads_granted_pct,
      ROUND(SAFE_DIVIDE(ads_denied, total_events) * 100, 2) AS ads_denied_pct,
      ROUND(SAFE_DIVIDE(ads_undefined, total_events) * 100, 2) AS ads_undefined_pct,
      
      -- Tasa de consentimiento combinada (ambos aceptados)
      ROUND(
        SAFE_DIVIDE(
          COUNTIF(
            LOWER(CAST(privacy_info.analytics_storage AS STRING)) IN ('true', 'yes', '1')
            AND LOWER(CAST(privacy_info.ads_storage AS STRING)) IN ('true', 'yes', '1')
          ),
          total_events
        ) * 100, 
        2
      ) AS full_consent_pct
      
    FROM daily_consent
    CROSS JOIN `{project}.{dataset}.events_*`
    WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
      AND PARSE_DATE('%Y%m%d', event_date) = daily_consent.date
    GROUP BY 
      date, total_events, unique_users, unique_sessions,
      analytics_granted, analytics_denied, analytics_undefined,
      ads_granted, ads_denied, ads_undefined
    ORDER BY date
    """

def generar_query_consentimiento_por_geografia(project, dataset, start_date, end_date):
    """
    Consulta para análisis de consentimiento por geografía
    Muestra tasas de consentimiento por país y ciudad
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Consentimiento por Geografía (País y Ciudad)
    WITH geo_consent AS (
      SELECT
        geo.country AS country,
        geo.city AS city,
        geo.continent AS continent,
        geo.region AS region,
        
        -- Conteo de eventos
        COUNT(*) AS total_events,
        COUNT(DISTINCT user_pseudo_id) AS unique_users,
        COUNT(DISTINCT CONCAT(
          user_pseudo_id, '-',
          CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
        )) AS unique_sessions,
        
        -- Analytics Storage
        COUNTIF(
          privacy_info.analytics_storage IS NOT NULL 
          AND LOWER(CAST(privacy_info.analytics_storage AS STRING)) IN ('true', 'yes', '1')
        ) AS analytics_granted,
        
        -- Ads Storage
        COUNTIF(
          privacy_info.ads_storage IS NOT NULL 
          AND LOWER(CAST(privacy_info.ads_storage AS STRING)) IN ('true', 'yes', '1')
        ) AS ads_granted,
        
        -- Ambos aceptados
        COUNTIF(
          LOWER(CAST(privacy_info.analytics_storage AS STRING)) IN ('true', 'yes', '1')
          AND LOWER(CAST(privacy_info.ads_storage AS STRING)) IN ('true', 'yes', '1')
        ) AS both_granted,
        
        -- Ninguno aceptado
        COUNTIF(
          LOWER(CAST(privacy_info.analytics_storage AS STRING)) IN ('false', 'no', '0')
          AND LOWER(CAST(privacy_info.ads_storage AS STRING)) IN ('false', 'no', '0')
        ) AS both_denied
        
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND geo.country IS NOT NULL
      GROUP BY country, city, continent, region
    )
    
    SELECT
      country,
      city,
      continent,
      region,
      total_events,
      unique_users,
      unique_sessions,
      
      -- Conteos
      analytics_granted,
      ads_granted,
      both_granted,
      both_denied,
      
      -- Porcentajes
      ROUND(SAFE_DIVIDE(analytics_granted, total_events) * 100, 2) AS analytics_consent_rate,
      ROUND(SAFE_DIVIDE(ads_granted, total_events) * 100, 2) AS ads_consent_rate,
      ROUND(SAFE_DIVIDE(both_granted, total_events) * 100, 2) AS full_consent_rate,
      ROUND(SAFE_DIVIDE(both_denied, total_events) * 100, 2) AS full_denial_rate,
      
      -- Ranking dentro del país
      RANK() OVER (PARTITION BY country ORDER BY total_events DESC) AS city_rank_in_country
      
    FROM geo_consent
    WHERE total_events >= 10  -- Filtrar localizaciones con volumen significativo
    ORDER BY total_events DESC
    LIMIT 500
    """

def generar_query_consentimiento_por_fuente_trafico(project, dataset, start_date, end_date):
    """
    Consulta para análisis de consentimiento por fuente de tráfico
    Muestra tasas de consentimiento según utm_source, utm_medium, utm_campaign
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Consentimiento por Fuente de Tráfico
    WITH traffic_consent AS (
      SELECT
        -- Fuentes de tráfico
        traffic_source.source AS utm_source,
        traffic_source.medium AS utm_medium,
        traffic_source.name AS utm_campaign,
        
        -- Channel Grouping simplificado
        CASE
          WHEN traffic_source.source IS NULL THEN 'Direct'
          WHEN REGEXP_CONTAINS(traffic_source.source, r'(?i)google|bing|yahoo|duckduckgo')
            AND traffic_source.medium = 'organic' THEN 'Organic Search'
          WHEN REGEXP_CONTAINS(traffic_source.medium, r'(?i)cpc|ppc|paid') THEN 'Paid Search'
          WHEN REGEXP_CONTAINS(traffic_source.source, r'(?i)facebook|instagram|twitter|linkedin|tiktok')
            AND REGEXP_CONTAINS(traffic_source.medium, r'(?i)social|cpc|ppc|paid') THEN 'Paid Social'
          WHEN REGEXP_CONTAINS(traffic_source.source, r'(?i)facebook|instagram|twitter|linkedin|tiktok')
            OR traffic_source.medium = 'social' THEN 'Organic Social'
          WHEN REGEXP_CONTAINS(traffic_source.medium, r'(?i)email|e-mail') THEN 'Email'
          WHEN traffic_source.medium = 'referral' THEN 'Referral'
          WHEN REGEXP_CONTAINS(traffic_source.medium, r'(?i)display|banner|cpm') THEN 'Display'
          ELSE 'Other'
        END AS channel_group,
        
        -- Conteo de eventos
        COUNT(*) AS total_events,
        COUNT(DISTINCT user_pseudo_id) AS unique_users,
        COUNT(DISTINCT CONCAT(
          user_pseudo_id, '-',
          CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
        )) AS unique_sessions,
        
        -- Analytics Storage
        COUNTIF(
          privacy_info.analytics_storage IS NOT NULL 
          AND LOWER(CAST(privacy_info.analytics_storage AS STRING)) IN ('true', 'yes', '1')
        ) AS analytics_granted,
        COUNTIF(
          privacy_info.analytics_storage IS NOT NULL 
          AND LOWER(CAST(privacy_info.analytics_storage AS STRING)) IN ('false', 'no', '0')
        ) AS analytics_denied,
        
        -- Ads Storage
        COUNTIF(
          privacy_info.ads_storage IS NOT NULL 
          AND LOWER(CAST(privacy_info.ads_storage AS STRING)) IN ('true', 'yes', '1')
        ) AS ads_granted,
        COUNTIF(
          privacy_info.ads_storage IS NOT NULL 
          AND LOWER(CAST(privacy_info.ads_storage AS STRING)) IN ('false', 'no', '0')
        ) AS ads_denied,
        
        -- Consentimiento completo (ambos aceptados)
        COUNTIF(
          LOWER(CAST(privacy_info.analytics_storage AS STRING)) IN ('true', 'yes', '1')
          AND LOWER(CAST(privacy_info.ads_storage AS STRING)) IN ('true', 'yes', '1')
        ) AS full_consent,
        
        -- Sin consentimiento (ambos denegados)
        COUNTIF(
          LOWER(CAST(privacy_info.analytics_storage AS STRING)) IN ('false', 'no', '0')
          AND LOWER(CAST(privacy_info.ads_storage AS STRING)) IN ('false', 'no', '0')
        ) AS no_consent
        
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
      GROUP BY utm_source, utm_medium, utm_campaign, channel_group
    )
    
    SELECT
      channel_group,
      utm_source,
      utm_medium,
      utm_campaign,
      total_events,
      unique_users,
      unique_sessions,
      
      -- Conteos
      analytics_granted,
      analytics_denied,
      ads_granted,
      ads_denied,
      full_consent,
      no_consent,
      
      -- Tasas de consentimiento
      ROUND(SAFE_DIVIDE(analytics_granted, total_events) * 100, 2) AS analytics_consent_rate,
      ROUND(SAFE_DIVIDE(analytics_denied, total_events) * 100, 2) AS analytics_denial_rate,
      ROUND(SAFE_DIVIDE(ads_granted, total_events) * 100, 2) AS ads_consent_rate,
      ROUND(SAFE_DIVIDE(ads_denied, total_events) * 100, 2) AS ads_denial_rate,
      ROUND(SAFE_DIVIDE(full_consent, total_events) * 100, 2) AS full_consent_rate,
      ROUND(SAFE_DIVIDE(no_consent, total_events) * 100, 2) AS no_consent_rate,
      
      -- Ratio de consentimiento (granted vs denied)
      ROUND(SAFE_DIVIDE(analytics_granted, NULLIF(analytics_denied, 0)), 2) AS analytics_consent_ratio,
      ROUND(SAFE_DIVIDE(ads_granted, NULLIF(ads_denied, 0)), 2) AS ads_consent_ratio
      
    FROM traffic_consent
    WHERE total_events >= 10  -- Filtrar fuentes con volumen significativo
    ORDER BY total_events DESC
    LIMIT 500
    """
