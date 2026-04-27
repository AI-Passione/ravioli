import os
import json
import csv
from io import StringIO
from typing import List, Dict, Any
from psycopg2 import sql
from psycopg2.extras import execute_values
from tqdm import tqdm
from ravioli.backend.data.olap.ingestion.Legacy.base import BaseIngestor
from ravioli.backend.data.oltp.session import get_db_connection, ensure_schema
from ravioli.backend.core.config import settings

class SpotifyIngestor(BaseIngestor):
    def __init__(self):
        super().__init__(schema_name="s_spotify", table_name="multi_table")

    def flatten_json(self, data, parent_key='', sep='_'):
        """Flatten nested JSON structure"""
        items = []
        if isinstance(data, dict):
            for k, v in data.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, (dict, list)):
                    items.extend(self.flatten_json(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
        elif isinstance(data, list):
            for i, v in enumerate(data):
                new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
                if isinstance(v, (dict, list)):
                    items.extend(self.flatten_json(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
        return dict(items)

    def ingest_json(self, file_path: str, table_name: str, conn):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            if len(data) == 1 and isinstance(list(data.values())[0], list):
                records = list(data.values())[0]
            else:
                records = [data]
        else:
            return

        flattened_records = []
        all_keys = set()
        for record in records:
            if isinstance(record, dict):
                flattened = self.flatten_json(record)
                flattened_records.append(flattened)
                all_keys.update(flattened.keys())
            else:
                flattened_records.append({'value': str(record)})
                all_keys.add('value')

        if not all_keys:
            return

        columns = sorted([k.strip().lower().replace(' ', '_').replace('-', '_') for k in all_keys])
        key_mapping = {c: k for k in all_keys for c in [k.strip().lower().replace(' ', '_').replace('-', '_')]}

        with conn.cursor() as cur:
            cur.execute(sql.SQL("DROP TABLE IF EXISTS {}.{} CASCADE").format(sql.Identifier(self.schema_name), sql.Identifier(table_name)))
            cols_def = ", ".join([f"{sql.Identifier(c).as_string(conn)} TEXT" for c in columns])
            cur.execute(sql.SQL("CREATE TABLE {}.{} ({})").format(sql.Identifier(self.schema_name), sql.Identifier(table_name), sql.SQL(cols_def)))
            
            insert_query = sql.SQL("INSERT INTO {}.{} VALUES %s").format(sql.Identifier(self.schema_name), sql.Identifier(table_name))
            
            rows = []
            for record in flattened_records:
                row = [str(record.get(key_mapping[c])) if record.get(key_mapping[c]) is not None else None for c in columns]
                rows.append(row)
                if len(rows) >= 1000:
                    execute_values(cur, insert_query, rows)
                    rows = []
            if rows:
                execute_values(cur, insert_query, rows)
        conn.commit()

    def ingest_csv(self, file_path: str, table_name: str, conn):
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        content = None
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                    break
            except:
                continue
        if not content:
            return

        csv_reader = csv.reader(StringIO(content))
        headers = next(csv_reader, None)
        if not headers:
            return

        columns = [h.strip().lower().replace(' ', '_').replace('-', '_') for h in headers]
        
        with conn.cursor() as cur:
            cur.execute(sql.SQL("DROP TABLE IF EXISTS {}.{} CASCADE").format(sql.Identifier(self.schema_name), sql.Identifier(table_name)))
            cols_def = ", ".join([f"{sql.Identifier(c).as_string(conn)} TEXT" for c in columns])
            cur.execute(sql.SQL("CREATE TABLE {}.{} ({})").format(sql.Identifier(self.schema_name), sql.Identifier(table_name), sql.SQL(cols_def)))
            
            insert_query = sql.SQL("INSERT INTO {}.{} VALUES %s").format(sql.Identifier(self.schema_name), sql.Identifier(table_name))
            rows = []
            for row in csv_reader:
                if len(row) < len(columns):
                    row += [None] * (len(columns) - len(row))
                else:
                    row = row[:len(columns)]
                rows.append(row)
                if len(rows) >= 1000:
                    execute_values(cur, insert_query, rows)
                    rows = []
            if rows:
                execute_values(cur, insert_query, rows)
        conn.commit()

    def ingest(self, data_path: str = None):
        if data_path is None:
            data_path = settings.local_data_path / "spotify"
        
        files_to_process = []
        for root, _, files in os.walk(data_path):
            for f in files:
                path = os.path.join(root, f)
                if f.lower().endswith('.json'):
                    files_to_process.append((path, 'json', os.path.splitext(f)[0].lower().replace(' ', '_')))
                elif f.lower().endswith('.csv'):
                    files_to_process.append((path, 'csv', os.path.splitext(f)[0].lower().replace(' ', '_')))

        if not files_to_process:
            print(f"No Spotify files found in {data_path}")
            return

        conn = get_db_connection()
        ensure_schema(self.schema_name)
        
        for path, ftype, table_name in tqdm(files_to_process, desc="Spotify Ingestion"):
            if ftype == 'json':
                self.ingest_json(path, table_name, conn)
            else:
                self.ingest_csv(path, table_name, conn)
        conn.close()
