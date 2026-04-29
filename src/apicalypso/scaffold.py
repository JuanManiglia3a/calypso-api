from pathlib import Path
import os

def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def _write_lf(path: Path, content: str):
    """Write file forcing LF line endings (required for shell scripts on Linux containers)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def create_dir_with_readme(root: Path, dir_name: str, readme_text: str):
    path = root / dir_name
    path.mkdir(parents=True, exist_ok=True)
    _write(path / "__init__.py", "")
    _write(path / "README.md", readme_text)
    return path

# ------------------------------------------------------------------------------
# FILE CONTENT TEMPLATES
# ------------------------------------------------------------------------------

MAIN_PY = """from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware 
from starlette.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from dependencies.limitador import limiter
from database.db_service import create_db_and_tables
from core import config
from contextlib import asynccontextmanager
from database.db import session_manager
from core.exceptions import exception_handler, http_exception_handler
from utils.logger import configure_logger
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
# ----------------------------------------------------------------
# Routers
# ----------------------------------------------------------------
from auth.auth_routes import router as security_router
from routes.crudUsuarios_router import router as crudUsuarios_router


description = f\"\"\"\n![Logo TripleAlpha](https://www.triplealpha.in/assets/img/logo-triple-alpha.svg)\n<br></br>\n*{config.PROJECT_DESCRIPTION}*\n\"\"\"\nlogger = configure_logger(name=__name__)\n\nusuariosDefault = False\ncrear_tablas = False\n\n@asynccontextmanager\nasync def lifespan(app: FastAPI):\n    \"\"\"\n    Función que maneja los eventos de inicio y cierre de la aplicación.\n    \"\"\"\n    if config.crear_usuarios_y_tablas:\n        await create_db_and_tables()\n    \n        from utils.defaultUser import create_defaultAdmin_user\n        from database.db_service import get_session_context\n        async for session in get_session_context():\n            await create_defaultAdmin_user(db=session)\n            break\n        \n    yield\n    \n    if session_manager._engine is not None:\n        await session_manager.close()\n        logger.info(\"Conexión a la base de datos cerrada.\")\n\napp = FastAPI(\n    title=config.PROJECT_NAME,\n    description=description,\n    version=config.VERSION,\n    debug=config.DEBUG,\n    contact={'email':'adosil@triplealpha.in'},\n    lifespan=lifespan,\n    docs_url=None,\n    redoc_url=None,\n    )\n\n# ----------------------------------------------------------------\n# Favicon, raíz, docs y redoc\n# ----------------------------------------------------------------\napp.mount(\"/static\", StaticFiles(directory=\"static\"), name=\"static\")\n@app.get(\"/favicon.ico\", include_in_schema=False)\nasync def favicon():\n    return FileResponse(\"static/img/favicon.ico\")\n\n@app.get(\"/\", include_in_schema=False)\nasync def root():\n    return {\"mensaje\": f\"Bienvenido a {config.PROJECT_NAME}. Para más información, visita /docs o /redoc. Con la API Key, puedes acceder a la documentación de la API en /docs?api_key=<<api_key>> o /redoc?api_key=<<api_key>>.\"}\n\n@app.get(\"/docs\", include_in_schema=False)\nasync def custom_swagger_ui_html():\n    return get_swagger_ui_html(\n        openapi_url=app.openapi_url,\n        title=app.title + \" - Calypso Swagger UI\",\n        swagger_favicon_url=\"/static/img/favicon.ico\"\n    )\n    \n@app.get(\"/redoc\", include_in_schema=False)\nasync def custom_redoc_html():\n    return get_redoc_html(\n        openapi_url=app.openapi_url,\n        title=app.title + \" - Calypso ReDoc\",\n        redoc_favicon_url=\"/static/img/favicon.ico\"\n    )\n\n# ----------------------------------------------------------------\n# Configuración de límites de velocidad\n# ----------------------------------------------------------------\napp.state.limiter = limiter\napp.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)\n\n# ----------------------------------------------------------------\n# Middleware para permitir CORS\n# ----------------------------------------------------------------\napp.add_middleware(\n    CORSMiddleware,\n    allow_origins=[config.origenes_permitidos],\n    allow_credentials=False,\n    allow_methods=[\"*\"],\n    allow_headers=[\"*\"],\n)\n    \n# ----------------------------------------------------------------\n# Protege /docs y /redoc con api_key\n# ----------------------------------------------------------------\n@app.middleware(\"http\")\nasync def check_api_key(request: Request, call_next):\n    if request.url.path in [\"/docs\", \"/redoc\"]: \n        api_key = request.query_params.get(\"api_key\")\n\n        if not api_key:\n            return JSONResponse(status_code=401, content={\"detail\": \"Para acceder a /docs y /redoc, se requiere una API Key, la cual hay que pasarla como parámetro 'api_key' en la URL. Ejemplo: /docs?api_key=API\"})\n        if api_key != config.DOCS_API_KEY:\n            return JSONResponse(status_code=401, content={\"detail\": \"API Key incorrecta.\"})\n\n    response = await call_next(request)\n    return response\n\n# ----------------------------------------------------------------\n# Manejo de excepciones\n# ----------------------------------------------------------------\napp.add_exception_handler(Exception, exception_handler)\napp.add_exception_handler(HTTPException, http_exception_handler)\n\n# ----------------------------------------------------------------\n# Rutas\n# ----------------------------------------------------------------\n# Middleware de compresión GZip para respuestas grandes\napp.add_middleware(GZipMiddleware, minimum_size=1024)\n\napp.include_router(security_router)\napp.include_router(crudUsuarios_router)\n"""

CORE_CONFIG_PY = """\"\"\"
core/config.py

Este archivo contiene la configuración global de la aplicación.

Responsabilidades principales:
    - Configurar la aplicación para diferentes entornos (producción, desarrollo, local).
    - Definir las variables de entorno y constantes globales de la aplicación.
    - Configurar la base de datos y otros servicios externos.
\"\"\"
import os

# Define el modo de ejecución de la aplicación para seleccionar la configuración de la base de datos.
# Valores posibles: "Local", "Producción"
Modo = "Local"  # Modos posibles: ["Local", "Producción"]

crear_usuarios_y_tablas = True  # Crea las tablas y el usuario admin por defecto al iniciar
perrobot = {perrobot}  # Utiliza perrobot para el envio de mensajes

# Configuración de la API
API_KEY = os.environ.get('API_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')
ALGORITHM = os.environ.get('ALGORITHM', 'HS256')
X_API_KEY = os.environ.get('X_API_KEY')
DOCS_API_KEY = os.environ.get('DOCS_API_KEY')
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 4    # 4 horas
REFRESH_TOKEN_EXPIRES_DAYS = 7          # 1 semana
FERNET_KEY = os.environ.get('FERNET_KEY')

# CORS
origenes_permitidos = '*'

API_PREFIX: str = "/api"
VERSION: str = "1.0.0"
PROJECT_NAME: str = "{project_name}"
PROJECT_DESCRIPTION: str = "{description}"
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
"""

CORE_EXCEPTIONS_PY = """from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from utils.logger import configure_logger
import functools

logger = configure_logger(name=__name__)

class CustomException(Exception):
    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message

async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Ocurrió un error interno en el servidor."},
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

def handle_db_exceptions(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error de base de datos en {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar la solicitud en la base de datos"
            )
    return wrapper
"""

DATABASE_DB_PY = """\"\"\"
database/db.py

Este archivo define la configuración de la base de datos.
Crea un contexto asíncrono para manejar sesiones de la base de datos.

Responsabilidades:
    - Crear un contexto asíncrono para manejar sesiones de la base de datos.
    - Configurar la base de datos según el modo de ejecución.
\"\"\"

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from core import config
import contextlib
from typing import AsyncIterator, Any
from utils.logger import configure_logger

logger = configure_logger(name=__name__)

Base = declarative_base()

class DatabaseSessionManager:
    def __init__(self, db_url: str, engine_kwargs: dict[str, Any] = {}):
        engine_kwargs = engine_kwargs or {}
        self._engine = create_async_engine(db_url, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")
        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Configuración de la base de datos según el modo
match config.Modo:
    case "Local":
        logger.info("Utilizando base de datos local...")
        async_uri = config.DATABASE_URI_ASYNC_LOCAL
    case "Producción":
        logger.warning("Utilizando base de datos de producción...")
        async_uri = config.DATABASE_URI_ASYNC_PROD
    case _:
        raise ValueError("Modo no soportado")

# Instancia global del gestor de sesiones para ser utilizada en toda la aplicacion.
session_manager = DatabaseSessionManager(
    async_uri,
    {"echo": False, "pool_pre_ping": True, "pool_recycle": 3600},
)
"""

DATABASE_SERVICE_PY = """\"\"\"
database/db_service.py

Este archivo define las dependencias necesarias para los servicios de la base de datos.

Responsabilidades principales:
- Proporcionar un contexto para una sesión asíncrona de la base de datos.
- Crear las tablas en la base de datos si no existen.
\"\"\"

from database.db import Base, session_manager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncIterator, Annotated
from fastapi import Depends
from utils.logger import configure_logger
logger = configure_logger(name=__name__)

async def get_session_context() -> AsyncIterator[AsyncSession]:
    \"\"\"Proporciona un contexto para una sesión asíncrona de la base de datos.\"\"\"
    async with session_manager.session() as session:
        yield session

async def create_db_and_tables():
    \"\"\"Crea las tablas en la base de datos.\"\"\"
    logger.info("Creando tablas en la base de datos...")
    async with session_manager._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
DBSessionAsyncDependency = Annotated[AsyncSession, Depends(get_session_context)]
"""

MODELS_PY = '''"""
models/models.py

Este archivo define las clases que representan las tablas de la base de datos utilizando SQLAlchemy ORM.

Responsabilidades:
- Definir las clases que representan las tablas de la base de datos.
- Definir las relaciones entre las tablas.
"""

from sqlalchemy import (
    UniqueConstraint, LargeBinary
)
from sqlalchemy.orm import (
    Mapped, mapped_column
)
from database.db import Base

#========== Usuarios
class Usuario(Base):
    __tablename__ = \'Usuario\'

    username: Mapped[str] = mapped_column(primary_key=True)
    passhash: Mapped[bytes] = mapped_column(LargeBinary)
    salt: Mapped[bytes] = mapped_column(LargeBinary)
    deshabilitado: Mapped[bool]
    isAdmin: Mapped[bool]

    __table_args__ = (
        UniqueConstraint(\'username\'),
        {\'schema\': \'public\'},
    )
'''

AUTH_DEPENDENCIES_PY = '''"""
auth/auth_dependencies.py

Este archivo define las dependencias relacionadas con la autenticación para FastAPI. 
Estas dependencias se utilizan para validar y obtener información del usuario autenticado 
antes de permitir el acceso a ciertos endpoints.

Responsabilidades principales:
- Validar el token de acceso y obtener al usuario actual.
- Verificar roles o permisos del usuario autenticado.
- Configurar dependencias reutilizables para proteger endpoints de la API.
- Implementar funciones para validar API Keys.
"""


from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader, APIKeyQuery
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from auth.auth_service import get_user
from schemas.schemas import TokenData, User
from core import config
from database.db_service import get_session_context

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name="x_api_key", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session_context)
):
    """Obtener el usuario actual a partir del token."""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user = await get_user(db, username=token_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user

async def get_current_active_user(
    current_user: User = Security(get_current_user)
):
    """Validar que el usuario no esté deshabilitado."""
    if current_user.deshabilitado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
    return current_user

async def get_current_admin_user(
    current_user: User = Security(get_current_user)
):
    """Validar que el usuario sea administrador."""
    if not current_user.isAdmin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario no autorizado")
    return current_user

api_key_query = APIKeyQuery(name="api_key", auto_error=False, description=\'API Key QUERY para acceder a endpoints protegidos con Query.\')
def get_api_key_query(api_key: str = Security(api_key_query)) -> str:
    if api_key == config.API_KEY:
        return api_key

    raise HTTPException(status_code=401, detail="API Key incorrecta")

api_key_header = APIKeyHeader(name="x_api_key", auto_error=False, description=\'API Key HEADER para acceder a endpoints protegidos con Header.\')
def get_api_key_header(api_key: str = Security(api_key_header)) -> str:
    if api_key == config.X_API_KEY:
        return api_key

    raise HTTPException(status_code=401, detail="API Key incorrecta")
'''

