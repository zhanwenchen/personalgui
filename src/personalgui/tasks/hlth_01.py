"""Catalog hlth_01: confirm a clinic appointment using a confirmation code emailed by the
clinic, typed into the patient-portal web form. Within-desktop handoff (email -> form).

Decoy: a clinic newsletter thread shows a code-shaped "member ID CH-0001"; only the
appointment email's "Confirmation code: CH-4192" is authoritative.

Primary metric: handoff_correctness (the exact code must cross email -> portal form).
Secondary: global_success (form status flips to submitted), routing_accuracy.
Adaptation: relabels the within-desktop email->form carry as a clinic appointment
confirmation; reuses MockEmailApp + MockBrowserFormApp with health-administrative content.

See catalog/health_wellness/hlth_01_confirm-appointment-code.md
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

CONFIRM_CODE = "CH-4192"
DECOY_MEMBER_ID = "CH-0001"  # newsletter footer decoy


def build_hlth_01_task(confirm_code: str = CONFIRM_CODE) -> Task:
    email_body = (
        "Cedar Hollow Family Medicine: please confirm your 2026-07-06 checkup. To lock in "
        "your appointment, enter this confirmation code on the patient portal:\n\n"
        f"  Confirmation code: {confirm_code}\n\n"
        "If you need to reschedule, reply to this email."
    )
    newsletter_body = (
        "Cedar Hollow monthly newsletter. Flu shots are now available. "
        f"Member ID {DECOY_MEMBER_ID}. Front desk: +1-555-0173."
    )
    return Task(
        task_id="hlth_01_v0_01",
        request="Confirm my Cedar Hollow checkup using the code they emailed me.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="portal_form",
                        type="MockBrowserFormApp",
                        display_name="Cedar Hollow — Patient Portal",
                        initial_state={
                            "title": "Cedar Hollow — Confirm appointment",
                            "hint": "Enter the confirmation code from your email.",
                            "success_text": "Appointment confirmed.",
                            "fields": {"confirmation_code": ""},
                            "field_types": {"confirmation_code": "text"},
                            "expected_fields": {"confirmation_code": confirm_code},
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
                                    "id": "t_clinic",
                                    "sender": "Cedar Hollow Family Medicine",
                                    "subject": "Confirm your 2026-07-06 visit",
                                    "ts": "today 8:10",
                                    "body": email_body,
                                },
                                {
                                    "id": "t_news",
                                    "sender": "Cedar Hollow",
                                    "subject": "Cedar Hollow newsletter",
                                    "ts": "yesterday",
                                    "body": newsletter_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="portal_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_code",
                    description="Open the clinic email and read the confirmation code.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="enter_code",
                    description="Enter the code in the portal form and submit.",
                    required_env="windows_desktop",
                    required_app="portal_form",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="code",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=confirm_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.portal_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
