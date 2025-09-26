import plotly.express as px
import plotly.graph_objects as go
from config.settings import Settings

def create_pie_chart(df, names_col, values_col, title, color_map=None):
    """Crea un gráfico de torta estándar"""
    fig = px.pie(df, names=names_col, values=values_col, title=title)
    if color_map:
        fig.update_traces(marker=dict(colors=[color_map.get(x, Settings.CHART_COLORS['primary']) for x in df[names_col]]))
    return fig

def create_bar_chart(df, x_col, y_col, color_col=None, title="", barmode='group'):
    """Crea un gráfico de barras estándar"""
    if color_col:
        fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title, barmode=barmode)
    else:
        fig = px.bar(df, x=x_col, y=y_col, title=title)
    return fig

def create_funnel_chart(labels, values, title="Funnel Chart"):
    """Crea un gráfico de funnel"""
    fig = go.Figure(go.Funnel(
        y=labels,
        x=values,
        textinfo="value+percent initial",
        opacity=0.8
    ))
    fig.update_layout(title=title)
    return fig