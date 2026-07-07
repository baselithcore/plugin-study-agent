"""Unit tests for the Active Study Module in Baselith Study Assistant."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from plugins.study_agent.agent import StudyAgent


class MockLLMService:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.generate_response = AsyncMock(return_value=response_text)


@pytest.mark.asyncio
async def test_select_feynman_concept():
    """Test extracting Feynman concept from subject documents."""
    mock_llm = MockLLMService("Teorema dei Carabinieri")
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
        mock_get_subjects.return_value = [{"id": 1, "name": "Analisi 1"}]
        mock_get_docs.return_value = [{"id": 10, "name": "Appunti.txt"}]
        mock_get_doc.return_value = {
            "id": 10,
            "name": "Appunti.txt",
            "raw_text": "Successioni e limiti ordinati...",
        }

        concept = await agent.select_feynman_concept(subject_id=1)
        assert concept == "Teorema dei Carabinieri"
        mock_llm.generate_response.assert_called_once()


@pytest.mark.asyncio
async def test_evaluate_feynman_step():
    """Test evaluating student's Feynman explanation response."""
    expected_feedback = {
        "punti_di_forza": ["Hai spiegato bene il concetto di limite."],
        "lacune": ["Manca la definizione formale di epsilon-delta."],
        "inesattezze": ["Hai confuso convergenza e divergenza."],
        "analogia": "Come avvicinarsi a un traguardo senza mai toccarlo.",
        "domanda_followup": "Cosa succede se prendiamo un epsilon arbitrariamente piccolo?",
    }

    mock_llm = MockLLMService(json.dumps(expected_feedback))
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
        mock_get_subjects.return_value = [{"id": 1, "name": "Analisi 1"}]
        mock_get_docs.return_value = [{"id": 10, "name": "Appunti.txt"}]
        mock_get_doc.return_value = {
            "id": 10,
            "name": "Appunti.txt",
            "raw_text": "Epsilon delta limite...",
        }

        result = await agent.evaluate_feynman_step(
            subject_id=1,
            concept_name="Limiti",
            explanation="Un limite descrive il comportamento di una funzione quando si avvicina a un punto.",
            history=[],
        )

        assert result == expected_feedback
        mock_llm.generate_response.assert_called_once()


@pytest.mark.asyncio
async def test_deconstruct_subject_concepts():
    """Test concept deconstruction focus sheets generation."""
    expected_deconstruct = {
        "cheat_sheet": [
            {"term": "Derivata", "definition": "Rapporto incrementale al limite."}
        ],
        "likely_questions": [
            {
                "question": "Cos'e' la derivata?",
                "focus_answer": "Pendenza della retta tangente.",
            }
        ],
        "mental_hooks": [{"concept": "Derivata", "mnemonic": "Pensa a un tachimetro."}],
        "concept_map": [
            {"source": "Funzione", "relationship": "ha derivata", "target": "Derivata"}
        ],
    }

    mock_llm = MockLLMService(json.dumps(expected_deconstruct))
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
        mock_get_subjects.return_value = [{"id": 1, "name": "Analisi 1"}]
        mock_get_docs.return_value = [{"id": 10, "name": "Appunti.txt"}]
        mock_get_doc.return_value = {
            "id": 10,
            "name": "Appunti.txt",
            "raw_text": "Derivate e rette tangenti...",
        }

        result = await agent.deconstruct_subject_concepts(subject_id=1)
        assert result == expected_deconstruct
        mock_llm.generate_response.assert_called_once()
