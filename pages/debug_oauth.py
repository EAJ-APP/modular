# pages/debug_oauth.py
import streamlit as st
import requests
from typing import Dict

st.set_page_config(page_title="Debug OAuth - BigQuery Shield", layout="wide", page_icon="🔬")

# CSS para ocultar el sidebar y menú
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
    </style>
""", unsafe_allow_html=True)

# Header profesional
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🔬 Diagnóstico de Autenticación OAuth")
    st.caption("Herramienta de diagnóstico para resolver problemas de autenticación con Google Cloud")
with col2:
    # Botón con enlace directo a la raíz
    st.markdown("""
    <a href="/" target="_self">
        <button style="
            background-color:#1976D2;
            color:white;
            padding:8px 16px;
            border:none;
            border-radius:4px;
            cursor:pointer;
            font-size:14px;
            width:100%;
        ">
            🏠 Volver al Login
        </button>
    </a>
    """, unsafe_allow_html=True)

st.divider()

# Tabs organizados por categoría
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Verificación de Configuración",
    "🧪 Test de Conectividad",
    "🔍 Información del Proyecto",
    "📚 Guía de Solución"
])

# ====================
# TAB 1: VERIFICACIÓN DE CONFIGURACIÓN
# ====================
with tab1:
    st.header("Verificación de Secrets y Configuración")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔐 OAuth Configuration")
        try:
            client_id = st.secrets["oauth"]["client_id"]
            client_secret = st.secrets["oauth"]["client_secret"]
            redirect_uri = st.secrets["oauth"]["redirect_uri"]
            
            # Verificar Client ID
            if client_id.endswith('.apps.googleusercontent.com'):
                st.success("✅ Client ID - Formato correcto")
            else:
                st.error("❌ Client ID - Formato incorrecto")
            
            with st.expander("Ver detalles del Client ID"):
                st.code(f"{client_id[:50]}...")
            
            # Verificar Client Secret
            if client_secret.startswith('GOCSPX-'):
                st.success("✅ Client Secret - Formato correcto")
            else:
                st.warning("⚠️ Client Secret - Formato no estándar (puede ser válido)")
            
            with st.expander("Ver detalles del Client Secret"):
                st.code(f"{client_secret[:15]}...")
            
            # Verificar Redirect URI
            st.write("**Redirect URI configurado:**")
            st.code(redirect_uri)
            
            if redirect_uri.startswith('https://'):
                st.success("✅ Redirect URI usa HTTPS")
            else:
                st.error("❌ Redirect URI debe usar HTTPS en producción")
            
            if redirect_uri.endswith('/'):
                st.warning("⚠️ Redirect URI termina en / (puede causar problemas)")
                st.info(f"Prueba sin la barra: {redirect_uri[:-1]}")
            
        except KeyError as e:
            st.error(f"❌ Falta configuración: {e}")
            with st.expander("💡 ¿Cómo configurar?"):
                st.code("""
# Añade esto a tus Secrets en Streamlit Cloud:

