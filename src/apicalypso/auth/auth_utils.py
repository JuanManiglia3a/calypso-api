"""
auth/auth_utils.py

Este archivo contiene funciones auxiliares relacionadas con la autenticación y seguridad. 
Estas funciones son independientes y reutilizables, diseñadas para facilitar tareas comunes 
como la manipulación de datos de autenticación.

Responsabilidades principales:
- Crear y verificar sal y hashes de contraseñas.
- Generar tokens JWT con datos personalizados.
- Validar estructuras y datos relacionados con autenticación.
- Encriptar y desencriptar datos sensibles.
"""

import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt
from cryptography.fernet import Fernet
from core import config
from utils.logger import configure_logger

logger = configure_logger(name='auth_utils')

def generate_salt() -> bytes:
    """Generar un salt para el hash de contraseñas."""
    return bcrypt.gensalt()

def get_password_hash(password: str, salt: bytes) -> bytes:
    """Hashear una contraseña utilizando bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    """Verificar si una contraseña coincide con su hash."""
    logger.info("Verificando contraseña...")
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Generar un token de acceso JWT."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)

def encriptar(token: str) -> bytes:
    cipher_suite = Fernet(config.FERNET_KEY)
    try:
        token_encriptado = cipher_suite.encrypt(token.encode())
        return token_encriptado
    except Exception as e:
        logger.error(f"Error al encriptar el token: {e}")
        raise e

def desencriptar(tokenCifrado: bytes) -> str:
    cipher_suite = Fernet(config.FERNET_KEY)
    try:
        token_desencriptado = cipher_suite.decrypt(tokenCifrado).decode()
        return token_desencriptado
    except Exception as e:
        logger.error(f"Error al desencriptar el token: {e}")
        raise e