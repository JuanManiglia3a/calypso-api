"""
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
                    registro.pop('_sa_instance_state', None)

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
