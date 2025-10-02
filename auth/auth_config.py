import streamlit as st
from typing import Dict, List

class AuthConfig:
    """Configuración centralizada de autenticación"""
    
    # OAuth Scopes necesarios
    SCOPES: List[str] = [
        'https://www.googleapis.com/auth/bigquery.readonly',
        'https://www.googleapis.com/auth/bigquery',
        'openid',
        'email',
        'profile'
    ]
    
    # Métodos de autenticación disponibles
    AUTH_METHODS = {
        'oauth': '🔐 Login con Google',
        'json': '📄 Subir Service Account JSON',
        'secrets': '🔑 Usar Secrets Configurados'
    }
    
    @staticmethod
    def get_oauth_config() -> Dict[str, str]:
        """
        Obtiene la configuración de OAuth desde secrets
        
        Returns:
            dict con client_id y client_secret
        """
        try:
            return {
                'client_id': st.secrets["oauth"]["client_id"],
                'client_secret': st.secrets["oauth"]["client_secret"],
                'redirect_uri': st.secrets["oauth"]["redirect_uri"]
            }
        except KeyError:
            st.error("⚠️ OAuth no configurado en secrets. Añade [oauth] con client_id, client_secret y redirect_uri")
            return {}
    
    @staticmethod
    def is_oauth_configured() -> bool:
        """Verifica si OAuth está configurado"""
        try:
            oauth_config = AuthConfig.get_oauth_config()
            return all(oauth_config.values())
        except:
            return False
    
    @staticmethod
    def is_secrets_configured() -> bool:
        """Verifica si service account secrets están configurados"""
        try:
            return "gcp_service_account" in st.secrets
        except:
            return False
