
import typer
import uvicorn
from typing import Optional
from calypso_api.core import config
from pathlib import Path
from calypso_api.scaffold import generate

app = typer.Typer()

@app.command()
def run(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = True
):
    uvicorn.run(
        "calypso_api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info" if config.DEBUG else "warning"
    )

@app.command()
def shell():
    import IPython
    from calypso_api.database.db import engine
    
    typer.echo("Opening shell...")
    IPython.embed(header="API Template Shell", colors="neutral")

@app.command()
def init(
    destino: Optional[Path] = typer.Argument(None, help="Directorio destino"),
    nombre: Optional[str] = typer.Argument(None, help="Nombre del proyecto"),
    host: str = typer.Option("127.0.0.1", help="Host para la aplicación"),
    port: int = typer.Option(8000, help="Puerto para la aplicación"),
    docker: bool = typer.Option(True, help="Incluir configuración de Docker"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Habilitar modo interactivo para opciones avanzadas")
):
    """
    Inicializa un nuevo proyecto Calypso.
    
    Si no se proporcionan argumentos, se solicitarán de forma interactiva.
    """
    if destino is None:
        typer.secho("👋 ¡Bienvenido al asistente de creación de proyectos Calypso!", fg=typer.colors.GREEN, bold=True)
        destino_str = typer.prompt("📂 ¿Dónde quieres crear el proyecto? (Directorio destino)")
        destino = Path(destino_str)
    
    if nombre is None:
        nombre = typer.prompt("📦 ¿Cuál es el nombre de tu proyecto?")
        
    if interactive:
        host = typer.prompt("🌐 Host para la aplicación", default=host)
        port = typer.prompt("🔌 Puerto para la aplicación", default=port, type=int)
        docker = typer.confirm("🐳 ¿Incluir configuración de Docker?", default=docker)

    generate(destino, nombre, host, port, docker)
    
    typer.secho(f"\n✨ Estructura creada exitosamente en {destino}", fg=typer.colors.GREEN, bold=True)
    typer.echo("🚀 Para iniciar:")
    typer.secho(f"  cd {destino}", fg=typer.colors.CYAN)
    typer.secho("  calypso run", fg=typer.colors.CYAN)

if __name__ == "__main__":
    app()
