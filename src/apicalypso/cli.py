
import typer
import uvicorn
import secrets
from typing import Optional
from pathlib import Path
from cryptography.fernet import Fernet
from apicalypso.scaffold import generate

app = typer.Typer()

WELCOME_BANNER = """
╔══════════════════════════════════════════════════════════╗
║              Bienvenido a  C A L Y P S O  API            ║
║                                                          ║
║  Tu punto de partida para crear APIs robustas con        ║
║  FastAPI + SQLAlchemy Async + PostgreSQL + Docker.       ║
║  En minutos tendrás una base lista para producción.      ║
╚══════════════════════════════════════════════════════════╝
"""


@app.command()
def run(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = True,
):
    from apicalypso.core import config
    uvicorn.run(
        "apicalypso.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info" if config.DEBUG else "warning",
    )


@app.command()
def shell():
    import IPython
    from apicalypso.database.db import engine

    typer.echo("Opening shell...")
    IPython.embed(header="Calypso API Shell", colors="neutral")


@app.command()
def init(
    destino: Optional[Path] = typer.Argument(None, help="Directorio destino"),
    nombre: Optional[str] = typer.Argument(None, help="Nombre del proyecto"),
):
    """
    Inicializa un nuevo proyecto Calypso de forma interactiva.
    """
    typer.secho(WELCOME_BANNER, fg=typer.colors.CYAN, bold=True)

    # ── Paso 1: Proyecto ───────────────────────────────────────────────────────
    typer.secho("[ 1 / 7 ]  Proyecto", fg=typer.colors.BRIGHT_BLUE, bold=True)

    if destino is None:
        destino_str = typer.prompt("  📂 Directorio destino")
        destino = Path(destino_str)

    if nombre is None:
        nombre = typer.prompt("  📦 Nombre del proyecto")

    descripcion = typer.prompt(
        "  📝 Descripción breve",
        default=f"API generada con Calypso para {nombre}",
    )

    # ── Paso 2: Entorno ────────────────────────────────────────────────────────
    typer.secho("\n[ 2 / 7 ]  Entorno", fg=typer.colors.BRIGHT_BLUE, bold=True)

    modo_opciones = ["Local", "Producción"]
    typer.echo("  🌍 Modo de ejecución:")
    for i, m in enumerate(modo_opciones, 1):
        typer.echo(f"     {i}) {m}")
    modo_idx = typer.prompt("  Elige (1/2)", default="1")
    modo = modo_opciones[int(modo_idx) - 1] if modo_idx in ("1", "2") else "Local"

    app_env_opciones = ["develop", "staging", "production"]
    typer.echo("  🏷️  App environment:")
    for i, e in enumerate(app_env_opciones, 1):
        typer.echo(f"     {i}) {e}")
    env_idx = typer.prompt("  Elige (1/2/3)", default="1")
    app_env = app_env_opciones[int(env_idx) - 1] if env_idx in ("1", "2", "3") else "develop"

    # ── Paso 3: BD Local ───────────────────────────────────────────────────────
    typer.secho("\n[ 3 / 7 ]  Base de datos local", fg=typer.colors.BRIGHT_BLUE, bold=True)
    project_slug = nombre.lower().replace(" ", "_")

    db_local = {
        "username": typer.prompt("  Usuario",    default="postgres"),
        "password": typer.prompt("  Contraseña", default="postgres", hide_input=True),
        "server":   typer.prompt("  Host",        default="localhost"),
        "dbname":   typer.prompt("  Nombre BD",   default=project_slug),
    }

    # ── Paso 4: BD Producción ──────────────────────────────────────────────────
    typer.secho("\n[ 4 / 7 ]  Base de datos producción", fg=typer.colors.BRIGHT_BLUE, bold=True)
    configurar_prod = typer.confirm("  ¿Quieres configurarla ahora?", default=False)
    db_prod = None
    if configurar_prod:
        db_prod = {
            "username": typer.prompt("  Usuario"),
            "password": typer.prompt("  Contraseña", hide_input=True),
            "server":   typer.prompt("  Host (ej: server.postgres.database.azure.com)"),
            "dbname":   typer.prompt("  Nombre BD"),
        }

    # ── Paso 5: Usuario admin ──────────────────────────────────────────────────
    typer.secho("\n[ 5 / 7 ]  Usuario administrador de la API", fg=typer.colors.BRIGHT_BLUE, bold=True)
    admin = {
        "username": typer.prompt("  Username", default="admin"),
        "password": typer.prompt("  Contraseña", hide_input=True),
    }

    # ── Paso 6: PerroBot ───────────────────────────────────────────────────────
    typer.secho("\n[ 6 / 7 ]  PerroBot", fg=typer.colors.BRIGHT_BLUE, bold=True)
    typer.echo("  PerroBot habilita el envío de mensajes desde la API.")
    usar_perrobot = typer.confirm("  ¿Usar PerroBot?", default=False)
    token_perrobot = None
    passhash_admin_bot = None
    if usar_perrobot:
        token_perrobot = typer.prompt("  TOKEN_PERROBOT (GitHub PAT)", hide_input=True)
        passhash_admin_bot = typer.prompt("  Contraseña admin de PerroBot", hide_input=True)

    # ── Paso 7: Secretos API ───────────────────────────────────────────────────
    typer.secho("\n[ 7 / 7 ]  Secretos de la API", fg=typer.colors.BRIGHT_BLUE, bold=True)
    generar_auto = typer.confirm("  ¿Generar secretos automáticamente?", default=True)

    if generar_auto:
        api_secrets = {
            "API_KEY":      secrets.token_urlsafe(48),
            "X_API_KEY":    secrets.token_urlsafe(48),
            "DOCS_API_KEY": secrets.token_urlsafe(48),
            "SECRET_KEY":   secrets.token_hex(32),
            "FERNET_KEY":   Fernet.generate_key().decode(),
            "ALGORITHM":    "HS256",
        }
        typer.secho("\n  ✅ Secretos generados automáticamente.", fg=typer.colors.GREEN)
    else:
        api_secrets = {
            "API_KEY":      typer.prompt("  API_KEY"),
            "X_API_KEY":    typer.prompt("  X_API_KEY"),
            "DOCS_API_KEY": typer.prompt("  DOCS_API_KEY"),
            "SECRET_KEY":   typer.prompt("  SECRET_KEY"),
            "FERNET_KEY":   typer.prompt("  FERNET_KEY"),
            "ALGORITHM":    typer.prompt("  ALGORITHM", default="HS256"),
        }

    # ── Generar ────────────────────────────────────────────────────────────────
    typer.echo("")
    typer.secho("  Generando estructura del proyecto...", fg=typer.colors.YELLOW)

    generate(
        target_dir=destino,
        name=nombre,
        description=descripcion,
        host="0.0.0.0",
        port=8000,
        modo=modo,
        app_env=app_env,
        perrobot=usar_perrobot,
        db_local=db_local,
        db_prod=db_prod,
        admin=admin,
        api_secrets=api_secrets,
        token_perrobot=token_perrobot,
        passhash_admin_bot=passhash_admin_bot,
    )

    # ── Resumen ────────────────────────────────────────────────────────────────
    typer.secho(f"\n✨ Proyecto '{nombre}' creado exitosamente en {destino}", fg=typer.colors.GREEN, bold=True)

    if generar_auto:
        typer.secho("\n🔑 Secretos generados (guárdalos, ya están en tu .env):", fg=typer.colors.YELLOW, bold=True)
        for k, v in api_secrets.items():
            typer.echo(f"   {k}={v}")

    typer.echo("\n🚀 Para iniciar:")
    typer.secho(f"   cd {destino}", fg=typer.colors.CYAN)
    typer.secho("   docker compose up --build -d", fg=typer.colors.CYAN)
    typer.echo("")


if __name__ == "__main__":
    app()
