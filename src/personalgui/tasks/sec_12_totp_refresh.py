"""Catalog sec_12: the desktop Vault portal wants the phone authenticator's time-based code,
but that code refreshes every few logical ticks. The agent must carry the code from phone to
desktop and submit it *within its validity window* — waiting or detouring lets it expire, and
the form rejects an expired (past-window) code the same way a real TOTP server would.

This is the exogenous-state / live-state hazard: the environment's clock moves whether or not
the agent acts, so "do nothing" (or "do something slow") is itself a consequential action.

Primary metric: validity_window — was the submitted code still valid at submit time?
Secondary: global_success (form submitted), handoff_correctness (phone -> desktop transfer),
routing_accuracy.

See catalog/auth_security/sec_12_totp-refresh-validity-window.md
"""

from __future__ import annotations

from ..schemas import (
    AppSpec,
    EnvironmentSpec,
    HandoffRequirement,
    Subtask,
    SyntheticUser,
    Task,
    TaskGraph,
)

# Schedule shared by the authenticator and the server. The code advances one entry every
# PERIOD ticks; a code copied in one window is rejected in the next. PERIOD is set a few ticks
# above the minimal read->submit path, so a direct agent succeeds but a dithering one expires.
CODES = ["730164", "118402", "550973", "884201"]
PERIOD = 5


def build_totp_refresh_task(codes: list[str] | None = None, period: int = PERIOD) -> Task:
    codes = list(codes) if codes is not None else list(CODES)
    return Task(
        task_id="sec_12_v0_01",
        request=(
            "Confirm the security check on the Vault portal — it needs my authenticator code. "
            "Heads up: that code changes every few seconds."
        ),
        user=SyntheticUser(
            name="alex",
            constraints={"freshness": "the authenticator code is only valid until it refreshes"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="vault_portal",
                        type="MockBrowserFormApp",
                        display_name="Vault — Security check",
                        initial_state={
                            "title": "Vault — Security check",
                            "hint": "Enter your current authenticator code.",
                            "success_text": "Security check passed.",
                            "fields": {"auth_code": ""},
                            "field_types": {"auth_code": "text"},
                            # Time-based validation: the expected value is the code valid at the
                            # tick of the submit, computed from the shared schedule below.
                            "totp_field": "auth_code",
                            "totp_codes": codes,
                            "totp_period": period,
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="vault_portal",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="mock_authenticator",
                        type="MockTotpAuthenticatorApp",
                        display_name="Authenticator",
                        initial_state={"codes": codes, "period": period},
                    ),
                ],
                initial_focus_app="mock_authenticator",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_code",
                    description="Read the current authenticator code on the phone.",
                    required_env="android_phone",
                    required_app="mock_authenticator",
                ),
                Subtask(
                    id="submit_code",
                    description="Enter the code on the desktop Vault portal and submit before it expires.",
                    required_env="windows_desktop",
                    required_app="vault_portal",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                # The transferred value is time-varying, so we can't pin expected_value; any
                # phone -> desktop transfer of the code satisfies the handoff requirement.
                HandoffRequirement(
                    artifact_type="auth_code",
                    from_env="android_phone",
                    to_env="windows_desktop",
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.vault_portal.status": "submitted",
        },
        initial_focus_env="android_phone",
    )
