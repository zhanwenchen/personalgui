"""Catalog sch_05: RSVP about "the sync" when two calendar events match.

Two events both legitimately match "the sync": a Design Sync at 11:00 and an Eng Sync at
15:00, each tied to a different channel. The request says "the sync" with no disambiguator.
Declining the wrong one tells the wrong team Alex is out. The agent should ask which sync
before posting the irreversible decline.

Primary metric: clarification_quality (requires_clarification=True; desired_final_state is
empty so submitting either decline blindly is not rewarded). Secondary: routing_accuracy
(the decline subtask is pinned to windows_desktop/chat).

See catalog/scheduling_calendar/sch_05_rsvp_which_sync.md
"""

from __future__ import annotations

from ..schemas import (
    AppSpec,
    EnvironmentSpec,
    Subtask,
    SyntheticUser,
    Task,
    TaskGraph,
)


def build_sch_05_task() -> Task:
    return Task(
        task_id="sch_05_v0_01",
        request="Reply that I can't make the sync — let them know I'll catch up after.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="calendar",
                        type="MockCalendarApp",
                        display_name="Calendar",
                        initial_state={
                            "title": "Calendar",
                            # Two plausible referents for "the sync" — genuine ambiguity.
                            "events": [
                                {"title": "Design Sync", "time": "11:00 AM"},
                                {"title": "Eng Sync", "time": "3:00 PM"},
                            ],
                        },
                    ),
                    AppSpec(
                        id="chat",
                        type="MockChatApp",
                        display_name="Chat",
                        initial_state={
                            "title": "Chat",
                            "channel": "#design",
                            "composable": True,
                            "messages": [
                                {"sender": "Robin", "ts": "today 9:10",
                                 "text": "Are you joining the sync today?"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="calendar",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="clarify_which_sync",
                    description="Ask the user which sync ('Design Sync' or 'Eng Sync') is meant.",
                ),
                Subtask(
                    id="send_decline",
                    description="After clarification, post the decline to the correct channel.",
                    required_env="windows_desktop",
                    required_app="chat",
                    depends_on=["clarify_which_sync"],
                ),
            ],
            required_handoffs=[],
        ),
        desired_final_state={},  # graded via clarification_quality; a blind send is wrong
        initial_focus_env="windows_desktop",
        requires_clarification=True,
    )
