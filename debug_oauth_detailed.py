import streamlit as st
import requests

st.title("🔬 Debug Detallado OAuth")

st.subheader("Test 1: Verificar Client ID")

try:
    client_id = st.secrets["oauth"]["client_id"]
    
    # Verificar formato del Client ID
    if client_id.endswith('.apps.googleusercontent.com'):
        st.success(f"✅ Client ID tiene formato correcto")
        st.code(client_id[:50] + "...")
    else:
        st.error("❌ Client ID no tiene formato correcto")
        st.write("Debería terminar en .apps.googleusercontent.com")
    
except Exception as e:
    st.error(f"Error leyendo client_id: {e}")

st.divider()

st.subheader("Test 2: Verificar Client Secret")

try:
    client_secret = st.secrets["oauth"]["client_secret"]
    
    if client_secret.startswith('GOCSPX-'):
        st.success("✅ Client Secret tiene formato correcto")
    else:
        st.warning("⚠️ Client Secret no empieza con GOCSPX-")
        st.info("Esto puede ser normal si es una versión antigua")
    
except Exception as e:
    st.error(f"Error leyendo client_secret: {e}")

st.divider()

st.subheader("Test 3: Verificar Project ID")

try:
    # Intentar obtener el project ID desde el client ID
    client_id = st.secrets["oauth"]["client_id"]
    project_number = client_id.split('-')[0]
    
    st.write("**Project Number (del Client ID):**", project_number)
    st.info("Este número debe coincidir con tu proyecto en Google Cloud")
    
except Exception as e:
    st.error(f"Error extrayendo project number: {e}")

st.divider()

st.subheader("Test 4: Probar acceso a Google API")

if st.button("🧪 Test API"):
    try:
        # Intentar acceder a la API de discovery
        response = requests.get(
            "https://www.googleapis.com/discovery/v1/apis/oauth2/v2/rest"
        )
        
        if response.status_code == 200:
            st.success("✅ Acceso a Google API funcionando")
        else:
            st.error(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error: {e}")
