"""Unit tests for the Study Assistant Plugin."""

import pytest

from core.world_model.types import State
from plugins.study_agent.agent import StudyAgent
from plugins.study_agent.mcts_engine import OralExamPlanner
from plugins.study_agent.plugin import StudyAgentPlugin


def test_study_plugin_metadata():
    """Test plugin metadata fields."""
    plugin = StudyAgentPlugin()
    assert plugin.metadata.name == "study-agent"
    assert plugin.metadata.version == "0.1.0"
    assert "study" in plugin.metadata.tags


def test_study_agent_creation():
    """Test study agent creation."""
    plugin = StudyAgentPlugin()
    agent = plugin.create_agent(service=None)
    assert isinstance(agent, StudyAgent)
    assert agent.name == "study-agent"


def test_study_router_creation():
    """Test study router prefix and tags."""
    plugin = StudyAgentPlugin()
    router = plugin.create_router()
    assert router.tags == []  # Not forced in creator, but router.routes list exists
    assert len(router.routes) > 0


def test_study_graph_schemas():
    """Test entity types and relationship types registered in Knowledge Graph."""
    plugin = StudyAgentPlugin()
    entities = plugin.register_entity_types()
    relationships = plugin.register_relationship_types()

    assert any(et["type"] == "study_subject" for et in entities)
    assert any(et["type"] == "study_flashcard" for et in entities)
    assert any(rt["type"] == "STUDY_CONTAINS" for rt in relationships)


@pytest.mark.asyncio
async def test_mcts_planner_actions_and_transitions():
    """Test MCTS OralExamPlanner state transitions, UCT actions, and rewards."""
    topics = ["Derivate", "Integrali", "Limiti"]
    planner = OralExamPlanner(topics=topics, strictness="equo", difficulty_level=3)

    # Initial state
    initial_state = State(
        name="test_state",
        variables={
            "topics_scores": {},
            "history": [],
            "current_topic": None,
        },
    )

    # 1. Get available actions
    actions = planner.get_actions(initial_state)
    assert len(actions) > 0
    # There should be theory questions generated for the topics
    assert any(a.parameters.get("style") == "theory" for a in actions)
    assert any(a.parameters.get("topic") == "Derivate" for a in actions)

    # 2. Apply action
    action = actions[0]
    next_state = planner.apply_action(initial_state, action)

    # Check that history was updated
    assert len(next_state.variables["history"]) == 1
    assert next_state.variables["current_topic"] == action.parameters["topic"]
    # Check that score was initialized for this topic
    assert action.parameters["topic"] in next_state.variables["topics_scores"]

    # 3. Test reward functions for different profiles
    # Friendly Professor
    friendly_planner = OralExamPlanner(
        topics=topics, strictness="amichevole", difficulty_level=3
    )
    friendly_state = State(
        variables={
            "topics_scores": {"Derivate": 9.0},
            "history": [{"topic": "Derivate", "style": "theory"}],
        }
    )
    friendly_reward = friendly_planner.reward_fn(friendly_state)
    # Should reward high scores and topic coverage
    assert friendly_reward > 0.0

    # Strict Professor
    strict_planner = OralExamPlanner(
        topics=topics, strictness="scrupoloso", difficulty_level=5
    )
    strict_state = State(
        variables={
            "topics_scores": {"Derivate": 4.0},
            "history": [{"topic": "Derivate", "style": "trick"}],
        }
    )
    strict_reward = strict_planner.reward_fn(strict_state)
    # High reward for finding a failure / low score
    assert strict_reward > 0.0
