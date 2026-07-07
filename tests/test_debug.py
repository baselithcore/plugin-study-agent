"""Unit tests for the Study Assistant Debug and Telemetry features."""

import concurrent.futures

from fastapi import FastAPI
from fastapi.testclient import TestClient

from plugins.study_agent.debug_tracker import DebugTracker
from plugins.study_agent.plugin import StudyAgentPlugin


def test_debug_tracker_basic_operations():
    """Test DebugTracker adding, retrieving, and clearing events."""
    DebugTracker.clear()
    assert len(DebugTracker.get_events()) == 0

    # Add MCTS event
    DebugTracker.add_event("mcts_search", {"iterations": 50, "time_ms": 120.5})
    # Add Graph RAG event
    DebugTracker.add_event(
        "graph_rag", {"query": "test query", "cypher": "MATCH (n) RETURN n"}
    )

    events = DebugTracker.get_events()
    assert len(events) == 2
    # Newest should be first
    assert events[0]["event_type"] == "graph_rag"
    assert events[0]["details"]["query"] == "test query"

    assert events[1]["event_type"] == "mcts_search"
    assert events[1]["details"]["iterations"] == 50

    # Clear
    DebugTracker.clear()
    assert len(DebugTracker.get_events()) == 0


def test_debug_tracker_thread_safety():
    """Verify thread-safety of DebugTracker by writing from multiple concurrent threads."""
    DebugTracker.clear()

    num_threads = 10
    events_per_thread = 5

    def worker(thread_idx):
        for i in range(events_per_thread):
            DebugTracker.add_event("thread_event", {"thread": thread_idx, "idx": i})

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, idx) for idx in range(num_threads)]
        concurrent.futures.wait(futures)

    events = DebugTracker.get_events()
    assert len(events) == num_threads * events_per_thread
    # Ensure all threads successfully stored their data
    for idx in range(num_threads):
        thread_events = [e for e in events if e["details"]["thread"] == idx]
        assert len(thread_events) == events_per_thread


def test_debug_endpoints():
    """Test debug router endpoints via TestClient."""
    DebugTracker.clear()
    DebugTracker.add_event("mcts_search", {"iterations": 10})

    # Create temporary FastAPI app to host the plugin's router
    app = FastAPI()
    plugin = StudyAgentPlugin()
    router = plugin.create_router()
    app.include_router(router)

    client = TestClient(app)

    # 1. GET /debug/events
    response = client.get("/debug/events")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["event_type"] == "mcts_search"
    assert data[0]["details"]["iterations"] == 10

    # 2. POST /debug/clear
    response = client.post("/debug/clear")
    assert response.status_code == 200
    assert response.json() == {"success": True}

    # 3. GET /debug/events again (should be empty)
    response = client.get("/debug/events")
    assert response.status_code == 200
    assert len(response.json()) == 0
