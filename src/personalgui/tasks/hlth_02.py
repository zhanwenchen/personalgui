"""Catalog hlth_02: set a reminder for a rescheduled dermatology appointment at the
clinic's authoritative new time (from the phone chat), NOT the stale desktop calendar time.

Source-of-truth: the clinic chat on the phone says 14:15; the desktop calendar still shows
the old 09:30. The reminder app only saves when time_field == "14:15".

Primary metric: source_of_truth — encoded by making the chat time the value the reminder's
expected_time requires; the stale calendar 09:30 is a decoy.
Secondary: handoff_correctness (time crosses phone -> desktop), global_success.
Adaptation: clinic chat (authoritative) vs stale calendar; agent sets a Reminder at the
authoritative time. Reuses MockChatApp + MockCalendarApp + MockReminderApp.

See catalog/health_wellness/hlth_02_reschedule-authoritative-time.md
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

NEW_TIME = "14:15"   # authoritative (clinic chat)
STALE_TIME = "09:30"  # decoy (calendar)


def build_hlth_02_task(new_time: str = NEW_TIME, stale_time: str = STALE_TIME) -> Task:
    return Task(
        task_id="hlth_02_v0_01",
        request="Set a reminder for my dermatology appointment at the new time the clinic gave me.",
        user=SyntheticUser(
            name="alex",
            constraints={"trust_order": "the clinic's chat message is authoritative over the calendar"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="clinic_chat",
                        type="MockChatApp",
                        display_name="Messages",
                        initial_state={
                            "title": "Messages",
                            "channel": "Alphawave Dermatology",
                            "composable": False,
                            "messages": [
                                {"sender": "Alphawave Dermatology", "ts": "today 7:40",
                                 "text": f"Your 2026-07-09 visit is rescheduled to {new_time}. Reply CONFIRM."},
                            ],
                        },
                    ),
                ],
                initial_focus_app="clinic_chat",
            ),
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
                            # Stale: never updated after the clinic moved the appointment.
                            "events": [{"title": "Dermatology", "time": stale_time}],
                        },
                    ),
                    AppSpec(
                        id="reminder",
                        type="MockReminderApp",
                        display_name="Reminders",
                        initial_state={
                            "reminders": [],
                            "time_field": "",
                            "note_field": "",
                            "expected_time": new_time,
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="calendar",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_new_time",
                    description="Read the rescheduled time from the clinic chat.",
                    required_env="android_phone",
                    required_app="clinic_chat",
                ),
                Subtask(
                    id="set_reminder",
                    description="Save a reminder at the new time on the desktop.",
                    required_env="windows_desktop",
                    required_app="reminder",
                    depends_on=["read_new_time"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="time",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=new_time,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.reminder.status": "saved",
        },
        initial_focus_env="windows_desktop",
    )
