"""Supervisor / router implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.core.config import get_settings


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self) -> None:
        self.llm = LLMClient()
        self.settings = get_settings()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        # 1. Enforce max iterations
        if state.iteration >= self.settings.max_iterations:
            state.record_route("done")
            state.add_trace_event("supervisor_max_iterations", {"next": "done"})
            return state

        # 2. Build orchestrator prompt
        system_prompt = (
            "You are the orchestrator (Supervisor) of a multi-agent research team.\n"
            "Your team consists of:\n"
            "- researcher: finds information and collects sources (runs first if information is missing).\n"
            "- analyst: analyzes notes, compares views, highlights gaps (runs after researcher).\n"
            "- writer: writes or revises the final comprehensive response (runs after analyst or critic feedback).\n"
            "- critic: reviews the final answer written by the writer, checking for accuracy and citation compliance (runs after writer).\n"
            "- done: choose this ONLY when the final answer is successfully produced, fully reviewed, and accepted by the critic.\n\n"
            "Your task is to inspect the current state and choose the next action.\n"
            "Respond ONLY with one of the following exact words:\n"
            "researcher\n"
            "analyst\n"
            "writer\n"
            "critic\n"
            "done"
        )

        user_prompt = (
            f"User Query: {state.request.query}\n\n"
            f"Current state:\n"
            f"- Iteration: {state.iteration}\n"
            f"- Route History: {state.route_history}\n"
            f"- Research notes present: {bool(state.research_notes)}\n"
            f"- Analysis notes present: {bool(state.analysis_notes)}\n"
            f"- Final answer present: {bool(state.final_answer)}\n"
            f"- Unresolved critique present: {bool(state.critique)}\n"
            f"- Revision count: {state.revision_count}\n\n"
            f"Please output the single next role word."
        )

        llm_res = self.llm.complete(system_prompt, user_prompt)
        next_step = llm_res.content.strip().lower()

        # Validation: check if it returned a valid route
        valid_routes = ["researcher", "analyst", "writer", "critic", "done"]
        if next_step not in valid_routes:
            # Fallback heuristic logic if LLM hallucinates the output format
            if not state.research_notes:
                next_step = "researcher"
            elif not state.analysis_notes:
                next_step = "analyst"
            elif not state.final_answer:
                next_step = "writer"
            elif state.critique:
                next_step = "writer"
            else:
                next_step = "done"

        state.record_route(next_step)
        state.add_trace_event("supervisor_decision", {"next": next_step})

        state.agent_results.append(
            AgentResult(
                agent=AgentName.SUPERVISOR,
                content=f"Decided to route to: {next_step}",
                metadata={"next_step": next_step}
            )
        )

        return state

