from fastapi import FastAPI, Request, HTTPException
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

description = f"""
# {config.PROJECT_NAME}

*{config.PROJECT_DESCRIPTION}*
"""

logger = configure_logger(name=__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Función que maneja los eventos de inicio y cierre de la aplicación.
    """
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