AUTH_ROUTES_PY = '''"""
auth/auth_routes.py

Este archivo contiene las rutas relacionadas con la autenticación y seguridad de la API. 
Incluye endpoints para iniciar sesión, obtener tokens de acceso y refrescar información del usuario.

Responsabilidades principales:
- Proporcionar rutas para el inicio de sesión con OAuth2.
- Permitir a los usuarios autenticados consultar información sobre su cuenta.
- Manejar límites de acceso mediante decoradores de rate limiting.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from auth.auth_service import authenticate_user, get_user
from auth.auth_utils import create_access_token
from auth.auth_dependencies import get_current_active_user
from database.db_service import get_session_context
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.schemas import Token, User
from dependencies.limitador import limiter
from datetime import timedelta
from core import config
from utils.logger import configure_logger

logger = configure_logger(name=__name__, level="INFO")

router = APIRouter(tags=["Seguridad y Autenticación"])

@router.post("/token")
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session_context)
):
    """Endpoint para obtener un token de acceso y refresh token."""
    user = await authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        logger.error(f"Intento de inicio de sesión fallido para el usuario {form_data.username} desde {request.client.host}. Usuario o contraseña incorrectos.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"Usuario {user.username} autenticado con éxito desde {request.client.host}")
    
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=config.REFRESH_TOKEN_EXPIRES_DAYS)

    access_token = create_access_token(
        data={"sub": user.username, "type": "access"}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": user.username, "type": "refresh"}, expires_delta=refresh_token_expires
    )

    # Aquí asegúrate de devolver ambos tokens
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@router.post("/refresh-token")
@limiter.limit("10/minute")
async def refresh_access_token(
    request: Request,
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_session_context)
):
    """Endpoint para renovar el access token usando el refresh token."""
    try:
        # Verificar el refresh token
        payload = jwt.decode(refresh_token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar que el usuario existe y está activo
        user = await get_user(db, username=username)
        if not user or user.deshabilitado:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generar nuevo access token
        access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": user.username, "type": "access"}, 
            expires_delta=access_token_expires
        )
        
        logger.info(f"Token renovado para usuario {user.username} desde {request.client.host}")
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except JWTError:
        logger.error(f"Intento de renovación con refresh token inválido desde {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Obtener la información del usuario actual."""
    return current_user
'''

CONTROLLERS_BASE_PY = '''"""
controllers/base_controller.py

Esta clase base define la funcionalidad común para todos los controladores en la API de SeaValue.

Responsabilidades principales:
    - Proporcionar métodos CRUD genéricos para todas las entidades
    - Reducir la duplicación de código entre controladores
    - Permitir extensión específica en controladores derivados
"""

from fastapi.responses import JSONResponse, FileResponse
from fastapi import BackgroundTasks
from utils.logger import configure_logger
from core.exceptions import handle_db_exceptions
from repositories.inserta_registros_repository import InsertaRegistros
from repositories.consulta_tabla_repository import ConsultaRegistros
from repositories.actualiza_registros_repository import ActualizaRegistros
from repositories.elimina_registros_repository import EliminaRegistros
from repositories.patch_registros_repository import PatchRegistros
from helpers.validate_dataframe_helper import DataFrameValidator
import pandas as pd
import io
import os

logger = configure_logger(name=__name__, level="INFO")

class BaseController:
    """
    Controlador base que proporciona funcionalidad CRUD común para todas las entidades.
    
    Attributes:
        db: Conexión a la base de datos
        model_class: Clase del modelo SQLAlchemy/SQLModel
        table_name: Nombre de la tabla en la base de datos
    """
    
    def __init__(self, db, model_class):
        """
        Inicializa el controlador base con la conexión a la base de datos y la clase del modelo.
        
        Args:
            db: Conexión a la base de datos
            model_class: Clase del modelo SQLAlchemy/SQLModel
        """
        self.db = db
        self.model_class = model_class
        self.table_name = model_class.__tablename__
        self.inserta_registros = InsertaRegistros(db)
        self.consulta_tablas = ConsultaRegistros(db)
        self.actualiza_registros = ActualizaRegistros(db)
        self.elimina_registros = EliminaRegistros(db)
        self.patch_repo = PatchRegistros(db)
        
    
    @handle_db_exceptions
    async def insert_registros(self, file, background_tasks: BackgroundTasks, schema=None):
        """
        Método genérico para insertar registros en la base de datos.
        
        Args:
            file: Archivo parquet subido
            background_tasks: Tareas en segundo plano de FastAPI
            schema: Esquema opcional para validación
            
        Returns:
            JSONResponse con mensaje de éxito
        """
        contents = await file.read()
        data = pd.read_parquet(io.BytesIO(contents), engine="pyarrow")
        if schema:
            DataFrameValidator.validate(data, schema)
        await self.inserta_registros.inserta_registros(
            self.model_class, contents, background_tasks, schema=schema
        )
        return JSONResponse(content={
            "message": f"Esquema validado, la inserción de registros en la tabla {self.table_name} se está procesando en segundo plano."
        })
    
    @handle_db_exceptions
    async def get_registros(self):
        """
        Método genérico para obtener todos los registros de la entidad en
        formato Parquet.

        Exporta la tabla a un fichero temporal en disco por chunks (bajo
        consumo de RAM) y lo devuelve como FileResponse.  El fichero
        temporal se elimina automáticamente tras enviar la respuesta
        mediante un BackgroundTask de Starlette.

        Consumible directamente desde pandas, Polars, PowerBI o cualquier
        cliente HTTP.

        Returns:
            FileResponse: Fichero .parquet con todos los registros de la tabla.
            JSONResponse: 204 si la tabla está vacía.
        """
        from starlette.background import BackgroundTask

        parquet_path, total_rows = await self.consulta_tablas.exportar_tabla_a_parquet(
            self.model_class
        )

        if total_rows == 0:
            return JSONResponse(
                status_code=204,
                content={"message": f"La tabla {self.table_name} está vacía."},
            )

        filename = f"{self.table_name}.parquet"

        return FileResponse(
            parquet_path,
            media_type="application/octet-stream",
            filename=filename,
            headers={"X-Total-Records": str(total_rows)},
            background=BackgroundTask(os.unlink, parquet_path),
        )

    @handle_db_exceptions
    async def get_registros_paginado(
        self, page: int = 1, size: int = 50, filtros: list = None,
        order_by: str = None, order_dir: str = "desc"
    ) -> dict:
        """
        Método genérico para obtener registros paginados con filtros opcionales.
        Replica el patrón de SeaValue (PaginatedResponse).

        Args:
            page: Número de página (empieza en 1)
            size: Registros por página (máx 500)
            filtros: Cláusulas WHERE opcionales
            order_by: Columna para ordenar
            order_dir: Dirección del orden ("asc" / "desc")

        Returns:
            dict con items, page, size, total_items, total_pages, has_next, has_prev
        """
        page = max(page, 1)
        size = max(min(size, 500), 1)
        offset = (page - 1) * size

        items, total_items = await self.consulta_tablas.obtener_tabla_paginada(
            self.model_class, filtros=filtros, offset=offset, limit=size,
            order_by=order_by, order_dir=order_dir
        )

        total_pages = (total_items + size - 1) // size if total_items else 0

        return {
            "items": items,
            "page": page,
            "size": size,
            "total_items": total_items or 0,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1 and total_pages > 0,
        }

    @handle_db_exceptions
    async def upsert_registros(self, file, background_tasks: BackgroundTasks, schema=None, primary_keys=None):
        """
        Método genérico para actualizar o insertar registros.
        
        Args:
            file: Archivo parquet subido
            background_tasks: Tareas en segundo plano de FastAPI
            schema: Esquema opcional para validación
            primary_keys: Lista de nombres de columnas que forman la clave primaria (opcional)
                
        Returns:
            JSONResponse con mensaje de éxito
        """
        contents = await file.read()
        data = pd.read_parquet(io.BytesIO(contents), engine="pyarrow")
        if schema:
            DataFrameValidator.validate(data, schema)
        
        # Si no se especifican claves primarias, las extraemos automáticamente del modelo
        if primary_keys is None:
            primary_keys = [key.name for key in self.model_class.__table__.primary_key.columns]
        
        await self.actualiza_registros.actualiza_registros(
            self.model_class, contents, background_tasks, primary_keys
        )
        return JSONResponse(content={
            "message": f"El upsert de registros en la tabla {self.table_name} se está procesando en segundo plano."
        })
        
    @handle_db_exceptions
    async def overwrite_registros(self, file, background_tasks: BackgroundTasks, schema=None):
        """
        Método genérico para sobrescribir todos los registros de la entidad.
        
        Args:
            file: Archivo parquet subido
            background_tasks: Tareas en segundo plano de FastAPI
            schema: Esquema opcional para validación
            
        Returns:
            JSONResponse con mensaje de éxito
        """
        contents = await file.read()
        data = pd.read_parquet(io.BytesIO(contents), engine="pyarrow")
        if schema:
            DataFrameValidator.validate(data, schema)
        
        await self.actualiza_registros.sobreescribir_registros(
            self.model_class, contents, background_tasks
        )
        return JSONResponse(content={
            "message": f"La sobrescritura de registros en la tabla {self.table_name} se está procesando en segundo plano."
        })
    
    @handle_db_exceptions
    async def delete_registros(self, claves_primarias: list, background_tasks: BackgroundTasks, nombre_columna_clave: str = None):
        """
        Método genérico para eliminar registros por claves primarias.
        
        Args:
            claves_primarias: Lista de valores de claves primarias a eliminar
            background_tasks: Tareas en segundo plano de FastAPI
            nombre_columna_clave: Nombre de la columna de clave primaria (opcional, se detecta automáticamente)
            
        Returns:
            None (FastAPI manejará automáticamente el código 204)
        """
        # Si no se especifica el nombre de la columna, extraemos la primera clave primaria del modelo
        if nombre_columna_clave is None:
            primary_key_columns = [key.name for key in self.model_class.__table__.primary_key.columns]
            if not primary_key_columns:
                raise ValueError(f"No se encontraron claves primarias en la tabla {self.table_name}")
            nombre_columna_clave = primary_key_columns[0]
        
        await self.elimina_registros.elimina_registros_por_claves(
            self.model_class, claves_primarias, background_tasks, nombre_columna_clave
        )
    
    @handle_db_exceptions
    async def patch_registro(self, clave_primaria, campos_actualizacion: dict, background_tasks: BackgroundTasks, nombre_columna_clave: str = None):
        """
        Actualiza campos específicos de un registro existente.
        
        Args:
            clave_primaria: Valor de la clave primaria del registro a actualizar
            campos_actualizacion: Diccionario con los campos y valores a actualizar
            background_tasks: Tareas en segundo plano de FastAPI
            nombre_columna_clave: Nombre de la columna de clave primaria (opcional, se detecta automáticamente)
            
        Returns:
            dict: Registro actualizado
        """
        # Si no se especifica el nombre de la columna, extraemos la primera clave primaria del modelo
        if nombre_columna_clave is None:
            primary_key_columns = [key.name for key in self.model_class.__table__.primary_key.columns]
            if not primary_key_columns:
                raise ValueError(f"No se encontraron claves primarias en la tabla {self.table_name}")
            nombre_columna_clave = primary_key_columns[0]
        
        # Verificar que el registro existe
        registro_existente = await self.patch_repo.verificar_existencia_registro(
            self.model_class, clave_primaria, nombre_columna_clave
        )
        
        if not registro_existente:
            raise ValueError(f"No se encontró el registro con {nombre_columna_clave}={clave_primaria}")
        
        # Actualizar el registro
        registro_actualizado = await self.patch_repo.patch_registro_generico(
            self.model_class, clave_primaria, campos_actualizacion, background_tasks, nombre_columna_clave
        )
        
        return registro_actualizado
'''

REPOSITORIES_CONSULTA_PY = '''"""
dependencies/consultatabla_depend.py

Este archivo contiene dependencias comunes para los controladores de la API.
Consulta tablas.

Responsabilidades:
    - Consultar tablas de la base de datos.
"""
from fastapi.responses import StreamingResponse, FileResponse
import tempfile
from core.exceptions import handle_db_exceptions
from sqlalchemy import select
import pandas as pd

class ConsultaRegistros:
    
    def __init__(self, db):
        self.db = db
        self.max_params = 32767  # Límite de asyncpg
        
    @handle_db_exceptions
    async def obtener_tabla_en_batches(self, tabla) -> StreamingResponse:
        """
        Obtiene los registros de la tabla en batches y los escribe en un archivo Parquet incrementalmente.
        Si la tabla está vacía, devuelve un diccionario vacío.
        """
        try:
            offset = 0
            registros_totales = 0  
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
            parquet_path = temp_file.name
            df_total = pd.DataFrame()
            
            # Obtener el número de columnas de la tabla
            query = select(tabla).limit(1)
            result = await self.db.execute(query)
            registros = result.scalars().all()
            if not registros:
                return {}

            num_columnas = len(registros[0].__dict__) - 1  # Excluir _sa_instance_state

            # Calcular batch_size dinámicamente
            batch_size = self.max_params // num_columnas

            while True:
                query = select(tabla).limit(batch_size).offset(offset)
                result = await self.db.execute(query)
                registros = result.scalars().all()

                if not registros:
                    break  # No hay más registros

                registros_totales += len(registros)

                # Convertir registros a lista de diccionarios
                registros_dict = [registro.__dict__ for registro in registros]
                for registro in registros_dict:
                    registro.pop(\'_sa_instance_state\', None)

                # Convertir a DataFrame de pandas
                df = pd.DataFrame(registros_dict)

                # Concatenar el DataFrame actual con el total
                df_total = pd.concat([df_total, df], ignore_index=True)

                offset += batch_size

            # Si no se encontraron registros, devolver un diccionario vacío
            if registros_totales == 0:
                return {}

            # Escribir el DataFrame total en el archivo Parquet usando pandas
            df_total.to_parquet(parquet_path, index=False)

        finally:
            temp_file.close()

        return FileResponse(
            parquet_path,
            media_type="application/octet-stream",
            filename="datos.parquet"
        )
'''

