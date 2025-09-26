from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st
from utils.error_handling import handle_bq_error

def get_bq_client(credentials_path=None):
    """Crea cliente de BigQuery con manejo de errores simple"""
    try:
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
        else:
            creds_dict = dict(st.secrets["gcp_service_account"])
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
        return bigquery.Client(credentials=credentials, project=creds_dict.get("project_id"))
    except Exception as e:
        handle_bq_error(e)

def run_query(client, query, timeout=30):
    """Ejecuta consulta en BigQuery - Versión actualizada"""
    from concurrent.futures import TimeoutError
    
    try:
        query_job = client.query(query)
        # Usar to_dataframe() sin create_bqstorage_client para compatibilidad
        return query_job.result(timeout=timeout).to_dataframe()
    except TimeoutError:
        handle_bq_error("⏳ Timeout: La consulta tardó demasiado. Filtra más datos.", query)
    except Exception as e:
        handle_bq_error(e, query)
