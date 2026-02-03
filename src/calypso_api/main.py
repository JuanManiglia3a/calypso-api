
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from calypso_api.core import config
from calypso_api.database.db import init_db
from calypso_api.routes import health

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown

app = FastAPI(
    title=config.PROJECT_NAME,
    description=config.PROJECT_DESCRIPTION,
    version=config.VERSION,
    lifespan=lifespan,
    docs_url=f"{config.API_PREFIX}/docs",
    redoc_url=f"{config.API_PREFIX}/redoc",
    openapi_url=f"{config.API_PREFIX}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=config.API_PREFIX)

@app.get("/")
async def root():
    return {"message": f"Welcome to {config.PROJECT_NAME}"}