SCHEMAS_PY = '''# models/schemas.py
\'\'\'
Esquemas de SQLModel para definir los esquemas para interactuar con la base de datos (SQLModel)
\'\'\'

from sqlmodel import SQLModel

#========= Autenticación ======== 
class User(SQLModel):
    username: str
    deshabilitado: bool | None = None
    isAdmin: bool | None = None

class Token(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(SQLModel):
    username: str | None = None

class UserInDB(User):
    passhash: str
    
class UserInResponse(SQLModel):
    username: str
    passhash: str
    deshabilitado: bool = False
    isAdmin: bool = False
'''

HELPERS_PY = """from datetime import datetime
import uuid

def get_current_timestamp() -> datetime:
    \"\"\"Retorna la fecha y hora actual.\"\"\"
    return datetime.utcnow()

def generate_unique_id() -> str:
    \"\"\"Genera un ID único (UUID4).\"\"\"
    return str(uuid.uuid4())

def format_currency(amount: float) -> str:
    \"\"\"Formatea un monto como moneda.\"\"\"
    return f"${amount:,.2f}"
"""

SERVICES_PY = """class BaseService:
    \"\"\"
    Servicio base para lógica de negocio compartida.
    \"\"\"
    def __init__(self, db):
        self.db = db

class ExampleService(BaseService):
    \"\"\"
    Ejemplo de servicio que encapsula lógica de negocio compleja.
    \"\"\"
    async def perform_complex_operation(self, input_data: dict) -> dict:
        # Aquí iría la lógica compleja
        result = {
            "processed": True,
            "data": input_data,
            "timestamp": "2023-01-01"
        }
        return result
"""

SERVICES_README = """# Services

La capa de **Servicios** se utiliza para encapsular lógica de negocio compleja que no pertenece a un controlador específico o que necesita ser reutilizada por múltiples controladores.

## Propósito
- Desacoplar lógica compleja de los controladores.
- Implementar integraciones con servicios externos (APIs, Email, Storage).
- Procesos en segundo plano.

## Estructura
Los servicios pueden ser clases o módulos de funciones. Se recomienda inyectar las dependencias (como `db`) en el constructor.

### Ejemplo de Servicio

```python
class PaymentService:
    def __init__(self, db):
        self.db = db

    async def process_payment(self, amount: float, currency: str):
        # Lógica de pago compleja
        if currency != "USD":
            amount = await self.convert_currency(amount, currency)
        return await self.gateway.charge(amount)
```
"""

HELPERS_README = """# Helpers

Este directorio contiene funciones de ayuda generales y utilidades que pueden ser reutilizadas en toda la aplicación.

## Propósito
Alojar lógica auxiliar que no pertenece estrictamente a la lógica de negocio (Controllers) ni a la infraestructura (Core/Database).

## Ejemplos de uso
- Formateo de fechas y horas.
- Manipulación de cadenas de texto.
- Generación de identificadores únicos.
- Validaciones genéricas.

## Estructura sugerida
Puedes organizar los helpers en módulos específicos (ej. `date_helpers.py`, `string_helpers.py`) o mantener un archivo `utils.py` para funciones generales.
"""

CONTROLLERS_README = """# Controllers

Los **Controladores** encapsulan la lógica de negocio de la aplicación. Actúan como intermediarios entre las Rutas (entrada de datos) y los Repositorios (acceso a datos).

## Responsabilidades
- Validar reglas de negocio complejas.
- Orquestar llamadas a múltiples repositorios o servicios.
- Transformar datos para la respuesta.
- Manejar excepciones específicas del dominio.

## Estructura
Todos los controladores deberían heredar de `BaseController` para aprovechar funcionalidades comunes (CRUD básico, manejo de sesiones).

### Ejemplo de Controlador

```python
from controllers.base_controller import BaseController
from models.models import ExampleModel

class ExampleController(BaseController):
    def __init__(self, db):
        super().__init__(db, ExampleModel)

    async def get_custom_data(self):
        # Lógica personalizada
        return await self.repository.get_all()
```
"""

MODELS_README = """# Models

Este directorio contiene los modelos ORM (Object-Relational Mapping) definidos con **SQLAlchemy**.

## Propósito
Representar las tablas de la base de datos como clases de Python.

## Convenciones
- Cada clase representa una tabla.
- Los atributos de la clase representan las columnas.
- Se recomienda usar nombres en singular para las clases (ej. `User`) y plural para las tablas (ej. `users`).

### Ejemplo de Modelo

```python
from sqlalchemy import Column, Integer, String, Boolean
from database.db import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
```
"""

ROUTES_README = """# Routes

Aquí se definen los **Endpoints** de la API utilizando `APIRouter` de FastAPI.

## Responsabilidades
- Definir rutas HTTP (GET, POST, PUT, DELETE, etc.).
- Recibir peticiones y validar parámetros de entrada.
- Inyectar dependencias (como la sesión de base de datos).
- Delegar la lógica de negocio a los **Controllers**.
- Retornar respuestas HTTP adecuadas.

### Ejemplo de Router

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.db_service import get_session_context
from controllers.example_controller import ExampleController

router = APIRouter(prefix="/items", tags=["Items"])

@router.get("/")
async def read_items(db: AsyncSession = Depends(get_session_context)):
    controller = ExampleController(db)
    return await controller.get_registros()
```
"""

SCHEMAS_README = """# Schemas

Los **Esquemas** (Schemas) son definiciones de datos utilizando **Pydantic**.

## Propósito
- **Validación de entrada**: Asegurar que los datos enviados por el cliente cumplen con el formato esperado.
- **Serialización de salida**: Definir qué datos se envían de vuelta al cliente (filtrando información sensible).
- **Documentación automática**: FastAPI usa estos esquemas para generar la documentación Swagger/OpenAPI.

### Ejemplo de Schema

```python
from pydantic import BaseModel
from typing import Optional

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    price: float

class ItemResponse(ItemBase):
    id: int
    
    class Config:
        from_attributes = True
```
"""

README_TEMPLATE = """# {project_name}

{project_description}

Este proyecto fue generado con **Calypso API**, proporcionando una estructura robusta y escalable basada en FastAPI, SQLAlchemy (Async) y PostgreSQL.

## 🚀 Características

- **FastAPI**: Framework moderno y de alto rendimiento.
- **SQLAlchemy Async**: ORM asíncrono para interactuar con la base de datos.
- **PostgreSQL**: Base de datos relacional robusta.
- **Docker & Docker Compose**: Configuración lista para desplegar en contenedores.
- **Autenticación JWT**: Sistema seguro de login y protección de rutas.
- **Estructura Modular**: Organización clara en controladores, servicios, repositorios y rutas.

## 📋 Requisitos Previos

- Python 3.10+
- Docker y Docker Compose (opcional, para despliegue en contenedores)
- PostgreSQL (si no se usa Docker)

## 🛠️ Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd {project_slug}
```

### 2. Configurar entorno virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\\Scripts\\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Variables de Entorno

El proyecto ya viene configurado con valores por defecto en `core/config.py`, pero puedes sobrescribirlos mediante variables de entorno del sistema o creando un archivo `.env` (si añades soporte para `python-dotenv`).

Variables clave:
- `POSTGRES_USER`: Usuario de la BD.
- `POSTGRES_PASSWORD`: Contraseña de la BD.
- `POSTGRES_DB`: Nombre de la BD.
- `SECRET_KEY`: Llave para firmar tokens JWT.

## ▶️ Ejecución

### Modo Local

Asegúrate de tener una instancia de PostgreSQL corriendo localmente o ajusta la configuración en `core/config.py`.

```bash
uvicorn main:app --reload --host {host} --port {port}
```

La API estará disponible en: `http://{host}:{port}`

### Modo Docker

Si prefieres usar contenedores (recomendado para desarrollo y producción):

```bash
docker-compose up --build -d
```

Esto levantará la API y una base de datos PostgreSQL automáticamente.

## 📂 Estructura del Proyecto

```
/
├── auth/           # Rutas y lógica de autenticación (JWT)
├── controllers/    # Lógica de negocio y orquestación
├── core/           # Configuración global y manejo de excepciones
├── database/       # Conexión a BD y gestión de sesiones
├── dependencies/   # Dependencias inyectables (ej. Rate Limiter)
├── helpers/        # Funciones auxiliares generales
├── models/         # Modelos ORM (SQLAlchemy)
├── repositories/   # Capa de acceso a datos (CRUD)
├── routes/         # Definición de endpoints
├── schemas/        # Esquemas de validación (Pydantic)
├── services/       # Lógica de negocio compleja (opcional)
├── static/         # Archivos estáticos
├── utils/          # Utilidades (Logger, etc.)
└── main.py         # Punto de entrada de la aplicación
```

## 📚 Documentación

Una vez iniciada la aplicación, puedes acceder a la documentación interactiva:

- **Swagger UI**: [http://{host}:{port}/docs](http://{host}:{port}/docs)
- **ReDoc**: [http://{host}:{port}/redoc](http://{host}:{port}/redoc)

## 🤝 Contribución

1. Haz un Fork del proyecto.
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`).
3. Commit de tus cambios (`git commit -m 'Add some AmazingFeature'`).
4. Push a la rama (`git push origin feature/AmazingFeature`).
5. Abre un Pull Request.

---
Generado por **Calypso API CLI**.
"""

# ------------------------------------------------------------------------------
# PROMOTED INLINE TEMPLATES
# ------------------------------------------------------------------------------

AUTH_UTILS_PY = '''"""
auth/auth_utils.py

Este archivo contiene funciones auxiliares relacionadas con la autenticación y seguridad. 
Estas funciones son independientes y reutilizables, diseñadas para facilitar tareas comunes 
como la manipulación de datos de autenticación.

Responsabilidades principales:
- Crear y verificar sal y hashes de contraseñas.
- Generar tokens JWT con datos personalizados.
- Validar estructuras y datos relacionados con autenticación.
- Encriptar y desencriptar datos sensibles.
"""

import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt
from cryptography.fernet import Fernet
from core import config
from utils.logger import configure_logger

logger = configure_logger(name=\'auth_utils\')

def generate_salt() -> bytes:
    """Generar un salt para el hash de contraseñas."""
    return bcrypt.gensalt()

def get_password_hash(password: str, salt: bytes) -> bytes:
    """Hashear una contraseña utilizando bcrypt."""
    return bcrypt.hashpw(password.encode(\'utf-8\'), salt)

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    """Verificar si una contraseña coincide con su hash."""
    logger.info("Verificando contraseña...")
    return bcrypt.checkpw(plain_password.encode(\'utf-8\'), hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Generar un token de acceso JWT."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)

def encriptar(token: str) -> bytes:
    cipher_suite = Fernet(config.FERNET_KEY)
    try:
        token_encriptado = cipher_suite.encrypt(token.encode())
        return token_encriptado
    except Exception as e:
        logger.error(f"Error al encriptar el token: {e}")
        raise e

def desencriptar(tokenCifrado: bytes) -> str:
    cipher_suite = Fernet(config.FERNET_KEY)
    try:
        token_desencriptado = cipher_suite.decrypt(tokenCifrado).decode()
        return token_desencriptado
    except Exception as e:
        logger.error(f"Error al desencriptar el token: {e}")
        raise e
'''

AUTH_SERVICE_PY = '''"""
auth/auth_service.py

Este archivo contiene la lógica central de autenticación de la aplicación. 
Incluye funciones para manejar la generación de hashes de contraseñas, 
verificación de credenciales, autenticación de usuarios y emisión de tokens JWT. 

Responsabilidades principales:
- Generar y verificar contraseñas seguras.
- Autenticar usuarios mediante credenciales.
- Crear tokens de acceso y refresh.
- Implementar funciones para recuperar usuarios autenticados.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import Usuario
from auth.auth_utils import verify_password

async def get_user(db: AsyncSession, username: str):
    """Obtener un usuario de la base de datos por su username."""
    user = (await db.scalars(select(Usuario).where(Usuario.username == username))).first()
    return user

async def authenticate_user(db: AsyncSession, username: str, password: str):
    """Autenticar a un usuario verificando su contraseña."""
    user = await get_user(db, username)
    if not user or not verify_password(password, user.passhash):
        return None
    return user
'''

