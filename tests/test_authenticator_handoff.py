"""End-to-end tests for the v0 vertical slice."""

from personalgui.agents import ScriptedNaiveAgent, ScriptedOracleAgent
from personalgui.harness import _build_agent_visible_setup, evaluate_task
from personalgui.tasks import build_authenticator_handoff_task
from personalgui.verifiers import DEFAULT_VERIFIERS


def test_oracle_agent_completes_authenticator_task():
    task = build_authenticator_handoff_task()
    metrics, log = evaluate_task(task, ScriptedOracleAgent(), DEFAULT_VERIFIERS)
    assert metrics["global_success"] is True
    assert metrics["routing_accuracy"] == 1.0
    assert metrics["handoff_correctness"] == 1.0
    assert any(rec["action"]["type"] == "declare_done" for rec in log)


def test_naive_agent_fails_global_success():
    task = build_authenticator_handoff_task()
    metrics, _ = evaluate_task(task, ScriptedNaiveAgent(), DEFAULT_VERIFIERS)
    assert metrics["global_success"] is False
    assert metrics["routing_accuracy"] < 1.0
    assert metrics["handoff_correctness"] == 0.0


def test_expected_code_is_hidden_from_agent_setup():
    """The harness must not leak the OTP via the agent-visible setup payload."""
    task = build_authenticator_handoff_task(otp_code="9173")
    setup = _build_agent_visible_setup(task)
    serialized = repr(setup)
    assert "expected_code" not in serialized
    assert "9173" not in serialized


def test_expected_code_is_never_leaked_in_observations():
    """The portal's hidden expected_code must never appear in any agent observation.

    The OTP value WILL appear in the desktop view after the agent pastes it into the input field,
    but that's the agent's own input echoing back, not a leak. The leak we guard against is
    expected_code surfacing via render() at any point.
    """
    task = build_authenticator_handoff_task(otp_code="9173")
    captured: list[dict[str, object]] = []

    class _ObsCapturingAgent(ScriptedOracleAgent):
        def act(self, observation, history):
            captured.append({"app_id": observation.app_id, "visible": observation.visible_state})
            return super().act(observation, history)

    evaluate_task(task, _ObsCapturingAgent(), DEFAULT_VERIFIERS)

    for view in captured:
        assert "expected_code" not in repr(view["visible"])
