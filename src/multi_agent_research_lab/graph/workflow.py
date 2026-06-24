"""LangGraph workflow implementation."""

from langgraph.graph import StateGraph, END
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.agents.critic import CriticAgent


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Orchestrates the routing and transitions between agents.
    """

    def __init__(self) -> None:
        self.supervisor = SupervisorAgent()
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        self.critic = CriticAgent()

    def build(self) -> object:
        """Create a compiled LangGraph application."""
        workflow = StateGraph(ResearchState)

        # Register nodes
        workflow.add_node("supervisor", lambda state: self.supervisor.run(state))
        workflow.add_node("researcher", lambda state: self.researcher.run(state))
        workflow.add_node("analyst", lambda state: self.analyst.run(state))
        workflow.add_node("writer", lambda state: self.writer.run(state))
        workflow.add_node("critic", lambda state: self.critic.run(state))

        # Set entry point
        workflow.set_entry_point("supervisor")

        # Define conditional routing from supervisor
        def route_next(state: ResearchState) -> str:
            if not state.route_history:
                return "supervisor"
            next_step = state.route_history[-1]
            if next_step == "done":
                return "done"
            return next_step

        # Add conditional edges
        workflow.add_conditional_edges(
            "supervisor",
            route_next,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "critic": "critic",
                "done": END
            }
        )

        # Worker agents route back to supervisor
        workflow.add_edge("researcher", "supervisor")
        workflow.add_edge("analyst", "supervisor")
        workflow.add_edge("writer", "supervisor")
        workflow.add_edge("critic", "supervisor")

        return workflow.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        app = self.build()
        # LangGraph invoke
        result = app.invoke(state)
        if isinstance(result, dict):
            return ResearchState(**result)
        return result

