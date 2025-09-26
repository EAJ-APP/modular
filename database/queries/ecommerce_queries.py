def generar_query_comparativa_eventos(project, dataset, start_date, end_date):
    """Consulta para comparativa completa de eventos de ecommerce"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    SELECT
      event_date,
      event_name,
      COUNT(*) AS total_events,
      COUNT(DISTINCT user_pseudo_id) AS unique_users
    FROM `{project}.{dataset}.events_*`
    WHERE event_name IN ('page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase')
      AND _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
    GROUP BY event_date, event_name
    ORDER BY event_date, total_events DESC
    """

def generar_query_ingresos_transacciones(project, dataset, start_date, end_date):
    """Consulta CORREGIDA para ingresos y transacciones"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    SELECT
        event_date AS date,
        COUNT(*) AS total_purchase_events,
        COUNT(DISTINCT ecommerce.transaction_id) AS unique_transactions,
        SUM(ecommerce.purchase_revenue) AS purchase_revenue,
        COUNT(DISTINCT user_pseudo_id) AS unique_buyers
    FROM
        `{project}.{dataset}.events_*`
    WHERE
        _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name = 'purchase'
        AND ecommerce.transaction_id IS NOT NULL
    GROUP BY 
        event_date
    ORDER BY 
        event_date
    """

def generar_query_productos_mas_vendidos(project, dataset, start_date, end_date):
    """Performance de productos por ingresos (CON NOMBRE)"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    WITH PurchaseItems AS (
        SELECT
            items.item_id AS item_id,
            items.item_name AS item_name,
            items.quantity AS item_quantity,
            items.item_revenue AS item_revenue
        FROM
            `{project}.{dataset}.events_*`,
            UNNEST(items) AS items
        WHERE
            event_name = 'purchase'
            AND _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
    )
    SELECT
        item_id,
        item_name,
        SUM(item_quantity) AS total_quantity_sold,
        COUNT(*) AS total_purchases,
        SUM(item_revenue) AS total_revenue
    FROM 
        PurchaseItems
    GROUP BY 
        item_id, item_name
    ORDER BY 
        total_revenue DESC
    """

def generar_query_relacion_productos(project, dataset, start_date, end_date):
    """Relación ID vs Nombre de productos"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    WITH ProductEvents AS (
        SELECT DISTINCT
            items.item_id AS item_id,
            items.item_name AS item_name
        FROM
            `{project}.{dataset}.events_*`,
            UNNEST(items) AS items
        WHERE
            _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
            AND items.item_id IS NOT NULL
            AND items.item_name IS NOT NULL
    )
    SELECT
        item_id,
        item_name,
        COUNT(*) OVER(PARTITION BY item_name) AS nombres_por_producto,
        COUNT(*) OVER(PARTITION BY item_id) AS ids_por_nombre
    FROM 
        ProductEvents
    ORDER BY 
        item_name, item_id
    """

def generar_query_funnel_por_producto(project, dataset, start_date, end_date):
    """Funnel de conversión por producto"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    WITH events_data AS (
      SELECT
        user_pseudo_id,
        event_name,
        TIMESTAMP_MICROS(event_timestamp) AS event_timestamp,
        item.item_name AS item_name 
      FROM 
        `{project}.{dataset}.events_*`,
        UNNEST(items) AS item
      WHERE 
        event_name IN ('view_item', 'add_to_cart', 'begin_checkout', 'purchase')
        AND _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
    ),

    event_stages AS (
      SELECT
        user_pseudo_id,
        event_timestamp,
        item_name,
        CASE event_name
          WHEN 'view_item' THEN 'view_item'
          WHEN 'add_to_cart' THEN 'add_to_cart'
          WHEN 'begin_checkout' THEN 'begin_checkout'
          WHEN 'purchase' THEN 'purchase'
        END AS event_stage
      FROM 
        events_data
    ),

    aggregated_funnel AS (
      SELECT
        vi.item_name,
        COUNT(DISTINCT vi.user_pseudo_id) AS view_item_count,
        COUNT(DISTINCT atc.user_pseudo_id) AS add_to_cart_count,
        COUNT(DISTINCT bc.user_pseudo_id) AS begin_checkout_count,
        COUNT(DISTINCT p.user_pseudo_id) AS purchase_count
      FROM 
        event_stages vi
        LEFT JOIN event_stages atc
          ON vi.user_pseudo_id = atc.user_pseudo_id
          AND vi.item_name = atc.item_name
          AND vi.event_timestamp < atc.event_timestamp
          AND atc.event_stage = 'add_to_cart'
        LEFT JOIN event_stages bc
          ON atc.user_pseudo_id = bc.user_pseudo_id
          AND atc.item_name = bc.item_name
          AND atc.event_timestamp < bc.event_timestamp
          AND bc.event_stage = 'begin_checkout'
        LEFT JOIN event_stages p
          ON bc.user_pseudo_id = p.user_pseudo_id
          AND bc.item_name = p.item_name
          AND bc.event_timestamp < p.event_timestamp
          AND p.event_stage = 'purchase'
      WHERE 
        vi.event_stage = 'view_item'
      GROUP BY 
        vi.item_name
    )

    SELECT
      item_name,
      view_item_count AS view_item,
      add_to_cart_count AS add_to_cart,
      begin_checkout_count AS begin_checkout,
      purchase_count AS purchase,
      ROUND(COALESCE(add_to_cart_count / NULLIF(view_item_count, 0), 0) * 100, 2) AS add_to_cart_rate,
      ROUND(COALESCE(begin_checkout_count / NULLIF(view_item_count, 0), 0) * 100, 2) AS begin_checkout_rate,
      ROUND(COALESCE(purchase_count / NULLIF(view_item_count, 0), 0) * 100, 2) AS purchase_rate
    FROM 
      aggregated_funnel
    WHERE 
      view_item_count > 0
    ORDER BY 
      purchase_count DESC, view_item_count DESC
    """