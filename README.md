# 📊 Análisis Exploratorio GA4 - Streamlit App

Aplicación web completa para análisis exploratorio de datos de Google Analytics 4 (GA4) exportados a BigQuery. Construida con Streamlit, ofrece visualizaciones interactivas y consultas avanzadas para análisis de marketing digital y ecommerce.

## 🎯 Características Principales

- 🔐 **Gestión de Consentimientos**: Análisis completo de cookies y privacidad (GDPR)
- 🛒 **Ecommerce Avanzado**: Funnels, productos más vendidos, ingresos y transacciones
- 📈 **Adquisición Multicanal**: Attribution modeling con 7 modelos diferentes
- 🎯 **Análisis de Eventos**: Exploración completa de eventos GA4 con flattenización
- 👥 **Análisis de Usuarios**: CLV, retención, tiempo a conversión, segmentación
- 🕒 **Análisis de Sesiones**: Rutas de navegación, rendimiento horario, exit pages

---

## 📁 Estructura del Proyecto

```
modular/
├── .devcontainer/
│   └── devcontainer.json          # Configuración de desarrollo
├── config/
│   ├── __init__.py
│   └── settings.py                # Configuración centralizada (colores, constantes)
├── database/
│   ├── __init__.py
│   ├── connection.py              # Cliente BigQuery y gestión de consultas
│   └── queries/
│       ├── __init__.py
│       ├── cookies_queries.py     # Consultas de consentimiento
│       ├── ecommerce_queries.py   # Consultas de ecommerce
│       ├── acquisition_queries.py # Consultas de atribución
│       ├── events_queries.py      # Consultas de eventos
│       ├── users_queries.py       # Consultas de usuarios
│       └── sessions_queries.py    # Consultas de sesiones
├── ui/
│   ├── __init__.py
│   ├── sidebar.py                 # Sidebar con configuración
│   └── tabs/
│       ├── __init__.py
│       ├── cookies_tab.py         # Tab de Cookies
│       ├── ecommerce_tab.py       # Tab de Ecommerce
│       ├── acquisition_tab.py     # Tab de Adquisición
│       ├── events_tab.py          # Tab de Eventos
│       ├── users_tab.py           # Tab de Usuarios
│       └── sessions_tab.py        # Tab de Sesiones
├── utils/
│   ├── __init__.py
│   ├── error_handling.py          # Manejo de errores
│   └── helpers.py                 # Funciones auxiliares
├── visualization/
│   ├── __init__.py
│   ├── common_charts.py           # Gráficos reutilizables
│   ├── cookies_visualizations.py  # Visualizaciones de cookies
│   ├── ecommerce_visualizations.py # Visualizaciones de ecommerce
│   ├── acquisition_visualizations.py # Visualizaciones de adquisición
│   ├── events_visualizations.py   # Visualizaciones de eventos
│   ├── users_visualizations.py    # Visualizaciones de usuarios
│   └── sessions_visualizations.py # Visualizaciones de sesiones
├── main.py                        # Punto de entrada de la aplicación
├── requirements.txt               # Dependencias del proyecto
├── LICENSE                        # Licencia MIT
└── README.md                      # Este archivo
```

---

### Requisitos Previos

- Python 3.11 o superior
- Cuenta de Google Cloud Platform con BigQuery habilitado
- Exportación de GA4 a BigQuery configurada
- Credenciales de servicio de GCP (archivo JSON)

---

## 📊 Módulos y Consultas

### 🍪 Cookies y Privacidad

Análisis de consentimientos (GDPR compliance):
- **Consentimiento Básico**: Distribución de analytics_storage y ads_storage
- **Consentimiento por Dispositivo**: Análisis cross-device de consentimientos
- **Porcentaje Real**: Cálculo preciso de tasas de consentimiento

**Visualizaciones**: Pie charts, gráficos de barras comparativos, métricas de compliance

---

### 🛒 Ecommerce

Análisis completo del funnel de ecommerce:
- **Funnel de Conversión**: page_view → view_item → add_to_cart → begin_checkout → purchase
- **Ingresos y Transacciones**: Evolución temporal de revenue y órdenes
- **Productos Más Vendidos**: Top productos por ingresos con nombres normalizados
- **Relación Productos**: Validación de consistencia item_id vs item_name

**Visualizaciones**: Funnel charts, gráficos de líneas temporales, scatter plots, heatmaps

---

### 📈 Adquisición

