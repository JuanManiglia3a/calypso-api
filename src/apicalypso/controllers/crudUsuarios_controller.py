"""
controllers/crudUsuarios_controller.py

Este archivo contiene la lógica para crear, leer, actualizar y eliminar usuarios de la api en la base de datos.

Responsabilidades principales:
    - Crear un usuario en la base de datos.
    - Actualizar un usuario en la base de datos.
    - Eliminar un usuario de la base de datos.
"""

from fastapi.responses import JSONResponse
from utils.logger import configure_logger
from repositories.crudUsuarios_repository import CrudUsuariosRepository
from services.crudUsuarios_service import CrudUsuariosService

logger = configure_logger(name=__name__)

class CrudUsuariosController:
    def __init__(self, db):
        self.db = db
        repo = CrudUsuariosRepository(db)
        self.service = CrudUsuariosService(repo)

    
    async def crear_usuario(self, usuario_dict: dict):
        """ Llama al servicio para crear un usuario en la base de datos """
        response = await self.service.crear_usuario(usuario_dict)
        
        return JSONResponse(
            status_code=201,
            content=response
        )
        
    async def listar_usuarios(self):
        """ Lista todos los usuarios de la base de datos """
        
        # Delegar la lógica al servicio
        response = await self.service.listar_usuarios()
        return response
    

    async def actualizar_usuario(self, username: str, usuario_dict: dict):
        """ Actualiza un usuario en la base de datos """
        
        # Delegar la actualización al servicio
        response = await self.service.actualizar_usuario(username, usuario_dict)
        return response
    
    async def eliminar_usuario(self, username: str):
        """ Elimina un usuario de la base de datos """
        
        # Delegar la eliminación al servicio
        response = await self.service.eliminar_usuario(username)
        return response
