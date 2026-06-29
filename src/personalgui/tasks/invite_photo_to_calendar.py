"""Catalog sch_10: add a calendar event from a phone photo of a paper invite.

The event title and date are copyable off a phone invite photo; the editable calendar is
on the personal laptop. Two phone -> personal_laptop handoffs (title + date).

Primary metric: handoff_correctness. Secondary: routing_accuracy, global_success.

See catalog/scheduling_calendar/sch_10_invite_from_photo.md
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

EVENT_TITLE = "Priya & Sam's Wedding"
EVENT_DATE = "2026-09-12"
RSVP_DECOY = "2026-08-01"  # RSVP-by date shown nearby; not the event date


def build_invite_photo_to_calendar_task(
    event_title: str = EVENT_TITLE, event_date: str = EVENT_DATE
) -> Task:
    return Task(
        task_id="invite_photo_to_calendar_v0_01",
        request="There's a photo of the wedding invite on my phone — put it on my calendar.",
        user=SyntheticUser(name="alex", constraints={"personal_calendar": "google"}),
        environments_spec=[
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="photos",
                        type="MockInvitePhotoApp",
                        display_name="Photos — Invite",
                        initial_state={
                            "title": "Wedding invite",
                            "event_title": event_title,
                            "event_date": event_date,
                            "note": f"RSVP by {RSVP_DECOY}",
                        },
                    ),
                ],
                initial_focus_app="photos",
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
                            "events": [{"title": "Yoga class", "time": "07:00"}],
                            "draft_title": "",
                            "draft_time": "",
                            "sync_status": "syncing",
                            "expected_titles": [event_title],
                        },
                    ),
                ],
                initial_focus_app="google_calendar",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_invite",
                    description="Read the event title and date off the phone invite photo.",
                    required_env="android_phone",
                    required_app="photos",
                ),
                Subtask(
                    id="add_event",
                    description="Add the wedding event to Google Calendar on the personal laptop.",
                    required_env="personal_laptop",
                    required_app="google_calendar",
                    depends_on=["read_invite"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="event_title",
                    from_env="android_phone",
                    to_env="personal_laptop",
                    expected_value=event_title,
                ),
                HandoffRequirement(
                    artifact_type="date",
                    from_env="android_phone",
                    to_env="personal_laptop",
                    expected_value=event_date,
                ),
            ],
        ),
        desired_final_state={
            "personal_laptop.google_calendar.sync_status": "synced",
        },
        initial_focus_env="android_phone",
    )
