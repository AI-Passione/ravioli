import uuid
import pytest
from datetime import datetime, UTC
from unittest.mock import MagicMock, AsyncMock
from ravioli.backend.core.models import Insight, Analysis

def create_mock_insight(id=None, analysis_id=None, content="Test", is_verified=False):
    return Insight(
        id=id or uuid.uuid4(),
        analysis_id=analysis_id or uuid.uuid4(),
        content=content,
        is_verified=is_verified,
        is_published=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )

def test_get_insight_stats(client, session):
    mock_query = MagicMock()
    session.query.return_value = mock_query
    mock_query.filter.return_value.scalar.side_effect = [10, 3] # verified, contributors
    mock_query.scalar.return_value = 5 # analyses_count
    
    response = client.get("/api/v1/insights/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert data["verified_count"] == 10
    assert data["analyses_count"] == 5
    assert data["contributors_count"] == 3

@pytest.mark.anyio
async def test_get_insights_summary(client, session, mocker):
    # Mock OllamaClient at its source since it's imported locally in the endpoint
    mock_ollama = mocker.patch("ravioli.backend.core.ollama.OllamaClient")
    mock_client = mock_ollama.return_value
    mock_client.generate_insights_summary = AsyncMock(return_value="* Point 1\n* Point 2\n* Point 3\n* Point 4\n* Point 5")
    
    # Mock DB query for insights
    mock_insight = create_mock_insight(is_verified=True)
    session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_insight]
    
    response = client.get("/api/v1/insights/summary?days=7")
    
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "* Point 1\n* Point 2\n* Point 3\n* Point 4\n* Point 5"
    assert data["insight_count"] == 1
    assert data["days"] == 7

def test_get_review_queue(client, session):
    mock_insight = create_mock_insight(content="Unverified", is_verified=False)
    session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_insight]
    
    response = client.get("/api/v1/insights/review-queue")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Unverified"
    assert data[0]["is_verified"] is False

def test_get_insights_feed(client, session):
    mock_insight = create_mock_insight(content="Verified", is_verified=True)
    session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_insight]
    
    response = client.get("/api/v1/insights/feed?days=30")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Verified"
    assert data[0]["is_verified"] is True

def test_verify_insight(client, session):
    insight_id = uuid.uuid4()
    mock_insight = create_mock_insight(id=insight_id, is_verified=False)
    session.query.return_value.filter.return_value.first.return_value = mock_insight
    
    response = client.patch(f"/api/v1/insights/{insight_id}/verify")
    
    assert response.status_code == 200
    assert mock_insight.is_verified is True
    assert session.commit.called

def test_reject_insight(client, session):
    insight_id = uuid.uuid4()
    mock_insight = create_mock_insight(id=insight_id)
    session.query.return_value.filter.return_value.first.return_value = mock_insight
    
    response = client.patch(f"/api/v1/insights/{insight_id}/reject")
    
    assert response.status_code == 200
    assert session.delete.called
    assert session.commit.called

def test_verify_insight_not_found(client, session):
    insight_id = uuid.uuid4()
    session.query.return_value.filter.return_value.first.return_value = None
    
    response = client.patch(f"/api/v1/insights/{insight_id}/verify")
    assert response.status_code == 404

def test_list_insights(client, session):
    mock_insight = create_mock_insight()
    session.query.return_value.order_by.return_value.all.return_value = [mock_insight]
    
    response = client.get("/api/v1/insights/")
    assert response.status_code == 200
    assert len(response.json()) == 1
