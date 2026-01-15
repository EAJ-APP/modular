"""
Página de Visualización Admin
Permite al admin ver datos de clientes usando sus credenciales OAuth
"""

import streamlit as st
from datetime import datetime
from utils.access_manager import AccessManager
from auth import SessionManager
from google.cloud import bigquery
from google.oauth2 import service_account

# Importar tabs (solo cuando sea necesario)
def import_tabs():
    """Importa los módulos de tabs solo cuando sea necesario"""
    from ui.tabs import (
        show_cookies_tab,
        show_ecommerce_tab,
        show_acquisition_tab,
        show_events_tab,
        show_users_tab,
        show_sessions_tab,
        show_monitoring_tab
    )
    return {
        'cookies': show_cookies_tab,
        'ecommerce': show_ecommerce_tab,
        'acquisition': show_acquisition_tab,
        'events': show_events_tab,
        'users': show_users_tab,
        'sessions': show_sessions_tab,
        'monitoring': show_monitoring_tab
    }

# Configuración de página
st.set_page_config(
    page_title="BigQuery Shield - Vista Admin",
    layout="wide",
    page_icon="👨‍💼"
)

# CSS personalizado
st.markdown("""
    <style>
        /* Ocultar elementos de navegación */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        /* Estilo para el banner de admin */
        .admin-banner {
            background: linear-gradient(90deg, #6A1B9A 0%, #8E24AA 100%);
            color: white;
            padding: 20px 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
            border-left: 5px solid #FFD700;
        }

        .admin-banner h2 {
            margin: 0;
            font-size: 24px;
        }

        .admin-banner p {
            margin: 5px 0 0 0;
            font-size: 14px;
            opacity: 0.95;
        }

        .admin-badge {
            background-color: #FFD700;
            color: #6A1B9A;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
            margin-left: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Obtener token de query params
query_params = st.query_params
token = query_params.get('token', None)

# Si no hay token, mostrar error
if not token:
    st.error("🔒 Acceso Denegado")
    st.warning("⚠️ No se proporcionó un token de acceso válido")
    
    st.info("""
    **¿Cómo acceder?**
    
    Este enlace requiere un token de acceso válido proporcionado por FLAT 101.
    
    Si eres cliente y no tienes el enlace correcto, contacta con tu gestor de cuenta.
    """)
    
    st.divider()
    
    if st.button("🏠 Ir a Login Principal"):
        st.switch_page("main.py")
    
    st.stop()

# Validar token
access_data = AccessManager.validate_token(token)

if not access_data:
    st.error("🔒 Token Inválido o Expirado")
    st.warning("⚠️ El token de acceso no es válido o ha expirado")
    
    st.info("""
    **Posibles causas:**
    - El enlace ha expirado
    - El acceso ha sido revocado
    - El token es incorrecto
    
    Por favor, contacta con FLAT 101 para obtener un nuevo enlace de acceso.
    """)
    
    st.divider()
    
    if st.button("🏠 Ir a Login Principal"):
        st.switch_page("main.py")
    
    st.stop()

# Token válido - Configurar acceso
client_name = access_data['client_name']
project_id = access_data.get('project_id')
dataset_id = access_data.get('dataset_id')
allowed_tabs = access_data['allowed_tabs']
oauth_status = access_data.get('oauth_status', 'not_required')

# Verificar que el token OAuth esté completamente configurado
if oauth_status in ['pending', 'authorized']:
    st.warning("⚠️ Token pendiente de configuración")
    st.info("""
    **Token en proceso de configuración**

    Este token requiere autorización OAuth del cliente y configuración del administrador.

    **Estado actual:**
    """ + ("⏳ Esperando autorización del cliente" if oauth_status == 'pending' else "⏳ Esperando configuración del administrador"))

    st.markdown("""
    Por favor, contacta al administrador para completar la configuración.
    """)
    st.stop()

# Verificar que tengamos project_id y dataset_id
if not project_id or not dataset_id:
    st.error("❌ Error de Configuración")
    st.warning("Este token no tiene proyecto/dataset configurado.")
    st.info("Por favor, contacta al administrador.")
    st.stop()

# Banner de admin viendo datos del cliente
st.markdown(f"""
<div class="admin-banner">
    <h2>👨‍💼 Vista Admin <span class="admin-badge">ADMIN</span></h2>
    <p>📊 Visualizando datos de: <strong>{client_name}</strong></p>
    <p style="font-size: 12px; margin-top: 5px;">Dataset: {project_id}.{dataset_id}</p>
</div>
""", unsafe_allow_html=True)

# Advertencia clara de que es vista admin
st.warning("""
⚠️ **VISTA DE ADMINISTRADOR**

Estás viendo los datos del cliente usando sus credenciales OAuth autorizadas.
El cliente NO tiene acceso a esta herramienta.
""")

# Información de acceso en sidebar
with st.sidebar:
    st.success("✅ Modo Admin Activo")
    
    st.write("**Cliente:**")
    st.info(client_name)
    
    st.write("**Dataset:**")
    st.code(f"{project_id}.{dataset_id}")
    
    # Mostrar fecha de expiración
    expiration = datetime.fromisoformat(access_data['expiration_date'])
    days_left = (expiration - datetime.now()).days
    
    st.write("**Vigencia del Acceso:**")
    if days_left > 7:
        st.success(f"Expira en {days_left} días")
    elif days_left > 0:
        st.warning(f"⚠️ Expira en {days_left} días")
    else:
        st.error("🔴 Expirado")
    
    st.write(f"Fecha: {expiration.strftime('%d/%m/%Y')}")
    
    st.divider()
    
    # Selector de fechas
    st.subheader("📅 Rango de Fechas")
    
    from config.settings import Settings
    import pandas as pd
    
    start_date = st.date_input(
        "Desde:",
        value=Settings.DEFAULT_START_DATE,
        key="client_start_date"
    )
    
    end_date = st.date_input(
        "Hasta:",
        value=Settings.DEFAULT_END_DATE,
        key="client_end_date"
    )
    
    days_diff = (end_date - start_date).days
    if days_diff > 0:
        st.info(f"📊 {days_diff} días seleccionados")
    
    st.divider()
    
    # Info de contacto
    st.write("**Soporte:**")
    st.caption("FLAT 101 Digital Business")
    st.caption("📧 contacto@flat101.es")

# Crear cliente de BigQuery
try:
    # Verificar si el token tiene credenciales OAuth
    oauth_credentials_dict = access_data.get('oauth_credentials')

    if oauth_credentials_dict and oauth_status == 'configured':
        # Usar credenciales OAuth del cliente
        from auth import OAuthHandler
        from google.oauth2.credentials import Credentials

        # Convertir diccionario a Credentials
        credentials = OAuthHandler.dict_to_credentials(oauth_credentials_dict)

        # Refrescar si es necesario
        credentials = OAuthHandler.refresh_credentials(credentials)

        # Crear cliente con las credenciales del cliente
        client = bigquery.Client(
            credentials=credentials,
            project=project_id
        )

        # Mostrar info en sidebar de que se están usando credenciales OAuth
        with st.sidebar:
            st.success("🔐 Usando credenciales OAuth del cliente")

    else:
        # Usar service account desde secrets (flujo tradicional)
        creds_dict = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        client = bigquery.Client(
            credentials=credentials,
            project=project_id
        )

except Exception as e:
    st.error(f"❌ Error conectando a BigQuery: {str(e)}")
    st.info("Por favor, contacta con el administrador del sistema.")
    with st.expander("🔍 Ver detalles técnicos"):
        st.code(str(e))
    st.stop()

# Obtener funciones de tabs
tab_functions = import_tabs()

# Crear mapeo de nombres de tabs
tab_display_names = AccessManager.get_tab_display_names()

# Filtrar solo tabs permitidos
allowed_tab_titles = [tab_display_names[tab_id] for tab_id in allowed_tabs if tab_id in tab_display_names]
allowed_tab_ids = [tab_id for tab_id in allowed_tabs if tab_id in tab_display_names]

# Si no hay tabs permitidos, mostrar error
if not allowed_tab_ids:
    st.error("❌ No hay tabs permitidos para este acceso")
    st.info("Contacta con el administrador para revisar los permisos.")
    st.stop()

# Mostrar mensaje informativo sobre acceso restringido
with st.expander("ℹ️ Información sobre tu Acceso", expanded=False):
    st.write(f"""
    **Acceso configurado para:**
    - **Cliente:** {client_name}
    - **Proyecto:** {project_id}
    - **Dataset:** {dataset_id}
    
    **Análisis disponibles:**
    """)
    
    for tab_title in allowed_tab_titles:
        st.write(f"✅ {tab_title}")
    
    st.divider()
    
    st.caption("""
    **Nota:** Este acceso está limitado únicamente a los datos y análisis especificados.
    Para solicitar acceso a análisis adicionales, contacta con tu gestor de cuenta en FLAT 101.
    """)

# Crear tabs dinámicamente según permisos
tabs = st.tabs(allowed_tab_titles)

# Renderizar cada tab permitido
for tab, tab_id in zip(tabs, allowed_tab_ids):
    with tab:
        try:
            # Llamar a la función correspondiente del tab
            tab_function = tab_functions[tab_id]
            tab_function(
                client=client,
                project=project_id,
                dataset=dataset_id,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            st.error(f"❌ Error cargando el análisis: {str(e)}")
            st.info("Si el problema persiste, contacta con soporte técnico.")

# Footer profesional
st.divider()

footer_col1, footer_col2, footer_col3 = st.columns([2, 2, 1])

with footer_col1:
    st.caption(f"© 2025 FLAT 101 Digital Business | Acceso para {client_name}")

with footer_col2:
    st.caption(f"📊 Dataset: {dataset_id}")

with footer_col3:
    st.caption("v1.0.0")

# Nota de seguridad al final
st.caption("""
🔒 **Nota de Seguridad:** Este enlace es personal e intransferible. 
No compartas este enlace con terceros. Todos los accesos quedan registrados.
""")
