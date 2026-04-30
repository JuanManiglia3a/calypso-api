"""
repositories/patch_registros_repository.py

Este archivo contiene el repositorio genérico para operaciones PATCH.
Permite actualizar campos específicos de cualquier modelo de manera genérica.

Responsabilidades:
    - Actualizar campos específicos por clave primaria de manera genérica
    - Manejar validaciones de existencia de registros
    - Proporcionar funcionalidad reutilizable para operaciones PATCH
"""

from core.exceptions import handle_db_exceptions
from sqlalchemy import update, select
from utils.logger import configure_logger
from typing import Dict, Any, Optional
from fastapi import HTTPException

logger = configure_logger(name=__name__, level="INFO")

class PatchRegistros:
    
    def __init__(self, db):
        self.db = db

    @handle_db_exceptions
    async def patch_registro_generico(
        self, 
        model_class, 
        primary_key_value: str, 
        campos_actualizar: Dict[str, Any], 
        primary_key_name: str = None
    ) -> bool:
        """
        Actualiza campos específicos de un registro de manera genérica.
        
        Args:
            model_class: Clase del modelo SQLAlchemy
            primary_key_value: Valor de la clave primaria del registro a actualizar
            campos_actualizar: Diccionario con los campos y valores a actualizar
            primary_key_name: Nombre de la columna de clave primaria (opcional, se detecta automáticamente)
            
        Returns:
            bool: True si se actualizó el registro, False si no se encontró
            
        Raises:
            HTTPException: Si no se encuentran claves primarias en el modelo
        """
        # Si no se especifica el nombre de la columna, extraemos la primera clave primaria del modelo
        if primary_key_name is None:
            primary_key_columns = [key.name for key in model_class.__table__.primary_key.columns]
            if not primary_key_columns:
                raise HTTPException(
                    status_code=500, 
                    detail=f"No se encontraron claves primarias en la tabla {model_class.__tablename__}"
                )
            primary_key_name = primary_key_columns[0]

        # Filtrar campos None del diccionario de actualización
        campos_filtrados = {k: v for k, v in campos_actualizar.items() if v is not None}
        
        if not campos_filtrados:
            logger.warning(f"No hay campos para actualizar en {model_class.__tablename__}")
            return False

        # Obtener la columna de clave primaria
        primary_key_column = getattr(model_class, primary_key_name)
        
        # Crear la consulta de actualización
        stmt = (
            update(model_class)
            .where(primary_key_column == primary_key_value)
            .values(**campos_filtrados)
        )
        
        # Ejecutar la actualización
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        registros_actualizados = result.rowcount
        
        if registros_actualizados > 0:
            logger.info(f"Registro actualizado en {model_class.__tablename__}. Clave: {primary_key_value}")
            return True
        else:
            logger.warning(f"No se encontró registro con {primary_key_name}={primary_key_value} en {model_class.__tablename__}")
            return False

    @handle_db_exceptions
    async def verificar_existencia_registro(
        self, 
        model_class, 
        primary_key_value: str, 
        primary_key_name: str = None
    ) -> bool:
        """
        Verifica si existe un registro con la clave primaria especificada.
        
        Args:
            model_class: Clase del modelo SQLAlchemy
            primary_key_value: Valor de la clave primaria a verificar
            primary_key_name: Nombre de la columna de clave primaria (opcional)
            
        Returns:
            bool: True si existe el registro, False si no existe
        """
        # Si no se especifica el nombre de la columna, extraemos la primera clave primaria del modelo
        if primary_key_name is None:
            primary_key_columns = [key.name for key in model_class.__table__.primary_key.columns]
            if not primary_key_columns:
                raise HTTPException(
                    status_code=500, 
                    detail=f"No se encontraron claves primarias en la tabla {model_class.__tablename__}"
                )
            primary_key_name = primary_key_columns[0]

        # Obtener la columna de clave primaria
        primary_key_column = getattr(model_class, primary_key_name)
        
        # Crear la consulta de verificación
        stmt = select(model_class).where(primary_key_column == primary_key_value)
        
        # Ejecutar la consulta
        result = await self.db.execute(stmt)
        registro = result.scalar_one_or_none()
        
        return registro is not None

    @handle_db_exceptions
    async def obtener_registro_por_clave(
        self, 
        model_class, 
        primary_key_value: str, 
        primary_key_name: str = None
    ) -> Optional[Any]:
        """
        Obtiene un registro completo por su clave primaria.
        
        Args:
            model_class: Clase del modelo SQLAlchemy
            primary_key_value: Valor de la clave primaria
            primary_key_name: Nombre de la columna de clave primaria (opcional)
            
        Returns:
            El registro encontrado o None si no existe
        """
        # Si no se especifica el nombre de la columna, extraemos la primera clave primaria del modelo
        if primary_key_name is None:
            primary_key_columns = [key.name for key in model_class.__table__.primary_key.columns]
            if not primary_key_columns:
                raise HTTPException(
                    status_code=500, 
                    detail=f"No se encontraron claves primarias en la tabla {model_class.__tablename__}"
                )
            primary_key_name = primary_key_columns[0]

        # Obtener la columna de clave primaria
        primary_key_column = getattr(model_class, primary_key_name)
        
        # Crear la consulta
        stmt = select(model_class).where(primary_key_column == primary_key_value)
        
        # Ejecutar la consulta
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()