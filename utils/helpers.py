import warnings

def setup_environment():
    """Configura el entorno y suprime warnings"""
    warnings.filterwarnings("ignore", category=FutureWarning, 
                          message="When grouping with a length-1 list-like.*")

def format_percentage(value):
    """Formatea un valor como porcentaje"""
    return f"{value:.2f}%"

def format_currency(value):
    """Formatea un valor como moneda"""
    return f"€{value:,.2f}"

def safe_divide(numerator, denominator):
    """División segura evitando división por cero"""
    return numerator / denominator if denominator != 0 else 0