Attribution modeling y análisis de canales:
- **Canales de Tráfico**: Channel grouping automático (20+ categorías)
- **Atribución Básica**: 3 modelos (Last Click, First Click, Linear)
- **Atribución Completa**: 7 modelos incluidos
  - Last Click
  - First Click
  - Linear
  - Time Decay
  - Position Based (40-20-40)
  - Last Non-Direct
  - Data Driven

**Visualizaciones**: Sankey diagrams, gráficos comparativos multi-modelo, treemaps

---

### 🎯 Eventos

Exploración profunda de eventos GA4:
- **Eventos Flatten**: Desanidado completo de event_params, user_properties, items
- **Resumen de Eventos**: Top 50 eventos con métricas agregadas
- **Evolución Temporal**: Tendencias de eventos por fecha
- **Parámetros de Eventos**: Análisis detallado de parámetros por evento específico
- **Métricas Diarias**: Dashboard completo con 11+ métricas clave

**Visualizaciones**: Tablas interactivas, gráficos de líneas, scatter plots, métricas diarias

---

### 👥 Usuarios

Análisis de comportamiento y valor del usuario:
- **Retención Semanal**: Análisis de cohortes (Week 0-4)
- **Customer Lifetime Value**: CLV y correlación con sesiones
- **Tiempo a Primera Compra**: Velocidad de conversión por fuente
- **Landing Page Attribution**: Primera página vs métricas de conversión
- **Adquisición de Usuarios**: Channel grouping con métricas de performance
- **Conversión Mensual**: Tendencias de conversión mes a mes

**Visualizaciones**: Heatmaps de retención, scatter plots CLV, funnels, gráficos temporales

---

### 🕒 Sesiones

Análisis avanzado de sesiones:
- **Low Converting Sessions**: Identificación de sesiones sin conversión
  - Por fuente de tráfico, dispositivo, landing page
  - Bounce rate y engagement metrics
- **Session Path Analysis**: Rutas de navegación completas
  - Previous → Current → Next page
  - Sankey diagrams de flujos
  - Landing y exit pages
- **Hourly Performance**: Rendimiento por hora y día
  - Heatmap de actividad (día × hora)
  - Métricas de ecommerce por franja horaria
  - Identificación de picos de tráfico
- **Exit Pages Analysis**: Páginas de abandono
  - Top páginas con mayor salida
  - Análisis de Pareto (80/20)
  - Recomendaciones de optimización

**Visualizaciones**: Heatmaps, Sankey diagrams, gráficos de Pareto, scatter plots, análisis temporal

---

## 🎨 Tecnologías Utilizadas

### Backend
- **Python 3.11+**: Lenguaje principal
- **BigQuery**: Data warehouse y motor de consultas
- **Google Cloud SDK**: Autenticación y APIs

### Frontend
- **Streamlit**: Framework de la aplicación web
- **Plotly**: Gráficos interactivos
- **Pandas**: Manipulación de datos

### Visualización
- Gráficos de líneas y barras
- Pie charts y donut charts
- Scatter plots
- Heatmaps
- Funnel charts
- Sankey diagrams
- Treemaps
- Análisis de Pareto

---

## 📈 Métricas y KPIs

### Ecommerce
- Revenue, Transactions, AOV
- Conversion Rate, Add-to-Cart Rate
- Product Performance
- Funnel Drop-off Rates

### Usuarios
- New Users, Total Users
- User Retention (Week 0-4)
- Customer Lifetime Value
- Time to First Purchase
- Revenue per User

### Sesiones
- Session Count, Session Duration
- Bounce Rate, Engagement Rate
- Pages per Session
- Exit Rate por página
- Hourly Distribution

### Marketing
- Traffic by Channel
- Attribution by Model
- Source/Medium Performance
- Campaign Effectiveness
- ROI Metrics

---

## 🐛 Troubleshooting

### Error de Autenticación

```python
# Verifica que las credenciales estén correctamente configuradas
# En Streamlit Cloud: Settings > Secrets
# En local: archivo JSON de credenciales
```

### Timeout en Consultas

```python
# Ajusta el timeout en config/settings.py
QUERY_TIMEOUT = 60  # Aumentar a 60 segundos
```

### Memoria Insuficiente

```python
# Limita el número de resultados en las consultas
LIMIT 100  # Añadir al final de consultas pesadas
```

---

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

```
MIT License

Copyright (c) 2025 EAJ-APP

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 👨‍💻 Autor

**EAJ-APP**

- GitHub: [@EAJ-APP](https://github.com/EAJ-APP)

---

## 📊 Estadísticas del Proyecto

- **Líneas de código**: ~8,000+
- **Consultas SQL**: 25+
- **Visualizaciones**: 50+
- **Módulos**: 6 principales
- **Tests**: En desarrollo
