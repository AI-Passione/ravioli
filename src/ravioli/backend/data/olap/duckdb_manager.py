import duckdb
import os
from pathlib import Path
from ravioli.backend.core.config import settings

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

    def ingest_csv(self, file_path: Path, table_name: str) -> int:
        """
        Ingest a CSV file into a DuckDB table.
        If the table exists, it will be replaced.
        Returns the row count.
        """
        conn = self.connection
        # Using DuckDB's native CSV reader for high performance
        query = f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{file_path}')"
        conn.execute(query)
        
        # Get row count
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        return count
        
    def query(self, sql: str):
        """
        Execute a SQL query and return the result as a list of dictionaries.
        """
        conn = self.connection
        result = conn.execute(sql).fetchdf()
        return result.to_dict(orient="records")

    def list_tables(self):
        """
        List all tables in the DuckDB database.
        """
        conn = self.connection
        return [row[0] for row in conn.execute("SHOW TABLES").fetchall()]

duckdb_manager = DuckDBManager()
