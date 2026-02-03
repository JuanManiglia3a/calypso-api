
import typer
import uvicorn
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
    destino: Path = typer.Argument(..., file_okay=False, dir_okay=True, readable=True, writable=True, help="Directorio destino"),
    nombre: str = typer.Argument(..., help="Nombre del proyecto"),
    host: str = typer.Option("127.0.0.1", help="Host para la aplicación"),
    port: int = typer.Option(8000, help="Puerto para la aplicación"),
    docker: bool = typer.Option(True, help="Incluir configuración de Docker")
):
    generate(destino, nombre, host, port, docker)
    typer.echo(f"Estructura creada en {destino}")

if __name__ == "__main__":
    app()
