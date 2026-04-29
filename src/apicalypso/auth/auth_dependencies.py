"""
auth/auth_dependencies.py

Este archivo define las dependencias relacionadas con la autenticación para FastAPI. 
Estas dependencias se utilizan para validar y obtener información del usuario autenticado 
antes de permitir el acceso a ciertos endpoints.

Responsabilidades principales:
- Validar el token de acceso y obtener al usuario actual.
- Verificar roles o permisos del usuario autenticado.
- Configurar dependencias reutilizables para proteger endpoints de la API.
- Implementar funciones para validar API Keys.
"""


from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader, APIKeyQuery
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from auth.auth_service import get_user
from schemas.schemas import TokenData, User
from core import config
from database.db_service import get_session_context

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name="x_api_key", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session_context)
):
    """Obtener el usuario actual a partir del token."""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user = await get_user(db, username=token_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user

async def get_current_active_user(
    current_user: User = Security(get_current_user)
):
    """Validar que el usuario no esté deshabilitado."""
    if current_user.deshabilitado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
    return current_user

async def get_current_admin_user(
    current_user: User = Security(get_current_user)
):
    """Validar que el usuario sea administrador."""
    if not current_user.isAdmin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario no autorizado")
    return current_user

api_key_query = APIKeyQuery(name="api_key", auto_error=False, description='API Key QUERY para acceder a endpoints protegidos con Query.')
def get_api_key_query(api_key: str = Security(api_key_query)) -> str:
    if api_key == config.API_KEY:
        return api_key

    raise HTTPException(status_code=401, detail="API Key incorrecta")

api_key_header = APIKeyHeader(name="x_api_key", auto_error=False, description='API Key HEADER para acceder a endpoints protegidos con Header.')
def get_api_key_header(api_key: str = Security(api_key_header)) -> str:
    if api_key == config.X_API_KEY:
        return api_key

    raise HTTPException(status_code=401, detail="API Key incorrecta")