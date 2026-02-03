
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Configuración de la API
API_KEY = os.environ.get('API_KEY', 'default_api_key')
SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
ALGORITHM = os.environ.get('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 4
PROJECT_NAME: str = "API Template"
PROJECT_DESCRIPTION: str = "Template para nuevas APIs con FastAPI y Typer"
VERSION: str = "0.1.0"
API_PREFIX: str = "/api"
DEBUG: bool = os.environ.get('DEBUG', 'False').lower() == 'true'

# Base de datos
DATABASE_URL = os.environ.get('DATABASE_URL', "sqlite+aiosqlite:///./test.db")

# CORS
ORIGINS: List[str] = ["*"]
