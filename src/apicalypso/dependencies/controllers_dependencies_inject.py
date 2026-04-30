"""
dependencies/controllers_dependencies_inject.py

Este archivo define las dependencias necesarias para inyectar los controladores en las rutas de la API.

Responsabilidades principales:
- Inyectar todas las instancias de controladores con sus dependencias (sesiones de BD).
- Proporcionar factory functions para cada controlador de tablas de datos.

Los controladores se organizan en categorías según el Data Warehouse:
- HUBS: Tablas de hechos principales
- MAESTROS: Tablas dimensionales de códigos y configuración
- DIMENSIONES: Tablas de contexto y descripción
- HECHOS: Tablas de eventos y transacciones
- RESULTADOS: Tablas de síntesis y reportes
"""

from database.db_service import DBSessionAsyncDependency
from controllers.crudUsuarios_controller import CrudUsuariosController

# ================================================================
# Factory Functions - HUBS
# ================================================================
def get_crud_usuarios_controller(db: DBSessionAsyncDependency) -> CrudUsuariosController:
    return CrudUsuariosController(db=db)
