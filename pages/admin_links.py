"""
Página de Administración de Enlaces para Clientes
Permite a los administradores crear y gestionar accesos restringidos
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.access_manager import AccessManager

# Configuración de página
st.set_page_config(
    page_title="Admin - Enlaces de Clientes",
    layout="wide",
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
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🔐 Gestión de Enlaces para Clientes")
st.markdown("**Panel de administración** - Crea y gestiona accesos restringidos a BigQuery Shield")

# Verificar autenticación de admin
if not AccessManager.is_admin():
    st.warning("🔒 Acceso Restringido - Requiere autenticación de administrador")
        
    with st.form("admin_login"):
        password = st.text_input("Contraseña de Administrador:", type="password")
        submit = st.form_submit_button("Acceder")
        
        if submit:
            if AccessManager.set_admin_session(password):
                st.success("✅ Acceso concedido")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    
    st.divider()
    st.info("""
    **💡 Información:**
    - Esta página permite crear enlaces de acceso restringido para clientes
    - Cada cliente tendrá acceso SOLO a su proyecto/dataset específico
    - Puedes limitar qué tabs pueden ver
    - Los enlaces expiran automáticamente
    """)
    
    # Botón para volver
    if st.button("🏠 Volver a Login Principal"):
        st.switch_page("ui/login_screen.py")
    
    st.stop()

# Usuario autenticado como admin
st.success(f"✅ Sesión de administrador activa")

# Botones de acción principales
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🏠 Ir a App Principal", use_container_width=True):
        st.switch_page("main.py")

with col2:
    if st.button("🔄 Refrescar Datos", use_container_width=True):
        st.rerun()

with col3:
    if st.button("📥 Exportar Tokens", use_container_width=True):
        json_data = AccessManager.export_tokens_to_json()
        st.download_button(
            label="Descargar JSON",
            data=json_data,
            file_name=f"tokens_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

with col4:
    if st.button("🚪 Cerrar Sesión Admin", use_container_width=True):
        st.session_state['is_admin'] = False
        st.rerun()

st.divider()

# Estadísticas generales
st.subheader("📊 Estadísticas Generales")

stats = AccessManager.get_token_stats()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Enlaces", stats['total_tokens'])
with col2:
    st.metric("Enlaces Activos", stats['active_tokens'])
with col3:
    st.metric("Expirados", stats['expired_tokens'])
with col4:
    st.metric("Revocados", stats['revoked_tokens'])
with col5:
    st.metric("Total Accesos", stats['total_accesses'])

st.divider()

# Tabs principales
tab1, tab2, tab3 = st.tabs([
    "➕ Crear Nuevo Enlace",
    "📋 Enlaces Existentes",
    "⚙️ Configuración"
])

# ==========================================
# TAB 1: CREAR NUEVO ENLACE
# ==========================================
with tab1:
    st.subheader("➕ Crear Nuevo Enlace de Acceso")
    
    with st.form("create_access_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            client_name = st.text_input(
                "Nombre del Cliente *",
                placeholder="Ej: Empresa XYZ",
                help="Nombre identificativo del cliente"
            )
            
            project_id = st.text_input(
                "Project ID de BigQuery *",
                placeholder="Ej: mi-proyecto-analytics",
                help="ID del proyecto BigQuery al que tendrá acceso"
            )
            
            dataset_id = st.text_input(
                "Dataset ID *",
                placeholder="Ej: analytics_123456789",
                help="ID del dataset GA4 específico"
            )
        
        with col2:
            expiration_days = st.number_input(
                "Días de Vigencia *",
                min_value=1,
                max_value=365,
                value=30,
                help="Días hasta que expire el enlace"
            )
            
            # Selector de tabs permitidos
            tab_options = AccessManager.get_tab_display_names()
            
            allowed_tabs = st.multiselect(
                "Tabs Permitidos *",
                options=list(tab_options.keys()),
                format_func=lambda x: tab_options[x],
                default=['ecommerce', 'acquisition'],
                help="Selecciona los análisis que puede ver el cliente"
            )
            
            notes = st.text_area(
                "Notas (Opcional)",
                placeholder="Información adicional sobre este acceso...",
                height=100
            )
        
        # Botón de crear
        submitted = st.form_submit_button("🔗 Crear Enlace de Acceso", use_container_width=True)
        
        if submitted:
            # Validaciones
            if not client_name or not project_id or not dataset_id:
                st.error("❌ Por favor completa todos los campos obligatorios (*)")
            elif not allowed_tabs:
                st.error("❌ Debes seleccionar al menos un tab permitido")
            else:
                # Crear acceso
                try:
                    access_data = AccessManager.create_client_access(
                        client_name=client_name,
                        project_id=project_id,
                        dataset_id=dataset_id,
                        allowed_tabs=allowed_tabs,
                        expiration_days=expiration_days,
                        notes=notes
                    )
                    
                    st.success("✅ ¡Enlace creado exitosamente!")
                    
                    # Mostrar el enlace generado
                    access_url = AccessManager.get_access_url(access_data['token'])
                    
                    st.markdown("### 🔗 Enlace de Acceso Generado:")
                    st.code(access_url, language=None)
                    
                    # Información del acceso
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"**Cliente:** {client_name}")
                    with col2:
                        st.info(f"**Proyecto:** {project_id}")
                    with col3:
                        expiration = datetime.fromisoformat(access_data['expiration_date'])
                        st.info(f"**Expira:** {expiration.strftime('%d/%m/%Y')}")
                    
                    # Botón para copiar
                    st.markdown(f"""
                    <a href="{access_url}" target="_blank">
                        <button style="
                            background-color:#4CAF50;
                            color:white;
                            padding:12px 24px;
                            border:none;
                            border-radius:8px;
                            cursor:pointer;
                            font-size:16px;
                            width:100%;
                            margin-top:10px;
                        ">
                            🚀 Abrir Enlace en Nueva Pestaña
                        </button>
                    </a>
                    """, unsafe_allow_html=True)
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error creando el acceso: {str(e)}")

# ==========================================
# TAB 2: ENLACES EXISTENTES
# ==========================================
with tab2:
    st.subheader("📋 Gestión de Enlaces Existentes")
    
    # Obtener todos los tokens
    tokens = AccessManager.get_all_tokens()
    
    if not tokens:
        st.info("ℹ️ No hay enlaces creados aún. Crea uno en la pestaña anterior.")
    else:
        # Convertir a DataFrame para mejor visualización
        tokens_list = []
        
        for token, data in tokens.items():
            expiration = datetime.fromisoformat(data['expiration_date'])
            created = datetime.fromisoformat(data['created_at'])
            
            # Determinar estado
            if not data.get('active', False):
                status = "🔴 Revocado"
            elif datetime.now() > expiration:
                status = "⏰ Expirado"
            else:
                days_left = (expiration - datetime.now()).days
                status = f"✅ Activo ({days_left}d)"
            
            tokens_list.append({
                'Cliente': data['client_name'],
                'Proyecto': data['project_id'],
                'Dataset': data['dataset_id'],
                'Estado': status,
                'Creado': created.strftime('%d/%m/%Y'),
                'Expira': expiration.strftime('%d/%m/%Y'),
                'Accesos': data.get('access_count', 0),
                'Token': token
            })
        
        df_tokens = pd.DataFrame(tokens_list)
        
        # Mostrar tabla
        st.dataframe(
            df_tokens[['Cliente', 'Proyecto', 'Dataset', 'Estado', 'Creado', 'Expira', 'Accesos']],
            use_container_width=True,
            height=400
        )
        
        st.divider()
        
        # Selector de token para acciones
        st.subheader("⚙️ Acciones sobre Enlaces")
        
        # Crear opciones para el selector
        token_options = {
            f"{data['client_name']} - {data['project_id']} ({token[:8]}...)": token
            for token, data in tokens.items()
        }
        
        selected_display = st.selectbox(
            "Seleccionar enlace:",
            options=list(token_options.keys())
        )
        
        if selected_display:
            selected_token = token_options[selected_display]
            token_data = tokens[selected_token]
            
            # Mostrar detalles del token seleccionado
            with st.expander("ℹ️ Detalles del Enlace", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Información General:**")
                    st.write(f"- Cliente: {token_data['client_name']}")
                    st.write(f"- Proyecto: {token_data['project_id']}")
                    st.write(f"- Dataset: {token_data['dataset_id']}")
                    st.write(f"- Activo: {'✅ Sí' if token_data.get('active') else '❌ No'}")
                
                with col2:
                    st.write("**Estadísticas:**")
                    st.write(f"- Accesos: {token_data.get('access_count', 0)}")
                    
                    last_access = token_data.get('last_access')
                    if last_access:
                        last_access_dt = datetime.fromisoformat(last_access)
                        st.write(f"- Último acceso: {last_access_dt.strftime('%d/%m/%Y %H:%M')}")
                    else:
                        st.write("- Último acceso: Nunca")
                    
                    expiration = datetime.fromisoformat(token_data['expiration_date'])
                    days_left = (expiration - datetime.now()).days
                    st.write(f"- Días restantes: {days_left}")
                
                # Tabs permitidos
                st.write("**Tabs Permitidos:**")
                tab_names = AccessManager.get_tab_display_names()
                tabs_display = ", ".join([tab_names.get(tab, tab) for tab in token_data['allowed_tabs']])
                st.write(tabs_display)
                
                # Notas
                if token_data.get('notes'):
                    st.write("**Notas:**")
                    st.info(token_data['notes'])
                
                # URL del enlace
                st.write("**Enlace de Acceso:**")
                access_url = AccessManager.get_access_url(selected_token)
                st.code(access_url, language=None)
            
            # Acciones
            st.subheader("🔧 Acciones Disponibles")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("➕ Extender 30 días", use_container_width=True):
                    if AccessManager.extend_expiration(selected_token, 30):
                        st.success("✅ Expiración extendida 30 días")
                        st.rerun()
                    else:
                        st.error("❌ Error extendiendo expiración")
            
            with col2:
                if token_data.get('active', False):
                    if st.button("🚫 Revocar Acceso", use_container_width=True):
                        if AccessManager.revoke_token(selected_token):
                            st.warning("⚠️ Acceso revocado")
                            st.rerun()
                        else:
                            st.error("❌ Error revocando acceso")
                else:
                    st.button("✅ Reactivar", use_container_width=True, disabled=True)
            
            with col3:
                if st.button("🗑️ Eliminar", use_container_width=True):
                    if AccessManager.delete_token(selected_token):
                        st.success("✅ Enlace eliminado")
                        st.rerun()
                    else:
                        st.error("❌ Error eliminando enlace")
            
            with col4:
                if st.button("📋 Copiar URL", use_container_width=True):
                    st.info("💡 Usa el botón derecho > Copiar en el cuadro de código arriba")

# ==========================================
# TAB 3: CONFIGURACIÓN
# ==========================================
with tab3:
    st.subheader("⚙️ Configuración del Sistema")
    
    st.write("### 🔗 URL Base de la Aplicación")
    
    try:
        current_url = st.secrets.get("app_url", "No configurada")
    except:
        current_url = "No configurada"
    
    st.info(f"**URL actual:** {current_url}")
    
    st.markdown("""
    Para configurar la URL base, añade esto a tus **Secrets de Streamlit**:
    
    ```toml
    app_url = "https://tu-app.streamlit.app"
    ```
    """)
    
    st.divider()
    
    st.write("### 🔐 Contraseña de Administrador")
    
    try:
        has_password = "admin_password" in st.secrets
    except:
        has_password = False
    
    if has_password:
        st.success("✅ Contraseña personalizada configurada")
    else:
        st.warning("⚠️ Usando contraseña por defecto (admin123)")
    
    st.markdown("""
    Para configurar una contraseña personalizada, añade esto a tus **Secrets**:
    
    ```toml
    admin_password = "tu_password_seguro"
    ```
    """)
    
    st.divider()
    
    st.write("### 💾 Backup y Restauración")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Exportar Tokens:**")
        json_data = AccessManager.export_tokens_to_json()
        st.download_button(
            label="📥 Descargar Backup JSON",
            data=json_data,
            file_name=f"tokens_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        st.write("**Importar Tokens:**")
        uploaded_file = st.file_uploader(
            "Subir archivo JSON de backup",
            type=['json'],
            key="import_tokens"
        )
        
        if uploaded_file is not None:
            if st.button("📤 Importar Tokens", use_container_width=True):
                try:
                    json_str = uploaded_file.read().decode('utf-8')
                    if AccessManager.import_tokens_from_json(json_str):
                        st.success("✅ Tokens importados correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error importando tokens")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    
    st.write("### 📋 Tabs Disponibles")
    
    tab_names = AccessManager.get_tab_display_names()
    
    for tab_id, tab_name in tab_names.items():
        st.write(f"- `{tab_id}`: {tab_name}")

# Footer
st.divider()
st.caption("🔐 Panel de Administración - BigQuery Shield | FLAT 101 Digital Business")
