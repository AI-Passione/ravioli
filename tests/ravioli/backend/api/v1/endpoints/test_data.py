import uuid
import pytest
from datetime import datetime, UTC
from unittest.mock import MagicMock, AsyncMock
from ravioli.backend.core.models import UploadedFile

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

def test_get_table_preview_schema_qualified(client, mocker):
    mock_duckdb = mocker.patch("ravioli.backend.api.v1.endpoints.data.duckdb_manager")
    mock_duckdb.query.return_value = [{"col1": "val1"}]

    response = client.get("/api/v1/data/preview/s_manual.test_table")

    assert response.status_code == 200
    assert response.json() == [{"col1": "val1"}]
    # Should be quoted correctly in the query
    mock_duckdb.query.assert_called_once_with('SELECT * FROM "s_manual"."test_table" LIMIT 10')

def test_delete_file(client, session, mocker):
    file_id = uuid.uuid4()
    mock_file = MagicMock(spec=UploadedFile)
    mock_file.id = file_id
    mock_file.filename = "test_uuid.csv"
    mock_file.table_name = "test_table"
    mock_file.schema_name = "s_manual"
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_file
    session.execute.return_value = mock_result
    
    # Mock DuckDB and Filesystem
    mock_duckdb = mocker.patch("ravioli.backend.api.v1.endpoints.data.duckdb_manager")
    mock_path = mocker.patch("ravioli.backend.api.v1.endpoints.data.Path.exists")
    mock_path.return_value = True
    mock_unlink = mocker.patch("ravioli.backend.api.v1.endpoints.data.Path.unlink")

    response = client.delete(f"/api/v1/data/files/{file_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert session.delete.called
    assert session.commit.called
    mock_unlink.assert_called_once()
    mock_duckdb.connection.execute.assert_called_once_with('DROP TABLE IF EXISTS "s_manual"."test_table"')

def test_update_file_pii(client, session):
    file_id = uuid.uuid4()
    mock_file = MagicMock(spec=UploadedFile)
    mock_file.id = file_id
    mock_file.has_pii = False
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_file
    session.execute.return_value = mock_result

    response = client.patch(f"/api/v1/data/files/{file_id}/pii", json={"has_pii": True})

    assert response.status_code == 200
    assert mock_file.has_pii is True
    assert session.commit.called

@pytest.mark.anyio
async def test_ingest_wfs_layer(client, session, mocker):
    # Mock WFSClient
    mock_client_cls = mocker.patch("ravioli.backend.api.v1.endpoints.data.WFSClient")
    mock_client = mock_client_cls.return_value
    mock_client.get_features_generator = MagicMock()
    
    # Mock dlt pipeline
    mock_pipeline_run = mocker.patch("ravioli.backend.data.olap.ingestion.dlt_utils.dlt.pipeline")
    mock_instance = mock_pipeline_run.return_value
    mock_instance.run.return_value = MagicMock()
    
    # Mock DuckDB for count and schema check
    mock_duckdb = mocker.patch("ravioli.backend.api.v1.endpoints.data.duckdb_manager")
    mock_duckdb.connection.execute.return_value.fetchone.return_value = [10]

    payload = {
        "url": "https://test-wfs.com",
        "layer": "test_layer",
        "count": 10
    }

    response = client.post("/api/v1/data/wfs/ingest", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["row_count"] == 10
    assert data["schema_name"] == "s_test-wfs.com" # Simplistic derivation in code
    assert session.commit.called

@pytest.mark.anyio
async def test_list_wfs_layers(client, mocker):
    mock_client_cls = mocker.patch("ravioli.backend.api.v1.endpoints.data.WFSClient")
    mock_client = mock_client_cls.return_value
    mock_client.get_capabilities = AsyncMock(return_value=[{"name": "layer1", "title": "Layer 1"}])

    response = client.get("/api/v1/data/wfs/layers?url=https://test.com")

    assert response.status_code == 200
    assert response.json() == [{"name": "layer1", "title": "Layer 1"}]

def test_update_file_description(client, session):
    file_id = uuid.uuid4()
    mock_file = MagicMock(spec=UploadedFile)
    mock_file.id = file_id
    mock_file.description = None
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_file
    session.execute.return_value = mock_result

    response = client.patch(f"/api/v1/data/files/{file_id}", json={"description": "New description"})

    assert response.status_code == 200
    assert mock_file.description == "New description"
    assert session.commit.called
