def generar_query_canales_trafico(project, dataset, start_date, end_date):
    """Consulta para análisis de canales de tráfico"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    WITH traffic_data AS (
      SELECT
        CONCAT(
          user_pseudo_id, '-',
          (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
        ) AS session_id,
        collected_traffic_source.manual_source AS session_source,
        collected_traffic_source.manual_medium AS session_medium,
        collected_traffic_source.manual_campaign_name AS session_campaign_name,
        collected_traffic_source.gclid
      FROM
        `{project}.{dataset}.events_*`
      WHERE
        _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
    ),

    channel_grouping_cte AS (
      SELECT
        session_id,
        CASE
          WHEN session_source IS NULL THEN "Direct"
          WHEN REGEXP_CONTAINS(session_campaign_name, "cross-network") THEN "Cross-network"
          WHEN REGEXP_CONTAINS(session_source, "(openai|copilot|chatgpt|perplexity|deepseek|gemini)")
            OR REGEXP_CONTAINS(session_medium, "(openai|copilot|chatgpt|perplexity|deepseek|gemini)")
            THEN "AI Traffic"
          WHEN (
                REGEXP_CONTAINS(session_source, "alibaba|amazon|google shopping|shopify|etsy|ebay|stripe|walmart")
             OR REGEXP_CONTAINS(session_campaign_name, "^(.*(([^a-df-z]|^)shop|shopping).*)$")
              )
             AND REGEXP_CONTAINS(session_medium, "^(.*cp.*|ppc|paid.*)$")
            THEN "Paid Shopping"
          WHEN gclid IS NOT NULL
             OR (
                REGEXP_CONTAINS(session_source, "baidu|bing|duckduckgo|ecosia|google|yahoo|yandex")
             AND REGEXP_CONTAINS(session_medium, "^(.*cp.*|ppc|paid.*)$")
              )
            THEN "Paid Search"
          WHEN REGEXP_CONTAINS(session_source, "badoo|facebook|fb|instagram|linkedin|pinterest|tiktok|twitter|whatsapp")
             AND REGEXP_CONTAINS(session_medium, "^(.*cp.*|ppc|paid.*)$")
            THEN "Paid Social"
          WHEN REGEXP_CONTAINS(session_source, "dailymotion|disneyplus|netflix|youtube|vimeo|twitch")
             AND REGEXP_CONTAINS(session_medium, "^(.*cp.*|ppc|paid.*)$")
            THEN "Paid Video"
          WHEN session_medium IN ("display", "banner", "expandable", "interstitial", "cpm") THEN "Display"
          WHEN REGEXP_CONTAINS(session_source, "alibaba|amazon|google shopping|shopify|etsy|ebay|stripe|walmart")
             OR REGEXP_CONTAINS(session_campaign_name, "^(.*(([^a-df-z]|^)shop|shopping).*)$")
            THEN "Organic Shopping"
          WHEN REGEXP_CONTAINS(session_source, "badoo|facebook|fb|instagram|linkedin|pinterest|tiktok|twitter|whatsapp")
             OR session_medium IN ("social", "social-network", "social-media", "sm", "social network", "social media")
            THEN "Organic Social"
          WHEN REGEXP_CONTAINS(session_source, "dailymotion|disneyplus|netflix|youtube|vimeo|twitch")
             OR REGEXP_CONTAINS(session_medium, "^(.*video.*)$")
            THEN "Organic Video"
          WHEN REGEXP_CONTAINS(session_source, "baidu|bing|duckduckgo|ecosia|google|yahoo|yandex")
             OR session_medium = "organic"
            THEN "Organic Search"
          WHEN REGEXP_CONTAINS(session_source, "email|e-mail|e_mail|e mail")
             OR REGEXP_CONTAINS(session_medium, "email|e-mail|e_mail|e mail")
            THEN "Email"
          WHEN session_medium = "affiliate" THEN "Affiliates"
          WHEN session_medium = "referral" THEN "Referral"
          WHEN session_medium = "audio" THEN "Audio"
          WHEN session_medium = "sms" THEN "SMS"
          WHEN session_medium LIKE "%push"
             OR REGEXP_CONTAINS(session_medium, "mobile|notification")
            THEN "Mobile Push Notifications"
          ELSE "Unassigned"
        END AS traffic_channel
      FROM
        traffic_data
    ),

    sessions_by_channel AS (
      SELECT
        traffic_channel,
        COUNT(DISTINCT session_id) AS session_count
      FROM
        channel_grouping_cte
      GROUP BY
        traffic_channel
    ),

    total_sessions AS (
      SELECT
        SUM(session_count) AS total_count
      FROM
        sessions_by_channel
    )

    SELECT
      s.traffic_channel,
      s.session_count,
      ROUND( (s.session_count / t.total_count) * 100 , 2 ) AS traffic_percentage
    FROM
      sessions_by_channel s
    CROSS JOIN
      total_sessions t
    ORDER BY
      s.session_count DESC
    """

