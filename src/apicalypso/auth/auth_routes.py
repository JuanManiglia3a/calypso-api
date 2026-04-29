"""
auth/auth_routes.py

Este archivo contiene las rutas relacionadas con la autenticación y seguridad de la API. 
Incluye endpoints para iniciar sesión, obtener tokens de acceso y refrescar información del usuario.

Responsabilidades principales:
- Proporcionar rutas para el inicio de sesión con OAuth2.
- Permitir a los usuarios autenticados consultar información sobre su cuenta.
- Manejar límites de acceso mediante decoradores de rate limiting.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from auth.auth_service import authenticate_user, get_user
from auth.auth_utils import create_access_token
from auth.auth_dependencies import get_current_active_user
from database.db_service import get_session_context
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.schemas import Token, User
from dependencies.limitador import limiter
from datetime import timedelta
from core import config
from utils.logger import configure_logger

logger = configure_logger(name=__name__, level="INFO")

router = APIRouter(tags=["Seguridad y Autenticación"])

@router.post("/token")
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session_context)
):
    """Endpoint para obtener un token de acceso y refresh token."""
    user = await authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        logger.error(f"Intento de inicio de sesión fallido para el usuario {form_data.username} desde {request.client.host}. Usuario o contraseña incorrectos.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"Usuario {user.username} autenticado con éxito desde {request.client.host}")
    
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=config.REFRESH_TOKEN_EXPIRES_DAYS)

    access_token = create_access_token(
        data={"sub": user.username, "type": "access"}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": user.username, "type": "refresh"}, expires_delta=refresh_token_expires
    )

    # Aquí asegúrate de devolver ambos tokens
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@router.post("/refresh-token")
@limiter.limit("10/minute")
async def refresh_access_token(
    request: Request,
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_session_context)
):
    """Endpoint para renovar el access token usando el refresh token."""
    try:
        # Verificar el refresh token
        payload = jwt.decode(refresh_token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar que el usuario existe y está activo
        user = await get_user(db, username=username)
        if not user or user.deshabilitado:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generar nuevo access token
        access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": user.username, "type": "access"}, 
            expires_delta=access_token_expires
        )
        
        logger.info(f"Token renovado para usuario {user.username} desde {request.client.host}")
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except JWTError:
        logger.error(f"Intento de renovación con refresh token inválido desde {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Obtener la información del usuario actual."""
    return current_user