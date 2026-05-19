"""Sample unit test for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

@pytest.mark.unit
def test_app_instantiation():
    """Test that the FastAPI app is properly instantiated."""
    assert app is not None
    assert app.title == "Apply-Agent API"


@pytest.mark.unit
def test_app_routes():
    """Test that core routes are registered."""
    routes = [route.path for route in app.routes]
    assert "/docs" in routes or "/openapi.json" in routes


@pytest.mark.unit
def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
