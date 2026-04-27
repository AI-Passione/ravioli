import dlt
from ravioli.backend.core.config import settings

def create_ravioli_pipeline(pipeline_name: str, dataset_name: str = "main"):
    """
    Creates a dlt pipeline configured to use the Ravioli DuckDB instance.
    """
    # dlt duckdb destination accepts a file path
    return dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=dlt.destinations.duckdb(str(settings.duckdb_path)),
        dataset_name=dataset_name
    )
