"""
API Tests for Phase 8: Data Structures & Algorithms Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_triage_status():
    response = client.get("/api/v1/dsa/triage/status", headers={"X-User-Role": "viewer"})
    assert response.status_code == 200
    data = response.json()
    assert "total_queued" in data
    assert "is_empty" in data
    assert "queue_preview" in data
    assert data["total_queued"] >= 0


def test_triage_enqueue_and_dequeue_flow():
    # Enqueue a new patient
    payload = {
        "encounter_id": "TEST-ENC-999",
        "patient_id": "PT-TEST-01",
        "risk_score": 0.999,  # Highest priority
        "time_in_hospital": 14,
        "num_medications": 35,
        "primary_diagnosis": "Circulatory",
        "notes": "Urgent review required",
    }
    # Viewer cannot enqueue (403)
    resp_forbidden = client.post("/api/v1/dsa/triage/enqueue", json=payload, headers={"X-User-Role": "viewer"})
    assert resp_forbidden.status_code == 403

    # Analyst can enqueue (201)
    resp_enqueue = client.post("/api/v1/dsa/triage/enqueue", json=payload, headers={"X-User-Role": "analyst"})
    assert resp_enqueue.status_code == 201
    enqueued = resp_enqueue.json()
    assert enqueued["encounter_id"] == "TEST-ENC-999"
    assert enqueued["risk_score"] == 0.999

    # Peek top patient should now be our 0.999 patient
    resp_peek = client.get("/api/v1/dsa/triage/peek", headers={"X-User-Role": "viewer"})
    assert resp_peek.status_code == 200
    assert resp_peek.json()["encounter_id"] == "TEST-ENC-999"

    # Dequeue highest priority patient
    resp_dequeue = client.post("/api/v1/dsa/triage/dequeue", headers={"X-User-Role": "analyst"})
    assert resp_dequeue.status_code == 200
    dequeued = resp_dequeue.json()
    assert dequeued["encounter_id"] == "TEST-ENC-999"


def test_get_graph_schema():
    response = client.get("/api/v1/dsa/graph/schema", headers={"X-User-Role": "viewer"})
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert data["node_count"] > 0
    assert data["edge_count"] > 0


def test_graph_traverse_bfs_and_dfs():
    # BFS traversal
    bfs_payload = {
        "start_node": "Diabetes",
        "algorithm": "bfs",
        "visit_all_components": False,
    }
    resp_bfs = client.post("/api/v1/dsa/graph/traverse", json=bfs_payload, headers={"X-User-Role": "viewer"})
    assert resp_bfs.status_code == 200
    bfs_data = resp_bfs.json()
    assert bfs_data["algorithm"] == "BFS"
    assert bfs_data["start_node"] == "Diabetes"
    assert "traversal_path" in bfs_data
    assert len(bfs_data["traversal_path"]) > 1

    # DFS traversal
    dfs_payload = {
        "start_node": "Diabetes",
        "algorithm": "dfs",
        "visit_all_components": False,
    }
    resp_dfs = client.post("/api/v1/dsa/graph/traverse", json=dfs_payload, headers={"X-User-Role": "viewer"})
    assert resp_dfs.status_code == 200
    dfs_data = resp_dfs.json()
    assert dfs_data["algorithm"] == "DFS"
    assert len(dfs_data["traversal_path"]) > 1


def test_graph_shortest_path():
    payload = {
        "start_node": "Diabetes",
        "target_node": "Respiratory",
    }
    response = client.post("/api/v1/dsa/graph/shortest-path", json=payload, headers={"X-User-Role": "viewer"})
    assert response.status_code == 200
    data = response.json()
    assert data["path_found"] is True
    assert data["start_node"] == "Diabetes"
    assert data["target_node"] == "Respiratory"
    assert data["hops"] >= 1
    assert data["path"][0] == "Diabetes"
    assert data["path"][-1] == "Respiratory"
