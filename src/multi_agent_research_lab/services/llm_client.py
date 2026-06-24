"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
import logging
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client using Google Gemini via OpenAI SDK."""

    def __init__(self) -> None:
        self.settings = get_settings()
        api_key = self.settings.gemini_api_key or self.settings.openai_api_key
        base_url = self.settings.gemini_base_url
        self.client = OpenAI(
            api_key=api_key or "mock-key",
            base_url=base_url
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _call_api(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        response = self.client.chat.completions.create(
            model=self.settings.gemini_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            timeout=float(self.settings.timeout_seconds),
        )
        content = response.choices[0].message.content or ""
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
        return content, input_tokens, output_tokens

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Connects to Google Gemini via OpenAI SDK compatibility.
        """
        try:
            content, input_tokens, output_tokens = self._call_api(system_prompt, user_prompt)
            # Cost calculation: Gemini 1.5/3.1 flash-lite models: $0.075/1M input, $0.30/1M output tokens
            cost_usd = (input_tokens * 0.075 + output_tokens * 0.30) / 1_000_000
            return LLMResponse(
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd
            )
        except Exception as exc:
            logger.error(f"Failed to get LLM response: {exc}")
            raise

