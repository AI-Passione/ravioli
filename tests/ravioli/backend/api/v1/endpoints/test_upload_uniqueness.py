import uuid
import io
import pytest
from unittest.mock import MagicMock

@pytest.mark.anyio
async def test_upload_generates_unique_table_name(client, session, mocker):
    # Mocking the hash calculation
    mocker.patch("ravioli.backend.api.v1.endpoints.data.calculate_hash", return_value="unique_hash")
    
    # Mocking check for existing file (no duplicates)
    mock_query_result = MagicMock()
    mock_query_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_query_result
    
    # Mocking file saving
    mocker.patch("ravioli.backend.api.v1.endpoints.data.shutil.copyfileobj")
    mocker.patch("ravioli.backend.api.v1.endpoints.data.Path.open", mocker.mock_open())
    mocker.patch("ravioli.backend.api.v1.endpoints.data.Path.stat", return_value=MagicMock(st_size=1024))
    
    # Mocking DuckDB ingestion
    mock_duckdb = mocker.patch("ravioli.backend.api.v1.endpoints.data.duckdb_manager")
    mock_duckdb.ingest_csv.return_value = 10
    
    # Mocking PII scan
    mocker.patch("ravioli.backend.api.v1.endpoints.data.pii_scanner.scan_dataframe", return_value=False)
    
    # Mocking session behavior
    import datetime
    def mock_session_add(obj):
        if not obj.id:
            obj.id = uuid.uuid4()
        if not obj.source_type:
            obj.source_type = "file"
        if not obj.created_at:
            obj.created_at = datetime.datetime.now()
        if not obj.updated_at:
            obj.updated_at = datetime.datetime.now()
        return obj
    session.add.side_effect = mock_session_add
    session.commit.side_effect = lambda: None
    session.refresh.side_effect = lambda x: x
    
    # Create a dummy CSV file
    csv_content = b"col1,col2\nval1,val2"
    file = ("test.csv", io.BytesIO(csv_content), "text/csv")
    
    response = client.post(
        "/api/v1/data/upload",
        files={"file": file}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Table name should be "test_<short_id>"
    assert data["table_name"].startswith("test_")
    assert len(data["table_name"]) == 5 + 4 # "test_" + 4 chars
    
    # Verify the table_name was used in ingestion
    mock_duckdb.ingest_csv.assert_called_once()
    args, kwargs = mock_duckdb.ingest_csv.call_args
    assert args[1] == data["table_name"]
