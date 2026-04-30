"""
routes/crudUsuarios_router.py

Este archivo define las rutas para las entidades relacionadas con el CRUD de usuarios.

Responsabilidades:
    - Define las rutas para el CRUD de usuarios.
"""

from fastapi import APIRouter, Depends, Request, Security
from dependencies.limitador import limiter
from controllers.crudUsuarios_controller import CrudUsuariosController
from dependencies import constants_descriptions
from dependencies.controllers_dependencies_inject import get_crud_usuarios_controller
from schemas.schemas import UserInResponse
from auth.auth_dependencies import get_current_admin_user, get_api_key_query

router = APIRouter(
    tags=["CRUD de Usuarios | Router Admin"],
    prefix="/usuarios",
    dependencies=[Security(get_current_admin_user)]
)

@router.post(
    "/crearUsuario",
    description=constants_descriptions.DESCRIPTIONS["crearUsuario"],
    status_code=201
)
@limiter.limit("60/minute")
async def crearUsuario(
    request: Request,
    usuario_in: UserInResponse,
    controller: CrudUsuariosController = Depends(get_crud_usuarios_controller)
):
    """Crea un nuevo usuario en la base de datos."""
    
    usuario_dict = usuario_in.model_dump()
    return await controller.crear_usuario(usuario_dict=usuario_dict)


@router.put(
    "/actualizarUsuario",
    description=constants_descriptions.DESCRIPTIONS["actualizarUsuario"],
    status_code=200
)
@limiter.limit("60/minute")
async def actualizarUsuario(
    request: Request,
    username: str,
    usuario_in: UserInResponse,
    controller: CrudUsuariosController = Depends(get_crud_usuarios_controller)
):
    """Actualiza un usuario en la base de datos."""
    
    usuario_dict = usuario_in.model_dump(exclude_unset=True)
    return await controller.actualizar_usuario(username=username, usuario_dict=usuario_dict)


@router.get(
    "/listarUsuarios",
    description=constants_descriptions.DESCRIPTIONS["listarUsuarios"],
    status_code=200,
    response_model=list[UserInResponse]
)
@limiter.limit("60/minute")
async def listarUsuarios(
    request: Request,
    controller: CrudUsuariosController = Depends(get_crud_usuarios_controller)
):
    """Lista todos los usuarios de la base de datos."""
    
    return await controller.listar_usuarios()


@router.delete(
    "/eliminarUsuario",
    description=constants_descriptions.DESCRIPTIONS["eliminarUsuario"],
    status_code=200
)
@limiter.limit("60/minute")
async def eliminarUsuario(
    request: Request,
    username: str,
    api_key: str = Depends(get_api_key_query),
    controller: CrudUsuariosController = Depends(get_crud_usuarios_controller)
):
    """Elimina un usuario de la base de datos."""
    
    return await controller.eliminar_usuario(username=username)