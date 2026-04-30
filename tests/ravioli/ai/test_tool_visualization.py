import pytest
from unittest.mock import patch, MagicMock
from ravioli.ai.tools.visualization import create_viz_payload

@pytest.mark.anyio
@patch('ravioli.ai.tools.visualization.duckdb_manager')
async def test_create_viz_payload_success(mock_duckdb):
    import pandas as pd
    mock_df = pd.DataFrame({"date": ["2021-01-01"], "impressions": [100]})
    mock_duckdb.connection.execute.return_value.fetchdf.return_value = mock_df

    async def mock_gen(*args, **kwargs):
        return {
            "chart_type": "bar",
            "labels_column": "date",
            "values_columns": ["impressions"],
            "title": "Test Chart"
        }

    res = await create_viz_payload("SELECT * FROM test", "Show me chart", mock_gen, "model")
    assert res["type"] == "chart"
    assert res["chart_type"] == "bar"

@pytest.mark.anyio
@patch('ravioli.ai.tools.visualization.duckdb_manager')
async def test_create_viz_payload_empty_data(mock_duckdb):
    mock_df = MagicMock()
    mock_df.empty = True
    mock_duckdb.connection.execute.return_value.fetchdf.return_value = mock_df

    async def mock_gen(*args, **kwargs):
        return {}

    res = await create_viz_payload("SELECT * FROM test", "Show me chart", mock_gen, "model")
    assert res["type"] == "error"
    assert "Query returned no data" in res["message"]

@pytest.mark.anyio
@patch('ravioli.ai.tools.visualization.duckdb_manager')
async def test_create_viz_payload_error(mock_duckdb):
    mock_duckdb.connection.execute.side_effect = Exception("DB Error")

    async def mock_gen(*args, **kwargs):
        return {}

    res = await create_viz_payload("SELECT * FROM test", "Show me chart", mock_gen, "model")
    assert res["type"] == "error"
    assert "DB Error" in res["message"]
