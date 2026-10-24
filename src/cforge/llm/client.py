"""Enterprise LLM Client supporting Google Gemini and Anthropic Claude with JSON-Schema validation and Disk Cache."""

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from cforge.config import PROJECT_ROOT
from cforge.llm.cache import LLMDiskCache

T = TypeVar("T", bound=BaseModel)

# Model pricing in USD per 1,000,000 tokens
MODEL_PRICING = {
    # Google Gemini Models (Fast, high-quality, economical)
    "gemini-3.5-flash-lite": {"input": 0.075, "output": 0.30},
    "gemini-3.1-flash-lite": {"input": 0.075, "output": 0.30},
    "gemini-2.5-flash-lite": {"input": 0.075, "output": 0.30},
    "gemini-flash-lite-latest": {"input": 0.075, "output": 0.30},
    "gemini-3.8-flash": {"input": 0.15, "output": 0.60},
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    # Anthropic Claude Models
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    # OpenAI Models
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}
DEFAULT_MODEL = "gemini-3.1-flash-lite"


class LLMAuthenticationError(Exception):
    """Raised when an LLM API call is attempted without configured credentials."""


@dataclass
class StructuredLLMResponse(Generic[T]):
    parsed: T
    raw_text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    cached: bool
    model: str


@dataclass
class TextLLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    cached: bool
    model: str


def extract_json_from_text(text: str) -> dict[str, Any]:
    """Extract and parse JSON object from raw LLM text output."""
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    
    if not (text.startswith("{") and text.endswith("}")):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

    return json.loads(text)


