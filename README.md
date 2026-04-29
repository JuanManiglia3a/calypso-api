# Calypso API

> Genera una API lista para producción en minutos — sin configurar nada desde cero.

Librería y CLI para scaffolding de proyectos robustos y escalables con **FastAPI**, **SQLAlchemy Async** y **PostgreSQL**. Con un solo comando interactivo obtienes: estructura de carpetas completa, autenticación JWT, Docker Compose configurado, `.env` con secretos generados automáticamente y soporte opcional para PerroBot.

## Instalación

```bash
uv add calypso-api
# O con pip
pip install calypso-api
```

## Uso

Una vez instalado, tendrás acceso al comando `calypso` en tu terminal.

### Crear un nuevo proyecto

```bash
calypso init
```

El asistente te guiará paso a paso (7 pasos):

1. **Proyecto** — nombre, directorio destino y descripción
2. **Entorno** — modo (`Local` / `Producción`) y `APP_ENV`
3. **Base de datos local** — credenciales PostgreSQL local (con defaults)
4. **Base de datos producción** — opcional, configurable ahora o después
5. **Usuario admin** — credenciales del usuario administrador de la API
6. **PerroBot** — habilitar envío de mensajes (requiere GitHub PAT privado)
7. **Secretos API** — generados automáticamente o introducidos manualmente

Al finalizar se crea el proyecto con:
- Estructura modular lista (Controllers, Models, Routes, Repositories, etc.)
- `Dockerfile` y `docker-compose.yml` sincronizados con tus credenciales
- `.env` completo con todos los secretos (las API keys se muestran una sola vez)
- Autenticación JWT + usuario admin creado automáticamente en arranque

### Iniciar el proyecto generado

```bash
cd mi_proyecto
docker compose up --build -d
```

### Comandos disponibles

```bash
calypso init            # Crear un nuevo proyecto (interactivo)
calypso run             # Arrancar la API localmente
calypso --help          # Ayuda
```

## Estructura Generada

```
mi_proyecto/
├── auth/               # Autenticación JWT (login, tokens, dependencias)
├── controllers/        # Lógica de negocio
├── core/               # Configuración global (config.py, excepciones)
├── database/           # Conexión async a PostgreSQL
├── dependencies/       # Rate limiter y otras dependencias inyectables
├── helpers/            # Funciones auxiliares reutilizables
├── models/             # Modelos ORM SQLAlchemy
├── repositories/       # Acceso a datos (CRUD)
├── routes/             # Endpoints FastAPI
├── schemas/            # Schemas Pydantic (validación/serialización)
├── services/           # Lógica de negocio compleja
├── static/             # Archivos estáticos
├── utils/              # Logger, usuario por defecto
├── main.py             # Punto de entrada
├── Dockerfile          # python:3.12-alpine + uv (con PerroBot opcional)
├── docker-compose.yml  # API + PostgreSQL con healthcheck
├── requirements.txt    # Dependencias sincronizadas con la API de referencia
└── .env                # Secretos generados (API keys, Fernet, JWT, BD)
```

## Secretos gestionados

La CLI genera o solicita estos valores y los escribe en `.env`:

| Variable | Descripción |
|---|---|
| `API_KEY`, `X_API_KEY`, `DOCS_API_KEY` | Claves de acceso a la API |
| `SECRET_KEY` | Clave JWT (hex 32 bytes) |
| `FERNET_KEY` | Clave de cifrado Fernet |
| `ALGORITHM` | Algoritmo JWT (`HS256`) |
| `APP_ENV` | Entorno (`develop` / `staging` / `production`) |
| `usernameDBLocal/passwordDBLocal/...` | Credenciales BD local |
| `usernameDB/passwordDB/...` | Credenciales BD producción (opcional) |
| `usernameAdmin` / `passhashAdminAPI` | Usuario admin de la API |
| `TOKEN_PERROBOT` / `passhashAdmin` | Solo si PerroBot está habilitado |

## Requisitos Previos

- Python 3.12+
- Docker y Docker Compose
- Una base de datos PostgreSQL (local o en la nube — puedes usar el `docker-compose.yml` generado para local)
  
