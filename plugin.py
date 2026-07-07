"""Plugin class definition for Baselith Study Assistant."""

from typing import Any

from fastapi import APIRouter

from core.plugins import AgentPlugin, GraphPlugin, RouterPlugin

from .agent import StudyAgent
from .router import create_router


class StudyAgentPlugin(AgentPlugin, RouterPlugin, GraphPlugin):
    """
    Baselith Study Assistant Plugin.
    Extends the platform with:
    - Tutoring Agents per course
    - Automatic flashcard generation & SM-2 Spaced Repetition reviews
    - Voice-enabled Oral Exam Simulator powered by MCTS
    - Custom UI dashboard widgets and styles
    - Knowledge Graph entity/relationship bindings
    """

    def create_agent(self, service: Any, **kwargs) -> StudyAgent:
        """Create StudyAgent instance."""
        return StudyAgent(service)

    def create_router(self) -> APIRouter:
        """Create APIRouter for study API routes."""
        return create_router(self)

    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize plugin persistence layers."""
        await super().initialize(config)

        # Initialize persistence pool and verify database schema
        from .persistence import ensure_schema, init_pool

        await init_pool()
        await ensure_schema()

        print("[Study Assistant] Plugin initialized successfully!")

    async def shutdown(self) -> None:
        """Close DB pool on shutdown."""
        from .persistence import close_pool

        await close_pool()
        print("[Study Assistant] Plugin shut down.")
        await super().shutdown()

    def get_static_paths(self) -> list[str]:
        """Expose local static directory.

        Serves the built React SPA (plugins/study_agent/ui, see ui/README
        for the build step) via the core's automatic index.html SPA mount,
        alongside runtime-generated assets in static/podcasts/.
        """
        return ["static"]

    def get_ui_tabs(self) -> list[dict[str, str]]:
        """Add navigation entry to the Admin Sidebar."""
        return [{"id": "study-dashboard", "label": "Studio & Esami"}]

    def register_entity_types(self) -> list[dict[str, Any]]:
        """Register custom Knowledge Graph entities for study concepts."""
        return [
            {
                "type": "study_subject",
                "display_name": "Materia",
                "schema": {
                    "name": str,
                    "description": str,
                },
                "icon": "",
            },
            {
                "type": "study_flashcard",
                "display_name": "Flashcard",
                "schema": {
                    "question": str,
                    "answer": str,
                    "ease_factor": float,
                    "interval_days": int,
                },
                "icon": "",
            },
        ]

    def register_relationship_types(self) -> list[dict[str, Any]]:
        """Register relationships between study nodes."""
        return [
            {
                "type": "STUDY_CONTAINS",
                "source_types": ["study_subject"],
                "target_types": ["study_flashcard"],
                "properties_schema": {},
                "bidirectional": False,
                "label": "CONTIENE",
            }
        ]


# Cleanup imports to prevent the core loader from mistaking base plugin classes for the active plugin class
del AgentPlugin
del RouterPlugin
del GraphPlugin
