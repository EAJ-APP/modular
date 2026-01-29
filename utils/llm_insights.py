"""
Módulo para generar análisis de datos con Perplexity LLM
"""
import streamlit as st
import pandas as pd
from openai import OpenAI


def get_perplexity_client() -> OpenAI | None:
    """Obtiene el cliente de Perplexity usando la API key de secrets."""
    try:
        api_key = st.secrets["perplexity"]["api_key"]
        return OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
    except Exception:
        return None


def generar_insight_tabla(df: pd.DataFrame, contexto: str) -> str | None:
    """
    Envía los datos de un DataFrame a Perplexity y devuelve un análisis en texto.

    Args:
        df: DataFrame con los datos a analizar
        contexto: Descripción de qué representan los datos

    Returns:
        str con el análisis generado o None si falla
    """
    client = get_perplexity_client()
    if not client:
        return None

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
        response = client.chat.completions.create(
            model="sonar",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": "Eres un analista de datos experto. Responde siempre en español."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al generar análisis: {str(e)}"
