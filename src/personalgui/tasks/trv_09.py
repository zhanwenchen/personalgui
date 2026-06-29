"""Catalog trv_09: confirm a hotel reservation using the code from the hotel's email.

Single desktop environment, two apps. The reservation code arrived by email; the hotel's
confirmation web form needs it. Within-desktop handoff (copy from email, paste into form).

Primary metric: handoff_correctness (the hyphenated reservation code must cross email ->
form intact). Secondary: global_success (form status flips to submitted), routing_accuracy.

Adaptation: catalog body co-locates the room rate and check-in date with the code; only the
reservation code matches the form. Modeled with MockEmailApp + MockBrowserFormApp.

See catalog/travel/trv_09_hotel-reservation-confirm.md
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

RESERVATION_CODE = "CS-8841-RT"


def build_trv_09_task(reservation_code: str = RESERVATION_CODE) -> Task:
    email_body = (
        "Thanks for booking Cascade Suites. Please confirm your stay on our site within "
        "24 hours.\n\n"
        f"  Reservation code: {reservation_code}. Check-in 2026-07-10. Room rate $189/night.\n\n"
        "Enter your reservation code on the confirmation page to lock in your room."
    )
    return Task(
        task_id="trv_09_v0_01",
        request="Confirm my Cascade Suites reservation on their website.",
        user=SyntheticUser(name="alex", constraints={"booking_device": "windows_desktop"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="hotel_form",
                        type="MockBrowserFormApp",
                        display_name="Cascade Suites — Confirm stay",
                        initial_state={
                            "title": "Cascade Suites — Confirm reservation",
                            "hint": "Enter your reservation code to confirm your stay.",
                            "success_text": "Reservation confirmed.",
                            "fields": {"reservation_code": ""},
                            "field_types": {"reservation_code": "text"},
                            "expected_fields": {"reservation_code": reservation_code},
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
                                    "id": "hk1",
                                    "sender": "Cascade Suites",
                                    "subject": "Confirm your stay",
                                    "ts": "today 10:31",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="hotel_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_code",
                    description="Open the hotel email and read the reservation code.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="confirm_resv",
                    description="Paste the code into the hotel form and submit.",
                    required_env="windows_desktop",
                    required_app="hotel_form",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="reservation_code",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=reservation_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.hotel_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
