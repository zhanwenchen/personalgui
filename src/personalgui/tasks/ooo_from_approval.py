"""Catalog sch_02: set email out-of-office for the approved leave dates, read from an HR
approval email. Distinct from the implemented ooo_setup task (which sources dates from a
calendar): here the dates come from an email thread, and a decoy "team offsite" email
tempts the agent to block the wrong, longer range.

Primary metric: handoff_correctness (the approved start date crosses email body -> OOO
field intact). Secondary: global_success (ooo_enabled plus the exact start/end dates).

See catalog/scheduling_calendar/sch_02_ooo_from_approval.md
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

LEAVE_START = "2026-07-06"
LEAVE_END = "2026-07-10"


def build_ooo_from_approval_task(
    start_date: str = LEAVE_START, end_date: str = LEAVE_END
) -> Task:
    approval_body = (
        "Good news — your paid time-off request is approved.\n\n"
        f"  Approved leave: {start_date} through {end_date}\n\n"
        "Please set your out-of-office before you go."
    )
    # Decoy: a later, longer offsite range that should NOT become the OOO window.
    offsite_body = (
        "Team offsite planning: hold 2026-07-13 to 2026-07-17 on your calendar. "
        "Optional; not part of your leave."
    )
    return Task(
        task_id="ooo_from_approval_v0_01",
        request="Set my email out-of-office for my approved time off.",
        user=SyntheticUser(name="alex"),
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
                                    "id": "leave_approved",
                                    "sender": "HR Time-off",
                                    "subject": "Your time-off request is approved",
                                    "ts": "today 8:15",
                                    "body": approval_body,
                                },
                                {
                                    "id": "offsite",
                                    "sender": "Team Events",
                                    "subject": "Team offsite — hold these dates",
                                    "ts": "yesterday",
                                    "body": offsite_body,
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
                    id="read_approved_dates",
                    description="Open the HR approval email to read the approved leave dates.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="enable_ooo",
                    description="Set the OOO start/end to the approved dates and turn it on.",
                    required_env="windows_desktop",
                    required_app="email",
                    depends_on=["read_approved_dates"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="date",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=start_date,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.email.ooo_enabled": True,
            "windows_desktop.email.ooo_start_field": start_date,
            "windows_desktop.email.ooo_end_field": end_date,
        },
        initial_focus_env="windows_desktop",
    )
