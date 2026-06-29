"""Catalog sec_11: enroll the phone authenticator using a setup key shown on the desktop.

Reverse-direction handoff (desktop -> phone): read the setup key on the desktop 2FA page,
enter it into the phone authenticator to enroll. A decoy account email sits next to the key.

Primary metric: handoff_correctness. Secondary: global_success, routing_accuracy.

See catalog/auth_security/sec_11_enroll-authenticator-desktop-to-phone.md
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

SETUP_KEY = "QSTN-7H4K-2M9P"
ACCOUNT_DECOY = "alex@quillstone.io"


def build_enroll_authenticator_task(setup_key: str = SETUP_KEY) -> Task:
    return Task(
        task_id="enroll_authenticator_v0_01",
        request="Set up my authenticator app for Quillstone — the setup key is on the website.",
        user=SyntheticUser(name="alex", constraints={"authenticator_device": "android_phone"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="twofa_setup",
                        type="MockProfileApp",
                        display_name="Quillstone — Set up 2FA",
                        initial_state={
                            "title": "Quillstone — Set up two-factor",
                            "name": "Two-factor setup",
                            "fields": {
                                "Account": ACCOUNT_DECOY,   # decoy: not the key
                                "Setup key": setup_key,
                            },
                            "last_updated": "just now",
                        },
                    ),
                ],
                initial_focus_app="twofa_setup",
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
                        initial_state={
                            "otp_code": "",
                            "expected_setup_key": setup_key,
                            "setup_key_field": "",
                            "enroll_status": "unenrolled",
                        },
                    ),
                ],
                initial_focus_app="mock_authenticator",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_setup_key",
                    description="Read the setup key on the desktop 2FA page (not the account email).",
                    required_env="windows_desktop",
                    required_app="twofa_setup",
                ),
                Subtask(
                    id="enroll_phone",
                    description="Enter the setup key into the phone authenticator to enroll.",
                    required_env="android_phone",
                    required_app="mock_authenticator",
                    depends_on=["read_setup_key"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="setup_key",
                    from_env="windows_desktop",
                    to_env="android_phone",
                    expected_value=setup_key,
                ),
            ],
        ),
        desired_final_state={
            "android_phone.mock_authenticator.enroll_status": "enrolled",
        },
        initial_focus_env="windows_desktop",
    )
