"""
database/db.py

Este archivo define la configuración de la base de datos.
Crea un contexto asíncrono para manejar sesiones de la base de datos.

Responsabilidades:
    - Crear un contexto asíncrono para manejar sesiones de la base de datos.
    - Configurar la base de datos según el modo de ejecución.
"""

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

# Clase base para los modelos ORM de SQLAlchemy.
Base = declarative_base()

class DatabaseSessionManager:
    """
    Gestor de sesiones asíncronas para la base de datos.
    Permite crear y gestionar conexiones y sesiones ORM de manera asíncrona.
    """
    def __init__(self, db_url: str, engine_kwargs: dict[str, Any] = {}):
        """
        Inicializa el gestor de sesiones de la base de datos.

        Args:
            db_url (str): URI de conexión a la base de datos.
            engine_kwargs (dict): Parámetros adicionales para el motor SQLAlchemy.
        """
        engine_kwargs = engine_kwargs or {}
        self._engine = create_async_engine(db_url, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )

    async def close(self):
        """
        Cierra el motor de la base de datos y libera los recursos asociados.
        Debe llamarse al finalizar la aplicación para evitar fugas de recursos.
        """
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Proporciona un contexto asíncrono para una sesión ORM de la base de datos (nivel de sesión)."""
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
        logger.info("Utilizando base de datos local......")
        async_uri = config.DATABASE_URI_ASYNC_LOCAL
    case "Producción":
        logger.warning("Utilizando base de datos de producción......")
        async_uri = config.DATABASE_URI_ASYNC_PROD
    case _:
        raise ValueError("Modo no soportado")

# Instancia global del gestor de sesiones para ser utilizada en toda la aplicación.
session_manager = DatabaseSessionManager(
    async_uri,
    {"echo": False, "pool_pre_ping": True, "pool_recycle": 3600},
)
