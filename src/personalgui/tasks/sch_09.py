"""Catalog sch_09: resolve a double-booking by keeping the chat-confirmed event.

Two overlapping 1 PM events exist on Google Calendar: "Lunch with Morgan" (confirmed in
chat) and "Vendor demo" (still tentative). Only the chat thread reveals which is confirmed.
The agent must keep "Lunch with Morgan" as the 1 PM entry, not the tentative vendor demo.

Primary metric: source_of_truth ("Lunch with Morgan" is the value expected_titles /
desired_final_state requires; keeping the tentative vendor event fails). Secondary:
global_success (sync_status == synced), handoff_correctness (the confirmed title carried
into the calendar edit within the desktop).

Adaptation: MockGoogleCalendarApp models no deletion, so "keep the right one" is encoded as
ensuring the confirmed title is present — the agent confirms/re-adds "Lunch with Morgan"
(which flips sync_status to synced) and is not lured into making the vendor the canonical
1 PM entry. See catalog/scheduling_calendar/sch_09_double_booking_resolve.md
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

CONFIRMED_TITLE = "Lunch with Morgan"
TENTATIVE_TITLE = "Vendor demo"


def build_sch_09_task(confirmed_title: str = CONFIRMED_TITLE) -> Task:
    return Task(
        task_id="sch_09_v0_01",
        request="I'm double-booked at 1pm — keep the one that's actually confirmed.",
        user=SyntheticUser(
            name="alex",
            constraints={"trust_order": "an event confirmed in chat outranks a tentative one"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="chat",
                        type="MockChatApp",
                        display_name="Chat",
                        initial_state={
                            "title": "Chat",
                            "channel": "1pm conflicts",
                            "composable": False,
                            "messages": [
                                {"sender": "Morgan", "ts": "yesterday",
                                 "text": "Confirmed for 1, see you then!"},
                                {"sender": "Vendor (Acme)", "ts": "this morning",
                                 "text": "Pencil us in for 1 — still tentative on our end."},
                            ],
                        },
                    ),
                    AppSpec(
                        id="google_calendar",
                        type="MockGoogleCalendarApp",
                        display_name="Google Calendar",
                        initial_state={
                            # Both overlapping 1 PM events present; only chat says which is real.
                            "events": [
                                {"title": CONFIRMED_TITLE, "time": "13:00"},
                                {"title": TENTATIVE_TITLE, "time": "13:00"},
                            ],
                            "draft_title": "",
                            "draft_time": "",
                            "sync_status": "syncing",
                            "expected_titles": [confirmed_title],
                        },
                    ),
                ],
                initial_focus_app="chat",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_confirmation",
                    description="Read which 1 PM event is confirmed (Morgan) vs tentative (vendor) in chat.",
                    required_env="windows_desktop",
                    required_app="chat",
                ),
                Subtask(
                    id="keep_confirmed",
                    description="Ensure 'Lunch with Morgan' is the kept 1 PM entry.",
                    required_env="windows_desktop",
                    required_app="google_calendar",
                    depends_on=["read_confirmation"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="event_title",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=confirmed_title,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.google_calendar.sync_status": "synced",
        },
        initial_focus_env="windows_desktop",
    )
