"""
Página de Autorización OAuth para Clientes
Permite a los clientes autorizar el acceso a sus datos de BigQuery mediante OAuth
y seleccionar el proyecto/dataset
"""

import streamlit as st
from auth import OAuthHandler, AuthConfig
from utils.access_manager import AccessManager
import requests
from google.oauth2.credentials import Credentials
from google.cloud import bigquery
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
    Retorna las credenciales si fue exitoso
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
                    return None

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

                # Obtener info del usuario
                user_info = get_user_info_from_token(credentials.token)

                status_text.text(f"✅ Usuario identificado: {user_info.get('name', 'Usuario')}")
                progress_bar.progress(100)

                # Limpiar query params
                st.query_params.clear()

                # Guardar en session_state para el siguiente paso
                st.session_state['oauth_credentials'] = credentials
                st.session_state['oauth_user_info'] = user_info
                st.session_state['oauth_token'] = token
                st.session_state['oauth_completed'] = True

                st.success("✅ ¡Autorización completada!")
                st.balloons()

                return credentials

            except Exception as e:
                st.error(f"❌ Error en callback OAuth: {str(e)}")
                with st.expander("🔍 Ver detalles técnicos"):
                    import traceback
                    st.code(traceback.format_exc())

                # Botón para limpiar y volver a intentar
                if st.button("🔄 Volver a intentar"):
                    st.query_params.clear()
                    st.rerun()

                return None

    return None

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

def list_projects(credentials):
    """Lista los proyectos de BigQuery del cliente"""
    try:
        # Crear cliente temporal con las credenciales del cliente
        client = bigquery.Client(credentials=credentials, project='dummy-project-for-listing')
        projects = list(client.list_projects())
        return [(p.project_id, p.friendly_name or p.project_id) for p in projects]
    except Exception as e:
        st.error(f"❌ Error listando proyectos: {str(e)}")
        return []

def list_datasets(credentials, project_id):
    """Lista los datasets de un proyecto"""
    try:
        client = bigquery.Client(credentials=credentials, project=project_id)
        datasets = list(client.list_datasets())
        return [d.dataset_id for d in datasets]
    except Exception as e:
        st.error(f"❌ Error listando datasets: {str(e)}")
        return []

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

