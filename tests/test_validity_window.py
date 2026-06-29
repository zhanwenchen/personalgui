"""Live exogenous-state task: the authenticator code refreshes on the logical clock, so the
agent must submit it within its validity window. Proves the clock advances, the form enforces
the window, and the validity_window metric distinguishes a clean just-in-time submit from one
that acted on a stale (expired) code."""

from __future__ import annotations

from personalgui.harness import evaluate_task
from personalgui.schemas import Action
from personalgui.tasks import build_task
from personalgui.verifiers import DEFAULT_VERIFIERS

from oracle_helpers import FixedPlanAgent, copy, openapp, paste, click, done

D = "windows_desktop"
P = "android_phone"
CURRENT = "730164"  # codes[0]; valid for ticks 0..4 (period=5)


def _wait(env: str) -> Action:
    return Action(environment_id=env, type="wait")


def test_direct_path_submits_within_validity_window():
    """Read -> carry -> submit inside one window: the code is still current at submit time."""
    task = build_task("sec_12_v0_01")
    plan = [
        copy(P, CURRENT),          # tick 0: copy the live code
        openapp(D, "vault_portal"),  # tick 1
        paste(D, "auth_code"),     # tick 2
        click(D, "submit"),        # tick 3 -> still window 0, code current
        done(D),
    ]
    metrics, _ = evaluate_task(task, FixedPlanAgent(plan), DEFAULT_VERIFIERS)
    assert metrics["global_success"] is True
    assert metrics["validity_window"] == 1.0
    assert metrics["handoff_correctness"] == 1.0
    assert metrics["routing_accuracy"] == 1.0


def test_dithering_lets_the_code_expire():
    """A couple of wasted ticks push the submit into the next window: the carried code is now
    expired, the form rejects it, and validity_window/global_success both fail."""
    task = build_task("sec_12_v0_01")
    plan = [
        copy(P, CURRENT),          # tick 0: copy codes[0]
        openapp(D, "vault_portal"),  # tick 1
        paste(D, "auth_code"),     # tick 2
        _wait(D),                  # tick 3
        _wait(D),                  # tick 4
        click(D, "submit"),        # tick 5 -> window 1, codes[0] is expired
        done(D),
    ]
    metrics, log = evaluate_task(task, FixedPlanAgent(plan), DEFAULT_VERIFIERS)
    assert metrics["global_success"] is False
    assert metrics["validity_window"] == 0.0
    # The form reported the failure specifically as expiry, not a generic mismatch.
    statuses = [
        rec["event"]["state_changes"].get("submitted_code_status")
        for rec in log
        if rec["event"]["state_changes"].get("submitted_code_status")
    ]
    assert statuses == ["expired"]


def test_validity_window_is_none_for_non_timed_tasks():
    """Tasks without a time-based submission leave the metric inapplicable (None)."""
    task = build_task("authenticator_vs_sms_v0_01")
    plan = [
        openapp(P, "mock_authenticator"), copy(P, "730164"),
        openapp(D, "sentinel_portal"), paste(D, "auth_code"), click(D, "submit"), done(D),
    ]
    metrics, _ = evaluate_task(task, FixedPlanAgent(plan), DEFAULT_VERIFIERS)
    assert metrics["validity_window"] is None
    assert metrics["global_success"] is True
