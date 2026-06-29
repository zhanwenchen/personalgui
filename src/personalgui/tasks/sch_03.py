"""Catalog sch_03: set a reminder at the chat-confirmed time, not the stale calendar time.

The personal calendar still lists the photographer call at 2:00 PM, but a later chat
message moved it to 3:30 PM and Alex agreed. The agent must set the reminder for the
authoritative 15:30 (and do the 12h -> 24h conversion), not the stale 14:00.

Primary metric: source_of_truth (15:30 is the value expected_time / desired_final_state
requires; the stale 14:00 fails). Secondary: handoff_correctness (the agreed time carried
into the reminder within the desktop), global_success (status saved & time_field == 15:30).

See catalog/scheduling_calendar/sch_03_reminder_authoritative_chat.md
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

STALE_TIME = "2:00 PM"  # phone calendar decoy
CONFIRMED_TIME_24H = "15:30"  # authoritative, after 12h->24h conversion


def build_sch_03_task(expected_time: str = CONFIRMED_TIME_24H) -> Task:
    return Task(
        task_id="sch_03_v0_01",
        request="Set me a reminder for the photographer call this afternoon.",
        user=SyntheticUser(
            name="alex",
            constraints={
                "trust_order": "the most recent message in the thread overrides the calendar entry"
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
                            # Stale decoy: recent-looking but pre-dates the chat re-negotiation.
                            "events": [
                                {
                                    "title": "Photographer call",
                                    "time": STALE_TIME,
                                    "last_updated": "this morning",
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
                        id="chat",
                        type="MockChatApp",
                        display_name="Chat — Photographer",
                        initial_state={
                            "title": "Chat — Jamie (Photographer)",
                            "channel": "Jamie Okafor",
                            "composable": False,
                            "messages": [
                                {"sender": "Jamie", "ts": "this morning",
                                 "text": "Looking forward to our 2:00 call today."},
                                {"sender": "Jamie", "ts": "40 min ago",
                                 "text": "Sorry, can we push to 3:30 PM?"},
                                {"sender": "you", "ts": "38 min ago", "text": "works"},
                            ],
                        },
                    ),
                    AppSpec(
                        id="reminder_app",
                        type="MockReminderApp",
                        display_name="Reminders",
                        initial_state={
                            "reminders": [
                                {"time": "08:00", "note": "Stretch"},
                                {"time": "12:30", "note": "Lunch"},
                            ],
                            "time_field": "",
                            "note_field": "",
                            "status": "drafting",
                            "expected_time": expected_time,
                        },
                    ),
                ],
                initial_focus_app="chat",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_chat_time",
                    description="Read the latest agreed time (3:30 PM) from the chat thread.",
                    required_env="windows_desktop",
                    required_app="chat",
                ),
                Subtask(
                    id="set_reminder",
                    description="Save a reminder for 15:30.",
                    required_env="windows_desktop",
                    required_app="reminder_app",
                    depends_on=["read_chat_time"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="time",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=expected_time,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.reminder_app.status": "saved",
            "windows_desktop.reminder_app.time_field": expected_time,
        },
        initial_focus_env="windows_desktop",
    )
