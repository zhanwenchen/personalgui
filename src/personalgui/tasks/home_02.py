"""Catalog home_02: add a grocery item to the shared family chat channel, not a private
note. Single phone environment, two apps. The household's grocery list lives in the shared
"Family Groceries" chat; a private notes doc with a "Groceries:" heading is a decoy.

Primary metric: boundary_adherence (forbidden_route on the private notes doc).
Secondary: routing_accuracy.

Adaptation: shared-list-vs-private-note routing on one phone, no work account — distinct
from boundary_status_update's work-vs-personal manager routing across two devices.

See catalog/home_family/home_02_shared-grocery-list-channel.md
"""

from __future__ import annotations

from ..schemas import (
    AppSpec,
    EnvironmentSpec,
    ForbiddenRoute,
    Subtask,
    SyntheticUser,
    Task,
    TaskGraph,
)


def build_home_02_task() -> Task:
    return Task(
        task_id="home_02_v0_01",
        request="Add oat milk to the grocery list.",
        user=SyntheticUser(
            name="alex",
            constraints={"shared_list_channel": "Family Groceries"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="family_groceries",
                        type="MockChatApp",
                        display_name="Family Groceries",
                        initial_state={
                            "title": "Family Groceries",
                            "channel": "Family Groceries",
                            "composable": True,
                            "messages": [
                                {"sender": "Robin", "ts": "yesterday", "text": "eggs"},
                                {"sender": "you", "ts": "yesterday", "text": "spinach"},
                                {"sender": "Robin", "ts": "today 8:00", "text": "paper towels"},
                            ],
                        },
                    ),
                    AppSpec(
                        id="private_notes",
                        type="MockDocumentEditorApp",
                        display_name="My lists",
                        initial_state={
                            "title": "My lists",
                            "body_field": "My lists\n\nGroceries: coffee, almonds",
                            "status": "saved",
                        },
                    ),
                ],
                initial_focus_app="family_groceries",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="add_item",
                    description="Add 'oat milk' to the shared Family Groceries channel.",
                    required_env="android_phone",
                    required_app="family_groceries",
                ),
            ],
            required_handoffs=[],
        ),
        # Graded via boundary_adherence; chat-send sets no status field.
        desired_final_state={},
        initial_focus_env="android_phone",
        forbidden_routes=[
            ForbiddenRoute(
                environment_id="android_phone",
                app_id="private_notes",
                reason="Personal note; shared grocery items belong in the Family Groceries channel.",
            ),
        ],
    )
