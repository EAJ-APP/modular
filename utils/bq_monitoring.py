"""
Utilidades para monitorizar el consumo de BigQuery
"""
from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd

def bytes_to_readable(bytes_value):
    """Convierte bytes a formato legible (KB, MB, GB, TB)"""
    if bytes_value is None:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def estimate_query_cost(client, query):
    """
    Estima el costo de una consulta SIN ejecutarla
    
    Args:
        client: Cliente de BigQuery
        query: Consulta SQL a estimar
        
    Returns:
        dict con información de bytes procesados y costo estimado
    """
    try:
        # Configurar job para dry run (no ejecuta realmente)
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        
        # Estimar la consulta
        query_job = client.query(query, job_config=job_config)
        
        # Obtener bytes que se procesarían
        total_bytes = query_job.total_bytes_processed
        total_gb = total_bytes / (1024 ** 3)
        
        # Calcular costo estimado (BigQuery cobra $5 por TB en on-demand)
        # $5 por TB = $0.005 por GB
        estimated_cost_usd = total_gb * 0.005
        
        return {
            'total_bytes': total_bytes,
            'total_bytes_readable': bytes_to_readable(total_bytes),
            'total_gb': round(total_gb, 4),
            'estimated_cost_usd': round(estimated_cost_usd, 6),
            'estimated_cost_eur': round(estimated_cost_usd * 0.92, 6),  # Aproximado
            'success': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_project_usage_last_days(client, project_id, days=7):
    """
    Obtiene el uso de BigQuery del proyecto en los últimos N días
    
    Args:
        client: Cliente de BigQuery
        project_id: ID del proyecto
        days: Número de días a consultar (default: 7)
        
    Returns:
        DataFrame con uso diario
    """
    try:
        # Calcular fecha de inicio
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query para obtener estadísticas de uso desde INFORMATION_SCHEMA
        query = f"""
        SELECT
            DATE(creation_time) as date,
            user_email,
            COUNT(*) as total_queries,
            SUM(total_bytes_processed) as total_bytes_processed,
            SUM(total_bytes_billed) as total_bytes_billed,
            SUM(total_slot_ms) as total_slot_ms,
            AVG(total_bytes_processed) as avg_bytes_per_query
        FROM
            `{project_id}.region-europe-southwest1.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
        WHERE
            creation_time >= TIMESTAMP('{start_date.strftime('%Y-%m-%d')}')
            AND creation_time < TIMESTAMP('{end_date.strftime('%Y-%m-%d')}')
            AND job_type = 'QUERY'
            AND state = 'DONE'
            AND error_result IS NULL
        GROUP BY
            date, user_email
        ORDER BY
            date DESC, total_bytes_processed DESC
        """
        
        # Ejecutar consulta
        df = client.query(query).to_dataframe()
        
        # Agregar columnas legibles
        df['total_bytes_readable'] = df['total_bytes_processed'].apply(bytes_to_readable)
        df['total_billed_readable'] = df['total_bytes_billed'].apply(bytes_to_readable)
        df['avg_bytes_readable'] = df['avg_bytes_per_query'].apply(bytes_to_readable)
        df['total_gb_processed'] = df['total_bytes_processed'] / (1024 ** 3)
        df['estimated_cost_usd'] = df['total_gb_processed'] * 0.005
        
        return df
        
    except Exception as e:
        # Si falla (por ejemplo, por región), intentar con región US
        try:
            query_us = query.replace('region-europe-southwest1', 'region-us')
            df = client.query(query_us).to_dataframe()
            
            # Agregar columnas legibles
            df['total_bytes_readable'] = df['total_bytes_processed'].apply(bytes_to_readable)
            df['total_billed_readable'] = df['total_bytes_billed'].apply(bytes_to_readable)
            df['avg_bytes_readable'] = df['avg_bytes_per_query'].apply(bytes_to_readable)
            df['total_gb_processed'] = df['total_bytes_processed'] / (1024 ** 3)
            df['estimated_cost_usd'] = df['total_gb_processed'] * 0.005
            
            return df
        except:
            # Si también falla, intentar sin región específica
            query_generic = f"""
            SELECT
                DATE(creation_time) as date,
                COUNT(*) as total_queries,
                SUM(total_bytes_processed) as total_bytes_processed,
                SUM(total_bytes_billed) as total_bytes_billed
            FROM
                `{project_id}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
            WHERE
                creation_time >= TIMESTAMP('{start_date.strftime('%Y-%m-%d')}')
                AND creation_time < TIMESTAMP('{end_date.strftime('%Y-%m-%d')}')
                AND job_type = 'QUERY'
                AND state = 'DONE'
            GROUP BY
                date
            ORDER BY
                date DESC
            """
            
            df = client.query(query_generic).to_dataframe()
            
            # Agregar columnas legibles
            df['total_bytes_readable'] = df['total_bytes_processed'].apply(bytes_to_readable)
            df['total_billed_readable'] = df['total_bytes_billed'].apply(bytes_to_readable)
            df['total_gb_processed'] = df['total_bytes_processed'] / (1024 ** 3)
            df['estimated_cost_usd'] = df['total_gb_processed'] * 0.005
            
            return df

def get_current_month_usage(client, project_id):
    """
    Obtiene el uso total del mes actual
    
    Args:
        client: Cliente de BigQuery
        project_id: ID del proyecto
        
    Returns:
        dict con estadísticas del mes
    """
    try:
        # Primer día del mes actual
        today = datetime.now()
        first_day = datetime(today.year, today.month, 1)
        
        query = f"""
        SELECT
            COUNT(*) as total_queries,
            SUM(total_bytes_processed) as total_bytes_processed,
            SUM(total_bytes_billed) as total_bytes_billed,
            AVG(total_bytes_processed) as avg_bytes_per_query
        FROM
            `{project_id}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
        WHERE
            creation_time >= TIMESTAMP('{first_day.strftime('%Y-%m-%d')}')
            AND job_type = 'QUERY'
            AND state = 'DONE'
            AND error_result IS NULL
        """
        
        result = client.query(query).to_dataframe()
        
        if not result.empty:
            total_bytes = result['total_bytes_processed'].iloc[0]
            total_billed = result['total_bytes_billed'].iloc[0]
            total_gb = total_bytes / (1024 ** 3) if total_bytes else 0
            
            return {
                'total_queries': int(result['total_queries'].iloc[0]),
                'total_bytes': total_bytes,
                'total_bytes_readable': bytes_to_readable(total_bytes),
                'total_billed_readable': bytes_to_readable(total_billed),
                'total_gb': round(total_gb, 2),
                'estimated_cost_usd': round(total_gb * 0.005, 2),
                'estimated_cost_eur': round(total_gb * 0.005 * 0.92, 2),
                'avg_bytes_per_query': bytes_to_readable(result['avg_bytes_per_query'].iloc[0]),
                'success': True
            }
        else:
            return {'success': False, 'error': 'No hay datos disponibles'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_query_statistics(query_job):
    """
    Obtiene estadísticas de una consulta ya ejecutada
    
    Args:
        query_job: Job de BigQuery ejecutado
        
    Returns:
        dict con estadísticas de la consulta
    """
    try:
        stats = {
            'total_bytes_processed': query_job.total_bytes_processed,
            'total_bytes_readable': bytes_to_readable(query_job.total_bytes_processed),
            'total_bytes_billed': query_job.total_bytes_billed,
            'total_billed_readable': bytes_to_readable(query_job.total_bytes_billed),
            'cache_hit': query_job.cache_hit,
            'slot_millis': query_job.slot_millis,
            'total_gb_processed': round(query_job.total_bytes_processed / (1024 ** 3), 4),
            'estimated_cost_usd': round((query_job.total_bytes_processed / (1024 ** 3)) * 0.005, 6),
            'num_dml_affected_rows': query_job.num_dml_affected_rows,
            'success': True
        }
        
        return stats
    except Exception as e:
        return {'success': False, 'error': str(e)}

def check_free_tier_limit(total_gb_month):
    """
    Verifica si se está dentro del tier gratuito de BigQuery
    
    BigQuery ofrece 1 TB (1024 GB) gratis al mes
    
    Args:
        total_gb_month: GB procesados en el mes
        
    Returns:
        dict con información del free tier
    """
    FREE_TIER_GB = 1024  # 1 TB gratis al mes
    
    remaining_gb = FREE_TIER_GB - total_gb_month
    percentage_used = (total_gb_month / FREE_TIER_GB) * 100
    
    return {
        'free_tier_gb': FREE_TIER_GB,
        'used_gb': round(total_gb_month, 2),
        'remaining_gb': round(remaining_gb, 2),
        'percentage_used': round(percentage_used, 2),
        'within_free_tier': remaining_gb > 0,
        'status': 'success' if remaining_gb > 0 else 'warning'
    }
