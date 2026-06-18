"""Task B: clarification — which Sara?

Two contacts share the name "Sara" (one a work coworker, one a personal trainer).
The agent can't unambiguously pick one without asking. The benchmark rewards calling
ask_clarification at least once before any irreversible action.
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


def build_clarification_sara_task() -> Task:
    return Task(
        task_id="clarification_sara_v0_01",
        request="Reply to Sara about lunch.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_contacts",
                        type="MockContactsApp",
                        display_name="Contacts",
                        initial_state={
                            "title": "Contacts",
                            "contacts": [
                                {"id": "sara_work", "name": "Sara Mendez",
                                 "label": "coworker", "phone": "555-0103"},
                                {"id": "sara_trainer", "name": "Sara Lin",
                                 "label": "personal trainer", "phone": "555-0207"},
                                {"id": "jamie", "name": "Jamie", "label": "friend",
                                 "phone": "555-0142"},
                            ],
                        },
                    ),
                    AppSpec(
                        id="phone_chat",
                        type="MockChatApp",
                        display_name="Messages",
                        initial_state={
                            "title": "Messages",
                            "channel": "—",
                            "composable": True,
                            "messages": [],
                            "recipient_id": None,
                        },
                    ),
                ],
                initial_focus_app="phone_contacts",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="resolve_ambiguity",
                    description="The request refers to 'Sara' but two contacts match; the agent must clarify.",
                    required_env="android_phone",
                    required_app="phone_contacts",
                ),
            ],
            required_handoffs=[],
        ),
        desired_final_state={},  # global_success is not the headline metric for this task
        initial_focus_env="android_phone",
        requires_clarification=True,
    )
