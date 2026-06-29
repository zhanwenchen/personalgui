"""Catalog wrk_09: mirror the project board's AUTHORITATIVE Atlas milestone deadline onto
the personal phone calendar. A stale #atlas-eng chat names an earlier date; the board wins.

Primary metric: source_of_truth — encoded by requiring the board's "2026-09-04" (via the
handoff expected_value and the calendar event time); the chat's "2026-08-21" is a decoy.
Secondary: handoff_correctness (the board deadline crosses work laptop -> phone),
routing_accuracy (read on windows_desktop, write on android_phone).

See catalog/work_docs_projects/wrk_09_mirror_deadline_to_calendar.md
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

AUTHORITATIVE_DEADLINE = "2026-09-04"  # locked on the project board
STALE_DEADLINE = "2026-08-21"          # older chat date (decoy)
EVENT_TITLE = "Atlas Beta cutoff"


def build_wrk_09_task(deadline: str = AUTHORITATIVE_DEADLINE) -> Task:
    return Task(
        task_id="wrk_09_v0_01",
        request="Put the Atlas milestone deadline on my personal calendar as an event so I don't miss it.",
        user=SyntheticUser(
            name="alex",
            constraints={"authoritative_source": "project_board"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Work Laptop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="project_board",
                        type="MockProfileApp",
                        display_name="Atlas — Project Board (Milestones)",
                        initial_state={
                            "title": "Atlas — Project Board (Milestones)",
                            "name": "Atlas — Project Board (Milestones)",
                            "fields": {
                                "milestone": "Beta cutoff",
                                "deadline": deadline,
                                "status": "locked",
                            },
                            "last_updated": "2026-06-25",
                        },
                    ),
                    AppSpec(
                        id="atlas_chat",
                        type="MockChatApp",
                        display_name="#atlas-eng",
                        initial_state={
                            "title": "#atlas-eng",
                            "channel": "#atlas-eng",
                            "composable": False,
                            # Stale decoy date, easier to read at a glance.
                            "messages": [
                                {"sender": "Sam", "ts": "3 weeks ago",
                                 "text": f"target beta cutoff is Aug 21 ({STALE_DEADLINE})"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="project_board",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_calendar",
                        type="MockGoogleCalendarApp",
                        display_name="Google Calendar",
                        initial_state={
                            "events": [{"title": "Dentist", "time": "2026-07-02 10:00"}],
                            "draft_title": "",
                            "draft_time": "",
                            "expected_titles": [EVENT_TITLE],
                            "sync_status": "pending",
                        },
                    ),
                ],
                initial_focus_app="phone_calendar",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_deadline",
                    description="Read the locked milestone deadline from the project board.",
                    required_env="windows_desktop",
                    required_app="project_board",
                ),
                Subtask(
                    id="add_event",
                    description="Create the milestone event on the personal calendar at the board's date.",
                    required_env="android_phone",
                    required_app="phone_calendar",
                    depends_on=["read_deadline"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="deadline",
                    from_env="windows_desktop",
                    to_env="android_phone",
                    expected_value=deadline,
                ),
            ],
        ),
        desired_final_state={
            "android_phone.phone_calendar.sync_status": "synced",
        },
        initial_focus_env="windows_desktop",
    )
