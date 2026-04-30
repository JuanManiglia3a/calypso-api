"""
auth/auth_service.py

Este archivo contiene la lógica central de autenticación de la aplicación. 
Incluye funciones para manejar la generación de hashes de contraseñas, 
verificación de credenciales, autenticación de usuarios y emisión de tokens JWT. 

Responsabilidades principales:
- Generar y verificar contraseñas seguras.
- Autenticar usuarios mediante credenciales.
- Crear tokens de acceso y refresh.
- Implementar funciones para recuperar usuarios autenticados.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import Usuario
from auth.auth_utils import verify_password

async def get_user(db: AsyncSession, username: str):
    """Obtener un usuario de la base de datos por su username."""
    user = (await db.scalars(select(Usuario).where(Usuario.username == username))).first()
    return user

async def authenticate_user(db: AsyncSession, username: str, password: str):
    """Autenticar a un usuario verificando su contraseña."""
    user = await get_user(db, username)
    if not user or not verify_password(password, user.passhash):
        return None
    return user
