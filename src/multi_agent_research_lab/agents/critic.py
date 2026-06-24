"""Critic agent implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class CriticAgent(BaseAgent):
    """Fact-checking, relevance, and formatting review agent."""

    name = "critic"

    def __init__(self) -> None:
        self.llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and decide whether to accept or request revision."""
        if not state.final_answer:
            state.critique = "No answer was generated yet."
            state.add_trace_event("critic_run", {"verdict": "REVISE", "critique": state.critique})
            return state

        # Prompt critic to review the answer
        system_prompt = (
            "You are a strict and critical research reviewer. Evaluate the provided final answer against the user's query.\n"
            "Identify any gaps, logical errors, formatting errors, or issues with citations. You must decide whether "
            "to ACCEPT the answer or request a REVISION.\n\n"
            "Your output must follow this exact format:\n"
            "VERDICT: [Either ACCEPT or REVISE]\n"
            "CRITIQUE: [Detailed critique if REVISE, empty if ACCEPT]"
        )

        user_prompt = (
            f"User Query: {state.request.query}\n\n"
            f"Final Answer Draft:\n{state.final_answer}\n\n"
            "Evaluate and respond with the exact VERDICT and CRITIQUE template."
        )

        llm_res = self.llm.complete(system_prompt, user_prompt)
        content = llm_res.content.strip()

        # Parse verdict and critique
        content_upper = content.upper()
        verdict = "ACCEPT"
        critique = ""

        verdict_idx = content_upper.find("VERDICT:")
        critique_idx = content_upper.find("CRITIQUE:")

        if verdict_idx != -1:
            start_verdict = verdict_idx + len("VERDICT:")
            end_verdict = critique_idx if (critique_idx != -1 and critique_idx > verdict_idx) else len(content)
            verdict = content[start_verdict:end_verdict].strip().upper()

        if critique_idx != -1:
            critique = content[critique_idx + len("CRITIQUE:"):].strip()

        # Sanitize verdict
        if "REVISE" in verdict:
            verdict = "REVISE"
        else:
            verdict = "ACCEPT"

        if verdict == "REVISE":
            state.critique = critique or "Please revise the draft to make it more comprehensive and address the prompt."
            state.revision_count += 1
        else:
            state.critique = None # accepted

        state.add_trace_event("critic_run", {
            "verdict": verdict,
            "critique": state.critique,
            "revision_count": state.revision_count
        })

        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=f"Verdict: {verdict}. Critique: {state.critique or 'None'}",
                metadata={"verdict": verdict, "revision_count": state.revision_count}
            )
        )

        return state
