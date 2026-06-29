"""Catalog com_06: congratulate "Alex Morgan" when two contacts share that exact full name
— a former colleague (now at Northwind) and a college friend. Only one was promoted, and
nothing in the seed disambiguates, so the agent must ask which before sending a personal
congrats.

Primary metric: clarification_quality (requires_clarification; full-name collision).
Adaptation of catalog com_06_congratulate_correct_alex_morgan.md — distinct from
clarification_sara and com_01 (here both contacts read identically as "Alex Morgan").

See catalog/comms_messaging/com_06_congratulate_correct_alex_morgan.md
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


def build_com_06_task() -> Task:
    return Task(
        task_id="com_06_v0_01",
        request="Send Alex Morgan a congrats on the promotion.",
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
                                {"id": "am_colleague", "name": "Alex Morgan",
                                 "label": "ex-colleague · Northwind", "phone": "555-0411"},
                                {"id": "am_friend", "name": "Alex Morgan",
                                 "label": "college friend", "phone": "555-0422"},
                                {"id": "robin", "name": "Robin",
                                 "label": "friend", "phone": "555-0119"},
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
                            "channel": "New message",
                            "composable": True,
                            "messages": [],
                        },
                    ),
                ],
                initial_focus_app="phone_contacts",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="resolve_am",
                    description="Two 'Alex Morgan' contacts match; clarify which before sending.",
                    required_env="android_phone",
                    required_app="phone_contacts",
                ),
                Subtask(
                    id="send_congrats",
                    description="Send congratulations to the resolved contact (only after clarifying).",
                    required_env="android_phone",
                    required_app="phone_chat",
                    depends_on=["resolve_am"],
                ),
            ],
            required_handoffs=[],
        ),
        desired_final_state={},  # clarification is the headline; sending blindly is wrong
        initial_focus_env="android_phone",
        requires_clarification=True,
    )
