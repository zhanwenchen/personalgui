"""LLMAgent: drives an OpenAI-compatible LLM through a tool-calling loop.

Conversation layout (one act() call = one model turn):
    [system, user(initial)]                       -> assistant(tool_call_0)
    + tool(result_0), user(observation_1)         -> assistant(tool_call_1)
    + tool(result_1), user(observation_2)         -> assistant(tool_call_2)
    ...

The harness calls act() once per step. We replay the next observation + previous event
into the message list, call the backend, and translate the returned tool call into an
Action. If the backend returns no tool call (text only) we fall back to declare_done so
the episode terminates rather than hanging.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from ..agents import Agent
from ..schemas import Action, Event, Observation
from .backend import LLMBackend, ToolCall
from .prompts import SYSTEM_PROMPT, render_event, render_initial_user_message, render_observation
from .tools import build_tools, tool_call_to_action


class LLMAgent(Agent):
    """OpenAI-compatible agent driver.

    Args:
        backend: anything implementing LLMBackend (OpenAICompat or Scripted).
        system_prompt: overridable system prompt.
        max_messages: rolling-history cap. Once the conversation grows past this many
            messages, the oldest (assistant, tool, user) triples are dropped to stay
            under the server's context window. The system message and the initial user
            message (which carries the task setup and env list) are always preserved.
            With ~1.8K tokens of system+tools and ~500 tokens per turn, 24 messages
            (system + initial + 7 turns + 1 in-flight) fits in an 8K context with margin.
    """

    def __init__(
        self,
        backend: LLMBackend,
        system_prompt: str = SYSTEM_PROMPT,
        max_messages: int = 24,
    ) -> None:
        self._backend = backend
        self._system_prompt = system_prompt
        self._tools = build_tools()
        self._max_messages = max_messages

    def setup(self, task_id: str, request: str, environments: list[dict[str, Any]]) -> None:
        self._task_id = task_id
        self._request = request
        self._environments = environments
        self._messages: list[dict[str, Any]] = []
        self._initialized = False
        self._last_tool_call_id: str | None = None

    def act(
        self,
        observation: Observation,
        history: list[tuple[Observation, Action, Event]],
    ) -> Action:
        if not self._initialized:
            self._messages = [
                {"role": "system", "content": self._system_prompt},
                {
                    "role": "user",
                    "content": render_initial_user_message(self._request, self._environments, observation),
                },
            ]
            self._initialized = True
        else:
            last_event = history[-1][2]
            if self._last_tool_call_id is not None:
                self._messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": self._last_tool_call_id,
                        "content": render_event(last_event),
                    }
                )
            self._messages.append({"role": "user", "content": render_observation(observation)})

        self._trim_history()
        # Snapshot the exact request before the response is appended.
        prompt_messages = [dict(m) for m in self._messages]
        response = self._backend.chat(messages=self._messages, tools=self._tools)
        self._messages.append(response.raw_assistant_message)

        meta = {
            "request": {
                "model": getattr(self._backend, "model", None),
                "messages": prompt_messages,
                "tools": self._tools,
            },
            "response": response.raw_assistant_message,
        }

        if not response.tool_calls:
            self._last_tool_call_id = None
            env_id = observation.environment_id or (self._environments[0]["id"] if self._environments else "")
            action = Action(environment_id=env_id, type="declare_done")
        else:
            tool_call: ToolCall = response.tool_calls[0]
            self._last_tool_call_id = tool_call.id
            env_id = observation.environment_id or (self._environments[0]["id"] if self._environments else "")
            try:
                action = tool_call_to_action(tool_call.name, tool_call.arguments)
            except ValueError:
                action = Action(environment_id=env_id, type="ask_clarification", value=f"unknown tool: {tool_call.name}")
        return dataclasses.replace(action, meta=meta)

    def _trim_history(self) -> None:
        """Drop oldest (assistant, tool, user) triples once self._messages exceeds the cap.

        Layout after the first turn looks like:
            [system, user_initial,
             assistant_0, tool_0, user_obs_1,
             assistant_1, tool_1, user_obs_2,
             ... ]
        Each triple after the prelude is one completed action+observation cycle. Dropping
        a triple removes one turn without orphaning tool_call_ids (the tool message and
        the assistant message that emitted that tool_call disappear together).
        """
        # Reserve 1 slot for the about-to-be-added assistant response.
        budget = self._max_messages - 1
        while len(self._messages) > budget and len(self._messages) >= 5:
            i = 2
            if (
                i + 2 < len(self._messages)
                and self._messages[i].get("role") == "assistant"
                and self._messages[i + 1].get("role") == "tool"
                and self._messages[i + 2].get("role") == "user"
            ):
                del self._messages[i : i + 3]
            else:
                # Layout unexpectedly broke (e.g. text-only assistant turn). Drop one.
                del self._messages[2]
