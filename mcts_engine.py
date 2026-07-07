"""MCTS-based Questioning Engine for Oral Exam Simulations."""

import random
from typing import Any

from core.observability.logging import get_logger
from core.world_model.simulation import MCTSSimulator
from core.world_model.types import Action, ActionType, State

logger = get_logger(__name__)


class OralExamPlanner:
    """
    Coordinates MCTS planning to choose the next question or action
    for an oral exam based on professor strictness and student answers.
    """

    def __init__(
        self,
        topics: list[str],
        strictness: str = "equo",
        difficulty_level: int = 3,
    ) -> None:
        """
        Initialize oral exam planner.

        Args:
            topics: List of topics in the syllabus.
            strictness: amichevole (friendly), equo (fair), scrupoloso (strict).
            difficulty_level: 1 to 5.
        """
        self.topics = topics
        self.strictness = strictness.lower()
        self.difficulty_level = difficulty_level

        # Instantiate MCTSSimulator
        self.simulator = MCTSSimulator(
            get_actions=self.get_actions,
            apply_action=self.apply_action,
            reward_fn=self.reward_fn,
            is_goal=self.is_goal,
        )

    def get_actions(self, state: State) -> list[Action]:
        """
        Generate possible questioning actions for the professor from the current state.

        Actions:
        - Ask theory question on topic X
        - Ask application/exercise question on topic X
        - Ask trick/edge-case question on topic X
        - Give hint on current topic
        """
        actions = []
        history = state.get("history", [])

        # Avoid listing too many actions to keep search tree branching factor controlled
        # Focus on topics that haven't been asked 3+ times
        for topic in self.topics:
            asked_count = sum(1 for act in history if act.get("topic") == topic)
            if asked_count >= 3:
                continue

            # Theory action
            actions.append(
                Action(
                    name=f"ask_{topic}_theory",
                    action_type=ActionType.COMMUNICATE,
                    parameters={"topic": topic, "style": "theory"},
                    cost=1.0,
                    description=f"Domanda di teoria su {topic}",
                )
            )

            # Application action (more common for higher difficulty)
            if self.difficulty_level >= 2:
                actions.append(
                    Action(
                        name=f"ask_{topic}_application",
                        action_type=ActionType.COMMUNICATE,
                        parameters={"topic": topic, "style": "application"},
                        cost=1.5,
                        description=f"Esercizio o applicazione pratica su {topic}",
                    )
                )

            # Trick/edge case action (more common for strict professor)
            if self.difficulty_level >= 3 or self.strictness == "scrupoloso":
                actions.append(
                    Action(
                        name=f"ask_{topic}_trick",
                        action_type=ActionType.COMMUNICATE,
                        parameters={"topic": topic, "style": "trick"},
                        cost=2.0,
                        description=f"Domanda tranello o caso limite su {topic}",
                    )
                )

        # Hint action: if there is a current topic and the student score is low (< 6.0)
        current_topic = state.get("current_topic")
        if current_topic:
            scores = state.get("topics_scores", {})
            curr_score = scores.get(current_topic)
            if curr_score is not None and curr_score < 6.0:
                actions.append(
                    Action(
                        name=f"give_hint_{current_topic}",
                        action_type=ActionType.COMMUNICATE,
                        parameters={"topic": current_topic, "style": "hint"},
                        cost=0.5,
                        description=f"Suggerimento costruttivo su {current_topic}",
                    )
                )

        return actions

    def apply_action(self, state: State, action: Action) -> State:
        """
        Simulate the transition of state when an action is taken.
        Updates student scores based on probabilistic performance.
        """
        new_state = state.copy()

        # Get parameters
        params = action.parameters
        topic = params.get("topic")
        style = params.get("style")

        # Update history
        history = list(new_state.get("history", []))
        history.append(params)
        new_state.variables["history"] = history

        # Get scores
        scores = dict(new_state.get("topics_scores", {}))
        curr_score = scores.get(topic)

        # Determine base level or update it
        if curr_score is None:
            # First time asking about this topic. Assume a baseline student capability of 6.5
            curr_score = 6.5

        # Simulating student performance based on question type
        if style == "theory":
            # Theory is relatively easy. High probability of maintaining score
            delta = random.uniform(-0.5, 1.5)  # nosec B311
        elif style == "application":
            # Requires application. Harder
            delta = random.uniform(-1.5, 1.0)  # nosec B311
        elif style == "trick":
            # Trick question. Prone to mistakes
            delta = random.uniform(-2.5, 0.5)  # nosec B311
        elif style == "hint":
            # Hint helps!
            delta = random.uniform(1.0, 2.5)  # nosec B311
        else:
            delta = 0.0

        # Adjust for difficulty level
        delta -= (self.difficulty_level - 3) * 0.3

        # Adjust for strictness
        if self.strictness == "scrupoloso":
            delta -= 0.5
        elif self.strictness == "amichevole":
            delta += 0.5

        # Update and clamp score
        new_score = max(0.0, min(10.0, curr_score + delta))
        scores[topic] = new_score

        new_state.variables["topics_scores"] = scores
        new_state.variables["current_topic"] = topic

        return new_state

    def reward_fn(self, state: State) -> float:
        """
        Evaluate the utility of the exam state based on professor strictness.
        """
        scores = state.get("topics_scores", {})
        history = state.get("history", [])

        if not scores:
            return 0.0

        avg_score = sum(scores.values()) / len(scores)

        # 1. Friendly Professor
        # Goal: Help student pass and cover topics smoothly. Punishes trick questions.
        if self.strictness == "amichevole":
            # Reward higher scores
            reward = avg_score * 2.0
            # Bonus for hints given
            hints_count = sum(1 for q in history if q.get("style") == "hint")
            reward += hints_count * 1.5
            # Penalty for trick questions
            tricks_count = sum(1 for q in history if q.get("style") == "trick")
            reward -= tricks_count * 2.0
            # Coverage bonus (different topics)
            reward += len(scores) * 1.0
            return reward

        # 2. Strict/Demanding Professor
        # Goal: Find gaps in knowledge (adversarial red-teaming). Loves trick questions, hates hints.
        elif self.strictness == "scrupoloso":
            min_score = min(scores.values()) if scores else 10.0
            # High reward if we found a gap (a topic with a low score)
            reward = (10.0 - min_score) * 3.0
            # Bonus for trick questions
            tricks_count = sum(1 for q in history if q.get("style") == "trick")
            reward += tricks_count * 2.0
            # Penalty for hints
            hints_count = sum(1 for q in history if q.get("style") == "hint")
            reward -= hints_count * 3.0
            # Penalty if average score is too high (wants to challenge the student)
            reward -= avg_score * 0.5
            return reward

        # 3. Fair Professor (Default)
        # Goal: Balanced assessment, tests core topics evenly, penalizes high variance.
        else:
            # Reward coverage
            coverage_ratio = len(scores) / len(self.topics) if self.topics else 1.0
            reward = coverage_ratio * 10.0 + avg_score
            # Variance penalty (standard deviation check)
            if len(scores) > 1:
                variance = sum((s - avg_score) ** 2 for s in scores.values()) / len(
                    scores
                )
                reward -= (variance**0.5) * 1.5
            return reward

    def is_goal(self, state: State) -> bool:
        """
        Check if we reached the goal state (e.g. asked at least 3 topics or 4 questions).
        """
        history = state.get("history", [])
        scores = state.get("topics_scores", {})

        # Stop simulation if we have covered at least 3 topics or asked 4 questions
        return len(scores) >= 3 or len(history) >= 4

    async def select_next_question(
        self,
        current_scores: dict[str, float],
        question_history: list[dict[str, Any]],
        current_topic: str | None = None,
    ) -> dict[str, Any]:
        """
        Run MCTS search to determine the best next question parameters.

        Args:
            current_scores: Current topic scores.
            question_history: Past question parameters.
            current_topic: Optional current topic.

        Returns:
            Dict containing best action parameters (topic, style).
        """
        # Build initial state
        initial_state = State(
            name="initial_exam_state",
            variables={
                "topics_scores": current_scores.copy(),
                "history": question_history.copy(),
                "current_topic": current_topic,
            },
        )

        try:
            # Run simulation search
            result = await self.simulator.search(initial_state)

            best_action_info = None
            if result.best_path and result.best_path.actions:
                best_action = result.best_path.actions[0]
                best_action_info = {
                    "name": best_action.name,
                    "parameters": best_action.parameters,
                    "reward": result.best_path.total_reward,
                }

            # Log search to DebugTracker
            try:
                from .debug_tracker import DebugTracker

                DebugTracker.add_event(
                    "mcts_search",
                    {
                        "topics": self.topics,
                        "initial_state": initial_state.variables,
                        "best_action": best_action_info,
                        "iterations": result.iterations,
                        "computation_time_ms": result.computation_time * 1000,
                        "success": result.success,
                        "goal_reached": result.goal_reached,
                        "explored_paths": [
                            {
                                "actions": [
                                    {"name": a.name, "parameters": a.parameters}
                                    for a in path.actions
                                ],
                                "total_reward": path.total_reward,
                                "probability": path.probability,
                            }
                            for path in result.all_paths
                        ],
                        "tree_nodes": result.metadata.get("children", [])
                        if result.metadata
                        else [],
                    },
                )
            except Exception as d_err:
                logger.error(f"Failed to log debug event for MCTS: {d_err}")

            if result.best_path and result.best_path.actions:
                best_action = result.best_path.actions[0]
                logger.info(
                    "mcts_question_selected",
                    name=best_action.name,
                    params=best_action.parameters,
                )
                return best_action.parameters
        except Exception as e:
            logger.error(f"Error during MCTS questioning search: {e}")

        # Fallback: Pick a random topic and style
        available_topics = [t for t in self.topics if t not in current_scores]
        if not available_topics:
            available_topics = self.topics

        fallback_topic = (
            random.choice(available_topics) if available_topics else "General"
        )  # nosec B311
        fallback_style = "theory" if self.strictness == "amichevole" else "application"
        return {"topic": fallback_topic, "style": fallback_style}
