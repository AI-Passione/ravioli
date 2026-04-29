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
        Ingest an XLSX file into DuckDB with structural awareness.
        Loops through all worksheets, performs AI-driven structural analysis,
        and handles complex layouts (offsets, split tables, etc.).
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
                
                # 1. Structural Analysis Phase
                # Load a larger sample (20 rows) for structural analysis
                df_raw_sample = pd.read_excel(file_path, sheet_name=sheet_name, nrows=20, header=None)
                
                grid_lines = []
                for idx, row in df_raw_sample.iterrows():
                    # Clean up values for readability
                    row_vals = [str(val).strip().replace("\n", " ") for val in row.tolist()]
                    grid_lines.append(f"Row {idx}: | " + " | ".join(row_vals) + " |")
                sample_grid = "\n".join(grid_lines)
                
                analysis = {
                    "verdict": "ready",
                    "header_row": 0,
                    "data_start_row": 1,
                    "is_split": False,
                    "column_mapping": {}
                }
                
                if ollama_client:
                    analysis = await ollama_client.analyze_sheet_structure(sheet_name, sample_grid)
                
                verdict = analysis.get("verdict", "ready")
                if verdict == "reject":
                    logger.warning(f"Sheet '{sheet_name}' REJECTED by AI. Reason: {analysis.get('reason', 'No reason provided.')}")
                    results.append({
                        "sheet_name": sheet_name,
                        "table_name": table_name,
                        "status": "failed",
                        "error": analysis.get("reason", "Rejected by structural analysis.")
                    })
                    continue

                logger.info(f"AI Strategy for '{sheet_name}': {verdict}. Header Row: {analysis.get('header_row')}, Split: {analysis.get('is_split')}")

                # 2. Ingestion Phase
                try:
                    # Read the entire sheet without header first to apply fixes
                    df_full = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                    
                    df_final = self._process_sheet_with_analysis(df_full, analysis)
                    
                    if df_final is None or df_final.empty:
                        raise ValueError("Processed dataframe is empty or invalid.")

                    conn.execute(f"CREATE OR REPLACE TABLE {full_table_name} AS SELECT * FROM df_final")
                    
                    count = conn.execute(f"SELECT COUNT(*) FROM {full_table_name}").fetchone()[0]
                    logger.info(f"Sheet '{sheet_name}' successfully ingested into {full_table_name} ({count} rows).")
                    
                    results.append({
                        "sheet_name": sheet_name,
                        "table_name": table_name,
                        "status": "completed",
                        "row_count": count,
                        "reason": analysis.get("reason", "Success")
                    })
                except Exception as e:
                    logger.error(f"Error processing sheet '{sheet_name}': {e}")
                    results.append({
                        "sheet_name": sheet_name,
                        "table_name": table_name,
                        "status": "failed",
                        "error": str(e)
                    })
                    
        except Exception as e:
            logger.error(f"Failed to process XLSX file {file_path}: {e}")
            raise e
            
        return results

    def _process_sheet_with_analysis(self, df: pd.DataFrame, analysis: dict) -> pd.DataFrame:
        """Apply the structural fixes discovered by AI analysis."""
        header_row_idx = analysis.get("header_row", 0)
        data_start_idx = analysis.get("data_start_row", header_row_idx + 1)
        is_split = analysis.get("is_split", False)
        mapping = analysis.get("column_mapping", {})

        # 1. Extraction Phase
        if is_split:
            split_offset = analysis.get("split_column_offset")
            if split_offset:
                logger.info(f"Reconciling split table with offset {split_offset}...")
                data = self._reconcile_split_table(df, header_row_idx, data_start_idx, split_offset)
            else:
                logger.warning("Split detected but no split_column_offset provided. Falling back to standard extraction.")
                raw_headers = df.iloc[header_row_idx].tolist()
                headers = [str(h).strip() if pd.notna(h) else f"col_{i}" for i, h in enumerate(raw_headers)]
                data = df.iloc[data_start_idx:].copy()
                data.columns = headers
        else:
            # Standard Extraction
            raw_headers = df.iloc[header_row_idx].tolist()
            headers = [str(h).strip() if pd.notna(h) else f"col_{i}" for i, h in enumerate(raw_headers)]
            data = df.iloc[data_start_idx:].copy()
            data.columns = headers
        
        # 2. Cleaning Phase
        # Drop completely empty columns and rows
        data = data.dropna(axis=1, how='all')
        data = data.dropna(axis=0, how='all')
        
        # 3. Mapping Phase
        if mapping:
            # Only map if the original column actually exists in our extracted data
            # Also handle potential duplicates or variations in naming
            clean_mapping = {k: v for k, v in mapping.items() if k in data.columns}
            if clean_mapping:
                logger.info(f"Applying AI column mapping: {clean_mapping}")
                data = data.rename(columns=clean_mapping)
        
        # 4. Final Polish
        # Remove internal pandas 'Unnamed' artifacts or temporary col_N placeholders
        # BUT keep columns that were explicitly mapped (even if they were col_N)
        data = data.loc[:, ~data.columns.astype(str).str.contains('^Unnamed|^col_', regex=True) | data.columns.astype(str).isin(mapping.values())]
        
        return data

    def _reconcile_split_table(self, df: pd.DataFrame, header_row: int, data_start: int, split_offset: int) -> pd.DataFrame:
        """Merge side-by-side table blocks into a single vertical table."""
        # Block 1: Columns 0 to split_offset-1
        h1 = df.iloc[header_row, 0:split_offset].tolist()
        
        # Block 2: Find the next real header in the second block (skip potential empty spacers)
        h2_slice = df.iloc[header_row, split_offset:]
        first_valid_h2_idx = None
        for i, val in enumerate(h2_slice):
            if pd.notna(val) and str(val).strip():
                first_valid_h2_idx = split_offset + i
                break
        
        if first_valid_h2_idx is None:
            logger.warning("Could not find second block headers in split table. Returning block 1 only.")
            block1 = df.iloc[data_start:, 0:split_offset].copy()
            block1.columns = [str(h).strip() if pd.notna(h) else f"col_{i}" for i, h in enumerate(h1)]
            return block1

        h2 = df.iloc[header_row, first_valid_h2_idx:].tolist()
        
        # Extract data blocks
        block1 = df.iloc[data_start:, 0:split_offset].copy()
        block2 = df.iloc[data_start:, first_valid_h2_idx:].copy()
        
        # Clean headers
        block1.columns = [str(h).strip() if pd.notna(h) else f"col_{i}" for i, h in enumerate(h1)]
        block2.columns = [str(h).strip() if pd.notna(h) else f"col_{i}" for i, h in enumerate(h2)]
        
        # Vertical stack
        logger.info(f"Stacking blocks: B1({len(block1)} rows), B2({len(block2)} rows)")
        return pd.concat([block1, block2], ignore_index=True)
        
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
