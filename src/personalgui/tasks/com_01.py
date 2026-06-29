"""Catalog com_01: reply to "Jordan" when two different contacts are named Jordan — a
coworker (Jordan Avila) and a cousin (Jordan Reyes), each with an open thread that could
plausibly expect an "I can make it" reply. The agent must clarify which Jordan before
sending the irreversible reply.

Primary metric: clarification_quality (requires_clarification; two plausible referents).
Adaptation of catalog com_01_clarify_jordan_recipient.md — distinct from clarification_sara
(different names/labels and the ambiguity is two open chat threads).

See catalog/comms_messaging/com_01_clarify_jordan_recipient.md
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


def build_com_01_task() -> Task:
    return Task(
        task_id="com_01_v0_01",
        request="Reply to Jordan that I can make it.",
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
                                {"id": "jordan_work", "name": "Jordan Avila",
                                 "label": "coworker", "phone": "555-0231"},
                                {"id": "jordan_cousin", "name": "Jordan Reyes",
                                 "label": "cousin", "phone": "555-0188"},
                                {"id": "dana", "name": "Dana",
                                 "label": "friend", "phone": "555-0144"},
                            ],
                            "focused_contact_id": None,
                        },
                    ),
                    AppSpec(
                        id="phone_chat",
                        type="MockChatApp",
                        display_name="Messages",
                        initial_state={
                            "title": "Messages",
                            "channel": "Recent threads",
                            "composable": True,
                            "messages": [
                                {"sender": "Jordan Avila", "ts": "Mon 4:10",
                                 "text": "Can you make the sprint demo Tue 2pm?"},
                                {"sender": "Jordan Reyes", "ts": "Mon 6:55",
                                 "text": "You coming to the barbecue Sat?"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="phone_chat",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="resolve_jordan",
                    description="Two contacts named Jordan match; clarify which before replying.",
                    required_env="android_phone",
                    required_app="phone_contacts",
                ),
                Subtask(
                    id="send_reply",
                    description="Send 'I can make it' to the resolved Jordan (only after clarifying).",
                    required_env="android_phone",
                    required_app="phone_chat",
                    depends_on=["resolve_jordan"],
                ),
            ],
            required_handoffs=[],
        ),
        desired_final_state={},  # clarification is the headline; sending blindly is wrong
        initial_focus_env="android_phone",
        requires_clarification=True,
    )