class LLMClient:
    """Unified LLM Client providing JSON-schema validation, token accounting, and disk caching."""

    def __init__(self, model_name: str | None = None, cache_path: Path | None = None):
        self.cache = LLMDiskCache(cache_path)
        self._gemini_client = None
        self._anthropic_client = None

        gemini_key = self._get_key("GEMINI_API_KEY") or self._get_key("GOOGLE_API_KEY")
        anthropic_key = self._get_key("ANTHROPIC_API_KEY")
        configured_model = self._get_key("CFORGE_LLM_MODEL")

        if model_name:
            self.model = model_name
        elif configured_model:
            self.model = configured_model
        elif gemini_key:
            self.model = "gemini-3.1-flash-lite"
        elif anthropic_key:
            self.model = "claude-3-5-haiku-20241022"
        else:
            self.model = DEFAULT_MODEL

    def _get_key(self, var_name: str) -> str | None:
        # Check environment
        val = os.getenv(var_name)
        if val:
            return val
        
        # Check .env files
        env_files = [PROJECT_ROOT / ".env", Path.home() / ".env"]
        for env_path in env_files:
            if env_path.exists():
                try:
                    for line in env_path.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line.startswith(f"{var_name}="):
                            v = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if v:
                                return v
                except Exception:
                    pass
        return None

    def _get_gemini_client(self):
        if self._gemini_client is None:
            key = self._get_key("GEMINI_API_KEY") or self._get_key("GOOGLE_API_KEY")
            if not key:
                raise LLMAuthenticationError(
                    "GEMINI_API_KEY (or GOOGLE_API_KEY) is not set. Please set the GEMINI_API_KEY "
                    "environment variable or add it to your .env file."
                )
            from google import genai
            from google.genai import types
            self._gemini_client = genai.Client(
                api_key=key,
                http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(attempts=1),
                    timeout=15000
                )
            )
        return self._gemini_client

    def _get_anthropic_client(self):
        if self._anthropic_client is None:
            key = self._get_key("ANTHROPIC_API_KEY")
            if not key:
                raise LLMAuthenticationError(
                    "ANTHROPIC_API_KEY is not set. Please set ANTHROPIC_API_KEY in your .env file."
                )
            import anthropic
            self._anthropic_client = anthropic.Anthropic(api_key=key)
        return self._anthropic_client

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Compute exact USD cost based on published model token rates."""
        rates = MODEL_PRICING.get(model, MODEL_PRICING[DEFAULT_MODEL])
        input_cost = (input_tokens / 1_000_000.0) * rates["input"]
        output_cost = (output_tokens / 1_000_000.0) * rates["output"]
        return round(input_cost + output_cost, 6)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        model: str | None = None
    ) -> StructuredLLMResponse[T]:
        """Generate structured data strictly validated against a Pydantic schema."""
        target_model = model or self.model
        schema = response_model.model_json_schema()
        cache_key = LLMDiskCache.compute_key(target_model, system_prompt, user_prompt, schema)

        # 1. Check persistent disk cache
        cached = self.cache.get(cache_key)
        if cached is not None and cached.parsed_json is not None:
            try:
                parsed_obj = response_model.model_validate(cached.parsed_json)
                return StructuredLLMResponse(
                    parsed=parsed_obj,
                    raw_text=cached.response_text,
                    input_tokens=cached.input_tokens,
                    output_tokens=cached.output_tokens,
                    latency_ms=cached.latency_ms,
                    cost_usd=cached.cost_usd,
                    cached=True,
                    model=cached.model
                )
            except ValidationError:
                pass

        # 2. Live API Execution
        t0 = time.perf_counter()

        try:
            if target_model.startswith("gemini") or "gemini" in target_model or (not self._get_key("ANTHROPIC_API_KEY") and (self._get_key("GEMINI_API_KEY") or self._get_key("GOOGLE_API_KEY"))):
                gemini_client = self._get_gemini_client()
                from google.genai import types

                max_attempts = 4
                response = None
                for attempt in range(max_attempts):
                    try:
                        response = gemini_client.models.generate_content(
                            model=target_model,
                            contents=user_prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                response_mime_type="application/json",
                                response_schema=response_model,
                                temperature=0.0
                            )
                        )
                        break
                    except Exception as exc:
                        if ("429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)) and attempt < max_attempts - 1:
                            time.sleep(25.0)
                        else:
                            raise
                latency_ms = (time.perf_counter() - t0) * 1000.0
                raw_text = response.text
                input_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else len(user_prompt) // 4
                output_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else len(raw_text) // 4

            else:
                client = self._get_anthropic_client()
                schema_json_str = json.dumps(schema, indent=2)
                system_instruction = (
                    f"{system_prompt}\n\n"
                    f"CRITICAL: You MUST respond ONLY with a single valid JSON object strictly conforming to the following JSON Schema. "
                    f"Do not include any text before or after the JSON.\n\n"
                    f"JSON Schema:\n{schema_json_str}"
                )
                response = client.messages.create(
                    model=target_model,
                    max_tokens=4096,
                    temperature=0.0,
                    system=system_instruction,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0
                raw_text = response.content[0].text
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens

            cost_usd = self.calculate_cost(target_model, input_tokens, output_tokens)
            parsed_json = extract_json_from_text(raw_text)
            parsed_obj = response_model.model_validate(parsed_json)

            # Store in disk cache
            self.cache.set(
                cache_key=cache_key,
                model=target_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_text=raw_text,
                parsed_json=parsed_json,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd
            )

            return StructuredLLMResponse(
                parsed=parsed_obj,
                raw_text=raw_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                cached=False,
                model=target_model
            )
        except Exception:
            raise

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None
    ) -> TextLLMResponse:
        """Generate text/SQL response with real token and cost accounting."""
        target_model = model or self.model
        cache_key = LLMDiskCache.compute_key(target_model, system_prompt, user_prompt, None)

        cached = self.cache.get(cache_key)
        if cached is not None:
            return TextLLMResponse(
                text=cached.response_text,
                input_tokens=cached.input_tokens,
                output_tokens=cached.output_tokens,
                latency_ms=cached.latency_ms,
                cost_usd=cached.cost_usd,
                cached=True,
                model=cached.model
            )

        t0 = time.perf_counter()

        try:
            if target_model.startswith("gemini") or "gemini" in target_model or (not self._get_key("ANTHROPIC_API_KEY") and (self._get_key("GEMINI_API_KEY") or self._get_key("GOOGLE_API_KEY"))):
                gemini_client = self._get_gemini_client()
                from google.genai import types

                max_attempts = 4
                response = None
                for attempt in range(max_attempts):
                    try:
                        response = gemini_client.models.generate_content(
                            model=target_model,
                            contents=user_prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                temperature=0.0
                            )
                        )
                        break
                    except Exception as exc:
                        if ("429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)) and attempt < max_attempts - 1:
                            time.sleep(25.0)
                        else:
                            raise
                latency_ms = (time.perf_counter() - t0) * 1000.0
                raw_text = response.text
                input_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else len(user_prompt) // 4
                output_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else len(raw_text) // 4

            else:
                client = self._get_anthropic_client()
                response = client.messages.create(
                    model=target_model,
                    max_tokens=2048,
                    temperature=0.0,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0
                raw_text = response.content[0].text
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens

            cost_usd = self.calculate_cost(target_model, input_tokens, output_tokens)

            self.cache.set(
                cache_key=cache_key,
                model=target_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_text=raw_text,
                parsed_json=None,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd
            )

            return TextLLMResponse(
                text=raw_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                cached=False,
                model=target_model
            )
        except Exception:
            raise