def generar_query_atribucion_marketing(project, dataset, start_date, end_date):
    """Consulta SIMPLIFICADA para atribución básica (3 modelos)"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Consulta básica de 3 modelos (Last Click, First Click, Linear)
    WITH session_data AS (
      SELECT
        CONCAT(user_pseudo_id, '-', 
          (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
        ) AS session_id,
        user_pseudo_id,
        traffic_source.source AS utm_source,
        traffic_source.medium AS utm_medium,
        traffic_source.name AS utm_campaign,
        TIMESTAMP_MICROS(event_timestamp) AS session_start_ts,
        device.category AS device_type
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name = 'session_start'
    ),
    conversion_data AS (
      SELECT
        CONCAT(user_pseudo_id, '-', 
          (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
        ) AS session_id,
        ecommerce.purchase_revenue AS revenue
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name = 'purchase'
        AND ecommerce.purchase_revenue > 0
    ),
    user_journeys AS (
      SELECT
        s.user_pseudo_id,
        s.session_id,
        s.utm_source,
        s.utm_medium,
        s.utm_campaign,
        s.session_start_ts,
        s.device_type,
        COALESCE(c.revenue, 0) AS revenue,
        CASE WHEN c.revenue > 0 THEN 1 ELSE 0 END AS conversion
      FROM session_data s
      LEFT JOIN conversion_data c ON s.session_id = c.session_id
    ),
    conversion_users AS (
      SELECT DISTINCT user_pseudo_id
      FROM user_journeys
      WHERE conversion = 1
    ),
    -- Modelo Last Click
    last_click AS (
      SELECT
        'Last Click' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        COUNT(*) AS sessions,
        SUM(conversion) AS conversions,
        SUM(revenue) AS revenue,
        SUM(conversion) AS attributed_conversions,
        SUM(revenue) AS attributed_revenue
      FROM (
        SELECT *,
          ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY session_start_ts DESC) as rn
        FROM user_journeys
        WHERE user_pseudo_id IN (SELECT user_pseudo_id FROM conversion_users)
      ) ranked
      WHERE rn = 1
      GROUP BY utm_source, utm_medium, utm_campaign
    ),
    -- Modelo First Click
    first_click AS (
      SELECT
        'First Click' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        COUNT(*) AS sessions,
        SUM(conversion) AS conversions,
        SUM(revenue) AS revenue,
        SUM(conversion) AS attributed_conversions,
        SUM(revenue) AS attributed_revenue
      FROM (
        SELECT *,
          ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY session_start_ts ASC) as rn
        FROM user_journeys
        WHERE user_pseudo_id IN (SELECT user_pseudo_id FROM conversion_users)
      ) ranked
      WHERE rn = 1
      GROUP BY utm_source, utm_medium, utm_campaign
    ),
    -- Modelo Linear
    linear AS (
      SELECT
        'Linear' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        COUNT(*) AS sessions,
        SUM(conversion) AS conversions,
        SUM(revenue) AS revenue,
        SUM(conversion / NULLIF(user_sessions.total_sessions, 0)) AS attributed_conversions,
        SUM(revenue / NULLIF(user_sessions.total_sessions, 0)) AS attributed_revenue
      FROM user_journeys uj
      JOIN (
        SELECT user_pseudo_id, COUNT(*) as total_sessions
        FROM user_journeys
        WHERE user_pseudo_id IN (SELECT user_pseudo_id FROM conversion_users)
        GROUP BY user_pseudo_id
      ) user_sessions ON uj.user_pseudo_id = user_sessions.user_pseudo_id
      WHERE uj.user_pseudo_id IN (SELECT user_pseudo_id FROM conversion_users)
      GROUP BY utm_source, utm_medium, utm_campaign
    ),
    combined_models AS (
      SELECT * FROM last_click
      UNION ALL SELECT * FROM first_click
      UNION ALL SELECT * FROM linear
    )
    SELECT
      attribution_model,
      utm_source,
      utm_medium,
      utm_campaign,
      sessions,
      conversions,
      revenue,
      ROUND(attributed_conversions, 2) AS attributed_conversions,
      ROUND(attributed_revenue, 2) AS attributed_revenue,
      ROUND(CASE WHEN sessions > 0 THEN (attributed_conversions / sessions) * 100 ELSE 0 END, 2) AS attribution_rate
    FROM combined_models
    WHERE attributed_conversions > 0
    ORDER BY attribution_model, attributed_revenue DESC
    LIMIT 100
    """

