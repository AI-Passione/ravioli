import os
from abc import ABC, abstractmethod
from typing import Optional, List, Any
import pandas as pd
from tqdm import tqdm
from jimwurst.db.session import get_db_connection, ensure_schema, get_engine
from jimwurst.core.config import settings

class BaseIngestor(ABC):
    """
    Base class for all data ingestors.
    Provides standardized methods for DB connection, schema management, and ingestion.
    """
    
    def __init__(self, schema_name: str, table_name: str):
        self.schema_name = schema_name
        self.table_name = table_name
        self.engine = get_engine()

    def run(self, *args, **kwargs):
        """Main entry point for the ingestor."""
        print(f"Starting ingestion for {self.schema_name}.{self.table_name}...")
        ensure_schema(self.schema_name)
        return self.ingest(*args, **kwargs)

    @abstractmethod
    def ingest(self, *args, **kwargs):
        """Implement the actual ingestion logic here."""
        pass

    def load_to_db(self, df: pd.DataFrame, if_exists: str = "replace"):
        """Utility to load a DataFrame to the database."""
        print(f"Loading {len(df)} rows to {self.schema_name}.{self.table_name}...")
        df.to_sql(
            self.table_name,
            self.engine,
            schema=self.schema_name,
            if_exists=if_exists,
            index=False
        )
        print("Done.")

class CSVIngestor(BaseIngestor):
    """Generic ingestor for CSV files."""
    
    def ingest(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found.")
        
        df = pd.read_csv(file_path)
        # Standard cleaning
        df.columns = [c.strip().lower().replace(' ', '_').replace('-', '_') for c in df.columns]
        self.load_to_db(df)
