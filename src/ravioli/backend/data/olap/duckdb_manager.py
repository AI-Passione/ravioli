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
                    logger.info(f"Sheet '{sheet_name}' full shape: {df_full.shape}")
                    
                    df_final = self._process_sheet_with_analysis(df_full, analysis)
                    
                    if df_final is None or df_final.empty:
                        logger.error(f"Sheet '{sheet_name}' processed result is empty. Analysis: {analysis}")
                        if df_final is not None:
                            logger.error(f"Columns remaining: {df_final.columns.tolist()}")
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
        try:
            header_row_idx = int(analysis.get("header_row", 0))
        except (ValueError, TypeError):
            header_row_idx = 0
            
        try:
            data_start_idx = int(analysis.get("data_start_row", header_row_idx + 1))
        except (ValueError, TypeError):
            data_start_idx = header_row_idx + 1
            
        is_split = analysis.get("is_split", False)
        split_offsets = analysis.get("split_offsets", [])
        mapping = analysis.get("column_mapping", {})

        # Heuristic Override: If AI missed a split but we see duplicate headers, force it.
        # This is common in LinkedIn 'Top Posts' where the same columns repeat for different metrics.
        if not is_split:
            raw_headers = df.iloc[header_row_idx].tolist()
            seen_headers = set()
            for i, h in enumerate(raw_headers):
                h_str = str(h).strip().lower()
                # Skip empty or generic headers
                if not h_str or "unnamed" in h_str or h_str.startswith("col_"):
                    continue
                if h_str in seen_headers:
                    logger.warning(f"Heuristic: Detected duplicate header '{h}' at col {i}. Forcing Split mode.")
                    is_split = True
                    # Estimate split offsets by finding repeating blocks of the first valid header
                    first_header = str(raw_headers[0]).strip().lower()
                    split_offsets = [j for j, val in enumerate(raw_headers) if str(val).strip().lower() == first_header and j > 0]
                    break
                seen_headers.add(h_str)

        # Safety Check: If AI suggested a data start that is beyond the end of the file,
        # fallback to something safer (like the header row itself or row 0)
        if data_start_idx >= df.shape[0]:
            logger.warning(f"AI suggested data_start_row {data_start_idx} is beyond sheet length {df.shape[0]}. Falling back to header_row_idx.")
            data_start_idx = header_row_idx
            
        # If still beyond (e.g. both were too high), fallback to 0
        if data_start_idx >= df.shape[0]:
            data_start_idx = 0

        # 1. Extraction Phase
        if is_split:
            # Use heuristic offsets if available, otherwise get from analysis
            if not split_offsets:
                split_offsets = analysis.get("split_offsets")
                if not split_offsets and "split_column_offset" in analysis:
                    split_offsets = [analysis["split_column_offset"]]
                
            if split_offsets:
                logger.info(f"Reconciling multi-block split table with offsets {split_offsets}...")
                data = self._reconcile_split_table(df, header_row_idx, data_start_idx, split_offsets)
            else:
                logger.warning("Split detected but no split_offsets provided. Falling back to standard extraction.")
                raw_headers = df.iloc[header_row_idx].tolist()
                headers = [str(h).strip() if pd.notna(h) and str(h).strip() != "" else f"col_{i}" for i, h in enumerate(raw_headers)]
                data = df.iloc[data_start_idx:].copy()
                data.columns = headers
        else:
            # Standard Extraction
            raw_headers = df.iloc[header_row_idx].tolist()
            headers = [str(h).strip() if pd.notna(h) and str(h).strip() != "" else f"col_{i}" for i, h in enumerate(raw_headers)]
            logger.info(f"Standard extraction: header_row={header_row_idx}, data_start={data_start_idx}, headers={headers}")
            data = df.iloc[data_start_idx:].copy()
            data.columns = headers
        
        logger.info(f"Data shape after extraction: {data.shape}")
        
        # 2. Cleaning Phase
        # Drop completely empty columns and rows
        data = data.dropna(axis=1, how='all')
        data = data.dropna(axis=0, how='all')
        logger.info(f"Data shape after dropna: {data.shape}")
        
        # 3. Mapping Phase
        if mapping:
            clean_mapping = {k: v for k, v in mapping.items() if k in data.columns}
            if clean_mapping:
                logger.info(f"Applying AI column mapping: {clean_mapping}")
                data = data.rename(columns=clean_mapping)
        
        # 4. Final Polish
        # Remove internal pandas 'Unnamed' artifacts.
        unnamed_mask = data.columns.astype(str).str.contains('^Unnamed', regex=True)
        to_drop = [col for i, col in enumerate(data.columns) if unnamed_mask[i] and col not in mapping.values()]
        
        if to_drop:
            logger.info(f"Dropping unnamed columns: {to_drop}")
            data = data.drop(columns=to_drop)
        
        logger.info(f"Final data shape: {data.shape}")
        
        # Ultimate Fallback: If after all that the data is empty but the original sheet had data,
        # just ingest the whole sheet as generic columns so we don't lose information.
        if data.empty and not df.dropna(how='all').empty:
            logger.warning("Processed data is empty but original sheet has content. Falling back to full sheet ingestion.")
            data = df.copy()
            data.columns = [f"col_{i}" for i in range(df.shape[1])]
            # Basic cleanup on fallback data
            data = data.dropna(axis=1, how='all')
            data = data.dropna(axis=0, how='all')

        return data

    def _reconcile_split_table(self, df: pd.DataFrame, header_row: int, data_start: int, split_offsets: list) -> pd.DataFrame:
        """Merge multiple side-by-side table blocks into a single vertical table."""
        if not split_offsets:
            return df
            
        # Ensure offsets are sorted and unique
        split_offsets = sorted(list(set(split_offsets)))
        
        blocks = []
        # Block 0: from 0 to first offset
        blocks.append(self._extract_block(df, header_row, data_start, 0, split_offsets[0]))
        
        # Intermediate blocks
        for i in range(len(split_offsets) - 1):
            blocks.append(self._extract_block(df, header_row, data_start, split_offsets[i], split_offsets[i+1]))
            
        # Last block
        blocks.append(self._extract_block(df, header_row, data_start, split_offsets[-1], df.shape[1]))
        
        # Filter out empty blocks
        valid_blocks = [b for b in blocks if b is not None and not b.empty]
        
        if not valid_blocks:
            logger.warning("No valid data blocks found during reconciliation.")
            return pd.DataFrame()
            
        logger.info(f"Successfully reconciled {len(valid_blocks)} data blocks.")
        return pd.concat(valid_blocks, ignore_index=True)

    def _extract_block(self, df: pd.DataFrame, header_row: int, data_start: int, start_col: int, end_col: int) -> pd.DataFrame:
        """Helper to extract and clean a single block from a split table."""
        if start_col >= df.shape[1]:
            return None
            
        raw_headers = df.iloc[header_row, start_col:end_col].tolist()
        
        # Check if this is a "spacer" block (all NaNs or empty strings)
        if all(pd.isna(h) or str(h).strip() == "" for h in raw_headers):
            # Check a few rows of data too
            sample_data = df.iloc[data_start:data_start+5, start_col:end_col]
            if sample_data.isna().all().all():
                return None

        headers = [str(h).strip() if pd.notna(h) else f"col_{i}" for i, h in enumerate(raw_headers)]
        block = df.iloc[data_start:, start_col:end_col].copy()
        block.columns = headers
        
        # Drop completely empty columns/rows from block
        block = block.dropna(axis=1, how='all')
        block = block.dropna(axis=0, how='all')
        
        return block
        
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
