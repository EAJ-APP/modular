def generar_query_retencion_semanal(project, dataset, start_date, end_date):
    """
    Weekly User Retention Analysis
    Analiza la retención semanal de usuarios adquiridos en semana 0
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Weekly User Retention Analysis (CORREGIDO - sin división por cero)
    WITH user_first_engagement AS (
      SELECT 
        user_pseudo_id,
        MIN(PARSE_DATE('%Y%m%d', event_date)) AS first_engagement_date,
        DATE_TRUNC(MIN(PARSE_DATE('%Y%m%d', event_date)), WEEK) AS cohort_week
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
      GROUP BY user_pseudo_id
    ),
    
    user_activity AS (
      SELECT 
        user_pseudo_id,
        PARSE_DATE('%Y%m%d', event_date) AS activity_date,
        DATE_TRUNC(PARSE_DATE('%Y%m%d', event_date), WEEK) AS activity_week
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
      GROUP BY user_pseudo_id, activity_date, activity_week
    ),
    
    user_retention AS (
      SELECT 
        ufe.cohort_week,
        ufe.user_pseudo_id,
        ua.activity_week,
        DATE_DIFF(ua.activity_week, ufe.cohort_week, WEEK) AS weeks_since_first_engagement
      FROM user_first_engagement ufe
      JOIN user_activity ua ON ufe.user_pseudo_id = ua.user_pseudo_id
    )
    
    SELECT 
      cohort_week,
      COUNT(DISTINCT user_pseudo_id) AS cohort_size,
      COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 0 THEN user_pseudo_id END) AS week_0_users,
      COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 1 THEN user_pseudo_id END) AS week_1_users,
      COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 2 THEN user_pseudo_id END) AS week_2_users,
      COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 3 THEN user_pseudo_id END) AS week_3_users,
      COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 4 THEN user_pseudo_id END) AS week_4_users,
      -- SAFE_DIVIDE evita errores de división por cero
      ROUND(SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 1 THEN user_pseudo_id END),
        COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 0 THEN user_pseudo_id END)
      ) * 100, 2) AS week_1_retention_pct,
      ROUND(SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 2 THEN user_pseudo_id END),
        COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 0 THEN user_pseudo_id END)
      ) * 100, 2) AS week_2_retention_pct,
      ROUND(SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 3 THEN user_pseudo_id END),
        COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 0 THEN user_pseudo_id END)
      ) * 100, 2) AS week_3_retention_pct,
      ROUND(SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 4 THEN user_pseudo_id END),
        COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 0 THEN user_pseudo_id END)
      ) * 100, 2) AS week_4_retention_pct
    FROM user_retention
    GROUP BY cohort_week
    HAVING week_0_users > 0  -- Filtrar cohortes sin usuarios
    ORDER BY cohort_week DESC
    """

def generar_query_clv_sesiones(project, dataset, start_date, end_date):
    """
    Customer Lifetime Value (CLV) with Sessions
    Calcula el CLV y total de sesiones por usuario
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Customer Lifetime Value with Sessions (CORREGIDO)
    WITH user_sessions AS (
      SELECT 
        user_pseudo_id,
        COUNT(DISTINCT CONCAT(
          CAST(user_pseudo_id AS STRING), 
          '-', 
          CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
        )) AS total_sessions
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND user_pseudo_id IS NOT NULL
      GROUP BY user_pseudo_id
    ),
    
    user_revenue AS (
      SELECT 
        user_pseudo_id,
        SUM(ecommerce.purchase_revenue) AS total_revenue,
        COUNT(DISTINCT ecommerce.transaction_id) AS total_transactions
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name = 'purchase'
        AND ecommerce.purchase_revenue IS NOT NULL
        AND ecommerce.purchase_revenue > 0
        AND user_pseudo_id IS NOT NULL
      GROUP BY user_pseudo_id
    )
    
    SELECT 
      us.user_pseudo_id,
      us.total_sessions,
      COALESCE(ur.total_revenue, 0) AS customer_lifetime_value,
      COALESCE(ur.total_transactions, 0) AS total_transactions,
      ROUND(SAFE_DIVIDE(COALESCE(ur.total_revenue, 0), us.total_sessions), 2) AS revenue_per_session,
      CASE 
        WHEN ur.total_revenue IS NOT NULL AND ur.total_revenue > 0 THEN 'Buyer'
        ELSE 'Non-Buyer'
      END AS user_type
    FROM user_sessions us
    LEFT JOIN user_revenue ur ON us.user_pseudo_id = ur.user_pseudo_id
    WHERE us.total_sessions > 0
    ORDER BY customer_lifetime_value DESC
    LIMIT 5000
    """

