"""Catalog trv_04: airline account login needs a 2FA code read from the phone authenticator.

Two environments. The desktop sign-in shows an OTP challenge; the live code is only on the
phone authenticator. Phone -> desktop handoff.

Primary metric: handoff_correctness (the live OTP must cross phone -> desktop intact).
Secondary: global_success (portal flips to authenticated), routing_accuracy.

Adaptation: framed as the Aerolux frequent-flyer portal. Modeled with MockAuthenticatorApp
(phone, copyable otp) + MockExpensePortalApp (desktop OTP sign-in form, reused as the
airline sign-in). Distinct seed values keep it from duplicating auth_handoff.

See catalog/travel/trv_04_airline-login-2fa.md
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

OTP_CODE = "704218"


def build_trv_04_task(otp_code: str = OTP_CODE) -> Task:
    return Task(
        task_id="trv_04_v0_01",
        request="Log me into my Aerolux account on the desktop.",
        user=SyntheticUser(name="alex", constraints={"twofa_device": "android_phone"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="signin",
                        type="MockExpensePortalApp",
                        display_name="Aerolux — Sign in",
                        initial_state={
                            "otp_field": "",
                            "expected_code": otp_code,
                            "status": "awaiting_otp",
                        },
                    ),
                ],
                initial_focus_app="signin",
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
                    description="Read the current 2FA code in the phone authenticator.",
                    required_env="android_phone",
                    required_app="authenticator",
                ),
                Subtask(
                    id="enter_otp",
                    description="Enter the code in the desktop sign-in form and submit.",
                    required_env="windows_desktop",
                    required_app="signin",
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
            "windows_desktop.signin.status": "authenticated",
        },
        initial_focus_env="windows_desktop",
    )
