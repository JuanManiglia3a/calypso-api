import traceback
import logging
import asyncio
from typing import Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError
from pyarrow.lib import ArrowInvalid
from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError
from perroBot.enviaLogs import EnviaLogs
from utils.logger import configure_logger
from core import config

logger = configure_logger(name=__name__)
loggerteams = EnviaLogs(level=logging.INFO)

# Manejo de excepciones no esperadas
async def exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unexpected error: {exc}")
    tb = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content={
            "message": f"Unexpected Error: {exc.__class__.__name__}.",
            "description": str(exc),
            "traceback": tb
        }
    )

# Manejo específico de excepciones HTTP
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

def _build_perrobot_message(prefix: str, e: Exception) -> str:
    return f"{prefix}: {e}"

async def _enviar_perrobot_seguro(level: int, mensaje: str):
    """Envía el mensaje a Teams de forma segura (truncado y sin bloquear)."""
    if not config.perrobot:
        return
    MAX_TEAMS_LEN = 800
    safe_msg = mensaje if len(mensaje) <= MAX_TEAMS_LEN else mensaje[:MAX_TEAMS_LEN] + "..."
    try:
        resp: Any = await asyncio.to_thread(
            loggerteams.enviar_log_teams,
            nombreCliente="Calypso",
            grupo="perroBot",
            mensaje=safe_msg,
            level=level,
            proyecto=config.PROJECT_NAME
        )
        logger.debug(f"perroBot respuesta: {resp}")
    except RequestsJSONDecodeError as ex:
        logger.info(f"perroBot respuesta no JSON ignorada: {ex}")
    except Exception as ex:
        logger.warning(f"Fallo enviando log a Teams (ignorado): {ex}")

def _is_background_task(func) -> bool:
    """Detecta si una función es un background task por su nombre."""
    return "background" in func.__name__ or "task" in func.__name__


def handle_db_exceptions(func):
    async def wrapper(*args, **kwargs):
        self = args[0]
        is_bg = _is_background_task(func)
        try:
            return await func(*args, **kwargs)
        except (IntegrityError, DataError, SQLAlchemyError,
                OSError, ValueError, ArrowInvalid) as e:
            await self.db.rollback()
            error_message = _build_perrobot_message("Database error", e)
            if is_bg:
                # CRITICAL: Los errores en background tasks se logueaban pero se
                # silenciaban. Ahora se loguean como CRITICAL con traceback completo
                # para que sean visibles en los logs del contenedor.
                logger.critical(
                    f"[BACKGROUND TASK FAILED] {func.__name__}: {error_message}\n"
                    f"{traceback.format_exc()}"
                )
            else:
                logger.error(error_message)
            if config.perrobot:
                await _enviar_perrobot_seguro(logging.ERROR, error_message)
            if is_bg:
                return
            raise HTTPException(status_code=400, detail=error_message)
        except HTTPException as e:
            await self.db.rollback()
            error_message = _build_perrobot_message("HTTP error", e)
            logger.warning(error_message)
            if config.perrobot:
                await _enviar_perrobot_seguro(logging.WARNING, error_message)
            if is_bg:
                return
            raise e
        except Exception as e:
            await self.db.rollback()
            error_message = _build_perrobot_message("Unexpected error", e)
            if is_bg:
                logger.critical(
                    f"[BACKGROUND TASK FAILED] {func.__name__}: {error_message}\n"
                    f"{traceback.format_exc()}"
                )
            else:
                logger.critical(error_message)
            if config.perrobot:
                await _enviar_perrobot_seguro(logging.CRITICAL, error_message)
            if is_bg:
                return
            raise HTTPException(status_code=500, detail=error_message)
    return wrapper