def generar_query_tiempo_primera_compra(project, dataset, start_date, end_date):
    """
    Time from First Visit to Purchase by Source
    Analiza el tiempo entre primera visita y compra por fuente de tráfico
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Time from First Visit to Purchase by Source
    WITH first_visit AS (
      SELECT 
        user_pseudo_id,
        MIN(TIMESTAMP_MICROS(event_timestamp)) AS first_visit_time,
        ARRAY_AGG(
          traffic_source.source 
          ORDER BY event_timestamp 
          LIMIT 1
        )[OFFSET(0)] AS first_source,
        ARRAY_AGG(
          traffic_source.medium 
          ORDER BY event_timestamp 
          LIMIT 1
        )[OFFSET(0)] AS first_medium
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
      GROUP BY user_pseudo_id
    ),
    
    first_purchase AS (
      SELECT 
        user_pseudo_id,
        MIN(TIMESTAMP_MICROS(event_timestamp)) AS first_purchase_time
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name = 'purchase'
      GROUP BY user_pseudo_id
    ),
    
    time_to_purchase AS (
      SELECT 
        fv.user_pseudo_id,
        fv.first_source,
        fv.first_medium,
        fv.first_visit_time,
        fp.first_purchase_time,
        DATE_DIFF(DATE(fp.first_purchase_time), DATE(fv.first_visit_time), DAY) AS days_to_purchase
      FROM first_visit fv
      INNER JOIN first_purchase fp ON fv.user_pseudo_id = fp.user_pseudo_id
      WHERE fp.first_purchase_time > fv.first_visit_time
    )
    
    SELECT 
      first_source,
      first_medium,
      COUNT(DISTINCT user_pseudo_id) AS users_with_purchase,
      ROUND(AVG(days_to_purchase), 2) AS avg_days_to_purchase,
      MIN(days_to_purchase) AS min_days_to_purchase,
      MAX(days_to_purchase) AS max_days_to_purchase,
      APPROX_QUANTILES(days_to_purchase, 100)[OFFSET(50)] AS median_days_to_purchase
    FROM time_to_purchase
    GROUP BY first_source, first_medium
    HAVING users_with_purchase >= 5
    ORDER BY users_with_purchase DESC
    LIMIT 100
    """

def generar_query_landing_page_attribution(project, dataset, start_date, end_date):
    """
    First Landing Page Attribution
    Atribuye métricas clave (views, add-to-cart, purchases) a la primera landing page
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- First Landing Page Attribution
    WITH user_first_landing AS (
      SELECT 
        user_pseudo_id,
        ARRAY_AGG(
          (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location')
          ORDER BY event_timestamp 
          LIMIT 1
        )[OFFSET(0)] AS first_landing_page
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name = 'page_view'
      GROUP BY user_pseudo_id
    ),
    
    user_events AS (
      SELECT 
        user_pseudo_id,
        COUNTIF(event_name = 'page_view') AS total_page_views,
        COUNTIF(event_name = 'view_item') AS total_view_items,
        COUNTIF(event_name = 'add_to_cart') AS total_add_to_cart,
        COUNTIF(event_name = 'begin_checkout') AS total_begin_checkout,
        COUNTIF(event_name = 'purchase') AS total_purchases,
        SUM(CASE WHEN event_name = 'purchase' THEN ecommerce.purchase_revenue ELSE 0 END) AS total_revenue
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
      GROUP BY user_pseudo_id
    )
    
    SELECT 
      ufl.first_landing_page,
      COUNT(DISTINCT ufl.user_pseudo_id) AS unique_users,
      SUM(ue.total_page_views) AS total_page_views,
      SUM(ue.total_view_items) AS total_view_items,
      SUM(ue.total_add_to_cart) AS total_add_to_cart,
      SUM(ue.total_begin_checkout) AS total_begin_checkout,
      SUM(ue.total_purchases) AS total_purchases,
      SUM(ue.total_revenue) AS total_revenue,
      ROUND(SAFE_DIVIDE(SUM(ue.total_purchases), COUNT(DISTINCT ufl.user_pseudo_id)) * 100, 2) AS conversion_rate,
      ROUND(SAFE_DIVIDE(SUM(ue.total_revenue), COUNT(DISTINCT ufl.user_pseudo_id)), 2) AS revenue_per_user
    FROM user_first_landing ufl
    LEFT JOIN user_events ue ON ufl.user_pseudo_id = ue.user_pseudo_id
    WHERE ufl.first_landing_page IS NOT NULL
    GROUP BY ufl.first_landing_page
    HAVING unique_users >= 10
    ORDER BY total_revenue DESC
    LIMIT 100
    """

