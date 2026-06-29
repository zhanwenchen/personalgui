"""Catalog shop_05: clarify which headphones order to return before starting an irreversible return.

Alex has two recent, equally plausible headphone orders (over-ear studio set + wireless
earbuds, both emails use the word "headphones"). They ship one day apart, so recency does not
disambiguate. Starting a return is irreversible (generates an RMA, schedules a pickup), so the
agent must ask which order before acting.

Adaptation: MockEmailApp with two order threads + a newsletter distractor; a generic
MockBrowserFormApp return form left drafting (never submitted blindly).

Primary metric: clarification_quality (requires_clarification). Secondary: routing_accuracy.

See catalog/shopping_orders/shop_05_clarify_which_headphones.md
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


def build_shop_05_task() -> Task:
    return Task(
        task_id="shop_05_v0_01",
        request="Return the headphones I ordered.",
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
                                    "id": "hp_studio",
                                    "sender": "Aurio Sound",
                                    "subject": "Your order has shipped",
                                    "ts": "2026-06-22",
                                    "body": (
                                        "Your over-ear studio headphones have shipped. "
                                        "Order #AU-5521. Eligible for return within 30 days."
                                    ),
                                },
                                {
                                    "id": "hp_buds",
                                    "sender": "Kestrel Audio",
                                    "subject": "Your order has shipped",
                                    "ts": "2026-06-23",
                                    "body": (
                                        "Your wireless headphones (earbuds) have shipped. "
                                        "Order #KA-8830. Eligible for return within 30 days."
                                    ),
                                },
                                {
                                    "id": "nl",
                                    "sender": "Gadget Weekly",
                                    "subject": "This week's audio deals",
                                    "ts": "2026-06-24",
                                    "body": "Top headphone picks and discount codes inside.",
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                    AppSpec(
                        id="return_form",
                        type="MockBrowserFormApp",
                        display_name="Start a return",
                        initial_state={
                            "title": "Start a return",
                            "hint": "Enter the order number to return.",
                            "success_text": "Return started.",
                            "fields": {"order_number": ""},
                            "field_types": {"order_number": "text"},
                            # Intentionally unsatisfiable referent: there is no single correct
                            # order, so a blind submit cannot succeed without clarifying first.
                            "expected_fields": {"order_number": "__needs_clarification__"},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="email",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="resolve_order",
                    description="Two headphone orders match 'the headphones'; the agent must clarify which.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="start_return",
                    description="Start the return for the resolved order (only after clarifying).",
                    required_env="windows_desktop",
                    required_app="return_form",
                    depends_on=["resolve_order"],
                ),
            ],
            required_handoffs=[],
        ),
        desired_final_state={},  # clarification is the headline; starting either return blindly is wrong
        initial_focus_env="windows_desktop",
        requires_clarification=True,
    )