def generar_query_atribucion_completa(project, dataset, start_date, end_date):
    """Consulta COMPLETAMENTE NUEVA para 7 modelos - VERSIÓN CORREGIDA CON TIME DECAY"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- CONSULTA DE 7 MODELOS - VERSIÓN COMPLETA
    WITH base_data AS (
      SELECT
        user_pseudo_id,
        CONCAT(user_pseudo_id, '-', 
          (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
        ) AS session_id,
        traffic_source.source AS utm_source,
        traffic_source.medium AS utm_medium,
        traffic_source.name AS utm_campaign,
        TIMESTAMP_MICROS(event_timestamp) AS session_start_ts,
        device.category AS device_type,
        ecommerce.purchase_revenue AS revenue,
        CASE WHEN event_name = 'purchase' AND ecommerce.purchase_revenue > 0 THEN 1 ELSE 0 END AS conversion
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name IN ('session_start', 'purchase')
    ),
    user_conversions AS (
      SELECT DISTINCT user_pseudo_id
      FROM base_data
      WHERE conversion = 1
    ),
    conversion_paths AS (
      SELECT *
      FROM base_data
      WHERE user_pseudo_id IN (SELECT user_pseudo_id FROM user_conversions)
    ),
    session_ranking AS (
      SELECT *,
        ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY session_start_ts) as session_asc,
        ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY session_start_ts DESC) as session_desc,
        COUNT(*) OVER (PARTITION BY user_pseudo_id) as total_sessions,
        -- Para Time Decay: calcular el peso basado en la posición
        EXP(-0.5 * (ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY session_start_ts DESC) - 1)) as time_decay_weight
      FROM conversion_paths
    ),
    -- 1. Last Click
    last_click AS (
      SELECT
        'Last Click' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(conversion) AS conversions,
        SUM(revenue) AS revenue,
        SUM(CASE WHEN session_desc = 1 THEN conversion ELSE 0 END) AS attributed_conversions,
        SUM(CASE WHEN session_desc = 1 THEN revenue ELSE 0 END) AS attributed_revenue
      FROM session_ranking
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- 2. First Click
    first_click AS (
      SELECT
        'First Click' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(conversion) AS conversions,
        SUM(revenue) AS revenue,
        SUM(CASE WHEN session_asc = 1 THEN conversion ELSE 0 END) AS attributed_conversions,
        SUM(CASE WHEN session_asc = 1 THEN revenue ELSE 0 END) AS attributed_revenue
      FROM session_ranking
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- 3. Linear
    linear AS (
      SELECT
        'Linear' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(conversion) AS conversions,
        SUM(revenue) AS revenue,
        SUM(conversion / NULLIF(total_sessions, 0)) AS attributed_conversions,
        SUM(revenue / NULLIF(total_sessions, 0)) AS attributed_revenue
      FROM session_ranking
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- 4. Time Decay - CORREGIDO
    time_decay AS (
      SELECT
        'Time Decay' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(conversion) AS conversions,
        SUM(revenue) AS revenue,
        -- Fórmula corregida: normalizar los pesos
        SUM(conversion * (time_decay_weight / user_total_weight.total_weight)) AS attributed_conversions,
        SUM(revenue * (time_decay_weight / user_total_weight.total_weight)) AS attributed_revenue
      FROM session_ranking sr
      JOIN (
        SELECT 
          user_pseudo_id, 
          SUM(time_decay_weight) as total_weight
        FROM session_ranking
        GROUP BY user_pseudo_id
      ) user_total_weight ON sr.user_pseudo_id = user_total_weight.user_pseudo_id
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- 5. Position Based
    position_based AS (
      SELECT
        'Position Based' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(conversion) AS conversions,
        SUM(revenue) AS revenue,
        SUM(
          CASE 
            WHEN session_asc = 1 THEN conversion * 0.4
            WHEN session_desc = 1 THEN conversion * 0.4
            ELSE conversion * 0.2 / NULLIF(GREATEST(total_sessions - 2, 1), 0)
          END
        ) AS attributed_conversions,
        SUM(
          CASE 
            WHEN session_asc = 1 THEN revenue * 0.4
            WHEN session_desc = 1 THEN revenue * 0.4
            ELSE revenue * 0.2 / NULLIF(GREATEST(total_sessions - 2, 1), 0)
          END
        ) AS attributed_revenue
      FROM session_ranking
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- 6. Last Non-Direct
    last_non_direct AS (
      SELECT
        'Last Non-Direct' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(conversion) AS conversions,
        SUM(revenue) AS revenue,
        SUM(CASE WHEN utm_source != '(direct)' AND session_desc = 1 THEN conversion ELSE 0 END) AS attributed_conversions,
        SUM(CASE WHEN utm_source != '(direct)' AND session_desc = 1 THEN revenue ELSE 0 END) AS attributed_revenue
      FROM session_ranking
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- 7. Data Driven (simplificado)
    data_driven AS (
      SELECT
        'Data Driven' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(conversion) AS conversions,
        SUM(revenue) AS revenue,
        SUM(conversion * 0.5) AS attributed_conversions,
        SUM(revenue * 0.5) AS attributed_revenue
      FROM session_ranking
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- COMBINAR LOS 7 MODELOS
    all_models AS (
      SELECT * FROM last_click
      UNION ALL SELECT * FROM first_click
      UNION ALL SELECT * FROM linear
      UNION ALL SELECT * FROM time_decay
      UNION ALL SELECT * FROM position_based
      UNION ALL SELECT * FROM last_non_direct
      UNION ALL SELECT * FROM data_driven
    )
    SELECT
      attribution_model,
      utm_source,
      utm_medium,
      utm_campaign,
      device_type,
      touchpoints,
      conversions,
      revenue,
      ROUND(attributed_conversions, 2) AS attributed_conversions,
      ROUND(attributed_revenue, 2) AS attributed_revenue,
      ROUND(CASE WHEN touchpoints > 0 THEN (attributed_conversions / touchpoints) * 100 ELSE 0 END, 2) AS conversion_rate,
      ROUND(CASE WHEN attributed_conversions > 0 THEN attributed_revenue / attributed_conversions ELSE 0 END, 2) AS revenue_per_conversion
    FROM all_models
    WHERE attributed_conversions > 0 OR conversions > 0
    ORDER BY attribution_model, attributed_revenue DESC
    LIMIT 1000
    """
