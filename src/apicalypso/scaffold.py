from pathlib import Path
import os

def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
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

# Routers
from auth.auth_routes import router as security_router
from routes.example_router import router as example_router

description = f\"\"\"
# {config.PROJECT_NAME}

*{config.PROJECT_DESCRIPTION}*
\"\"\"

logger = configure_logger(name=__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    \"\"\"
    Función que maneja los eventos de inicio y cierre de la aplicación.
    \"\"\"
    if config.crear_usuarios_y_tablas:
        await create_db_and_tables()
    
        from utils.defaultUser import create_defaultAdmin_user
        from database.db_service import get_session_context
        async for session in get_session_context():
            await create_defaultAdmin_user(db=session)
            break
        
    yield
    
    if session_manager._engine is not None:
        await session_manager.close()
        logger.info("Conexión a la base de datos cerrada.")

app = FastAPI(
    title=config.PROJECT_NAME,
    description=description,
    version=config.VERSION,
    debug=config.DEBUG,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.origenes_permitidos],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(Exception, exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/img/favicon.ico")

@app.get("/", include_in_schema=False)
async def root():
    return {"mensaje": f"Bienvenido a {config.PROJECT_NAME}. Para más información, visita /docs o /redoc."}

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_favicon_url="/static/img/favicon.ico"
    )
    
@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_favicon_url="/static/img/favicon.ico"
    )

# Include Routers
app.include_router(security_router)
app.include_router(example_router)
"""

CORE_CONFIG_PY = """import os

# Define el modo de ejecución de la aplicación para seleccionar la configuración de la base de datos.
# Se puede sobreescribir con la variable de entorno MODO
Modo = os.environ.get('MODO', '{modo}')  # Modos posibles: ["Local", "Producción"]

crear_usuarios_y_tablas = True  # Crea las tablas y el usuario admin por defecto al iniciar
perrobot = {perrobot}  # Utiliza perrobot para el envío de mensajes

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

# PerroBot
passhashAdmin = os.environ.get('passhashAdmin')
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

DATABASE_DB_PY = """from sqlalchemy.ext.asyncio import (
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
        # Fallback
        async_uri = config.DATABASE_URI_ASYNC_LOCAL

session_manager = DatabaseSessionManager(
    async_uri,
    {"echo": config.DEBUG, "pool_pre_ping": True, "pool_recycle": 3600},
)
"""

DATABASE_SERVICE_PY = """from database.db import Base, session_manager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

async def create_db_and_tables():
    async with session_manager._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    async with session_manager.session() as session:
        yield session
"""

MODELS_PY = """from sqlalchemy import (
    UniqueConstraint, LargeBinary, Integer, String, Boolean
)
from sqlalchemy.orm import (
    Mapped, mapped_column
)
from database.db import Base

class Usuario(Base):
    __tablename__ = 'Usuario'

    username: Mapped[str] = mapped_column(String, primary_key=True)
    passhash: Mapped[bytes] = mapped_column(LargeBinary)
    salt: Mapped[bytes] = mapped_column(LargeBinary)
    deshabilitado: Mapped[bool] = mapped_column(Boolean, default=False)
    isAdmin: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint('username'),
        {'schema': 'public'},
    )

class ExampleModel(Base):
    __tablename__ = 'Example'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, nullable=True)
    
    __table_args__ = {'schema': 'public'}
"""

AUTH_DEPENDENCIES_PY = """from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from core import config
from auth.auth_service import get_user
from database.db_service import get_session_context
from schemas.schemas import TokenData, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session_context)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.deshabilitado:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
"""

AUTH_ROUTES_PY = """from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from auth.auth_service import authenticate_user, get_user
from auth.auth_utils import create_access_token
from auth.auth_dependencies import get_current_active_user
from database.db_service import get_session_context
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.schemas import Token
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
    user = await authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=config.REFRESH_TOKEN_EXPIRES_DAYS)

    access_token = create_access_token(
        data={"sub": user.username, "type": "access"}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": user.username, "type": "refresh"}, expires_delta=refresh_token_expires
    )

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
"""

