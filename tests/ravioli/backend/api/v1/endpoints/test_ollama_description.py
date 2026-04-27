import uuid
import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock
from ravioli.backend.core.models import DataSource

@pytest.mark.anyio
async def test_generate_file_description(client, session, mocker):
    file_id = uuid.uuid4()
    table_name = "test_table"
    filename = "test.csv"
    
    # Mock the DB file record
    db_file = DataSource(
        id=file_id,
        filename=f"{file_id}.csv",
        original_filename=filename,
        content_type="text/csv",
        size_bytes=100,
        table_name=table_name,
        schema_name="main",
        source_type="file",
        has_pii=False,
        status="completed",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    # Mock session.execute().scalar_one_or_none()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = db_file
    session.execute.return_value = mock_result
    
    # Mock DuckDB interaction by patching the class property
    mock_conn = MagicMock()
    mocker.patch("ravioli.backend.data.olap.duckdb_manager.DuckDBManager.connection", new_callable=lambda: mock_conn)
    
    mock_df = MagicMock()
    mock_conn.execute.return_value.fetchdf.return_value = mock_df
    mock_df.to_csv.return_value = "col1,col2\nval1,val2"
    
    # Mock OllamaClient
    mock_ollama_client = mocker.patch("ravioli.backend.api.v1.endpoints.data.OllamaClient")
    mock_instance = mock_ollama_client.return_value
    mock_instance.generate_description = AsyncMock(return_value="A generated description")
    
    response = client.post(f"/api/v1/data/files/{file_id}/generate-description")
    
    assert response.status_code == 200
    assert response.json()["description"] == "A generated description"
    
    # Verify mocks were called
    mock_instance.generate_description.assert_called_once_with(filename, "col1,col2\nval1,val2")
    assert session.commit.called
