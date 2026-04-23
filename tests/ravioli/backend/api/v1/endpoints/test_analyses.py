import uuid
from datetime import datetime, UTC

def test_create_analysis(client, session):
    # Prepare mock data
    analysis_id = uuid.uuid4()
    analysis_data = {
        "title": "Test Analysis",
        "description": "Testing the API",
        "analysis_metadata": {"key": "value"}
    }
    
    # Mock session behavior
    # When session.add is called, we don't do much
    # When session.refresh is called, we set the ID and timestamps
    def mock_refresh(obj):
        obj.id = analysis_id
        obj.status = "pending"
        obj.created_at = datetime.now(UTC)
        obj.updated_at = datetime.now(UTC)

    session.refresh.side_effect = mock_refresh

    # Execute request
    response = client.post("/api/v1/analyses/", json=analysis_data)

    # Assertions
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Analysis"
    assert data["id"] == str(analysis_id)
    assert session.add.called
    assert session.commit.called

def test_list_analyses(client, session):
    analysis_id = uuid.uuid4()
    class MockAnalysis:
        def __init__(self, id, title):
            self.id = id
            self.title = title
            self.description = "Testing"
            self.status = "pending"
            self.created_at = datetime.now(UTC)
            self.updated_at = datetime.now(UTC)
            self.result = None
            self.analysis_metadata = {}
            self.logs = []
    
    mock_analysis = MockAnalysis(analysis_id, "Test Analysis")
    session.query().offset().limit().all.return_value = [mock_analysis]

    # Execute request
    response = client.get("/api/v1/analyses/")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Analysis"

def test_get_analysis_not_found(client, session):
    # Mock session to return None
    session.query().filter().first.return_value = None

    # Execute request
    response = client.get(f"/api/v1/analyses/{uuid.uuid4()}")

    # Assertions
    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis not found"
