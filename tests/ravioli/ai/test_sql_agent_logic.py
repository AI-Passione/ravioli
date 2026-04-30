import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Directly mock the DuckDBManager instance's internal state
# to avoid ANY file access or property calls that trigger duckdb.connect()
from ravioli.backend.data.olap.duckdb_manager import duckdb_manager
mock_connection = MagicMock()
duckdb_manager._connection = mock_connection

from ravioli.ai.agents.sql_agent import KowalskiSQLAgent

@pytest.fixture
def agent():
    return KowalskiSQLAgent()

@pytest.mark.anyio
async def test_get_schema_success(agent):
    """Verify that _get_schema correctly queries duckdb_tables."""
    # Configure mock connection
    mock_connection.execute.return_value.fetchone.return_value = ["CREATE TABLE test (id INT)"]
    
    schema = agent._get_schema("test_table", "test_schema")
    assert "CREATE TABLE test" in schema
    
    # Verify query used placeholders for safety
    args = mock_connection.execute.call_args[0]
    assert "SELECT sql FROM duckdb_tables" in args[0]
    assert "?" in args[0]

@pytest.mark.anyio
async def test_get_schema_fallback(agent):
    """Verify that _get_schema falls back to DESCRIBE if SQL is missing."""
    # First call (duckdb_tables) returns None
    mock_connection.execute.return_value.fetchone.return_value = None
    # Second call (DESCRIBE) returns column info
    mock_connection.execute.return_value.fetchall.return_value = [("id", "INT", "YES", None, None, None)]
    
    schema = agent._get_schema("test_table")
    assert "Table test_table columns: id" in schema

@pytest.mark.anyio
async def test_generate_sql_parsing(agent):
    """Verify that generate_sql correctly extracts SQL from markdown."""
    with patch.object(agent, "_get_schema", return_value="CREATE TABLE test (val INT)"):
        # Mock Ollama returning markdown SQL
        mock_response = "Here is the query: ```sql SELECT * FROM test ```"
        with patch.object(agent, "_generate", return_value=mock_response):
            sql = await agent.generate_sql("show me data", "test")
            assert sql == "SELECT * FROM test"

@pytest.mark.anyio
async def test_create_viz_payload_logic(agent):
    """Verify that create_viz_payload builds a valid Chart.js object."""
    # Mock DuckDB result
    df = pd.DataFrame({
        "category": ["A", "B"],
        "count": [10, 20]
    })
    mock_connection.execute.return_value.fetchdf.return_value = df
    
    # Mock LLM decision
    viz_config = {
        "chart_type": "bar",
        "labels_column": "category",
        "values_columns": ["count"],
        "title": "Test Chart"
    }
    
    with patch.object(agent, "_generate", return_value=viz_config):
        payload = await agent.create_viz_payload("SELECT * FROM test", "test question")
        
        assert payload["type"] == "chart"
        assert payload["chart_type"] == "bar"
        assert payload["data"]["labels"] == ["A", "B"]
        assert payload["data"]["datasets"][0]["data"] == [10, 20]

@pytest.mark.anyio
async def test_process_question_generator(agent):
    """Verify that process_question yields status updates before the result."""
    with patch.object(agent, "_generate", return_value={"requires_viz": True}):
        with patch.object(agent, "generate_sql", return_value="SELECT 1"):
            with patch.object(agent, "create_viz_payload", return_value={"type": "chart"}):
                updates = []
                async for update in agent.process_question("test", "table"):
                    updates.append(update)
                
                # Should yield at least 3 strings (progress) and 1 dict (result)
                assert len(updates) >= 4
                assert isinstance(updates[0], str)
                assert "Kowalski is engaging" in updates[0]
                assert isinstance(updates[-1], dict)
                assert updates[-1]["answer_type"] == "viz"

@pytest.mark.anyio
async def test_generate_sql_strips_preamble(agent):
    """Verify that generate_sql strips preamble text like 'duckdb -- ...'."""
    with patch.object(agent, "_get_schema", return_value="CREATE TABLE test (val INT)"):
        # Mock Ollama returning preamble + SQL
        mock_response = "duckdb -- helpful comment\nSELECT * FROM test;"
        with patch.object(agent, "_generate", return_value=mock_response):
            sql = await agent.generate_sql("show me data", "test")
            assert sql == "SELECT * FROM test"
