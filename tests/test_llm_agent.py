"""LLMAgent tests using the scripted backend. No real LLM required."""

from __future__ import annotations

import json
import os

import pytest

from personalgui.harness import evaluate_task
from personalgui.llm import LLMAgent, OpenAICompatBackend, ScriptedBackend, ScriptedToolCall
from personalgui.tasks import build_authenticator_handoff_task
from personalgui.verifiers import DEFAULT_VERIFIERS


def _oracle_plan(otp: str) -> list[ScriptedToolCall]:
    """Hand-written tool-call plan that solves the authenticator-handoff task.

    Exercises every tool-call type the agent loop needs: open_app, copy_value,
    paste_value (cross-env handoff), click, declare_done.
    """
    return [
        ScriptedToolCall("open_app", {"environment_id": "android_phone", "app_id": "mock_authenticator"}),
        ScriptedToolCall("copy_value", {"environment_id": "android_phone", "value": otp}),
        ScriptedToolCall("open_app", {"environment_id": "windows_desktop", "app_id": "expense_portal"}),
        ScriptedToolCall("paste_value", {"environment_id": "windows_desktop", "target": "otp"}),
        ScriptedToolCall("click", {"environment_id": "windows_desktop", "target": "submit"}),
        ScriptedToolCall("declare_done", {"environment_id": "windows_desktop"}),
    ]


def test_llm_agent_solves_authenticator_task_with_scripted_backend():
    otp = "4729"
    task = build_authenticator_handoff_task(otp_code=otp)
    backend = ScriptedBackend(plan=_oracle_plan(otp))
    agent = LLMAgent(backend=backend)

    metrics, log = evaluate_task(task, agent, DEFAULT_VERIFIERS)

    assert metrics["global_success"] is True
    assert metrics["routing_accuracy"] == 1.0
    assert metrics["handoff_correctness"] == 1.0
    assert any(rec["action"]["type"] == "declare_done" for rec in log)


def test_llm_agent_sees_otp_in_phone_observation():
    """The agent should be able to read the OTP from the phone after open_app."""
    otp = "8821"
    task = build_authenticator_handoff_task(otp_code=otp)

    # A plan that *would* solve the task IF the agent picks up the OTP from the observation
    # the backend sees on the second turn. We use a sentinel value here and assert that the
    # backend received an observation message containing the real OTP between turn 1 and 2.
    backend = ScriptedBackend(plan=_oracle_plan(otp))
    agent = LLMAgent(backend=backend)

    evaluate_task(task, agent, DEFAULT_VERIFIERS)

    second_call_messages = backend.received_messages[1]
    user_messages = [m for m in second_call_messages if m.get("role") == "user"]
    rendered = "\n".join(str(m.get("content", "")) for m in user_messages)
    assert otp in rendered, "OTP from phone authenticator should appear in observation rendering"


def test_llm_agent_no_tool_call_falls_back_to_declare_done():
    """If the backend returns text without a tool_call, the agent must not hang."""

    class _NoToolBackend:
        def chat(self, messages, tools):
            from personalgui.llm.backend import BackendResponse
            return BackendResponse(
                tool_calls=[],
                raw_assistant_message={"role": "assistant", "content": "I'll just talk."},
            )

    task = build_authenticator_handoff_task()
    agent = LLMAgent(backend=_NoToolBackend())
    metrics, log = evaluate_task(task, agent, DEFAULT_VERIFIERS)

    assert metrics["global_success"] is False
    assert log[0]["action"]["type"] == "declare_done"
    assert len(log) == 1


def test_llm_agent_handles_unknown_tool_name():
    """An unknown tool name should not crash the agent loop."""

    from personalgui.llm.backend import BackendResponse, ToolCall

    class _BogusToolBackend:
        def chat(self, messages, tools):
            return BackendResponse(
                tool_calls=[ToolCall(id="call_x", name="hallucinated_tool", arguments={})],
                raw_assistant_message={
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{"id": "call_x", "type": "function",
                                    "function": {"name": "hallucinated_tool", "arguments": "{}"}}],
                },
            )

    task = build_authenticator_handoff_task()
    agent = LLMAgent(backend=_BogusToolBackend())
    # Cap with max_steps so the test doesn't loop forever
    task.max_steps = 3
    metrics, log = evaluate_task(task, agent, DEFAULT_VERIFIERS)

    assert metrics["global_success"] is False
    assert all(rec["action"]["type"] == "ask_clarification" for rec in log)


def test_llm_agent_tool_schemas_are_well_formed():
    """Every tool definition should be a valid OpenAI tool spec."""
    from personalgui.llm.tools import build_tools

    tools = build_tools()
    names = {t["function"]["name"] for t in tools}
    assert {"open_app", "tap", "click", "type_text", "view", "copy_value",
            "paste_value", "ask_clarification", "declare_done",
            "mouse_click", "key_press"} == names
    for t in tools:
        assert t["type"] == "function"
        params = t["function"]["parameters"]
        assert params["type"] == "object"
        assert params["additionalProperties"] is False
        assert "environment_id" in params["properties"]
        assert "environment_id" in params["required"]


@pytest.mark.skipif(
    "RUN_LIVE_LLM" not in os.environ,
    reason="Live LLM test gated by RUN_LIVE_LLM=1 (requires a running OpenAI-compatible server).",
)
def test_llm_agent_against_live_server():
    """Optional smoke test: hit the real local model.

    Set RUN_LIVE_LLM=1 and (optionally) PERSONALGUI_LLM_BASE_URL and PERSONALGUI_LLM_MODEL.
    Defaults: http://localhost:8000/v1, model 'qwen3.5-4b'.
    """
    task = build_authenticator_handoff_task()
    backend = OpenAICompatBackend()
    agent = LLMAgent(backend=backend)
    metrics, log = evaluate_task(task, agent, DEFAULT_VERIFIERS)
    # We don't assert on success; small local models may fail. We only assert the loop ran.
    assert len(log) > 0
    print(json.dumps(metrics, indent=2))
