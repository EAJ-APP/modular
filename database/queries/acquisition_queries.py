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

          -- ✅ TRÁFICO DE IA
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
    """Consulta para atribución de marketing multi-modelo"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Versión simplificada para integración inicial
    WITH base_data AS (
      SELECT
        CONCAT(user_pseudo_id, '-', 
          (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
        ) AS session_id,
        user_pseudo_id,
        traffic_source.source AS utm_source,
        traffic_source.medium AS utm_medium,
        traffic_source.name AS utm_campaign,
        event_name,
        TIMESTAMP_MICROS(event_timestamp) AS event_ts,
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page_path,
        ecommerce.purchase_revenue AS revenue,
        ecommerce.transaction_id AS transaction_id
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name IN ('session_start', 'purchase')
    ),
    sessions_with_conversions AS (
      SELECT
        session_id,
        utm_source,
        utm_medium, 
        utm_campaign,
        MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS had_conversion,
        SUM(COALESCE(revenue, 0)) AS total_revenue,
        COUNT(DISTINCT transaction_id) AS conversions
      FROM base_data
      GROUP BY session_id, utm_source, utm_medium, utm_campaign
    )
    SELECT
      utm_source,
      utm_medium,
      utm_campaign,
      COUNT(*) AS sessions,
      SUM(had_conversion) AS conversions,
      SUM(total_revenue) AS revenue,
      ROUND(SUM(had_conversion) / COUNT(*) * 100, 2) AS conversion_rate
    FROM sessions_with_conversions
    GROUP BY utm_source, utm_medium, utm_campaign
    ORDER BY revenue DESC
    LIMIT 50
    """
