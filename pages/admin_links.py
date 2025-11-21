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
    
    # DEBUG INFO - Añadido cerca de la línea 44
    with st.expander("🔍 Debug Info"):
        try:
            stored_password = st.secrets.get("admin_password", "admin123")
            st.write(f"Contraseña configurada: {stored_password[:3]}... (primeros 3 caracteres)")
            st.write(f"Longitud: {len(stored_password)} caracteres")
        except Exception as e:
            st.error(f"Error leyendo secret: {e}")
        
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
        st.switch_page("main.py")
    
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
        # Selector de tipo de enlace
        require_oauth = st.checkbox(
            "🔐 Requiere OAuth del Cliente",
            value=True,
            help="Si activas esto, el cliente deberá autorizar con su cuenta de Google antes de que puedas configurar el acceso"
        )

        if require_oauth:
            st.info("""
            **Flujo con OAuth:**
            1. Creas el token con el nombre del cliente
            2. Envías el enlace de OAuth al cliente
            3. El cliente autoriza con su cuenta de Google
            4. Tú configuras el proyecto/dataset después de la autorización
            5. Usas el enlace final para acceder a sus datos
            """)

        col1, col2 = st.columns(2)

        with col1:
            client_name = st.text_input(
                "Nombre del Cliente *",
                placeholder="Ej: Empresa XYZ",
                help="Nombre identificativo del cliente"
            )

            if not require_oauth:
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
            else:
                project_id = None
                dataset_id = None
                st.info("ℹ️ Configurarás el proyecto/dataset después de que el cliente autorice")

        with col2:
            expiration_days = st.number_input(
                "Días de Vigencia *",
                min_value=1,
                max_value=365,
                value=30,
                help="Días hasta que expire el enlace"
            )

            if not require_oauth:
                # Selector de tabs permitidos
                tab_options = AccessManager.get_tab_display_names()

                allowed_tabs = st.multiselect(
                    "Tabs Permitidos *",
                    options=list(tab_options.keys()),
                    format_func=lambda x: tab_options[x],
                    default=['ecommerce', 'acquisition'],
                    help="Selecciona los análisis que puede ver el cliente"
                )
            else:
                # Para OAuth, permitir todos los tabs por defecto (el admin puede cambiar después)
                allowed_tabs = list(AccessManager.get_tab_display_names().keys())
                st.info(f"ℹ️ Tabs permitidos por defecto: Todos ({len(allowed_tabs)})")

            notes = st.text_area(
                "Notas (Opcional)",
                placeholder="Información adicional sobre este acceso...",
                height=100
            )

        # Botón de crear
        submitted = st.form_submit_button("🔗 Crear Enlace de Acceso", use_container_width=True)

        if submitted:
            # Validaciones
            if not client_name:
                st.error("❌ Por favor ingresa el nombre del cliente")
            elif not require_oauth and (not project_id or not dataset_id):
                st.error("❌ Por favor completa todos los campos obligatorios (*)")
            elif not require_oauth and not allowed_tabs:
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
                        notes=notes,
                        require_oauth=require_oauth
                    )

                    st.success("✅ ¡Enlace creado exitosamente!")

                    if require_oauth:
                        # Mostrar enlace de OAuth
                        oauth_url = AccessManager.get_oauth_url(access_data['token'])

                        st.markdown("### 🔐 Enlace de Autorización OAuth:")
                        st.markdown("**Envía este enlace al cliente para que autorice el acceso:**")
                        st.code(oauth_url, language=None)

                        st.info(f"**Cliente:** {client_name}")
                        st.warning("⏳ **Estado:** Pendiente de autorización del cliente")

                        st.markdown("""
                        **Próximos pasos:**
                        1. 📧 Envía el enlace de arriba al cliente
                        2. ⏳ Espera a que el cliente autorice con su cuenta de Google
                        3. ✅ Cuando esté autorizado, podrás configurar el proyecto/dataset en la pestaña "Enlaces Existentes"
                        4. 🚀 Usa el enlace final para acceder a los datos del cliente
                        """)
                    else:
                        # Mostrar el enlace generado (flujo tradicional)
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

            # Determinar estado OAuth
            oauth_status = data.get('oauth_status', 'not_required')
            if oauth_status == 'pending':
                oauth_display = "⏳ Pendiente OAuth"
            elif oauth_status == 'authorized':
                oauth_display = "✅ OAuth OK"
            elif oauth_status == 'configured':
                oauth_display = "✅ Configurado"
            else:
                oauth_display = "➖ No requiere"

            tokens_list.append({
                'Cliente': data['client_name'],
                'Proyecto': data.get('project_id', 'N/A'),
                'Dataset': data.get('dataset_id', 'N/A'),
                'Estado': status,
                'OAuth': oauth_display,
                'Creado': created.strftime('%d/%m/%Y'),
                'Expira': expiration.strftime('%d/%m/%Y'),
                'Accesos': data.get('access_count', 0),
                'Token': token
            })
        
        df_tokens = pd.DataFrame(tokens_list)

        # Mostrar tabla
        st.dataframe(
            df_tokens[['Cliente', 'Proyecto', 'Dataset', 'Estado', 'OAuth', 'Creado', 'Expira', 'Accesos']],
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
            oauth_status = token_data.get('oauth_status', 'not_required')

            with st.expander("ℹ️ Detalles del Enlace", expanded=True):
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Información General:**")
                    st.write(f"- Cliente: {token_data['client_name']}")
                    st.write(f"- Proyecto: {token_data.get('project_id', 'N/A')}")
                    st.write(f"- Dataset: {token_data.get('dataset_id', 'N/A')}")
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

                # Estado OAuth
                st.write("**Estado OAuth:**")
                if oauth_status == 'pending':
                    st.warning("⏳ Pendiente de autorización del cliente")
                elif oauth_status == 'authorized':
                    st.success("✅ Cliente autorizó, falta configurar proyecto/dataset")
                    oauth_authorized_at = token_data.get('oauth_authorized_at')
                    if oauth_authorized_at:
                        auth_dt = datetime.fromisoformat(oauth_authorized_at)
                        st.write(f"- Autorizado el: {auth_dt.strftime('%d/%m/%Y %H:%M')}")
                elif oauth_status == 'configured':
                    st.success("✅ Completamente configurado")
                    oauth_authorized_at = token_data.get('oauth_authorized_at')
                    if oauth_authorized_at:
                        auth_dt = datetime.fromisoformat(oauth_authorized_at)
                        st.write(f"- Autorizado el: {auth_dt.strftime('%d/%m/%Y %H:%M')}")
                else:
                    st.info("➖ No requiere OAuth")

                # Tabs permitidos
                if token_data.get('allowed_tabs'):
                    st.write("**Tabs Permitidos:**")
                    tab_names = AccessManager.get_tab_display_names()
                    tabs_display = ", ".join([tab_names.get(tab, tab) for tab in token_data['allowed_tabs']])
                    st.write(tabs_display)

                # Notas
                if token_data.get('notes'):
                    st.write("**Notas:**")
                    st.info(token_data['notes'])

                # URLs según el estado
                if oauth_status == 'pending':
                    st.write("**🔐 Enlace de OAuth (enviar al cliente):**")
                    oauth_url = AccessManager.get_oauth_url(selected_token)
                    st.code(oauth_url, language=None)
                    st.caption("Envía este enlace al cliente para que autorice el acceso")
                elif oauth_status == 'configured' or oauth_status == 'not_required':
                    st.write("**🔗 Enlace de Acceso (para usar tú):**")
                    access_url = AccessManager.get_access_url(selected_token)
                    st.code(access_url, language=None)
                    st.caption("Usa este enlace para acceder a los datos del cliente")

            # Formulario de configuración para tokens autorizados
            if oauth_status == 'authorized':
                st.divider()
                st.subheader("⚙️ Configurar Proyecto y Dataset")
                st.info("✅ El cliente ya autorizó. Ahora selecciona el proyecto y dataset de GA4:")

                # Obtener proyectos y datasets disponibles
                with st.spinner("🔍 Cargando proyectos y datasets del cliente..."):
                    ga4_projects = AccessManager.get_ga4_projects_and_datasets(selected_token)

                if not ga4_projects:
                    st.warning("⚠️ No se encontraron proyectos con datasets de GA4")
                    st.markdown("""
                    **Posibles causas:**
                    - El cliente no tiene proyectos con GA4 en su cuenta
                    - El cliente no otorgó los permisos necesarios
                    - Los datasets no siguen el patrón de GA4 (tablas `events_*`)

                    **Solución:** Contacta al cliente para verificar que tiene acceso a proyectos con GA4.
                    """)

                    # Opción manual como fallback
                    with st.expander("🔧 Configurar manualmente (modo avanzado)"):
                        with st.form(f"configure_oauth_manual_{selected_token}"):
                            manual_col1, manual_col2 = st.columns(2)

                            with manual_col1:
                                manual_project_id = st.text_input(
                                    "Project ID de BigQuery *",
                                    placeholder="Ej: mi-proyecto-analytics"
                                )

                            with manual_col2:
                                manual_dataset_id = st.text_input(
                                    "Dataset ID *",
                                    placeholder="Ej: analytics_123456789"
                                )

                            manual_submitted = st.form_submit_button("✅ Guardar Configuración Manual", use_container_width=True)

                            if manual_submitted:
                                if not manual_project_id or not manual_dataset_id:
                                    st.error("❌ Por favor completa ambos campos")
                                else:
                                    if AccessManager.configure_oauth_token(selected_token, manual_project_id, manual_dataset_id):
                                        st.success("✅ Configuración guardada exitosamente")
                                        st.rerun()
                                    else:
                                        st.error("❌ Error guardando la configuración")
                else:
                    st.success(f"✅ Se encontraron {len(ga4_projects)} proyecto(s) con datasets de GA4")

                    with st.form(f"configure_oauth_{selected_token}"):
                        config_col1, config_col2 = st.columns(2)

                        with config_col1:
                            # Crear opciones con contador de datasets
                            project_options = [
                                f"{project_id} ({len(datasets)} dataset{'s' if len(datasets) > 1 else ''})"
                                for project_id, datasets in ga4_projects.items()
                            ]

                            # Mapeo para obtener el project_id original
                            project_mapping = {
                                f"{project_id} ({len(datasets)} dataset{'s' if len(datasets) > 1 else ''})": project_id
                                for project_id, datasets in ga4_projects.items()
                            }

                            selected_project_display = st.selectbox(
                                "Proyecto GCP con GA4 *",
                                options=project_options,
                                help="Selecciona el proyecto del cliente"
                            )

                            config_project_id = project_mapping[selected_project_display]

                        with config_col2:
                            # Obtener datasets del proyecto seleccionado
                            available_datasets = ga4_projects[config_project_id]

                            config_dataset_id = st.selectbox(
                                "Dataset GA4 *",
                                options=available_datasets,
                                help="Selecciona el dataset de GA4"
                            )

                        config_submitted = st.form_submit_button("✅ Guardar Configuración", use_container_width=True)

                        if config_submitted:
                            if not config_project_id or not config_dataset_id:
                                st.error("❌ Por favor completa ambos campos")
                            else:
                                if AccessManager.configure_oauth_token(selected_token, config_project_id, config_dataset_id):
                                    st.success("✅ Configuración guardada exitosamente")
                                    st.info("🔗 Ahora puedes usar el enlace de acceso para acceder a los datos del cliente")
                                    st.rerun()
                                else:
                                    st.error("❌ Error guardando la configuración")
            
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
