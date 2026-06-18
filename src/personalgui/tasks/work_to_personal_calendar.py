"""v0 task #4: copy work-calendar events from Outlook (work laptop) to Google Calendar
(personal laptop).

Two laptop environments (both kind=desktop), no phone:
  - work_laptop:    Outlook with sign-in required + work calendar
  - personal_laptop: Google Calendar (read/write) with personal events

The agent must:
  1. Sign in to Outlook with the given credentials
  2. Read the work events
  3. Copy each event title across to the personal laptop
  4. Add matching events to Google Calendar

Notable wrinkles vs the other tasks:
  - Auth flow: wrong credentials fail noisily (persistent error banner). Until auth,
    the work calendar contents are invisible.
  - Multiple required handoffs: one per work event title. Each must cross
    work_laptop -> personal_laptop with the right value.
  - Boundary: the personal_laptop is the canonical personal device. Personal events
    pre-exist in Google Calendar; the agent must NOT remove them.
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

WORK_USERNAME = "alex@work.example"
WORK_PASSWORD = "Standup!2026"

# Work events the agent must copy. Each title is a required handoff value.
WORK_EVENTS = [
    {"title": "Team Standup", "time": "10:00 AM", "date": "Tomorrow"},
    {"title": "Quarterly Review", "time": "2:00 PM", "date": "Tomorrow"},
]


def build_work_to_personal_calendar_task(
    username: str = WORK_USERNAME,
    password: str = WORK_PASSWORD,
    work_events: list[dict] | None = None,
) -> Task:
    work_events = work_events or [dict(ev) for ev in WORK_EVENTS]
    expected_titles = [ev["title"] for ev in work_events]
    return Task(
        task_id="work_to_personal_calendar_v0_01",
        request=(
            f"Mirror tomorrow's work calendar to your personal Google Calendar. "
            f"Sign in to Outlook with {username} / {password}, then add each work event "
            f"to Google Calendar."
        ),
        user=SyntheticUser(name="alex"),
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
                            "username_field": "",
                            "password_field": "",
                            "expected_username": username,
                            "expected_password": password,
                            "events": work_events,
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
                            # Pre-existing personal events. The agent should leave these
                            # alone and only ADD the work events.
                            "events": [
                                {"title": "Yoga class", "time": "07:00"},
                                {"title": "Dinner w/ Sam", "time": "19:00"},
                            ],
                            "draft_title": "",
                            "draft_time": "",
                            "sync_status": "syncing",
                            "expected_titles": expected_titles,
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
                    id="add_events_to_google",
                    description="Add each work event to Google Calendar on the personal laptop.",
                    required_env="personal_laptop",
                    required_app="google_calendar",
                    depends_on=["sign_in_outlook"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="event_title",
                    from_env="work_laptop",
                    to_env="personal_laptop",
                    expected_value=title,
                )
                for title in expected_titles
            ],
        ),
        desired_final_state={
            "personal_laptop.google_calendar.sync_status": "synced",
        },
        initial_focus_env="work_laptop",
    )
