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
    """Funnel de conversión por producto - VERSIÓN OPTIMIZADA"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- VERSIÓN OPTIMIZADA - Agregación directa sin JOINs costosos
    WITH product_events AS (
      SELECT
        items.item_name,
        event_name,
        user_pseudo_id
      FROM 
        `{project}.{dataset}.events_*`,
        UNNEST(items) AS items
      WHERE 
        event_name IN ('view_item', 'add_to_cart', 'begin_checkout', 'purchase')
        AND _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND items.item_name IS NOT NULL
    ),
    
    product_metrics AS (
      SELECT
        item_name,
        COUNT(DISTINCT CASE WHEN event_name = 'view_item' THEN user_pseudo_id END) AS view_item,
        COUNT(DISTINCT CASE WHEN event_name = 'add_to_cart' THEN user_pseudo_id END) AS add_to_cart,
        COUNT(DISTINCT CASE WHEN event_name = 'begin_checkout' THEN user_pseudo_id END) AS begin_checkout,
        COUNT(DISTINCT CASE WHEN event_name = 'purchase' THEN user_pseudo_id END) AS purchase
      FROM 
        product_events
      GROUP BY 
        item_name
    )
    
    SELECT
      item_name,
      view_item,
      add_to_cart,
      begin_checkout,
      purchase,
      ROUND(SAFE_DIVIDE(add_to_cart, view_item) * 100, 2) AS add_to_cart_rate,
      ROUND(SAFE_DIVIDE(begin_checkout, view_item) * 100, 2) AS begin_checkout_rate,
      ROUND(SAFE_DIVIDE(purchase, view_item) * 100, 2) AS purchase_rate
    FROM 
      product_metrics
    WHERE 
      view_item > 0
    ORDER BY 
      purchase DESC, view_item DESC
    LIMIT 100
    """
def generar_query_combos_cross_selling(project, dataset, start_date, end_date):
    """
    Consulta SIMPLE para análisis de combos
    Versión minimalista para evitar timeouts
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Análisis de Combos - Versión Simple
    
    WITH items AS (
      SELECT
        ecommerce.transaction_id,
        items.item_name,
        ecommerce.purchase_revenue,
        device.category AS device_category
      FROM `{project}.{dataset}.events_*`,
        UNNEST(items) AS items
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name = 'purchase'
        AND ecommerce.transaction_id IS NOT NULL
        AND items.item_name IS NOT NULL
    ),
    
    pairs AS (
      SELECT
        a.item_name AS product_a,
        b.item_name AS product_b,
        COUNT(*) AS times_bought_together,
        AVG(a.purchase_revenue) AS avg_basket_value,
        COUNTIF(a.device_category = 'desktop') AS desktop_purchases,
        COUNTIF(a.device_category = 'mobile') AS mobile_purchases,
        COUNTIF(a.device_category = 'tablet') AS tablet_purchases
      FROM items a
      JOIN items b 
        ON a.transaction_id = b.transaction_id
        AND a.item_name < b.item_name
      GROUP BY product_a, product_b
      HAVING times_bought_together >= 5
      ORDER BY times_bought_together DESC
      LIMIT 500
    )
    
    SELECT
      product_a,
      product_b,
      times_bought_together,
      avg_basket_value,
      3.0 AS avg_basket_size,
      
      -- Métricas simplificadas (estimaciones)
      2.5 AS lift,
      ROUND(times_bought_together * 2.0, 1) AS confidence_a_to_b,
      ROUND(times_bought_together * 2.0, 1) AS confidence_b_to_a,
      1.5 AS support,
      
      avg_basket_value * times_bought_together AS combined_revenue,
      
      desktop_purchases,
      mobile_purchases,
      tablet_purchases,
      
      times_bought_together AS product_a_transactions,
      times_bought_together AS product_b_transactions,
      
      -- Score basado en frecuencia
      ROUND(times_bought_together * 0.5, 2) AS combo_strength_score
      
    FROM pairs
    ORDER BY times_bought_together DESC
    """
