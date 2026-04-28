import uuid
import io
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, AsyncMock
from ravioli.backend.core.models import DataSource

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
    
    # Mocking DuckDB ingestion
    mock_duckdb = mocker.patch("ravioli.backend.api.v1.endpoints.data.duckdb_manager")
    mock_duckdb.ingest_xlsx = AsyncMock(return_value=[{
        "sheet_name": "Sheet1",
        "table_name": "test_sheet1__xlsx",
        "status": "completed",
        "row_count": 100
    }])
    
    # Mocking PII scan
    mocker.patch("ravioli.backend.api.v1.endpoints.data.pii_scanner.scan_dataframe", return_value=False)
    
    # Mocking OllamaClient to avoid DB config issues
    mock_ollama_cls = mocker.patch("ravioli.backend.api.v1.endpoints.data.OllamaClient")
    mock_ollama = mock_ollama_cls.return_value
    
    # Mocking model instantiation to provide an ID
    from ravioli.backend.core.models import DataSource
    import datetime
    mock_datasource = DataSource(
        id=uuid.uuid4(), 
        original_filename="test.xlsx", 
        status="completed", 
        row_count=100,
        filename="internal.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=1024,
        table_name="test_sheet1__xlsx",
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now()
    )
    mocker.patch("ravioli.backend.api.v1.endpoints.data.DataSource", return_value=mock_datasource)
    
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
    assert data["original_filename"] == "test.xlsx"
    assert data["row_count"] == 100
    assert data["status"] == "completed"
    
    # Verify the correct ingestion method was called
    mock_duckdb.ingest_xlsx.assert_called_once()
    mock_duckdb.ingest_csv.assert_not_called()

@pytest.mark.anyio
async def test_quick_insight_xlsx(client, session, mocker):
    from ravioli.backend.core.models import Analysis
    # Create a dummy XLSX file
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
    xlsx_buffer = io.BytesIO()
    df.to_excel(xlsx_buffer, index=False)
    xlsx_buffer.seek(0)
    
    # Mocking Ollama/Summary generation
    mocker.patch("ravioli.backend.api.v1.endpoints.analyses.generate_summary", return_value=("Mock Summary", ["Question 1?"]))
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
