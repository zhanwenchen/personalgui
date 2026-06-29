"""Catalog shop_07: forward an order receipt's grand total into the expense report.

The Brightmark receipt lists subtotal/tax/shipping/order total in one block. The expense form
requires the exact grand total (the charged amount) plus the merchant; the prominent, round
subtotal is a decoy. A within-desktop, cross-domain handoff: copy the order total from the
email, paste into the expense report amount, type the merchant, submit.

Adaptation: MockEmailApp receipt thread embeds the total beside a tempting subtotal;
MockExpenseReportApp's expected_amount is the grand total.

Primary metric: handoff_correctness. Secondary: global_success, routing_accuracy.

See catalog/shopping_orders/shop_07_receipt_to_expense_report.md
"""

from __future__ import annotations

from ..schemas import (
    AppSpec,
    EnvironmentSpec,
    HandoffRequirement,
    Subtask,
    SyntheticUser,
    Task,
    TaskGraph,
)

ORDER_TOTAL = "$146.51"
SUBTOTAL = "$128.00"  # decoy: prominent, round-looking
MERCHANT = "Brightmark Supply"


def build_shop_07_task(
    order_total: str = ORDER_TOTAL, subtotal: str = SUBTOTAL, merchant: str = MERCHANT
) -> Task:
    email_body = (
        f"Thanks for your order from {merchant} (Order BM-7741). Here is your receipt:\n\n"
        f"  Subtotal: {subtotal}\n"
        "  Tax: $10.56\n"
        "  Shipping: $7.95\n"
        f"  Order total: {order_total}\n\n"
        "The order total is the amount charged to your card."
    )
    return Task(
        task_id="shop_07_v0_01",
        request="Add my Brightmark order total to this month's expense report.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="expense_report",
                        type="MockExpenseReportApp",
                        display_name="Expense Report",
                        initial_state={
                            "amount_field": "",
                            "merchant_field": "",
                            "expected_amount": order_total,
                            "status": "drafting",
                        },
                    ),
                    AppSpec(
                        id="email",
                        type="MockEmailApp",
                        display_name="Email",
                        initial_state={
                            "title": "Email",
                            "threads": [
                                {
                                    "id": "bm_receipt",
                                    "sender": "Brightmark Supply",
                                    "subject": "Your receipt — Order BM-7741",
                                    "ts": "today 11:20",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="expense_report",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_total",
                    description="Open the Brightmark receipt and read the order total (not the subtotal).",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="file_expense",
                    description="Enter the order total + merchant on the expense report and submit.",
                    required_env="windows_desktop",
                    required_app="expense_report",
                    depends_on=["read_total"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="amount",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=order_total,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.expense_report.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
