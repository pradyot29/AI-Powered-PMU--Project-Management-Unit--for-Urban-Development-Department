import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_get_templates():
    """Test templates endpoint"""
    response = client.get("/templates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "id" in data[0]
    assert "document_type" in data[0]

def test_generate_official_letter():
    """Test generating official letter"""
    request_data = {
        "document_type": "official_letter",
        "subject": "Test Letter",
        "content": "This is a test letter for unit testing",
        "recipient_name": "Test Recipient",
        "recipient_designation": "Test Designation",
        "priority": "normal"
    }
    
    response = client.post("/generate", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "generated_content" in data
    assert data["document_type"] == "official_letter"

def test_list_documents():
    """Test listing documents"""
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data

def test_get_statistics():
    """Test statistics endpoint"""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "total_tokens_used" in data