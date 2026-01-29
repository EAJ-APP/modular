"""
Módulo para generar análisis de datos con Claude (Anthropic LLM)
"""
import streamlit as st
import pandas as pd
from anthropic import Anthropic


def get_anthropic_client() -> Anthropic | None:
    """Obtiene el cliente de Anthropic usando la API key de secrets."""
    try:
        api_key = st.secrets["anthropic"]["api_key"]
        return Anthropic(api_key=api_key)
    except Exception:
        return None


def generar_insight_tabla(df: pd.DataFrame, contexto: str) -> str | None:
    """
    Envía los datos de un DataFrame a Claude y devuelve un análisis en texto.

    Args:
        df: DataFrame con los datos a analizar
        contexto: Descripción de qué representan los datos

    Returns:
        str con el análisis generado o None si falla
    """
    client = get_anthropic_client()
    if not client:
        return None

    # Convertir DataFrame a texto legible (limitar filas para no exceder tokens)
    datos_csv = df.to_csv(index=False)

    prompt = f"""Eres un analista de datos especializado en Google Analytics 4 y consentimiento de cookies (GDPR/RGPD).

Contexto: {contexto}

Aquí tienes los datos en formato CSV:

{datos_csv}

Genera un análisis claro y accionable en español. El texto debe ser entendible para alguien sin conocimientos técnicos. Estructura tu respuesta así:

1. **Resumen general**: Qué muestran los datos en 2-3 frases
2. **Hallazgos clave**: Los 3-4 puntos más relevantes
3. **Tendencias**: Si hay patrones temporales o cambios significativos
4. **Recomendaciones**: 2-3 acciones concretas basadas en los datos

Sé conciso y directo. No repitas los números en bruto, interprétalos."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-20250414",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error al generar análisis: {str(e)}"
