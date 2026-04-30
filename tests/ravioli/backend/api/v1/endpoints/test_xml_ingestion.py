import uuid
import io
import pytest
import datetime
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_external_tools(mocker):
    mocker.patch("ravioli.backend.api.v1.endpoints.data.calculate_hash", return_value="fake_hash")
    mocker.patch("ravioli.backend.api.v1.endpoints.data.shutil.copyfileobj")
    mocker.patch("ravioli.backend.api.v1.endpoints.data.Path.open", mocker.mock_open(read_data="fake file content"))
    mocker.patch("ravioli.backend.api.v1.endpoints.data.Path.stat", return_value=MagicMock(st_size=1024))
    mocker.patch("ravioli.backend.api.v1.endpoints.data.pii_scanner.scan_dataframe", return_value=False)
    
    # Mock AI Agent and Skill
    mocker.patch("ravioli.backend.api.v1.endpoints.data.KowalskiAgent")
    mocker.patch("ravioli.backend.api.v1.endpoints.data.skill_comm.generate_description", new_callable=AsyncMock, return_value="Mocked Description")
    
    mocker.patch("ravioli.backend.api.v1.endpoints.data.duckdb_manager")

@pytest.mark.anyio
async def test_upload_apple_health_xml(client, session, mocker, mock_external_tools):
    """Test uploading a standard Apple Health export.xml."""
    # Mocking check for existing file
    mock_query_result = MagicMock()
    mock_query_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_query_result
    
    # Mocking DataIngestor ingestion
    mock_ingestor = mocker.patch("ravioli.backend.api.v1.endpoints.data.data_ingestor")
    mock_ingestor.ingest_xml = MagicMock(return_value=[
        {"table_name": "apple_health_records", "row_count": 1000, "status": "completed"}
    ])
    
    # Mocking session behavior to avoid DB issues
    def mock_session_add(obj):
        obj.id = uuid.uuid4()
        obj.created_at = datetime.datetime.now()
        obj.updated_at = datetime.datetime.now()
        obj.source_type = "xml"
        obj.has_pii = False
        return obj

    session.add.side_effect = mock_session_add
    session.commit.side_effect = lambda: None
    session.refresh.side_effect = lambda x: x

    # Create a dummy XML file
    xml_content = b"<HealthData><Record type='StepCount' value='10'/></HealthData>"
    file = ("export.xml", io.BytesIO(xml_content), "text/xml")
    
    response = client.post(
        "/api/v1/data/upload",
        files={"file": file}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "export.xml"
    assert data["row_count"] == 1000
    assert data["status"] == "completed"

@pytest.mark.anyio
async def test_upload_apple_health_cda_xml(client, session, mocker, mock_external_tools):
    """Test uploading an Apple Health export_cda.xml."""
    mock_query_result = MagicMock()
    mock_query_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_query_result
    
    mock_ingestor = mocker.patch("ravioli.backend.api.v1.endpoints.data.data_ingestor")
    mock_ingestor.ingest_xml = MagicMock(return_value=[
        {"table_name": "apple_health_observations", "row_count": 5000, "status": "completed"}
    ])
    
    def mock_session_add(obj):
        obj.id = uuid.uuid4()
        obj.created_at = datetime.datetime.now()
        obj.updated_at = datetime.datetime.now()
        obj.source_type = "xml"
        obj.has_pii = False
        return obj

    session.add.side_effect = mock_session_add
    session.commit.side_effect = lambda: None
    session.refresh.side_effect = lambda x: x
    
    xml_content = b"<ClinicalDocument><observation>Value</observation></ClinicalDocument>"
    file = ("export_cda.xml", io.BytesIO(xml_content), "text/xml")
    
    response = client.post(
        "/api/v1/data/upload",
        files={"file": file}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "export_cda.xml"
    assert data["row_count"] == 5000
    assert data["status"] == "completed"

@pytest.mark.anyio
async def test_xml_chunk_generator_logic(mocker):
    """Test the low-level XML chunk generator logic in utils."""
    from ravioli.backend.data.olap.ingestion.utils import xml_chunk_generator
    from pathlib import Path
    
    xml_data = b"""
    <HealthData>
        <Record type="HKQuantityTypeIdentifierStepCount" value="100" unit="count" />
        <Record type="HKQuantityTypeIdentifierDistanceWalkingRunning" value="0.5" unit="km" />
    </HealthData>
    """
    mocker.patch("ravioli.backend.data.olap.ingestion.utils.open", mocker.mock_open(read_data=xml_data))
    
    gen = xml_chunk_generator(Path("fake.xml"), "Record", 0, len(xml_data))
    results = list(gen)
    
    assert len(results) == 2
    assert results[0]["type"] == "HKQuantityTypeIdentifierStepCount"
    assert results[1]["type"] == "HKQuantityTypeIdentifierDistanceWalkingRunning"

@pytest.mark.anyio
async def test_xml_chunk_generator_observation(mocker):
    """Test the CDA observation extraction logic."""
    from ravioli.backend.data.olap.ingestion.utils import xml_chunk_generator
    from pathlib import Path
    
    xml_data = b"""
    <ClinicalDocument>
        <observation classCode="OBS" moodCode="EVN">
            <code code="123" displayName="Test Observation"/>
            <value value="45.6" unit="mg"/>
            <effectiveTime><low value="20230101"/><high value="20230102"/></effectiveTime>
        </observation>
    </ClinicalDocument>
    """
    mocker.patch("ravioli.backend.data.olap.ingestion.utils.open", mocker.mock_open(read_data=xml_data))
    
    gen = xml_chunk_generator(Path("fake.xml"), "observation", 0, len(xml_data))
    results = list(gen)
    
    assert len(results) == 1
    assert results[0]["code_code"] == "123"
    assert results[0]["value_value"] == "45.6"
    assert results[0]["start_value"] == "20230101"
    assert results[0]["end_value"] == "20230102"
