"""
dependencies/inserta_registros_depend.py

Este archivo contiene dependencias comunes para los controladores del ETL.
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

        # Calcula batch_size dinámicamente
        batch_size = self.max_params // num_columnas
        batch_size = min(batch_size, len(records))  # No hacer lotes más grandes de lo necesario
        total_registros = len(records)
        logger.info(f"Total de registros a insertar en {tabla.__tablename__}: {total_registros} (Batch size: {batch_size})")

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            insert_stmt = postgres_insert(tabla).values(batch)
            do_nothing_stmt = insert_stmt.on_conflict_do_nothing()
            await self.db.execute(do_nothing_stmt)
        
        await self.db.commit()
        logger.info(f"Registros insertados correctamente en la tabla {tabla.__tablename__}")