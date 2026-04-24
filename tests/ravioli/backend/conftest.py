import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from ravioli.backend.main import app
from ravioli.backend.core.database import get_db

@pytest.fixture(name="session")
def session_fixture(mocker):
    """Provides a mocked SQLAlchemy session."""
    mock_session = mocker.Mock()
    return mock_session

@pytest.fixture(name="client")
def client_fixture(session):
    """Provides a TestClient with the get_db dependency overridden."""
    def get_db_override():
        yield session

    app.dependency_overrides[get_db] = get_db_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
