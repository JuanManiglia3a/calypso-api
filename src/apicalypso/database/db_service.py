"""
database/db_service.py

Este archivo define las dependencias necesarias para los servicios de la base de datos.

Responsabilidades principales:
- Proporcionar un contexto para una sesión asíncrona de la base de datos.
- Crear las tablas en la base de datos si no existen.
"""

from database.db import Base, session_manager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncIterator, Annotated
from fastapi import Depends
from utils.logger import configure_logger
logger = configure_logger(name=__name__)

async def get_session_context() -> AsyncIterator[AsyncSession]:
    """Proporciona un contexto para una sesión asíncrona de la base de datos."""
    async with session_manager.session() as session:
        yield session

async def create_db_and_tables():
    """Crea las tablas en la base de datos."""
    logger.info("Creando tablas en la base de datos...")
    async with session_manager._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
DBSessionAsyncDependency = Annotated[AsyncSession, Depends(get_session_context)]