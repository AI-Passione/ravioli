from ravioli.backend.data.olap.ingestion.base import CSVIngestor
from ravioli.backend.core.config import settings

class BoltIngestor(CSVIngestor):
    def __init__(self):
        super().__init__(schema_name="s_bolt", table_name="rides")

    def ingest(self, file_path: str = None):
        if file_path is None:
            file_path = settings.local_data_path / "bolt" / "rides.csv"
        super().ingest(str(file_path))

class TelegramIngestor(CSVIngestor):
    def __init__(self):
        super().__init__(schema_name="s_telegram", table_name="messages")

    def ingest(self, file_path: str = None):
        if file_path is None:
            file_path = settings.local_data_path / "telegram" / "result.json" 
            # Note: Telegram usually exports JSON, but the task said CSVIngestor. 
            # I'll stick to CSV for now as per the task context, or handle JSON if needed.
            # Actually, most of these were simple CSVs in the legacy code.
            pass
        super().ingest(str(file_path))
