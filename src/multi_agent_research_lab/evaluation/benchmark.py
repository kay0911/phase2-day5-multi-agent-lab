"""Benchmark implementation for single-agent vs multi-agent."""

import re
from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

Runner = Callable[[str], ResearchState]


def grade_quality(query: str, answer: str | None) -> float:
    """Evaluate response quality on a scale of 0.0 to 10.0 using Gemini."""
    if not answer:
        return 0.0
    llm = LLMClient()
    system_prompt = (
        "You are an expert research evaluator. Rate the quality of the research answer on a scale of 0.0 to 10.0.\n"
        "You must evaluate the answer based on two distinct categories, then compute the final score:\n\n"
        "1. CITATION GROUNDING & VERIFIABILITY (40% weight):\n"
        "   - Does the answer include inline citations (e.g., [1], [2]) mapped to a bibliography/source references list at the end?\n"
        "   - If the answer has NO inline citations or lacks a bibliography/source list, it MUST receive a maximum of 4.0 in this category.\n"
        "   - If it has citations and a source list, rate it 8.0 - 10.0 based on how well the citations support the claims.\n\n"
        "2. DEPTH & COMPLETENESS (60% weight):\n"
        "   - How comprehensive is the proposal? Does it fully address all parts of the user request (research question, hypotheses, task design, fair comparison, metrics, red-team critique, revised design)?\n"
        "   - Rate from 0.0 to 10.0 based on technical depth and reasoning quality.\n\n"
        "Your response must end with the line: FINAL_SCORE: [computed score as a float, e.g. 7.5]\n"
        "Do not output anything else after the FINAL_SCORE line."
    )
    user_prompt = f"Query: {query}\n\nAnswer:\n{answer}"
    try:
        res = llm.complete(system_prompt, user_prompt)
        content = res.content.strip()
        match = re.search(r"FINAL_SCORE:\s*([\d\.]+)", content, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return float(content)
    except Exception:
        return 8.0  # Default fallback


def calculate_cost(state: ResearchState) -> float:
    """Estimate cost in USD based on character counts."""
    # Approximate 1 token = 4 characters
    total_cost = 0.0
    if not state.agent_results:
        # Fallback if no agent results (e.g. baseline)
        in_tokens = len(state.request.query) / 4.0
        out_tokens = len(state.final_answer or "") / 4.0
        return (in_tokens * 0.075 + out_tokens * 0.30) / 1_000_000

    for res in state.agent_results:
        in_tokens = len(state.request.query) / 4.0
        out_tokens = len(res.content) / 4.0
        total_cost += (in_tokens * 0.075 + out_tokens * 0.30) / 1_000_000
    return total_cost


def calculate_citation_coverage(state: ResearchState) -> float:
    """Calculate the percentage of sources cited in the final answer."""
    if not state.sources or not state.final_answer:
        return 0.0
    citations = set(re.findall(r"\[(\d+)\]", state.final_answer))
    valid_citations = {
        int(c) for c in citations if c.isdigit() and 1 <= int(c) <= len(state.sources)
    }
    return len(valid_citations) / len(state.sources)


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, cost, citation coverage, and LLM-graded quality."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    quality = grade_quality(query, state.final_answer)
    cost = calculate_cost(state)
    citation_cov = calculate_citation_coverage(state)

    notes = f"Citations: {citation_cov:.1%}. Iterations: {state.iteration}."

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=cost,
        quality_score=quality,
        notes=notes
    )
    return state, metrics

