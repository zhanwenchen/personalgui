"""Catalog home_03: set a reminder for a school concert at the authoritative emailed time,
not the stale family-calendar time. Single desktop, three apps.

The family calendar shows 6:00 PM (copied from an old flyer); the school later emailed a
corrected 6:45 PM start. The email also mentions a 6:30 arrival time (a second-time trap).
The reminder must be saved for 18:45.

Primary metric: source_of_truth — encoded by making 18:45 the value expected_time /
desired_final_state requires; the stale 18:00 (and the 18:30 arrival) fail.
Secondary: handoff_correctness (the emailed "6:45 PM" carried into the reminder),
global_success (reminder saved at 18:45).

Adaptation: a child's school concert whose authoritative override arrives by institutional
email, with a start-vs-arrival second-time trap — distinct from standup_reminder.

See catalog/home_family/home_03_school-event-authoritative-time.md
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

STALE_TIME_12H = "6:00 PM"      # decoy (family calendar)
EMAIL_TIME_12H = "6:45 PM"      # authoritative start (carried as handoff value)
ARRIVAL_TIME_12H = "6:30 PM"    # second-time trap
AUTHORITATIVE_TIME_24H = "18:45"


def build_home_03_task() -> Task:
    email_body = (
        "Hello families,\n\n"
        "A quick update on Mia's grade-4 winter concert this Thursday. The program runs "
        f"a little longer than planned, so the concert now begins at {EMAIL_TIME_12H} — "
        f"please arrive by {ARRIVAL_TIME_12H} to find seats. Doors open at 6:15.\n\n"
        "— Maplewood Elementary front office"
    )
    return Task(
        task_id="home_03_v0_01",
        request="Set me a reminder for Mia's school concert.",
        user=SyntheticUser(
            name="alex",
            constraints={"authoritative_source": "the school email overrides the family calendar"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="family_calendar",
                        type="MockCalendarApp",
                        display_name="Family Calendar",
                        initial_state={
                            "title": "Family Calendar",
                            "events": [
                                {
                                    "title": "Mia — school concert",
                                    "time": STALE_TIME_12H,
                                    "last_updated": "3 weeks ago",
                                },
                            ],
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
                                    "id": "school_office",
                                    "sender": "Maplewood Elementary",
                                    "subject": "Concert update — new start time",
                                    "ts": "2 days ago",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                    AppSpec(
                        id="reminder_app",
                        type="MockReminderApp",
                        display_name="Reminders",
                        initial_state={
                            "reminders": [
                                {"time": "08:00", "note": "Trash out"},
                            ],
                            "time_field": "",
                            "note_field": "",
                            "expected_time": AUTHORITATIVE_TIME_24H,
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="email",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_school_email",
                    description="Open the school email and read the corrected start time (6:45 PM).",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="set_reminder",
                    description="Save a reminder for the authoritative start time (18:45).",
                    required_env="windows_desktop",
                    required_app="reminder_app",
                    depends_on=["read_school_email"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="event_time",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=EMAIL_TIME_12H,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.reminder_app.status": "saved",
            "windows_desktop.reminder_app.time_field": AUTHORITATIVE_TIME_24H,
        },
        initial_focus_env="windows_desktop",
    )
