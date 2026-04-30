from pathlib import Path

from ..._io import _write, _write_lf
from ._templates_app import (
    MAIN_PY, CORE_CONFIG_PY, CORE_EXCEPTIONS_PY,
    DATABASE_DB_PY, DATABASE_SERVICE_PY,
    MODELS_PY, SCHEMAS_PY, HELPERS_PY, SERVICES_PY,
    LOGGER_PY, DEFAULT_USER_PY,
)
from ._templates_auth import (
    AUTH_DEPENDENCIES_PY, AUTH_ROUTES_PY,
    AUTH_SERVICE_PY, AUTH_UTILS_PY,
)
from ._templates_crud import (
    CONTROLLERS_BASE_PY, CRUD_USUARIOS_CONTROLLER_PY,
    CRUD_USUARIOS_SERVICE_PY, CRUD_USUARIOS_REPOSITORY_PY,
    CRUD_USUARIOS_ROUTER_PY, CONSTANTS_DESCRIPTIONS_PY,
    CONTROLLERS_DEPENDENCIES_INJECT_PY, VALIDATE_DATAFRAME_HELPER_PY,
)
from ._templates_repositories import (
    REPOSITORIES_CONSULTA_PY, INSERTA_REGISTROS_REPOSITORY_PY,
    ACTUALIZA_REGISTROS_REPOSITORY_PY, ELIMINA_REGISTROS_REPOSITORY_PY,
    PATCH_REGISTROS_REPOSITORY_PY,
)
from ._templates_docker import (
    SSHD_CONFIG, DOCKERFILE_BASE, DOCKERFILE_WITH_PERROBOT,
    INIT_CONTAINER_SH, REQUIREMENTS_TEMPLATE, ENV_TEMPLATE, FAVICON_ICO_B64,
)
from ._templates_readmes import (
    README_TEMPLATE, SERVICES_README, HELPERS_README,
    CONTROLLERS_README, MODELS_README, ROUTES_README, SCHEMAS_README,
)


