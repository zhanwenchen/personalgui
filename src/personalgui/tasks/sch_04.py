"""Catalog sch_04: mirror one work meeting to the personal calendar, keep the decoy.

Exactly one work meeting ("Client Review") should be copied to the shared personal Google
Calendar. A same-named "Client Review prep" entry already sits on the personal calendar and
must be left alone. The real title is only visible after signing in to Outlook on the work
laptop; the add must happen on the personal laptop.

Primary metric: routing_accuracy (read on work_laptop/outlook, add on
personal_laptop/google_calendar). Secondary: handoff_correctness (the "Client Review" title
crosses work_laptop -> personal_laptop), global_success (sync_status == synced).

See catalog/scheduling_calendar/sch_04_mirror_single_event.md
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

MEETING_TITLE = "Client Review"
WORK_USER = "alex@work.example"
WORK_PASS = "Hunter2-work!"


def build_sch_04_task(meeting_title: str = MEETING_TITLE) -> Task:
    return Task(
        task_id="sch_04_v0_01",
        request="Add my Friday client review to my personal calendar so my partner can see I'm busy.",
        user=SyntheticUser(
            name="alex",
            constraints={"work_account": WORK_USER, "personal_calendar": "google"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="work_laptop",
                display_name="Work Laptop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="outlook",
                        type="MockOutlookApp",
                        display_name="Outlook",
                        initial_state={
                            "status": "signed_out",
                            "expected_username": WORK_USER,
                            "expected_password": WORK_PASS,
                            "username_field": "",
                            "password_field": "",
                            "events": [
                                {"title": meeting_title, "time": "3:00 PM", "date": "2026-07-03"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="outlook",
            ),
            EnvironmentSpec(
                id="personal_laptop",
                display_name="Personal Laptop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="google_calendar",
                        type="MockGoogleCalendarApp",
                        display_name="Google Calendar",
                        initial_state={
                            # Decoy: a same-named "prep" entry already present at home.
                            "events": [
                                {"title": "Client Review prep", "time": "19:00"},
                                {"title": "Yoga", "time": "07:00"},
                            ],
                            "draft_title": "",
                            "draft_time": "",
                            "sync_status": "syncing",
                            "expected_titles": [meeting_title],
                        },
                    ),
                ],
                initial_focus_app="google_calendar",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="sign_in_outlook",
                    description="Sign in to Outlook on the work laptop.",
                    required_env="work_laptop",
                    required_app="outlook",
                ),
                Subtask(
                    id="read_meeting",
                    description="Read the single 'Client Review' event title.",
                    required_env="work_laptop",
                    required_app="outlook",
                    depends_on=["sign_in_outlook"],
                ),
                Subtask(
                    id="add_to_google",
                    description="Add exactly 'Client Review' to Google Calendar.",
                    required_env="personal_laptop",
                    required_app="google_calendar",
                    depends_on=["read_meeting"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="event_title",
                    from_env="work_laptop",
                    to_env="personal_laptop",
                    expected_value=meeting_title,
                ),
            ],
        ),
        desired_final_state={
            "personal_laptop.google_calendar.sync_status": "synced",
        },
        initial_focus_env="work_laptop",
    )
