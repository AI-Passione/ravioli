import os
import io
import logging
import httpx
import dlt
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional

from ravioli.backend.data.olap.ingestion.utils import (
    create_ravioli_pipeline,
    process_sheet_with_analysis,
    xlsx_chunk_generator,
    xml_tag_generator,
    xml_chunk_generator,
    xml_full_parse_generator,
    parallel_xml_tag_generator,
    XML_STRATEGIES
)

logger = logging.getLogger(__name__)

# --- WFS Client ---
class WFSClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = 30.0

    async def get_capabilities(self) -> List[Dict[str, Any]]:
        params = {"service": "WFS", "version": "2.0.0", "request": "GetCapabilities"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
        root = ET.fromstring(response.text)
        ns = {'wfs': 'http://www.opengis.net/wfs/2.0', 'ows': 'http://www.opengis.net/ows/1.1'}
        layers = []
        ft_list = root.find('.//wfs:FeatureTypeList', ns)
        if ft_list is not None:
            for ft in ft_list.findall('wfs:FeatureType', ns):
                n_el = ft.find('wfs:Name', ns); t_el = ft.find('wfs:Title', ns)
                name = n_el.text if n_el is not None else "Unknown"
                title = t_el.text if t_el is not None else name
                layers.append({"name": name, "title": title})
        return layers

    async def get_features_generator(self, layer_name: str, chunk_size: int = 1000, output_format: Optional[str] = None):
        start_index = 0
        while True:
            params = {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": layer_name, "count": str(chunk_size), "startIndex": str(start_index)}
            params["outputFormat"] = output_format or "application/json"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                if response.status_code != 200 and not output_format:
                    params["outputFormat"] = "csv"
                    response = await client.get(self.base_url, params=params)
                response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            features_yielded = 0
            if "application/json" in content_type or "json" in response.text[:100].lower():
                data = response.json()
                for feat in data.get("features", []):
                    yield feat.get("properties", {})
                    features_yielded += 1
            elif "csv" in content_type or "," in response.text[:100]:
                df = pd.read_csv(io.StringIO(response.text))
                for _, row in df.iterrows():
                    yield row.to_dict(); features_yielded += 1
            else: raise ValueError(f"Unsupported format: {content_type}")
            if features_yielded < chunk_size: break
            start_index += chunk_size

    async def get_features(self, layer_name: str, chunk_size: int = 1000, output_format: Optional[str] = None) -> pd.DataFrame:
        rows = []
        async for row in self.get_features_generator(layer_name, chunk_size, output_format):
            rows.append(row)
        return pd.DataFrame(rows)

# --- Main Data Ingestor ---
class DataIngestor:
    CHUCKING_THRESHOLD = 1_000_000_000 # 1GB (Decimal)

    def __init__(self, duckdb_manager):
        self.duckdb_manager = duckdb_manager

    def _is_chucking(self, file_path: Path) -> bool:
        """Determines if a file is large enough to trigger chunked processing."""
        return os.path.getsize(file_path) >= self.CHUCKING_THRESHOLD

    def ingest_csv(self, file_path: Path, table_name: str, schema: str = "main") -> int:
        """Standard CSV Ingestion."""
        conn = self.duckdb_manager.connection
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        full_table_name = f'"{schema}"."{table_name}"'
        
        if self._is_chucking(file_path):
            logger.info(f"CHUCKING MODE ACTIVATED for CSV: {file_path}")
            # DuckDB handles this well natively, but we could add specific settings here
        
        conn.execute(f"CREATE OR REPLACE TABLE {full_table_name} AS SELECT * FROM read_csv_auto('{file_path}')")
        return conn.execute(f"SELECT COUNT(*) FROM {full_table_name}").fetchone()[0]

    async def ingest_xlsx(self, file_path: Path, base_table_name: str, schema: str = "main", ollama_client=None) -> list:
        """XLSX Ingestion with AI analysis."""
        conn = self.duckdb_manager.connection
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        results = []
        is_chucking = self._is_chucking(file_path)
        
        try:
            excel_file = pd.ExcelFile(file_path)
            for sheet_name in excel_file.sheet_names:
                clean_name = "".join(c if c.isalnum() else "_" for c in sheet_name).lower()
                table_name = f"{base_table_name}_{clean_name}__xlsx"
                full_table_name = f'"{schema}"."{table_name}"'
                
                # Analyze sheet structure regardless of size (using small sample)
                df_raw_sample = pd.read_excel(file_path, sheet_name=sheet_name, nrows=20, header=None)
                grid_lines = [f"Row {i}: | " + " | ".join([str(v).strip().replace('\n',' ') for v in row]) + " |" for i, row in df_raw_sample.iterrows()]
                analysis = await ollama_client.analyze_sheet_structure(sheet_name, "\n".join(grid_lines)) if ollama_client else {"verdict": "ready"}
                if analysis.get("verdict") == "reject": continue

                if is_chucking:
                    logger.info(f"CHUCKING MODE ACTIVATED for XLSX Sheet: {sheet_name} (Streaming enabled)")
                    gen = xlsx_chunk_generator(file_path, sheet_name, analysis)
                    xlsx_pipeline = create_ravioli_pipeline(f"xlsx_{clean_name}", schema)
                    xlsx_pipeline.run(gen, table_name=table_name)
                else:
                    df_final = process_sheet_with_analysis(pd.read_excel(file_path, sheet_name=sheet_name, header=None), analysis)
                    conn.execute(f"CREATE OR REPLACE TABLE {full_table_name} AS SELECT * FROM df_final")
                
                results.append({"sheet_name": sheet_name, "table_name": table_name, "status": "completed", "row_count": conn.execute(f"SELECT COUNT(*) FROM {full_table_name}").fetchone()[0]})
        except Exception as e:
            logger.error(f"XLSX Ingestion failed: {e}")
            raise e
        return results

    def ingest_xml(self, file_path: Path, original_filename: str, schema: str = "s_manual") -> list:
        """Config-driven XML Ingestion with chucking (chunked) mode."""
        fn = original_filename.lower()
        file_size = os.path.getsize(file_path)
        is_chucking = self._is_chucking(file_path)
        
        strategy = next((s for s in XML_STRATEGIES.values() if s["match"](fn)), None)
        results = []
        pipeline = create_ravioli_pipeline(f"xml_{file_size}", schema)
        
        if is_chucking:
            logger.info(f"CHUCKING MODE ACTIVATED for {original_filename} ({file_size / 1024**2:.1f} MB)")
        
        if strategy:
            # Collect resources to run them in one go for better worker distribution
            resources = []
            logger.info(f"Strategy found: {strategy['match'].__name__ if hasattr(strategy['match'], '__name__') else 'dynamic'}. Collecting resources...")
            
            num_workers = 4
            chunk_size = file_size // num_workers
            chunks = [(i * chunk_size, (i + 1) * chunk_size if i < num_workers - 1 else file_size) for i in range(num_workers)]

            for table_cfg in strategy["tables"]:
                tag = table_cfg.get("tag")
                tn = table_cfg["table_name"]
                extract_metadata = table_cfg.get("extract_metadata", False)
                
                logger.info(f"Preparing resource for table '{tn}' (Tag: {tag})")
                if tag:
                    if is_chucking:
                        logger.info(f"Parallelizing {tn} into {num_workers} streaming resources...")
                        for i, (start, end) in enumerate(chunks):
                            gen = xml_chunk_generator(file_path, tag, start, end, extract_metadata)
                            # Using a unique resource name but same table_name for dlt
                            resources.append(dlt.resource(gen, name=f"{tn}_p{i}", table_name=tn, write_disposition="append"))
                    else:
                        gen = xml_tag_generator(file_path, tag, extract_metadata)
                        resources.append(dlt.resource(gen, name=tn, write_disposition="append"))
                else:
                    gen = xml_full_parse_generator(file_path, original_filename)
                    resources.append(dlt.resource(gen, name=tn, write_disposition="replace"))
            
            # Run all resources together
            logger.info(f"Executing dlt pipeline with {len(resources)} parallel resources...")
            load_info = pipeline.run(resources)
            logger.info(f"Pipeline execution completed. Status: {load_info}")
            
            for table_cfg in strategy["tables"]:
                tn = table_cfg["table_name"]
                try:
                    count = self.duckdb_manager.connection.execute(f'SELECT COUNT(*) FROM "{schema}"."{tn}"').fetchone()[0]
                    results.append({"table_name": tn, "row_count": count, "status": "completed"})
                    logger.info(f"Ingestion successful for table '{tn}': {count:,} rows.")
                except Exception as e:
                    logger.warning(f"Table '{tn}' was not created or is empty: {e}")
                    results.append({"table_name": tn, "row_count": 0, "status": "no_data_found"})
        else:
            # Fallback for unrecognized XML
            tn = f"xml_{''.join(c if c.isalnum() else '_' for c in original_filename).lower()[:20]}"
            gen = xml_full_parse_generator(file_path, original_filename)
            pipeline.run(dlt.resource(gen, name=tn))
            results.append({"table_name": tn, "row_count": 1, "status": "completed"})
            
        return results

    def ingest_gpx(self, file_path: Path, original_filename: str, schema: str = "s_manual") -> list:
        """Ingest spatial data from GPX files."""
        def parse_gpx():
            for _, e in ET.iterparse(file_path, events=("end",)):
                if e.tag.split('}')[-1] == "trkpt":
                    p = {"latitude": float(e.attrib['lat']), "longitude": float(e.attrib['lon']), "time": None, "elevation": None}
                    for c in e:
                        ct = c.tag.split('}')[-1]
                        if ct == "time": p["time"] = c.text
                        elif ct == "ele": p["elevation"] = float(c.text) if c.text else None
                    yield p; e.clear()
        
        tn = f"route_{''.join(c if c.isalnum() else '_' for c in original_filename).lower()[:20]}"
        p = create_ravioli_pipeline(f"gpx_{original_filename}", schema)
        p.run(parse_gpx(), table_name=tn)
        count = self.duckdb_manager.connection.execute(f'SELECT COUNT(*) FROM "{schema}"."{tn}"').fetchone()[0]
        return [{"table_name": tn, "row_count": count, "status": "completed"}]
