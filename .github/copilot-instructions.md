# AI Coding Agent Instructions for ravioli

## Project Overview
ravioli is a monolithic data warehouse (DWH) repository for personal data analytics and AI. It implements an ELT (Extract, Load, Transform) pipeline designed to run 100% locally. The architecture emphasizes tool-agnostic design, with tooling abstracted into folder structure, prioritizing open-source solutions.

## Architecture
- **Monolithic Structure**: All components in a single repo for simplicity and local execution.
- **ELT Pipeline**:
  - **Extract & Load**: Data ingestion from various sources (manual scripts or Airbyte).
  - **Transform**: dbt Core for data modeling.
  - **Activate**: Metabase/Lightdash for reporting, Jupyter for analysis, Ollama for AI.
- **Key Components**:
  - `apps/data_ingestion/`: Manual Python scripts or Airbyte configs.
  - `apps/data_transformation/dbt/`: dbt project (currently minimal).
  - `apps/data_activation/`: BI tools like Metabase.
  - `docker/`: Local Postgres setup with docker-compose.
- **Database Schemas**:
  - `marts`: Consumer-ready modeled data.
  - `intermediate`: Transformation intermediates.
  - `staging`: Raw data landing.
  - `s_<source>`: Source-specific ODS (e.g., `s_spotify`).

## Developer Workflows
- **Start Local Stack**: Run `make up` to launch Postgres via Docker Compose. Creates `.env` if missing.
- **Dependency Management**: Use `uv` for Python deps (e.g., `uv pip install -r requirements.txt`). Root `requirements.txt` includes core libs; source-specific scripts may have additional deps.
- **Run Ingestion**: Use `make ingest-<source>` (e.g., `make ingest-spotify`) to execute manual ingestion scripts. Scripts scan `~/Documents/ravioli_local_data/<source>/` for JSON/CSV files.
- **Environment**: Load config from `docker/.env` using `python-dotenv`. Defaults: host=localhost, db=ravioli_db, user=ravioli_user, pass=ravioli_password.

## Coding Patterns
- **Ingestion Scripts** (`apps/data_ingestion/manual_job/<source>/ingest.py`):
  - Use `psycopg2` with `sql.Identifier` for safe SQL construction.
  - Create schema `s_<source>` if not exists.
  - Flatten nested JSON/CSV data into tabular format.
  - Drop/recreate tables for idempotency (suitable for personal data).
  - Use `tqdm` for progress bars, `execute_values` for batch inserts.
  - Import common utilities from `utils/ingestion_utils.py` (e.g., `load_env`, `get_db_connection`, `ensure_schema`).
  - Example: [apps/data_ingestion/manual_job/spotify/ingest.py](apps/data_ingestion/manual_job/spotify/ingest.py)
- **Data Safety**: PII stays in local `LOCAL_DATA_PATH` (default `~/Documents/ravioli_local_data/`), never committed to Git.
- **Error Handling**: Basic try/except with sys.exit(1) on critical failures.
- **Naming**: snake_case for files/folders, clean column names (lowercase, underscores).

## Dependencies & Tools
- **Core Libs**: psycopg2-binary, python-dotenv, tqdm, lxml, openpyxl.
- **Local Dev**: Docker for Postgres, uv for Python env.
- **CI/CD**: GitHub Actions (not yet configured).
- **Transformation**: dbt Core (project structure TBD).
- **Shared Utils**: Common ingestion utilities in `utils/ingestion_utils.py`.

## Integration Points
- **Database Connection**: Always via env vars, connect to local Postgres.
- **Cross-Component**: Ingestion loads to `staging`/`s_<source>`, dbt transforms to `intermediate`/`marts`.
- **External APIs**: Manual scripts may pull from APIs (e.g., Spotify exports), but prioritize local file processing for PII safety.

## Philosophy
- Tools-agnostic: Logic separated from tools; folder structure reflects capabilities.
- Open-source first.
- 100% local runnable.
- Casual attitude, serious architecture ("Es ist mir wurst" - it doesn't matter, but excellence in DWH design).</content>
<parameter name="filePath">/Users/jimmypang/VSCodeProjects/ravioli/.github/copilot-instructions.md