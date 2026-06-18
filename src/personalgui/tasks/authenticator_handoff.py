"""v0 task: agent must transfer the OTP from the phone authenticator to the desktop expense portal."""

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

DEFAULT_OTP = "4729"


def build_authenticator_handoff_task(otp_code: str = DEFAULT_OTP) -> Task:
    return Task(
        task_id="auth_handoff_v0_01",
        request="Sign in to the expense portal.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="expense_portal",
                        type="MockExpensePortalApp",
                        display_name="Mock Expense Portal",
                        initial_state={
                            "otp_field": "",
                            "status": "awaiting_otp",
                            "expected_code": otp_code,
                        },
                    ),
                ],
                initial_focus_app="expense_portal",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="mock_authenticator",
                        type="MockAuthenticatorApp",
                        display_name="Mock Authenticator",
                        initial_state={"otp_code": otp_code},
                    ),
                ],
                initial_focus_app="mock_authenticator",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_otp",
                    description="Read the one-time code from the phone authenticator.",
                    required_env="android_phone",
                    required_app="mock_authenticator",
                ),
                Subtask(
                    id="submit_otp",
                    description="Enter the code into the desktop expense portal and submit.",
                    required_env="windows_desktop",
                    required_app="expense_portal",
                    depends_on=["read_otp"],
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
            "windows_desktop.expense_portal.status": "authenticated",
        },
        initial_focus_env="windows_desktop",
    )
