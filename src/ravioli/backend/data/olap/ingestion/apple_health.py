import os
import xml.etree.ElementTree as ET
from datetime import datetime
from tqdm import tqdm
from psycopg2 import sql
from psycopg2.extras import execute_values
from ravioli.backend.db.olap.ingestion.base import BaseIngestor
from ravioli.backend.db.oltp.session import get_db_connection
from ravioli.backend.core.config import settings

class AppleHealthIngestor(BaseIngestor):
    def __init__(self):
        super().__init__(schema_name="s_apple_health", table_name="records")

    def get_record_count(self, xml_file):
        """Quickly counts the number of Record tags in the XML."""
        print("Pre-scanning file to estimate records...")
        count = 0
        context = ET.iterparse(xml_file, events=("end",))
        for event, elem in context:
            if elem.tag == "Record":
                count += 1
            elem.clear()
        return count

    def ingest(self, xml_file: str = None):
        if xml_file is None:
            xml_file = settings.local_data_path / "apple_health" / "export.xml"
        
        if not os.path.exists(xml_file):
            alt_path = str(xml_file).replace("export.xml", "Export.xml")
            if os.path.exists(alt_path):
                xml_file = alt_path
            else:
                raise FileNotFoundError(f"Apple Health export file not found: {xml_file}")

        total_records = self.get_record_count(xml_file)
        
        conn = get_db_connection()
        
        # DDL for records table
        create_table_query = sql.SQL("""
            DROP TABLE IF EXISTS {schema}.{table};
            CREATE TABLE {schema}.{table} (
                type VARCHAR(255),
                source_name VARCHAR(255),
                source_version VARCHAR(255),
                unit VARCHAR(50),
                creation_date TIMESTAMP,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                value TEXT,
                device TEXT,
                metadata JSONB
            );
        """).format(
            schema=sql.Identifier(self.schema_name),
            table=sql.Identifier(self.table_name)
        )

        with conn.cursor() as cur:
            cur.execute(create_table_query)
        conn.commit()

        # Streaming Parse
        context = ET.iterparse(xml_file, events=("start", "end"))
        context = iter(context)
        event, root = next(context)

        batch_size = 5000
        batch = []
        record_count = 0
        
        print("Starting ingestion...")
        with conn.cursor() as cur:
            for event, elem in tqdm(context, total=total_records):
                if event == "end" and elem.tag == "Record":
                    attrib = elem.attrib
                    
                    def parse_date(d_str):
                        try:
                            return datetime.strptime(d_str, '%Y-%m-%d %H:%M:%S %z')
                        except:
                            return None

                    row = (
                        attrib.get('type'),
                        attrib.get('sourceName'),
                        attrib.get('sourceVersion'),
                        attrib.get('unit'),
                        parse_date(attrib.get('creationDate')),
                        parse_date(attrib.get('startDate')),
                        parse_date(attrib.get('endDate')),
                        attrib.get('value'),
                        attrib.get('device'),
                        "{}" 
                    )
                    
                    batch.append(row)
                    record_count += 1
                    elem.clear()
                    
                    if len(batch) >= batch_size:
                        execute_values(cur, 
                            sql.SQL("INSERT INTO {schema}.{table} VALUES %s").format(
                                schema=sql.Identifier(self.schema_name),
                                table=sql.Identifier(self.table_name)
                            ),
                            batch
                        )
                        conn.commit()
                        batch = []

            if batch:
                execute_values(cur, 
                    sql.SQL("INSERT INTO {schema}.{table} VALUES %s").format(
                        schema=sql.Identifier(self.schema_name),
                        table=sql.Identifier(self.table_name)
                    ),
                    batch
                )
                conn.commit()

        print(f"Ingestion complete. {record_count} records inserted.")
        conn.close()
