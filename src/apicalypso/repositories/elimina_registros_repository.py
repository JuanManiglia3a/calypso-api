"""
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