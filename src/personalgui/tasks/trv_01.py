"""Catalog trv_01: online check-in using the confirmation code from a booking email.

Single desktop environment, two apps. The airline confirmation code lives in a booking
email; the check-in web form needs it. Within-desktop handoff (copy from email, paste
into form).

Primary metric: handoff_correctness (the exact record locator must cross email -> form).
Secondary: global_success (form status flips to submitted), routing_accuracy.

Adaptation: catalog body co-locates the flight number and seat with the code; only the
six-character confirmation code matches the form. Modeled with MockEmailApp +
MockBrowserFormApp on one desktop.

See catalog/travel/trv_01_online-checkin-confirmation-code.md
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

CONFIRMATION_CODE = "QPZ4K9"


def build_trv_01_task(confirmation_code: str = CONFIRMATION_CODE) -> Task:
    email_body = (
        "Your Aerolux booking is confirmed.\n\n"
        f"  Confirmation code: {confirmation_code}. Flight AX482, 2026-06-29 07:15, seat 14C.\n\n"
        "Online check-in is now open — enter your confirmation code on the check-in page."
    )
    return Task(
        task_id="trv_01_v0_01",
        request="Check me in for my Aerolux flight tomorrow.",
        user=SyntheticUser(name="alex", constraints={"checkin_device": "windows_desktop"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="checkin_form",
                        type="MockBrowserFormApp",
                        display_name="Aerolux — Online check-in",
                        initial_state={
                            "title": "Aerolux check-in",
                            "hint": "Enter your confirmation code to check in.",
                            "success_text": "Checked in. Boarding pass ready.",
                            "fields": {"confirmation_code": ""},
                            "field_types": {"confirmation_code": "text"},
                            "expected_fields": {"confirmation_code": confirmation_code},
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
                                    "id": "bk1",
                                    "sender": "Aerolux",
                                    "subject": "Booking confirmed — AX482",
                                    "ts": "today 6:02",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="checkin_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_code",
                    description="Open the booking email and read the confirmation code.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="submit_checkin",
                    description="Paste the code into the check-in form and submit.",
                    required_env="windows_desktop",
                    required_app="checkin_form",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="confirmation_code",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=confirmation_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.checkin_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
