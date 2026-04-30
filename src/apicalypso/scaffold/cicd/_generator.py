"""
scaffold/cicd/_generator.py

Generates CI/CD files for a given resource type (currently: api).
Extensible: add more resource_type branches or template functions as needed.
"""
from pathlib import Path

from .._io import _write, _write_lf
from ._templates import (
    WORKFLOW_YML,
    SET_SECRETS_PS1,
    PUBLISH_PROFILE_PLACEHOLDER,
    REPO_SECRETS_TEMPLATE,
    REPO_VARIABLES_TEMPLATE,
)


def generate_cicd(
    project_root: Path,
    slug: str,
    name: str,
    api_secrets: dict,
    folder_name: str | None = None,
    db_prod: dict | None = None,
    admin: dict | None = None,
    perrobot_token: str | None = None,
    app_env: str = "develop",
    passhash_admin_bot: str | None = None,
    resource_type: str = "api",
) -> None:
    """
    Generate CI/CD scaffolding for the specified resource type.

    Parameters
    ----------
    project_root   Root of the generated project (where settings/ will live).
    slug           project_slug (lowercase, underscores) — used for image names.
    folder_name    Name of the target directory (e.g. 'api'). Defaults to slug.
    name           Human-readable project name.
    api_secrets    Dict with API_KEY, X_API_KEY, DOCS_API_KEY, SECRET_KEY,
                   FERNET_KEY, ALGORITHM.
    db_prod        Optional dict with username/password/server/dbname for prod DB.
    admin          Dict with username/password for the default admin user.
    perrobot_token PerroBot GitHub PAT (if used).
    app_env        Application environment string (default: "develop").
    passhash_admin_bot  PerroBot admin password hash.
    resource_type  Type of resource ("api" | future: "chatbot", "aci", ...).
    """
    if resource_type == "api":
        _generate_api_cicd(
            project_root=project_root,
            slug=slug,
            folder_name=folder_name or slug,
            name=name,
            api_secrets=api_secrets,
            db_prod=db_prod,
            admin=admin,
            perrobot_token=perrobot_token,
            app_env=app_env,
            passhash_admin_bot=passhash_admin_bot,
        )
    else:
        raise NotImplementedError(f"resource_type '{resource_type}' not yet supported.")


def _generate_api_cicd(
    project_root: Path,
    slug: str,
    folder_name: str,
    name: str,
    api_secrets: dict,
    db_prod: dict | None,
    admin: dict | None,
    perrobot_token: str | None,
    app_env: str,
    passhash_admin_bot: str | None,
) -> None:
    acr_slug = slug.replace("_", "")
    acr_server   = f"acr-dev-{acr_slug}.azurecr.io"
    acr_username = f"acr-dev-{acr_slug}"
    app_name     = f"app-dev-api{acr_slug}"
    db = db_prod or {"username": "", "password": "", "server": "", "dbname": ""}
    adm = admin or {"username": "", "password": ""}

    settings_dir = project_root / "settings"
    settings_dir.mkdir(parents=True, exist_ok=True)

    # 1. GitHub Actions workflow
    workflows_dir = project_root / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    workflow_content = WORKFLOW_YML.format(
        app_name=app_name,
        slug=slug,
        folder_name=folder_name,
    )
    _write(workflows_dir / f"dev-api-{acr_slug}.yml", workflow_content)

    # 2. setSecretsAndVariables.ps1
    _write(settings_dir / "setSecretsAndVariables.ps1", SET_SECRETS_PS1)

    # 3. repo-publishprofile-dev-001.yml  (placeholder)
    _write(settings_dir / "repo-publishprofile-dev-001.yml", PUBLISH_PROFILE_PLACEHOLDER)

    # 4. repo-secrets-dev.env
    secrets_content = REPO_SECRETS_TEMPLATE.format(
        acr_server=acr_server,
        acr_username=acr_username,
        project_name=name,
        db_prod_username=db["username"],
        db_prod_password=db["password"],
        db_prod_server=db["server"],
        db_prod_dbname=db["dbname"],
        api_key=api_secrets.get("API_KEY", ""),
        x_api_key=api_secrets.get("X_API_KEY", ""),
        docs_api_key=api_secrets.get("DOCS_API_KEY", ""),
        secret_key=api_secrets.get("SECRET_KEY", ""),
        fernet_key=api_secrets.get("FERNET_KEY", ""),
        algorithm=api_secrets.get("ALGORITHM", "HS256"),
        app_env=app_env,
        admin_username=adm["username"],
        admin_password=adm["password"],
        passhash_admin_bot=passhash_admin_bot or "",
        perrobot_token=perrobot_token or "",
    )
    _write(settings_dir / "repo-secrets-dev.env", secrets_content)

    # 5. repo-variables-dev.env
    variables_content = REPO_VARIABLES_TEMPLATE.format(app_name=app_name)
    _write(settings_dir / "repo-variables-dev.env", variables_content)
