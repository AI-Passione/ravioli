import duckdb
import os
from pathlib import Path
import pandas as pd
import logging
from ravioli.backend.core.config import settings

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

    def ingest_csv(self, file_path: Path, table_name: str, schema: str = "main") -> int:
        """
        Ingest a CSV file into a DuckDB table.
        If the table exists, it will be replaced.
        Returns the row count.
        """
        conn = self.connection
        
        # Create schema if it doesn't exist
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        
        full_table_name = f'"{schema}"."{table_name}"'
        
        # Using DuckDB's native CSV reader for high performance
        query = f"CREATE OR REPLACE TABLE {full_table_name} AS SELECT * FROM read_csv_auto('{file_path}')"
        conn.execute(query)
        
        # Get row count
        count = conn.execute(f"SELECT COUNT(*) FROM {full_table_name}").fetchone()[0]
        return count

    async def ingest_xlsx(self, file_path: Path, base_table_name: str, schema: str = "main", ollama_client=None) -> list:
        """
        Ingest an XLSX file into DuckDB.
        Loops through all worksheets, validates content with AI if client provided,
        and creates tables with __xlsx postfix.
        Returns a list of ingestion results.
        """
        conn = self.connection
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        
        results = []
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            logger.info(f"Scanning XLSX file: {file_path.name}. Found {len(sheet_names)} sheets: {sheet_names}")
            
            for sheet_name in sheet_names:
                # Clean sheet name for table naming
                clean_sheet_name = "".join(c if c.isalnum() else "_" for c in sheet_name).lower()
                table_name = f"{base_table_name}_{clean_sheet_name}__xlsx"
                full_table_name = f'"{schema}"."{table_name}"'
                
                # Load a raw sample for structural analysis (no header)
                df_raw_sample = pd.read_excel(file_path, sheet_name=sheet_name, nrows=10, header=None)
                
                # Create a Visual Grid for the AI to understand the structure
                grid_lines = []
                for idx, row in df_raw_sample.iterrows():
                    # Clean up values for readability
                    row_vals = [str(val).strip().replace("\n", " ") for val in row.tolist()]
                    grid_lines.append(f"Row {idx}: | " + " | ".join(row_vals) + " |")
                sample_grid = "\n".join(grid_lines)
                
                # AI Validation & Handling Strategy
                verdict = "ready"
                reason = "No AI validation performed."
                header_row = 0
                
                if ollama_client:
                    validation = await ollama_client.validate_sheet_content(sheet_name, sample_grid)
                    verdict = validation.get("verdict", "ready")
                    reason = validation.get("reason", "Accepted by AI.")
                    header_row = validation.get("header_row", 0)
                
                if verdict == "reject":
                    logger.warning(f"Sheet '{sheet_name}' REJECTED for ingestion. Reason: {reason}")
                    results.append({
                        "sheet_name": sheet_name,
                        "table_name": table_name,
                        "status": "failed",
                        "error": reason
                    })
                    continue
                
                logger.info(f"AI Verdict for '{sheet_name}': {verdict} (Header Row: {header_row}). Reason: {reason}")
                
                # Load full data using the detected header row
                if header_row > 0:
                    logger.info(f"Structural Offset detected in '{sheet_name}'. Re-reading with header at row {header_row}...")
                
                applied_fix = False
                if verdict == "no_headers":
                    logger.info(f"No headers detected in '{sheet_name}'. Using generic placeholders (col_1, col_2, ...)")
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, skiprows=header_row)
                    df.columns = [f"col_{i+1}" for i in range(len(df.columns))]
                    applied_fix = True
                else:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)

                if verdict == "needs_fix" and ollama_client:
                    logger.info(f"Applying AI Schema Fix for sheet '{sheet_name}' (Verdict: needs_fix)...")
                    original_cols = df.columns.tolist()
                    
                    # For schema fix, we use a grid sample WITH the correct headers
                    fix_grid_lines = []
                    fix_grid_lines.append("Headers: | " + " | ".join(original_cols) + " |")
                    for f_idx, f_row in df.head(5).iterrows():
                        f_vals = [str(val).strip().replace("\n", " ") for val in f_row.tolist()]
                        fix_grid_lines.append(f"Row {f_idx}: | " + " | ".join(f_vals) + " |")
                    sample_grid_fix = "\n".join(fix_grid_lines)
                    
                    mapping = await ollama_client.suggest_schema_fix(sheet_name, sample_grid_fix)
                    filtered_mapping = {k: v for k, v in mapping.items() if k in df.columns}
                    
                    if filtered_mapping:
                        logger.info(f"AI Schema Fix for '{sheet_name}' - INPUT: {original_cols}")
                        logger.info(f"AI Schema Fix for '{sheet_name}' - OUTPUT: {list(filtered_mapping.values())}")
                        df = df.rename(columns=filtered_mapping)
                        applied_fix = True
                    else:
                        logger.info(f"AI Schema Fix for '{sheet_name}': No valid mapping returned.")
                elif verdict != "no_headers":
                    logger.info(f"Sheet '{sheet_name}' proceeding with direct ingestion (Verdict: {verdict}).")
                
                conn.execute(f"CREATE OR REPLACE TABLE {full_table_name} AS SELECT * FROM df")
                
                count = conn.execute(f"SELECT COUNT(*) FROM {full_table_name}").fetchone()[0]
                logger.info(f"Sheet '{sheet_name}' successfully ingested into {full_table_name} ({count} rows). Fix applied: {applied_fix}")
                
                results.append({
                    "sheet_name": sheet_name,
                    "table_name": table_name,
                    "status": "completed",
                    "row_count": count,
                    "reason": reason
                })
                
        except Exception as e:
            logger.error(f"Failed to process XLSX file {file_path}: {e}")
            raise e
            
        return results
        
    def query(self, sql: str):
        """
        Execute a SQL query and return the result as a list of dictionaries.
        """
        conn = self.connection
        result = conn.execute(sql).fetchdf()
        return result.to_dict(orient="records")

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

duckdb_manager = DuckDBManager()
