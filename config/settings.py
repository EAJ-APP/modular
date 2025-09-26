import pandas as pd
from datetime import datetime

class Settings:
    # Configuración de la aplicación
    APP_TITLE = "📊 Análisis Exploratorio GA4"
    PAGE_LAYOUT = "wide"
    
    # Configuración de BigQuery
    QUERY_TIMEOUT = 30
    DEFAULT_START_DATE = pd.to_datetime("2023-01-01")
    DEFAULT_END_DATE = pd.to_datetime("today")
    
    # Colores para gráficos
    CHART_COLORS = {
        'primary': '#1f77b4',
        'success': '#4CAF50',
        'warning': '#FF9800',
        'error': '#F44336',
        'info': '#2196F3',
        'secondary': '#9E9E9E'
    }
    
    # Orden de eventos para funnel
    FUNNEL_EVENTS = ['page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase']
    
    # Configuración de consentimiento
    CONSENT_MAPPING = {
        'true': 'Consentido',
        'false': 'No Consentido', 
        'null': 'No Definido'
    }