def generate(
    target_dir: Path,
    name: str,
    description: str,
    host: str,
    port: int,
    modo: str,
    app_env: str,
    perrobot: bool,
    include_db_container: bool,
    db_local: dict,
    db_prod: dict | None,
    admin: dict,
    api_secrets: dict,
    passhash_admin_bot: str | None = None,
    token_perrobot: str | None = None,
) -> None:
    project_slug = name.lower().replace(" ", "_")

    # 1. Create directories
    dirs_with_init = [
        "auth", "controllers", "core", "database", "dependencies",
        "helpers", "models", "repositories", "routes", "schemas",
        "services", "static", "utils", "test"
    ]
    for d in dirs_with_init:
        (target_dir / d).mkdir(parents=True, exist_ok=True)
        _write(target_dir / d / "__init__.py", "")
    # static/img has no __init__.py
    (target_dir / "static/img").mkdir(parents=True, exist_ok=True)

    # 2. Write File Contents
    
    # --- Main ---
    _write(target_dir / "main.py", MAIN_PY)
    
    # --- Auth ---
    _write(target_dir / "auth/auth_routes.py", AUTH_ROUTES_PY)
    _write(target_dir / "auth/auth_dependencies.py", AUTH_DEPENDENCIES_PY)
    _write(target_dir / "auth/auth_utils.py", AUTH_UTILS_PY)
    _write(target_dir / "auth/auth_service.py", AUTH_SERVICE_PY)

    # --- Core ---
    config_content = (
        CORE_CONFIG_PY
        .replace("{project_name}", name)
        .replace("{description}", description)
        .replace("{modo}", modo)
        .replace("{perrobot}", str(perrobot))
    )
    _write(target_dir / "core/config.py", config_content)
    _write(target_dir / "core/exceptions.py", CORE_EXCEPTIONS_PY)
    
    # --- Database ---
    _write(target_dir / "database/db.py", DATABASE_DB_PY)
    _write(target_dir / "database/db_service.py", DATABASE_SERVICE_PY)
    
    # --- Dependencies ---
    _write(target_dir / "dependencies/limitador.py", "from slowapi import Limiter\nfrom slowapi.util import get_remote_address\nlimiter = Limiter(key_func=get_remote_address)")
    _write(target_dir / "dependencies/constants_descriptions.py", CONSTANTS_DESCRIPTIONS_PY)
    _write(target_dir / "dependencies/controllers_dependencies_inject.py", CONTROLLERS_DEPENDENCIES_INJECT_PY)
    
    # --- Models ---
    _write(target_dir / "models/models.py", MODELS_PY)
    
    # --- Repositories ---
    _write(target_dir / "repositories/consulta_tabla_repository.py", REPOSITORIES_CONSULTA_PY)
    _write(target_dir / "repositories/inserta_registros_repository.py", INSERTA_REGISTROS_REPOSITORY_PY)
    _write(target_dir / "repositories/actualiza_registros_repository.py", ACTUALIZA_REGISTROS_REPOSITORY_PY)
    _write(target_dir / "repositories/elimina_registros_repository.py", ELIMINA_REGISTROS_REPOSITORY_PY)
    _write(target_dir / "repositories/patch_registros_repository.py", PATCH_REGISTROS_REPOSITORY_PY)
    _write(target_dir / "repositories/crudUsuarios_repository.py", CRUD_USUARIOS_REPOSITORY_PY)
    
    # --- Controllers ---
    _write(target_dir / "controllers/base_controller.py", CONTROLLERS_BASE_PY)
    _write(target_dir / "controllers/crudUsuarios_controller.py", CRUD_USUARIOS_CONTROLLER_PY)
    
    # --- Routes ---
    _write(target_dir / "routes/crudUsuarios_router.py", CRUD_USUARIOS_ROUTER_PY)
    
    # --- Schemas ---
    _write(target_dir / "schemas/schemas.py", SCHEMAS_PY)
    
    # --- Utils ---
    _write(target_dir / "utils/logger.py", LOGGER_PY)
    _write(target_dir / "utils/defaultUser.py", DEFAULT_USER_PY)

    # --- Services ---
    _write(target_dir / "services/crudUsuarios_service.py", CRUD_USUARIOS_SERVICE_PY)

    # --- Helpers ---
    _write(target_dir / "helpers/validate_dataframe_helper.py", VALIDATE_DATAFRAME_HELPER_PY)

    # --- Static ---
    import base64
    (target_dir / "static/img").mkdir(parents=True, exist_ok=True)
    with open(target_dir / "static/img/favicon.ico", "wb") as _f:
        _f.write(base64.b64decode(FAVICON_ICO_B64))

    # --- Docker ---
    dockerfile = (
        DOCKERFILE_WITH_PERROBOT
        .replace("{perrobot_token}", token_perrobot or "")
        .replace("{port}", str(port))
        if perrobot else
        DOCKERFILE_BASE.replace("{port}", str(port))
    )
    _write(target_dir / "Dockerfile", dockerfile)
    _write(target_dir / "sshd_config", SSHD_CONFIG)

    # Build docker-compose programmatically
    build_section = f"build: ./{target_dir.name}"

    depends_on_section = (
        "\n    depends_on:\n"
        "      db:\n"
        "        condition: service_healthy"
        if include_db_container else ""
    )

    db_service_section = (
        "\n  db:\n"
        "    image: postgres:15-alpine\n"
        "    environment:\n"
        "      POSTGRES_USER: ${usernameDBLocal}\n"
        "      POSTGRES_PASSWORD: ${passwordDBLocal}\n"
        "      POSTGRES_DB: ${databasenameDBLocal}\n"
        "    volumes:\n"
        "      - postgres_data:/var/lib/postgresql/data\n"
        "    ports:\n"
        "      - \"5432:5432\"\n"
        "    healthcheck:\n"
        "      test: [\"CMD-SHELL\", \"pg_isready -U ${usernameDBLocal}\"]\n"
        "      interval: 5s\n"
        "      timeout: 5s\n"
        "      retries: 5"
        if include_db_container else ""
    )

    volumes_section = "\nvolumes:\n  postgres_data:\n" if include_db_container else ""

    environment_section = (
        f"\n    environment:\n"
        f"      - APP_ENV={app_env}"
    )

    docker_compose = (
        f"services:\n"
        f"  {project_slug}:\n"
        f"    container_name: {project_slug}\n"
        f"    image: acrdev{project_slug}.azurecr.io/{project_slug}:latest\n"
        f"    {build_section}\n"
        f"    env_file:\n"
        f"      - ./{target_dir.name}/.env"
        f"{environment_section}\n"
        f"    ports:\n"
        f"      - \"{port}:{port}\"\n"
        f"    volumes:\n"
        f"      - ./{target_dir.name}:/app"
        f"{depends_on_section}"
        f"{db_service_section}"
        f"{volumes_section}"
    )
    _write(target_dir.parent / "docker-compose.yml", docker_compose)

    # --- .gitignore ---
    gitignore_content = (
        "# Python\n"
        "__pycache__/\n"
        "*.py[cod]\n"
        "*$py.class\n"
        ".python-version\n\n"
        "# Distribution\n"
        "dist/\n"
        "build/\n"
        "*.egg-info/\n\n"
        "# Environments\n"
        ".venv/\n"
        "venv/\n"
        "env/\n\n"
        "# IDEs\n"
        ".vscode/\n"
        ".idea/\n\n"
        "# Environment variables\n"
        ".env\n\n"
        "# Database\n"
        "*.sqlite\n"
        "*.db\n\n"
        "# Logs\n"
        "*.log\n\n"
        "# uv\n"
        "uv.lock\n\n"
        "# CI/CD secrets (do not commit)\n"
        "settings/repo-publishprofile-dev-001.yml\n"
        "settings/repo-secrets-dev.env\n"
        "settings/repo-variables-dev.env\n"
    )
    _write(target_dir.parent / ".gitignore", gitignore_content)

    # --- init_container.sh ---
    init_sh = (
        INIT_CONTAINER_SH
        .replace("{project_name}", name)
        .replace("{port}", str(port))
    )
    _write_lf(target_dir / "init_container.sh", init_sh)

    # --- Requirements ---
    _write(target_dir / "requirements.txt", REQUIREMENTS_TEMPLATE)

    # --- .env ---
    db_prod_data = db_prod or {"username": "", "password": "", "server": "", "dbname": ""}
    env_content = ENV_TEMPLATE.format(
        api_key=api_secrets["API_KEY"],
        x_api_key=api_secrets["X_API_KEY"],
        docs_api_key=api_secrets["DOCS_API_KEY"],
        secret_key=api_secrets["SECRET_KEY"],
        fernet_key=api_secrets["FERNET_KEY"],
        algorithm=api_secrets["ALGORITHM"],
        app_env=app_env,
        db_local_username=db_local["username"],
        db_local_password=db_local["password"],
        db_local_server=db_local["server"],
        db_local_dbname=db_local["dbname"],
        db_prod_username=db_prod_data["username"],
        db_prod_password=db_prod_data["password"],
        db_prod_server=db_prod_data["server"],
        db_prod_dbname=db_prod_data["dbname"],
        admin_username=admin["username"],
        admin_password=admin["password"],
        passhash_admin_bot=passhash_admin_bot or "",
    )
    _write(target_dir / ".env", env_content)

    # --- Main README ---
    readme_content = README_TEMPLATE.format(
        project_name=name,
        project_description=description,
        project_slug=project_slug,
        host=host,
        port=port,
    )
    _write(target_dir / "README.md", readme_content)
