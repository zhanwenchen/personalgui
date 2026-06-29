"""Catalog fin_02: pay a vendor invoice on its portal using the emailed payment reference.

Both the email and the payment portal are open on the same desktop. The portal accepts
only the exact payment reference (not the more salient invoice number). Within-desktop,
cross-app handoff.

Primary metric: handoff_correctness (the exact payment reference crosses email -> form).
Secondary: global_success (portal status flips to submitted), routing_accuracy.

See catalog/finance_expenses/fin_02_invoice-payment-reference.md
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

PAYMENT_REFERENCE = "BLF-2026-77413"
INVOICE_NUMBER = "INV-3092"
AMOUNT_DUE = "$1,240.00"


def build_fin_02_task(
    reference: str = PAYMENT_REFERENCE,
    invoice: str = INVOICE_NUMBER,
    amount: str = AMOUNT_DUE,
) -> Task:
    email_body = (
        "Brightleaf Supplies payment notice.\n\n"
        f"  Invoice #: {invoice}\n"
        f"  Payment reference: {reference}\n"
        f"  Amount due: {amount}\n\n"
        "Enter the payment reference on our portal to pay this invoice."
    )
    return Task(
        task_id="fin_02_v0_01",
        request=(
            "Pay the Brightleaf Supplies invoice on their portal — the reference is in "
            "their email."
        ),
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="payment_portal",
                        type="MockBrowserFormApp",
                        display_name="Brightleaf — Pay invoice",
                        initial_state={
                            "title": "Brightleaf Supplies — Payment portal",
                            "hint": "Enter the payment reference from your email.",
                            "success_text": "Payment submitted.",
                            "fields": {"reference": "", "amount": ""},
                            "field_types": {"reference": "text", "amount": "text"},
                            "expected_fields": {"reference": reference, "amount": amount},
                            "buttons": ["submit"],
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
                                    "id": "brightleaf",
                                    "sender": "Brightleaf Supplies",
                                    "subject": "Payment notice — invoice due",
                                    "ts": "today 9:40",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="payment_portal",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_reference",
                    description="Open Brightleaf's email and read the payment reference.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="submit_payment",
                    description="Enter reference + amount on the portal form and submit.",
                    required_env="windows_desktop",
                    required_app="payment_portal",
                    depends_on=["read_reference"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="payment_reference",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=reference,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.payment_portal.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
