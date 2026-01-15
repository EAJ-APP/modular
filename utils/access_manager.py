"""
Sistema de Gestión de Accesos para Clientes
Permite crear enlaces con tokens únicos para acceso restringido
"""

import streamlit as st
from datetime import datetime, timedelta
import hashlib
import secrets
import json
from typing import Dict, List, Optional
from google.oauth2.credentials import Credentials
from google.cloud import bigquery

class AccessManager:
    """Gestiona los accesos de clientes mediante tokens y restricciones"""

    # Key para almacenar tokens en secrets o session_state
    TOKENS_KEY = 'client_access_tokens'
    TOKENS_FILE = '/tmp/client_tokens.json'  # Archivo temporal para persistencia

    @staticmethod
    def load_tokens_from_file():
        """Carga tokens desde archivo JSON"""
        try:
            import os
            if os.path.exists(AccessManager.TOKENS_FILE):
                with open(AccessManager.TOKENS_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            st.warning(f"No se pudieron cargar tokens desde archivo: {e}")
        return {}

    @staticmethod
    def save_tokens_to_file(tokens):
        """Guarda tokens en archivo JSON"""
        try:
            with open(AccessManager.TOKENS_FILE, 'w') as f:
                json.dump(tokens, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error guardando tokens: {e}")
            return False

    @staticmethod
    def initialize_tokens():
        """Inicializa el sistema de tokens si no existe"""
        if AccessManager.TOKENS_KEY not in st.session_state:
            # 1. Intentar cargar desde archivo (prioridad más alta)
            tokens = AccessManager.load_tokens_from_file()

            # 2. Si no hay tokens en archivo, intentar desde secrets
            if not tokens:
                try:
                    if AccessManager.TOKENS_KEY in st.secrets:
                        tokens = dict(st.secrets[AccessManager.TOKENS_KEY])
                except:
                    pass

            # 3. Si tampoco hay en secrets, inicializar vacío
            if not tokens:
                tokens = {}

            st.session_state[AccessManager.TOKENS_KEY] = tokens
    
    @staticmethod
    def generate_token() -> str:
        """Genera un token único y seguro"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_client_access(
        client_name: str,
        project_id: str = None,
        dataset_id: str = None,
        allowed_tabs: List[str] = None,
        expiration_days: int = 30,
        notes: str = "",
        require_oauth: bool = False
    ) -> Dict:
        """
        Crea un nuevo acceso para cliente

        Args:
            client_name: Nombre del cliente
            project_id: ID del proyecto BigQuery (opcional si require_oauth=True)
            dataset_id: ID del dataset BigQuery (opcional si require_oauth=True)
            allowed_tabs: Lista de tabs permitidos (opcional si require_oauth=True)
            expiration_days: Días hasta expiración
            notes: Notas adicionales
            require_oauth: Si True, crea token pendiente de OAuth del cliente

        Returns:
            Dict con información del acceso creado
        """
        AccessManager.initialize_tokens()

        # Generar token único
        token = AccessManager.generate_token()

        # Calcular fecha de expiración
        expiration_date = datetime.now() + timedelta(days=expiration_days)

        # Determinar estado inicial
        if require_oauth:
            oauth_status = "pending"  # Esperando OAuth del cliente
        else:
            oauth_status = "not_required"  # No requiere OAuth

        # Crear registro de acceso
        access_data = {
            'token': token,
            'client_name': client_name,
            'project_id': project_id,
            'dataset_id': dataset_id,
            'allowed_tabs': allowed_tabs or [],
            'created_at': datetime.now().isoformat(),
            'expiration_date': expiration_date.isoformat(),
            'notes': notes,
            'active': True,
            'access_count': 0,
            'last_access': None,
            'oauth_status': oauth_status,  # pending | authorized | configured | not_required
            'oauth_credentials': None,  # Credenciales OAuth del cliente
            'oauth_authorized_at': None  # Fecha de autorización OAuth
        }

        # Guardar en session_state
        st.session_state[AccessManager.TOKENS_KEY][token] = access_data

        # Persistir en archivo
        AccessManager.save_tokens_to_file(st.session_state[AccessManager.TOKENS_KEY])

        return access_data
    
    @staticmethod
    def validate_token(token: str) -> Optional[Dict]:
        """
        Valida un token y retorna la información de acceso si es válido
        
        Args:
            token: Token a validar
            
        Returns:
            Dict con información de acceso o None si no es válido
        """
        AccessManager.initialize_tokens()
        
        tokens = st.session_state[AccessManager.TOKENS_KEY]
        
        if token not in tokens:
            return None
        
        access_data = tokens[token]
        
        # Verificar si está activo
        if not access_data.get('active', False):
            return None
        
        # Verificar expiración
        expiration_date = datetime.fromisoformat(access_data['expiration_date'])
        if datetime.now() > expiration_date:
            return None
        
        # Actualizar contador de accesos
        access_data['access_count'] = access_data.get('access_count', 0) + 1
        access_data['last_access'] = datetime.now().isoformat()

        # Persistir cambios
        AccessManager.save_tokens_to_file(st.session_state[AccessManager.TOKENS_KEY])

        return access_data
    
    @staticmethod
    def get_all_tokens() -> Dict:
        """Retorna todos los tokens registrados"""
        AccessManager.initialize_tokens()
        return st.session_state[AccessManager.TOKENS_KEY]
    
    @staticmethod
    def revoke_token(token: str) -> bool:
        """
        Revoca un token (lo marca como inactivo)

        Args:
            token: Token a revocar

        Returns:
            True si se revocó exitosamente
        """
        AccessManager.initialize_tokens()

        tokens = st.session_state[AccessManager.TOKENS_KEY]

        if token in tokens:
            tokens[token]['active'] = False
            AccessManager.save_tokens_to_file(tokens)
            return True

        return False
    
    @staticmethod
    def delete_token(token: str) -> bool:
        """
        Elimina completamente un token

        Args:
            token: Token a eliminar

        Returns:
            True si se eliminó exitosamente
        """
        AccessManager.initialize_tokens()

        tokens = st.session_state[AccessManager.TOKENS_KEY]

        if token in tokens:
            del tokens[token]
            AccessManager.save_tokens_to_file(tokens)
            return True

        return False
    
    @staticmethod
    def extend_expiration(token: str, additional_days: int) -> bool:
        """
        Extiende la fecha de expiración de un token

        Args:
            token: Token a extender
            additional_days: Días adicionales

        Returns:
            True si se extendió exitosamente
        """
        AccessManager.initialize_tokens()

        tokens = st.session_state[AccessManager.TOKENS_KEY]

        if token in tokens:
            current_expiration = datetime.fromisoformat(tokens[token]['expiration_date'])
            new_expiration = current_expiration + timedelta(days=additional_days)
            tokens[token]['expiration_date'] = new_expiration.isoformat()
            AccessManager.save_tokens_to_file(tokens)
            return True

        return False
    
    @staticmethod
    def get_access_url(token: str, base_url: str = None) -> str:
        """
        Genera la URL de acceso para un cliente
        
        Args:
            token: Token de acceso
            base_url: URL base de la aplicación
            
        Returns:
            URL completa con el token
        """
        if base_url is None:
            # Intentar obtener de secrets
            try:
                base_url = st.secrets.get("app_url", "https://modular-t4qqlkh4xr4wdblf4eyjjo.streamlit.app")
            except:
                base_url = "https://modular-t4qqlkh4xr4wdblf4eyjjo.streamlit.app"

        # Construir URL con query parameter (Vista Admin)
        return f"{base_url}/admin_client_view?token={token}"
    
    @staticmethod
    def get_token_stats() -> Dict:
        """
        Obtiene estadísticas generales de tokens
        
        Returns:
            Dict con estadísticas
        """
        AccessManager.initialize_tokens()
        
        tokens = st.session_state[AccessManager.TOKENS_KEY]
        
        total_tokens = len(tokens)
        active_tokens = sum(1 for t in tokens.values() if t.get('active', False))
        expired_tokens = 0
        
        for token_data in tokens.values():
            if token_data.get('active', False):
                expiration = datetime.fromisoformat(token_data['expiration_date'])
                if datetime.now() > expiration:
                    expired_tokens += 1
        
        total_accesses = sum(t.get('access_count', 0) for t in tokens.values())
        
        return {
            'total_tokens': total_tokens,
            'active_tokens': active_tokens,
            'expired_tokens': expired_tokens,
            'revoked_tokens': total_tokens - active_tokens,
            'total_accesses': total_accesses
        }
    
    @staticmethod
    def export_tokens_to_json() -> str:
        """
        Exporta todos los tokens a formato JSON
        
        Returns:
            String JSON con todos los tokens
        """
        AccessManager.initialize_tokens()
        
        tokens = st.session_state[AccessManager.TOKENS_KEY]
        return json.dumps(tokens, indent=2)
    
    @staticmethod
    def import_tokens_from_json(json_str: str) -> bool:
        """
        Importa tokens desde formato JSON

        Args:
            json_str: String JSON con tokens

        Returns:
            True si se importó exitosamente
        """
        try:
            tokens = json.loads(json_str)
            st.session_state[AccessManager.TOKENS_KEY] = tokens
            AccessManager.save_tokens_to_file(tokens)
            return True
        except Exception as e:
            st.error(f"Error importando tokens: {e}")
            return False
    
    @staticmethod
    def get_tab_display_names() -> Dict[str, str]:
        """
        Retorna mapeo de IDs de tabs a nombres amigables
        
        Returns:
            Dict con mapeo tab_id -> display_name
        """
        return {
            'cookies': '🍪 Cookies y Privacidad',
            'ecommerce': '🛒 Ecommerce',
            'acquisition': '📈 Adquisición',
            'events': '🎯 Eventos',
            'users': '👥 Usuarios',
            'sessions': '🕒 Sesiones',
            'monitoring': '📊 Monitorización'
        }
    
    @staticmethod
    def is_admin() -> bool:
        """
        Verifica si el usuario actual es administrador
        
        Returns:
            True si es admin
        """
        # Verificar si hay una sesión de administrador activa
        return st.session_state.get('is_admin', False)
    
    @staticmethod
    def set_admin_session(password: str) -> bool:
        """
        Establece una sesión de administrador

        Args:
            password: Contraseña de admin

        Returns:
            True si la contraseña es correcta
        """
        try:
            admin_password = st.secrets.get("admin_password", "admin123")
        except:
            admin_password = "admin123"

        if password == admin_password:
            st.session_state['is_admin'] = True
            return True

        return False

    @staticmethod
    def save_oauth_credentials(token: str, credentials_dict: Dict) -> bool:
        """
        Guarda las credenciales OAuth del cliente en el token

        Args:
            token: Token del cliente
            credentials_dict: Diccionario con credenciales OAuth

        Returns:
            True si se guardó exitosamente
        """
        AccessManager.initialize_tokens()

        tokens = st.session_state[AccessManager.TOKENS_KEY]

        if token in tokens:
            tokens[token]['oauth_credentials'] = credentials_dict
            tokens[token]['oauth_status'] = 'authorized'
            tokens[token]['oauth_authorized_at'] = datetime.now().isoformat()
            AccessManager.save_tokens_to_file(tokens)
            return True

        return False

    @staticmethod
    def configure_oauth_token(token: str, project_id: str, dataset_id: str) -> bool:
        """
        Configura project/dataset para un token que ya tiene OAuth autorizado

        Args:
            token: Token del cliente
            project_id: ID del proyecto BigQuery
            dataset_id: ID del dataset BigQuery

        Returns:
            True si se configuró exitosamente
        """
        AccessManager.initialize_tokens()

        tokens = st.session_state[AccessManager.TOKENS_KEY]

        if token in tokens and tokens[token]['oauth_status'] == 'authorized':
            tokens[token]['project_id'] = project_id
            tokens[token]['dataset_id'] = dataset_id
            tokens[token]['oauth_status'] = 'configured'
            AccessManager.save_tokens_to_file(tokens)
            return True

        return False

    @staticmethod
    def get_oauth_url(token: str, base_url: str = None) -> str:
        """
        Genera la URL de OAuth para que el cliente autorice

        Args:
            token: Token de acceso
            base_url: URL base de la aplicación

        Returns:
            URL completa con el token para OAuth
        """
        if base_url is None:
            try:
                base_url = st.secrets.get("app_url", "https://modular-t4qqlkh4xr4wdblf4eyjjo.streamlit.app")
            except:
                base_url = "https://modular-t4qqlkh4xr4wdblf4eyjjo.streamlit.app"

        return f"{base_url}/client_oauth?token={token}"

    @staticmethod
    def get_oauth_credentials(token: str) -> Optional[Dict]:
        """
        Obtiene las credenciales OAuth guardadas para un token

        Args:
            token: Token del cliente

        Returns:
            Dict con credenciales o None si no existen
        """
        AccessManager.initialize_tokens()

        tokens = st.session_state[AccessManager.TOKENS_KEY]

        if token in tokens:
            return tokens[token].get('oauth_credentials')

        return None

    @staticmethod
    def get_bigquery_client_from_token(token: str) -> Optional[bigquery.Client]:
        """
        Crea un cliente de BigQuery usando las credenciales OAuth de un token

        Args:
            token: Token del cliente

        Returns:
            Cliente de BigQuery o None si no hay credenciales
        """
        creds_dict = AccessManager.get_oauth_credentials(token)

        if not creds_dict:
            return None

        try:
            # Reconstruir credenciales desde el diccionario
            credentials = Credentials(
                token=creds_dict.get('token'),
                refresh_token=creds_dict.get('refresh_token'),
                token_uri=creds_dict.get('token_uri'),
                client_id=creds_dict.get('client_id'),
                client_secret=creds_dict.get('client_secret'),
                scopes=creds_dict.get('scopes', [])
            )

            # Crear cliente de BigQuery
            return bigquery.Client(credentials=credentials)

        except Exception as e:
            st.error(f"Error creando cliente BigQuery: {e}")
            return None

    @staticmethod
    def is_ga4_dataset(client: bigquery.Client, project_id: str, dataset_id: str) -> bool:
        """
        Verifica si un dataset es de GA4 (tiene tablas events_*)

        Args:
            client: Cliente de BigQuery
            project_id: ID del proyecto
            dataset_id: ID del dataset

        Returns:
            True si es dataset de GA4
        """
        try:
            # Listar tablas del dataset
            dataset_ref = f"{project_id}.{dataset_id}"
            tables = list(client.list_tables(dataset_ref, max_results=10))

            # Verificar si hay tablas que empiecen con "events_"
            for table in tables:
                if table.table_id.startswith('events_'):
                    return True

            return False

        except Exception:
            return False

    @staticmethod
    def get_ga4_projects_and_datasets(token: str) -> Dict[str, List[str]]:
        """
        Obtiene proyectos y datasets de GA4 usando las credenciales OAuth del token

        Args:
            token: Token del cliente

        Returns:
            Dict con {project_id: [lista de datasets GA4]}
        """
        client = AccessManager.get_bigquery_client_from_token(token)

        if not client:
            return {}

        ga4_projects = {}

        try:
            # Listar todos los proyectos
            projects = list(client.list_projects())

            for project in projects:
                project_id = project.project_id

                try:
                    # Listar datasets del proyecto
                    datasets = list(client.list_datasets(project_id))

                    # Filtrar solo datasets de GA4
                    ga4_datasets = []
                    for dataset in datasets:
                        dataset_id = dataset.dataset_id

                        if AccessManager.is_ga4_dataset(client, project_id, dataset_id):
                            ga4_datasets.append(dataset_id)

                    # Solo añadir el proyecto si tiene datasets GA4
                    if ga4_datasets:
                        ga4_projects[project_id] = ga4_datasets

                except Exception:
                    # Si no se pueden listar datasets del proyecto, continuar
                    continue

            return ga4_projects

        except Exception as e:
            st.error(f"Error listando proyectos: {e}")
            return {}