[oauth]
client_id = "TU_CLIENT_ID.apps.googleusercontent.com"
client_secret = "GOCSPX-xxxxxxxxxxxxx"
redirect_uri = "https://modular-t4qqlkh4xr4wdblf4eyjjo.streamlit.app"
                """, language="toml")
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    with col2:
        st.subheader("🔑 Service Account")
        try:
            if "gcp_service_account" in st.secrets:
                st.success("✅ Service Account configurado")
                sa_email = st.secrets["gcp_service_account"]["client_email"]
                with st.expander("Ver detalles"):
                    st.code(f"Email: {sa_email}")
            else:
                st.info("ℹ️ Service Account no configurado (opcional para OAuth)")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.divider()
    
    # Scopes de BigQuery
    st.subheader("🔐 Scopes Configurados")
    
    try:
        from auth import AuthConfig
        
        st.write("**Permisos solicitados:**")
        for i, scope in enumerate(AuthConfig.SCOPES, 1):
            if 'bigquery' in scope:
                st.code(f"{i}. {scope} 🔐")
            else:
                st.code(f"{i}. {scope} ✅")
        
        st.info("""
        💡 **Nota sobre BigQuery:**
        - Si obtienes error 403, verifica los permisos en Google Cloud Console
        - Solución: Añade tu email como "Test User" en OAuth consent screen
        """)
        
    except ImportError:
        st.error("No se pudo importar AuthConfig")

# ====================
# TAB 2: TEST DE CONECTIVIDAD
# ====================
with tab2:
    st.header("Test de Conectividad con Google APIs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧪 Test OAuth2 API", use_container_width=True, type="primary"):
            with st.spinner("Probando conexión a OAuth2 API..."):
                try:
                    response = requests.get(
                        "https://www.googleapis.com/discovery/v1/apis/oauth2/v2/rest",
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ Conexión a OAuth2 API exitosa")
                        with st.expander("Ver respuesta"):
                            st.json(response.json())
                    else:
                        st.error(f"❌ Error {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    st.error("❌ Timeout conectando a Google APIs")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with col2:
        if st.button("🧪 Test BigQuery API", use_container_width=True, type="primary"):
            with st.spinner("Probando conexión a BigQuery API..."):
                try:
                    response = requests.get(
                        "https://www.googleapis.com/discovery/v1/apis/bigquery/v2/rest",
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ Conexión a BigQuery API exitosa")
                        with st.expander("Ver respuesta"):
                            st.json(response.json())
                    else:
                        st.error(f"❌ Error {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    st.error("❌ Timeout conectando a Google APIs")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    st.divider()
    
    # Generar URL de autorización
    st.subheader("🔗 Generar URL de Autorización")
    
    st.info("""
    👉 Esta herramienta genera la URL de autorización sin hacer redirect.
    Podrás copiar la URL y probarla manualmente para ver el error exacto.
    """)
    
    if st.button("🚀 Generar URL de Autorización", type="primary", use_container_width=True):
        try:
            from auth import OAuthHandler, AuthConfig
            
            oauth_config = AuthConfig.get_oauth_config()
            
            if not all(oauth_config.values()):
                st.error("❌ Configuración OAuth incompleta")
            else:
                oauth_handler = OAuthHandler(
                    client_id=oauth_config['client_id'],
                    client_secret=oauth_config['client_secret'],
                    redirect_uri=oauth_config['redirect_uri'],
                    scopes=AuthConfig.SCOPES
                )
                
                auth_url = oauth_handler.get_authorization_url()
                
                st.success("✅ URL generada correctamente")
                
                st.markdown("### 🔗 URL de Autorización:")
                st.code(auth_url, language=None)
                
                # Botón para copiar
                st.markdown(f"""
                <a href="{auth_url}" target="_blank">
                    <button style="background-color:#4CAF50;color:white;padding:12px 24px;border:none;border-radius:8px;cursor:pointer;font-size:16px;width:100%;">
                        🚀 Abrir en nueva pestaña
                    </button>
                </a>
                """, unsafe_allow_html=True)
                
                st.divider()
                
                st.markdown("### 📋 Pasos para probar manualmente:")
                st.markdown("""
                1. **Copia la URL de arriba** o haz click en el botón
                2. **Ábrela en una nueva pestaña** (navegación privada recomendada)
                3. **Observa qué error aparece**:
                   - **403**: Problema con Test Users o Consent Screen
                   - **400**: Problema con Redirect URI o Client ID
                   - **Página de Google pidiendo permisos**: ¡Funciona correctamente!
                4. **Toma captura** del error si aparece
                """)
                
                # Desglose de la URL
                with st.expander("🔍 Desglose de la URL"):
                    if '?' in auth_url:
                        base_url, params = auth_url.split('?', 1)
                        st.code(f"Base: {base_url}")
                        st.write("**Parámetros:**")
                        for param in params.split('&'):
                            if '=' in param:
                                key, value = param.split('=', 1)
                                st.code(f"{key} = {value[:50]}...")
        
        except Exception as e:
            st.error(f"❌ Error generando URL: {e}")
            
            with st.expander("🔍 Stack trace completo"):
                import traceback
                st.code(traceback.format_exc())

# ====================
# TAB 3: INFORMACIÓN DEL PROYECTO
# ====================
with tab3:
    st.header("Información del Proyecto Google Cloud")
    
    try:
        client_id = st.secrets["oauth"]["client_id"]
        project_number = client_id.split('-')[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Project Number", project_number)
            st.caption("Extraído del Client ID")
        
        with col2:
            st.info("""
            💡 Este número debe coincidir con tu proyecto en Google Cloud Console.
            
            **Para verificar:**
            1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
            2. Selecciona tu proyecto
            3. El número aparece en el dashboard
            """)
        
        st.divider()
        
        st.subheader("📋 Checklist de Google Cloud Console")
        
        st.markdown(f"""
        ### ✅ Verificaciones Necesarias:
        
        1. **OAuth consent screen** → [Ir](https://console.cloud.google.com/apis/credentials/consent)
           - ¿Publishing status es **Testing** o **In Production**?
           - Si es Testing → **Añade tu email** en Test Users
        
        2. **Credentials** → [Ir](https://console.cloud.google.com/apis/credentials)
           - Verifica que el Redirect URI sea **exactamente**: `{st.secrets["oauth"]["redirect_uri"]}`
           - Sin `/` al final
           - HTTPS obligatorio
        
        3. **Espera 5 minutos** después de cualquier cambio
        """)
        
    except Exception as e:
        st.error(f"Error obteniendo información: {e}")

# ====================
# TAB 4: GUÍA DE SOLUCIÓN
# ====================
with tab4:
    st.header("Guía de Solución de Problemas")
    
    error_type = st.selectbox(
        "¿Qué error estás viendo?",
        [
            "Selecciona un error...",
            "403 - Access Denied",
            "400 - Bad Request",
            "redirect_uri_mismatch",
            "invalid_client",
            "access_denied",
            "Otro error"
        ]
    )
    
    if error_type == "403 - Access Denied":
        st.error("### 🔴 Error 403: Acceso Denegado")
        st.markdown("""
        **Causa más común**: OAuth Consent Screen en modo "Testing" y tu email no está en Test Users.
        
        **Solución paso a paso:**
        1. Ve a [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)
        2. Si "Publishing status" = **Testing**:
           - Scroll hasta **"Test users"**
           - Click **"+ ADD USERS"**
           - Añade tu email de Google
           - Click **SAVE**
           - **Espera 5 minutos**
        3. Vuelve a intentar
        
        **Solución alternativa:**
        - Click en **"PUBLISH APP"** para hacerla pública
        - No requiere verificación para uso interno
        """)
    
    elif error_type == "400 - Bad Request":
        st.error("### 🔴 Error 400: Bad Request")
        st.markdown("""
        **Causa más común**: Redirect URI no coincide.
        
        **Solución:**
        1. Copia el `redirect_uri` de tus Secrets (Tab 1 de este debug)
        2. Ve a [Credentials](https://console.cloud.google.com/apis/credentials)
        3. Click en tu OAuth 2.0 Client ID
        4. En "Authorized redirect URIs", verifica que esté **EXACTAMENTE** igual
        5. Si no está, añádelo y click SAVE
        6. **Espera 5 minutos**
        """)
    
    elif error_type == "redirect_uri_mismatch":
        st.error("### 🔴 Error: redirect_uri_mismatch")
        st.markdown("""
        **Causa**: El redirect_uri de la solicitud no está autorizado.
        
        **Solución:**
        1. En Google Cloud → Credentials → OAuth 2.0 Client ID
        2. Añade EXACTAMENTE el redirect_uri de tu configuración
        3. Sin `/` al final
        4. SAVE y espera 5 minutos
        """)
    
    elif error_type == "invalid_client":
        st.error("### 🔴 Error: invalid_client")
        st.markdown("""
        **Causa**: Client ID o Client Secret incorrectos.
        
        **Solución:**
        1. Ve a [Credentials](https://console.cloud.google.com/apis/credentials)
        2. Verifica tu OAuth 2.0 Client ID
        3. Si es necesario, crea uno nuevo
        4. Actualiza los Secrets en Streamlit Cloud
        """)
    
    elif error_type == "access_denied":
        st.error("### 🔴 Error: access_denied")
        st.markdown("""
        **Causas posibles:**
        - El usuario canceló el proceso
        - Google denegó el acceso (verificar Test Users)
        
        **Solución:**
        - Si tú cancelaste: Vuelve a intentar y acepta los permisos
        - Si Google denegó: Verifica Test Users (ver error 403)
        """)
    
    elif error_type != "Selecciona un error...":
        st.info("Si tu error no está listado, contacta con soporte o revisa los logs completos.")
    
    st.divider()
    
    st.success("""
    ### ✅ Una vez que corrijas el error:
    
    1. **Espera 5 minutos** después de cualquier cambio en Google Cloud
    2. Vuelve a la página principal
    3. Intenta el login con Google de nuevo
    4. Si persiste, vuelve a este debug y genera la URL de nuevo
    """)

# Footer
st.divider()
st.caption("🔬 BigQuery Shield - Debug Tool v1.0 | FLAT 101 Digital Business")
