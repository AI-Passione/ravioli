import uuid
import pytest
from datetime import datetime, UTC
from unittest.mock import MagicMock
from ravioli.backend.core.models import KnowledgePage

def create_mock_page(id=None, title="Test Page", properties=None, content=None):
    return KnowledgePage(
        id=id or uuid.uuid4(),
        title=title,
        properties=properties if properties is not None else {"title": [{"text": {"content": title}}]},
        content=content or [{"type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Hello"}}]}}],
        icon={"type": "emoji", "emoji": "📄"},
        cover={"type": "external", "external": {"url": "https://example.com/cover.jpg"}},
        ownership_type="individual",
        source="manual",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )

def test_list_knowledge_pages(client, session):
    mock_page = create_mock_page()
    session.query.return_value.order_by.return_value.all.return_value = [mock_page]
    
    response = client.get("/api/v1/knowledge/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Page"
    assert data[0]["properties"]["title"][0]["text"]["content"] == "Test Page"

def test_list_knowledge_pages_with_null_properties(client, session):
    # This specifically tests the fix for ResponseValidationError
    mock_page = create_mock_page(title="Null Props Page")
    mock_page.properties = None # Simulate NULL in DB
    
    session.query.return_value.order_by.return_value.all.return_value = [mock_page]
    
    response = client.get("/api/v1/knowledge/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Null Props Page"
    # The schema should default it to {}
    assert data[0]["properties"] == {}

def test_create_knowledge_page(client, session):
    payload = {
        "title": "New Intelligence",
        "properties": {"tags": ["AI", "Notion"]},
        "content": [{"type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Body"}}]}}],
        "icon": {"type": "emoji", "emoji": "🧠"},
        "ownership_type": "team"
    }
    
    # Mock the return value of create to have timestamps
    mock_page = create_mock_page(title="New Intelligence")
    session.add.side_effect = lambda x: setattr(x, 'id', mock_page.id) or setattr(x, 'created_at', mock_page.created_at) or setattr(x, 'updated_at', mock_page.updated_at)
    
    response = client.post("/api/v1/knowledge/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Intelligence"
    assert data["ownership_type"] == "team"
    assert session.add.called
    assert session.commit.called

def test_get_knowledge_page(client, session):
    page_id = uuid.uuid4()
    mock_page = create_mock_page(id=page_id)
    session.query.return_value.filter.return_value.first.return_value = mock_page
    
    response = client.get(f"/api/v1/knowledge/{page_id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(page_id)

def test_update_knowledge_page(client, session):
    page_id = uuid.uuid4()
    mock_page = create_mock_page(id=page_id)
    session.query.return_value.filter.return_value.first.return_value = mock_page
    
    payload = {"title": "Updated Title"}
    response = client.patch(f"/api/v1/knowledge/{page_id}", json=payload)
    
    assert response.status_code == 200
    assert mock_page.title == "Updated Title"
    assert session.commit.called

def test_delete_knowledge_page(client, session):
    page_id = uuid.uuid4()
    mock_page = create_mock_page(id=page_id)
    session.query.return_value.filter.return_value.first.return_value = mock_page
    
    response = client.delete(f"/api/v1/knowledge/{page_id}")
    assert response.status_code == 204
    assert session.delete.called
    assert session.commit.called