LOGGER_PY = '''"""
utils/logger.py

Este módulo configura y devuelve loggers personalizados para el proyecto.
"""
import logging
import sys

class CustomFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels."""
    COLORS = {
        \'DEBUG\': \'\\033[94m\',  # Azul
        \'INFO\': \'\\033[32m\',   # Verde
        \'WARNING\': \'\\033[94m\', # Azul
        \'ERROR\': \'\\033[91m\',  # Rojo
        \'CRITICAL\': \'\\033[95m\'# Magenta
    }
    RESET = \'\\033[0m\'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}" # Añadir color al nivel de log
        record.msg = f"{log_color}{record.getMessage()}{self.RESET}" # Añadir color al mensaje
        return super().format(record)

def configure_logger(name=\'perroBot_Logger\', level=logging.INFO, log_to_file: str = None):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = CustomFormatter(\'[%(name)s] %(levelname)s:  %(message)s\')
    
    if not logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        if log_to_file:
            file_handler = logging.FileHandler(log_to_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
    logger.propagate = False

    return logger
'''

DEFAULT_USER_PY = """from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import Usuario
from auth.auth_utils import get_password_hash, generate_salt
from core import config
from utils.logger import configure_logger

logger = configure_logger(name=__name__, level="INFO")

async def create_defaultAdmin_user(db: AsyncSession):
    logger.info("Creando usuario por defecto...")
    result = await db.scalars(select(Usuario).where(Usuario.username == config.usernameAdmin))
    default_user = result.first()
    if default_user:
        logger.warning(f"Usuario {default_user.username} ya existe.")
        return
    salt = generate_salt()
    default_user = Usuario(
        username=config.usernameAdmin,
        passhash=get_password_hash(config.passhashAdminAPI, salt),
        salt=salt,
        deshabilitado=False,
        isAdmin=True,
    )
    db.add(default_user)
    try:
        await db.commit()
        logger.info(f"Usuario por defecto creado: {default_user.username}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al crear usuario por defecto: {e}")
"""

# ------------------------------------------------------------------------------
# ENV / DOCKER / REQUIREMENTS TEMPLATES
# ------------------------------------------------------------------------------

ENV_TEMPLATE = """# API
API_KEY="{api_key}"
X_API_KEY="{x_api_key}"
DOCS_API_KEY="{docs_api_key}"
SECRET_KEY="{secret_key}"
FERNET_KEY="{fernet_key}"
ALGORITHM="{algorithm}"
APP_ENV="{app_env}"

# Base de datos local
usernameDBLocal="{db_local_username}"
passwordDBLocal="{db_local_password}"
servernameDBLocal="{db_local_server}"
databasenameDBLocal="{db_local_dbname}"

# Base de datos produccion
usernameDB="{db_prod_username}"
passwordDB="{db_prod_password}"
servernameDB="{db_prod_server}"
databasenameDB="{db_prod_dbname}"

# Usuario admin
usernameAdmin="{admin_username}"
passhashAdminAPI="{admin_password}"

# PerroBot
passhashAdmin="{passhash_admin_bot}"
"""

SSHD_CONFIG = """Port 			2222
ListenAddress 		0.0.0.0
LoginGraceTime 		180
X11Forwarding 		yes
Ciphers aes128-cbc,3des-cbc,aes256-cbc,aes128-ctr,aes192-ctr,aes256-ctr
MACs hmac-sha1,hmac-sha1-96
StrictModes 		yes
SyslogFacility 		DAEMON
PasswordAuthentication 	yes
PermitEmptyPasswords 	no
PermitRootLogin 	yes
Subsystem sftp internal-sftp
"""

DOCKERFILE_BASE = """FROM python:3.12-alpine

LABEL maintainer="calypso"

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_NO_CACHE_DIR=off \\
    PIP_DISABLE_PIP_VERSION_CHECK=on \\
    PIP_DEFAULT_TIMEOUT=100 \\
    VIRTUAL_ENV=/usr/local \\
    TZ="Europe/Madrid"

WORKDIR /app/

COPY . .

RUN pip install uv==0.11.8
RUN apk add --no-cache git build-base postgresql-dev libffi-dev \\
 && uv pip install --system -r requirements.txt \\
 && rm -rf /root/.cache

RUN apk add --no-cache bash dos2unix
RUN dos2unix /app/init_container.sh && chmod +x /app/init_container.sh

RUN apk add --no-cache dialog openssh
RUN echo "root:Docker!" | chpasswd \\
    && ssh-keygen -A

COPY sshd_config /etc/ssh/

EXPOSE 80 2222 {port}

ENTRYPOINT ["bash", "init_container.sh"]
"""

PERROBOT_TOKEN = ""  # Token provided by user at generation time

DOCKERFILE_WITH_PERROBOT = """FROM python:3.12-alpine

LABEL maintainer="calypso"

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_NO_CACHE_DIR=off \\
    PIP_DISABLE_PIP_VERSION_CHECK=on \\
    PIP_DEFAULT_TIMEOUT=100 \\
    VIRTUAL_ENV=/usr/local \\
    TZ="Europe/Madrid"

WORKDIR /app/

COPY . .

RUN pip install uv==0.11.8
RUN apk add --no-cache git build-base postgresql-dev libffi-dev \\
 && uv pip install --system -r requirements.txt \\
 && rm -rf /root/.cache

RUN uv pip install --system "git+https://{perrobot_token}@github.com/triplealpha-innovation/perroBot.git@main" \\
 && rm -rf /root/.cache

RUN apk add --no-cache bash dos2unix
RUN dos2unix /app/init_container.sh && chmod +x /app/init_container.sh

RUN apk add --no-cache dialog openssh
RUN echo "root:Docker!" | chpasswd \\
    && ssh-keygen -A

COPY sshd_config /etc/ssh/

EXPOSE 80 2222 {port}

ENTRYPOINT ["bash", "init_container.sh"]
"""

INIT_CONTAINER_SH = """#!/bin/bash
echo "Iniciando ssh para poder acceder al contenedor por ssh........"
/usr/sbin/sshd &

if [ "$APP_ENV" = "production" ]; then
    echo "Iniciando {project_name} en modo $APP_ENV con gunicorn..........."
    NUM_WORKERS=$(nproc)
    echo "Número de workers: $NUM_WORKERS, uno por cada núcleo de CPU"
    exec gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:80 --workers $NUM_WORKERS
else
    echo "Iniciando {project_name} en modo desarrollo con uvicorn............"
    exec uvicorn main:app --reload --host 0.0.0.0 --port {port}
fi
"""

REQUIREMENTS_TEMPLATE = """fastapi==0.136.1
uvicorn==0.46.0
gunicorn==25.3.0
pydantic==2.13.3
sqlmodel==0.0.24
SQLAlchemy==2.0.49
asyncpg==0.31.0
contextlib2==21.6.0
slowapi==0.1.9
cryptography==47.0.0
bcrypt==5.0.0
python-jose[cryptography]
psycopg2-binary==2.9.12
python-multipart==0.0.27
httpx==0.28.1
requests==2.33.1
pytz==2026.1.post1
email-validator==2.3.0
pandas==3.0.2
pyarrow==24.0.0
orjson==3.11.8
"""

CRUD_USUARIOS_CONTROLLER_PY = '''"""
controllers/crudUsuarios_controller.py

Este archivo contiene la lógica para crear, leer, actualizar y eliminar usuarios de la api en la base de datos.

Responsabilidades principales:
    - Crear un usuario en la base de datos.
    - Actualizar un usuario en la base de datos.
    - Eliminar un usuario de la base de datos.
"""

from fastapi.responses import JSONResponse
from utils.logger import configure_logger
from repositories.crudUsuarios_repository import CrudUsuariosRepository
from services.crudUsuarios_service import CrudUsuariosService

logger = configure_logger(name=__name__)

class CrudUsuariosController:
    def __init__(self, db):
        self.db = db
        repo = CrudUsuariosRepository(db)
        self.service = CrudUsuariosService(repo)

    
    async def crear_usuario(self, usuario_dict: dict):
        """ Llama al servicio para crear un usuario en la base de datos """
        response = await self.service.crear_usuario(usuario_dict)
        
        return JSONResponse(
            status_code=201,
            content=response
        )
        
    async def listar_usuarios(self):
        """ Lista todos los usuarios de la base de datos """
        
        # Delegar la lógica al servicio
        response = await self.service.listar_usuarios()
        return response
    

    async def actualizar_usuario(self, username: str, usuario_dict: dict):
        """ Actualiza un usuario en la base de datos """
        
        # Delegar la actualización al servicio
        response = await self.service.actualizar_usuario(username, usuario_dict)
        return response
    
    async def eliminar_usuario(self, username: str):
        """ Elimina un usuario de la base de datos """
        
        # Delegar la eliminación al servicio
        response = await self.service.eliminar_usuario(username)
        return response
'''

CRUD_USUARIOS_REPOSITORY_PY = '''"""
repositories/crudUsuarios_repository.py

Este repositorio define las operaciones de acceso a datos para el CRUD de usuarios en la API.

Responsabilidades:
    - Acceso a la base de datos para crear, actualizar, eliminar y listar usuarios.
"""

from core.exceptions import handle_db_exceptions
from sqlalchemy.future import select
from models.models import Usuario
from utils.logger import configure_logger

logger = configure_logger(name=__name__)

class CrudUsuariosRepository:
    def __init__(self, db):
        self.db = db
        
    @handle_db_exceptions
    async def verifica_usuario_ya_existe(self, username: str):
        """ Verifica si un usuario ya existe en la base de datos """
        
        result = await self.db.scalars(select(Usuario).where(Usuario.username == username))
        usuario = result.first()
        
        return usuario
    
    @handle_db_exceptions
    async def listar_usuarios(self):
        """ Lista todos los usuarios de la base de datos """
        result = await self.db.scalars(select(Usuario))
        usuarios = result.all()
        return usuarios
    
        
    @handle_db_exceptions
    async def eliminar_usuario(self, usuario: Usuario):
        """ Elimina un usuario de la base de datos """
        await self.db.delete(usuario)
        await self.db.commit()

        logger.warning(f"¡Usuario {usuario.username} eliminado de la base de datos!")
        return {"mensaje": f"¡Usuario {usuario.username} eliminado correctamente!"}
'''

CRUD_USUARIOS_SERVICE_PY = '''"""
services/crudUsuarios_service.py

Este servicio define la lógica de negocio para el CRUD de usuarios en la API.

Responsabilidades:
    - Crear un usuario en la base de datos.
    - Actualizar un usuario en la base de datos.
    - Eliminar un usuario de la base de datos.
    - Listar todos los usuarios de la base de datos.
"""

from fastapi import HTTPException
from models.models import Usuario
from repositories.crudUsuarios_repository import CrudUsuariosRepository
from auth.auth_utils import get_password_hash, generate_salt
from utils.logger import configure_logger

logger = configure_logger(name=__name__)

class CrudUsuariosService:
    def __init__(self, repo: CrudUsuariosRepository):
        self.repo = repo
        
    
    async def crear_usuario(self, usuario_dict: dict):
        """ Crea un usuario en la base de datos """

        # Verifica si el usuario ya existe
        usuario_db = await self.repo.verifica_usuario_ya_existe(usuario_dict[\'username\'])
        if usuario_db:
            raise HTTPException(
                status_code=400,
                detail=f"El usuario {usuario_dict[\'username\']} ya existe."
            )

        salt = generate_salt()
        usuario_dict[\'passhash\'] = get_password_hash(usuario_dict[\'passhash\'], salt)
        usuario_dict[\'salt\'] = salt

        nuevo_usuario = Usuario(**usuario_dict)
        self.repo.db.add(nuevo_usuario)
        await self.repo.db.commit()

        logger.info(f"¡Usuario {usuario_dict[\'username\']} creado correctamente!")
        
        return {
            "mensaje": f\'¡Usuario {usuario_dict["username"]} creado correctamente!\',
            "username": usuario_dict["username"]
        }
        
    async def listar_usuarios(self):
        """ Lista todos los usuarios de la base de datos """
        
        # Delegar la lógica al repositorio
        usuarios = await self.repo.listar_usuarios()

        if not usuarios:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron usuarios en la base de datos."
            )

        return usuarios

    async def actualizar_usuario(self, username: str, usuario_dict: dict):
        """ Actualiza un usuario en la base de datos """
        
        # Verifica si el usuario existe
        usuario_db = await self.repo.verifica_usuario_ya_existe(username)
        if not usuario_db:
            raise HTTPException(
                status_code=404,
                detail=f"El usuario {username} no fue encontrado."
            )
        
        # Genera nuevo salt y hash para la contraseña
        salt = generate_salt()
        usuario_dict[\'passhash\'] = get_password_hash(usuario_dict[\'passhash\'], salt)
        usuario_dict[\'salt\'] = salt

        # Actualiza los campos del usuario
        usuario_db.username = usuario_dict[\'username\']
        usuario_db.passhash = usuario_dict[\'passhash\']
        usuario_db.salt = usuario_dict[\'salt\']
        usuario_db.deshabilitado = usuario_dict[\'deshabilitado\']
        usuario_db.isAdmin = usuario_dict[\'isAdmin\']

        # Delega la actualización al repositorio
        self.repo.db.add(usuario_db) 
        await self.repo.db.commit()

        logger.info(f"¡Usuario {username} actualizado correctamente!")
        
        return {
            "mensaje": f\'¡Usuario {username} actualizado correctamente!\',
            "username": username
        }
    
    async def eliminar_usuario(self, username: str):
        """ Elimina un usuario en la base de datos """
        
        # Verifica si el usuario existe
        usuario_db = await self.repo.verifica_usuario_ya_existe(username)
        if not usuario_db:
            raise HTTPException(
                status_code=404,
                detail=f"El usuario {username} no fue encontrado."
            )

        # Delega la eliminación al repositorio
        await self.repo.eliminar_usuario(usuario_db)
        logger.warning(f"¡Usuario {username} eliminado de la base de datos!")
        
        return {
            "mensaje": f\'¡Usuario {username} eliminado correctamente!\',
            "username": username
        }
'''

