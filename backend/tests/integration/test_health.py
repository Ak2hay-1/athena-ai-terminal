def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert payload["service"] == "Athena AI Terminal"
