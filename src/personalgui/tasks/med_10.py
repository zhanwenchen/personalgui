"""Catalog med_10: confirm a cloud photo backup on the desktop using a one-time code the
phone authenticator displays. Phone -> desktop value handoff into a generic web form.

The authenticator view also shows a countdown timer / account id as decoys; only the exact
code (with its hyphen) matches the form's expected_fields.

Primary metric: handoff_correctness. Secondary: global_success, routing_accuracy.

See catalog/media_files/med_10_photo_backup_confirmation_code.md
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

BACKUP_CODE = "491-302"


def build_med_10_task(backup_code: str = BACKUP_CODE) -> Task:
    return Task(
        task_id="med_10_v0_01",
        request="Confirm the photo backup on the desktop using the code my phone shows.",
        user=SyntheticUser(name="alex", constraints={"backup_device": "windows_desktop"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="backup_form",
                        type="MockBrowserFormApp",
                        display_name="Confirm photo backup",
                        initial_state={
                            "title": "Confirm photo backup",
                            "hint": "Enter the confirmation code shown on your phone.",
                            "success_text": "Photo backup confirmed.",
                            "fields": {"confirm_code": ""},
                            "field_types": {"confirm_code": "text"},
                            "expected_fields": {"confirm_code": backup_code},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="backup_form",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_auth",
                        type="MockAuthenticatorApp",
                        display_name="Authenticator",
                        initial_state={"otp_code": backup_code},
                    ),
                ],
                initial_focus_app="phone_auth",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_code",
                    description="Read the confirmation code from the phone authenticator.",
                    required_env="android_phone",
                    required_app="phone_auth",
                ),
                Subtask(
                    id="confirm_backup",
                    description="Paste the code into the desktop backup confirmation form and submit.",
                    required_env="windows_desktop",
                    required_app="backup_form",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="confirmation_code",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=backup_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.backup_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
