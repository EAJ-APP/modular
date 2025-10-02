import streamlit as st
from google.oauth2 import service_account
from auth import OAuthHandler, SessionManager, AuthConfig
import json
import requests

def show_login_screen():
    """Muestra la pantalla de login con las 3 opciones"""
    
    # Configurar página
    st.set_page_config(
        page_title="BigQuery Shield - Login",
        layout="centered",
        page_icon="🛡️"
    )
    
    # Header con logo y título
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🛡️ BigQuery Shield")
        st.markdown("### Plataforma de Análisis GA4")
    
    st.divider()
    
    # IMPORTANTE: Manejar callback ANTES de mostrar opciones
    if handle_oauth_callback():
        return  # Si hay callback exitoso, no mostrar el resto
    
    # Verificar qué métodos están disponibles
    oauth_available = AuthConfig.is_oauth_configured()
    secrets_available = AuthConfig.is_secrets_configured()
    
    # Mostrar opciones de login
    st.markdown("## Selecciona cómo conectarte:")
    st.markdown("")
    
    # OPCIÓN 1: OAuth Login con Google
    with st.container():
        st.markdown("### 🔐 Login con Google")
        st.markdown("Accede usando tu cuenta de Google con permisos en BigQuery")
        
        if oauth_available:
            if st.button("🚀 Login con Google", use_container_width=True, type="primary"):
                handle_oauth_login()
        else:
            st.warning("⚠️ OAuth no configurado. Contacta al administrador.")
            with st.expander("ℹ️ Información para administradores"):
                st.code("""
# Añade esto a tus secrets de Streamlit:

[oauth]
client_id = "TU_CLIENT_ID.apps.googleusercontent.com"
client_secret = "TU_CLIENT_SECRET"
redirect_uri = "https://TU-APP.streamlit.app"
                """)
    
    st.divider()
    
    # OPCIÓN 2: Upload JSON
    with st.container():
        st.markdown("### 📄 Subir Service Account JSON")
        st.markdown("Modo desarrollo: Sube un archivo JSON de service account")
        
        uploaded_file = st.file_uploader(
            "Selecciona tu archivo JSON",
            type=['json'],
            help="Archivo de credenciales de Google Cloud Service Account"
        )
        
        if uploaded_file is not None:
            if st.button("✅ Conectar con JSON", use_container_width=True):
                handle_json_upload(uploaded_file)
    
    st.divider()
    
    # OPCIÓN 3: Usar Secrets
    with st.container():
        st.markdown("### 🔑 Usar Secrets Configurados")
        st.markdown("Acceso directo usando service account pre-configurado")
        
        if secrets_available:
            if st.button("⚡ Acceso Directo", use_container_width=True):
                handle_secrets_login()
        else:
            st.warning("⚠️ Service Account no configurado en secrets.")
            with st.expander("ℹ️ Información para administradores"):
                st.code("""
# Añade [gcp_service_account] a tus secrets de Streamlit
# con la configuración de tu service account
                """)
    
    # Footer
    st.divider()
    st.caption("© 2025 FLAT 101 Digital Business | BigQuery Shield v1.0")

