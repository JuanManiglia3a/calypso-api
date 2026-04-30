"""
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
