import logging
from langchain_core.tools import tool
from ravioli.backend.data.olap.ingestion.Legacy.base import CSVIngestor
from ravioli.backend.core.dbt import run_dbt_command

logger = logging.getLogger(__name__)

@tool
def ingest_data_tool(file_path: str):
    """
    Ingests a CSV file into the database. 
    Input should be the full absolute path to the CSV file.
    """
    ingestor = CSVIngestor(schema_name="staging", table_name="raw_ingestion")
    try:
        ingestor.run(file_path)
        return f"Successfully ingested {file_path}"
    except Exception as e:
        logger.error(f"Ingestion tool failed: {e}")
        return f"Error: {e}"

@tool
def run_transformations_tool(command: str = "build"):
    """
    Runs dbt transformations to process data. 
    Input can be 'run' or 'build'. Default is 'build'.
    """
    try:
        return run_dbt_command(command)
    except Exception as e:
        logger.error(f"Transformations tool failed: {e}")
        return f"Error: {e}"
