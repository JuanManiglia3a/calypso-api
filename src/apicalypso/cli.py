
import typer
import uvicorn
import secrets
from typing import Optional
from pathlib import Path
from cryptography.fernet import Fernet
from apicalypso.scaffold import generate

app = typer.Typer()

def _confirmar(pregunta: str, default: bool = False) -> bool:
    """Prompt de Sí/No en español."""
    sufijo = " [S/n]: " if default else " [s/N]: "
    while True:
        respuesta = input(pregunta + sufijo).strip().lower()
        if respuesta == "":
            return default
        if respuesta in ("s", "si", "sí"):
            return True
        if respuesta in ("n", "no"):
            return False
        typer.echo("  Por favor responde 's' o 'n'.")

WELCOME_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║  Bienvenido a la librería de Calypso, hecha a mano desde el sur del mundo   ║
║                    por trabajadores migrantes orgánicos.                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
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

    app_env_opciones = ["develop", "production"]
    typer.echo("  🏷️  App environment:")
    for i, e in enumerate(app_env_opciones, 1):
        typer.echo(f"     {i}) {e}")
    env_idx = typer.prompt("  Elige (1/2)", default="1")
    app_env = app_env_opciones[int(env_idx) - 1] if env_idx in ("1", "2") else "develop"

    # ── Paso 3: BD Local ───────────────────────────────────────────────────────
    typer.secho("\n[ 3 / 7 ]  Base de datos local", fg=typer.colors.BRIGHT_BLUE, bold=True)
    project_slug = nombre.lower().replace(" ", "_")

    db_local = {
        "username": typer.prompt("  Usuario",    default="postgres"),
        "password": typer.prompt("  Contraseña", default="postgres", hide_input=True),
        "server":   typer.prompt("  Host",        default="localhost"),
        "dbname":   typer.prompt("  Nombre BD",   default=project_slug),
    }
    include_db_container = _confirmar(
        "  ¿Crear un contenedor PostgreSQL de prueba en Docker Compose?",
        default=False,
    )
    if include_db_container:
        typer.echo("  ℹ️  Se añadirá un servicio 'db' en docker-compose.yml.")
    else:
        typer.echo("  ℹ️  Se asume que tienes una instancia PostgreSQL ya disponible.")

    # ── Paso 3b: Puerto de la API ──────────────────────────────────────────────
    api_port = typer.prompt("  Puerto de la API (desarrollo)", default=8000, type=int)

    # ── Paso 4: BD Producción ──────────────────────────────────────────────────
    typer.secho("\n[ 4 / 7 ]  Base de datos producción", fg=typer.colors.BRIGHT_BLUE, bold=True)
    configurar_prod = _confirmar("  ¿Quieres configurarla ahora?", default=False)
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
    usar_perrobot = _confirmar("  ¿Usar PerroBot?", default=False)
    passhash_admin_bot = None
    token_perrobot = None
    if usar_perrobot:
        token_perrobot = typer.prompt("  Token de acceso a PerroBot (GitHub PAT)", hide_input=True)
        passhash_admin_bot = typer.prompt("  Contraseña admin de PerroBot", hide_input=True)

    # ── Paso 7: Secretos API ───────────────────────────────────────────────────
    typer.secho("\n[ 7 / 7 ]  Secretos de la API", fg=typer.colors.BRIGHT_BLUE, bold=True)
    generar_auto = _confirmar("  ¿Generar secretos automáticamente?", default=True)

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
        port=api_port,
        modo=modo,
        app_env=app_env,
        perrobot=usar_perrobot,
        include_db_container=include_db_container,
        db_local=db_local,
        db_prod=db_prod,
        admin=admin,
        api_secrets=api_secrets,
        passhash_admin_bot=passhash_admin_bot,
        token_perrobot=token_perrobot,
    )

    # ── Resumen ────────────────────────────────────────────────────────────────
    typer.secho(f"\n✨ Proyecto '{nombre}' creado exitosamente en {destino}", fg=typer.colors.GREEN, bold=True)

    if generar_auto:
        typer.secho("\n🔑 Secretos generados (guárdalos, ya están en tu .env):", fg=typer.colors.YELLOW, bold=True)
        for k, v in api_secrets.items():
            typer.echo(f"   {k}={v}")

    typer.echo("\n🚀 Para iniciar:")
    typer.secho("   docker compose up --build -d", fg=typer.colors.CYAN)
    typer.echo("")
    typer.secho("Gracias por utilizar tecnología Calypso. ¡Mucho éxito con tu proyecto! 🌍", fg=typer.colors.MAGENTA, bold=True)
    typer.echo("")


if __name__ == "__main__":
    app()
