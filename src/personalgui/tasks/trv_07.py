"""Catalog trv_07: set the email out-of-office for the exact travel dates from the itinerary.

Single desktop environment. The away window must come from the itinerary email, not a guess;
a decoy "long weekend" thread tempts a wrong date. Within-desktop handoff: dates read from
the itinerary flow into the OOO start/end inputs.

Primary metric: handoff_correctness (the trip start/end must cross intact into OOO fields).
Secondary: global_success (ooo_enabled True), routing_accuracy.

Adaptation: mirrors ooo_setup but ties dates to a travel itinerary with a decoy thread;
distinct seed keeps it from duplicating that task. Modeled with MockEmailApp (ooo_supported).

See catalog/travel/trv_07_ooo-for-travel-dates.md
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

TRIP_START = "2026-07-21"
TRIP_END = "2026-07-26"


def build_trv_07_task(trip_start: str = TRIP_START, trip_end: str = TRIP_END) -> Task:
    itinerary_body = (
        "Here is your itinerary.\n\n"
        f"  Trip: depart {trip_start}, return {trip_end}.\n\n"
        "Safe travels!"
    )
    # Decoy: an unrelated social-plan date that must NOT become the OOO window.
    weekend_body = (
        "Any interest in a long weekend? Penciling in 2026-08-01 if people are around. "
        "Totally optional."
    )
    return Task(
        task_id="trv_07_v0_01",
        request="Turn on my out-of-office for while I'm away.",
        user=SyntheticUser(name="alex", constraints={"ooo_email": "primary"}),
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
                                    "subject": "Your itinerary",
                                    "ts": "today 7:40",
                                    "body": itinerary_body,
                                },
                                {
                                    "id": "pr1",
                                    "sender": "Jordan",
                                    "subject": "Long weekend?",
                                    "ts": "yesterday",
                                    "body": weekend_body,
                                },
                            ],
                            "opened_thread_id": None,
                            "ooo_supported": True,
                            "ooo_enabled": False,
                            "ooo_start_field": "",
                            "ooo_end_field": "",
                            "ooo_message_field": "",
                        },
                    ),
                ],
                initial_focus_app="email",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_dates",
                    description="Read the trip start/end from the itinerary email.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="set_ooo",
                    description="Set the OOO start/end to the trip dates and enable it.",
                    required_env="windows_desktop",
                    required_app="email",
                    depends_on=["read_dates"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="ooo_start",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=trip_start,
                ),
                HandoffRequirement(
                    artifact_type="ooo_end",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=trip_end,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.email.ooo_enabled": True,
            "windows_desktop.email.ooo_start_field": trip_start,
            "windows_desktop.email.ooo_end_field": trip_end,
        },
        initial_focus_env="windows_desktop",
    )
