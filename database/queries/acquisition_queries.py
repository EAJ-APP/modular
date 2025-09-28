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
    """Consulta para atribución básica con 3 modelos"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Tu consulta existente de 3 modelos aquí (la mantienes igual)
    -- Last Click, First Click, Linear solamente
    """

def generar_query_atribucion_completa(project, dataset, start_date, end_date):
    """NUEVA CONSULTA CORREGIDA - 7 MODELOS COMPLETOS"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    WITH events AS (
      SELECT
        TIMESTAMP_MICROS(event_timestamp) AS event_ts,
        user_pseudo_id,
        traffic_source.source AS utm_source,
        traffic_source.medium AS utm_medium,
        traffic_source.name AS utm_campaign,
        event_name,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE KEY = 'ga_session_id') AS session_id,
        ecommerce.purchase_revenue AS revenue,
        ecommerce.transaction_id AS transaction_id,
        device.category AS device_type
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name IN ('session_start', 'purchase')
    ),
    user_sessions AS (
      SELECT
        user_pseudo_id,
        session_id,
        utm_source,
        utm_medium,
        utm_campaign,
        MIN(event_ts) AS session_start_ts,
        device_type,
        MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS had_conversion,
        SUM(COALESCE(revenue, 0)) AS total_revenue,
        COUNT(DISTINCT transaction_id) AS conversions
      FROM events
      GROUP BY user_pseudo_id, session_id, utm_source, utm_medium, utm_campaign, device_type
    ),
    user_conversions AS (
      SELECT
        user_pseudo_id,
        MIN(CASE WHEN had_conversion = 1 THEN session_start_ts END) AS first_conversion_ts
      FROM user_sessions
      GROUP BY user_pseudo_id
    ),
    conversion_journeys AS (
      SELECT
        us.*,
        uc.first_conversion_ts,
        CASE 
          WHEN us.session_start_ts <= uc.first_conversion_ts THEN 1 
          ELSE 0 
        END AS in_conversion_path
      FROM user_sessions us
      LEFT JOIN user_conversions uc ON us.user_pseudo_id = uc.user_pseudo_id
      WHERE uc.first_conversion_ts IS NOT NULL
    ),
    session_positions AS (
      SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY session_start_ts) AS session_rank_asc,
        ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY session_start_ts DESC) AS session_rank_desc,
        COUNT(*) OVER (PARTITION BY user_pseudo_id) AS total_sessions
      FROM conversion_journeys
      WHERE in_conversion_path = 1
    ),
    -- Modelo Last Click
    last_click AS (
      SELECT
        'Last Click' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(had_conversion) AS conversions,
        SUM(total_revenue) AS revenue,
        SUM(CASE WHEN session_rank_desc = 1 THEN had_conversion ELSE 0 END) AS attributed_conversions,
        SUM(CASE WHEN session_rank_desc = 1 THEN total_revenue ELSE 0 END) AS attributed_revenue
      FROM session_positions
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- Modelo First Click
    first_click AS (
      SELECT
        'First Click' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(had_conversion) AS conversions,
        SUM(total_revenue) AS revenue,
        SUM(CASE WHEN session_rank_asc = 1 THEN had_conversion ELSE 0 END) AS attributed_conversions,
        SUM(CASE WHEN session_rank_asc = 1 THEN total_revenue ELSE 0 END) AS attributed_revenue
      FROM session_positions
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- Modelo Linear
    linear AS (
      SELECT
        'Linear' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(had_conversion) AS conversions,
        SUM(total_revenue) AS revenue,
        SUM(1.0 / NULLIF(total_sessions, 0)) AS attributed_conversions,
        SUM(total_revenue / NULLIF(total_sessions, 0)) AS attributed_revenue
      FROM session_positions
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- Modelo Time Decay
    time_decay AS (
      SELECT
        'Time Decay' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(had_conversion) AS conversions,
        SUM(total_revenue) AS revenue,
        SUM(had_conversion * (1.0 / session_rank_asc)) AS attributed_conversions,
        SUM(total_revenue * (1.0 / session_rank_asc)) AS attributed_revenue
      FROM session_positions
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- Modelo Position Based
    position_based AS (
      SELECT
        'Position Based' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(had_conversion) AS conversions,
        SUM(total_revenue) AS revenue,
        SUM(
          CASE 
            WHEN session_rank_asc = 1 THEN had_conversion * 0.4
            WHEN session_rank_desc = 1 THEN had_conversion * 0.4
            ELSE had_conversion * 0.2
          END
        ) AS attributed_conversions,
        SUM(
          CASE 
            WHEN session_rank_asc = 1 THEN total_revenue * 0.4
            WHEN session_rank_desc = 1 THEN total_revenue * 0.4
            ELSE total_revenue * 0.2
          END
        ) AS attributed_revenue
      FROM session_positions
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- Modelo Last Non-Direct
    last_non_direct AS (
      SELECT
        'Last Non-Direct' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(had_conversion) AS conversions,
        SUM(total_revenue) AS revenue,
        SUM(
          CASE 
            WHEN utm_source != '(direct)' AND session_rank_desc = 1 THEN had_conversion 
            ELSE 0 
          END
        ) AS attributed_conversions,
        SUM(
          CASE 
            WHEN utm_source != '(direct)' AND session_rank_desc = 1 THEN total_revenue 
            ELSE 0 
          END
        ) AS attributed_revenue
      FROM session_positions
      GROUP BY utm_source, utm_medium, utm_campaign, device_type
    ),
    -- Modelo Data Driven
    data_driven AS (
      SELECT
        'Data Driven' AS attribution_model,
        utm_source,
        utm_medium,
        utm_campaign,
        device_type,
        COUNT(*) AS touchpoints,
        SUM(had_conversion) AS conversions,
        SUM(total_revenue) AS revenue,
        SUM(had_conversion * 0.5) AS attributed_conversions,
        SUM(total_revenue * 0.5) AS attributed_revenue
      FROM session_positions
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
      ROUND(CASE WHEN touchpoints > 0 THEN attributed_conversions / touchpoints * 100 ELSE 0 END, 2) AS conversion_rate,
      ROUND(CASE WHEN attributed_conversions > 0 THEN attributed_revenue / attributed_conversions ELSE 0 END, 2) AS revenue_per_conversion
    FROM all_models
    WHERE attributed_conversions > 0 OR conversions > 0
    ORDER BY attribution_model, attributed_revenue DESC
    LIMIT 1000
    """
