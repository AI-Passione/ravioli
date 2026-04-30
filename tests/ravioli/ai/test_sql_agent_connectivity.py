import pytest
import httpx
from unittest.mock import patch, MagicMock
from ravioli.ai.agents.sql_agent import KowalskiSQLAgent

@pytest.mark.anyio
async def test_sql_agent_connect_error():
    """Verify that SQL agent handles httpx.ConnectError and raises a descriptive Exception."""
    agent = KowalskiSQLAgent()
    
    # Mock httpx to raise ConnectError
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Name or service not known")):
        # The agent catches ConnectError and raises a custom Exception
        with pytest.raises(Exception) as excinfo:
            await agent._generate("test", "test-model")
        assert "Kowalski: Statistical Brain unreachable" in str(excinfo.value)

@pytest.mark.anyio
async def test_sql_agent_host_resolution():
    """Verify that SQL agent correctly resolves host.docker.internal in Docker."""
    agent = KowalskiSQLAgent()
    # Mock the config which the property uses
    agent._config = {"base_url": "http://localhost:11434"}
    
    with patch("os.path.exists", return_value=True): # Simulate Docker
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200, json=lambda: {"response": "ok"})
            await agent._generate("test", "test-model")
            
            # Check if url was replaced
            call_url = mock_post.call_args[0][0]
            assert "host.docker.internal" in call_url
