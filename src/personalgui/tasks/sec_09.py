"""Catalog sec_09: revoke a leaked session by confirming an emailed code on the desktop
security-settings form (within-desktop, cross-app handoff that gates an account-state change).

Auroracast's "Active sessions" page has a "Revoke all other sessions" action that needs an
emailed confirmation code. The agent opens the email, reads the code, and enters it on the
security form to actually revoke. Co-located decoys (a session ID and an IP address) tempt a
naive agent into grabbing the wrong identifier.

Primary metric: handoff_correctness — within-env required_handoff carrying the confirmation
code as expected_value. Secondary: global_success (form flips to submitted), routing_accuracy.

See catalog/auth_security/sec_09_revoke-leaked-session.md
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

CONFIRM_CODE = "365182"        # confirmation code (correct)
SESSION_ID_DECOY = "9F-22A1"   # which session, not the confirmation
IP_DECOY = "203.0.113.44"      # session IP, not the confirmation


def build_sec_09_task(confirm_code: str = CONFIRM_CODE) -> Task:
    email_body = (
        "An unrecognized session was detected on your Auroracast account.\n\n"
        f"Session ID {SESSION_ID_DECOY}, signed in from IP {IP_DECOY}.\n\n"
        f"Confirm session revocation with code {confirm_code} on the security settings page."
    )
    return Task(
        task_id="sec_09_v0_01",
        request="Kick out that unknown session on my Auroracast account — it emailed me a confirmation code.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="security_settings",
                        type="MockBrowserFormApp",
                        display_name="Auroracast — Revoke other sessions",
                        initial_state={
                            "title": "Auroracast — Revoke other sessions",
                            "hint": "Enter the confirmation code we emailed you to revoke.",
                            "success_text": "Other sessions revoked.",
                            "fields": {"confirm_code": ""},
                            "field_types": {"confirm_code": "text"},
                            "expected_fields": {"confirm_code": confirm_code},
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
                                    "id": "auroracast_security",
                                    "sender": "Auroracast Security",
                                    "subject": "Unrecognized session detected",
                                    "ts": "just now",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="security_settings",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_confirm_code",
                    description="Open the Auroracast security email and read the confirmation code.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="revoke_session",
                    description="Enter the code on the security settings form and submit to revoke.",
                    required_env="windows_desktop",
                    required_app="security_settings",
                    depends_on=["read_confirm_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="confirm_code",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=confirm_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.security_settings.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