CRUD_USUARIOS_ROUTER_PY = '''"""
routes/crudUsuarios_router.py

Este archivo define las rutas para las entidades relacionadas con el CRUD de usuarios.

Responsabilidades:
    - Define las rutas para el CRUD de usuarios.
"""

from fastapi import APIRouter, Depends, Request, Security
from dependencies.limitador import limiter
from controllers.crudUsuarios_controller import CrudUsuariosController
from dependencies import constants_descriptions
from dependencies.controllers_dependencies_inject import get_crud_usuarios_controller
from schemas.schemas import UserInResponse
from auth.auth_dependencies import get_current_admin_user, get_api_key_query

router = APIRouter(
    tags=["CRUD de Usuarios | Router Admin"],
    prefix="/usuarios",
    dependencies=[Security(get_current_admin_user)]
)

@router.post(
    "/crearUsuario",
    description=constants_descriptions.DESCRIPTIONS["crearUsuario"],
    status_code=201
)
@limiter.limit("60/minute")
async def crearUsuario(
    request: Request,
    usuario_in: UserInResponse,
    controller: CrudUsuariosController = Depends(get_crud_usuarios_controller)
):
    """Crea un nuevo usuario en la base de datos."""
    
    usuario_dict = usuario_in.model_dump()
    return await controller.crear_usuario(usuario_dict=usuario_dict)


@router.put(
    "/actualizarUsuario",
    description=constants_descriptions.DESCRIPTIONS["actualizarUsuario"],
    status_code=200
)
@limiter.limit("60/minute")
async def actualizarUsuario(
    request: Request,
    username: str,
    usuario_in: UserInResponse,
    controller: CrudUsuariosController = Depends(get_crud_usuarios_controller)
):
    """Actualiza un usuario en la base de datos."""
    
    usuario_dict = usuario_in.model_dump(exclude_unset=True)
    return await controller.actualizar_usuario(username=username, usuario_dict=usuario_dict)


@router.get(
    "/listarUsuarios",
    description=constants_descriptions.DESCRIPTIONS["listarUsuarios"],
    status_code=200,
    response_model=list[UserInResponse]
)
@limiter.limit("60/minute")
async def listarUsuarios(
    request: Request,
    controller: CrudUsuariosController = Depends(get_crud_usuarios_controller)
):
    """Lista todos los usuarios de la base de datos."""
    
    return await controller.listar_usuarios()


@router.delete(
    "/eliminarUsuario",
    description=constants_descriptions.DESCRIPTIONS["eliminarUsuario"],
    status_code=200
)
@limiter.limit("60/minute")
async def eliminarUsuario(
    request: Request,
    username: str,
    api_key: str = Depends(get_api_key_query),
    controller: CrudUsuariosController = Depends(get_crud_usuarios_controller)
):
    """Elimina un usuario de la base de datos."""
    
    return await controller.eliminar_usuario(username=username)
'''

CONSTANTS_DESCRIPTIONS_PY = '''"""
dependencies/constants_descriptions.py

Descripciones centralizadas de los endpoints de la API para documentación Swagger/OpenAPI.
"""

DESCRIPTIONS = {
    # ── Usuarios ──
    "crearUsuario": "Crea un nuevo usuario en la base de datos.",
    "actualizarUsuario": "Actualiza un usuario en la base de datos.",
    "eliminarUsuario": "Es necesario utilizar API_KEY en el header para esta operación. Elimina un usuario de la base de datos.",
    "listarUsuarios": "Lista todos los usuarios de la base de datos."
}
'''

CONTROLLERS_DEPENDENCIES_INJECT_PY = '''"""
dependencies/controllers_dependencies_inject.py

Este archivo define las dependencias necesarias para inyectar los controladores en las rutas de la API.

Responsabilidades principales:
- Inyectar todas las instancias de controladores con sus dependencias (sesiones de BD).
- Proporcionar factory functions para cada controlador de tablas de datos.
"""

from database.db_service import DBSessionAsyncDependency
from controllers.crudUsuarios_controller import CrudUsuariosController

# ================================================================
# Factory Functions
# ================================================================
def get_crud_usuarios_controller(db: DBSessionAsyncDependency) -> CrudUsuariosController:
    return CrudUsuariosController(db=db)
'''

VALIDATE_DATAFRAME_HELPER_PY = '''"""
helpers/validate_dataframe_helper.py

Este módulo contiene la clase DataFrameValidator, que se encarga de validar un DataFrame de pandas contra un esquema definido en un modelo de datos.

Responsabilidades principales:
    - Validar la presencia de columnas requeridas en el DataFrame.
    - Verificar que no existan columnas adicionales no permitidas.
    - Comprobar que los tipos de datos de las columnas coincidan con los tipos esperados según el esquema.
"""


import pandas as pd
from pandas.api.types import (
    is_integer_dtype,
    is_float_dtype,
    is_bool_dtype,
    is_string_dtype,
    is_datetime64_any_dtype,
)
from datetime import datetime
from utils.logger import configure_logger

logger = configure_logger(name=__name__, level="INFO")

class DataFrameValidator:
    @staticmethod
    def _is_datetime_series(series: pd.Series) -> bool:
        try:
            if is_datetime64_any_dtype(series):
                return True
        except Exception:
            pass
        try:
            first_valid_index = series.first_valid_index()
            if first_valid_index is not None:
                sample = series.loc[first_valid_index]
                if isinstance(sample, (pd.Timestamp, datetime)):
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def validate(df: pd.DataFrame, schema):
        logger.info("Iniciando validación del DataFrame contra el esquema.")
        expected_fields = schema.model_fields.keys()
        missing = set(expected_fields) - set(df.columns)
        extra = set(df.columns) - set(expected_fields)
        if missing:
            logger.error(f"Faltan columnas requeridas: {missing}")
            raise ValueError(f"Faltan columnas requeridas: {missing}")
        if extra:
            logger.error(f"Columnas no permitidas en el archivo: {extra}")
            raise ValueError(f"Columnas no permitidas en el archivo: {extra}")
        for field, field_info in schema.model_fields.items():
            if field in df.columns:
                expected_type = field_info.annotation
                series = df[field]
                origin = getattr(expected_type, \'__origin__\', None)
                if origin is not None and origin is not type(None):
                    for t in expected_type.__args__:
                        if t is not type(None):
                            expected_type = t
                            break
                if expected_type == int:
                    non_null = series.dropna()
                    if non_null.empty:
                        pass
                    elif is_integer_dtype(series):
                        pass
                    elif is_float_dtype(series):
                        vals = pd.to_numeric(non_null, errors=\'coerce\')
                        mask = pd.notna(vals)
                        if ((vals[mask] % 1) == 0).all():
                            pass
                        else:
                            logger.error(f"Columna \'{field}\' debe ser de tipo entero")
                            raise ValueError(f"Columna \'{field}\' debe ser de tipo entero")
                    elif str(series.dtype) == \'object\':
                        vals = pd.to_numeric(non_null, errors=\'coerce\')
                        mask = pd.notna(vals)
                        if ((vals[mask] % 1) == 0).all():
                            pass
                        else:
                            logger.error(f"Columna \'{field}\' debe ser de tipo entero")
                            raise ValueError(f"Columna \'{field}\' debe ser de tipo entero")
                    else:
                        logger.error(f"Columna \'{field}\' debe ser de tipo entero")
                        raise ValueError(f"Columna \'{field}\' debe ser de tipo entero")
                elif expected_type == float:
                    if not is_float_dtype(series):
                        logger.error(f"Columna \'{field}\' debe ser de tipo flotante")
                        raise ValueError(f"Columna \'{field}\' debe ser de tipo flotante")
                elif expected_type == bool:
                    if not is_bool_dtype(series):
                        logger.error(f"Columna \'{field}\' debe ser de tipo booleano")
                        raise ValueError(f"Columna \'{field}\' debe ser de tipo booleano")
                elif expected_type == str:
                    non_null = series.dropna()
                    if non_null.empty:
                        pass
                    elif is_string_dtype(series) or str(series.dtype) == \'object\':
                        pass
                    else:
                        logger.error(f"Columna \'{field}\' debe ser de tipo string")
                        raise ValueError(f"Columna \'{field}\' debe ser de tipo string")
                elif getattr(expected_type, "__name__", "") == "datetime" or expected_type is datetime:
                    if not DataFrameValidator._is_datetime_series(series):
                        logger.error(f"Columna \'{field}\' debe ser de tipo datetime")
                        raise ValueError(f"Columna \'{field}\' debe ser de tipo datetime")
        logger.info("Validación del DataFrame completada exitosamente.")
'''

INSERTA_REGISTROS_REPOSITORY_PY = '''"""
repositories/inserta_registros_repository.py

Inserta registros en la base de datos.

Responsabilidades:
    - Insertar registros en la base de datos.
"""
from core.exceptions import handle_db_exceptions
import io
import pyarrow.parquet as pq
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from fastapi import BackgroundTasks
from utils.logger import configure_logger

logger = configure_logger(name=__name__, level="INFO")

class InsertaRegistros:
    
    def __init__(self, db):
        self.db = db
        self.max_params = 32767  # Límite de asyncpg
        
    @handle_db_exceptions
    async def inserta_registros(self, tabla, contents, background_tasks: BackgroundTasks, schema=None):
        """Inserta registros en la tabla especificada. En batch y en segundo plano."""
        logger.info(f"Iniciando tarea en segundo plano para insertar registros en la tabla {tabla.__tablename__}")
        background_tasks.add_task(self._inserta_registros_task, tabla, contents, schema)

    @handle_db_exceptions
    async def _inserta_registros_task(self, tabla, contents, schema=None):
        """Tarea en segundo plano para insertar registros en la tabla especificada."""
        logger.info(f"Tarea en segundo plano iniciada para la tabla {tabla.__tablename__}")
        table = pq.read_table(io.BytesIO(contents))
        records = table.to_pylist()
        num_columnas = len(table.column_names)
        batch_size = self.max_params // num_columnas
        batch_size = min(batch_size, len(records))
        total_registros = len(records)
        logger.info(f"Total de registros a insertar en {tabla.__tablename__}: {total_registros} (Batch size: {batch_size})")
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            insert_stmt = postgres_insert(tabla).values(batch)
            do_nothing_stmt = insert_stmt.on_conflict_do_nothing()
            await self.db.execute(do_nothing_stmt)
        await self.db.commit()
        logger.info(f"Registros insertados correctamente en la tabla {tabla.__tablename__}")
'''

