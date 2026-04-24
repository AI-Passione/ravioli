import uuid
from datetime import datetime, UTC
from unittest.mock import MagicMock

def test_list_files(client, session):
    file_id = uuid.uuid4()
    class MockFile:
        def __init__(self, id, filename):
            self.id = id
            self.filename = filename
            self.original_filename = "test.csv"
            self.content_type = "text/csv"
            self.size_bytes = 100
            self.table_name = "test_table"
            self.row_count = 10
            self.status = "completed"
            self.error_message = None
            self.created_at = datetime.now(UTC)
            self.updated_at = datetime.now(UTC)
    
    mock_file = MockFile(file_id, "test_uuid.csv")
    
    # Mock the execute().scalars().all() chain
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    session.execute.return_value = mock_result
    mock_result.scalars.return_value = mock_scalars
    mock_scalars.all.return_value = [mock_file]

    response = client.get("/api/v1/data/files")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["original_filename"] == "test.csv"
    assert data[0]["row_count"] == 10

def test_get_table_preview(client, mocker):
    # Mock the duckdb_manager instance imported in data.py
    mock_duckdb = mocker.patch("ravioli.backend.api.v1.endpoints.data.duckdb_manager")
    mock_duckdb.list_tables.return_value = ["test_table"]
    mock_duckdb.query.return_value = [{"col1": "val1"}]

    response = client.get("/api/v1/data/preview/test_table")

    assert response.status_code == 200
    assert response.json() == [{"col1": "val1"}]
    mock_duckdb.query.assert_called_once()

def test_get_table_preview_invalid_name(client):
    response = client.get("/api/v1/data/preview/invalid;table")
    assert response.status_code == 400
    assert "Invalid table name" in response.json()["detail"]