CONTROLLERS_BASE_PY = """from fastapi.responses import JSONResponse
from fastapi import BackgroundTasks
from utils.logger import configure_logger
from core.exceptions import handle_db_exceptions
from repositories.inserta_registros_repository import InsertaRegistros
from repositories.consulta_tabla_repository import ConsultaRegistros
import pandas as pd
import io

logger = configure_logger(name=__name__, level="INFO")

class BaseController:
    def __init__(self, db, model_class):
        self.db = db
        self.model_class = model_class
        self.table_name = model_class.__tablename__
        self.inserta_registros = InsertaRegistros(db)
        self.consulta_tablas = ConsultaRegistros(db)
        
    @handle_db_exceptions
    async def get_registros(self):
        return await self.consulta_tablas.obtener_tabla_en_batches(self.model_class)
"""

REPOSITORIES_CONSULTA_PY = """from fastapi.responses import StreamingResponse, FileResponse
import tempfile
from core.exceptions import handle_db_exceptions
from sqlalchemy import select
import pandas as pd
import os

class ConsultaRegistros:
    def __init__(self, db):
        self.db = db
        self.max_params = 32767
        
    @handle_db_exceptions
    async def obtener_tabla_en_batches(self, tabla):
        # Implementación simplificada para el ejemplo
        query = select(tabla)
        result = await self.db.execute(query)
        registros = result.scalars().all()
        return [r.__dict__ for r in registros]
"""

SCHEMAS_PY = """from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    deshabilitado: Optional[bool] = False
    isAdmin: Optional[bool] = False

    class Config:
        from_attributes = True

class ExampleSchema(BaseModel):
    name: str
    description: Optional[str] = None
"""

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

AUTH_UTILS_PY = """import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt
from cryptography.fernet import Fernet
from core import config
from utils.logger import configure_logger

logger = configure_logger(name='auth_utils')

def generate_salt() -> bytes:
    return bcrypt.gensalt()

def get_password_hash(password: str, salt: bytes) -> bytes:
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)

def encriptar(token: str) -> bytes:
    return Fernet(config.FERNET_KEY).encrypt(token.encode())

def desencriptar(token_cifrado: bytes) -> str:
    return Fernet(config.FERNET_KEY).decrypt(token_cifrado).decode()
"""

AUTH_SERVICE_PY = """from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import Usuario
from auth.auth_utils import verify_password

async def get_user(db: AsyncSession, username: str):
    user = (await db.scalars(select(Usuario).where(Usuario.username == username))).first()
    return user

async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user(db, username)
    if not user or not verify_password(password, user.passhash):
        return None
    return user
"""

LOGGER_PY = """import logging
import sys

def configure_logger(name='Logger', level=logging.INFO, log_to_file: str = None):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter('[%(name)s] %(levelname)s:  %(message)s')
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        if log_to_file:
            file_handler = logging.FileHandler(log_to_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    logger.propagate = False
    return logger
"""

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
API_KEY={api_key}
X_API_KEY={x_api_key}
DOCS_API_KEY={docs_api_key}
SECRET_KEY={secret_key}
FERNET_KEY={fernet_key}
ALGORITHM={algorithm}
APP_ENV={app_env}

# Base de datos local
usernameDBLocal={db_local_username}
passwordDBLocal={db_local_password}
servernameDBLocal={db_local_server}
databasenameDBLocal={db_local_dbname}

# Base de datos produccion
usernameDB={db_prod_username}
passwordDB={db_prod_password}
servernameDB={db_prod_server}
databasenameDB={db_prod_dbname}

# Usuario admin
usernameAdmin={admin_username}
passhashAdminAPI={admin_password}

# PerroBot
TOKEN_PERROBOT={token_perrobot}
passhashAdmin={passhash_admin_bot}
"""

DOCKERFILE_BASE = """FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ="Europe/Madrid"

WORKDIR /app/

COPY . .

RUN pip install uv==0.11.8
RUN apk add --no-cache git build-base postgresql-dev libffi-dev
RUN uv pip install --system -r requirements.txt
RUN rm -rf /root/.cache

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

DOCKERFILE_WITH_PERROBOT = """FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ="Europe/Madrid"

WORKDIR /app/

COPY . .

RUN pip install uv==0.11.8
RUN apk add --no-cache git build-base postgresql-dev libffi-dev
RUN uv pip install --system -r requirements.txt
RUN rm -rf /root/.cache

ARG TOKEN_PERROBOT
RUN uv pip install --system "git+https://${TOKEN_PERROBOT}@github.com/triplealpha-innovation/perroBot.git@main"
RUN rm -rf /root/.cache

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

DOCKER_COMPOSE_BASE = """services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${usernameDBLocal}
      POSTGRES_PASSWORD: ${passwordDBLocal}
      POSTGRES_DB: ${databasenameDBLocal}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${usernameDBLocal}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
