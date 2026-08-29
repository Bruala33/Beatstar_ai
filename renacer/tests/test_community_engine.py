import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["num_lanes"] == 3
    assert "osu! Mania" in data["sources"]
    assert "Quaver" in data["sources"]
    assert "Clone Hero" in data["sources"]

def test_search_community_empty():
    response = client.get("/api/v1/search/community?q=")
    assert response.status_code in (422, 200)

def test_search_community_query():
    response = client.get("/api/v1/search/community?q=Galaxy")
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    if len(results) > 0:
        first = results[0]
        assert "title" in first
        assert "source" in first
        assert "difficulties" in first
        assert isinstance(first["difficulties"], list)

def test_download_proxy_invalid():
    response = client.get("/api/v1/download/proxy?url=invalid-url")
    assert response.status_code == 400
