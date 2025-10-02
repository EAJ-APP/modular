# test_auth.py
import streamlit as st
from auth import SessionManager, AuthConfig
from google.cloud import bigquery

st.set_page_config(page_title="Test Auth", layout="wide")

st.title("🧪 Test de Autenticación BigQuery Shield")

st.divider()

# Test 1: Verificar configuración
st.header("1️⃣ Verificar Configuración")

col1, col2 = st.columns(2)

with col1:
    st.subheader("OAuth")
    oauth_configured = AuthConfig.is_oauth_configured()
    if oauth_configured:
        st.success("✅ OAuth configurado")
        try:
            config = AuthConfig.get_oauth_config()
            st.write("**Client ID:**", config['client_id'][:50] + "...")
            st.write("**Redirect URI:**", config['redirect_uri'])
        except Exception as e:
            st.error(f"Error obteniendo config: {e}")
    else:
        st.error("❌ OAuth NO configurado")

with col2:
    st.subheader("Service Account")
    secrets_configured = AuthConfig.is_secrets_configured()
    if secrets_configured:
        st.success("✅ Service Account configurado")
    else:
        st.error("❌ Service Account NO configurado")

st.divider()

# Test 2: Estado de sesión
st.header("2️⃣ Estado de Sesión")

SessionManager.initialize_session()

col1, col2, col3 = st.columns(3)

with col1:
    is_auth = SessionManager.is_authenticated()
    if is_auth:
        st.success("✅ Usuario autenticado")
    else:
        st.warning("⚠️ No autenticado")

with col2:
    method = SessionManager.get_auth_method()
    st.metric("Método", method if method else "Ninguno")

with col3:
    user_info = SessionManager.get_user_info()
    st.write("**Usuario:**", user_info.get('name', 'N/A'))

st.divider()

# Test 3: Cliente de BigQuery
st.header("3️⃣ Cliente de BigQuery")

client = SessionManager.get_bigquery_client()

if client:
    st.success("✅ Cliente de BigQuery disponible")
    
    try:
        with st.spinner("Listando proyectos..."):
            projects = list(client.list_projects())
            st.metric("Proyectos accesibles", len(projects))
            
            with st.expander("📋 Ver proyectos"):
                for project in projects[:10]:  # Mostrar solo los primeros 10
                    st.write(f"- **{project.project_id}**")
                if len(projects) > 10:
                    st.info(f"... y {len(projects) - 10} más")
    
    except Exception as e:
        st.error(f"❌ Error listando proyectos: {e}")
        with st.expander("🔍 Ver error completo"):
            import traceback
            st.code(traceback.format_exc())
else:
    st.warning("⚠️ No hay cliente de BigQuery disponible")
    st.info("👉 Autentica primero en la aplicación principal")

st.divider()

# Test 4: Query de prueba
st.header("4️⃣ Test de Query")

if client:
    if st.button("🧪 Ejecutar query de prueba"):
        try:
            with st.spinner("Ejecutando query..."):
                query = "SELECT 1 as test"
                result = client.query(query).result()
                st.success("✅ Query ejecutada correctamente")
                st.json({"resultado": "OK"})
        except Exception as e:
            st.error(f"❌ Error en query: {e}")

st.divider()

# Test 5: Acciones
st.header("5️⃣ Acciones")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refrescar", use_container_width=True):
        st.rerun()

with col2:
    if st.button("🧹 Limpiar Sesión", use_container_width=True):
        SessionManager.logout()
        st.success("Sesión limpiada")
        st.rerun()

with col3:
    if st.button("🏠 Ir a App Principal", use_container_width=True):
        st.switch_page("main.py")

st.divider()

# Debug: Session State completo
with st.expander("🔍 Debug - Session State Completo"):
    st.json(dict(st.session_state))