# Si ya está configurado, mostrar mensaje
if oauth_status == 'configured':
    st.success("✅ Ya has configurado el acceso anteriormente")
    st.markdown(f"""
    ### ✅ Configuración Completada

    **Cliente:** {token_data['client_name']}
    **Proyecto:** {token_data.get('project_id', 'N/A')}
    **Dataset:** {token_data.get('dataset_id', 'N/A')}

    Este enlace ya ha sido configurado.

    El administrador ya puede acceder a tus datos usando su enlace.

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

# IMPORTANTE: Manejar callback PRIMERO
credentials = handle_oauth_callback(token)

# Si acabamos de completar OAuth o ya lo teníamos en session_state
if credentials or st.session_state.get('oauth_completed', False):

    # Recuperar credenciales de session_state si no las tenemos
    if not credentials:
        credentials = st.session_state.get('oauth_credentials')

    user_info = st.session_state.get('oauth_user_info', {'name': 'Usuario'})

    # Header
    st.title("🔐 Configuración de Acceso")
    st.markdown(f"""
    ### ¡Gracias, **{user_info.get('name', 'Usuario')}**!

    Tu autorización ha sido completada. Ahora selecciona el proyecto y dataset de BigQuery al que quieres dar acceso.
    """)

    st.divider()

    # Obtener proyectos
    with st.spinner("📊 Cargando tus proyectos de BigQuery..."):
        projects = list_projects(credentials)

    if not projects:
        st.error("❌ No se pudieron cargar tus proyectos de BigQuery")
        st.warning("Verifica que tu cuenta tenga acceso a BigQuery y que los permisos OAuth sean correctos.")
        st.stop()

    # Selector de proyecto
    st.subheader("1️⃣ Selecciona tu Proyecto")

    project_options = {f"{name} ({pid})": pid for pid, name in projects}

    selected_project_display = st.selectbox(
        "Proyecto de BigQuery:",
        options=list(project_options.keys()),
        help="Selecciona el proyecto que contiene los datos de Analytics"
    )

    selected_project = project_options[selected_project_display]

    st.divider()

    # Selector de dataset
    st.subheader("2️⃣ Selecciona tu Dataset")

    with st.spinner(f"📂 Cargando datasets del proyecto {selected_project}..."):
        datasets = list_datasets(credentials, selected_project)

    if not datasets:
        st.error(f"❌ No se encontraron datasets en el proyecto {selected_project}")
        st.info("Verifica que el proyecto seleccionado tenga datasets de BigQuery.")
        st.stop()

    selected_dataset = st.selectbox(
        "Dataset de BigQuery:",
        options=datasets,
        help="Selecciona el dataset que contiene los datos de Google Analytics 4"
    )

    st.divider()

    # Resumen de la configuración
    st.subheader("📋 Resumen de Configuración")

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"**Proyecto:** {selected_project}")

    with col2:
        st.info(f"**Dataset:** {selected_dataset}")

    st.warning("""
    ⚠️ **Importante:** Esta configuración es permanente.
    Una vez confirmada, el administrador podrá acceder a este proyecto y dataset.
    Si necesitas cambiar la configuración, deberás contactar al administrador.
    """)

    # Botón de confirmación
    if st.button("✅ Confirmar y Finalizar", type="primary", use_container_width=True):
        with st.spinner("💾 Guardando configuración..."):
            try:
                # Convertir credenciales a diccionario
                creds_dict = OAuthHandler.credentials_to_dict(credentials)

                # Guardar todo de una vez usando el nuevo método
                if AccessManager.configure_oauth_token_complete(token, creds_dict, selected_project, selected_dataset):
                    st.success("✅ ¡Configuración guardada exitosamente!")
                    st.balloons()

                    # Limpiar session_state
                    if 'oauth_credentials' in st.session_state:
                        del st.session_state['oauth_credentials']
                    if 'oauth_user_info' in st.session_state:
                        del st.session_state['oauth_user_info']
                    if 'oauth_completed' in st.session_state:
                        del st.session_state['oauth_completed']

                    st.markdown(f"""
                    ### 🎉 ¡Todo Listo!

                    **Tu configuración ha sido guardada:**
                    - ✅ Autorización OAuth completada
                    - ✅ Proyecto: {selected_project}
                    - ✅ Dataset: {selected_dataset}

                    El administrador ya puede acceder a tus datos de BigQuery.

                    **Puedes cerrar esta ventana ahora.**

                    ---

                    *Si tienes alguna pregunta, contacta al administrador que te envió este enlace.*
                    """)

                    st.stop()
                else:
                    st.error("❌ Error guardando la configuración. Por favor, contacta al administrador.")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                with st.expander("🔍 Ver detalles técnicos"):
                    import traceback
                    st.code(traceback.format_exc())

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
    2. **Autorizar el acceso a BigQuery** para que el administrador pueda ejecutar consultas en tu nombre
    3. **Seleccionar tu proyecto y dataset** de BigQuery

    ## 🔒 Seguridad y Privacidad

    - ✅ Solo el administrador que creó este enlace tendrá acceso
    - ✅ El acceso es específico al proyecto/dataset que selecciones
    - ✅ Puedes revocar el acceso en cualquier momento contactando al administrador
    - ✅ No compartimos tu información con terceros

    ## 📝 ¿Qué sigue después de autorizar?

    1. Autorizas el acceso con Google (siguiente paso)
    2. Seleccionas el proyecto y dataset de BigQuery
    3. ¡Listo! El administrador podrá acceder a tus datos

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
