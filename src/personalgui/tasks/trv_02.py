"""Catalog trv_02: add flight and hotel itinerary events from an email to the calendar.

Single desktop environment. One confirmation email bundles outbound flight, return flight,
and a hotel stay; none are on the calendar. Within-desktop handoffs carry each leg's time
from the email into the calendar's draft_time input.

Primary metric: handoff_correctness (each leg's time crosses email -> calendar intact).
Secondary: global_success (sync_status flips to synced once all three titles present),
routing_accuracy.

Adaptation: titles are normalized event names the agent must produce; the pre-existing
"Dentist" event must remain. Modeled with MockEmailApp + MockGoogleCalendarApp.

See catalog/travel/trv_02_itinerary-to-calendar.md
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

OUTBOUND_TIME = "2026-07-10 08:40"
RETURN_TIME = "2026-07-13 18:05"
HOTEL_TIME = "2026-07-10"

OUTBOUND_TITLE = "Aerolux AX610 to Denver"
RETURN_TITLE = "Aerolux AX617 home"
HOTEL_TITLE = "Cascade Suites check-in"


def build_trv_02_task() -> Task:
    itinerary_body = (
        "Your Denver itinerary is confirmed.\n\n"
        f"  Outbound AX610 DEN {OUTBOUND_TIME}, seat 12A.\n"
        f"  Return AX617 {RETURN_TIME}, frequent-flyer AL-4471.\n"
        f"  Hotel: Cascade Suites, check-in {HOTEL_TIME}.\n\n"
        "Have a great trip."
    )
    return Task(
        task_id="trv_02_v0_01",
        request="Put my Denver trip flights and hotel on my calendar.",
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
                                    "id": "it1",
                                    "sender": "Aerolux",
                                    "subject": "Your Denver itinerary",
                                    "ts": "today 9:00",
                                    "body": itinerary_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                    AppSpec(
                        id="gcal",
                        type="MockGoogleCalendarApp",
                        display_name="Google Calendar",
                        initial_state={
                            "events": [{"title": "Dentist", "time": "2026-07-02 09:00"}],
                            "draft_title": "",
                            "draft_time": "",
                            "expected_titles": [
                                OUTBOUND_TITLE,
                                RETURN_TITLE,
                                HOTEL_TITLE,
                            ],
                            "sync_status": "pending",
                        },
                    ),
                ],
                initial_focus_app="gcal",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_itinerary",
                    description="Open the itinerary email and read the three legs.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="add_outbound",
                    description="Add the outbound flight event.",
                    required_env="windows_desktop",
                    required_app="gcal",
                    depends_on=["read_itinerary"],
                ),
                Subtask(
                    id="add_return",
                    description="Add the return flight event.",
                    required_env="windows_desktop",
                    required_app="gcal",
                    depends_on=["read_itinerary"],
                ),
                Subtask(
                    id="add_hotel",
                    description="Add the hotel check-in event.",
                    required_env="windows_desktop",
                    required_app="gcal",
                    depends_on=["read_itinerary"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="event_time",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=OUTBOUND_TIME,
                ),
                HandoffRequirement(
                    artifact_type="event_time",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=RETURN_TIME,
                ),
                HandoffRequirement(
                    artifact_type="event_time",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=HOTEL_TIME,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.gcal.sync_status": "synced",
        },
        initial_focus_env="windows_desktop",
    )
