"""Environment runtime: per-env focus + cross-env routing."""

from __future__ import annotations

from typing import Any, Callable

from .apps import App, build_app
from .handoff import HandoffBuffer
from .schemas import Action, EnvironmentSpec, Event, Observation


class Clock:
    """Logical clock: advances exactly one tick per environment step (one agent action,
    including an explicit ``wait``). Time-varying apps read ``tick`` to compute state that
    evolves on its own — codes refresh, OTPs expire, deadlines approach — independent of
    which action the agent takes. The world is not waiting for the agent: delay itself
    changes the problem. Wall-clock-free, so episodes stay deterministic and replayable."""

    def __init__(self) -> None:
        self.tick = 0


def _hit_test(bounds: list[dict[str, Any]], x: float, y: float) -> dict[str, Any] | None:
    """Return the FIRST bounds entry containing (x, y), or None. Bounds are dicts with
    x, y, w, h keys (logical pixels)."""
    for b in bounds:
        bx, by, bw, bh = b.get("x", 0), b.get("y", 0), b.get("w", 0), b.get("h", 0)
        if bx <= x <= bx + bw and by <= y <= by + bh:
            return b
    return None


class Environment:
    def __init__(self, spec: EnvironmentSpec, handoff: HandoffBuffer, clock: Clock) -> None:
        self.id = spec.id
        self.display_name = spec.display_name
        self.kind = spec.kind
        self.apps: dict[str, App] = {a.id: build_app(a) for a in spec.apps}
        for app in self.apps.values():
            app.bind_clock(clock)
        self.focused_app: str | None = spec.initial_focus_app
        # Within the focused app, which input element has the keyboard focus.
        # Set by mouse_click on an input or by a semantic "type" action.
        self.focused_element: str | None = None
        self.handoff = handoff
        handoff.register_env(self.id)

    def observe(self) -> Observation:
        app = self.apps.get(self.focused_app) if self.focused_app else None
        visible = app.render() if app else {"kind": "home", "apps_available": list(self.apps.keys())}
        return Observation(
            environment_id=self.id,
            app_id=self.focused_app,
            visible_state=visible,
            clipboard_preview=self.handoff.peek(self.id),
        )

    def step(self, action: Action) -> Event:
        if action.type == "open_app":
            # target=None means "go home" — clear the focused app. Useful for the phone's
            # home button / home indicator gesture.
            if action.target is None:
                prev = self.focused_app
                self.focused_app = None
                return Event(action=action, accepted=True, state_changes={"focused_app": [prev, None]})
            if action.target not in self.apps:
                return Event(action=action, accepted=False, error=f"unknown app {action.target}")
            prev = self.focused_app
            self.focused_app = action.target
            return Event(action=action, accepted=True, state_changes={"focused_app": [prev, self.focused_app]})

        if action.type == "mouse_click":
            # Hit-test (x, y) against the focused app's element_bounds and dispatch
            # the matching semantic action.
            if action.x is None or action.y is None:
                return Event(action=action, accepted=False, error="mouse_click requires x and y")
            if not self.focused_app:
                return Event(action=action, accepted=False, error="no app focused; cannot hit-test")
            app = self.apps[self.focused_app]
            hit = _hit_test(app.element_bounds(), float(action.x), float(action.y))
            if hit is None:
                return Event(action=action, accepted=False, error=f"no element at ({action.x}, {action.y})")
            # Translate the hit into the right semantic action and dispatch.
            kind = hit.get("kind")
            target = hit.get("target")
            if kind == "button":
                accepted, error, changes = app.handle_action("click", target, None)
                changes = dict(changes)
                changes["resolved_target"] = target
                changes["hit_kind"] = "button"
                return Event(action=action, accepted=accepted, error=error, state_changes=changes)
            if kind == "input":
                self.focused_element = target
                return Event(
                    action=action, accepted=True,
                    state_changes={"focused_element": target, "resolved_target": target, "hit_kind": "input"},
                )
            if kind == "copyable":
                value = hit.get("value", "")
                self.handoff.copy(self.id, value)
                return Event(
                    action=action, accepted=True,
                    handoff={"copied_from": self.id, "to_env": None, "value": value},
                    state_changes={"resolved_target": target, "hit_kind": "copyable", "copied_value": value},
                )
            return Event(action=action, accepted=False, error=f"unknown element kind {kind}")

        if action.type == "key_press":
            if not action.key:
                return Event(action=action, accepted=False, error="key_press requires key")
            # Enter on a focused input that has a sibling submit -> click submit.
            # For v0, we just record the keypress and apply minimal semantics.
            if action.key == "Enter" and self.focused_app and self.focused_element:
                # Try clicking a "submit"/"save" button on the same app.
                app = self.apps[self.focused_app]
                for b in app.element_bounds():
                    if b.get("kind") == "button" and b.get("target") in {"submit", "save"}:
                        accepted, error, changes = app.handle_action("click", b["target"], None)
                        changes = dict(changes)
                        changes["resolved_by_key"] = action.key
                        changes["resolved_target"] = b["target"]
                        return Event(action=action, accepted=accepted, error=error, state_changes=changes)
            # Escape clears focused element on the input.
            if action.key == "Escape":
                prev = self.focused_element
                self.focused_element = None
                return Event(action=action, accepted=True, state_changes={"focused_element": [prev, None]})
            # Otherwise just acknowledge — keystroke recorded in the log without state change.
            return Event(action=action, accepted=True, state_changes={"recorded_key": action.key})

        if action.type == "copy_value":
            value = action.value or ""
            self.handoff.copy(self.id, value)
            return Event(
                action=action,
                accepted=True,
                handoff={"copied_from": self.id, "to_env": None, "value": value},
            )

        if action.type == "paste_value":
            if not self.focused_app:
                return Event(action=action, accepted=False, error="no app focused")
            clipboard_value: str | None = self.handoff.peek(self.id)
            origin = self.handoff.origin(self.id)
            if clipboard_value is None:
                return Event(action=action, accepted=False, error="clipboard empty")
            value = clipboard_value
            app = self.apps[self.focused_app]
            accepted, error, changes = app.handle_action("type", action.target, value)
            handoff_info: dict[str, Any] | None = None
            # Record EVERY paste-driven transfer, including same-env (e.g. copy from
            # email app and paste into chat compose on the same desktop). Verifiers can
            # filter by from_env/to_env match if they care about cross-device specifically.
            if accepted and origin:
                handoff_info = {"from_env": origin, "to_env": self.id, "value": value}
                self.handoff.record_transfer(from_env=origin, to_env=self.id, value=value)
            return Event(action=action, accepted=accepted, error=error, handoff=handoff_info, state_changes=changes)

        if action.type == "declare_done":
            return Event(action=action, accepted=True)

        if action.type == "ask_clarification":
            return Event(action=action, accepted=True)

        if action.type == "wait":
            # A deliberate no-op. It still consumes a tick (advanced by EnvironmentSet),
            # so the exogenous world keeps moving — "do nothing" is a real action here.
            return Event(action=action, accepted=True, state_changes={"waited": True})

        if not self.focused_app:
            return Event(action=action, accepted=False, error="no app focused")
        app = self.apps[self.focused_app]
        accepted, error, changes = app.handle_action(action.type, action.target, action.value)
        return Event(action=action, accepted=accepted, error=error, state_changes=changes)


