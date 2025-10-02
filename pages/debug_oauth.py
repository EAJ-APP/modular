# pages/debug_oauth.py
import streamlit as st
import requests
from typing import Dict

st.set_page_config(page_title="Debug OAuth", layout="wide", page_icon="🔬")

st.title("🔬 Debug Completo de OAuth")
st.caption("Usa esta página para diagnosticar problemas con Google OAuth")

st.divider()

# ====================
# TEST 1: SECRETS
# ====================
st.header("1️⃣ Verificación de Secrets")

col1, col2 = st.columns(2)

with col1:
    st.subheader("OAuth Config")
    try:
        client_id = st.secrets["oauth"]["client_id"]
        client_secret = st.secrets["oauth"]["client_secret"]
        redirect_uri = st.secrets["oauth"]["redirect_uri"]
        
        # Verificar Client ID
        if client_id.endswith('.apps.googleusercontent.com'):
            st.success("✅ Client ID formato correcto")
        else:
            st.error("❌ Client ID formato incorrecto")
        
        st.code(f"Client ID: {client_id[:30]}...")
        
        # Verificar Client Secret
        if client_secret.startswith('GOCSPX-'):
            st.success("✅ Client Secret formato correcto")
        else:
            st.warning("⚠️ Client Secret formato no estándar")
        
        st.code(f"Client Secret: {client_secret[:15]}...")
        
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
        st.code("""
# Añade esto a tus Secrets en Streamlit Cloud:

[oauth]
client_id = "TU_CLIENT_ID.apps.googleusercontent.com"
client_secret = "GOCSPX-xxxxxxxxxxxxx"
redirect_uri = "https://tu-app.streamlit.app"
        """)
    except Exception as e:
        st.error(f"❌ Error: {e}")

with col2:
    st.subheader("Service Account")
    try:
        if "gcp_service_account" in st.secrets:
            st.success("✅ Service Account configurado")
            sa_email = st.secrets["gcp_service_account"]["client_email"]
            st.code(f"Email: {sa_email}")
        else:
            st.warning("⚠️ Service Account no configurado")
    except Exception as e:
        st.error(f"Error: {e}")

st.divider()

# ====================
# TEST 2: SCOPES
# ====================
st.header("2️⃣ Scopes de BigQuery")

try:
    from auth import AuthConfig
    
    st.write("**Scopes configurados actualmente:**")
    for i, scope in enumerate(AuthConfig.SCOPES, 1):
        if 'bigquery' in scope:
            st.code(f"{i}. {scope} 🔐 (Requiere permisos especiales)")
        else:
            st.code(f"{i}. {scope} ✅ (Básico)")
    
    st.info("""
    💡 **Nota sobre scopes de BigQuery:**
    - Si obtienes error 403, puede ser porque BigQuery requiere verificación
    - Solución temporal: Usa solo `bigquery.readonly`
    - Solución definitiva: Añade tu email como "Test User" en Google Cloud
    """)
    
except ImportError as e:
    st.error(f"No se pudo importar AuthConfig: {e}")

st.divider()

# ====================
# TEST 3: GOOGLE CLOUD CONFIG
# ====================
st.header("3️⃣ Configuración en Google Cloud Console")

st.warning("""
⚠️ **IMPORTANTE**: Verifica MANUALMENTE en Google Cloud Console
""")

try:
    redirect_uri = st.secrets["oauth"]["redirect_uri"]
    
    st.markdown(f"""
    ### ✅ Checklist de Google Cloud Console:
    
    1. **Ve a**: [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)
    
    2. **Verifica "Publishing status":**
       - ¿Está en **Testing** o **In Production**?
       - Si está en Testing → necesitas añadir Test Users
    
    3. **Si está en Testing, añade Test Users:**
       - Scroll hasta **"Test users"**
       - Click **"+ ADD USERS"**
       - Añade **tu email de Google** (el que usarás para login)
       - Click **SAVE**
       - **Espera 5 minutos** antes de volver a intentar
    
    4. **Ve a**: [Credentials](https://console.cloud.google.com/apis/credentials)
    
    5. **Click en tu OAuth 2.0 Client ID**
    
    6. **Verifica "Authorized redirect URIs":**
       - Debe incluir **EXACTAMENTE**: `{redirect_uri}`
       - Sin `/` al final
       - Sin rutas adicionales
    
    7. **Si hiciste cambios:**
       - Click **SAVE**
       - **Espera 5 minutos** (Google necesita propagar cambios)
    """)
    
except Exception as e:
    st.error(f"Error: {e}")

st.divider()

# ====================
# TEST 4: GENERAR URL DE PRUEBA
# ====================
st.header("4️⃣ Generar URL de Autorización")

st.info("""
👉 Este test generará la URL de autorización SIN hacer redirect.
Podrás copiar la URL y probarla manualmente para ver el error exacto.
""")

