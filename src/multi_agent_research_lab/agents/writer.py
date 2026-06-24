"""Writer agent implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self) -> None:
        self.llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        sources_text = "\n".join([
            f"[{i+1}] {s.title} ({s.url or 'No URL'})"
            for i, s in enumerate(state.sources)
        ])

        system_prompt = (
            f"You are a professional science and tech writer. Your audience is {state.request.audience}. "
            "Your task is to write a comprehensive, clear, and well-structured answer. "
            "You MUST integrate the research notes and analysis notes provided. "
            "You MUST include inline citations like [1] or [2] linking to the numbered sources list."
        )

        user_prompt = (
            f"User Query: {state.request.query}\n\n"
            f"Research Notes:\n{state.research_notes or 'None'}\n\n"
            f"Analysis Notes:\n{state.analysis_notes or 'None'}\n\n"
            f"Sources:\n{sources_text or 'None'}\n\n"
        )
        if state.critique:
            user_prompt += (
                f"Previous Answer Draft:\n{state.final_answer or 'None'}\n\n"
                f"Reviewer Critique/Feedback:\n{state.critique}\n\n"
                "Please revise the previous answer draft to fully address all the points in the reviewer critique above. "
                "Retain the overall structure and keep all inline citations."
            )
        else:
            user_prompt += "Please draft the final output in Markdown."

        writer_res = self.llm.complete(system_prompt, user_prompt)
        state.final_answer = writer_res.content
        state.add_trace_event("writer_run", {
            "has_sources": len(state.sources) > 0,
            "answer_len": len(writer_res.content)
        })

        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=writer_res.content,
                metadata={}
            )
        )

        return state

