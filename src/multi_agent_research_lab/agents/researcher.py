"""Researcher agent implementation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self) -> None:
        self.llm = LLMClient()
        self.search_client = SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        # 1. Generate search queries
        system_prompt = (
            "You are a researcher agent. Your task is to generate 1 or 2 search queries "
            "to find high-quality information answering the user's request. "
            "Respond ONLY with the search query strings, one per line. Do not include any other text."
        )
        user_prompt = f"User Request: {state.request.query}"
        llm_res = self.llm.complete(system_prompt, user_prompt)
        queries = [q.strip() for q in llm_res.content.split("\n") if q.strip()]

        if not queries:
            queries = [state.request.query]

        # 2. Search for documents
        all_sources = []
        for q in queries[:2]:
            sources = self.search_client.search(q, max_results=state.request.max_sources)
            all_sources.extend(sources)

        # De-duplicate by URL
        seen_urls = set()
        unique_sources = []
        for s in all_sources:
            url_key = s.url or s.title
            if url_key not in seen_urls:
                seen_urls.add(url_key)
                unique_sources.append(s)

        state.sources = unique_sources[:state.request.max_sources]

        # 3. Synthesize research notes
        sources_text = "\n\n".join([
            f"Source Title: {s.title}\nURL: {s.url}\nContent: {s.snippet}"
            for s in state.sources
        ])

        notes_prompt = (
            f"Based on the following source documents, compile concise research notes "
            f"relevant to answering: '{state.request.query}'. "
            f"Focus on extracting key facts, data points, entity definitions, and citations. "
            f"Be objective and do not perform deep analysis yet.\n\n"
            f"Sources:\n{sources_text}"
        )

        notes_res = self.llm.complete(
            "You are a professional research agent. Synthesize facts objectively from sources.",
            notes_prompt
        )

        state.research_notes = notes_res.content
        state.add_trace_event("researcher_run", {
            "queries": queries,
            "sources_found": len(state.sources)
        })

        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=notes_res.content,
                metadata={"sources": [s.model_dump() for s in state.sources]}
            )
        )

        return state

