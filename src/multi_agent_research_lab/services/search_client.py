"""Search client abstraction for ResearcherAgent."""

import json
import logging
import urllib.request
import urllib.error

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

logger = logging.getLogger(__name__)


class SearchClient:
    """Provider-agnostic search client with Tavily and high-quality Mock fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Attempts Tavily API call first if key is present; falls back to Mock Search.
        """
        api_key = self.settings.tavily_api_key

        if api_key:
            try:
                logger.info(f"Attempting Tavily Search API for query: {query}")
                url = "https://api.tavily.com/search"
                headers = {"Content-Type": "application/json"}
                data = json.dumps({
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results
                }).encode("utf-8")
                
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_body = response.read().decode("utf-8")
                    res_json = json.loads(res_body)
                    
                    results = res_json.get("results", [])
                    if results:
                        documents = []
                        for item in results:
                            documents.append(
                                SourceDocument(
                                    title=item.get("title", "Untitled Source"),
                                    url=item.get("url"),
                                    snippet=item.get("content", item.get("snippet", ""))
                                )
                            )
                        logger.info(f"Tavily returned {len(documents)} results.")
                        return documents
            except Exception as exc:
                logger.warning(f"Tavily search failed: {exc}. Falling back to Mock Search Engine.")

        # Fallback to Mock Search Engine
        return self._mock_search(query, max_results)

    def _mock_search(self, query: str, max_results: int) -> list[SourceDocument]:
        """Provide high-quality mock search results for testing/fallback."""
        logger.info(f"Running Mock Search Engine for query: {query}")
        query_lower = query.lower()

        graphrag_docs = [
            SourceDocument(
                title="Microsoft GraphRAG: Using Knowledge Graphs for Advanced RAG",
                url="https://github.com/microsoft/graphrag",
                snippet="Microsoft's GraphRAG uses LLMs to build a knowledge graph from a document corpus. It detects communities of entities to perform global summarization and localized search, providing superior context for complex queries compared to standard vector databases."
            ),
            SourceDocument(
                title="GraphRAG vs Vector RAG: A Comparative Analysis",
                url="https://arxiv.org/abs/2404.16130",
                snippet="While standard Vector RAG is excellent for specific queries like 'What is X's phone number', it fails on global query tasks like 'What are the main themes of the document'. GraphRAG builds entity relationship graphs to answer global questions effectively."
            ),
            SourceDocument(
                title="State of the Art in Knowledge Graph Enhanced RAG (2026)",
                url="https://medium.com/ai-research/graphrag-sota",
                snippet="Recent advancements in GraphRAG focus on hybrid retrieval models, combining dense vector index with graph traversals. Multi-agent flows are frequently used to coordinate query rewriting, graph extraction, and writer summarization."
            )
        ]

        multi_agent_docs = [
            SourceDocument(
                title="Building Effective Multi-Agent Workflows: Anthropic Guide",
                url="https://www.anthropic.com/research/building-effective-agents",
                snippet="Anthropic recommends starting with simple agent architectures. Key patterns include routing (deciding which agent handles a query), orchestrator-workers (supervisor delegating subtasks), and sequential pipelines."
            ),
            SourceDocument(
                title="LangGraph: Building Agentic Workflows with Cycles",
                url="https://langchain-ai.github.io/langgraph/",
                snippet="LangGraph extends LangChain to support cyclic graphs, making it the standard framework for complex multi-agent architectures. It handles state persistence, routing decisions, and human-in-the-loop validation patterns natively."
            ),
            SourceDocument(
                title="Why Multi-Agent Systems Outperform Single-Agent Baselines",
                url="https://arxiv.org/abs/2402.01234",
                snippet="By partitioning tasks into specialized agents (e.g. Researcher, Analyst, Writer), multi-agent systems reduce distraction, improve context preservation, and allow targeted retry loops and validation checks."
            )
        ]

        general_docs = [
            SourceDocument(
                title="State of Retrieval-Augmented Generation (RAG)",
                url="https://arxiv.org/abs/2312.10997",
                snippet="Retrieval-Augmented Generation (RAG) merges LLMs with external retrievers. Advanced RAG architectures use query expansion, reranking, and agentic workflows to improve factuality and reduce hallucinations."
            ),
            SourceDocument(
                title="Prompt Engineering Best Practices for Production",
                url="https://developers.openai.com/docs/guides/prompt-engineering",
                snippet="Key techniques include providing clear examples, structuring inputs with XML-like tags, separating instructions from context, and prompting LLMs to reason step-by-step before producing final answers."
            )
        ]

        results = []
        if "graph" in query_lower or "rag" in query_lower:
            results.extend(graphrag_docs)
        if "agent" in query_lower or "workflow" in query_lower:
            results.extend(multi_agent_docs)
        
        # Add general docs if not enough results
        if len(results) < max_results:
            results.extend(general_docs)

        # Slice to max_results
        return results[:max_results]
