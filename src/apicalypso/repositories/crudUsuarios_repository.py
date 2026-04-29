"""
repositories/crudUsuarios_repository.py

Este ropositorio define las operaciones de acceso a datos para el CRUD de usuarios en la API de SeaValue.

Responsabilidades:
    - Acceso a la base de datos para crear, actualizar, eliminar y listar usuarios.
"""

from core.exceptions import handle_db_exceptions
from sqlalchemy.future import select
from models.models import Usuario
from utils.logger import configure_logger

logger = configure_logger(name=__name__)

class CrudUsuariosRepository:
    def __init__(self, db):
        self.db = db
        
    @handle_db_exceptions
    async def verifica_usuario_ya_existe(self, username: str):
        """ Verifica si un usuario ya existe en la base de datos """
        
        result = await self.db.scalars(select(Usuario).where(Usuario.username == username))
        usuario = result.first()
        
        return usuario
    
    @handle_db_exceptions
    async def listar_usuarios(self):
        """ Lista todos los usuarios de la base de datos """
        result = await self.db.scalars(select(Usuario))
        usuarios = result.all()
        return usuarios
    
        
    @handle_db_exceptions
    async def eliminar_usuario(self, usuario: Usuario):
        """ Elimina un usuario de la base de datos """
        await self.db.delete(usuario)
        await self.db.commit()

        logger.warning(f"¡Usuario {usuario.username} eliminado de la base de datos!")
        return {"mensaje": f"¡Usuario {usuario.username} eliminado correctamente!"}