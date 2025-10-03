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
    Consulta para análisis de combos y cross-selling
    Identifica qué productos se compran juntos con más frecuencia
    Market Basket Analysis para optimizar recomendaciones y bundles
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Análisis de Combos y Cross-Selling (Market Basket Analysis)
    
    WITH purchase_transactions AS (
      -- Extraer todas las transacciones con sus items
      SELECT
        ecommerce.transaction_id,
        items.item_id,
        items.item_name,
        items.item_category,
        items.quantity,
        items.item_revenue,
        ecommerce.purchase_revenue AS transaction_revenue,
        COUNT(items.item_id) OVER (PARTITION BY ecommerce.transaction_id) AS items_in_transaction,
        user_pseudo_id,
        device.category AS device_category,
        traffic_source.source AS utm_source,
        traffic_source.medium AS utm_medium
      FROM `{project}.{dataset}.events_*`,
        UNNEST(items) AS items
      WHERE _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name = 'purchase'
        AND ecommerce.transaction_id IS NOT NULL
        AND items.item_name IS NOT NULL
    ),
    
    -- Calcular métricas base por producto
    product_metrics AS (
      SELECT
        item_name,
        COUNT(DISTINCT transaction_id) AS total_transactions,
        SUM(quantity) AS total_quantity,
        SUM(item_revenue) AS total_revenue,
        AVG(item_revenue) AS avg_item_revenue
      FROM purchase_transactions
      GROUP BY item_name
    ),
    
    -- Identificar pares de productos en la misma transacción
    product_pairs AS (
      SELECT
        a.item_name AS product_a,
        b.item_name AS product_b,
        a.transaction_id,
        a.transaction_revenue,
        a.items_in_transaction,
        a.device_category,
        a.utm_source
      FROM purchase_transactions a
      JOIN purchase_transactions b 
        ON a.transaction_id = b.transaction_id
        AND a.item_id < b.item_id  -- Evitar duplicados (A,B) y (B,A)
      WHERE a.item_name != b.item_name
    ),
    
    -- Calcular métricas de asociación
    combo_metrics AS (
      SELECT
        product_a,
        product_b,
        COUNT(DISTINCT transaction_id) AS times_bought_together,
        AVG(transaction_revenue) AS avg_basket_value,
        AVG(items_in_transaction) AS avg_basket_size,
        
        -- Métricas por dispositivo
        COUNTIF(device_category = 'desktop') AS desktop_purchases,
        COUNTIF(device_category = 'mobile') AS mobile_purchases,
        COUNTIF(device_category = 'tablet') AS tablet_purchases,
        
        -- Top fuente de tráfico para este combo
        APPROX_TOP_COUNT(utm_source, 1)[OFFSET(0)].value AS top_traffic_source
        
      FROM product_pairs
      GROUP BY product_a, product_b
    ),
    
    -- Calcular métricas de asociación avanzadas
    combo_analysis AS (
      SELECT
        cm.product_a,
        cm.product_b,
        cm.times_bought_together,
        cm.avg_basket_value,
        cm.avg_basket_size,
        cm.desktop_purchases,
        cm.mobile_purchases,
        cm.tablet_purchases,
        cm.top_traffic_source,
        
        -- Métricas individuales de cada producto
        pm_a.total_transactions AS product_a_transactions,
        pm_b.total_transactions AS product_b_transactions,
        pm_a.total_revenue AS product_a_revenue,
        pm_b.total_revenue AS product_b_revenue,
        
        -- Lift: ¿Comprar A aumenta probabilidad de comprar B?
        -- Lift > 1 significa que hay sinergia positiva
        ROUND(
          SAFE_DIVIDE(
            cm.times_bought_together,
            SAFE_DIVIDE(
              pm_a.total_transactions * pm_b.total_transactions,
              (SELECT COUNT(DISTINCT transaction_id) FROM purchase_transactions)
            )
          ),
          2
        ) AS lift,
        
        -- Confidence: De los que compraron A, ¿qué % también compró B?
        ROUND(
          SAFE_DIVIDE(cm.times_bought_together, pm_a.total_transactions) * 100,
          2
        ) AS confidence_a_to_b,
        
        -- Confidence inversa: De los que compraron B, ¿qué % también compró A?
        ROUND(
          SAFE_DIVIDE(cm.times_bought_together, pm_b.total_transactions) * 100,
          2
        ) AS confidence_b_to_a,
        
        -- Support: ¿Qué % del total de transacciones incluyen ambos productos?
        ROUND(
          SAFE_DIVIDE(
            cm.times_bought_together,
            (SELECT COUNT(DISTINCT transaction_id) FROM purchase_transactions)
          ) * 100,
          2
        ) AS support
        
      FROM combo_metrics cm
      JOIN product_metrics pm_a ON cm.product_a = pm_a.item_name
      JOIN product_metrics pm_b ON cm.product_b = pm_b.item_name
    )
    
    SELECT
      product_a,
      product_b,
      times_bought_together,
      avg_basket_value,
      avg_basket_size,
      
      -- Métricas de asociación (Market Basket)
      lift,
      confidence_a_to_b,
      confidence_b_to_a,
      support,
      
      -- Revenue potencial del combo
      ROUND(product_a_revenue + product_b_revenue, 2) AS combined_revenue,
      
      -- Métricas por dispositivo
      desktop_purchases,
      mobile_purchases,
      tablet_purchases,
      
      -- Fuente de tráfico principal
      top_traffic_source,
      
      -- Transacciones individuales de cada producto
      product_a_transactions,
      product_b_transactions,
      
      -- Strength Score (métrica combinada para ranking)
      -- Combina lift, confidence y frecuencia
      ROUND(
        (lift * 0.4) + 
        (confidence_a_to_b * 0.3) + 
        (LEAST(times_bought_together / 10.0, 10) * 0.3),
        2
      ) AS combo_strength_score
      
    FROM combo_analysis
    WHERE times_bought_together >= 3  -- Filtrar combos con al menos 3 co-ocurrencias
      AND lift >= 1.0  -- Solo combos con lift positivo
    ORDER BY combo_strength_score DESC, times_bought_together DESC
    LIMIT 500
    """