"""

DOCKER_COMPOSE_WITH_PERROBOT = """services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        TOKEN_PERROBOT: ${TOKEN_PERROBOT}
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${usernameDBLocal}
      POSTGRES_PASSWORD: ${passwordDBLocal}
      POSTGRES_DB: ${databasenameDBLocal}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${usernameDBLocal}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
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
python-dotenv>=1.2.1
"""

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
    db_local: dict,
    db_prod: dict | None,
    admin: dict,
    api_secrets: dict,
    token_perrobot: str | None = None,
    passhash_admin_bot: str | None = None,
) -> None:
    project_slug = name.lower().replace(" ", "_")

    # 1. Create directories
    dirs = [
        "auth", "controllers", "core", "database", "dependencies", 
        "helpers", "models", "repositories", "routes", "schemas", 
        "services", "static", "static/img", "utils", "test"
    ]
    
    for d in dirs:
        (target_dir / d).mkdir(parents=True, exist_ok=True)
        _write(target_dir / d / "__init__.py", "")

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
    
    # --- Models ---
    _write(target_dir / "models/models.py", MODELS_PY)
    
    # --- Repositories ---
    _write(target_dir / "repositories/consulta_tabla_repository.py", REPOSITORIES_CONSULTA_PY)
    _write(target_dir / "repositories/inserta_registros_repository.py", "class InsertaRegistros:\n    def __init__(self, db):\n        self.db = db\n    async def inserta_registros(self, model, data, background_tasks, schema=None):\n        pass")
    
    # --- Controllers ---
    _write(target_dir / "controllers/base_controller.py", CONTROLLERS_BASE_PY)
    _write(target_dir / "controllers/example_controller.py", "from controllers.base_controller import BaseController\nfrom models.models import ExampleModel\n\nclass ExampleController(BaseController):\n    def __init__(self, db):\n        super().__init__(db, ExampleModel)")
    
    # --- Routes ---
    _write(target_dir / "routes/example_router.py", "from fastapi import APIRouter, Depends\nfrom database.db_service import get_session_context\nfrom sqlalchemy.ext.asyncio import AsyncSession\nfrom controllers.example_controller import ExampleController\n\nrouter = APIRouter(prefix=\"/examples\", tags=[\"Examples\"])\n\n@router.get(\"/\")\nasync def get_examples(db: AsyncSession = Depends(get_session_context)):\n    controller = ExampleController(db)\n    return await controller.get_registros()")
    
    # --- Schemas ---
    _write(target_dir / "schemas/schemas.py", SCHEMAS_PY)
    
    # --- Utils ---
    _write(target_dir / "utils/logger.py", LOGGER_PY)
    _write(target_dir / "utils/defaultUser.py", DEFAULT_USER_PY)

    # --- Services ---
    _write(target_dir / "services/README.md", SERVICES_README)
    _write(target_dir / "services/example_service.py", SERVICES_PY)

    # --- Helpers ---
    _write(target_dir / "helpers/README.md", HELPERS_README)
    _write(target_dir / "helpers/common.py", HELPERS_PY)

    # --- Static ---
    (target_dir / "static/img").mkdir(parents=True, exist_ok=True)

    # --- Docker ---
    dockerfile = DOCKERFILE_WITH_PERROBOT if perrobot else DOCKERFILE_BASE
    _write(target_dir / "Dockerfile", dockerfile)
    docker_compose = DOCKER_COMPOSE_WITH_PERROBOT if perrobot else DOCKER_COMPOSE_BASE
    _write(target_dir / "docker-compose.yml", docker_compose)

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
        token_perrobot=token_perrobot or "",
        passhash_admin_bot=passhash_admin_bot or "",
    )
    _write(target_dir / ".env", env_content)

    # --- READMEs for subdirectories ---
    _write(target_dir / "controllers/README.md", CONTROLLERS_README)
    _write(target_dir / "models/README.md", MODELS_README)
    _write(target_dir / "routes/README.md", ROUTES_README)
    _write(target_dir / "schemas/README.md", SCHEMAS_README)

    # --- Main README ---
    readme_content = README_TEMPLATE.format(
        project_name=name,
        project_description=description,
        project_slug=project_slug,
        host=host,
        port=port,
    )
    _write(target_dir / "README.md", readme_content)
