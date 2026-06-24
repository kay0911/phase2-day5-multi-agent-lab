"""Analyst agent implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self) -> None:
        self.llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        if not state.research_notes:
            state.analysis_notes = "No research notes available to analyze."
            return state

        system_prompt = (
            "You are an expert systems analyst. Your task is to review research notes, "
            "extract key claims, identify underlying assumptions, compare viewpoints, "
            "and explicitly flag any weak evidence, missing details, or information gaps."
        )

        user_prompt = (
            f"User Query: {state.request.query}\n\n"
            f"Research Notes:\n{state.research_notes}\n\n"
            f"Please structure your analysis with headers:\n"
            f"- Key Claims & Evidence\n"
            f"- Viewpoints Comparison (if applicable)\n"
            f"- Missing Information & Weak Evidence"
        )

        analysis_res = self.llm.complete(system_prompt, user_prompt)
        state.analysis_notes = analysis_res.content
        state.add_trace_event("analyst_run", {
            "has_research_notes": bool(state.research_notes)
        })

        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=analysis_res.content,
                metadata={}
            )
        )

        return state

