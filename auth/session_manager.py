import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from typing import Optional, Tuple
import json

class SessionManager:
    """Gestiona las sesiones de autenticación"""
    
    # Keys para session_state
    AUTH_METHOD_KEY = 'auth_method'
    CREDENTIALS_KEY = 'credentials'
    BQ_CLIENT_KEY = 'bq_client'
    USER_INFO_KEY = 'user_info'
    IS_AUTHENTICATED_KEY = 'is_authenticated'
    SELECTED_PROJECT_KEY = 'selected_project'
    
    @staticmethod
    def initialize_session():
        """Inicializa el estado de la sesión"""
        if SessionManager.IS_AUTHENTICATED_KEY not in st.session_state:
            st.session_state[SessionManager.IS_AUTHENTICATED_KEY] = False
        
        if SessionManager.AUTH_METHOD_KEY not in st.session_state:
            st.session_state[SessionManager.AUTH_METHOD_KEY] = None
        
        if SessionManager.USER_INFO_KEY not in st.session_state:
            st.session_state[SessionManager.USER_INFO_KEY] = {}
    
    @staticmethod
    def is_authenticated() -> bool:
        """Verifica si el usuario está autenticado"""
        return st.session_state.get(SessionManager.IS_AUTHENTICATED_KEY, False)
    
    @staticmethod
    def get_auth_method() -> Optional[str]:
        """Obtiene el método de autenticación usado"""
        return st.session_state.get(SessionManager.AUTH_METHOD_KEY)
    
    @staticmethod
    def set_oauth_session(credentials: Credentials, user_info: dict):
        """Configura sesión para OAuth"""
        from auth.oauth_handler import OAuthHandler
        
        st.session_state[SessionManager.AUTH_METHOD_KEY] = 'oauth'
        st.session_state[SessionManager.CREDENTIALS_KEY] = OAuthHandler.credentials_to_dict(credentials)
        st.session_state[SessionManager.USER_INFO_KEY] = user_info
        
        # Crear cliente de BigQuery con el primer proyecto disponible
        # o con un proyecto por defecto
        try:
            # Intentar obtener el primer proyecto disponible
            temp_client = bigquery.Client(credentials=credentials, project='dummy-project')
            projects = list(temp_client.list_projects(max_results=1))
            
            if projects:
                project = projects[0].project_id
                st.session_state[SessionManager.SELECTED_PROJECT_KEY] = project
                st.session_state[SessionManager.BQ_CLIENT_KEY] = bigquery.Client(
                    credentials=credentials, 
                    project=project
                )
            else:
                # Si no hay proyectos accesibles, marcar como autenticado pero sin cliente
                st.session_state[SessionManager.BQ_CLIENT_KEY] = None
                
        except Exception as e:
            # Si falla, intentar con el proyecto por defecto de secrets
            try:
                default_project = st.secrets.get("gcp_service_account", {}).get("project_id", "ai-nibw")
                st.session_state[SessionManager.SELECTED_PROJECT_KEY] = default_project
                st.session_state[SessionManager.BQ_CLIENT_KEY] = bigquery.Client(
                    credentials=credentials, 
                    project=default_project
                )
            except:
                # Último fallback
                st.session_state[SessionManager.BQ_CLIENT_KEY] = None
        
        st.session_state[SessionManager.IS_AUTHENTICATED_KEY] = True
    
    @staticmethod
    def set_service_account_session(credentials, method: str = 'secrets'):
        """Configura sesión para Service Account"""
        st.session_state[SessionManager.AUTH_METHOD_KEY] = method
        
        # Para service accounts, el proyecto viene en las credenciales
        project = credentials.project_id if hasattr(credentials, 'project_id') else None
        
        st.session_state[SessionManager.BQ_CLIENT_KEY] = bigquery.Client(
            credentials=credentials,
            project=project
        )
        st.session_state[SessionManager.USER_INFO_KEY] = {
            'name': 'Service Account',
            'email': credentials.service_account_email if hasattr(credentials, 'service_account_email') else 'N/A'
        }
        st.session_state[SessionManager.IS_AUTHENTICATED_KEY] = True
    
    @staticmethod
    def get_bigquery_client() -> Optional[bigquery.Client]:
        """Obtiene el cliente de BigQuery actual"""
        return st.session_state.get(SessionManager.BQ_CLIENT_KEY)
    
    @staticmethod
    def get_user_info() -> dict:
        """Obtiene información del usuario autenticado"""
        return st.session_state.get(SessionManager.USER_INFO_KEY, {})
    
    @staticmethod
    def logout():
        """Cierra la sesión y limpia el estado"""
        keys_to_clear = [
            SessionManager.AUTH_METHOD_KEY,
            SessionManager.CREDENTIALS_KEY,
            SessionManager.BQ_CLIENT_KEY,
            SessionManager.USER_INFO_KEY,
            SessionManager.IS_AUTHENTICATED_KEY,
            SessionManager.SELECTED_PROJECT_KEY
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state[SessionManager.IS_AUTHENTICATED_KEY] = False
    
    @staticmethod
    def refresh_oauth_credentials():
        """Refresca las credenciales OAuth si es necesario"""
        from auth.oauth_handler import OAuthHandler
        
        if st.session_state.get(SessionManager.AUTH_METHOD_KEY) == 'oauth':
            creds_dict = st.session_state.get(SessionManager.CREDENTIALS_KEY)
            if creds_dict:
                credentials = OAuthHandler.dict_to_credentials(creds_dict)
                
                if OAuthHandler.is_token_expired(credentials):
                    try:
                        credentials = OAuthHandler.refresh_credentials(credentials)
                        st.session_state[SessionManager.CREDENTIALS_KEY] = OAuthHandler.credentials_to_dict(credentials)
                        
                        # Recrear el cliente con el proyecto seleccionado
                        project = st.session_state.get(SessionManager.SELECTED_PROJECT_KEY)
                        if project:
                            st.session_state[SessionManager.BQ_CLIENT_KEY] = bigquery.Client(
                                credentials=credentials,
                                project=project
                            )
                    except Exception as e:
                        st.error(f"⚠️ Error refrescando credenciales: {e}")
                        SessionManager.logout()
