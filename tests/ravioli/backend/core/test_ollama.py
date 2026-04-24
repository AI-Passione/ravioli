import pytest
from unittest.mock import MagicMock, AsyncMock
from ravioli.backend.core.ollama import OllamaClient
from ravioli.backend.core.models import SystemSetting
from ravioli.backend.core.encryption import encrypt_value

@pytest.fixture
def mock_db(session):
    return session

def test_ollama_client_default_config(mock_db, mocker):
    # Mock no settings in DB
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Mock settings.ollama_model to be consistent
    mocker.patch("ravioli.backend.core.ollama.settings.ollama_model", "gemma3:4b")
    
    client = OllamaClient(mock_db)
    assert client.mode == "default"
    assert "localhost" in client.base_url or "ollama" in client.base_url
    assert client.model == "gemma3:4b"
    assert client.api_key == ""

def test_ollama_client_cloud_mode(mock_db):
    # Mock cloud settings in DB - must use encrypted key
    encrypted_key = encrypt_value("test-key")
    setting = SystemSetting(key="ollama", value={
        "mode": "cloud",
        "default_model": "custom-model",
        "api_key": encrypted_key
    })
    mock_db.query.return_value.filter.return_value.first.return_value = setting
    
    client = OllamaClient(mock_db)
    assert client.mode == "cloud"
    assert client.base_url == "https://api.ollama.com"
    assert client.model == "custom-model"
    assert client.api_key == "test-key"

def test_ollama_client_local_mode_docker(mock_db, mocker):
    # Mock local settings in DB
    setting = SystemSetting(key="ollama", value={
        "mode": "local",
        "base_url": "http://localhost:11434"
    })
    mock_db.query.return_value.filter.return_value.first.return_value = setting
    
    # Mock being inside docker
    mocker.patch("os.path.exists", return_value=True)
    
    client = OllamaClient(mock_db)
    assert client.mode == "local"
    assert client.base_url == "http://host.docker.internal:11434"

@pytest.mark.anyio
async def test_generate_description_success(mock_db, mocker):
    # Mock settings - must use encrypted key
    encrypted_key = encrypt_value("key")
    setting = SystemSetting(key="ollama", value={"mode": "cloud", "api_key": encrypted_key})
    mock_db.query.return_value.filter.return_value.first.return_value = setting
    
    client = OllamaClient(mock_db)
    
    # Mock httpx response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "A beautiful dataset."}
    
    mock_httpx = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    mock_httpx.return_value = mock_response
    
    desc = await client.generate_description("test.csv", "sample data")
    assert desc == "A beautiful dataset."
    
    # Verify headers (Auth should be present in cloud mode)
    args, kwargs = mock_httpx.call_args
    assert "Authorization" in kwargs["headers"]
    assert "Bearer key" in kwargs["headers"]["Authorization"]

@pytest.mark.anyio
async def test_generate_description_auth_failure(mock_db, mocker):
    encrypted_key = encrypt_value("wrong")
    setting = SystemSetting(key="ollama", value={"mode": "cloud", "api_key": encrypted_key})
    mock_db.query.return_value.filter.return_value.first.return_value = setting
    
    client = OllamaClient(mock_db)
    
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    
    mock_httpx = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    mock_httpx.return_value = mock_response
    
    with pytest.raises(Exception) as exc:
        await client.generate_description("test.csv", "sample")
    assert "authentication failed" in str(exc.value)
