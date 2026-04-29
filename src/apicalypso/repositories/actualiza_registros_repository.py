"""
dependencies/actualiza_registros_depend.py

Este archivo contiene dependencias comunes para los controladores.
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
from perroBot.enviaLogs import EnviaLogs
import logging

logger = configure_logger(name=__name__, level="INFO")
loggerteams = EnviaLogs(level=logging.INFO)

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
        
        # Validar que el conjunto no esté vacío
        if len(records) == 0:
            logger.warning(f"El archivo está vacío. No se sobrescribirá la tabla {tabla.__tablename__}")
            return
        
        num_columnas = len(table.column_names)
        batch_size = self.max_params // num_columnas
        batch_size = min(batch_size, len(records))
        total_registros = len(records)
        
        logger.info(f"Total de registros a sobrescribir en {tabla.__tablename__}: {total_registros} (Batch size: {batch_size})")
        
        # Eliminar todos los registros existentes
        logger.info(f"Eliminando todos los registros existentes de {tabla.__tablename__}")
        await self.db.execute(tabla.__table__.delete())
        
        # Insertar nuevos registros en batches
        registros_insertados = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            await self.db.execute(tabla.__table__.insert().values(batch))
            registros_insertados += len(batch)
            logger.info(f"Insertados {registros_insertados}/{total_registros} registros en {tabla.__tablename__}")
        
        await self.db.commit()
        if config.perrobot:
            loggerteams.enviar_log_teams(
                nombreCliente="Calypso",
                grupo="perroBot",
                mensaje=f"Se sobrescribieron {total_registros} registros en la tabla {tabla.__tablename__} de Postgresql",
                level=logging.INFO,
                proyecto=config.PROJECT_NAME
            )
        logger.info(f"Registros sobrescritos correctamente en la tabla {tabla.__tablename__} - Total: {total_registros} registros")
