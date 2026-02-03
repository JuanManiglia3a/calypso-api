# Calypso API

Librería y CLI para crear estructuras de proyectos robustos y escalables con FastAPI, SQLAlchemy (Async) y PostgreSQL.

## Instalación

Puedes instalar `calypso-api` directamente desde PyPI usando `pip` o `uv`:

```bash
uv add calypso-api
# O con pip
pip install calypso-api
```

## Uso

Una vez instalado, tendrás acceso al comando `calypso` en tu terminal.

### Crear un nuevo proyecto

Para generar un nuevo proyecto con toda la estructura lista:

```bash
calypso init mi_nuevo_proyecto "Mi Nuevo Proyecto" --host 0.0.0.0 --port 8000 --docker
```

Esto creará una carpeta `mi_nuevo_proyecto` con:
- Estructura modular (Controllers, Models, Routes, etc.)
- Configuración de Docker y Docker Compose.
- Autenticación JWT configurada.
- Documentación automática lista.

### Comandos disponibles

```bash
# Inicializar un proyecto
calypso init <directorio> <nombre_proyecto>

# Ver ayuda
calypso --help
```

## Estructura Generada

El proyecto generado tendrá la siguiente estructura:

- `auth/`: Lógica de autenticación.
- `controllers/`: Controladores de la lógica de negocio.
- `core/`: Configuración global.
- `database/`: Configuración de base de datos.
- `routes/`: Definición de endpoints.
- `models/`: Modelos de base de datos.
- `schemas/`: Schemas Pydantic.
- `helpers/`: Utilidades generales.
- `services/`: Lógica de negocio compleja.
- `docker-compose.yml`: Orquestación de contenedores.
