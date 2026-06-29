"""Catalog hlth_03: sign into the pharmacy refill portal at the 2FA step using the rotating
one-time code from the phone authenticator. Cross-device handoff (phone -> desktop).

Primary metric: handoff_correctness (the OTP must cross android_phone -> windows_desktop).
Secondary: global_success (portal status flips to authenticated), routing_accuracy.
Adaptation: pharmacy refill 2FA framing; reuses MockAuthenticatorApp (phone OTP) +
MockExpensePortalApp (desktop OTP sign-in form) with health-administrative content.

See catalog/health_wellness/hlth_03_refill-2fa-handoff.md
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

OTP_CODE = "481902"


def build_hlth_03_task(otp_code: str = OTP_CODE) -> Task:
    return Task(
        task_id="hlth_03_v0_01",
        request=(
            "Log into the GreenLeaf Pharmacy site so I can refill my prescription — "
            "it's asking for my 2FA code."
        ),
        user=SyntheticUser(name="alex", constraints={"twofa_device": "android_phone"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="pharmacy_portal",
                        type="MockExpensePortalApp",
                        display_name="GreenLeaf Pharmacy — Sign in",
                        initial_state={
                            "otp_field": "",
                            "expected_code": otp_code,
                            "status": "awaiting_otp",
                        },
                    ),
                ],
                initial_focus_app="pharmacy_portal",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="authenticator",
                        type="MockAuthenticatorApp",
                        display_name="Authenticator",
                        initial_state={"otp_code": otp_code},
                    ),
                ],
                initial_focus_app="authenticator",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_otp",
                    description="Read the rotating 2FA code from the authenticator.",
                    required_env="android_phone",
                    required_app="authenticator",
                ),
                Subtask(
                    id="enter_otp",
                    description="Enter the code in the pharmacy sign-in form and submit.",
                    required_env="windows_desktop",
                    required_app="pharmacy_portal",
                    depends_on=["read_otp"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="otp",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=otp_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.pharmacy_portal.status": "authenticated",
        },
        initial_focus_env="windows_desktop",
    )
