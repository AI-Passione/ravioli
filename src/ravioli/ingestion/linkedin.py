import os
import pandas as pd
from tqdm import tqdm
from psycopg2 import sql
from ravioli.ingestion.base import BaseIngestor
from ravioli.db.session import get_db_connection, ensure_schema, get_engine
from ravioli.core.config import settings

class LinkedInIngestor(BaseIngestor):
    def __init__(self):
        super().__init__(schema_name="s_linkedin", table_name="multi_table")

    def clean_header(self, h):
        return str(h).strip().lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')

    def ingest_excel(self, file_path: str, table_prefix: str):
        xls = pd.ExcelFile(file_path, engine="openpyxl")
        for sheet_name in xls.sheet_names:
            df = xls.parse(sheet_name)
            if df.empty:
                continue
            
            df.columns = [self.clean_header(c) for c in df.columns]
            table_name = f"{table_prefix}_{sheet_name.lower().replace(' ', '_')}"
            
            print(f"Loading sheet {sheet_name} to {table_name}...")
            df.to_sql(table_name, get_engine(), schema=self.schema_name, if_exists='replace', index=False)

    def ingest_csv(self, file_path: str, table_name: str):
        df = pd.read_csv(file_path)
        df.columns = [self.clean_header(c) for c in df.columns]
        df.to_sql(table_name, get_engine(), schema=self.schema_name, if_exists='replace', index=False)

    def ingest(self, data_path: str = None):
        if data_path is None:
            data_path = settings.local_data_path / "linkedin"
        
        basic_path = data_path / "basic"
        complete_path = data_path / "complete"
        
        ensure_schema(self.schema_name)
        
        # Basic (Excel)
        if basic_path.exists():
            for f in basic_path.glob("*.xlsx"):
                self.ingest_excel(str(f), f"basic_{f.stem.lower()}")
        
        # Complete (CSV)
        if complete_path.exists():
            for f in complete_path.glob("*.csv"):
                self.ingest_csv(str(f), f"complete_{f.stem.lower()}")
        
        print("LinkedIn ingestion complete.")
