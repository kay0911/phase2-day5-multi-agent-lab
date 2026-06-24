"""Tracing hooks with optional Langfuse integration and JSON logging."""

from collections.abc import Iterator
from contextlib import contextmanager
import json
import logging
import os
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger("multi_agent_research_lab.trace")

# Optional Langfuse import
try:
    from langfuse import Langfuse
    settings = get_settings()
    if settings.langfuse_secret_key and settings.langfuse_public_key:
        langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host or "https://cloud.langfuse.com"
        )
    else:
        langfuse_client = None
except ImportError:
    langfuse_client = None


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Span context that logs JSON traces locally and sends telemetry to Langfuse if available."""
    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "duration_seconds": None
    }
    
    lf_span = None
    if langfuse_client:
        try:
            lf_span = langfuse_client.span(
                name=name,
                metadata=attributes
            )
        except Exception:
            pass

    try:
        yield span
    finally:
        duration = perf_counter() - started
        span["duration_seconds"] = duration
        
        # Log trace span as JSON
        log_data = {
            "event": "trace_span",
            "name": name,
            "duration_seconds": round(duration, 4),
            "attributes": span["attributes"]
        }
        logger.info(json.dumps(log_data))

        # Write to JSONL file
        try:
            os.makedirs("reports", exist_ok=True)
            with open("reports/trace_log.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except Exception:
            pass

        # Optional: End Langfuse span
        if lf_span:
            try:
                lf_span.end(
                    metadata={"duration_seconds": duration}
                )
            except Exception:
                pass

