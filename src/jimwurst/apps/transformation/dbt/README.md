# dbt Core for jimwurst

This directory contains the dbt Core project for data transformation in jimwurst.

## Structure

- `models/staging/`: Staging models that clean and standardize raw data from sources.
- `models/intermediate/`: Intermediate models for complex transformations.
- `models/marts/`: Final business-ready models for BI tools.

## Usage

1. Ensure the database is running: `make up`
2. Run dbt commands from this directory:
   - `uv run dbt debug` to test connection
   - `uv run dbt build` to run all models
   - `uv run dbt run --select staging` to run staging models

## Profiles

Configured in `~/.dbt/profiles.yml` for local Postgres.
