"""Shared scaffolding for oracle-solvability tests of catalog task builders.

An "oracle" here is a hand-written list of Actions that perfectly solves a task. Running it
through the real harness and asserting the headline metric proves the builder is solvable
(the apps, fields, handoffs, and desired_final_state all line up).

Usage in a per-domain test file (tests/ is on sys.path under pytest's default import mode):

    import pytest
    from oracle_helpers import FixedPlanAgent, run_oracle, openapp, copy, paste, click, type_, ask, done

    CASES = {
        "my_task_v0_01": (
            [openapp("windows_desktop", "email"), copy("windows_desktop", "CODE"),
             openapp("windows_desktop", "form"), paste("windows_desktop", "field"),
             click("windows_desktop", "submit"), done("windows_desktop")],
            {"global_success": True, "handoff_correctness": 1.0},
        ),
    }

    @pytest.mark.parametrize("task_id", sorted(CASES))
    def test_oracle(task_id):
        run_oracle(task_id, *CASES[task_id])
"""

from __future__ import annotations

from personalgui.harness import evaluate_task
from personalgui.schemas import Action
from personalgui.tasks import build_task
from personalgui.verifiers import DEFAULT_VERIFIERS


class FixedPlanAgent:
    """Replays a fixed list of Actions, then declares done in the last-used environment."""

    def __init__(self, plan: list[Action]) -> None:
        self._plan = plan
        self._idx = 0

    def setup(self, task_id, request, environments) -> None:
        pass

    def act(self, observation, history) -> Action:
        if self._idx < len(self._plan):
            action = self._plan[self._idx]
            self._idx += 1
            return action
        env = self._plan[-1].environment_id if self._plan else "windows_desktop"
        return Action(environment_id=env, type="declare_done")


# --- Action constructors (terse, to keep plans readable) --------------------------------

def openapp(env: str, app: str | None) -> Action:
    return Action(environment_id=env, type="open_app", target=app)


def copy(env: str, value: str) -> Action:
    return Action(environment_id=env, type="copy_value", value=value)


def paste(env: str, target: str) -> Action:
    return Action(environment_id=env, type="paste_value", target=target)


def click(env: str, target: str) -> Action:
    return Action(environment_id=env, type="click", target=target)


def tap(env: str, target: str) -> Action:
    return Action(environment_id=env, type="tap", target=target)


def type_(env: str, target: str, value: str) -> Action:
    return Action(environment_id=env, type="type", target=target, value=value)


def ask(env: str) -> Action:
    return Action(environment_id=env, type="ask_clarification")


def done(env: str) -> Action:
    return Action(environment_id=env, type="declare_done")


def run_oracle(task_id: str, plan: list[Action], expected: dict[str, object]) -> dict:
    """Build the task, run the plan, assert each expected metric. Returns the metrics."""
    task = build_task(task_id)
    metrics, _log = evaluate_task(task, FixedPlanAgent(plan), DEFAULT_VERIFIERS)
    for metric, want in expected.items():
        assert metrics[metric] == want, (
            f"{task_id}: {metric}={metrics[metric]!r}, expected {want!r}; "
            f"details={metrics.get(str(metric) + '_details')}"
        )
    assert metrics["terminated_by"] == "declare_done", (
        f"{task_id}: terminated_by={metrics['terminated_by']} (plan didn't reach declare_done)"
    )
    return metrics
