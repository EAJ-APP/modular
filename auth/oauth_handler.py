import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.cloud import bigquery
from datetime import datetime, timedelta
import json
from typing import Optional, Dict

class OAuthHandler:
    """Manejador de autenticación OAuth con Google"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scopes: list):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        
    def create_flow(self) -> Flow:
        """Crea el flujo de OAuth"""
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }
        
        return Flow.from_client_config(
            client_config,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
    
def get_authorization_url(self) -> str:
    """Genera la URL de autorización para login"""
    flow = self.create_flow()
    
    import time
    import hashlib
    
    # Generar un nonce único basado en timestamp
    nonce = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        login_hint=None,  # Forzar selección de cuenta
        # Añadir parámetro custom para evitar caché
        state=f"{state}_{nonce}"  # Hacer el state más único
    )
    
    # Guardar state en session_state
    st.session_state['oauth_state'] = state
    
    return authorization_url
    
    def handle_oauth_callback(self, authorization_response: str) -> Optional[Credentials]:
        """
        Maneja el callback de OAuth y obtiene las credenciales
        
        Args:
            authorization_response: URL completa de callback con code
            
        Returns:
            Credentials de Google o None si falla
        """
        try:
            flow = self.create_flow()
            
            # Verificar state (seguridad)
            if 'oauth_state' in st.session_state:
                flow.fetch_token(authorization_response=authorization_response)
                credentials = flow.credentials
                
                # Limpiar state
                del st.session_state['oauth_state']
                
                return credentials
            else:
                st.error("⚠️ Error de seguridad: State inválido")
                return None
                
        except Exception as e:
            st.error(f"❌ Error en OAuth callback: {str(e)}")
            return None
    
    @staticmethod
    def credentials_to_dict(credentials: Credentials) -> Dict:
        """Convierte Credentials a diccionario serializable"""
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
    
    @staticmethod
    def dict_to_credentials(creds_dict: Dict) -> Credentials:
        """Convierte diccionario a Credentials"""
        expiry = datetime.fromisoformat(creds_dict['expiry']) if creds_dict.get('expiry') else None
        
        return Credentials(
            token=creds_dict['token'],
            refresh_token=creds_dict.get('refresh_token'),
            token_uri=creds_dict['token_uri'],
            client_id=creds_dict['client_id'],
            client_secret=creds_dict['client_secret'],
            scopes=creds_dict['scopes'],
            expiry=expiry
        )
    
    @staticmethod
    def get_bigquery_client_from_credentials(credentials: Credentials, project: Optional[str] = None) -> bigquery.Client:
        """
        Crea un cliente de BigQuery desde las credenciales OAuth
        
        Args:
            credentials: Credenciales OAuth de Google
            project: Project ID (opcional, se intentará detectar automáticamente)
            
        Returns:
            Cliente de BigQuery configurado
        """
        if not project:
            try:
                # Intentar listar proyectos para obtener el primero disponible
                temp_client = bigquery.Client(credentials=credentials, project='dummy-project')
                projects = list(temp_client.list_projects(max_results=1))
                if projects:
                    project = projects[0].project_id
                else:
                    # Fallback al proyecto del service account si está disponible
                    try:
                        project = st.secrets.get("gcp_service_account", {}).get("project_id", "ai-nibw")
                    except:
                        project = "ai-nibw"
            except Exception:
                # Último fallback
                try:
                    project = st.secrets.get("gcp_service_account", {}).get("project_id", "ai-nibw")
                except:
                    project = "ai-nibw"
        
        return bigquery.Client(credentials=credentials, project=project)
    
    @staticmethod
    def is_token_expired(credentials: Credentials) -> bool:
        """Verifica si el token ha expirado"""
        if not credentials.expiry:
            return False
        return datetime.utcnow() >= credentials.expiry
    
    @staticmethod
    def refresh_credentials(credentials: Credentials) -> Credentials:
        """Refresca las credenciales si es necesario"""
        from google.auth.transport.requests import Request
        
        if OAuthHandler.is_token_expired(credentials):
            credentials.refresh(Request())
        
        return credentials