if st.button("🧪 Generar URL de Autorización", type="primary"):
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
            
            st.markdown("### 📋 Pasos para probar manualmente:")
            st.markdown("""
            1. **Copia la URL de arriba**
            2. **Ábrela en una nueva pestaña** (navegación privada/incógnito recomendado)
            3. **Observa qué error aparece**:
               - **403**: Problema con Test Users o Consent Screen
               - **400**: Problema con Redirect URI o Client ID
               - **Página de Google pidiendo permisos**: ¡Funciona! (acepta y verás el redirect)
            4. **Toma captura** del error si aparece
            """)
            
            # Botón para abrir en nueva pestaña
            st.markdown(f'<a href="{auth_url}" target="_blank"><button style="background-color:#4CAF50;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;">🚀 Abrir en nueva pestaña</button></a>', unsafe_allow_html=True)
            
            # Desglose de la URL
            with st.expander("🔍 Desglose de la URL"):
                st.write("**Parámetros de la URL:**")
                
                if '?' in auth_url:
                    base_url, params = auth_url.split('?', 1)
                    st.code(f"Base: {base_url}")
                    
                    for param in params.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            st.code(f"{key} = {value[:50]}...")
    
    except Exception as e:
        st.error(f"❌ Error generando URL: {e}")
        
        with st.expander("🔍 Stack trace completo"):
            import traceback
            st.code(traceback.format_exc())

st.divider()

# ====================
# TEST 5: PROJECT INFO
# ====================
st.header("5️⃣ Información del Proyecto")

try:
    client_id = st.secrets["oauth"]["client_id"]
    project_number = client_id.split('-')[0]
    
    st.write("**Project Number (del Client ID):**")
    st.code(project_number)
    
    st.info("""
    💡 Este número debe coincidir con tu proyecto `ai-nibw` en Google Cloud.
    
    Para verificar:
    1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
    2. Selecciona tu proyecto `ai-nibw`
    3. El número aparece en el dashboard principal
    """)
    
except Exception as e:
    st.error(f"Error: {e}")

st.divider()

# ====================
# TEST 6: CONNECTIVITY
# ====================
st.header("6️⃣ Test de Conectividad")

if st.button("🌐 Test de Conexión a Google APIs"):
    with st.spinner("Probando conexión..."):
        try:
            # Test 1: OAuth2 discovery
            response = requests.get(
                "https://www.googleapis.com/discovery/v1/apis/oauth2/v2/rest",
                timeout=5
            )
            
            if response.status_code == 200:
                st.success("✅ Acceso a Google OAuth2 API: OK")
            else:
                st.error(f"❌ Error {response.status_code}")
            
            # Test 2: BigQuery API
            response = requests.get(
                "https://www.googleapis.com/discovery/v1/apis/bigquery/v2/rest",
                timeout=5
            )
            
            if response.status_code == 200:
                st.success("✅ Acceso a BigQuery API: OK")
            else:
                st.error(f"❌ Error {response.status_code}")
            
        except requests.exceptions.Timeout:
            st.error("❌ Timeout conectando a Google APIs")
        except Exception as e:
            st.error(f"❌ Error: {e}")

st.divider()

# ====================
# GUÍA DE SOLUCIÓN
# ====================
st.header("📚 Guía de Solución de Errores")

error_type = st.selectbox(
    "¿Qué error estás viendo?",
    [
        "Selecciona un error...",
        "403 - That's an error. We're sorry, but you do not have access",
        "400 - Bad Request / Formato incorrecto",
        "redirect_uri_mismatch",
        "invalid_client",
        "access_denied",
        "Otro error"
    ]
)

if error_type == "403 - That's an error. We're sorry, but you do not have access":
    st.error("### 🔴 Error 403: Acceso Denegado")
    st.markdown("""
    **Causa más común**: OAuth Consent Screen en modo "Testing" y tu email no está en Test Users.
    
    **Solución**:
    1. Ve a [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)
    2. Si "Publishing status" = **Testing**:
       - Scroll hasta **"Test users"**
       - Click **"+ ADD USERS"**
       - Añade tu email de Google
       - Click **SAVE**
       - **Espera 5 minutos**
    3. Vuelve a intentar
    
    **Solución alternativa**:
    - Click en **"PUBLISH APP"** para hacerla pública
    - Confirma (no requiere verificación para uso interno)
    """)

elif error_type == "400 - Bad Request / Formato incorrecto":
    st.error("### 🔴 Error 400: Bad Request")
    st.markdown("""
    **Causa más común**: Redirect URI no coincide.
    
    **Solución**:
    1. Copia el `redirect_uri` de tus Secrets (arriba en este debug)
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
    
    **Solución**:
    1. En Google Cloud → Credentials → OAuth 2.0 Client ID
    2. Añade EXACTAMENTE: (ver arriba en Test 1)
    3. Sin `/` al final
    4. SAVE y espera 5 minutos
    """)

elif error_type == "invalid_client":
    st.error("### 🔴 Error: invalid_client")
    st.markdown("""
    **Causa**: Client ID o Client Secret incorrectos.
    
    **Solución**:
    1. Ve a [Credentials](https://console.cloud.google.com/apis/credentials)
    2. Verifica tu OAuth 2.0 Client ID
    3. Si es necesario, crea uno nuevo
    4. Actualiza los Secrets en Streamlit Cloud
    """)

elif error_type == "access_denied":
    st.error("### 🔴 Error: access_denied")
    st.markdown("""
    **Causa**: El usuario canceló o Google denegó el acceso.
    
    **Solución**:
    - Si tú cancelaste: Vuelve a intentar y acepta los permisos
    - Si Google denegó: Verifica Test Users (ver error 403)
    """)

st.divider()

st.success("""
### ✅ Una vez que corrijas el error:

1. Espera 5 minutos después de cualquier cambio en Google Cloud
2. Vuelve a la página principal
3. Intenta el login con Google de nuevo
4. Si persiste, vuelve a este debug y genera la URL de nuevo
""")
