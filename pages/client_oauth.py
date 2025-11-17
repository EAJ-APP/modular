"""
Página de Autorización OAuth para Clientes
Permite a los clientes autorizar el acceso a sus datos de BigQuery mediante OAuth
"""

import streamlit as st
from auth import OAuthHandler, AuthConfig
from utils.access_manager import AccessManager
import requests
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta

# Configuración de página
st.set_page_config(
    page_title="Autorización de Acceso",
    layout="centered",
    page_icon="🔐"
)

# CSS para ocultar sidebar y menú
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="collapsedControl"] {
            display: none;
        }
        .stDeployButton {
            display: none;
        }
        #MainMenu {
            display: none;
        }
        header {
            visibility: hidden;
        }
    </style>
""", unsafe_allow_html=True)

def handle_oauth_callback(token: str):
    """
    Maneja el callback de OAuth después del login del cliente
    """
    query_params = st.query_params

    if 'code' in query_params:
        with st.spinner("🔄 Completando autorización..."):
            try:
                oauth_config = AuthConfig.get_oauth_config()

                # Mostrar progreso
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("🔄 Intercambiando código por token...")
                progress_bar.progress(25)

                # Intercambiar código por token usando petición HTTP directa
                token_response = requests.post(
                    'https://oauth2.googleapis.com/token',
                    data={
                        'code': query_params['code'],
                        'client_id': oauth_config['client_id'],
                        'client_secret': oauth_config['client_secret'],
                        'redirect_uri': oauth_config['redirect_uri'],
                        'grant_type': 'authorization_code'
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )

                if token_response.status_code != 200:
                    st.error(f"❌ Error obteniendo token: {token_response.status_code}")
                    st.code(token_response.text)
                    return False

                token_data = token_response.json()

                status_text.text("✅ Token obtenido correctamente")
                progress_bar.progress(50)

                # Crear credenciales manualmente
                expiry = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))

                credentials = Credentials(
                    token=token_data['access_token'],
                    refresh_token=token_data.get('refresh_token'),
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=oauth_config['client_id'],
                    client_secret=oauth_config['client_secret'],
                    scopes=token_data.get('scope', '').split(),
                    expiry=expiry
                )

                status_text.text("✅ Credenciales creadas")
                progress_bar.progress(75)

                # Convertir credenciales a diccionario
                creds_dict = OAuthHandler.credentials_to_dict(credentials)

                # Guardar credenciales en el token
                if AccessManager.save_oauth_credentials(token, creds_dict):
                    status_text.text("✅ Credenciales guardadas")
                    progress_bar.progress(90)

                    # Obtener info del usuario
                    user_info = get_user_info_from_token(credentials.token)

                    progress_bar.progress(100)

                    # Limpiar query params
                    st.query_params.clear()

                    # Mostrar mensaje de éxito
                    st.success("✅ ¡Autorización completada exitosamente!")
                    st.balloons()

                    st.markdown(f"""
                    ### 🎉 ¡Gracias, {user_info.get('name', 'Usuario')}!

                    Tu autorización ha sido registrada correctamente.

                    #### ¿Qué sigue?

                    1. ✅ Has autorizado el acceso a tu cuenta de BigQuery
                    2. 📧 El administrador será notificado
                    3. ⚙️ El administrador configurará el proyecto y dataset específico
                    4. 🚀 Una vez configurado, el administrador podrá acceder a tus datos

                    **Puedes cerrar esta ventana ahora.**

                    ---

                    *Si tienes alguna pregunta, contacta al administrador que te envió este enlace.*
                    """)

                    return True
                else:
                    st.error("❌ Error guardando las credenciales")
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

# ==========================================
# FLUJO PRINCIPAL
# ==========================================

# Obtener token de los parámetros de query
token = st.query_params.get('token')

if not token:
    st.error("❌ Token no proporcionado")
    st.markdown("""
    ### Error de Acceso

    No se ha proporcionado un token de autorización válido.

    Por favor, usa el enlace completo que te proporcionó el administrador.
    """)
    st.stop()

# Validar el token
AccessManager.initialize_tokens()
tokens = AccessManager.get_all_tokens()

if token not in tokens:
    st.error("❌ Token inválido")
    st.markdown("""
    ### Token No Válido

    El token proporcionado no existe o ha sido eliminado.

    Por favor, contacta al administrador para obtener un nuevo enlace.
    """)
    st.stop()

token_data = tokens[token]

# Verificar estado del token
oauth_status = token_data.get('oauth_status', 'not_required')

# IMPORTANTE: Manejar callback ANTES de mostrar opciones
if handle_oauth_callback(token):
    st.stop()  # Si hay callback exitoso, no mostrar el resto

# Si ya está autorizado, mostrar mensaje
if oauth_status == 'authorized' or oauth_status == 'configured':
    st.success("✅ Ya has autorizado el acceso anteriormente")
    st.markdown(f"""
    ### ✅ Autorización Completada

    **Cliente:** {token_data['client_name']}

    Este enlace ya ha sido usado para autorizar el acceso.

    Si necesitas realizar cambios o revocar el acceso, contacta al administrador.

    **Puedes cerrar esta ventana.**
    """)
    st.stop()

# Si no requiere OAuth, mostrar error
if oauth_status == 'not_required':
    st.warning("⚠️ Este token no requiere autorización OAuth")
    st.markdown("""
    ### Configuración Incorrecta

    Este enlace no está configurado para autorización OAuth.

    Por favor, contacta al administrador.
    """)
    st.stop()

# Si el token está pendiente de OAuth, mostrar página de autorización
if oauth_status == 'pending':

    # Header
    st.title("🔐 Autorización de Acceso")
    st.markdown(f"""
    ### Hola, **{token_data['client_name']}**

    Para que el administrador pueda acceder a tus datos de Google BigQuery,
    necesitamos que autorices el acceso mediante tu cuenta de Google.
    """)

    st.divider()

    # Explicación del proceso
    st.markdown("""
    ## 🛡️ ¿Qué estás autorizando?

    Al hacer clic en el botón de abajo, se te pedirá:

    1. **Iniciar sesión con tu cuenta de Google** (si no lo has hecho ya)
    2. **Autorizar el acceso a BigQuery** para que el administrador pueda:
       - Ver tus proyectos de BigQuery
       - Ejecutar consultas en tu nombre
       - Acceder a los datos de Analytics que especifiques

    ## 🔒 Seguridad y Privacidad

    - ✅ Solo el administrador que creó este enlace tendrá acceso
    - ✅ El acceso es específico al proyecto/dataset que elijas
    - ✅ Puedes revocar el acceso en cualquier momento
    - ✅ No compartimos tu información con terceros

    ## 📝 ¿Qué sigue después de autorizar?

    1. Autorizas el acceso (este paso)
    2. El administrador selecciona el proyecto y dataset específico
    3. El administrador puede empezar a trabajar con tus datos

    ---
    """)

    st.info("""
    **💡 Importante:** Asegúrate de iniciar sesión con la cuenta de Google
    que tiene acceso al proyecto de BigQuery que quieres compartir.
    """)

    st.divider()

    # Verificar que OAuth esté disponible
    oauth_available = AuthConfig.is_oauth_configured()

    if oauth_available:
        try:
            # Generar la URL de autorización
            oauth_config = AuthConfig.get_oauth_config()

            oauth_handler = OAuthHandler(
                client_id=oauth_config['client_id'],
                client_secret=oauth_config['client_secret'],
                redirect_uri=oauth_config['redirect_uri'],
                scopes=AuthConfig.SCOPES
            )

            auth_url = oauth_handler.get_authorization_url()

            # Botón principal de autorización
            st.markdown("### 🚀 Autorizar Acceso")

            st.link_button(
                "🔐 Autorizar con Google",
                auth_url,
                use_container_width=True,
                type="primary"
            )

            st.caption("Al hacer clic, serás redirigido a Google para autorizar el acceso")

            # Opcional: mostrar la URL por si acaso
            with st.expander("🔍 Ver URL de autorización (avanzado)"):
                st.code(auth_url, language=None)
                st.caption("Puedes copiar esta URL y pegarla en tu navegador si el botón no funciona")

        except Exception as e:
            st.error(f"❌ Error generando URL de autorización: {str(e)}")
    else:
        st.error("❌ OAuth no configurado. Contacta al administrador.")

# Footer
st.divider()
st.caption("🔐 Autorización de Acceso - BigQuery Shield | FLAT 101 Digital Business")
