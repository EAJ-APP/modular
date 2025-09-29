def generar_query_retencion_semanal(project, dataset, start_date, end_date):
    """
    Weekly User Retention Analysis
    Analiza la retención semanal de usuarios adquiridos en semana 0
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Weekly User Retention Analysis
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
      ROUND(COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 1 THEN user_pseudo_id END) / 
            COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 0 THEN user_pseudo_id END) * 100, 2) AS week_1_retention_pct,
      ROUND(COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 2 THEN user_pseudo_id END) / 
            COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 0 THEN user_pseudo_id END) * 100, 2) AS week_2_retention_pct,
      ROUND(COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 3 THEN user_pseudo_id END) / 
            COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 0 THEN user_pseudo_id END) * 100, 2) AS week_3_retention_pct,
      ROUND(COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 4 THEN user_pseudo_id END) / 
            COUNT(DISTINCT CASE WHEN weeks_since_first_engagement = 0 THEN user_pseudo_id END) * 100, 2) AS week_4_retention_pct
    FROM user_retention
    GROUP BY cohort_week
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
    -- Customer Lifetime Value with Sessions
    WITH user_sessions AS (
      SELECT 
        user_pseudo_id,
        COUNT(DISTINCT CONCAT(user_pseudo_id, '-', 
          (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id'))) AS total_sessions
      FROM `{project}.{dataset}.events_*`
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
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
      GROUP BY user_pseudo_id
    )
    
    SELECT 
      us.user_pseudo_id,
      us.total_sessions,
      COALESCE(ur.total_revenue, 0) AS customer_lifetime_value,
      COALESCE(ur.total_transactions, 0) AS total_transactions,
      ROUND(COALESCE(ur.total_revenue, 0) / us.total_sessions, 2) AS revenue_per_session,
      CASE 
        WHEN ur.total_revenue IS NOT NULL THEN 'Buyer'
        ELSE 'Non-Buyer'
      END AS user_type
    FROM user_sessions us
    LEFT JOIN user_revenue ur ON us.user_pseudo_id = ur.user_pseudo_id
    ORDER BY customer_lifetime_value DESC
    LIMIT 1000
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
