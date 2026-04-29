"""
core/config.py

Este archivo contiene la configuración global de la aplicación. Aquí se definen las variables de entorno y constantes

Responsabilidades principales:
    - Configurar la aplicación para diferentes entornos (producción, desarrollo, local).
    - Definir las variables de entorno y constantes globales de la aplicación.
    - Configurar la base de datos y otros servicios externos.
    - Definir las rutas y versiones de la API.
    - Establecer las claves y tokens de autenticación.
    - Definir las variables de configuración de los servicios de mensajería y notificaciones.
"""
import os

# Define el modo de ejecución de la aplicación para seleccionar la configuración de la base de datos.
# Se puede sobreescribir con la variable de entorno MODO (valores: "Local", "Producción")
Modo = "Local"  # Modos posibles: ["Local", "Producción"]

crear_usuarios_y_tablas = True # Crea las tablas y el usuario admin por defecto al iniciar la aplicación (solo si no existen)
perrobot = True # Utiliza perrobot para el envío de mensajes

# Configuración de la API
API_KEY= os.environ.get('API_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')
ALGORITHM = os.environ.get('ALGORITHM')
X_API_KEY = os.environ.get('X_API_KEY')
DOCS_API_KEY = os.environ.get('DOCS_API_KEY')
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 4    # 4 horas (mejor balance seguridad/UX)
REFRESH_TOKEN_EXPIRES_DAYS = 7          # 1 semana (suficiente para uso laboral)
FERNET_KEY = os.environ.get('FERNET_KEY')
# CORS
origenes_permitidos = '*'

API_PREFIX: str = "/api"
VERSION: str = "1.0.0"
PROJECT_NAME: str = "API raw Calypso"
PROJECT_DESCRIPTION: str = "API raw Calypso"
DEBUG: bool = False

# Base de datos producción
usernameDB = os.environ.get('usernameDB')
passwordDB = os.environ.get('passwordDB')
servernameDB = os.environ.get('servernameDB')
databasenameDB = os.environ.get('databasenameDB')

# Base de datos local
usernameDBLocal = os.environ.get('usernameDBLocal')
passwordDBLocal = os.environ.get('passwordDBLocal')
servernameDBLocal = os.environ.get('servernameDBLocal')
databasenameDBLocal = os.environ.get('databasenameDBLocal')

# Uris modos — se pueden sobreescribir con variables de entorno directas
DATABASE_URI_ASYNC_PROD = os.environ.get(
    "DATABASE_URI_ASYNC_PROD",
    f"postgresql+asyncpg://{usernameDB}:{passwordDB}@{servernameDB}:5432/{databasenameDB}"
)
DATABASE_URI_ASYNC_LOCAL = os.environ.get(
    "DATABASE_URI_ASYNC_LOCAL",
    f"postgresql+asyncpg://{usernameDBLocal}:{passwordDBLocal}@{servernameDBLocal}:5432/{databasenameDBLocal}"
)

# Default user
usernameAdmin = os.environ.get('usernameAdmin')
passhashAdminAPI = os.environ.get('passhashAdminAPI')

#perrobot
passhashAdmin= os.environ.get('passhashPerroBot')
if os.environ.get("passhashPerroBot") and not os.environ.get("passhashAdmin"):
    os.environ["passhashAdmin"] = os.environ["passhashPerroBot"]
