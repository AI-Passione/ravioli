import duckdb
import os
import pandas as pd
import logging
from ravioli.backend.core.config import settings

from ravioli.backend.data.olap.ingestion.ingestor import DataIngestor

logger = logging.getLogger(__name__)

class DuckDBManager:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DuckDBManager, cls).__new__(cls)
        return cls._instance

    @property
    def connection(self):
        if self._connection is None:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(settings.duckdb_path), exist_ok=True)
            self._connection = duckdb.connect(str(settings.duckdb_path))
        return self._connection

    def list_tables(self):
        """
        List all user tables across all schemas in the DuckDB database.
        """
        conn = self.connection
        # Using information_schema to see all tables
        query = """
            SELECT table_schema || '.' || table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
        """
        return [row[0] for row in conn.execute(query).fetchall()]

    def query(self, sql: str):
        """
        Execute a query and return results as a list of dictionaries.
        Ensures results are JSON serializable (handles timestamps and NaNs).
        """
        df = self.connection.execute(sql).fetchdf()
        
        # Convert all timestamp columns to ISO format strings
        for col in df.select_dtypes(include=['datetime64', 'datetimetz']).columns:
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Replace NaN/NaT with None for JSON compliance
        return df.where(pd.notnull(df), None).to_dict(orient='records')

duckdb_manager = DuckDBManager()
data_ingestor = DataIngestor(duckdb_manager)