ACTUALIZA_REGISTROS_REPOSITORY_PY = '''"""
repositories/actualiza_registros_repository.py

Actualiza registros en la base de datos.

Responsabilidades:
    - Actualizar registros en la base de datos.
"""

from core.exceptions import handle_db_exceptions
import io
import pyarrow.parquet as pq
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from fastapi import BackgroundTasks
from utils.logger import configure_logger
from core import config
import logging

try:
    from perroBot.enviaLogs import EnviaLogs
    loggerteams = EnviaLogs(level=logging.INFO)
except ImportError:
    loggerteams = None

logger = configure_logger(name=__name__, level="INFO")

class ActualizaRegistros:
    
    def __init__(self, db):
        self.db = db
        self.max_params = 32767  # Límite de asyncpg
        
    @handle_db_exceptions
    async def actualiza_registros(self, tabla, contents, background_tasks: BackgroundTasks, columnas_conflicto: list[str]):
        """Actualiza registros dinámicamente en función de los datos. En batch y en segundo plano."""
        logger.info(f"Iniciando tarea en segundo plano para actualizar registros en la tabla {tabla.__tablename__}")
        background_tasks.add_task(self._actualiza_registros_task, tabla, contents, columnas_conflicto)

    @handle_db_exceptions
    async def _actualiza_registros_task(self, tabla, contents, columnas_conflicto: list[str]):
        logger.info(f"Tarea en segundo plano iniciada para actualizar la tabla {tabla.__tablename__}")
        table = pq.read_table(io.BytesIO(contents))
        records = table.to_pylist()
        num_columnas = len(table.column_names)
        batch_size = self.max_params // num_columnas
        batch_size = min(batch_size, len(records))
        total_registros = len(records)
        logger.info(f"Total de registros a actualizar en {tabla.__tablename__}: {total_registros} (Batch size: {batch_size})")
        columnas_data = table.column_names
        columnas_actualizar = [col for col in columnas_data if col not in columnas_conflicto]
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            insert_stmt = postgres_insert(tabla).values(batch)
            update_dict = {
                col: insert_stmt.excluded[col] for col in columnas_actualizar if col in insert_stmt.excluded
            }
            update_stmt = insert_stmt.on_conflict_do_update(
                index_elements=columnas_conflicto,
                set_=update_dict
            )
            await self.db.execute(update_stmt)
        await self.db.commit()
        logger.info(f"Registros actualizados correctamente en la tabla {tabla.__tablename__}")

    @handle_db_exceptions
    async def sobreescribir_registros(self, tabla, contents, background_tasks: BackgroundTasks):
        """Sobreescribe todos los registros en la tabla especificada."""
        logger.info(f"Iniciando tarea en segundo plano para sobrescribir registros en la tabla {tabla.__tablename__}")
        background_tasks.add_task(self._sobreescribir_registros_task, tabla, contents)

    @handle_db_exceptions
    async def _sobreescribir_registros_task(self, tabla, contents):
        logger.info(f"Tarea en segundo plano iniciada para sobrescribir la tabla {tabla.__tablename__}")
        table = pq.read_table(io.BytesIO(contents))
        records = table.to_pylist()
        if len(records) == 0:
            logger.warning(f"El archivo está vacío. No se sobrescribirá la tabla {tabla.__tablename__}")
            return
        num_columnas = len(table.column_names)
        batch_size = self.max_params // num_columnas
        batch_size = min(batch_size, len(records))
        total_registros = len(records)
        logger.info(f"Total de registros a sobrescribir en {tabla.__tablename__}: {total_registros} (Batch size: {batch_size})")
        logger.info(f"Eliminando todos los registros existentes de {tabla.__tablename__}")
        await self.db.execute(tabla.__table__.delete())
        registros_insertados = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            await self.db.execute(tabla.__table__.insert().values(batch))
            registros_insertados += len(batch)
            logger.info(f"Insertados {registros_insertados}/{total_registros} registros en {tabla.__tablename__}")
        await self.db.commit()
        if config.perrobot and loggerteams:
            loggerteams.enviar_log_teams(
                nombreCliente="Calypso",
                grupo="perroBot",
                mensaje=f"Se sobrescribieron {total_registros} registros en la tabla {tabla.__tablename__} de Postgresql",
                level=logging.INFO,
                proyecto=config.PROJECT_NAME
            )
        logger.info(f"Registros sobrescritos correctamente en la tabla {tabla.__tablename__} - Total: {total_registros} registros")
'''

ELIMINA_REGISTROS_REPOSITORY_PY = '''"""
repositories/elimina_registros_repository.py

Este archivo contiene dependencias comunes para los controladores.
Elimina registros en la base de datos.

Responsabilidades:
    - Eliminar registros en la base de datos por claves primarias.
"""

from core.exceptions import handle_db_exceptions
from sqlalchemy import delete
from fastapi import BackgroundTasks
from utils.logger import configure_logger
from typing import List, Any

logger = configure_logger(name=__name__, level="INFO")

class EliminaRegistros:
    
    def __init__(self, db):
        self.db = db

    @handle_db_exceptions
    async def elimina_registros_por_claves(self, tabla, claves_primarias: List[Any], background_tasks: BackgroundTasks, nombre_columna_clave: str):
        """Elimina registros dinámicamente por claves primarias. En batch y en segundo plano."""
        logger.info(f"Iniciando tarea en segundo plano para eliminar registros en la tabla {tabla.__tablename__}")
        background_tasks.add_task(self._elimina_registros_task, tabla, claves_primarias, nombre_columna_clave)

    @handle_db_exceptions
    async def _elimina_registros_task(self, tabla, claves_primarias: List[Any], nombre_columna_clave: str):
        """Tarea en segundo plano para eliminar registros por claves primarias."""
        logger.info(f"Tarea en segundo plano iniciada para eliminar registros de la tabla {tabla.__tablename__}")
        
        total_registros = len(claves_primarias)
        logger.info(f"Total de registros a eliminar en {tabla.__tablename__}: {total_registros}")

        # Obtener la columna de clave primaria de la tabla
        columna_clave = getattr(tabla, nombre_columna_clave)
        
        # Crear la consulta de eliminación
        stmt = delete(tabla).where(columna_clave.in_(claves_primarias))
        
        # Ejecutar la eliminación
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        registros_eliminados = result.rowcount
        logger.info(f"Eliminación completada en {tabla.__tablename__}. Registros eliminados: {registros_eliminados}")
'''

PATCH_REGISTROS_REPOSITORY_PY = '''"""
repositories/patch_registros_repository.py

Este archivo contiene el repositorio genérico para operaciones PATCH.
Permite actualizar campos específicos de cualquier modelo de manera genérica.

Responsabilidades:
    - Actualizar campos específicos por clave primaria de manera genérica
    - Manejar validaciones de existencia de registros
    - Proporcionar funcionalidad reutilizable para operaciones PATCH
"""

from core.exceptions import handle_db_exceptions
from sqlalchemy import update, select
from utils.logger import configure_logger
from typing import Dict, Any, Optional
from fastapi import HTTPException

logger = configure_logger(name=__name__, level="INFO")

class PatchRegistros:
    
    def __init__(self, db):
        self.db = db

    @handle_db_exceptions
    async def patch_registro_generico(
        self, 
        model_class, 
        primary_key_value: str, 
        campos_actualizar: Dict[str, Any], 
        primary_key_name: str = None
    ) -> bool:
        """
        Actualiza campos específicos de un registro de manera genérica.
        
        Args:
            model_class: Clase del modelo SQLAlchemy
            primary_key_value: Valor de la clave primaria del registro a actualizar
            campos_actualizar: Diccionario con los campos y valores a actualizar
            primary_key_name: Nombre de la columna de clave primaria (opcional, se detecta automáticamente)
            
        Returns:
            bool: True si se actualizó el registro, False si no se encontró
            
        Raises:
            HTTPException: Si no se encuentran claves primarias en el modelo
        """
        # Si no se especifica el nombre de la columna, extraemos la primera clave primaria del modelo
        if primary_key_name is None:
            primary_key_columns = [key.name for key in model_class.__table__.primary_key.columns]
            if not primary_key_columns:
                raise HTTPException(
                    status_code=500, 
                    detail=f"No se encontraron claves primarias en la tabla {model_class.__tablename__}"
                )
            primary_key_name = primary_key_columns[0]
        campos_filtrados = {k: v for k, v in campos_actualizar.items() if v is not None}
        
        if not campos_filtrados:
            logger.warning(f"No hay campos para actualizar en {model_class.__tablename__}")
            return False
        primary_key_column = getattr(model_class, primary_key_name)
        
        # Crear la consulta de actualización
        stmt = (
            update(model_class)
            .where(primary_key_column == primary_key_value)
            .values(**campos_filtrados)
        )
        # Ejecutar la actualización
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        registros_actualizados = result.rowcount
        if registros_actualizados > 0:
            logger.info(f"Registro actualizado en {model_class.__tablename__}. Clave: {primary_key_value}")
            return True
        else:
            logger.warning(f"No se encontró registro con {primary_key_name}={primary_key_value} en {model_class.__tablename__}")
            return False

    @handle_db_exceptions
    async def verificar_existencia_registro(
        self, 
        model_class, 
        primary_key_value: str, 
        primary_key_name: str = None
    ) -> bool:
        """
        Verifica si existe un registro con la clave primaria especificada.
        
        Args:
            model_class: Clase del modelo SQLAlchemy
            primary_key_value: Valor de la clave primaria a verificar
            primary_key_name: Nombre de la columna de clave primaria (opcional)
            
        Returns:
            bool: True si existe el registro, False si no existe
        """
        # Si no se especifica el nombre de la columna, extraemos la primera clave primaria del modelo
        if primary_key_name is None:
            primary_key_columns = [key.name for key in model_class.__table__.primary_key.columns]
            if not primary_key_columns:
                raise HTTPException(
                    status_code=500, 
                    detail=f"No se encontraron claves primarias en la tabla {model_class.__tablename__}"
                )
            primary_key_name = primary_key_columns[0]
        primary_key_column = getattr(model_class, primary_key_name)
        
        # Crear la consulta de verificación
        stmt = select(model_class).where(primary_key_column == primary_key_value)
        
        # Ejecutar la consulta
        result = await self.db.execute(stmt)
        registro = result.scalar_one_or_none()
        
        return registro is not None

    @handle_db_exceptions
    async def obtener_registro_por_clave(
        self, 
        model_class, 
        primary_key_value: str, 
        primary_key_name: str = None
    ) -> Optional[Any]:
        """
        Obtiene un registro completo por su clave primaria.
        
        Args:
            model_class: Clase del modelo SQLAlchemy
            primary_key_value: Valor de la clave primaria
            primary_key_name: Nombre de la columna de clave primaria (opcional)
            
        Returns:
            El registro encontrado o None si no existe
        """
        # Si no se especifica el nombre de la columna, extraemos la primera clave primaria del modelo
        if primary_key_name is None:
            primary_key_columns = [key.name for key in model_class.__table__.primary_key.columns]
            if not primary_key_columns:
                raise HTTPException(
                    status_code=500, 
                    detail=f"No se encontraron claves primarias en la tabla {model_class.__tablename__}"
                )
            primary_key_name = primary_key_columns[0]
        primary_key_column = getattr(model_class, primary_key_name)
        
        # Crear la consulta
        stmt = select(model_class).where(primary_key_column == primary_key_value)
        
        # Ejecutar la consulta
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
'''

