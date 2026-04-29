"""
services/crudUsuarios_service.py

Este servicio define la lógica de negocio para el CRUD de usuarios en la API de SeaValue.

Responsabilidades:
    - Crear un usuario en la base de datos.
    - Actualizar un usuario en la base de datos.
    - Eliminar un usuario de la base de datos.
    - Listar todos los usuarios de la base de datos.
"""

from fastapi import HTTPException
from models.models import Usuario
from repositories.crudUsuarios_repository import CrudUsuariosRepository
from auth.auth_utils import get_password_hash, generate_salt
from utils.logger import configure_logger

logger = configure_logger(name=__name__)

class CrudUsuariosService:
    def __init__(self, repo: CrudUsuariosRepository):
        self.repo = repo
        
    
    async def crear_usuario(self, usuario_dict: dict):
        """ Crea un usuario en la base de datos """

        # Verifica si el usuario ya existe
        usuario_db = await self.repo.verifica_usuario_ya_existe(usuario_dict['username'])
        if usuario_db:
            raise HTTPException(
                status_code=400,
                detail=f"El usuario {usuario_dict['username']} ya existe."
            )

        salt = generate_salt()
        usuario_dict['passhash'] = get_password_hash(usuario_dict['passhash'], salt)
        usuario_dict['salt'] = salt

        nuevo_usuario = Usuario(**usuario_dict)
        self.repo.db.add(nuevo_usuario)
        await self.repo.db.commit()

        logger.info(f"¡Usuario {usuario_dict['username']} creado correctamente!")
        
        return {
            "mensaje": f'¡Usuario {usuario_dict["username"]} creado correctamente!',
            "username": usuario_dict["username"]
        }
        
    async def listar_usuarios(self):
        """ Lista todos los usuarios de la base de datos """
        
        # Delegar la lógica al repositorio
        usuarios = await self.repo.listar_usuarios()

        if not usuarios:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron usuarios en la base de datos."
            )

        return usuarios

    async def actualizar_usuario(self, username: str, usuario_dict: dict):
        """ Actualiza un usuario en la base de datos """
        
        # Verifica si el usuario existe
        usuario_db = await self.repo.verifica_usuario_ya_existe(username)
        if not usuario_db:
            raise HTTPException(
                status_code=404,
                detail=f"El usuario {username} no fue encontrado."
            )
        
        # Genera nuevo salt y hash para la contraseña
        salt = generate_salt()
        usuario_dict['passhash'] = get_password_hash(usuario_dict['passhash'], salt)
        usuario_dict['salt'] = salt

        # Actualiza los campos del usuario
        usuario_db.username = usuario_dict['username']
        usuario_db.passhash = usuario_dict['passhash']
        usuario_db.salt = usuario_dict['salt']
        usuario_db.deshabilitado = usuario_dict['deshabilitado']
        usuario_db.isAdmin = usuario_dict['isAdmin']

        # Delega la actualización al repositorio
        self.repo.db.add(usuario_db) 
        await self.repo.db.commit()

        logger.info(f"¡Usuario {username} actualizado correctamente!")
        
        return {
            "mensaje": f'¡Usuario {username} actualizado correctamente!',
            "username": username
        }
    
    async def eliminar_usuario(self, username: str):
        """ Elimina un usuario en la base de datos """
        
        # Verifica si el usuario existe
        usuario_db = await self.repo.verifica_usuario_ya_existe(username)
        if not usuario_db:
            raise HTTPException(
                status_code=404,
                detail=f"El usuario {username} no fue encontrado."
            )

        # Delega la eliminación al repositorio
        await self.repo.eliminar_usuario(usuario_db)
        logger.warning(f"¡Usuario {username} eliminado de la base de datos!")
        
        return {
            "mensaje": f'¡Usuario {username} eliminado correctamente!',
            "username": username
        }

