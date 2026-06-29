"""Catalog hlth_08: add a telehealth visit to the personal Google Calendar at the confirmed
time from the confirmation email. Within-desktop handoff (email -> calendar).

Decoy: the email shows both the confirmed 11:00 and an "originally requested 09:30" line,
plus a join URL. Only 11:00 is correct; pre-existing calendar events must be preserved.

Primary metric: routing_accuracy (the personal calendar is the correct surface for a
telehealth visit). Secondary: handoff_correctness (confirmed time crosses email ->
calendar), global_success (calendar sync_status -> synced).
Adaptation: routing a telehealth event to the personal calendar (MockGoogleCalendarApp)
with expected_titles + sync_status synced. Reuses MockEmailApp.

See catalog/health_wellness/hlth_08_telehealth-event-correct-calendar.md
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

CONFIRMED_TIME = "11:00"
ORIGINAL_TIME = "09:30"  # decoy
EVENT_TITLE = "Telehealth visit"


def build_hlth_08_task(confirmed_time: str = CONFIRMED_TIME) -> Task:
    email_body = (
        "NorthStar Telehealth: your video visit is confirmed.\n\n"
        f"  Confirmed for 2026-07-10 at {confirmed_time}.\n"
        f"  (You originally requested {ORIGINAL_TIME}.)\n"
        "  Join link: https://nsth.example/v/8821\n"
    )
    return Task(
        task_id="hlth_08_v0_01",
        request="Put my telehealth visit on my calendar at the time in the confirmation email.",
        user=SyntheticUser(
            name="alex",
            constraints={"personal_calendar": "telehealth visits are personal events"},
        ),
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
                                    "id": "t_telehealth",
                                    "sender": "NorthStar Telehealth",
                                    "subject": "Your video visit is confirmed",
                                    "ts": "today 9:15",
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
                            "events": [
                                {"title": "Gym", "time": "07:00"},
                                {"title": "Book club", "time": "19:00"},
                            ],
                            "draft_title": "",
                            "draft_time": "",
                            "expected_titles": [EVENT_TITLE],
                            "sync_status": "unsynced",
                        },
                    ),
                ],
                initial_focus_app="email",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_confirm",
                    description="Read the confirmed time + visit detail from the email.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="add_event",
                    description="Add the visit to the personal calendar at that time.",
                    required_env="windows_desktop",
                    required_app="personal_calendar",
                    depends_on=["read_confirm"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="time",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=confirmed_time,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.personal_calendar.sync_status": "synced",
        },
        initial_focus_env="windows_desktop",
    )
