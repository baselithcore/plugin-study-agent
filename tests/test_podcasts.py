"""Unit tests for the Educational Podcast Generator in Baselith Study Assistant."""

import json
from unittest.mock import ANY, AsyncMock, MagicMock, mock_open, patch

import pytest

from plugins.study_agent.agent import StudyAgent


class MockLLMService:
    def __init__(self, responses: list):
        self.responses = responses
        self.call_count = 0

    async def generate_response(self, prompt: str) -> str:
        res = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return res


@pytest.mark.asyncio
async def test_choose_podcast_professor():
    """Test dynamically choosing a professor profile based on subject and topic."""
    expected_profile = {
        "professor_name": "Prof.ssa Valeria Bianchi",
        "voice": "nova",
        "description": "Un tono energico per spiegare la programmazione.",
    }
    mock_llm = MockLLMService([json.dumps(expected_profile)])
    agent = StudyAgent(service=mock_llm)

    profile = await agent.choose_podcast_professor(
        subject_name="Programmazione", topic="Algoritmi di Ordinamento"
    )

    assert profile == expected_profile
    assert profile["professor_name"] == "Prof.ssa Valeria Bianchi"
    assert profile["voice"] == "nova"


@pytest.mark.asyncio
async def test_generate_podcast():
    """Test generating a podcast with structured script episodes and TTS synthesis."""
    prof_profile = {
        "professor_name": "Prof. Marco Rossi",
        "voice": "onyx",
        "description": "Tono formale scientifico",
    }

    podcast_script = {
        "title": "Alla scoperta di Dijkstra",
        "episodes": [
            {
                "episode_number": 1,
                "title": "Introduzione ai cammini minimi",
                "script_text": "Benvenuti in questa puntata del nostro podcast didattico...",
            },
            {
                "episode_number": 2,
                "title": "Funzionamento dell'algoritmo",
                "script_text": "Oggi vediamo nel dettaglio i passaggi di Dijkstra...",
            },
        ],
    }

    mock_llm = MockLLMService([json.dumps(prof_profile), json.dumps(podcast_script)])

    agent = StudyAgent(service=mock_llm)

    # Mock VoiceResponse returned by VoiceService.text_to_speech
    mock_voice_res = MagicMock()
    mock_voice_res.audio_bytes = b"fake-mp3-data"
    mock_voice_res.content = b"fake-mp3-data"

    mock_voice_service_inst = MagicMock()
    mock_voice_service_inst.text_to_speech = AsyncMock(return_value=mock_voice_res)

    with (
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_subjects",
            new_callable=AsyncMock,
        ) as mock_get_subjects,
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_documents",
            new_callable=AsyncMock,
        ) as mock_get_docs,
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_document",
            new_callable=AsyncMock,
        ) as mock_get_doc,
        patch(
            "plugins.study_agent.persistence.StudyDAO.create_podcast",
            new_callable=AsyncMock,
        ) as mock_create_podcast,
        patch(
            "plugins.study_agent.persistence.StudyDAO.create_podcast_episode",
            new_callable=AsyncMock,
        ) as mock_create_episode,
        patch(
            "core.services.voice.service.VoiceService",
            return_value=mock_voice_service_inst,
        ),
        patch("os.makedirs"),
        patch("builtins.open", mock_open()) as mock_file,
    ):
        mock_get_subjects.return_value = [{"id": 1, "name": "Algoritmi"}]
        mock_get_docs.return_value = [{"id": 10, "name": "dijkstra.txt"}]
        mock_get_doc.return_value = {
            "id": 10,
            "name": "dijkstra.txt",
            "raw_text": "Grafi orientati e cammini minimi...",
        }
        mock_create_podcast.return_value = 100
        mock_create_episode.side_effect = [1001, 1002]

        result = await agent.generate_podcast(
            subject_id=1, topic="Algoritmo Dijkstra", depth_level="normale"
        )

        assert result["id"] == 100
        assert result["title"] == "Alla scoperta di Dijkstra"
        assert result["professor_name"] == "Prof. Marco Rossi"
        assert result["professor_voice"] == "onyx"
        assert result["depth_level"] == "normale"
        assert len(result["episodes"]) == 2

        # Verify DB calls
        mock_create_podcast.assert_called_once_with(
            subject_id=1,
            title="Alla scoperta di Dijkstra",
            topic="Algoritmo Dijkstra",
            professor_voice="onyx",
            professor_name="Prof. Marco Rossi",
            depth_level="normale",
        )
        assert mock_create_episode.call_count == 2
        mock_create_episode.assert_any_call(
            podcast_id=100,
            episode_number=1,
            title="Introduzione ai cammini minimi",
            script_text="Benvenuti in questa puntata del nostro podcast didattico...",
            audio_filename=ANY,
        )

        # Verify TTS HD calls
        assert mock_voice_service_inst.text_to_speech.call_count == 2
        mock_voice_service_inst.text_to_speech.assert_any_call(
            text="Benvenuti in questa puntata del nostro podcast didattico...",
            voice="onyx",
            format=ANY,
            provider=ANY,
        )

        # Verify file saving happened
        assert mock_file.call_count == 2
        mock_file().write.assert_called_with(b"fake-mp3-data")


@pytest.mark.asyncio
async def test_extract_document_topics():
    """Test extracting document topics via LLM."""
    expected_topics = ["Dijkstra Complexity", "Bellman-Ford Algorithm", "A* Search"]
    mock_llm = MockLLMService([json.dumps(expected_topics)])
    agent = StudyAgent(service=mock_llm)

    with (
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_subjects",
            new_callable=AsyncMock,
        ) as mock_get_subjects,
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_documents",
            new_callable=AsyncMock,
        ) as mock_get_docs,
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_document",
            new_callable=AsyncMock,
        ) as mock_get_doc,
    ):
        mock_get_subjects.return_value = [{"id": 1, "name": "Algoritmi"}]
        mock_get_docs.return_value = [{"id": 10, "name": "dijkstra.txt"}]
        mock_get_doc.return_value = {
            "id": 10,
            "name": "dijkstra.txt",
            "raw_text": "Grafi orientati e cammini minimi...",
        }

        topics = await agent.extract_document_topics(subject_id=1)
        assert topics == expected_topics
        assert mock_llm.call_count == 1
