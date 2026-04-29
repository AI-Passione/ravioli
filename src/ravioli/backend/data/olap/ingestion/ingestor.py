import os
import io
import logging
import httpx
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional

from ravioli.backend.data.olap.ingestion.utils import (
    create_ravioli_pipeline,
    process_sheet_with_analysis
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
    def __init__(self, duckdb_manager):
        self.duckdb_manager = duckdb_manager

    def ingest_csv(self, file_path: Path, table_name: str, schema: str = "main") -> int:
        """Standard CSV Ingestion."""
        conn = self.duckdb_manager.connection
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        full_table_name = f'"{schema}"."{table_name}"'
        conn.execute(f"CREATE OR REPLACE TABLE {full_table_name} AS SELECT * FROM read_csv_auto('{file_path}')")
        return conn.execute(f"SELECT COUNT(*) FROM {full_table_name}").fetchone()[0]

    async def ingest_xlsx(self, file_path: Path, base_table_name: str, schema: str = "main", ollama_client=None) -> list:
        """XLSX Ingestion with AI analysis."""
        conn = self.duckdb_manager.connection
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        results = []
        try:
            excel_file = pd.ExcelFile(file_path)
            for sheet_name in excel_file.sheet_names:
                clean_name = "".join(c if c.isalnum() else "_" for c in sheet_name).lower()
                table_name = f"{base_table_name}_{clean_name}__xlsx"
                full_table_name = f'"{schema}"."{table_name}"'
                
                df_raw_sample = pd.read_excel(file_path, sheet_name=sheet_name, nrows=20, header=None)
                grid_lines = [f"Row {i}: | " + " | ".join([str(v).strip().replace('\n',' ') for v in row]) + " |" for i, row in df_raw_sample.iterrows()]
                
                analysis = await ollama_client.analyze_sheet_structure(sheet_name, "\n".join(grid_lines)) if ollama_client else {"verdict": "ready"}
                if analysis.get("verdict") == "reject": continue
                
                df_final = process_sheet_with_analysis(pd.read_excel(file_path, sheet_name=sheet_name, header=None), analysis)
                conn.execute(f"CREATE OR REPLACE TABLE {full_table_name} AS SELECT * FROM df_final")
                results.append({
                    "sheet_name": sheet_name,
                    "table_name": table_name,
                    "status": "completed",
                    "row_count": conn.execute(f"SELECT COUNT(*) FROM {full_table_name}").fetchone()[0]
                })
        except Exception as e:
            logger.error(f"XLSX Ingestion failed: {e}")
            raise e
        return results

    def ingest_xml(self, file_path: Path, original_filename: str, schema: str = "s_manual") -> list:
        """Generic XML Ingestion (Handles Health Exports, CDA, etc.)."""
        fn = original_filename.lower()
        if 'export_cda' in fn:
            return self._process_clinical_xml(file_path, original_filename, schema)
        elif 'export' in fn:
            return self._process_health_export_xml(file_path, original_filename, schema)
        
        # Fallback for generic XML
        def generic_gen():
            root = ET.parse(file_path).getroot()
            yield {"filename": original_filename, "root_tag": root.tag, "attribs": dict(root.attrib)}
        
        p = create_ravioli_pipeline(f"xml_{original_filename}", schema)
        tn = f"xml_{''.join(c if c.isalnum() else '_' for c in original_filename).lower()[:20]}"
        p.run(generic_gen(), table_name=tn)
        return [{"table_name": tn, "row_count": 1, "status": "completed"}]

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

    # --- XML Processing Strategies ---
    def _process_health_export_xml(self, path: Path, fn: str, schema: str) -> list:
        """Specialized streaming for Health Export XML."""
        results = []
        def s_rec():
            for _, e in ET.iterparse(path, events=("end",)):
                if e.tag == "Record": yield dict(e.attrib); e.clear()
        def s_work():
            for _, e in ET.iterparse(path, events=("end",)):
                if e.tag == "Workout":
                    w = dict(e.attrib); m = {c.attrib['key']: c.attrib['value'] for c in e if c.tag == "MetadataEntry"}
                    if m: w['metadata'] = m
                    yield w; e.clear()
        def s_sum():
            for _, e in ET.iterparse(path, events=("end",)):
                if e.tag == "ActivitySummary": yield dict(e.attrib); e.clear()
        
        p = create_ravioli_pipeline(f"ah_{os.path.getsize(path)}", schema)
        for tn, gen in [("apple_health_records", s_rec), ("apple_health_workouts", s_work), ("apple_health_activity_summaries", s_sum)]:
            p.run(gen(), table_name=tn, write_disposition="append")
            count = self.duckdb_manager.connection.execute(f'SELECT COUNT(*) FROM "{schema}"."{tn}"').fetchone()[0]
            results.append({"table_name": tn, "row_count": count, "status": "completed"})
        return results

    def _process_clinical_xml(self, path: Path, fn: str, schema: str) -> list:
        """Specialized processing for Clinical Document Architecture."""
        def p_cda():
            root = ET.parse(path).getroot(); yield {"filename": fn, "root_tag": root.tag, "attribs": dict(root.attrib)}
        p = create_ravioli_pipeline(f"cda_{fn}", schema)
        p.run(p_cda(), table_name="apple_health_clinical_records")
        count = self.duckdb_manager.connection.execute(f'SELECT COUNT(*) FROM "{schema}"."apple_health_clinical_records"').fetchone()[0]
        return [{"table_name": "apple_health_clinical_records", "row_count": count, "status": "completed"}]