class EnvironmentSet:
    def __init__(self, specs: list[EnvironmentSpec], initial_focus_env: str) -> None:
        self.handoff = HandoffBuffer()
        self.clock = Clock()
        self.environments: dict[str, Environment] = {
            spec.id: Environment(spec, self.handoff, self.clock) for spec in specs
        }
        if initial_focus_env not in self.environments:
            raise ValueError(f"initial_focus_env {initial_focus_env} not in environments")
        self.focused_env: str = initial_focus_env
        self.step_observers: list[Callable[[Action, Event], None]] = []

    def observe(self) -> Observation:
        return self.environments[self.focused_env].observe()

    def step(self, action: Action) -> Event:
        if action.environment_id not in self.environments:
            event = Event(action=action, accepted=False, error=f"unknown env {action.environment_id}")
        else:
            if action.environment_id != self.focused_env:
                self.focused_env = action.environment_id
            event = self.environments[action.environment_id].step(action)
        # Every agent action consumes one tick — the action is applied at the current tick,
        # then the logical clock advances so the next observation reflects the moved world.
        self.clock.tick += 1
        self._notify(action, event)
        return event

    def _notify(self, action: Action, event: Event) -> None:
        for observer in self.step_observers:
            observer(action, event)

    def backend_snapshot(self) -> dict[str, Any]:
        return {
            env_id: {app_id: dict(app.state) for app_id, app in env.apps.items()}
            for env_id, env in self.environments.items()
        }
