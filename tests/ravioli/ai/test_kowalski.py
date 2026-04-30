import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from ravioli.ai.Kowalski import KowalskiAgent

@pytest.fixture
@patch('ravioli.ai.Kowalski.OllamaClient')
@patch('ravioli.ai.Kowalski.SQLDatabase')
@patch('ravioli.ai.Kowalski.create_sql_agent_executor')
@patch('ravioli.ai.Kowalski.get_query_database_tool')
@patch('ravioli.ai.Kowalski.initialize_agent')
@patch('ravioli.ai.Kowalski.Ollama')
def agent(mock_ollama, mock_init, mock_get_tool, mock_create, mock_db, mock_client):
    mock_client_instance = MagicMock()
    mock_client_instance.model = "test_model"
    mock_client_instance.mode = "local"
    mock_client_instance.generate = AsyncMock()
    mock_client.return_value = mock_client_instance
    return KowalskiAgent(db_session=MagicMock())

def test_load_persona(agent):
    assert "You are Kowalski" in agent.persona

@pytest.mark.anyio
async def test_generate(agent):
    agent.ollama_client.generate.return_value = "Response"
    res = await agent.generate("Test Task", "Task Name")
    assert res == "Response"
    agent.ollama_client.generate.assert_called_once()

@pytest.mark.anyio
@patch('ravioli.ai.Kowalski.tool_generate_sql')
async def test_generate_sql(mock_tool, agent):
    mock_tool.return_value = "SELECT * FROM test"
    res = await agent.generate_sql("query?", "test_table")
    assert res == "SELECT * FROM test"
    mock_tool.assert_called_once()

@pytest.mark.anyio
@patch('ravioli.ai.Kowalski.tool_create_viz_payload')
async def test_create_viz_payload(mock_tool, agent):
    mock_tool.return_value = {"type": "chart"}
    res = await agent.create_viz_payload("SELECT * FROM test", "query?")
    assert res == {"type": "chart"}
    mock_tool.assert_called_once()

@pytest.mark.anyio
async def test_process_question_text(agent):
    agent.generate = AsyncMock(return_value={"requires_viz": False})
    updates = []
    async for update in agent.process_question("query?", "test_table"):
        updates.append(update)
    assert len(updates) == 1
    assert updates[0] == {"answer_type": "text"}

@pytest.mark.anyio
async def test_process_question_viz(agent):
    agent.generate = AsyncMock(return_value={"requires_viz": True})
    agent.generate_sql = AsyncMock(return_value="SELECT 1")
    agent.create_viz_payload = AsyncMock(return_value={"type": "chart"})
    updates = []
    async for update in agent.process_question("query?", "test_table"):
        updates.append(update)
    assert len(updates) == 3
    assert updates[2]["answer_type"] == "viz"

def test_chat(agent):
    agent.agent.invoke.return_value = {"output": "Response"}
    res = agent.chat("Test")
    assert res == "Response"

def test_chat_error(agent):
    agent.agent.invoke.side_effect = Exception("Chat Error")
    res = agent.chat("Test")
    assert "Error: Chat Error" in res
