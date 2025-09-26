import streamlit as st
import sys
import os

# Debug: mostrar estructura de archivos
st.title("🔧 Debug - Estructura de Módulos")

# Verificar qué hay en utils/
st.subheader("📁 Contenido de utils/")
if os.path.exists("utils"):
    st.write("Archivos en utils/:")
    for file in os.listdir("utils"):
        st.write(f"- {file}")
        
        # Mostrar contenido de __init__.py
        if file == "__init__.py":
            st.code("Contenido de utils/__init__.py:")
            with open(os.path.join("utils", file), "r") as f:
                st.code(f.read())
else:
    st.error("❌ No existe la carpeta utils/")

# Intentar imports paso a paso
st.subheader("🔄 Probando imports...")

try:
    st.write("1. Intentando importar desde utils.error_handling...")
    from utils.error_handling import check_dependencies, handle_bq_error
    st.success("✅ utils.error_handling importado correctamente")
except ImportError as e:
    st.error(f"❌ Error importando error_handling: {e}")

try:
    st.write("2. Intentando importar desde utils.helpers...")
    from utils.helpers import setup_environment
    st.success("✅ utils.helpers importado correctamente")
except ImportError as e:
    st.error(f"❌ Error importando helpers: {e}")

try:
    st.write("3. Intentando importar mediante utils/__init__.py...")
    from utils import check_dependencies, setup_environment
    st.success("✅ Import via __init__.py exitoso")
    
    # Probar las funciones
    st.write("4. Probando funciones...")
    setup_environment()
    check_dependencies()
    st.success("✅ Todas las funciones funcionan correctamente")
    
except ImportError as e:
    st.error(f"❌ Error en import via __init__.py: {e}")

# Mostrar árbol de archivos completo
st.subheader("🌳 Árbol completo de archivos")
for root, dirs, files in os.walk("."):
    # Ignorar carpetas ocultas
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    files = [f for f in files if not f.startswith('.') and f.endswith('.py')]
    
    level = root.replace(".", "").count(os.sep)
    indent = " " * 2 * level
    st.text(f"{indent}{os.path.basename(root)}/")
    subindent = " " * 2 * (level + 1)
    for file in files:
        st.text(f"{subindent}{file}")

st.stop()
