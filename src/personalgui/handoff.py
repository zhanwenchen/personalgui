"""Cross-environment handoff bus.

v0 simplification: every environment shares one logical clipboard. A copy on env A
propagates to all envs immediately; the origin env is tracked so the harness can
distinguish a same-env paste from a true cross-environment handoff.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HandoffEvent:
    from_env: str
    to_env: str | None
    value: str
    artifact_type: str | None = None


class HandoffBuffer:
    def __init__(self) -> None:
        self._values: dict[str, str | None] = {}
        self._origin: dict[str, str | None] = {}
        self.events: list[HandoffEvent] = []

    def register_env(self, env_id: str) -> None:
        self._values.setdefault(env_id, None)
        self._origin.setdefault(env_id, None)

    def copy(self, env_id: str, value: str) -> None:
        for other in self._values:
            self._values[other] = value
            self._origin[other] = env_id
        self.events.append(HandoffEvent(from_env=env_id, to_env=None, value=value))

    def peek(self, env_id: str) -> str | None:
        return self._values.get(env_id)

    def origin(self, env_id: str) -> str | None:
        return self._origin.get(env_id)

    def record_transfer(self, from_env: str, to_env: str, value: str, artifact_type: str | None = None) -> None:
        self.events.append(
            HandoffEvent(from_env=from_env, to_env=to_env, value=value, artifact_type=artifact_type)
        )
