from fastapi.testclient import TestClient

from app.api import create_app


def test_health_endpoints_are_dependency_free_and_explicit():
    client = TestClient(create_app())
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").json() == {"status": "ready"}


def test_incident_api_returns_waiting_approval_and_replay_same_task():
    client = TestClient(create_app())
    payload = {
        "request_id": "api-001",
        "asset_id": "line-7",
        "summary": "Pressure anomaly with uncertain root cause",
    }
    first = client.post("/v1/incidents", json=payload)
    replay = client.post("/v1/incidents", json=payload)
    assert first.status_code == 202
    assert first.json()["status"] == "WAITING_APPROVAL"
    assert replay.json()["task_id"] == first.json()["task_id"]


def test_approval_endpoint_transitions_task_to_completed():
    client = TestClient(create_app())
    created = client.post("/v1/incidents", json={
        "request_id": "api-002",
        "asset_id": "line-8",
        "summary": "Conveyor speed anomaly",
    }).json()
    approved = client.post(
        f"/v1/tasks/{created['task_id']}/approve",
        json={"actor": "ops@example.com"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "COMPLETED"
