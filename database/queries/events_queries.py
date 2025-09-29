def generar_query_eventos_flatten(project, dataset, start_date, end_date):
    """Consulta para flattenizar todos los eventos de GA4"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    -- Flattenización completa de eventos GA4
    WITH FlatEvents AS (
        -- Flatten the main event-level data
        SELECT
            (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS ga_session_id,
            * EXCEPT(event_params, user_properties, items)
        FROM
            `{project}.{dataset}.events_*`
        WHERE 
            _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
    ),

    FlatEventParams AS (
        -- Unnest event parameters
        SELECT
            user_pseudo_id,
            event_timestamp,
            event_name,
            event_params.key AS param_key,
            event_params.value.string_value AS param_string_value,
            event_params.value.int_value AS param_int_value,
            event_params.value.float_value AS param_float_value,
            event_params.value.double_value AS param_double_value
        FROM
            `{project}.{dataset}.events_*`,
            UNNEST(event_params) AS event_params
        WHERE 
            _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
    ),

    FlatUserProperties AS (
        -- Unnest user properties
        SELECT
            user_pseudo_id,
            event_timestamp,
            event_name,
            user_properties.key AS user_property_key,
            user_properties.value.string_value AS user_property_string_value,
            user_properties.value.int_value AS user_property_int_value,
            user_properties.value.float_value AS user_property_float_value,
            user_properties.value.double_value AS user_property_double_value,
            user_properties.value.set_timestamp_micros AS user_property_set_timestamp
        FROM
            `{project}.{dataset}.events_*`,
            UNNEST(user_properties) AS user_properties
        WHERE 
            _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
    ),

    FlatItems AS (
        -- Unnest item-level data
        SELECT
            user_pseudo_id,
            event_timestamp,
            event_name,
            items.item_id,
            items.item_name,
            items.item_brand,
            items.item_variant,
            items.item_category,
            items.item_category2,
            items.item_category3,
            items.item_category4,
            items.item_category5,
            items.price_in_usd,
            items.price,
            items.quantity,
            items.item_revenue_in_usd,
            items.item_revenue,
            items.item_refund_in_usd,
            items.item_refund,
            items.coupon,
            items.affiliation,
            items.location_id,
            items.item_list_id,
            items.item_list_name,
            items.item_list_index,
            items.promotion_id,
            items.promotion_name,
            items.creative_name,
            items.creative_slot
        FROM
            `{project}.{dataset}.events_*`,
            UNNEST(items) AS items
        WHERE 
            _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
    )

    SELECT
        -- Combine all flattened data into one table
        fe.*,
        fep.param_key,
        fep.param_string_value,
        fep.param_int_value,
        fep.param_float_value,
        fep.param_double_value,
        fup.user_property_key,
        fup.user_property_string_value,
        fup.user_property_int_value,
        fup.user_property_float_value,
        fup.user_property_double_value,
        fup.user_property_set_timestamp,
        fi.item_id,
        fi.item_name,
        fi.item_brand,
        fi.item_variant,
        fi.item_category,
        fi.item_category2,
        fi.item_category3,
        fi.item_category4,
        fi.item_category5,
        fi.price_in_usd,
        fi.price,
        fi.quantity,
        fi.item_revenue_in_usd,
        fi.item_revenue,
        fi.item_refund_in_usd,
        fi.item_refund,
        fi.coupon,
        fi.affiliation,
        fi.location_id,
        fi.item_list_id,
        fi.item_list_name,
        fi.item_list_index,
        fi.promotion_id,
        fi.promotion_name,
        fi.creative_name,
        fi.creative_slot
    FROM 
        FlatEvents fe
    LEFT JOIN 
        FlatEventParams fep 
        ON fe.user_pseudo_id = fep.user_pseudo_id 
        AND fe.event_timestamp = fep.event_timestamp 
        AND fe.event_name = fep.event_name
    LEFT JOIN 
        FlatUserProperties fup 
        ON fe.user_pseudo_id = fup.user_pseudo_id 
        AND fe.event_timestamp = fup.event_timestamp 
        AND fe.event_name = fup.event_name
    LEFT JOIN 
        FlatItems fi 
        ON fe.user_pseudo_id = fi.user_pseudo_id 
        AND fe.event_timestamp = fi.event_timestamp 
        AND fe.event_name = fi.event_name
    LIMIT 1000
    """

def generar_query_eventos_resumen(project, dataset, start_date, end_date):
    """Consulta para resumen de eventos más comunes"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    SELECT
        event_name,
        COUNT(*) AS total_events,
        COUNT(DISTINCT user_pseudo_id) AS unique_users,
        COUNT(DISTINCT CONCAT(user_pseudo_id, '-', 
            (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id'))) AS unique_sessions
    FROM
        `{project}.{dataset}.events_*`
    WHERE
        _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
    GROUP BY
        event_name
    ORDER BY
        total_events DESC
    LIMIT 50
    """

def generar_query_eventos_por_fecha(project, dataset, start_date, end_date):
    """Consulta para evolución de eventos por fecha"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    SELECT
        event_date,
        event_name,
        COUNT(*) AS total_events,
        COUNT(DISTINCT user_pseudo_id) AS unique_users
    FROM
        `{project}.{dataset}.events_*`
    WHERE
        _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
    GROUP BY
        event_date,
        event_name
    ORDER BY
        event_date DESC,
        total_events DESC
    """

def generar_query_parametros_eventos(project, dataset, start_date, end_date, event_name):
    """Consulta para ver parámetros de un evento específico"""
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    return f"""
    SELECT
        ep.key AS parameter_name,
        COUNT(*) AS parameter_count,
        COUNT(DISTINCT CASE WHEN ep.value.string_value IS NOT NULL THEN ep.value.string_value END) AS unique_string_values,
        COUNT(DISTINCT CASE WHEN ep.value.int_value IS NOT NULL THEN ep.value.int_value END) AS unique_int_values
    FROM
        `{project}.{dataset}.events_*`,
        UNNEST(event_params) AS ep
    WHERE
        _TABLE_SUFFIX BETWEEN '{start_date_str}' AND '{end_date_str}'
        AND event_name = '{event_name}'
    GROUP BY
        parameter_name
    ORDER BY
        parameter_count DESC
    """
