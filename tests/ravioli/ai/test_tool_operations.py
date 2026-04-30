from unittest.mock import patch, MagicMock
from ravioli.ai.tools.operations import ingest_data_tool, run_transformations_tool

@patch('ravioli.ai.tools.operations.CSVIngestor')
def test_ingest_data_tool_success(mock_ingestor):
    mock_instance = MagicMock()
    mock_ingestor.return_value = mock_instance
    res = ingest_data_tool.invoke({"file_path": "test.csv"})
    assert "Successfully ingested test.csv" in res
    mock_instance.run.assert_called_once_with("test.csv")

@patch('ravioli.ai.tools.operations.CSVIngestor')
def test_ingest_data_tool_error(mock_ingestor):
    mock_instance = MagicMock()
    mock_instance.run.side_effect = Exception("Failed to read")
    mock_ingestor.return_value = mock_instance
    res = ingest_data_tool.invoke({"file_path": "test.csv"})
    assert "Error: Failed to read" in res

@patch('ravioli.ai.tools.operations.run_dbt_command')
def test_run_transformations_tool_success(mock_dbt):
    mock_dbt.return_value = "DBT Success"
    res = run_transformations_tool.invoke({"command": "run"})
    assert res == "DBT Success"
    mock_dbt.assert_called_once_with("run")

@patch('ravioli.ai.tools.operations.run_dbt_command')
def test_run_transformations_tool_error(mock_dbt):
    mock_dbt.side_effect = Exception("DBT Error")
    res = run_transformations_tool.invoke({"command": "run"})
    assert "Error: DBT Error" in res
