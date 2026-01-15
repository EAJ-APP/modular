"""
Utilidades para cálculo de costes y billing de BigQuery
"""
import streamlit as st
from typing import Dict, Optional

class BillingCalculator:
    """Calcula costes de consultas BigQuery"""

    # Precio estándar de BigQuery: $5 por TB = $0.005 por GB
    PRICE_PER_GB = 0.005

    @staticmethod
    def get_billing_project(selected_project: Optional[str] = None) -> str:
        """
        Obtiene el proyecto que será facturado por las consultas

        Args:
            selected_project: Proyecto seleccionado actualmente en el sidebar

        Returns:
            str: ID del proyecto o mensaje indicando el tipo
        """
        from auth import SessionManager

        auth_method = SessionManager.get_auth_method()

        # Usar el proyecto seleccionado si está disponible
        if selected_project:
            project_id = selected_project
        else:
            # Fallback al proyecto del cliente
            client = SessionManager.get_bigquery_client()
            if not client:
                return "No disponible"
            project_id = client.project

        # Determinar si es cliente o FLAT 101
        if auth_method == 'oauth':
            return f"{project_id} (Cliente)"
        else:
            return f"{project_id} (FLAT 101)"

    @staticmethod
    def calculate_query_cost(gb_used: float) -> float:
        """
        Calcula el coste de una consulta en USD

        Args:
            gb_used: GB procesados por la consulta

        Returns:
            float: Coste en USD
        """
        return gb_used * BillingCalculator.PRICE_PER_GB

    @staticmethod
    def get_last_query_info() -> Optional[Dict]:
        """
        Obtiene información de la última consulta ejecutada

        Returns:
            Dict con información de la última query o None
        """
        monitoring_data = st.session_state.get('monitoring_data', [])

        if not monitoring_data:
            return None

        # Obtener la última consulta exitosa
        successful_queries = [q for q in monitoring_data if q['status'] == 'Success']

        if not successful_queries:
            return None

        last_query = successful_queries[-1]

        return {
            'gb_used': last_query['gb_used'],
            'cost': BillingCalculator.calculate_query_cost(last_query['gb_used']),
            'query_name': last_query['query_name'],
            'timestamp': last_query['timestamp']
        }

    @staticmethod
    def get_session_total_info() -> Dict:
        """
        Obtiene información total de la sesión

        Returns:
            Dict con GB totales y coste total de la sesión
        """
        monitoring_data = st.session_state.get('monitoring_data', [])

        if not monitoring_data:
            return {
                'total_gb': 0.0,
                'total_cost': 0.0,
                'query_count': 0
            }

        # Sumar solo consultas exitosas
        successful_queries = [q for q in monitoring_data if q['status'] == 'Success']

        total_gb = sum(q['gb_used'] for q in successful_queries)
        total_cost = BillingCalculator.calculate_query_cost(total_gb)

        return {
            'total_gb': total_gb,
            'total_cost': total_cost,
            'query_count': len(successful_queries)
        }