def generar_query_adquisicion_usuarios(project, dataset, start_date, end_date):
    """
    User Acquisition by Source/Medium with Channel Grouping
    Agrupa usuarios por fuente, medio y categorías predefinidas
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- User Acquisition by Source/Medium with Channel Grouping
    WITH user_first_source AS (
      SELECT 
        user_pseudo_id,
        ARRAY_AGG(traffic_source.source ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS first_source,
        ARRAY_AGG(traffic_source.medium ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS first_medium,
        MIN(PARSE_DATE('%Y%m%d', event_date)) AS acquisition_date
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
      GROUP BY user_pseudo_id
    ),
    
    channel_grouping AS (
      SELECT 
        user_pseudo_id,
        first_source,
        first_medium,
        acquisition_date,
        CASE
          WHEN first_source IS NULL THEN 'Direct'
          WHEN REGEXP_CONTAINS(first_source, r'(?i)google|bing|yahoo|duckduckgo|ecosia|yandex|baidu')
            AND first_medium = 'organic' THEN 'Organic Search'
          WHEN REGEXP_CONTAINS(first_medium, r'(?i)cpc|ppc|paid') THEN 'Paid Search'
          WHEN REGEXP_CONTAINS(first_source, r'(?i)facebook|instagram|twitter|linkedin|pinterest|tiktok')
            AND REGEXP_CONTAINS(first_medium, r'(?i)social|cpc|ppc|paid') THEN 'Paid Social'
          WHEN REGEXP_CONTAINS(first_source, r'(?i)facebook|instagram|twitter|linkedin|pinterest|tiktok')
            OR first_medium = 'social' THEN 'Organic Social'
          WHEN REGEXP_CONTAINS(first_medium, r'(?i)email|e-mail') THEN 'Email'
          WHEN first_medium = 'referral' THEN 'Referral'
          WHEN REGEXP_CONTAINS(first_medium, r'(?i)display|banner|cpm') THEN 'Display'
          WHEN REGEXP_CONTAINS(first_source, r'(?i)youtube|vimeo') THEN 'Video'
          ELSE 'Other'
        END AS channel_group
      FROM user_first_source
    ),
    
    user_metrics AS (
      SELECT 
        user_pseudo_id,
        COUNT(DISTINCT CONCAT(
          CAST(user_pseudo_id AS STRING), 
          '-', 
          CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
        )) AS total_sessions,
        COUNTIF(event_name = 'purchase') AS total_purchases,
        SUM(CASE WHEN event_name = 'purchase' THEN ecommerce.purchase_revenue ELSE 0 END) AS total_revenue
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
      GROUP BY user_pseudo_id
    )
    
    SELECT 
      cg.channel_group,
      cg.first_source,
      cg.first_medium,
      COUNT(DISTINCT cg.user_pseudo_id) AS total_users,
      SUM(um.total_sessions) AS total_sessions,
      SUM(um.total_purchases) AS total_purchases,
      SUM(um.total_revenue) AS total_revenue,
      ROUND(SAFE_DIVIDE(SUM(um.total_sessions), COUNT(DISTINCT cg.user_pseudo_id)), 2) AS avg_sessions_per_user,
      ROUND(SAFE_DIVIDE(SUM(um.total_purchases), COUNT(DISTINCT cg.user_pseudo_id)) * 100, 2) AS conversion_rate,
      ROUND(SAFE_DIVIDE(SUM(um.total_revenue), COUNT(DISTINCT cg.user_pseudo_id)), 2) AS revenue_per_user
    FROM channel_grouping cg
    LEFT JOIN user_metrics um ON cg.user_pseudo_id = um.user_pseudo_id
    GROUP BY cg.channel_group, cg.first_source, cg.first_medium
    HAVING total_users >= 5
    ORDER BY total_users DESC
    LIMIT 100
    """

def generar_query_conversion_mensual(project, dataset, start_date, end_date):
    """
    Monthly User Conversion Rate
    Calcula la tasa de conversión mensual (usuarios convertidos / usuarios totales)
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Monthly User Conversion Rate
    WITH monthly_users AS (
      SELECT 
        FORMAT_DATE('%Y-%m', PARSE_DATE('%Y%m%d', event_date)) AS month,
        user_pseudo_id
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND user_pseudo_id IS NOT NULL
      GROUP BY month, user_pseudo_id
    ),
    
    monthly_converters AS (
      SELECT 
        FORMAT_DATE('%Y-%m', PARSE_DATE('%Y%m%d', event_date)) AS month,
        user_pseudo_id,
        SUM(ecommerce.purchase_revenue) AS user_revenue,
        COUNT(DISTINCT ecommerce.transaction_id) AS user_transactions
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name = 'purchase'
        AND ecommerce.purchase_revenue IS NOT NULL
        AND ecommerce.purchase_revenue > 0
        AND user_pseudo_id IS NOT NULL
      GROUP BY month, user_pseudo_id
    )
    
    SELECT 
      mu.month,
      COUNT(DISTINCT mu.user_pseudo_id) AS total_users,
      COUNT(DISTINCT mc.user_pseudo_id) AS converted_users,
      ROUND(SAFE_DIVIDE(COUNT(DISTINCT mc.user_pseudo_id), COUNT(DISTINCT mu.user_pseudo_id)) * 100, 2) AS conversion_rate,
      SUM(mc.user_revenue) AS total_revenue,
      SUM(mc.user_transactions) AS total_transactions,
      ROUND(SAFE_DIVIDE(SUM(mc.user_revenue), COUNT(DISTINCT mc.user_pseudo_id)), 2) AS avg_revenue_per_converter,
      ROUND(SAFE_DIVIDE(SUM(mc.user_revenue), COUNT(DISTINCT mu.user_pseudo_id)), 2) AS avg_revenue_per_user
    FROM monthly_users mu
    LEFT JOIN monthly_converters mc ON mu.month = mc.month AND mu.user_pseudo_id = mc.user_pseudo_id
    GROUP BY mu.month
    ORDER BY mu.month DESC
    """