FAVICON_ICO_B64 = (
    'AAABAAQAICAAAAEAIACoEAAARgAAACAgAAABAAgAqAgAAO4QAAAQEAAAAQAgAGgEAACWGQAAEBAA'
    'AAEACABoBQAA/h0AACgAAAAgAAAAQAAAAAEAIAAAAAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1//EAZS/koDT/6KAU3+uAJN/tIB'
    'TP7eAUz+3gJO/tQCTv65A0/+igZP/koPT/8QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1f/IANP/ooCTf7jAU//'
    '/wBQ//8AT///AE///wBO//8ATv//AE///wBP//8AUP//AE///wJO/uQDTv6MB0//IAAAAAAAAAAA'
    'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJEj+BwRO/nUB'
    'Tv7uAFD//wBO//8ATf//AE3//wBN//8ATf//AE3//wBN//8ATf//AE3//wBN//8ATf//AE7//wBQ'
    '//8BTf7vBFD+eR9f/wgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    'AAhX/h0CTv68AFD//wBO//8ATf//AE3//wBN//8ATf//AE3//wBN//8ATf//AE3//wBN//8ATf//'
    'AE3//wBN//8ATf//AE3//wBO//8AUf//Ak/+vghS/h8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    'AAAAAAAAAAAAAAAATf4kAU7+1wBQ//8ATP//AEf//wBG//8ARv//AEn//wBN//8ATf//AE3//wBN'
    '//8ATf//AE3//wBN//8ATf//AE3//wBI//8ARv//AEb//wBK//8AUP//Ak7+2RFT/isAAAAAAAAA'
    'AAAAAAAAAAAAAAAAAAAAAAAAAAAACE/+HQFN/tUAUP//AEv//wlR//9Ziv//mLf//4+w//8rav//'
    'AEb//wBL//8ATf//AE3//wBN//8ATf//AE3//wBN//8ASv//QXn//5Ky//96ov//ImP//wBJ//8A'
    'UP//Ak/+1whM/x4AAAAAAAAAAAAAAAAAAAAAAAAAACpV/wYBTv64AFD//wBL//8MVf//u87/////'
    '//////////////L1//9/pf//DFP//wBH//8ATf//AE3//wBN//8ATf//AEv//xZa///m7f//////'
    '///////l7P//JGX//wBK//8AUP//Ak7+vCRI/gcAAAAAAAAAAAAAAAAAAAAABFD+dQBQ//8ATf//'
    'AEn//zRw///+/v/////////////////////////////T3///R37//wBH//8ASv//AE3//wBN//8A'
    'R///VIX///////////////////////9Aef//AEj//wBN//8AUP//BFD+eQAAAAAAAAAAAAAAAA9U'
    '/iEBTv7qAE7//wBN//8AS///D1f//+Dp///////////////////////////////////8/f//n7v/'
    '/xte//8ARv//AEz//wBI//+lv///////////////////4er//xBX//8AS///AE3//wBO//8CTv7s'
    'DlD+IwAAAAAAAAAABVH+hwBR//8ATf//AE3//wBN//8AR///obz/////////////////////////'
    '////////////////////5u3//2KR//8ASv//D1P//+Pr//////////////////+jvf//AEf//wBN'
    '//8ATf//AE3//wBQ//8DT/6KAAAAABJb/g4BTv7dAE7//wBN//8ATf//AE3//wBH//9XiP//////'
    '/////////////////////////////////////////////////7jN//8tbP//U4b//9/o////////'
    '/////1iJ//8AR///AE3//wBN//8ATf//AE7//wJP/uEPWv8RB1L+RwBP//8ATf//AE3//wBN//8A'
    'Tf//AEr//xte///s8f//////////////////8vb///j6//////////////////////////////L1'
    '//9ynP//HF///5Cx///n7f//HV///wBK//8ATf//AE3//wBN//8ATf//AU///wZR/ksDT/6GAFD/'
    '/wBN//8ATf//AE3//wBN//8ATf//AEn//7XK///////////////////R3v//VYf//9rl////////'
    '///////////////////////////K2f//OnX//x9g//8DTP//AE3//wBN//8ATf//AE3//wBN//8A'
    'UP//A1D+iQJP/rQAT///AE3//wBN//8ATf//AE3//wBN//8ARv//bJb///////////////////z9'
    '//8waf//DFP//5Ky///6+//////////////////////////////6+///kLH//xRZ//8ARv//AEz/'
    '/wBN//8ATf//AE3//wBP//8CTv64Ak7+0ABP//8ATf//AE3//wBN//8ATf//AE3//wBJ//8paP//'
    '9/n//////////////////3yi//8AQ///AEb//z94///O3P//////////////////////////////'
    '////3+j//1aI//8BSf//AEn//wBN//8ATf//AE///wJP/tQCTv7dAE7//wBN//8ATf//AE3//wBN'
    '//8ATf//AEz//wJN///I1///////////////////xNX//wBM//8ATP//AEf//whQ//93oP//8/b/'
    '/////////////////////////////////6zE//8iY///AEb//wBM//8ATv//AU7+3QFO/t0ATv//'
    'AE3//wBN//8ATf//AE3//wBN//8ATf//AEb//4Gl///////////////////2+P//J2f//wBJ//8A'
    'S///G17//zZx//8nZ///us7//////////////////////////////////+zx//9plf//AU3//wBO'
    '//8BTf7dAk7+0ABP//8ATf//AE3//wBN//8ATf//AE3//wBN//8ASP//OnP///7+////////////'
    '//////9qlf//AEb//wBG//9lkv///////42v//8SWP//YpD//+vx////////////////////////'
    '//////////9De///AEn//wJO/tQCT/63AE///wBN//8ATf//AE3//wBN//8ATf//AE3//wBM//8K'
    'Uv//2OP//////////////////7XK//8ASf//AEj//67F/////////////9zm//9Ee///HWD//6zE'
    '/////////////////////////////z13//8ASv//Ak/+ugNO/4gAUP//AE3//wBN//8ATf//AE3/'
    '/wBN//8ATf//AE3//wBG//+Xtf//////////////////7fL//xlc//8SWP//6O7/////////////'
    '/////5i2//8AQ///AUn//1eJ///g6f////////////+0yv//Ak7//wBP//8DUP6MBlH+SwFP//8A'
    'Tf//AE3//wBN//8ATf//AE3//wBN//8ATf//AEf//02A////////////////////////UYT//0V7'
    '////////////////////////TID//wBH//8ATP//AEb//xhc//+OsP//kLH//xVZ//8ASv//AE//'
    '/wZP/k0PWv8RAk/+4QBO//8ATf//AE3//wBN//8ATf//AE3//wBN//8AS///FFn//+bt////////'
    '//////////+duf//kbD//////////////////+Xs//8UWf//AEv//wBN//8ATf//AEv//wBH//8A'
    'Rv//AEv//wBO//8BTv7iD0v/EQAAAAADUP6LAFD//wBN//8ATf//AE3//wBN//8ATf//AE3//wBN'
    '//8ASP//q8P//////////////////+nv///l7P//////////////////qcH//wBI//8ATf//AE3/'
    '/wBN//8ATf//AE3//wBN//8ATf//AFD//wNQ/o4AAAAAAAAAAAdQ/iMBTv7tAE7//wBN//8ATf//'
    'AE3//wBN//8ATf//AE3//wBG//9hj/////////////////////////////////////////////9e'
    'jf//AEb//wBN//8ATf//AE3//wBN//8ATf//AE3//wBO//8BT/7uBlL+JQAAAAAAAAAAAAAAAARQ'
    '/nwAUP//AE3//wBN//8ATf//AE3//wBN//8ATf//AEr//yJj///y9f//////////////////////'
    '////////////8PT//x9h//8ASv//AE3//wBN//8ATf//AE3//wBN//8ATf//AFD//wRQ/n8AAAAA'
    'AAAAAAAAAAAAAAAAHFT+CQJO/8AAUP//AE3//wBN//8ATf//AE3//wBN//8ATf//AEv//7/R////'
    '//////////////////////////////+7zv//AEr//wBN//8ATf//AE3//wBN//8ATf//AE3//wBQ'
    '//8CTv7DGUz/CgAAAAAAAAAAAAAAAAAAAAAAAAAAB1L/IgJO/t0AT///AE3//wBN//8ATf//AE3/'
    '/wBN//8ARv//dp7//////////////////////////////////3Ga//8ARv//AE3//wBN//8ATf//'
    'AE3//wBN//8AT///Ak7+3wdN/iQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAClX/MAJO/t8A'
    'UP//AE3//wBN//8ATf//AE3//wBK//8lZf//6O/////////////////////////j6///IGH//wBK'
    '//8ATf//AE3//wBN//8ATf//AFD//wJO/uAFT/8wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    'AAAAAAAAAAAAB1L/IgJO/sYAUf//AE7//wBN//8ATf//AE3//wBJ//8raf//kbH//7zQ//+5zv//'
    'iKv//yRk//8ASf//AE3//wBN//8ATf//AE7//wBQ//8CTv7HB1T+JAAAAAAAAAAAAAAAAAAAAAAA'
    'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAF1z+CwVO/oIBTf7zAFD//wBO//8ATf//AE3//wBJ'
    '//8ARv//AEr//wBJ//8ARv//AEr//wBN//8ATf//AE7//wBQ//8BTv70A0/+gxdc/gsAAAAAAAAA'
    'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA1U/icDTv6W'
    'Ak7+6gBQ//8AUP//AE///wBO//8ATP//AEz//wBO//8AT///AFD//wBQ//8BTv7qA0/+lwZO/icA'
    'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    'AAAAAAAAAAAAAAAAAAALUf4WBlH/VQNO/pYCTf7CAU7+2gZQ/vcHUP75AU7+2wJN/sIDT/6XBVL+'
    'VwtR/hYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//AP//+AAf//AAD/'
    '/AAAP/gAAB/wAAAP4AAAB+AAAAfAAAADgAAAAYAAAAGAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    'AAAAAAAAAAAAAACAAAABgAAAAYAAAAHAAAAD4AAAB+AAAAfwAAAP+AAAH/wAAD/+AAB//4AB///w'
    'D/8oAAAAIAAAAEAAAAABAAgAAAAAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAEP//wBG//8AR///AEj/'
    '/wBJ//8BSf//AEr//wBL//8ATP//AE3//wFN//8ATv//AE///wFP//8CTf//A0z//wJO//8AUP//'
    'AFH//whQ//8JUf//ClL//wxT//8PU///DFX//w9X//8QV///Elj//xRZ//8VWf//Flr//xhc//8Z'
    'XP//G17//xxf//8dX///HWD//x9g//8fYf//IGH//yJj//8kZP//JGX//yVl//8nZ///KWj//ytp'
    '//8rav//LWz//zBp//80cP//NnH//zpz//86df//PXf//z94//9Aef//QXn//0N7//9Ee///RXv/'
    '/0d+//9MgP//TYD//1GE//9Thv//VIX//1WH//9WiP//V4j//1eJ//9Yif//WYr//16N//9hj///'
    'YpD//2KR//9lkv//aZX//2qV//9slv//cZr//3Kc//92nv//d6D//3qi//98ov//f6X//4Gl//+I'
    'q///ja///46w//+PsP//kLH//5Gw//+Rsf//krL//5e1//+Ytv//mLf//525//+fu///obz//6O9'
    '//+lv///qcH//6vD//+sxP//rsX//7TK//+1yv//uM3//7nO//+6zv//u87//7zQ//+/0f//xNX/'
    '/8jX///K2f//ztz//9He///T3///2OP//9rl///c5v//3+j//+Dp///h6v//4+v//+Xs///m7f//'
    '5+3//+ju///o7///6e///+vx///s8f//7fL///D0///y9f//8vb///P2///2+P//9/n///j6///6'
    '+////P3///7+////////AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA'
    'AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA'
    '/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/'
    'AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8A'
    'AAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA'
    'AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA'
    '/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/'
    'AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAAAAAAAAAAAdEw0QEAoQ'
    'EBAPFwAAAAAAAAAAAAAAAAAAAAAAAAAAEw8QEg0MCwsMDBEMEA8VAAAAAAAAAAAAAAAAAAAdDgsR'
    'CwkJCQkJCQkJCQkMDQ8XAAAAAAAAAAAAAAAAAAATDAkJCQkJCQkJCQkJCQkJCxIQFwAAAAAAAAAA'
    'AA8OEQgCAQEECAkJCQkJCQoOAwEBBg8TAAAAAAAAAAAAABAIFEhjXC8BBgkJCQkJCQY5X1YoAxEO'
    'FAAAAAAAIAoRBxhylZWVjFcWAgkJCQoHHYWUlYIpBQ8AAAAAAAAAABAEMpSVlZWVlXo9AgYJCQJC'
    'lZSVlDgGCQsTAAAAFwsLCQcZf5WVlZWVlZNlIQEIA2iVlJV/GQcKDwAAAAAADwoJCQJmlZWVlZWV'
    'lZWDTAYXgZWUlWcCCgkJERAAFBALCQkJAkWVlZWVlZWVlZWVcDBBfpSVRwIJCQoLDRsTEgsKCQkG'
    'IYmVlZWMkZWVlZWVjFIhX4UjBgkJCQkMExARCQkJCQkEbpWVlXlBfJWVlZWUlXc1JA8JCQkJDhIN'
    'DQ0KCQkJCQFQlZWVkzEWYJKVlZSVlZJcHQEICQkJCQsQDAkJCQkJBC2QlZWVVgABN3iVlJWVlZV+'
    'RAUECAsNEAsLDgkJCQkIDnaVlZV1CAgCE1SMlZWVlZWVaygBCAsQCwsJCQkJCQkBWJWVlY8sBAch'
    'MyxwlZWUlZWViU4OCwkLDQoJCQkJCQM0lJWVlU8BAU2VWhtLiJSVlZWVlToFEA0NCQkJCQkJCBV7'
    'lZWVbgMBbJWVfTsla5WUlZWVNQYKEAgGCQoKCQkJAWGVlZWJIBuFlZWVYgAFRn6VlG0FEBMXDw8H'
    'CAkJCQkCP5WVlZVAPJWVlZU+AggCH1xeIAUPExcAABMPCgoKCQccg5WVlWRelZWVghwHCQkHAQAP'
    'Dw8AAAAAAQ8HCQkLCwFqlZWVh4KVlZVpAwkJDg4PBQAAAAAAAAAAFwAPDgoJAEyVlZWVlZWVlEkB'
    'CgkIBwgPEwAAAAAAAAAPBQ4GBxAFKIyVlZWVlZWMJgYJCgUTAAAAAAAAAAAAAAAAFwATBwkHdJWV'
    'lZWVlHEGDgcHDwUPAAAXAAAAAAAAAAAPBQ8HCAFTlJSVlZWUUQIKDw8TAAAAAAAAAAAAAAAAAAAA'
    'Ew8PBiuHlJWVlIEnAwgPDwAAAAAAAAAAAAAAAAAAAAAABQ8IBC5dcXFZKQ8PAAAAAAAAAAAAAAAA'
    'AAAAAAAAAAAAAA8PBQMGBQEGCQYBAAAAAAAAAAAAAAAAAAAAAAAAABMPEg0LEQcHDRICAAAAAAAA'
    'AAAAAAAAAAAAAAAAAAAAAAATDxANExMNEBAUGAAAAAAAAAAAAAD/8A///4AB//8AAP/8AAA/+AAA'
    'H/AAAA/gAAAH4AAAB8AAAAOAAAABgAAAAYAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    'AAAAAIAAAAGAAAABgAAAAcAAAAPgAAAH4AAAB/AAAA/4AAAf/AAAP/4AAH//gAH///AP/ygAAAAQ'
    'AAAAIAAAAAEAIAAAAAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABk7+KgFO'
    '/Y8ATv3QAE396wBM/ewBTv3QAU79jwBN/isAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASP4HAU/9'
    'jQBM/foATf//AE3//wBN//8ATf//AE3//wBN//8ATf37AVD9jwBI/gcAAAAAAAAAAAAAAAAASP4H'
    'AE79swJO//88c///Lmr//wBK//8ATf//AE3//wBN//8QVf//Q3j//whR//8BTv22AEj+BwAAAAAA'
    'AAAAAU79jABM//9+pP////////v8//+Xtf//EVb//wBM//8AS///k7L///////+Rsv//AEv//wFP'
    '/Y4AAAAABlD+KQBN/fkATP//Y5D//////////////////+bt//9YiP//A0z//+Hq////////ZJH/'
    '/wBM//8ATP36BU3+KwFO/YwATf//AE3//xxd///6+/////////r7/////////////7XL//9wmv//'
    '3ef//x1e//8ATf//AE3//wFO/Y8BT/3NAE3//wBN//8ASv//x9f///////+Usv//nbr///3+////'
    '////8fX//3ig//8FTf//AEz//wBN//8BTf3PAU796gBN//8ATf//AEv//3qh////////z93//wBI'
    '//9Fev//2uX/////////////zNv//zNu//8AS///AE796wBO/eoATf//AE3//wBN//8uaf///v7/'
    '//z9//8kYv//H2D//3qh//+Lrf//+vv////////6+///a5f//wBK/esBTf3PAE3//wBN//8ATf//'
    'Akz//9vl////////bpj//2qU////////rcX//zJs///N3P///////3yj//8BTf3QAU79jwBN//8A'
    'Tf//AE3//wBL//+Rsf///////7vO//+1yv///////5Cw//8ASv//Bk7//0d7//8FTv//AU79jwBN'
    '/isATP36AE3//wBN//8ATf//Qnf////////5+///+Pr///////9Bdv//AE3//wBN//8ATf//AE39'
    '+gBR/iwAAAAAAU/9kABN//8ATf//AE3//whR///r8f/////////////q7///B1D//wBN//8ATf//'
    'AE3//wFO/ZIAAAAAAAAAAAA//wgBTv26AE3//wBN//8ASv//oLz/////////////nLn//wBK//8A'
    'Tf//AE3//wFP/bsAOP4JAAAAAAAAAAAAAAAAAD//CAFP/ZQATP38AE3//wpS//9ThP//UIH//wlQ'
    '//8ATf//AEz9/AFO/ZUAVP4JAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABUv+LwFP/ZQBTP3VAUz9'
    '8wJO/fQBT/3VAE79lQBL/i8AAAAAAAAAAAAAAAAAAAAA+B8AAOAHAADAAwAAgAEAAIABAAAAAAAA'
    'AAAAAAAAAAAAAAAAAAAAAAAAAACAAQAAgAEAAMADAADgBwAA+B8AACgAAAAQAAAAIAAAAAEACAAA'
    'AAAAAAIAAAAAAAAAAAAAAAAAAAAAAAAASP//AEr//wBL//8ATP//AE3//wBO//8DTP//Ak7//wRM'
    '//8FT///Bk7//wZP//8IUf//CVH//wlS//8LUv//EFb//xJW//8dXv//IGD//yRj//8vav//M2z/'
    '/zRu//88dP//Qnf//0N4//9Fe///SHz//1CC//9ThP//WYn//2SR//9lkf//apX//2uX//9vmP//'
    'cJr//3mg//97of//eqL//32k//9+pP//i63//5Gx//+Ssf//krL//5Sz//+Vs///l7b//525//+e'
    'uv//obz//67G//+1yv//tsv//7vP///I2P//zdz//9Dd///a5f//2+b//93n///i6v//5u7//+rw'
    '///s8f//8vb///n6///6+///+vz///z9///9/f///v7///////8AAAD/AAAA/wAAAP8AAAD/AAAA'
    '/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/'
    'AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8A'
    'AAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA'
    'AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA'
    '/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/'
    'AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8A'
    'AAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA'
    'AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA'
    '/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/'
    'AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8A'
    'AAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAA'
    'AP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA'
    '/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAAAAsJBQcFBwAAAAAAAAAAAAAIBAUEBAQDAwcPAAAADQQH'
    'GBUBBAQEERoKAAAAAAAAKklHMRACAS9KLAMJAAwFBSBJSkpAHwg/SiEEBQkEBQUSRUpFSUk3JD4S'
    'BgUJBQQEATlKMDNJSUMmCgIDBQUDBAMnSjsAGzxJSToWAAoFBgICFUlIFBMnK0RISCICBAYACAg9'
    'SiQiSTUWO0QnCgAAAAgBLUk4NkgtAAgcAAIIAAAAABlJR0RJGQAAAAAAAAAAAAgNQklIQggAAAAA'
    'AAAAAAAAADRJSjIAAAAAAAAAAAAAAwIPHh4AAAAAAAAAAAAAAAAACQcHBQkJAAAAAPgfAADgBwAA'
    'wAMAAIABAACAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAEAAIABAADAAwAA4AcAAPgfAAA='
)

