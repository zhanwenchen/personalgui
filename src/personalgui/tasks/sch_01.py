"""Catalog sch_01: fix the dentist appointment to the clinic's confirmed date.

The phone calendar holds a stale 2026-07-14 entry; the clinic's email is the system of
record with the rescheduled 2026-07-15 date. The agent must read the authoritative email
date and correct the editable Google Calendar, not mirror the stale phone entry.

Primary metric: source_of_truth (encoded by making 2026-07-15 the value expected_titles /
desired_final_state requires; copying the stale 2026-07-14 leaves sync_status != synced).
Secondary: handoff_correctness (the confirmed date crosses email -> calendar draft within
the desktop), global_success (sync_status == synced).

See catalog/scheduling_calendar/sch_01_dentist_reschedule.md
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

STALE_DATE = "2026-07-14"  # phone calendar decoy (pre-dates the reschedule email)
CONFIRMED_DATE = "2026-07-15"  # authoritative clinic email date
EVENT_TITLE = f"Dentist cleaning · {CONFIRMED_DATE}"


def build_sch_01_task(confirmed_date: str = CONFIRMED_DATE) -> Task:
    email_body = (
        "Appointment update from Bright Smile Dental.\n\n"
        f"Your cleaning has been rescheduled to {confirmed_date} at 9:00 AM. "
        "This confirmation supersedes any earlier date on your calendar.\n\n"
        "Reply to this email if the new time does not work."
    )
    return Task(
        task_id="sch_01_v0_01",
        request="My dentist cleaning got moved — make sure my calendar has the right date.",
        user=SyntheticUser(
            name="alex",
            constraints={
                "trust_order": "clinic confirmation email is authoritative over the phone calendar entry"
            },
        ),
        environments_spec=[
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_calendar",
                        type="MockCalendarApp",
                        display_name="Calendar",
                        initial_state={
                            "title": "Calendar",
                            # Stale decoy: still on the original 07-14 booking.
                            "events": [
                                {
                                    "title": "Dentist cleaning",
                                    "time": STALE_DATE,
                                    "last_updated": "3 weeks ago",
                                },
                            ],
                        },
                    ),
                ],
                initial_focus_app="phone_calendar",
            ),
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="email",
                        type="MockEmailApp",
                        display_name="Email",
                        initial_state={
                            "title": "Email",
                            "threads": [
                                {
                                    "id": "clinic_reschedule",
                                    "sender": "Bright Smile Dental",
                                    "subject": "Your cleaning has been rescheduled",
                                    "ts": "today 7:40",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                    AppSpec(
                        id="google_calendar",
                        type="MockGoogleCalendarApp",
                        display_name="Google Calendar",
                        initial_state={
                            # Pre-existing wrong entry on the stale date.
                            "events": [{"title": "Dentist cleaning", "time": "09:00"}],
                            "draft_title": "",
                            "draft_time": "",
                            "sync_status": "syncing",
                            "expected_titles": [EVENT_TITLE],
                        },
                    ),
                ],
                initial_focus_app="email",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_email_date",
                    description="Open the clinic thread; read the confirmed reschedule date 2026-07-15.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="fix_calendar",
                    description="Correct the Google Calendar entry to the confirmed date.",
                    required_env="windows_desktop",
                    required_app="google_calendar",
                    depends_on=["read_email_date"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="date",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=confirmed_date,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.google_calendar.sync_status": "synced",
        },
        initial_focus_env="android_phone",
    )
