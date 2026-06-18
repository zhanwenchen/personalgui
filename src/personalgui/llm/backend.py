"""LLM backend protocol + an OpenAI-compatible HTTP backend + a scripted backend for tests.

The OpenAI-compatible backend works with vLLM, llama.cpp server, sglang, LM Studio, or any
other server that speaks /v1/chat/completions with native tool_calls. Bring your own model
and base_url.

The scripted backend returns canned tool calls in order. Tests use it; CI does not need a
running LLM server.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class BackendResponse:
    tool_calls: list[ToolCall]
    raw_assistant_message: dict[str, Any]  # OpenAI-shaped message dict; appended back into history verbatim


class LLMBackend(Protocol):
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> BackendResponse: ...


class OpenAICompatBackend:
    """Talks to an OpenAI-compatible HTTP endpoint (e.g. vLLM, llama.cpp, Ollama compat).

    Args:
        model: name registered on the server (e.g. "qwen3.5-4b").
        base_url: full base URL ending in /v1 (e.g. "http://localhost:8000/v1").
        api_key: optional; many local servers don't validate it. Defaults to "EMPTY".
        temperature: sampling temperature. Lower is more deterministic.
        timeout: per-request timeout in seconds.
    """

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.0,
        timeout: float = 60.0,
    ) -> None:
        try:
            import openai
        except ImportError as e:
            raise ImportError(
                "OpenAICompatBackend requires the `openai` package. "
                "Install with: pip install 'personalgui[llm]'"
            ) from e

        self.model = model or os.environ.get("PERSONALGUI_LLM_MODEL", "qwen3.5-4b")
        self.base_url = base_url or os.environ.get("PERSONALGUI_LLM_BASE_URL", "http://localhost:8000/v1")
        self.temperature = temperature
        self._client = openai.OpenAI(
            base_url=self.base_url,
            api_key=api_key or os.environ.get("PERSONALGUI_LLM_API_KEY", "EMPTY"),
            timeout=timeout,
        )

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> BackendResponse:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            tools=tools,  # type: ignore[arg-type]
            tool_choice="auto",
            temperature=self.temperature,
        )
        choice = response.choices[0]
        msg = choice.message

        tool_calls: list[ToolCall] = []
        raw_calls: list[dict[str, Any]] = []
        for tc in msg.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))
            raw_calls.append(
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"},
                }
            )

        raw_assistant_message: dict[str, Any] = {"role": "assistant", "content": msg.content}
        if raw_calls:
            raw_assistant_message["tool_calls"] = raw_calls

        return BackendResponse(tool_calls=tool_calls, raw_assistant_message=raw_assistant_message)


@dataclass
class ScriptedToolCall:
    name: str
    arguments: dict[str, Any]


class ScriptedBackend:
    """Returns pre-baked tool calls in order. Used in tests to make LLMAgent deterministic."""

    def __init__(self, plan: list[ScriptedToolCall]) -> None:
        self._plan = list(plan)
        self._idx = 0
        self.received_messages: list[list[dict[str, Any]]] = []
        self.received_tools: list[list[dict[str, Any]]] = []

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> BackendResponse:
        if self._idx >= len(self._plan):
            raise RuntimeError(f"ScriptedBackend exhausted at idx={self._idx}; plan had {len(self._plan)} calls")
        step = self._plan[self._idx]
        self._idx += 1
        self.received_messages.append([dict(m) for m in messages])
        self.received_tools.append(list(tools))

        call_id = f"call_{uuid.uuid4().hex[:8]}"
        return BackendResponse(
            tool_calls=[ToolCall(id=call_id, name=step.name, arguments=step.arguments)],
            raw_assistant_message={
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {"name": step.name, "arguments": json.dumps(step.arguments)},
                    }
                ],
            },
        )
