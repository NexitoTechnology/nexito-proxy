from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_TITLE: str = "Proxy Service API"
    API_DESCRIPTION: str = "Service for scraping, validating and managing proxies"
    API_VERSION: str = "0.1.0"
    API_KEY: str = Field(default="your_secret_api_key_here")
    
    # MongoDB Settings
    MONGODB_URL: str = Field(default="mongodb://localhost:27017")
    MONGODB_DB: str = Field(default="proxy_service")
    
    # Proxy Settings
    PROXY_VALIDATION_INTERVAL: int = Field(default=3600)  # Validar proxies cada hora
    PROXY_MIN_SCORE: int = Field(default=50)  # Puntuación mínima para considerar un proxy válido
    PROXY_SOURCES: List[str] = Field(default=["free_proxy_list", "geonode", "proxyscrape"])
    
    # Configuración de scraping
    SCRAPING_INTERVAL: int = Field(default=6 * 3600)  # 6 horas

    model_config = {
        "env_file": ".env"
    }

settings = Settings()