"""
utils/defaultUser.py

Este archivo contiene la lógica para crear un usuario por defecto en la base de datos.

Responsabilidades principales:
- Crear un usuario por defecto en la base de datos.
- Verificar si el usuario por defecto ya existe.
- Generar salt para el usuario por defecto.
- Crear el usuario por defecto en la base de datos.

"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import Usuario
from auth.auth_utils import get_password_hash, generate_salt
from core import config
from utils.logger import configure_logger

logger = configure_logger(name=__name__, level="INFO")

#======== Función crear usuario por defecto ========#
async def create_defaultAdmin_user(db: AsyncSession):

    logger.info("Creando usuario por defecto...")
    # Verifica si existe el usuario por defecto
    result = await db.scalars(select(Usuario).where(Usuario.username == config.usernameAdmin))
    default_user = result.first()
    
    if default_user:
        logger.warning(f"Usuario por defecto {default_user.username} ya existe.")
        return
    
    # Genera salt
    salt = generate_salt()
    
    # Crea el usuario por defecto
    default_user = Usuario(
        username=config.usernameAdmin,
        passhash=get_password_hash(config.passhashAdminAPI, salt),
        salt=salt,
        deshabilitado=False,
        isAdmin=True
    )
    
    db.add(default_user)
    try:
        await db.commit()
        logger.info(f"Usuario por defecto creado: {default_user.username}")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al crear usuario por defecto: {e}")