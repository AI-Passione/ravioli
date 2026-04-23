import typer
from typing import Optional
from pathlib import Path
from jimwurst.core.config import settings
from jimwurst.core.dbt import run_dbt_command as dbt_run
from jimwurst.db.session import ensure_schema

app = typer.Typer(help="Jimwurst Data Platform CLI")
ingest_app = typer.Typer(help="Data Ingestion Commands")
app.add_typer(ingest_app, name="ingest")

@ingest_app.command("apple-health")
def ingest_apple_health(file_path: Optional[Path] = None):
    """Ingest Apple Health XML export."""
    from jimwurst.ingestion.apple_health import AppleHealthIngestor
    AppleHealthIngestor().run(file_path)

@ingest_app.command("spotify")
def ingest_spotify(data_path: Optional[Path] = None):
    """Ingest Spotify JSON/CSV export."""
    from jimwurst.ingestion.spotify import SpotifyIngestor
    SpotifyIngestor().run(data_path)

@ingest_app.command("linkedin")
def ingest_linkedin(data_path: Optional[Path] = None):
    """Ingest LinkedIn Excel/CSV export."""
    from jimwurst.ingestion.linkedin import LinkedInIngestor
    LinkedInIngestor().run(data_path)

@ingest_app.command("substack")
def ingest_substack(data_path: Optional[Path] = None):
    """Ingest Substack CSV export."""
    from jimwurst.ingestion.substack import SubstackIngestor
    SubstackIngestor().run(data_path)

@app.command()
def transform(command: str = "build"):
    """Run dbt transformations."""
    print(f"Running dbt {command}...")
    result = dbt_run(command)
    print(result)

@app.command()
def agent():
    """Start the AI Agent UI."""
    import subprocess
    frontend_path = Path(__file__).parent.parent.parent / "apps" / "agents" / "ollama" / "frontend" / "app.py"
    print(f"Starting Streamlit agent from {frontend_path}...")
    subprocess.run(["streamlit", "run", str(frontend_path)])

@app.command()
def db_init():
    """Initialize database schemas."""
    schemas = ["marts", "staging", "intermediate"]
    for s in schemas:
        ensure_schema(s)
    print("Database initialization complete.")

if __name__ == "__main__":
    app()
