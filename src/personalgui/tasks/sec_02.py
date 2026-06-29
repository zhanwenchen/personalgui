"""Catalog sec_02: carry a recovery code from the desktop email into the desktop
account-recovery web form (within-desktop, cross-app handoff; no phone).

Nimbus Drive's "Recover your account" page waits on the desktop with a single recovery-code
field; the provider just emailed a six-character code. The agent opens the email, reads the
code, and pastes it into the recovery form on the same windows_desktop.

Primary metric: handoff_correctness — encoded by a within-env required_handoff carrying the
recovery code as expected_value. Secondary: global_success (form submitted), routing_accuracy.

See catalog/auth_security/sec_02_recovery-email-code.md
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

RECOVERY_CODE = "R7K2Q9"   # the recovery code (correct)
TICKET_DECOY = "48120"     # support ticket number, co-located, not the code


def build_sec_02_task(recovery_code: str = RECOVERY_CODE) -> Task:
    email_body = (
        "We received a request to recover your Nimbus Drive account.\n\n"
        f"Your recovery code is {recovery_code} (support ticket #{TICKET_DECOY}). "
        "This code expires in 15 minutes.\n\n"
        "Enter it on the recovery page to finish."
    )
    return Task(
        task_id="sec_02_v0_01",
        request="I locked myself out of Nimbus Drive — finish the account recovery, the code's in my email.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="recovery_form",
                        type="MockBrowserFormApp",
                        display_name="Nimbus Drive — Recover your account",
                        initial_state={
                            "title": "Nimbus Drive — Recover your account",
                            "hint": "Enter the recovery code we emailed you.",
                            "success_text": "Account recovered.",
                            "fields": {"recovery_code": ""},
                            "field_types": {"recovery_code": "text"},
                            "expected_fields": {"recovery_code": recovery_code},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                    AppSpec(
                        id="email",
                        type="MockEmailApp",
                        display_name="Email",
                        initial_state={
                            "title": "Email",
                            "threads": [
                                {
                                    "id": "nimbus_recovery",
                                    "sender": "Nimbus Drive",
                                    "subject": "Recover your account",
                                    "ts": "just now",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="recovery_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_recovery_code",
                    description="Open the Nimbus recovery email and read the recovery code.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="submit_recovery",
                    description="Enter the recovery code on the desktop recovery form and submit.",
                    required_env="windows_desktop",
                    required_app="recovery_form",
                    depends_on=["read_recovery_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="recovery_code",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=recovery_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.recovery_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
