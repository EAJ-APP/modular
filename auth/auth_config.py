class AuthConfig:
    """Configuración centralizada de autenticación"""
    
    # OAuth Scopes - VERSIÓN REDUCIDA TEMPORALMENTE
    SCOPES: List[str] = [
        # Scopes básicos (siempre permitidos)
        'openid',
        'email',
        'profile',
        # BigQuery - Solo lectura (menos restrictivo)
        'https://www.googleapis.com/auth/bigquery.readonly',
    ]
    
    # SCOPES COMPLETOS (comentados temporalmente para testing)
    # SCOPES: List[str] = [
    #     'https://www.googleapis.com/auth/bigquery.readonly',
    #     'https://www.googleapis.com/auth/bigquery',
    #     'openid',
    #     'email',
    #     'profile'
    # ]
