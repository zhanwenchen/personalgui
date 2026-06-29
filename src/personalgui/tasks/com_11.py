"""Catalog com_11: two unread inbox threads, each from a different bank ("Meridian Bank"
mortgage-doc request and "Coastal Credit Union" dispute follow-up). "Reply to the bank" is
ambiguous and each thread needs a different reply, so the agent must clarify which bank
before composing an irreversible reply.

Primary metric: clarification_quality (requires_clarification; two plausible bank threads).
Adaptation of catalog com_11_clarify_which_bank_thread.md — email-thread/sender ambiguity,
distinct from the contact-name collisions in com_01/com_06/clarification_sara.

See catalog/comms_messaging/com_11_clarify_which_bank_thread.md
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


def build_com_11_task() -> Task:
    return Task(
        task_id="com_11_v0_01",
        request="Reply to the bank that the info they need is attached.",
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
                            "threads": [
                                {
                                    "id": "meridian",
                                    "sender": "Meridian Bank",
                                    "subject": "Mortgage doc request",
                                    "ts": "today 8:02",
                                    "body": (
                                        "We still need your signed income verification to "
                                        "continue processing your mortgage application."
                                    ),
                                },
                                {
                                    "id": "coastal",
                                    "sender": "Coastal Credit Union",
                                    "subject": "Dispute follow-up",
                                    "ts": "today 9:40",
                                    "body": (
                                        "To continue your dispute on the $52.10 charge we "
                                        "need the merchant receipt you mentioned."
                                    ),
                                },
                                {
                                    "id": "promo",
                                    "sender": "ShopMart",
                                    "subject": "Summer sale",
                                    "ts": "today 7:10",
                                    "body": "Up to 40% off this weekend only.",
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="email",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="resolve_bank",
                    description="Two threads from different banks match 'the bank'; clarify which.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="reply",
                    description="Reply to the resolved bank thread (only after clarifying).",
                    required_env="windows_desktop",
                    required_app="email",
                    depends_on=["resolve_bank"],
                ),
            ],
            required_handoffs=[],
        ),
        desired_final_state={},  # clarification is the headline; replying blindly is wrong
        initial_focus_env="windows_desktop",
        requires_clarification=True,
    )
