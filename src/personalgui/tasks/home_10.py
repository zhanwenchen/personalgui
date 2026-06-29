"""Catalog home_10: add a family birthday dinner from an invite email to the personal
Google calendar at the confirmed time, without disturbing the existing events. Single
desktop, two apps; within-desktop handoff (email -> calendar draft).

Primary metric: routing_accuracy — the event must be added in the personal Google calendar
(the required app/env for a personal family event).
Secondary: handoff_correctness (the exact title carried into the draft), global_success
(sync_status flips to synced once expected_titles are present).

Adaptation: a family birthday invite from email onto the personal calendar — distinct from
work_to_personal_calendar (moving a work event) and trv itinerary tasks.

See catalog/home_family/home_10_rsvp-family-event-calendar.md
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

EVENT_TITLE = "Grandma's birthday dinner"
EVENT_TIME_24H = "18:30"


def build_home_10_task() -> Task:
    email_body = (
        "You're invited! We're celebrating Grandma's birthday with a dinner on "
        "Saturday, July 11, at 6:30 PM at Rosa's Trattoria. Hope you can make it — "
        "let us know if you're coming."
    )
    return Task(
        task_id="home_10_v0_01",
        request="Add Grandma's birthday dinner to my calendar from the invite email.",
        user=SyntheticUser(name="alex", constraints={"personal_calendar": "google"}),
        environments_spec=[
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
                                    "id": "birthday_invite",
                                    "sender": "Aunt Carol",
                                    "subject": "Grandma's birthday dinner",
                                    "ts": "today 11:00",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                    AppSpec(
                        id="personal_calendar",
                        type="MockGoogleCalendarApp",
                        display_name="Google Calendar",
                        initial_state={
                            # Pre-existing personal events the agent must preserve.
                            "events": [
                                {"title": "Dentist", "time": "09:00"},
                                {"title": "Soccer practice", "time": "17:00"},
                            ],
                            "draft_title": "",
                            "draft_time": "",
                            "sync_status": "pending",
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
                    id="read_invite",
                    description="Open the invite email and read the event title and start time.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="add_event",
                    description="Add 'Grandma's birthday dinner' at 6:30 PM to the personal calendar.",
                    required_env="windows_desktop",
                    required_app="personal_calendar",
                    depends_on=["read_invite"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="event_title",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=EVENT_TITLE,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.personal_calendar.sync_status": "synced",
        },
        initial_focus_env="windows_desktop",
    )
