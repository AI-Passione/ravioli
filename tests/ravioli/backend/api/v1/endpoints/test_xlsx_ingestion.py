import uuid
import io
import pytest
import pandas as pd
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.anyio
async def test_upload_xlsx(client, session, mocker):
    # Mocking the hash calculation
    mocker.patch("ravioli.backend.api.v1.endpoints.data.calculate_hash", return_value="fake_hash")
    
    # Mocking check for existing file
    mock_query_result = MagicMock()
    mock_query_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_query_result
    
    # Mocking file saving
    mocker.patch("ravioli.backend.api.v1.endpoints.data.shutil.copyfileobj")
    mocker.patch("ravioli.backend.api.v1.endpoints.data.Path.open", mocker.mock_open())
    mocker.patch("ravioli.backend.api.v1.endpoints.data.Path.stat", return_value=MagicMock(st_size=1024))
    
    # Mocking DataIngestor ingestion
    mock_ingestor = mocker.patch("ravioli.backend.api.v1.endpoints.data.data_ingestor")
    mock_ingestor.ingest_xlsx = AsyncMock(return_value=[{
        "sheet_name": "Sheet1",
        "table_name": "test_sheet1__xlsx",
        "status": "completed",
        "row_count": 100
    }])
    
    # Mocking duckdb_manager for sample data fetch
    mocker.patch("ravioli.backend.api.v1.endpoints.data.duckdb_manager")
    
    # Mocking PII scan
    mocker.patch("ravioli.backend.api.v1.endpoints.data.pii_scanner.scan_dataframe", return_value=False)
    
    # Mock AI Agent and Skill
    mocker.patch("ravioli.backend.api.v1.endpoints.data.KowalskiAgent")
    mocker.patch("ravioli.backend.api.v1.endpoints.data.skill_comm.generate_description", new_callable=AsyncMock, return_value="Mocked Description")
    
    # Mocking session behavior to avoid DB issues and populate required fields for validation
    import datetime
    def mock_session_add(obj):
        if hasattr(obj, 'id') and not obj.id:
            obj.id = uuid.uuid4()
        if hasattr(obj, 'created_at') and not obj.created_at:
            obj.created_at = datetime.datetime.now()
        if hasattr(obj, 'updated_at') and not obj.updated_at:
            obj.updated_at = datetime.datetime.now()
        if hasattr(obj, 'source_type') and not obj.source_type:
            obj.source_type = "xlsx"
        if hasattr(obj, 'has_pii') and obj.has_pii is None:
            obj.has_pii = False
        return obj

    session.add.side_effect = mock_session_add
    session.commit.side_effect = lambda: None
    session.refresh.side_effect = lambda x: x
    
    # Mocking refresh to do nothing so it doesn't clear our attributes
    session.refresh.side_effect = lambda x: x
    
    # Create a dummy XLSX file
    xlsx_content = b"fake xlsx content"
    file = ("test.xlsx", io.BytesIO(xlsx_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    response = client.post(
        "/api/v1/data/upload",
        files={"file": file}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "test.xlsx [Sheet1]"
    assert data["row_count"] == 100
    assert data["status"] == "completed"
    
    # Verify the correct ingestion method was called
    mock_ingestor.ingest_xlsx.assert_called_once()
    mock_ingestor.ingest_csv.assert_not_called()

@pytest.mark.anyio
async def test_quick_insight_xlsx(client, session, mocker):
    from ravioli.backend.core.models import Analysis
    # Create a dummy XLSX file
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
    xlsx_buffer = io.BytesIO()
    df.to_excel(xlsx_buffer, index=False)
    xlsx_buffer.seek(0)
    
    # Mock AI Agent and Local Skill Function
    mocker.patch("ravioli.backend.api.v1.endpoints.analyses.KowalskiAgent")
    mocker.patch("ravioli.backend.api.v1.endpoints.analyses.generate_summary", new_callable=AsyncMock, return_value=("Mock Summary", ["Question 1?"]))
    mocker.patch("ravioli.backend.api.v1.endpoints.analyses.extract_and_store_insights")
    
    # Mocking Analysis instantiation to provide an ID
    mock_analysis = Analysis(id=uuid.uuid4(), title="Quick Insight: test.xlsx", status="completed", result="Mock Summary")
    mocker.patch("ravioli.backend.api.v1.endpoints.analyses.models.Analysis", return_value=mock_analysis)
    
    file = ("test.xlsx", xlsx_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    response = client.post(
        "/api/v1/analyses/quick-insight",
        files={"file": file}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "Quick Insight: test.xlsx" in data["title"]
    assert data["stats"]["rows"] == 3
    assert data["summary"] == "Mock Summary"
