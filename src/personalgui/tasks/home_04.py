"""Catalog home_04: two children have a recital on the same day at different times, so
"the recital" is ambiguous. The agent must ask which child's recital before saving any
reminder. Single desktop, two apps.

Primary metric: clarification_quality (requires_clarification).
Secondary: routing_accuracy.

Adaptation: referent ambiguity across two same-day calendar events for two children, with
a reminder as the downstream action — distinct from clarification_sara (message recipient).

See catalog/home_family/home_04_clarify-which-kids-recital.md
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


def build_home_04_task() -> Task:
    return Task(
        task_id="home_04_v0_01",
        request="Remind me about the recital.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="family_calendar",
                        type="MockCalendarApp",
                        display_name="Family Calendar",
                        initial_state={
                            "title": "Family Calendar",
                            "events": [
                                {"title": "Trash pickup", "time": "8:00 AM"},
                                {"title": "Mia — piano recital", "time": "4:00 PM"},
                                {"title": "Leo — choir recital", "time": "7:00 PM"},
                            ],
                        },
                    ),
                    AppSpec(
                        id="reminder_app",
                        type="MockReminderApp",
                        display_name="Reminders",
                        initial_state={
                            "reminders": [
                                {"time": "09:00", "note": "Call dentist"},
                            ],
                            "time_field": "",
                            "note_field": "",
                            # No single correct time until the child is clarified.
                            "expected_time": None,
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="family_calendar",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="resolve_recital",
                    description="Two recitals today (Mia 4:00 PM, Leo 7:00 PM); clarify which child.",
                    required_env="windows_desktop",
                    required_app="family_calendar",
                ),
                Subtask(
                    id="set_reminder",
                    description="After clarifying, save a reminder for the chosen recital's time.",
                    required_env="windows_desktop",
                    required_app="reminder_app",
                    depends_on=["resolve_recital"],
                ),
            ],
            required_handoffs=[],
        ),
        # Clarification is the headline; saving either reminder blindly is wrong.
        desired_final_state={},
        initial_focus_env="windows_desktop",
        requires_clarification=True,
    )
