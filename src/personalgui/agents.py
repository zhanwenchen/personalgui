"""Agent adapter contract + two scripted baselines for the v0 vertical slice."""

from __future__ import annotations

from typing import Any

from .schemas import Action, Event, Observation


class Agent:
    """Adapter contract that external agent systems implement."""

    def setup(self, task_id: str, request: str, environments: list[dict[str, Any]]) -> None:
        pass

    def act(
        self, observation: Observation, history: list[tuple[Observation, Action, Event]]
    ) -> Action:
        raise NotImplementedError


class ScriptedOracleAgent(Agent):
    """Hard-coded perfect solution for the authenticator-handoff task. Exists to prove the
    pipeline can grade a success end-to-end. NOT a real agent."""

    _OTP_PLACEHOLDER = "__OTP__"

    def setup(self, task_id, request, environments):
        self._plan: list[Action] = [
            Action(environment_id="android_phone", type="open_app", target="mock_authenticator"),
            Action(environment_id="android_phone", type="copy_value", value=self._OTP_PLACEHOLDER),
            Action(environment_id="windows_desktop", type="open_app", target="expense_portal"),
            Action(environment_id="windows_desktop", type="paste_value", target="otp"),
            Action(environment_id="windows_desktop", type="click", target="submit"),
            Action(environment_id="windows_desktop", type="declare_done"),
        ]
        self._idx = 0
        self._observed_otp: str | None = None

    def act(self, observation, history):
        if self._observed_otp is None and observation.app_id == "mock_authenticator":
            self._observed_otp = observation.visible_state.get("code_visible")

        action = self._plan[self._idx]
        self._idx += 1
        if action.value == self._OTP_PLACEHOLDER:
            action = Action(
                environment_id=action.environment_id,
                type=action.type,
                target=action.target,
                value=self._observed_otp or "",
            )
        return action


class ScriptedNaiveAgent(Agent):
    """Never visits the phone; guesses an OTP directly on the desktop portal.
    Should fail global_success and show 0% handoff_correctness."""

    def setup(self, task_id, request, environments):
        self._plan: list[Action] = [
            Action(environment_id="windows_desktop", type="type", target="otp", value="0000"),
            Action(environment_id="windows_desktop", type="click", target="submit"),
            Action(environment_id="windows_desktop", type="declare_done"),
        ]
        self._idx = 0

    def act(self, observation, history):
        action = self._plan[self._idx]
        self._idx += 1
        return action
