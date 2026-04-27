import uuid
from datetime import datetime, UTC

def test_create_log(client, session):
    # Prepare mock data
    analysis_id = uuid.uuid4()
    log_id = uuid.uuid4()
    log_data = {
        "analysis_id": str(analysis_id),
        "log_type": "thought",
        "content": "Agent is thinking...",
        "data": {"thought_id": 1}
    }
    
    # Mock session behavior
    def mock_refresh(obj):
        obj.id = log_id
        obj.timestamp = datetime.now(UTC)

    session.refresh.side_effect = mock_refresh
    
    # Mock analysis check
    session.query().filter().first.return_value = True

    # Execute request
    response = client.post("/api/v1/analysis-logs/", json=log_data)

    # Assertions
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Agent is thinking..."
    assert data["analysis_id"] == str(analysis_id)

def test_list_logs_for_analysis(client, session):
    analysis_id = uuid.uuid4()
    class MockLog:
        def __init__(self):
            self.id = uuid.uuid4()
            self.analysis_id = analysis_id
            self.log_type = "thought"
            self.content = "Thinking..."
            self.tool_name = None
            self.data = {}
            self.timestamp = datetime.now(UTC)
            
    mock_log = MockLog()
    session.query().filter().order_by().all.return_value = [mock_log]

    # Execute request
    response = client.get(f"/api/v1/analysis-logs/analysis/{analysis_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Thinking..."
