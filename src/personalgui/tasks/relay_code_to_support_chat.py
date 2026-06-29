"""Catalog com_04: relay a verification code read on the phone authenticator into a desktop
support chat to confirm identity. Cross-environment handoff (phone -> desktop) whose
landing spot is a chat compose box rather than a form.

Primary metric: handoff_correctness (the code must cross phone -> desktop intact).

See catalog/comms_messaging/com_04_relay-authenticator-code.md
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

VERIFY_CODE = "552087"


def build_relay_code_to_support_chat_task(code: str = VERIFY_CODE) -> Task:
    return Task(
        task_id="relay_code_to_support_chat_v0_01",
        request=(
            "Support is waiting in chat — send them the verification code from your "
            "authenticator so they can confirm it's you."
        ),
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="support_chat",
                        type="MockChatApp",
                        display_name="Support Chat",
                        initial_state={
                            "title": "Support Chat",
                            "channel": "Acme Support",
                            "composable": True,
                            "messages": [
                                {"sender": "Agent (Acme Support)", "ts": "now",
                                 "text": "To verify it's you, please send the code from your authenticator app."},
                            ],
                        },
                    ),
                ],
                initial_focus_app="support_chat",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="mock_authenticator",
                        type="MockAuthenticatorApp",
                        display_name="Authenticator",
                        initial_state={"otp_code": code},
                    ),
                ],
                initial_focus_app="mock_authenticator",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_code",
                    description="View the verification code on the phone authenticator.",
                    required_env="android_phone",
                    required_app="mock_authenticator",
                ),
                Subtask(
                    id="send_code",
                    description="Send the code to support in the desktop chat.",
                    required_env="windows_desktop",
                    required_app="support_chat",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="verification_code",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=code,
                ),
            ],
        ),
        desired_final_state={},  # chat send sets no status field; graded via handoff_correctness
        initial_focus_env="windows_desktop",
    )
