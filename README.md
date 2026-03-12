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

#TODO Verificar que la estructura de carpetas de la API y su contenido es correcto. 
#TODO Verificar el ejemplo que se genera por defecto. Probablemente no sea necesario si se incluye ya directamente en los archivos de la API el crud de usuarios de la API. 
#TODO Poner en el readme los requisitos previos. El primero es crear previamente a la API una base de datos (de preferencia postgres) bien en local o en la nube con Terraform. 

#TODO Funcionamiento esperado: El usuario instala la librería y con el init crea todo el sistema de carpertas para la API, Chatbot y Etl, todo esto opcional. El esquema de la base de datos estará en la API (models.py). Una vez está especificado el modelo de datos habrá un comando para crear endpoints CRUD de las tablas que se pida. 

#TODO generar también el .env sugerido basándonos en el nombre del proyecto. Debería también poner apikeys aleatorias, clave fernet y openssh para el la clave secreta.

#TODO Debería generar también manera opcional la carpeta de Settings para el despliegue la la del .github/workflows también para el despliegue.  
