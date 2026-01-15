def generar_query_exit_pages(project, dataset, start_date, end_date):
    """
    Consulta para analizar las páginas de salida más frecuentes
    Identifica dónde los usuarios abandonan el sitio
    """
    from config.settings import Settings

    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Most Frequent Exit Pages Analysis
    -- Identifica las páginas donde los usuarios abandonan más frecuentemente
    
    WITH sessions_pages AS (
      -- Extract page view data for each session
      SELECT
        user_pseudo_id AS cid,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page,
        event_timestamp
      FROM `{project}.{dataset}.events_*`
      WHERE event_name = 'page_view'
        AND _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
    ),
    
    exit_pages AS (
      -- Identify the exit page for each session
      SELECT
        cid,
        session_id,
        FIRST_VALUE(page) OVER (PARTITION BY cid, session_id ORDER BY event_timestamp DESC) AS exit_page
      FROM sessions_pages
    ),
    
    exit_page_stats AS (
      -- Aggregate occurrences of each exit page
      SELECT
        exit_page,
        COUNT(DISTINCT CONCAT(cid, session_id)) AS sessions
      FROM exit_pages
      GROUP BY exit_page
    ),
    
    total_sessions AS (
      SELECT COUNT(DISTINCT CONCAT(cid, session_id)) AS total
      FROM exit_pages
    )
    
    -- Calculate percentage and normalize URLs
    SELECT
      REGEXP_REPLACE(
        REGEXP_REPLACE(exit_page, r'^https?://[^/]+', ''), -- Remove domain
        r'[\\?].*', '' -- Remove query parameters
      ) AS exit_page_path,
      exit_page AS exit_page_full,
      sessions,
      ROUND((sessions / total) * 100, 2) AS exit_percentage
    FROM exit_page_stats, total_sessions
    ORDER BY sessions DESC
    LIMIT {Settings.QUERY_LIMITS['exit_pages']}
    """

def generar_query_hourly_sessions_performance(project, dataset, start_date, end_date):
    """
    Consulta para analizar el rendimiento de sesiones por hora
    Incluye métricas de ecommerce: sesiones, pageviews, view_item, add_to_cart, purchases
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Hourly Sessions Ecommerce Performance
    -- Analiza el rendimiento de sesiones y eventos de ecommerce por hora del día
    
    WITH sessions AS (
      -- Calculate the number of sessions grouped by event date and hour
      SELECT
        event_date,
        FORMAT('%02d', EXTRACT(HOUR FROM TIMESTAMP_MICROS(event_timestamp))) AS hour,
        COUNT(DISTINCT params.value.int_value) AS sessions
      FROM
        `{project}.{dataset}.events_*`,
        UNNEST(event_params) AS params
      WHERE
        event_name = 'session_start'
        AND _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND params.key = 'ga_session_id'
      GROUP BY event_date, hour
    ),
    
    pageviews AS (
      -- Count pageviews grouped by event date and hour
      SELECT
        event_date,
        FORMAT('%02d', EXTRACT(HOUR FROM TIMESTAMP_MICROS(event_timestamp))) AS hour,
        COUNT(event_timestamp) AS pageviews
      FROM
        `{project}.{dataset}.events_*`
      WHERE
        event_name = 'page_view'
        AND _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
      GROUP BY event_date, hour
    ),
    
    view_item_sessions AS (
      -- Count sessions with "view_item" events grouped by event date and hour
      SELECT
        event_date,
        FORMAT('%02d', EXTRACT(HOUR FROM TIMESTAMP_MICROS(event_timestamp))) AS hour,
        COUNT(DISTINCT params.value.int_value) AS view_item_sessions
      FROM
        `{project}.{dataset}.events_*`,
        UNNEST(event_params) AS params,
        UNNEST(items) AS items
      WHERE
        event_name = 'view_item'
        AND _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND params.key = 'ga_session_id'
      GROUP BY event_date, hour
    ),
    
    add_to_carts AS (
      -- Count sessions with "add_to_cart" events grouped by event date and hour
      SELECT
        event_date,
        FORMAT('%02d', EXTRACT(HOUR FROM TIMESTAMP_MICROS(event_timestamp))) AS hour,
        COUNT(DISTINCT params.value.int_value) AS add_to_cart_sessions
      FROM
        `{project}.{dataset}.events_*`,
        UNNEST(event_params) AS params,
        UNNEST(items) AS items
      WHERE
        event_name = 'add_to_cart'
        AND _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND params.key = 'ga_session_id'
      GROUP BY event_date, hour
    ),
    
    orders AS (
      -- Count sessions with "purchase" events grouped by event date and hour
      SELECT
        event_date,
        FORMAT('%02d', EXTRACT(HOUR FROM TIMESTAMP_MICROS(event_timestamp))) AS hour,
        COUNT(DISTINCT params.value.int_value) AS order_sessions
      FROM
        `{project}.{dataset}.events_*`,
        UNNEST(event_params) AS params,
        UNNEST(items) AS items
      WHERE
        event_name = 'purchase'
        AND _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND params.key = 'ga_session_id'
      GROUP BY event_date, hour
    )
    
    -- Aggregate and combine data from all metrics
    SELECT
      PARSE_DATE('%Y%m%d', event_date) AS event_date,
      FORMAT_DATE('%W', PARSE_DATE('%Y%m%d', event_date)) AS iso_week_of_the_year,
      FORMAT_DATE('%w - %A', PARSE_DATE('%Y%m%d', event_date)) AS weekday,
      s.hour,
      s.sessions,
      COALESCE(p.pageviews, 0) AS pageviews,
      COALESCE(vi.view_item_sessions, 0) AS view_item_sessions,
      COALESCE(ac.add_to_cart_sessions, 0) AS add_to_cart_sessions,
      COALESCE(o.order_sessions, 0) AS order_sessions
    FROM
      sessions AS s
    LEFT JOIN pageviews AS p USING (event_date, hour)
    LEFT JOIN view_item_sessions AS vi USING (event_date, hour)
    LEFT JOIN add_to_carts AS ac USING (event_date, hour)
    LEFT JOIN orders AS o USING (event_date, hour)
    ORDER BY
      event_date DESC, s.hour
    """

def generar_query_session_path_analysis(project, dataset, start_date, end_date):
    """
    Consulta para analizar los caminos de navegación de los usuarios
    Identifica patrones de navegación: página anterior -> página actual -> página siguiente
    """
    from config.settings import Settings

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
    LIMIT {Settings.QUERY_LIMITS['session_paths']}
    """

def generar_query_low_converting_sessions(project, dataset, start_date, end_date):
    """
    Consulta para analizar sesiones con baja conversión
    Identifica patrones en sesiones que NO convirtieron para encontrar oportunidades de mejora
    """
    from config.settings import Settings

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
    LIMIT {Settings.QUERY_LIMITS['sessions_low_converting']}
    """
