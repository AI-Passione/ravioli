import uuid
from datetime import datetime

def test_create_mission(client, session):
    # Prepare mock data
    mission_id = uuid.uuid4()
    mission_data = {
        "title": "Test Mission",
        "description": "Testing the API",
        "mission_metadata": {"key": "value"}
    }
    
    # Mock session behavior
    # When session.add is called, we don't do much
    # When session.refresh is called, we set the ID and timestamps
    def mock_refresh(obj):
        obj.id = mission_id
        obj.status = "pending"
        obj.created_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()

    session.refresh.side_effect = mock_refresh

    # Execute request
    response = client.post("/api/v1/missions/", json=mission_data)

    # Assertions
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Mission"
    assert data["id"] == str(mission_id)
    assert session.add.called
    assert session.commit.called

def test_list_missions(client, session):
    mission_id = uuid.uuid4()
    class MockMission:
        def __init__(self, id, title):
            self.id = id
            self.title = title
            self.description = "Testing"
            self.status = "pending"
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            self.result = None
            self.mission_metadata = {}
            self.logs = []
    
    mock_mission = MockMission(mission_id, "Test Mission")
    session.query().offset().limit().all.return_value = [mock_mission]

    # Execute request
    response = client.get("/api/v1/missions/")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Mission"

def test_get_mission_not_found(client, session):
    # Mock session to return None
    session.query().filter().first.return_value = None

    # Execute request
    response = client.get(f"/api/v1/missions/{uuid.uuid4()}")

    # Assertions
    assert response.status_code == 404
    assert response.json()["detail"] == "Mission not found"
