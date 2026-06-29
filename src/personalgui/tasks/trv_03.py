"""Catalog trv_03: a rebooked flight — use the schedule-change time, not the original.

Single desktop environment. Two emails reference the same flight; the later "schedule
change" email supersedes the original. The agent must put the NEW departure time on the
calendar. Within-desktop handoff carries the authoritative time into the calendar draft.

Primary metric: source_of_truth — encoded by making the new time the value the handoff
requires; the stale original time is a decoy that fails handoff_correctness.
Secondary: handoff_correctness, global_success (sync_status synced).

Adaptation: GoogleCalendar syncs on expected_titles, so source-of-truth is enforced through
the value-checked handoff (expected_value = the new time). The stale email is listed first
to make the decoy tempting. Modeled with MockEmailApp + MockGoogleCalendarApp.

See catalog/travel/trv_03_rebooked-flight-schedule-change.md
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

STALE_TIME = "2026-07-09 07:15"   # decoy — original confirmation
NEW_TIME = "2026-07-09 10:50"     # authoritative — schedule change
EVENT_TITLE = "Aerolux AX482 departure"


def build_trv_03_task(new_time: str = NEW_TIME) -> Task:
    booking_body = (
        "Your Aerolux booking is confirmed.\n\n"
        f"  Flight AX482 — Departs {STALE_TIME}.\n\n"
        "We look forward to flying with you."
    )
    schedule_change_body = (
        "Schedule change for flight AX482.\n\n"
        f"  Your departure has moved to {new_time}. This replaces your earlier time.\n\n"
        "No action needed at the airport; just note the new departure."
    )
    return Task(
        task_id="trv_03_v0_01",
        request="Add my Aerolux departure to my calendar.",
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
                                    "id": "bk1",
                                    "sender": "Aerolux",
                                    "subject": "Booking confirmed — AX482",
                                    "ts": "2026-06-20",
                                    "body": booking_body,
                                },
                                {
                                    "id": "sc1",
                                    "sender": "Aerolux",
                                    "subject": "Schedule change — AX482",
                                    "ts": "2026-06-25",
                                    "body": schedule_change_body,
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
                            "events": [],
                            "draft_title": "",
                            "draft_time": "",
                            "expected_titles": [EVENT_TITLE],
                            "sync_status": "pending",
                        },
                    ),
                ],
                initial_focus_app="email",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="find_authoritative",
                    description="Read both emails; identify the schedule change as current.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="add_event",
                    description="Add the departure event with the new time.",
                    required_env="windows_desktop",
                    required_app="gcal",
                    depends_on=["find_authoritative"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="event_time",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=new_time,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.gcal.sync_status": "synced",
        },
        initial_focus_env="windows_desktop",
    )
