import uuid
import io
import pytest
import datetime
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_external_tools(mocker):
    mocker.patch("ravioli.backend.api.v1.endpoints.data.calculate_hash", return_value="fake_gpx_hash")
    mocker.patch("ravioli.backend.api.v1.endpoints.data.shutil.copyfileobj")
    mocker.patch("ravioli.backend.api.v1.endpoints.data.Path.open", mocker.mock_open(read_data="fake gpx content"))
    mocker.patch("ravioli.backend.api.v1.endpoints.data.Path.stat", return_value=MagicMock(st_size=1024))
    mocker.patch("ravioli.backend.api.v1.endpoints.data.pii_scanner.scan_dataframe", return_value=False)
    
    # Mock AI Agent and Skill
    mocker.patch("ravioli.backend.api.v1.endpoints.data.KowalskiAgent")
    mocker.patch("ravioli.backend.api.v1.endpoints.data.skill_comm.generate_description", new_callable=AsyncMock, return_value="Mocked GPX Description")
    
    mocker.patch("ravioli.backend.api.v1.endpoints.data.duckdb_manager")

@pytest.mark.anyio
async def test_upload_gpx_success(client, session, mocker, mock_external_tools):
    """Test uploading a standard GPX file through the API."""
    # Mocking check for existing file and current user
    mock_query_result = MagicMock()
    mock_query_result.scalars.return_value.first.return_value = None
    mock_query_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_query_result
    
    # Mocking DataIngestor ingestion
    mock_ingestor = mocker.patch("ravioli.backend.api.v1.endpoints.data.data_ingestor")
    mock_ingestor.ingest_gpx = MagicMock(return_value=[
        {"table_name": "route_test_1234", "row_count": 500, "status": "completed"}
    ])
    
    # Mocking session behavior to avoid DB issues
    def mock_session_add(obj):
        obj.id = uuid.uuid4()
        obj.created_at = datetime.datetime.now()
        obj.updated_at = datetime.datetime.now()
        obj.source_type = "gpx"
        obj.has_pii = False
        return obj

    session.add.side_effect = mock_session_add
    session.commit.side_effect = lambda: None
    session.refresh.side_effect = lambda x: x

    # Create a dummy GPX file
    gpx_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg><trkpt lat="59.3" lon="18.0"/></trkseg></trk>
</gpx>
"""
    file = ("route_2022-07-20_12.20pm.gpx", io.BytesIO(gpx_content), "application/gpx+xml")
    
    response = client.post(
        "/api/v1/data/upload",
        files={"file": file}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "route_2022-07-20_12.20pm.gpx"
    assert data["row_count"] == 500
    assert data["status"] == "completed"
    # Ensure ingest_gpx was called with the correct arguments (including table_name)
    mock_ingestor.ingest_gpx.assert_called_once()
    args, kwargs = mock_ingestor.ingest_gpx.call_args
    assert "table_name" in kwargs
    assert kwargs["table_name"].startswith("route_2022_07_20_12_20pm_")

def test_ingest_gpx_naming_logic(mocker):
    """Test the table and pipeline naming logic in DataIngestor.ingest_gpx."""
    from ravioli.backend.data.olap.ingestion.ingestor import DataIngestor
    
    mock_db = MagicMock()
    # Mock DuckDB connection execute
    mock_conn = mock_db.connection
    mock_conn.execute.return_value.fetchone.return_value = [10]
    
    ingestor = DataIngestor(mock_db)
    
    # Mock dlt pipeline
    mock_pipeline_run = MagicMock()
    mocker.patch("ravioli.backend.data.olap.ingestion.ingestor.create_ravioli_pipeline", return_value=mock_pipeline_run)
    mocker.patch("ravioli.backend.data.olap.ingestion.ingestor.ET.iterparse", return_value=[(None, MagicMock(tag="trkpt", attrib={'lat': '0', 'lon': '0'}))])
    
    # Test with a problematic filename (trailing underscore after truncation)
    original_filename = "route_2022-07-20_12.20pm.gpx"
    file_path = Path("fake.gpx")
    
    results = ingestor.ingest_gpx(file_path, original_filename, schema="s_test")
    
    # Check that trailing underscores were handled (though in current logic we don't truncate to 20 anymore)
    # The new logic uses [:40] and rstrip("_")
    tn = results[0]["table_name"]
    assert not tn.endswith("_")
    assert tn.startswith("route_route_2022_07_20_12_20pm_gpx")
    
    # Test that providing a table_name overrides generation
    custom_tn = "custom_table"
    results2 = ingestor.ingest_gpx(file_path, original_filename, table_name=custom_tn, schema="s_test")
    assert results2[0]["table_name"] == custom_tn

def test_ingest_xml_fallback_naming(mocker):
    """Test that the fallback naming in ingest_xml also strips trailing underscores."""
    from ravioli.backend.data.olap.ingestion.ingestor import DataIngestor
    
    mock_db = MagicMock()
    ingestor = DataIngestor(mock_db)
    
    mock_pipeline = MagicMock()
    mocker.patch("ravioli.backend.data.olap.ingestion.ingestor.create_ravioli_pipeline", return_value=mock_pipeline)
    mocker.patch("ravioli.backend.data.olap.ingestion.ingestor.XML_STRATEGIES", {}) # Empty to trigger fallback
    
    # Use a real generator function to avoid __qualname__ issues with mocks in dlt
    def fake_gen(*args, **kwargs):
        yield {"data": 1}
        
    mocker.patch("ravioli.backend.data.olap.ingestion.ingestor.xml_full_parse_generator", side_effect=fake_gen)
    mocker.patch("ravioli.backend.data.olap.ingestion.ingestor.os.path.getsize", return_value=100)
    
    # Filename that would end in underscore if truncated at 20 (or any point)
    original_filename = "aaaaaaaaaaaaaaaaaaa_bbbb.xml"
    
    results = ingestor.ingest_xml(Path("fake.xml"), original_filename)
    tn = results[0]["table_name"]
    assert not tn.endswith("_")
