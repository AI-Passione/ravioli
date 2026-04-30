import typer
from typing import Optional
from pathlib import Path
from ravioli.backend.core.config import settings
from ravioli.backend.core.dbt import run_dbt_command as dbt_run
from ravioli.backend.data.oltp.session import ensure_schema
from ravioli.backend.data.olap.ingestion.Legacy.apple_health import AppleHealthIngestor
from ravioli.backend.data.olap.ingestion.Legacy.spotify import SpotifyIngestor
from ravioli.backend.data.olap.ingestion.Legacy.linkedin import LinkedInIngestor
from ravioli.backend.data.olap.ingestion.Legacy.substack import SubstackIngestor
from ravioli.backend.data.olap.ingestion.Legacy.misc import BoltIngestor, TelegramIngestor

app = typer.Typer(help="Ravioli Data Platform CLI")
ingest_app = typer.Typer(help="Data Ingestion Commands")
app.add_typer(ingest_app, name="ingest")

@ingest_app.command("apple-health")
def ingest_apple_health(file_path: Optional[Path] = None):
    """Ingest Apple Health XML export."""
    AppleHealthIngestor().run(file_path)

@ingest_app.command("spotify")
def ingest_spotify(data_path: Optional[Path] = None):
    """Ingest Spotify JSON/CSV export."""
    SpotifyIngestor().run(data_path)

@ingest_app.command("linkedin")
def ingest_linkedin(data_path: Optional[Path] = None):
    """Ingest LinkedIn Excel/CSV export."""
    LinkedInIngestor().run(data_path)

@ingest_app.command("substack")
def ingest_substack(data_path: Optional[Path] = None):
    """Ingest Substack CSV export."""
    SubstackIngestor().run(data_path)

@ingest_app.command("bolt")
def ingest_bolt(file_path: Optional[Path] = None):
    """Ingest Bolt rides CSV."""
    BoltIngestor().run(file_path)

@ingest_app.command("telegram")
def ingest_telegram(file_path: Optional[Path] = None):
    """Ingest Telegram messages CSV."""
    TelegramIngestor().run(file_path)

@app.command()
def transform(command: str = "build"):
    """Run dbt transformations."""
    print(f"Running dbt {command}...")
    result = dbt_run(command)
    print(result)

@app.command()
def db_init():
    """Initialize database schemas."""
    schemas = ["marts", "staging", "intermediate"]
    for s in schemas:
        ensure_schema(s)
    print("Database initialization complete.")

if __name__ == "__main__":
    app()
