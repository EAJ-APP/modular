import streamlit as st
import pandas as pd
from config.settings import Settings
from google.cloud import bigquery
from utils.error_handling import handle_bq_error

def render_sidebar():
    """Renderiza la barra lateral con configuración - Versión sin credenciales"""
    with st.sidebar:
        # Logo en sidebar
        try:
            st.image("assets/logo.png", width=120)
        except:
            st.markdown("### 🛡️ BigQuery Shield")
        
        st.divider()
        
        # Rango de fechas más visible
        st.markdown("### 📅 Período de Análisis")
        start_date = st.date_input(
            "Fecha inicio", 
            value=Settings.DEFAULT_START_DATE, 
            key="global_start_date",
            help="Selecciona la fecha de inicio del análisis"
        )
        end_date = st.date_input(
            "Fecha fin", 
            value=Settings.DEFAULT_END_DATE, 
            key="global_end_date",
            help="Selecciona la fecha de fin del análisis"
        )
        
        # Mostrar duración del período
        days_diff = (end_date - start_date).days
        if days_diff > 0:
            st.info(f"📊 Analizando **{days_diff} días** de datos")
        elif days_diff == 0:
            st.warning("⚠️ Selecciona un rango de fechas válido")
        else:
            st.error("❌ La fecha de inicio debe ser anterior a la fecha de fin")
        
        st.divider()
        
        # Links útiles
        with st.expander("🔗 Enlaces Útiles", expanded=False):
            st.markdown("""
            - [📖 Documentación GA4](https://support.google.com/analytics)
            - [💡 Guía BigQuery](https://cloud.google.com/bigquery/docs)
            - [🎯 FLAT 101 Digital](https://flat101.es)
            """)
        
        # Información de versión al final
        st.caption("---")
        st.caption("**BigQuery Shield v1.0**")
        st.caption("Powered by FLAT 101")
    
    return False, start_date, end_date

def is_ga4_dataset(client: bigquery.Client, project_id: str, dataset_id: str) -> bool:
    """
    Verifica si un dataset es de GA4
    
    Args:
        client: Cliente de BigQuery
        project_id: ID del proyecto
        dataset_id: ID del dataset
        
    Returns:
        True si es un dataset de GA4, False si no
    """
    try:
        # Los datasets de GA4 siguen el patrón: analytics_XXXXXXXXX
        if not dataset_id.startswith('analytics_'):
            return False
        
        # Verificar que tenga al menos una tabla events_*
        dataset_ref = f"{project_id}.{dataset_id}"
        tables = list(client.list_tables(dataset_ref, max_results=10))
        
        # Buscar tablas que empiecen con "events_"
        has_events_tables = any(table.table_id.startswith('events_') for table in tables)
        
        return has_events_tables
        
    except Exception:
        # Si hay error al listar tablas, asumir que no es GA4
        return False

def get_ga4_projects_and_datasets(client: bigquery.Client):
    """
    Obtiene solo proyectos con datasets de GA4
    
    Args:
        client: Cliente de BigQuery
        
    Returns:
        dict: {project_id: [lista de datasets GA4]}
    """
    ga4_projects = {}
    
    try:
        # Listar todos los proyectos
        projects = list(client.list_projects())
        
        for project in projects:
            project_id = project.project_id
            
            try:
                # Listar datasets del proyecto
                datasets = list(client.list_datasets(project_id))
                
                # Filtrar solo datasets de GA4
                ga4_datasets = []
                for dataset in datasets:
                    dataset_id = dataset.dataset_id
                    
                    if is_ga4_dataset(client, project_id, dataset_id):
                        ga4_datasets.append(dataset_id)
                
                # Solo añadir el proyecto si tiene datasets GA4
                if ga4_datasets:
                    ga4_projects[project_id] = ga4_datasets
                    
            except Exception:
                # Si no se pueden listar datasets del proyecto, continuar con el siguiente
                continue
        
        return ga4_projects
        
    except Exception as e:
        st.error(f"Error listando proyectos: {e}")
        return {}

def get_project_dataset_selection(client):
    """Obtiene la selección de proyecto y dataset - Solo GA4"""
    try:
        st.sidebar.markdown("### 🗄️ Fuente de Datos (GA4)")
        
        # Mostrar spinner mientras se cargan proyectos
        with st.sidebar:
            with st.spinner("🔍 Buscando proyectos con GA4..."):
                ga4_projects = get_ga4_projects_and_datasets(client)
        
        if not ga4_projects:
            st.sidebar.error("⚠️ No se encontraron proyectos con datasets de GA4")
            st.sidebar.info("""
            **Posibles causas:**
            - No tienes acceso a proyectos con GA4
            - Los datasets no siguen el patrón `analytics_XXXXXXXXX`
            - No hay tablas `events_*` en los datasets
            """)
            
            # Mostrar botón para ver todos los proyectos (debug)
            if st.sidebar.button("🔧 Mostrar todos los proyectos (debug)"):
                st.sidebar.write("**Proyectos disponibles:**")
                all_projects = list(client.list_projects())
                for proj in all_projects[:10]:  # Limitar a 10
                    st.sidebar.code(proj.project_id)
            
            return None, None
        
        # Crear opciones para el selectbox con contador de datasets
        project_options = [
            f"{project_id} ({len(datasets)} dataset{'s' if len(datasets) > 1 else ''})"
            for project_id, datasets in ga4_projects.items()
        ]
        
        # Mapeo para obtener el project_id original
        project_mapping = {
            f"{project_id} ({len(datasets)} dataset{'s' if len(datasets) > 1 else ''})": project_id
            for project_id, datasets in ga4_projects.items()
        }
        
        # Selectbox de proyecto
        selected_project_display = st.sidebar.selectbox(
            "Proyecto GCP con GA4", 
            project_options,
            help="Solo se muestran proyectos con datasets de Google Analytics 4"
        )
        
        # Obtener el project_id real
        selected_project = project_mapping[selected_project_display]
        
        # Obtener los datasets GA4 del proyecto seleccionado
        ga4_datasets = ga4_projects[selected_project]
        
        # Selectbox de dataset
        selected_dataset = st.sidebar.selectbox(
            "Dataset GA4", 
            ga4_datasets,
            help="Datasets de Google Analytics 4 encontrados en el proyecto"
        )
        
        # Mostrar información adicional del dataset
        with st.sidebar.expander("ℹ️ Info del Dataset", expanded=False):
            try:
                dataset_ref = f"{selected_project}.{selected_dataset}"
                tables = list(client.list_tables(dataset_ref, max_results=100))
                
                # Contar tablas events_*
                events_tables = [t for t in tables if t.table_id.startswith('events_')]
                
                st.write(f"**Tablas events_**: {len(events_tables)}")
                st.write(f"**Total de tablas**: {len(tables)}")
                
                # Mostrar rango de fechas disponibles
                if events_tables:
                    dates = []
                    for table in events_tables:
                        if table.table_id.startswith('events_') and len(table.table_id) > 7:
                            date_str = table.table_id.replace('events_', '')
                            if date_str.isdigit() and len(date_str) == 8:
                                dates.append(date_str)
                    
                    if dates:
                        dates.sort()
                        st.write(f"**Desde**: {dates[0]}")
                        st.write(f"**Hasta**: {dates[-1]}")
                
            except Exception as e:
                st.write(f"Error obteniendo info: {e}")
        
        # Indicador visual de conexión exitosa
        st.sidebar.success("✅ Conectado a dataset GA4")
        
        return selected_project, selected_dataset
        
    except Exception as e:
        handle_bq_error(e)
        return None, None
