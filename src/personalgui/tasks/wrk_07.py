"""Catalog wrk_07: sign in to work Outlook on the work laptop, read this morning's planning
meeting title, then add it as a reminder on the personal phone task list. Titles are
copyable only after sign-in; the 1:1 event is a decoy morning event.

Primary metric: routing_accuracy — sign-in/read on work_laptop (Outlook), reminder on
android_phone (Reminders). Wrong-device placement fails.
Secondary: handoff_correctness (the planning title crosses work_laptop -> android_phone),
global_success (reminder saved at 09:00).

See catalog/work_docs_projects/wrk_07_signin_then_action_items.md
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

MEETING_TITLE = "Atlas Q3 Planning — Followups"
MEETING_TIME = "09:00"
WORK_USER = "alex@northwind.example"
WORK_PASS = "Atlas!2026"


def build_wrk_07_task(meeting_title: str = MEETING_TITLE) -> Task:
    return Task(
        task_id="wrk_07_v0_01",
        request=(
            "Sign in to my work Outlook, find the title of this morning's planning meeting, "
            "and add it as a reminder on my personal task list."
        ),
        user=SyntheticUser(
            name="alex",
            constraints={
                "work_account": WORK_USER,
                "personal_account": "alex@gmail",
            },
        ),
        environments_spec=[
            EnvironmentSpec(
                id="work_laptop",
                display_name="Work Laptop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="work_outlook",
                        type="MockOutlookApp",
                        display_name="Outlook",
                        initial_state={
                            "status": "signed_out",
                            "expected_username": WORK_USER,
                            "expected_password": WORK_PASS,
                            "events": [
                                {"title": meeting_title, "time": MEETING_TIME},
                                {"title": "1:1 with Maya", "time": "11:00"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="work_outlook",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_reminders",
                        type="MockReminderApp",
                        display_name="Reminders",
                        initial_state={
                            "reminders": [{"time": "08:00", "note": "Standup"}],
                            "time_field": "",
                            "note_field": "",
                            "status": "drafting",
                            "expected_time": MEETING_TIME,
                        },
                    ),
                ],
                initial_focus_app="phone_reminders",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="sign_in",
                    description="Sign in to work Outlook with the work credentials.",
                    required_env="work_laptop",
                    required_app="work_outlook",
                ),
                Subtask(
                    id="read_title",
                    description="Read the morning planning meeting's title.",
                    required_env="work_laptop",
                    required_app="work_outlook",
                    depends_on=["sign_in"],
                ),
                Subtask(
                    id="add_reminder",
                    description="Add a reminder on the personal task list with that title.",
                    required_env="android_phone",
                    required_app="phone_reminders",
                    depends_on=["read_title"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="meeting_title",
                    from_env="work_laptop",
                    to_env="android_phone",
                    expected_value=meeting_title,
                ),
            ],
        ),
        desired_final_state={
            "android_phone.phone_reminders.status": "saved",
            "android_phone.phone_reminders.time_field": MEETING_TIME,
        },
        initial_focus_env="work_laptop",
    )
