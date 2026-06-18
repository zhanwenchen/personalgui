"""Core schemas.

Two groups:
- Agent-visible: Action, Observation, Event (subset), AgentVisibleSetup.
- Harness-only: Task, TaskGraph, Subtask, HandoffRequirement, EnvironmentSpec, AppSpec,
  SyntheticUser. The harness must never hand these to the agent adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Action:
    environment_id: str
    type: str
    target: str | None = None
    value: str | None = None
    # Pixel-level metadata. mouse_click/mouse_move use (x, y); key_press uses key.
    # Logical coordinates are relative to the focused app's content area (origin top-left).
    # Semantic actions (click, tap, type, ...) may also carry (x, y) — recorded in the log
    # for observability, but the action's effect is driven by `target` when present.
    x: float | None = None
    y: float | None = None
    key: str | None = None
    # Optional agent-side provenance (e.g. the LLM's exact request + response for this
    # step). Excluded from equality/hash so it never affects action semantics; it just
    # rides along into the episode log for inspection in the replay viewer.
    meta: dict[str, Any] | None = field(default=None, compare=False)


@dataclass(frozen=True)
class Observation:
    environment_id: str
    app_id: str | None
    visible_state: dict[str, Any]
    clipboard_preview: str | None = None


@dataclass(frozen=True)
class Event:
    action: Action
    accepted: bool
    error: str | None = None
    handoff: dict[str, Any] | None = None
    state_changes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentVisibleSetup:
    task_id: str
    request: str
    environments: list[dict[str, Any]]


@dataclass
class AppSpec:
    id: str
    type: str
    display_name: str
    initial_state: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnvironmentSpec:
    id: str
    display_name: str
    apps: list[AppSpec]
    initial_focus_app: str | None = None
    kind: str = "desktop"  # "desktop" | "mobile"; drives the viewer's rendering choice


@dataclass
class Subtask:
    id: str
    description: str
    required_env: str | None = None
    required_app: str | None = None
    depends_on: list[str] = field(default_factory=list)


@dataclass
class HandoffRequirement:
    artifact_type: str
    from_env: str
    to_env: str
    # Optional manual criterion: the value that must actually cross from from_env to to_env.
    # When set, the verifier requires both the env pair AND the value to match. When None,
    # any handoff between the env pair counts as satisfied (the legacy behavior).
    expected_value: str | None = None


@dataclass
class TaskGraph:
    subtasks: list[Subtask]
    required_handoffs: list[HandoffRequirement] = field(default_factory=list)


@dataclass
class SyntheticUser:
    name: str
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class ForbiddenRoute:
    """A combination that, if observed in the accepted action log, fails boundary_adherence."""
    environment_id: str
    app_id: str
    reason: str = ""


@dataclass
class Task:
    task_id: str
    request: str
    user: SyntheticUser
    environments_spec: list[EnvironmentSpec]
    task_graph: TaskGraph
    desired_final_state: dict[str, Any]
    initial_focus_env: str
    max_steps: int = 50
    # ---- optional metric-config fields ------------------------------------------------
    # If an accepted action targets any of these (env, app) pairs, boundary_adherence fails.
    forbidden_routes: list[ForbiddenRoute] = field(default_factory=list)
    # When True, the agent must call ask_clarification at least once before acting; the
    # clarification_quality metric rewards this and penalizes irreversible actions taken
    # without it.
    requires_clarification: bool = False
    # Substrings that must NOT appear in any handoff value. Tests minimal-transfer behavior.
    forbidden_handoff_substrings: list[str] = field(default_factory=list)
