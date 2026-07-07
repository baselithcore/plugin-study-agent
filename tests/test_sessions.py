"""Unit tests for the Oral Exam Sessions endpoints in Baselith Study Assistant."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from plugins.study_agent.plugin import StudyAgentPlugin


@pytest.mark.asyncio
async def test_get_oral_session_success():
    """Test successful retrieval of an oral session."""
    plugin = StudyAgentPlugin()
    router = plugin.create_router()

    # Find the route for GET /sessions/oral/{session_id}
    route = next(
        (
            r
            for r in router.routes
            if r.path == "/sessions/oral/{session_id}" and "GET" in r.methods
        ),
        None,
    )
    assert route is not None
    endpoint = route.endpoint

    mock_session = {
        "id": 42,
        "subject_id": 1,
        "professor_name": "Prof. Rossi",
        "strictness": "equo",
        "difficulty_level": 3,
        "score": 8.5,
        "status": "active",
        "transcript": [{"type": "system", "message": "Esame avviato"}],
        "current_topic": "Limiti",
    }

    with patch(
        "plugins.study_agent.persistence.StudyDAO.get_session", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_session

        res = await endpoint(session_id=42)
        assert res["id"] == 42
        assert res["session_id"] == 42
        assert res["status"] == "active"
        assert res["professor_name"] == "Prof. Rossi"
        mock_get.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_get_oral_session_not_found():
    """Test retrieval of a non-existent oral session."""
    plugin = StudyAgentPlugin()
    router = plugin.create_router()

    route = next(
        (
            r
            for r in router.routes
            if r.path == "/sessions/oral/{session_id}" and "GET" in r.methods
        ),
        None,
    )
    assert route is not None
    endpoint = route.endpoint

    with patch(
        "plugins.study_agent.persistence.StudyDAO.get_session", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(session_id=999)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Session non trovata"
        mock_get.assert_called_once_with(999)
