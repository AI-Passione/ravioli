from ravioli.backend.data.olap.ingestion.Legacy.base import CSVIngestor
from ravioli.backend.core.config import settings

class SubstackIngestor(CSVIngestor):
    def __init__(self):
        super().__init__(schema_name="s_substack", table_name="multi_table")

    def ingest(self, data_path: str = None):
        if data_path is None:
            data_path = settings.local_data_path / "substack"
        
        if not data_path.exists():
            print(f"No Substack data found in {data_path}")
            return

        for f in data_path.glob("*.csv"):
            table_name = f.stem.lower().replace(' ', '_')
            print(f"Ingesting {f.name} into {self.schema_name}.{table_name}...")
            # Update table name for this specific file
            self.table_name = table_name
            super().ingest(str(f))
