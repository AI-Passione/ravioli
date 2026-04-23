import pytest
from fastapi.testclient import TestClient

from ravioli.backend.main import app
from ravioli.backend.core.database import get_db

# Use a separate SQLite database for testing if possible, 
# but since we use PostgreSQL types (UUID, JSON), 
# we'll use a mock or a separate test Postgres if we wanted to be thorough.
# For this walkthrough, we will override the get_db dependency with a mock session.

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
