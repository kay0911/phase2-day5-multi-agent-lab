"""Command-line entrypoint for the lab starter."""

import os
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline using Gemini."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)

    llm = LLMClient()
    system_prompt = (
        f"You are a professional research assistant. Your audience is {request.audience}. "
        "Provide a comprehensive, clear, and well-structured answer. "
        "Use markdown formatting and cite sources if applicable."
    )
    user_prompt = f"User Request: {query}"

    console.print("[blue]Running Single-Agent Baseline...[/blue]")
    res = llm.complete(system_prompt, user_prompt)

    state.final_answer = res.content
    console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    try:
        result = workflow.run(state)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Compare baseline and multi-agent performance and generate benchmark report."""
    _init()

    from multi_agent_research_lab.evaluation.benchmark import run_benchmark
    from multi_agent_research_lab.evaluation.report import render_markdown_report, render_html_report

    console.print(Panel.fit(f"Query: {query}", title="Starting Benchmark Comparison"))

    # 1. Run Baseline
    def run_baseline_fn(q: str) -> ResearchState:
        request = ResearchQuery(query=q)
        state = ResearchState(request=request)
        llm = LLMClient()
        system_prompt = "You are a professional research assistant. Answer the query comprehensively."
        res = llm.complete(system_prompt, f"User Request: {q}")
        state.final_answer = res.content
        return state

    console.print("[yellow]Running Baseline...[/yellow]")
    baseline_state, baseline_metrics = run_benchmark("Single-Agent Baseline", query, run_baseline_fn)

    # 2. Run Multi-Agent
    def run_multi_agent_fn(q: str) -> ResearchState:
        state = ResearchState(request=ResearchQuery(query=q))
        workflow = MultiAgentWorkflow()
        return workflow.run(state)

    console.print("[yellow]Running Multi-Agent Workflow...[/yellow]")
    multi_state, multi_metrics = run_benchmark("Multi-Agent Workflow", query, run_multi_agent_fn)

    # Enrich metrics with notes/cost if available
    baseline_metrics.notes = "Direct LLM prompt completion."
    multi_metrics.notes = f"LangGraph execution with {multi_state.iteration} iterations."

    # Save markdown report
    report_md = render_markdown_report([baseline_metrics, multi_metrics], baseline_state, multi_state)
    os.makedirs("reports", exist_ok=True)
    report_path = "reports/benchmark_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # Save HTML report
    report_html = render_html_report([baseline_metrics, multi_metrics], baseline_state, multi_state)
    html_path = "reports/benchmark_report.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(report_html)

    console.print(Panel.fit(f"Saved benchmark reports to:\n- {report_path}\n- {html_path}", title="Benchmark Completed", style="green"))


if __name__ == "__main__":
    app()

