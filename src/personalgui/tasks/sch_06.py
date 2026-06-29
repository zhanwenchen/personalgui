"""Catalog sch_06: store the investor call in local time after a timezone conversion.

The email quotes the call at 11:00 AM PT; Alex is in ET, so the local time is 14:00. The
reminder must store the converted 14:00, not the raw 11:00 that pastes cleanly off the
email (nor the 08:00 West-Coast decoy).

Primary metric: source_of_truth (14:00 is the value expected_time / desired_final_state
requires; raw 11:00 and 08:00 both fail). Secondary: handoff_correctness (the converted
time carried into the reminder), global_success (status saved & time_field == 14:00).

See catalog/scheduling_calendar/sch_06_timezone_convert.md
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

LOCAL_TIME_24H = "14:00"  # authoritative: 11:00 AM PT == 2:00 PM ET


def build_sch_06_task(expected_time: str = LOCAL_TIME_24H) -> Task:
    email_body = (
        "Investor call confirmed for Thursday.\n\n"
        "Start time: 11:00 AM PT (8:00 AM if you're on the West Coast — ignore, that's a typo).\n\n"
        "Dial-in details to follow. Please add it to your calendar."
    )
    return Task(
        task_id="sch_06_v0_01",
        request="Set a reminder for the investor call — the email has the time.",
        user=SyntheticUser(
            name="alex",
            constraints={"home_timezone": "America/New_York (ET)"},
        ),
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
                                    "id": "investor_call",
                                    "sender": "Riverstone Capital",
                                    "subject": "Investor call — Thursday",
                                    "ts": "today 6:50",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                    AppSpec(
                        id="reminder_app",
                        type="MockReminderApp",
                        display_name="Reminders",
                        initial_state={
                            "reminders": [
                                {"time": "09:00", "note": "Inbox review"},
                            ],
                            "time_field": "",
                            "note_field": "",
                            "status": "drafting",
                            "expected_time": expected_time,
                        },
                    ),
                ],
                initial_focus_app="email",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_call_time",
                    description="Read 11:00 AM PT from the email.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="set_reminder_local",
                    description="Convert to ET (14:00) and save the reminder.",
                    required_env="windows_desktop",
                    required_app="reminder_app",
                    depends_on=["read_call_time"],
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
