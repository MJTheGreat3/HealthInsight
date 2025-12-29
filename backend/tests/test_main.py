"""
Basic tests for the main application
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "HealthInsightCore API is running"}


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


def test_api_status():
    """Test the API status endpoint"""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json() == {"status": "API v1 is running"}