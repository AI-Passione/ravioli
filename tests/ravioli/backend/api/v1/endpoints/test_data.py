import uuid
import pytest
from datetime import datetime, UTC
from unittest.mock import MagicMock, AsyncMock
from ravioli.backend.core.models import UploadedFile

def test_list_files(client, session):
    file_id = uuid.uuid4()
    mock_file = UploadedFile(
        id=file_id,
        filename="test_uuid.csv",
        original_filename="test.csv",
        content_type="text/csv",
        size_bytes=100,
        table_name="test_table",
        schema_name="s_manual",
        row_count=10,
        status="completed",
        source_type="file",
        has_pii=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    mock_result = MagicMock()
    session.execute.return_value = mock_result
    mock_result.scalars.return_value.all.return_value = [mock_file]

    response = client.get("/api/v1/data/files")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["original_filename"] == "test.csv"

def test_get_table_preview_schema_qualified(client, mocker):
    mock_duckdb = mocker.patch("ravioli.backend.api.v1.endpoints.data.duckdb_manager")
    mock_duckdb.list_tables.return_value = ["s_manual.test_table"]
    mock_duckdb.query.return_value = [{"col1": "val1"}]

    response = client.get("/api/v1/data/preview/s_manual.test_table")

    assert response.status_code == 200
    assert response.json() == [{"col1": "val1"}]
    mock_duckdb.query.assert_called_once_with('SELECT * FROM "s_manual"."test_table" LIMIT 10')

def test_delete_file(client, session, mocker):
    file_id = uuid.uuid4()
    mock_file = UploadedFile(
        id=file_id,
        filename="test_uuid.csv",
        original_filename="test.csv",
        content_type="text/csv",
        size_bytes=100,
        table_name="test_table",
        schema_name="s_manual",
        status="completed",
        source_type="file",
        has_pii=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_file
    session.execute.return_value = mock_result
    
    mock_duckdb = mocker.patch("ravioli.backend.api.v1.endpoints.data.duckdb_manager")
    mocker.patch("ravioli.backend.api.v1.endpoints.data.Path.exists", return_value=True)
    mock_unlink = mocker.patch("ravioli.backend.api.v1.endpoints.data.Path.unlink")

    response = client.delete(f"/api/v1/data/files/{file_id}")

    assert response.status_code == 200
    assert session.delete.called
    mock_unlink.assert_called_once()
    mock_duckdb.connection.execute.assert_called_once_with('DROP TABLE IF EXISTS "s_manual"."test_table"')

def test_update_file_pii(client, session):
    file_id = uuid.uuid4()
    mock_file = UploadedFile(
        id=file_id,
        filename="test.csv",
        original_filename="test.csv",
        content_type="text/csv",
        size_bytes=100,
        table_name="test",
        schema_name="main",
        status="completed",
        source_type="file",
        has_pii=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_file
    session.execute.return_value = mock_result

    response = client.patch(f"/api/v1/data/files/{file_id}/pii", json={"has_pii": True})

    assert response.status_code == 200
    assert mock_file.has_pii is True
    assert session.commit.called

def test_update_file_description(client, session):
    file_id = uuid.uuid4()
    mock_file = UploadedFile(
        id=file_id,
        filename="test.csv",
        original_filename="test.csv",
        content_type="text/csv",
        size_bytes=100,
        table_name="test",
        schema_name="main",
        status="completed",
        source_type="file",
        has_pii=False,
        description=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_file
    session.execute.return_value = mock_result

    response = client.patch(f"/api/v1/data/files/{file_id}", json={"description": "New description"})

    assert response.status_code == 200
    assert mock_file.description == "New description"

@pytest.mark.anyio
async def test_list_wfs_layers(client, mocker):
    mock_client_cls = mocker.patch("ravioli.backend.api.v1.endpoints.data.WFSClient")
    mock_client = mock_client_cls.return_value
    mock_client.get_capabilities = AsyncMock(return_value=[{"name": "layer1", "title": "Layer 1", "formats": []}])

    response = client.get("/api/v1/data/wfs/layers?url=https://test.com")

    assert response.status_code == 200
    assert response.json() == [{"name": "layer1", "title": "Layer 1", "formats": []}]

@pytest.mark.anyio
async def test_ingest_wfs_layer(client, session, mocker):
    # Prevent the background task from running — this test only verifies
    # that the endpoint creates and returns the pending record immediately.
    mocker.patch("ravioli.backend.api.v1.endpoints.data._run_wfs_ingestion")

    # Mock UploadedFile to ensure Pydantic validation passes since we don't have a real DB filling in the defaults
    mock_file = UploadedFile(
        id=uuid.uuid4(),
        filename="wfs_test",
        original_filename="test:layer",
        content_type="application/wfs",
        size_bytes=0,
        table_name="layer",
        schema_name="s_geoserver",
        status="pending",
        source_type="wfs",
        has_pii=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    mocker.patch("ravioli.backend.api.v1.endpoints.data.UploadedFile", return_value=mock_file)

    payload = {
        "url": "https://test-wfs.com/geoserver",
        "layer": "test:layer"
    }

    response = client.post("/api/v1/data/wfs/ingest", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["schema_name"] == "s_geoserver"
    assert data["source_type"] == "wfs"
