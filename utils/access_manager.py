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

class AccessManager:
    """Gestiona los accesos de clientes mediante tokens y restricciones"""
    
    # Key para almacenar tokens en secrets o session_state
    TOKENS_KEY = 'client_access_tokens'
    
    @staticmethod
    def initialize_tokens():
        """Inicializa el sistema de tokens si no existe"""
        if AccessManager.TOKENS_KEY not in st.session_state:
            # Intentar cargar desde secrets si existen
            try:
                if AccessManager.TOKENS_KEY in st.secrets:
                    st.session_state[AccessManager.TOKENS_KEY] = dict(st.secrets[AccessManager.TOKENS_KEY])
                else:
                    st.session_state[AccessManager.TOKENS_KEY] = {}
            except:
                st.session_state[AccessManager.TOKENS_KEY] = {}
    
    @staticmethod
    def generate_token() -> str:
        """Genera un token único y seguro"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_client_access(
        client_name: str,
        project_id: str,
        dataset_id: str,
        allowed_tabs: List[str],
        expiration_days: int = 30,
        notes: str = ""
    ) -> Dict:
        """
        Crea un nuevo acceso para cliente
        
        Args:
            client_name: Nombre del cliente
            project_id: ID del proyecto BigQuery
            dataset_id: ID del dataset BigQuery
            allowed_tabs: Lista de tabs permitidos
            expiration_days: Días hasta expiración
            notes: Notas adicionales
            
        Returns:
            Dict con información del acceso creado
        """
        AccessManager.initialize_tokens()
        
        # Generar token único
        token = AccessManager.generate_token()
        
        # Calcular fecha de expiración
        expiration_date = datetime.now() + timedelta(days=expiration_days)
        
        # Crear registro de acceso
        access_data = {
            'token': token,
            'client_name': client_name,
            'project_id': project_id,
            'dataset_id': dataset_id,
            'allowed_tabs': allowed_tabs,
            'created_at': datetime.now().isoformat(),
            'expiration_date': expiration_date.isoformat(),
            'notes': notes,
            'active': True,
            'access_count': 0,
            'last_access': None
        }
        
        # Guardar en session_state
        st.session_state[AccessManager.TOKENS_KEY][token] = access_data
        
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
                base_url = st.secrets.get("app_url", "https://your-app.streamlit.app")
            except:
                base_url = "https://your-app.streamlit.app"
        
        # Construir URL con query parameter
        return f"{base_url}/client_access?token={token}"
    
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
