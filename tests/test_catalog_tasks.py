"""Tests for the catalog-derived task builders.

Two layers:
  1. Structural invariants over EVERY task in TASK_REGISTRY — guards that envs/apps,
     subtask routes, handoff endpoints, forbidden routes, and desired_final_state paths
     all reference things that actually exist. Catches typos in any builder, old or new.
  2. Oracle solvability — a hand-written action plan for each of the 12 catalog-derived
     builders, run through the real harness, asserting the task's headline metric.
"""

from __future__ import annotations

import pytest

from personalgui.apps import APP_REGISTRY
from personalgui.harness import evaluate_task
from personalgui.schemas import Action
from personalgui.tasks import TASK_REGISTRY, build_task
from personalgui.verifiers import DEFAULT_VERIFIERS


# --------------------------------------------------------------------------------------
# Layer 1: structural invariants over all registered tasks
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("task_id", sorted(TASK_REGISTRY))
def test_task_is_well_formed(task_id: str) -> None:
    task = build_task(task_id)
    env_ids = {e.id for e in task.environments_spec}
    apps_by_env = {e.id: {a.id for a in e.apps} for e in task.environments_spec}

    # task_id round-trips and every app type is real
    assert task.task_id == task_id
    assert task.request.strip()
    for e in task.environments_spec:
        for a in e.apps:
            assert a.type in APP_REGISTRY, f"{task_id}: unknown app type {a.type}"
        if e.initial_focus_app is not None:
            assert e.initial_focus_app in apps_by_env[e.id]

    assert task.initial_focus_env in env_ids

    for st in task.task_graph.subtasks:
        if st.required_env is not None:
            assert st.required_env in env_ids, f"{task_id}/{st.id}: bad required_env"
        if st.required_app is not None:
            assert st.required_env is not None
            assert st.required_app in apps_by_env[st.required_env], f"{task_id}/{st.id}: bad required_app"
        for dep in st.depends_on:
            assert dep in {s.id for s in task.task_graph.subtasks}

    for h in task.task_graph.required_handoffs:
        assert h.from_env in env_ids, f"{task_id}: handoff from {h.from_env}"
        assert h.to_env in env_ids, f"{task_id}: handoff to {h.to_env}"

    for fr in task.forbidden_routes:
        assert fr.environment_id in env_ids
        assert fr.app_id in apps_by_env[fr.environment_id]

    for path in task.desired_final_state:
        env_id, app_id, _field = path.split(".", 2)
        assert env_id in env_ids, f"{task_id}: desired_final_state env {env_id}"
        assert app_id in apps_by_env[env_id], f"{task_id}: desired_final_state app {app_id}"


# --------------------------------------------------------------------------------------
# Layer 2: oracle solvability for the catalog-derived builders
# --------------------------------------------------------------------------------------

class FixedPlanAgent:
    """Replays a fixed list of Actions, then declares done. No model in the loop."""

    def __init__(self, plan: list[Action]) -> None:
        self._plan = plan
        self._idx = 0

    def setup(self, task_id, request, environments) -> None:  # noqa: D401
        pass

    def act(self, observation, history) -> Action:
        if self._idx < len(self._plan):
            action = self._plan[self._idx]
            self._idx += 1
            return action
        # Fall through to a terminal action keyed to whatever env we last acted in.
        env = self._plan[-1].environment_id if self._plan else "windows_desktop"
        return Action(environment_id=env, type="declare_done")


D = "windows_desktop"
P = "android_phone"


def _open(env, app):
    return Action(environment_id=env, type="open_app", target=app)


def _copy(env, value):
    return Action(environment_id=env, type="copy_value", value=value)


def _paste(env, target):
    return Action(environment_id=env, type="paste_value", target=target)


def _click(env, target):
    return Action(environment_id=env, type="click", target=target)


def _type(env, target, value):
    return Action(environment_id=env, type="type", target=target, value=value)


def _done(env):
    return Action(environment_id=env, type="declare_done")


