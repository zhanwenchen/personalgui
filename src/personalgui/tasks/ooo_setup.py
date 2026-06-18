"""Task H: out-of-office setup.

Turn on email out-of-office for next week's conference. The conference dates come from
the calendar; the OOO toggle + start/end fields live in the email app. The agent must
combine info from two apps to fill one form correctly.
"""

from __future__ import annotations

from ..schemas import (
    AppSpec,
    EnvironmentSpec,
    SyntheticUser,
    Subtask,
    Task,
    TaskGraph,
)

CONFERENCE_START = "2026-05-25"
CONFERENCE_END = "2026-05-27"


def build_ooo_setup_task(
    start_date: str = CONFERENCE_START,
    end_date: str = CONFERENCE_END,
) -> Task:
    return Task(
        task_id="ooo_setup_v0_01",
        request="Turn on email out-of-office for the dates of next week's PersonalGUI Conf.",
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
                            "threads": [],
                            "opened_thread_id": None,
                            "ooo_supported": True,
                            "ooo_enabled": False,
                            "ooo_start_field": "",
                            "ooo_end_field": "",
                            "ooo_message_field": "",
                        },
                    ),
                    AppSpec(
                        id="work_calendar",
                        type="MockCalendarApp",
                        display_name="Calendar",
                        initial_state={
                            "title": "Next week",
                            "events": [
                                {"title": "PersonalGUI Conf · Day 1",
                                 "time": "All day", "date": start_date,
                                 "last_updated": "yesterday"},
                                {"title": "PersonalGUI Conf · Day 2",
                                 "time": "All day", "date": "2026-05-26",
                                 "last_updated": "yesterday"},
                                {"title": "PersonalGUI Conf · Day 3",
                                 "time": "All day", "date": end_date,
                                 "last_updated": "yesterday"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="work_calendar",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_conference_dates",
                    description="Read the conference dates from the calendar.",
                    required_env="windows_desktop",
                    required_app="work_calendar",
                ),
                Subtask(
                    id="enable_ooo",
                    description="Set the email out-of-office with those start and end dates.",
                    required_env="windows_desktop",
                    required_app="email",
                    depends_on=["read_conference_dates"],
                ),
            ],
            # No required_handoffs: the dates can be read visually from the calendar
            # and typed directly into the OOO form — the headline metric is whether
            # the final email.ooo_enabled / start / end match what's in the calendar.
            required_handoffs=[],
        ),
        desired_final_state={
            "windows_desktop.email.ooo_enabled": True,
            "windows_desktop.email.ooo_start_field": start_date,
            "windows_desktop.email.ooo_end_field": end_date,
        },
        initial_focus_env="windows_desktop",
    )