def handle_oauth_login():
    """Inicia el flujo de OAuth"""
    try:
        oauth_config = AuthConfig.get_oauth_config()
        
        oauth_handler = OAuthHandler(
            client_id=oauth_config['client_id'],
            client_secret=oauth_config['client_secret'],
            redirect_uri=oauth_config['redirect_uri'],
            scopes=AuthConfig.SCOPES
        )
        
        authorization_url = oauth_handler.get_authorization_url()
        
        st.info("🔄 Redirigiendo a Google para autenticación...")
        st.markdown(f"[🔗 Click aquí para autenticarte]({authorization_url})")
        
        # Redirección con meta refresh (más compatible)
        st.markdown(f"""
        <meta http-equiv="refresh" content="0; url={authorization_url}">
        <p>Si no se redirige automáticamente, <a href="{authorization_url}">click aquí</a></p>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Error iniciando OAuth: {str(e)}")
        with st.expander("🔍 Ver detalles del error"):
            st.code(str(e))

def handle_oauth_callback():
    """
    Maneja el callback de OAuth después del login
    Returns True si hubo un callback exitoso
    """
    # Obtener parámetros de la URL
    query_params = st.query_params
    
    # Debug: Mostrar parámetros recibidos
    if len(query_params) > 0:
        with st.expander("🔍 Debug - Parámetros recibidos"):
            st.json(dict(query_params))
    
    if 'code' in query_params:
        with st.spinner("🔄 Completando autenticación..."):
            try:
                oauth_config = AuthConfig.get_oauth_config()
                
                # Crear handler
                oauth_handler = OAuthHandler(
                    client_id=oauth_config['client_id'],
                    client_secret=oauth_config['client_secret'],
                    redirect_uri=oauth_config['redirect_uri'],
                    scopes=AuthConfig.SCOPES
                )
                
                # CORRECCIÓN CRÍTICA: Usar solo el código, no construir URL completa
                # El método fetch_token de google-auth-oauthlib necesita solo authorization_response
                
                # Construir la URL de callback COMPLETA como la recibió Google
                from urllib.parse import urlencode
                
                # Obtener la URL base actual
                import streamlit.web.bootstrap as bootstrap
                
                # Método alternativo: usar solo el código directamente
                flow = oauth_handler.create_flow()
                
                # Fetch token usando el authorization response completo
                # Necesitamos reconstruir la URL completa con todos los parámetros
                params = dict(query_params)
                authorization_response = f"{oauth_config['redirect_uri']}?{urlencode(params)}"
                
                st.write("🔍 **Debug**: URL de callback construida:")
                st.code(authorization_response)
                
                # Intentar obtener el token
                flow.fetch_token(authorization_response=authorization_response)
                credentials = flow.credentials
                
                if credentials:
                    # Obtener info del usuario
                    user_info = get_user_info_from_token(credentials.token)
                    
                    # Configurar sesión
                    SessionManager.set_oauth_session(credentials, user_info)
                    
                    # Limpiar query params
                    st.query_params.clear()
                    
                    st.success(f"✅ Bienvenido, {user_info.get('name', 'Usuario')}!")
                    st.balloons()
                    
                    # Recargar para ir a la app principal
                    st.rerun()
                    return True
                else:
                    st.error("❌ Error obteniendo credenciales")
                    return False
                    
            except Exception as e:
                st.error(f"❌ Error en callback OAuth: {str(e)}")
                with st.expander("🔍 Ver detalles técnicos"):
                    import traceback
                    st.code(traceback.format_exc())
                
                # Botón para limpiar y volver a intentar
                if st.button("🔄 Volver a intentar"):
                    st.query_params.clear()
                    st.rerun()
                
                return False
    
    return False

def get_user_info_from_token(access_token: str) -> dict:
    """Obtiene información del usuario desde el token de acceso"""
    try:
        response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'name': 'Usuario', 'email': 'unknown@example.com'}
            
    except Exception as e:
        st.warning(f"⚠️ No se pudo obtener info del usuario: {e}")
        return {'name': 'Usuario', 'email': 'unknown@example.com'}

def handle_json_upload(uploaded_file):
    """Maneja la subida de archivo JSON"""
    try:
        # Leer archivo JSON
        credentials_dict = json.load(uploaded_file)
        
        # Validar que sea un service account válido
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        if not all(field in credentials_dict for field in required_fields):
            st.error("❌ JSON inválido. Asegúrate de usar un Service Account JSON válido.")
            return
        
        if credentials_dict['type'] != 'service_account':
            st.error("❌ El archivo debe ser de tipo 'service_account'")
            return
        
        # Crear credenciales
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        
        # Configurar sesión
        SessionManager.set_service_account_session(credentials, method='json')
        
        st.success(f"✅ Conectado como: {credentials.service_account_email}")
        st.balloons()
        
        # Recargar para ir a la app principal
        st.rerun()
        
    except json.JSONDecodeError:
        st.error("❌ Error leyendo el archivo JSON. Verifica que sea válido.")
    except Exception as e:
        st.error(f"❌ Error procesando el archivo: {str(e)}")

def handle_secrets_login():
    """Maneja el login usando secrets configurados"""
    try:
        # Obtener credenciales desde secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        
        # Configurar sesión
        SessionManager.set_service_account_session(credentials, method='secrets')
        
        st.success(f"✅ Conectado como: {credentials.service_account_email}")
        st.balloons()
        
        # Recargar para ir a la app principal
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error conectando con secrets: {str(e)}")