# ------------------------------------------------------------------------------
# SCAFFOLD FUNCTION
# ------------------------------------------------------------------------------

def generate(
    target_dir: Path,
    name: str,
    description: str,
    host: str,
    port: int,
    modo: str,
    app_env: str,
    perrobot: bool,
    include_db_container: bool,
    db_local: dict,
    db_prod: dict | None,
    admin: dict,
    api_secrets: dict,
    passhash_admin_bot: str | None = None,
    token_perrobot: str | None = None,
) -> None:
    project_slug = name.lower().replace(" ", "_")

    # 1. Create directories
    dirs_with_init = [
        "auth", "controllers", "core", "database", "dependencies",
        "helpers", "models", "repositories", "routes", "schemas",
        "services", "static", "utils", "test"
    ]
    for d in dirs_with_init:
        (target_dir / d).mkdir(parents=True, exist_ok=True)
        _write(target_dir / d / "__init__.py", "")
    # static/img has no __init__.py
    (target_dir / "static/img").mkdir(parents=True, exist_ok=True)

    # 2. Write File Contents
    
    # --- Main ---
    _write(target_dir / "main.py", MAIN_PY)
    
    # --- Auth ---
    _write(target_dir / "auth/auth_routes.py", AUTH_ROUTES_PY)
    _write(target_dir / "auth/auth_dependencies.py", AUTH_DEPENDENCIES_PY)
    _write(target_dir / "auth/auth_utils.py", AUTH_UTILS_PY)
    _write(target_dir / "auth/auth_service.py", AUTH_SERVICE_PY)

    # --- Core ---
    config_content = (
        CORE_CONFIG_PY
        .replace("{project_name}", name)
        .replace("{description}", description)
        .replace("{modo}", modo)
        .replace("{perrobot}", str(perrobot))
    )
    _write(target_dir / "core/config.py", config_content)
    _write(target_dir / "core/exceptions.py", CORE_EXCEPTIONS_PY)
    
    # --- Database ---
    _write(target_dir / "database/db.py", DATABASE_DB_PY)
    _write(target_dir / "database/db_service.py", DATABASE_SERVICE_PY)
    
    # --- Dependencies ---
    _write(target_dir / "dependencies/limitador.py", "from slowapi import Limiter\nfrom slowapi.util import get_remote_address\nlimiter = Limiter(key_func=get_remote_address)")
    _write(target_dir / "dependencies/constants_descriptions.py", CONSTANTS_DESCRIPTIONS_PY)
    _write(target_dir / "dependencies/controllers_dependencies_inject.py", CONTROLLERS_DEPENDENCIES_INJECT_PY)
    
    # --- Models ---
    _write(target_dir / "models/models.py", MODELS_PY)
    
    # --- Repositories ---
    _write(target_dir / "repositories/consulta_tabla_repository.py", REPOSITORIES_CONSULTA_PY)
    _write(target_dir / "repositories/inserta_registros_repository.py", INSERTA_REGISTROS_REPOSITORY_PY)
    _write(target_dir / "repositories/actualiza_registros_repository.py", ACTUALIZA_REGISTROS_REPOSITORY_PY)
    _write(target_dir / "repositories/elimina_registros_repository.py", ELIMINA_REGISTROS_REPOSITORY_PY)
    _write(target_dir / "repositories/patch_registros_repository.py", PATCH_REGISTROS_REPOSITORY_PY)
    _write(target_dir / "repositories/crudUsuarios_repository.py", CRUD_USUARIOS_REPOSITORY_PY)
    
    # --- Controllers ---
    _write(target_dir / "controllers/base_controller.py", CONTROLLERS_BASE_PY)
    _write(target_dir / "controllers/crudUsuarios_controller.py", CRUD_USUARIOS_CONTROLLER_PY)
    
    # --- Routes ---
    _write(target_dir / "routes/crudUsuarios_router.py", CRUD_USUARIOS_ROUTER_PY)
    
    # --- Schemas ---
    _write(target_dir / "schemas/schemas.py", SCHEMAS_PY)
    
    # --- Utils ---
    _write(target_dir / "utils/logger.py", LOGGER_PY)
    _write(target_dir / "utils/defaultUser.py", DEFAULT_USER_PY)

    # --- Services ---
    _write(target_dir / "services/crudUsuarios_service.py", CRUD_USUARIOS_SERVICE_PY)

    # --- Helpers ---
    _write(target_dir / "helpers/validate_dataframe_helper.py", VALIDATE_DATAFRAME_HELPER_PY)

    # --- Static ---
    import base64
    (target_dir / "static/img").mkdir(parents=True, exist_ok=True)
    with open(target_dir / "static/img/favicon.ico", "wb") as _f:
        _f.write(base64.b64decode(FAVICON_ICO_B64))

    # --- Docker ---
    dockerfile = (
        DOCKERFILE_WITH_PERROBOT
        .replace("{perrobot_token}", token_perrobot or "")
        .replace("{port}", str(port))
        if perrobot else
        DOCKERFILE_BASE.replace("{port}", str(port))
    )
    _write(target_dir / "Dockerfile", dockerfile)
    _write(target_dir / "sshd_config", SSHD_CONFIG)

    # Build docker-compose programmatically
    build_section = f"build: ./{target_dir.name}"

    depends_on_section = (
        "\n    depends_on:\n"
        "      db:\n"
        "        condition: service_healthy"
        if include_db_container else ""
    )

    db_service_section = (
        "\n  db:\n"
        "    image: postgres:15-alpine\n"
        "    environment:\n"
        "      POSTGRES_USER: ${usernameDBLocal}\n"
        "      POSTGRES_PASSWORD: ${passwordDBLocal}\n"
        "      POSTGRES_DB: ${databasenameDBLocal}\n"
        "    volumes:\n"
        "      - postgres_data:/var/lib/postgresql/data\n"
        "    ports:\n"
        "      - \"5432:5432\"\n"
        "    healthcheck:\n"
        "      test: [\"CMD-SHELL\", \"pg_isready -U ${usernameDBLocal}\"]\n"
        "      interval: 5s\n"
        "      timeout: 5s\n"
        "      retries: 5"
        if include_db_container else ""
    )

    volumes_section = "\nvolumes:\n  postgres_data:\n" if include_db_container else ""

    environment_section = (
        f"\n    environment:\n"
        f"      - APP_ENV={app_env}"
    )

    docker_compose = (
        f"services:\n"
        f"  {project_slug}:\n"
        f"    container_name: {project_slug}\n"
        f"    image: acrdev{project_slug}.azurecr.io/{project_slug}:latest\n"
        f"    {build_section}\n"
        f"    env_file:\n"
        f"      - ./{target_dir.name}/.env"
        f"{environment_section}\n"
        f"    ports:\n"
        f"      - \"{port}:{port}\"\n"
        f"    volumes:\n"
        f"      - ./{target_dir.name}:/app"
        f"{depends_on_section}"
        f"{db_service_section}"
        f"{volumes_section}"
    )
    _write(target_dir.parent / "docker-compose.yml", docker_compose)

    # --- init_container.sh ---
    init_sh = (
        INIT_CONTAINER_SH
        .replace("{project_name}", name)
        .replace("{port}", str(port))
    )
    _write_lf(target_dir / "init_container.sh", init_sh)

    # --- Requirements ---
    _write(target_dir / "requirements.txt", REQUIREMENTS_TEMPLATE)

    # --- .env ---
    db_prod_data = db_prod or {"username": "", "password": "", "server": "", "dbname": ""}
    env_content = ENV_TEMPLATE.format(
        api_key=api_secrets["API_KEY"],
        x_api_key=api_secrets["X_API_KEY"],
        docs_api_key=api_secrets["DOCS_API_KEY"],
        secret_key=api_secrets["SECRET_KEY"],
        fernet_key=api_secrets["FERNET_KEY"],
        algorithm=api_secrets["ALGORITHM"],
        app_env=app_env,
        db_local_username=db_local["username"],
        db_local_password=db_local["password"],
        db_local_server=db_local["server"],
        db_local_dbname=db_local["dbname"],
        db_prod_username=db_prod_data["username"],
        db_prod_password=db_prod_data["password"],
        db_prod_server=db_prod_data["server"],
        db_prod_dbname=db_prod_data["dbname"],
        admin_username=admin["username"],
        admin_password=admin["password"],
        passhash_admin_bot=passhash_admin_bot or "",
    )
    _write(target_dir / ".env", env_content)

    # --- Main README ---
    readme_content = README_TEMPLATE.format(
        project_name=name,
        project_description=description,
        project_slug=project_slug,
        host=host,
        port=port,
    )
    _write(target_dir / "README.md", readme_content)
