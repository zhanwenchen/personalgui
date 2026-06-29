"""Catalog fin_04: authorize a rent transfer on the desktop bank portal using the phone
2FA code.

The bank portal sits in an "awaiting code" state on the desktop; the live one-time code
appears only in the phone authenticator. The code must cross android_phone ->
windows_desktop verbatim.

Primary metric: handoff_correctness (the 6-digit code crosses phone -> desktop intact).
Secondary: global_success (portal status flips to authenticated), routing_accuracy.

See catalog/finance_expenses/fin_04_transfer-2fa-code.md
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

OTP_CODE = "508134"


def build_fin_04_task(otp_code: str = OTP_CODE) -> Task:
    return Task(
        task_id="fin_04_v0_01",
        request="Authorize the rent transfer in the bank portal — it needs the code from my authenticator.",
        user=SyntheticUser(
            name="alex",
            constraints={"bank_device": "windows_desktop", "twofa_device": "android_phone"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="bank_portal",
                        type="MockExpensePortalApp",
                        display_name="Bank Portal — Authorize transfer",
                        initial_state={
                            "otp_field": "",
                            "status": "awaiting_otp",
                            "expected_code": otp_code,
                        },
                    ),
                ],
                initial_focus_app="bank_portal",
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
                    id="read_code",
                    description="Read the 2FA code from the phone authenticator.",
                    required_env="android_phone",
                    required_app="authenticator",
                ),
                Subtask(
                    id="authorize_transfer",
                    description="Enter the code into the desktop bank portal and submit.",
                    required_env="windows_desktop",
                    required_app="bank_portal",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="otp_code",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=otp_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.bank_portal.status": "authenticated",
        },
        initial_focus_env="windows_desktop",
    )
