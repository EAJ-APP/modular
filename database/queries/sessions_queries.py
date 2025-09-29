def generar_query_session_path_analysis(project, dataset, start_date, end_date):
    """
    Consulta para analizar los caminos de navegación de los usuarios
    Identifica patrones de navegación: página anterior -> página actual -> página siguiente
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Session Path Analysis
    -- Analiza los patrones de navegación de usuarios entre páginas
    
    WITH page_view_data AS (
      -- Extract page view data with previous and next page navigation details
      SELECT
        -- Unique session identifier combining user ID and session ID
        CONCAT(
          user_pseudo_id, '-', 
            (SELECT value.int_value 
             FROM UNNEST(event_params) 
             WHERE key = 'ga_session_id') 
        ) AS session_id,
        user_pseudo_id,
        -- Extract and normalize the page location to get the page path
        REGEXP_REPLACE(
          REGEXP_REPLACE(
            (SELECT value.string_value 
             FROM UNNEST(event_params) 
             WHERE key = 'page_location'),
            r'^https?://[^/]+', '' -- Remove the domain
          ),
          r'[\\?].*', '' -- Remove query parameters
        ) AS page_path,
        event_timestamp
      FROM
        `{project}.{dataset}.events_*`
      WHERE
        event_name = 'page_view'
        AND _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
    ),
    
    page_navigation AS (
      -- Derive navigation patterns using LAG and LEAD functions
      SELECT
        session_id,
        user_pseudo_id,
        -- Previous page
        LAG(page_path) OVER (
          PARTITION BY user_pseudo_id, session_id 
          ORDER BY event_timestamp ASC
        ) AS previous_page,
        -- Current page
        page_path AS current_page,
        -- Next page
        LEAD(page_path) OVER (
          PARTITION BY user_pseudo_id, session_id 
          ORDER BY event_timestamp ASC
        ) AS next_page,
        event_timestamp
      FROM 
        page_view_data
    )
    
    -- Aggregate navigation patterns and calculate session counts
    SELECT 
      IFNULL(previous_page, '(entrance)') AS previous_page,
      current_page,
      IFNULL(next_page, '(exit)') AS next_page,
      COUNT(DISTINCT session_id) AS session_count
    FROM 
      page_navigation
    GROUP BY 
      previous_page,
      current_page,
      next_page
    HAVING 
      current_page NOT IN (previous_page, next_page) -- Filter out loops
    ORDER BY 
      session_count DESC
    LIMIT 500
    """

def generar_query_low_converting_sessions(project, dataset, start_date, end_date):
    """
    Consulta para analizar sesiones con baja conversión
    Identifica patrones en sesiones que NO convirtieron para encontrar oportunidades de mejora
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Low Converting Sessions Analysis
    -- Analiza sesiones sin conversión para identificar patrones y oportunidades de mejora
    
    WITH session_data AS (
      SELECT
        CONCAT(
          user_pseudo_id, 
          '-', 
          (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
        ) AS session_id,
        user_pseudo_id,
        MIN(TIMESTAMP_MICROS(event_timestamp)) AS session_start,
        MAX(TIMESTAMP_MICROS(event_timestamp)) AS session_end,
        COUNT(DISTINCT CASE WHEN event_name = 'page_view' THEN CONCAT(user_pseudo_id, event_timestamp) END) AS page_views,
        COUNT(DISTINCT event_name) AS unique_events,
        
        -- Traffic source (primera ocurrencia en la sesión)
        ARRAY_AGG(traffic_source.source ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS session_source,
        ARRAY_AGG(traffic_source.medium ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS session_medium,
        ARRAY_AGG(traffic_source.name ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS session_campaign,
        
        -- Device info
        ARRAY_AGG(device.category ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS device_category,
        ARRAY_AGG(device.operating_system ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS device_os,
        ARRAY_AGG(device.web_info.browser ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS browser,
        
        -- Geo info
        ARRAY_AGG(geo.country ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS country,
        ARRAY_AGG(geo.city ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS city,
        
        -- Landing page
        ARRAY_AGG(
          (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location')
          ORDER BY event_timestamp LIMIT 1
        )[OFFSET(0)] AS landing_page,
        
        -- Exit page
        ARRAY_AGG(
          (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location')
          ORDER BY event_timestamp DESC LIMIT 1
        )[OFFSET(0)] AS exit_page,
        
        -- Engagement
        SUM(
          (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec')
        ) / 1000 AS engagement_time_seconds,
        
        -- Conversión
        COUNTIF(event_name = 'purchase') AS purchases,
        SUM(CASE WHEN event_name = 'purchase' THEN ecommerce.purchase_revenue ELSE 0 END) AS revenue
        
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
      GROUP BY session_id, user_pseudo_id
    ),
    
    non_converting_sessions AS (
      SELECT *,
        TIMESTAMP_DIFF(session_end, session_start, SECOND) AS session_duration_seconds
      FROM session_data
      WHERE purchases = 0  -- Filtrar solo sesiones SIN compra
        AND page_views > 0  -- Excluir sesiones sin actividad real
    )
    
    SELECT
      -- Dimensiones de tráfico
      session_source,
      session_medium,
      session_campaign,
      
      -- Dimensiones de dispositivo
      device_category,
      device_os,
      browser,
      
      -- Dimensiones geo
      country,
      city,
      
      -- Landing y Exit pages
      landing_page,
      exit_page,
      
      -- Métricas agregadas
      COUNT(DISTINCT session_id) AS total_non_converting_sessions,
      COUNT(DISTINCT user_pseudo_id) AS unique_users,
      
      ROUND(AVG(page_views), 2) AS avg_page_views,
      ROUND(AVG(unique_events), 2) AS avg_unique_events,
      ROUND(AVG(session_duration_seconds), 2) AS avg_session_duration_seconds,
      ROUND(AVG(engagement_time_seconds), 2) AS avg_engagement_time_seconds,
      
      -- Porcentaje de sesiones con engagement bajo (menos de 10 segundos)
      ROUND(
        COUNTIF(engagement_time_seconds < 10) / COUNT(*) * 100, 
        2
      ) AS pct_low_engagement,
      
      -- Porcentaje de sesiones con bounce (solo 1 página vista)
      ROUND(
        COUNTIF(page_views = 1) / COUNT(*) * 100, 
        2
      ) AS pct_bounced_sessions
      
    FROM non_converting_sessions
    GROUP BY 
      session_source, session_medium, session_campaign,
      device_category, device_os, browser,
      country, city,
      landing_page, exit_page
    HAVING total_non_converting_sessions >= 10  -- Filtrar grupos con volumen significativo
    ORDER BY total_non_converting_sessions DESC
    LIMIT 100
    """
