"""Episode runner and logger."""

from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any, Callable, Iterable

from .agents import Agent
from .environments import EnvironmentSet
from .schemas import Action, AgentVisibleSetup, Event, Observation, Task
from .verifiers import Verifier


class EpisodeLogger:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def record(self, step: int, observation: Observation, action: Action, event: Event) -> None:
        self.records.append(
            {
                "step": step,
                "observation": asdict(observation),
                "action": asdict(action),
                "event": asdict(event),
            }
        )

    def export(self) -> list[dict[str, Any]]:
        return list(self.records)


def _build_agent_visible_setup(task: Task) -> AgentVisibleSetup:
    envs_view = []
    for env in task.environments_spec:
        envs_view.append(
            {
                "id": env.id,
                "display_name": env.display_name,
                "apps": [{"id": a.id, "display_name": a.display_name} for a in env.apps],
            }
        )
    return AgentVisibleSetup(task_id=task.task_id, request=task.request, environments=envs_view)


def evaluate_task(
    task: Task,
    agent: Agent,
    verifiers: list[Verifier],
    step_delay: float = 0.0,
    on_setup: Callable[[EnvironmentSet, Task], None] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run one episode end-to-end and return verifier metrics + the log.

    Args:
        task: The task to evaluate.
        agent: Agent under test.
        verifiers: Verifiers to compute on the final state.
        step_delay: Seconds to sleep after each step. Use a small value (e.g. 0.4) when
            running with the viz server so a human can watch instant-finish scripted agents.
        on_setup: Optional hook invoked once with (env_set, task) before the loop starts.
            Used by the viz server to attach to the live environment.
    """
    env_set = EnvironmentSet(task.environments_spec, task.initial_focus_env)
    logger = EpisodeLogger()
    setup = _build_agent_visible_setup(task)

    if on_setup is not None:
        on_setup(env_set, task)

    agent.setup(
        task_id=setup.task_id,
        request=setup.request,
        environments=setup.environments,
    )

    observation = env_set.observe()
    history: list[tuple[Observation, Action, Event]] = []

    # "max_steps" until the agent explicitly declares done. This distinguishes a clean
    # finish from a budget exhaustion (the agent looping/stuck), which the state-based
    # metrics alone can't tell apart.
    terminated_by = "max_steps"
    for step in range(task.max_steps):
        action = agent.act(observation, history)
        event = env_set.step(action)
        logger.record(step, observation, action, event)
        history.append((observation, action, event))
        observation = env_set.observe()

        # Snapshot cumulative metrics after this step. Re-runs every verifier against the
        # partial log + state-so-far and keeps only the scalar values (not *_details) so the
        # replay viewer and trajectory printout can show how each metric evolved step-by-step.
        step_state = env_set.backend_snapshot()
        step_handoff_events = [asdict(e) for e in env_set.handoff.events]
        step_metrics: dict[str, Any] = {}
        for v in verifiers:
            step_metrics.update(v.run(
                task=task, final_state=step_state,
                log=logger.records, handoff_events=step_handoff_events,
            ))
        logger.records[-1]["cumulative_metrics"] = {
            k: val for k, val in step_metrics.items() if not k.endswith("_details")
        }

        if step_delay > 0:
            time.sleep(step_delay)
        if action.type == "declare_done":
            terminated_by = "declare_done"
            break

    final_state = env_set.backend_snapshot()
    handoff_events = [asdict(e) for e in env_set.handoff.events]

    metrics: dict[str, Any] = {
        "terminated_by": terminated_by,
        "steps_used": len(logger.records),
        "max_steps": task.max_steps,
    }
    for v in verifiers:
        metrics.update(
            v.run(task=task, final_state=final_state, log=logger.records, handoff_events=handoff_events)
        )

    return metrics, logger.export()


def evaluate_split(
    tasks: Iterable[Task], agents: dict[str, Agent], verifiers: list[Verifier]
) -> dict[str, list[dict[str, Any]]]:
    results: dict[str, list[dict[str, Any]]] = {}
    for name, agent in agents.items():
        results[name] = []
        for task in tasks:
            metrics, log = evaluate_task(task, agent, verifiers)
            results[name].append({"task_id": task.task_id, "metrics": metrics, "log_steps": len(log)})
    return results