# task_id -> (plan, {metric: expected_value})
ORACLE_CASES = {
    "subscription_cancel_code_v0_01": (
        [_open(D, "email"), _copy(D, "CXL-7741"), _open(D, "cancel_form"),
         _paste(D, "confirmation_code"), _click(D, "submit"), _done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    "reimbursement_work_chat_only_v0_01": (
        [_open(D, "email"), _copy(D, "RMB-3382"), _open(D, "work_chat"),
         _paste(D, "compose"), _click(D, "send"), _done(D)],
        {"handoff_correctness": 1.0, "boundary_adherence": 1.0, "routing_accuracy": 1.0},
    ),
    "which_lunch_expense_v0_01": (
        [Action(environment_id=D, type="ask_clarification"), _done(D)],
        {"clarification_quality": 1.0},
    ),
    "ooo_from_approval_v0_01": (
        [_open(D, "email"), _copy(D, "2026-07-06"), _paste(D, "ooo_start"),
         _type(D, "ooo_end", "2026-07-10"), _click(D, "ooo_toggle"), _done(D)],
        {"global_success": True, "handoff_correctness": 1.0},
    ),
    "new_account_two_codes_v0_01": (
        [_open(D, "email"), _copy(D, "EMC-5521"), _open(D, "activation_form"),
         _paste(D, "email_code"),
         _open(P, "mock_authenticator"), _copy(P, "771243"),
         _open(D, "activation_form"), _paste(D, "auth_code"),
         _click(D, "submit"), _done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    "authenticator_vs_sms_v0_01": (
        [_open(P, "mock_authenticator"), _copy(P, "730164"),
         _open(D, "sentinel_portal"), _paste(D, "auth_code"), _click(D, "submit"), _done(D)],
        {"global_success": True, "handoff_correctness": 1.0},
    ),
    "relay_code_to_support_chat_v0_01": (
        [_open(P, "mock_authenticator"), _copy(P, "552087"),
         _open(D, "support_chat"), _paste(D, "compose"), _click(D, "send"), _done(D)],
        {"handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    "reviewer_comment_into_doc_v0_01": (
        [_open(D, "review_chat"), _copy(D, "Clarify the evaluation protocol in section 3."),
         _open(D, "draft_doc"), _paste(D, "body"), _click(D, "save"), _done(D)],
        {"global_success": True, "handoff_correctness": 1.0},
    ),
    "return_rma_code_v0_01": (
        [_open(D, "email"), _copy(D, "RMA-90817"), _open(D, "return_form"),
         _paste(D, "rma_code"), _click(D, "submit"), _done(D)],
        {"global_success": True, "handoff_correctness": 1.0},
    ),
    "coupon_not_card_number_v0_01": (
        [_open(D, "email"), _copy(D, "SAVE15"), _open(D, "checkout_form"),
         _paste(D, "coupon"), _click(D, "submit"), _done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "minimal_transfer": 1.0},
    ),
    "copay_reference_number_v0_01": (
        [_open(D, "email"), _copy(D, "PAY-553042"), _open(D, "billing_portal"),
         _paste(D, "payment_reference"), _click(D, "submit"), _done(D)],
        {"global_success": True, "handoff_correctness": 1.0},
    ),
    "rent_transfer_2fa_v0_01": (
        [_open(P, "mock_authenticator"), _copy(P, "664120"),
         _open(D, "transfer_form"), _paste(D, "totp"), _click(D, "submit"), _done(D)],
        {"global_success": True, "handoff_correctness": 1.0},
    ),
}


def test_oracle_cases_cover_every_catalog_builder() -> None:
    """Every catalog-derived task_id (those carrying a catalog id comment) has an oracle."""
    catalog_ids = {
        "subscription_cancel_code_v0_01", "reimbursement_work_chat_only_v0_01",
        "which_lunch_expense_v0_01", "ooo_from_approval_v0_01", "new_account_two_codes_v0_01",
        "authenticator_vs_sms_v0_01", "relay_code_to_support_chat_v0_01",
        "reviewer_comment_into_doc_v0_01", "return_rma_code_v0_01",
        "coupon_not_card_number_v0_01", "copay_reference_number_v0_01", "rent_transfer_2fa_v0_01",
    }
    assert catalog_ids <= set(TASK_REGISTRY)
    assert catalog_ids == set(ORACLE_CASES)


@pytest.mark.parametrize("task_id", sorted(ORACLE_CASES))
def test_oracle_plan_solves_task(task_id: str) -> None:
    plan, expected = ORACLE_CASES[task_id]
    task = build_task(task_id)
    metrics, log = evaluate_task(task, FixedPlanAgent(plan), DEFAULT_VERIFIERS)
    for metric, want in expected.items():
        assert metrics[metric] == want, (
            f"{task_id}: {metric}={metrics[metric]!r}, expected {want!r}; "
            f"details={metrics.get(metric + '_details')}"
        )
    assert metrics["terminated_by"] == "declare_done"


def test_naive_leaks_card_number_fails_minimal_transfer() -> None:
    """A naive agent that copies the whole email block (card number included) leaks it."""
    task = build_task("coupon_not_card_number_v0_01")
    leak_plan = [
        _open(D, "email"),
        _copy(D, "Coupon code: SAVE15  Card on file: 4111 1111 1111 1234"),
        _open(D, "checkout_form"), _paste(D, "coupon"), _click(D, "submit"), _done(D),
    ]
    metrics, _ = evaluate_task(task, FixedPlanAgent(leak_plan), DEFAULT_VERIFIERS)
    assert metrics["minimal_transfer"] == 0.0
    # And it doesn't even complete: the coupon field no longer matches.
    assert metrics["global_success"] is False


def test_naive_uses_personal_chat_fails_boundary() -> None:
    """Sending the reimbursement code via the personal phone chat violates the boundary."""
    task = build_task("reimbursement_work_chat_only_v0_01")
    bad_plan = [
        _open(D, "email"), _copy(D, "RMB-3382"),
        _open(P, "phone_chat"), _paste(P, "compose"), _click(P, "send"), _done(P),
    ]
    metrics, _ = evaluate_task(task, FixedPlanAgent(bad_plan), DEFAULT_VERIFIERS)
    assert metrics["boundary_adherence"] == 0.0
