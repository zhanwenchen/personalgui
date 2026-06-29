"""Catalog sch_11: block focus time on the work calendar after a conflict check.

Alex wants a "Focus time" block Wed 2-4 PM, but only if the work window is free. The work
Outlook calendar has Wed meetings at 10:00 and 4:30 — the 2-4 window is clear. A personal
calendar event at 2:30 ("Dentist") looks like a conflict but does not block work focus time
and is the wrong write target. The agent signs in, confirms the work window is free, and
adds the block on the work calendar.

Primary metric: routing_accuracy (the block_focus subtask is pinned to the work calendar;
writing to the personal calendar fails it). Secondary: global_success (the "Focus time"
block exists on the work calendar -> sync_status == synced).

Adaptation: MockOutlookApp is not writable, so the writable WORK calendar is modeled as a
MockGoogleCalendarApp instance on the work_laptop (work account) with
expected_titles=["Focus time"]; a SECOND MockGoogleCalendarApp on the same laptop holds the
personal "Dentist" decoy and is the wrong write target. Outlook stays the read-only
conflict source after sign-in. See catalog/scheduling_calendar/sch_11_block_focus_time.md
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

WORK_USER = "alex@work.example"
WORK_PASS = "Hunter2-work!"
FOCUS_TITLE = "Focus time"


def build_sch_11_task(focus_title: str = FOCUS_TITLE) -> Task:
    return Task(
        task_id="sch_11_v0_01",
        request="If I'm free Wednesday 2–4, block it as focus time on my work calendar.",
        user=SyntheticUser(name="alex", constraints={"work_account": WORK_USER}),
        environments_spec=[
            EnvironmentSpec(
                id="work_laptop",
                display_name="Work Laptop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="outlook",
                        type="MockOutlookApp",
                        display_name="Outlook",
                        initial_state={
                            "status": "signed_out",
                            "expected_username": WORK_USER,
                            "expected_password": WORK_PASS,
                            "username_field": "",
                            "password_field": "",
                            # Wed meetings leave 2-4 PM free.
                            "events": [
                                {"title": "Standup", "time": "10:00 AM"},
                                {"title": "1:1", "time": "4:30 PM"},
                            ],
                        },
                    ),
                    AppSpec(
                        id="work_calendar",
                        type="MockGoogleCalendarApp",
                        display_name="Work Calendar (writable)",
                        initial_state={
                            "events": [],
                            "draft_title": "",
                            "draft_time": "",
                            "sync_status": "syncing",
                            "expected_titles": [focus_title],
                        },
                    ),
                    AppSpec(
                        id="personal_calendar",
                        type="MockGoogleCalendarApp",
                        display_name="Personal Calendar",
                        initial_state={
                            # Non-blocking decoy; also the wrong write target for work focus time.
                            "events": [{"title": "Dentist", "time": "14:30"}],
                            "draft_title": "",
                            "draft_time": "",
                            "sync_status": "syncing",
                            "expected_titles": ["__never__"],
                        },
                    ),
                ],
                initial_focus_app="outlook",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="sign_in_outlook",
                    description="Sign in to the work calendar.",
                    required_env="work_laptop",
                    required_app="outlook",
                ),
                Subtask(
                    id="check_conflict",
                    description="Confirm Wednesday 2–4 PM is free on the work calendar.",
                    required_env="work_laptop",
                    required_app="outlook",
                    depends_on=["sign_in_outlook"],
                ),
                Subtask(
                    id="block_focus",
                    description="Add 'Focus time' Wed 2–4 PM on the work calendar.",
                    required_env="work_laptop",
                    required_app="work_calendar",
                    depends_on=["check_conflict"],
                ),
            ],
            required_handoffs=[],
        ),
        desired_final_state={
            "work_laptop.work_calendar.sync_status": "synced",
        },
        initial_focus_env="work_laptop",
    )
