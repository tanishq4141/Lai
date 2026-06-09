"""
LLM client abstraction for Gemini 3.5 Flash.
Provides structured output (JSON schema) and text generation capabilities.
"""

import json
import os
from typing import Any

from google import genai
from google.genai import types


def _get_client() -> genai.Client:
    """Get a configured Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    return genai.Client(api_key=api_key)


def _get_model() -> str:
    """Get the configured model name."""
    return os.getenv("GEMINI_MODEL", "gemini-3.5-flash")


async def generate_text(
    prompt: str,
    system_instruction: str | None = None,
    temperature: float = 0.3,
) -> str:
    """Generate text from a prompt using Gemini.

    Args:
        prompt: The user prompt.
        system_instruction: Optional system instruction.
        temperature: Sampling temperature (lower = more deterministic).

    Returns:
        The generated text response.
    """
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
    )
    if system_instruction:
        config.system_instruction = system_instruction

    response = client.models.generate_content(
        model=_get_model(),
        contents=prompt,
        config=config,
    )
    return response.text or ""


async def generate_json(
    prompt: str,
    schema: dict[str, Any],
    system_instruction: str | None = None,
    temperature: float = 0.2,
) -> dict | list:
    """Generate structured JSON output from a prompt using Gemini.

    Uses Gemini's native JSON schema support for reliable structured extraction.

    Args:
        prompt: The user prompt.
        schema: JSON schema defining the expected output structure.
        system_instruction: Optional system instruction.
        temperature: Sampling temperature.

    Returns:
        Parsed JSON object (dict or list).
    """
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json",
        response_schema=schema,
    )
    if system_instruction:
        config.system_instruction = system_instruction

    response = client.models.generate_content(
        model=_get_model(),
        contents=prompt,
        config=config,
    )
    text = response.text or "{}"
    return json.loads(text)


async def generate_with_thinking(
    prompt: str,
    system_instruction: str | None = None,
    temperature: float = 0.3,
) -> str:
    """Generate text with thinking/reasoning enabled.

    Useful for complex legal analysis where chain-of-thought improves quality.

    Args:
        prompt: The user prompt.
        system_instruction: Optional system instruction.
        temperature: Sampling temperature.

    Returns:
        The generated text response (thinking content is internal).
    """
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        thinking_config=types.ThinkingConfig(
            thinking_budget=2048,
        ),
    )
    if system_instruction:
        config.system_instruction = system_instruction

    response = client.models.generate_content(
        model=_get_model(),
        contents=prompt,
        config=config,
    )
    return response.text or ""
