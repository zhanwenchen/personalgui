"""Catalog med_07: two near-identical receipt photos taken minutes apart at the same cafe;
"the receipt" is genuinely ambiguous, so the agent must clarify before filing.

Two MockPhotosApp instances (same merchant, close times, different amounts) plus a
composable chat where a clarifying reply could be voiced. Filing either blindly is wrong.

Primary metric: clarification_quality (requires_clarification, empty desired_final_state).
Secondary: routing_accuracy.

See catalog/media_files/med_07_clarify_which_receipt_photo.md
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

MERCHANT = "Cornerstone Cafe"


def build_med_07_task() -> Task:
    return Task(
        task_id="med_07_v0_01",
        request="File 'the receipt' I just photographed.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_photos",
                        type="MockPhotosApp",
                        display_name="Photos — receipt 11:58",
                        initial_state={
                            "amount": "$6.40",
                            "merchant": f"{MERCHANT} (own coffee)",
                            "date": "2026-06-28 11:58",
                        },
                    ),
                    AppSpec(
                        id="phone_photos_b",
                        type="MockPhotosApp",
                        display_name="Photos — receipt 12:01",
                        initial_state={
                            "amount": "$22.15",
                            "merchant": f"{MERCHANT} (colleague lunch, to split)",
                            "date": "2026-06-28 12:01",
                        },
                    ),
                    AppSpec(
                        id="phone_chat",
                        type="MockChatApp",
                        display_name="Messages",
                        initial_state={
                            "title": "Messages",
                            "channel": "Notes to self",
                            "composable": True,
                            "messages": [],
                        },
                    ),
                ],
                initial_focus_app="phone_photos",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="resolve_receipt",
                    description="Two similar receipt photos match 'the receipt'; agent must clarify which.",
                    required_env="android_phone",
                    required_app="phone_photos",
                ),
                Subtask(
                    id="file_resolved",
                    description="File the resolved receipt (only after clarifying).",
                    required_env="android_phone",
                    required_app="phone_photos",
                    depends_on=["resolve_receipt"],
                ),
            ],
            required_handoffs=[],
        ),
        desired_final_state={},  # clarification is the headline; filing either blindly is wrong
        initial_focus_env="android_phone",
        requires_clarification=True,
    )
