"""Catalog home_01: pay a household utility bill on the utility's web portal using the
account number from the billing email. Within-desktop, cross-app handoff (email -> form).

The email lists four numbers in close proximity (account number, meter number, customer
service phone, amount due); only the exact account number is accepted by the portal.

Primary metric: handoff_correctness (the account number must cross email -> form).
Secondary: global_success (form status flips to submitted), routing_accuracy.

Adaptation: a household electric-utility account number vs meter/phone decoys, distinct
from fin_02's vendor-invoice payment reference.

See catalog/home_family/home_01_utility-bill-payment-reference.md
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

ACCOUNT_NUMBER = "RP-4471-2208"
METER_NUMBER = "M-90871"          # decoy
SERVICE_PHONE = "1-800-555-0117"  # decoy
AMOUNT_DUE = "$138.42"


def build_home_01_task(
    account_number: str = ACCOUNT_NUMBER, amount_due: str = AMOUNT_DUE
) -> Task:
    email_body = (
        "Your Riverside Power statement is ready.\n\n"
        f"  Account number: {account_number}\n"
        f"  Meter #: {METER_NUMBER}\n"
        f"  Customer service: {SERVICE_PHONE}\n"
        f"  Amount due: {amount_due}\n\n"
        "Pay online by the due date to avoid a late fee."
    )
    return Task(
        task_id="home_01_v0_01",
        request="Pay the Riverside Power bill on their site — the account number is in their email.",
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
                        display_name="Riverside Power — Pay bill",
                        initial_state={
                            "title": "Riverside Power — Pay your bill",
                            "hint": "Enter your account number and the amount due.",
                            "success_text": "Payment submitted. Thank you.",
                            "fields": {"account": "", "amount": ""},
                            "field_types": {"account": "text", "amount": "text"},
                            "expected_fields": {
                                "account": account_number,
                                "amount": amount_due,
                            },
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
                                    "id": "riverside",
                                    "sender": "Riverside Power",
                                    "subject": "Your statement is ready",
                                    "ts": "today 6:10",
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
                    id="read_account",
                    description="Open Riverside Power's email and read the account number.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="submit_payment",
                    description="Enter the account number and amount on the portal and submit.",
                    required_env="windows_desktop",
                    required_app="payment_portal",
                    depends_on=["read_account"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="account_number",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=account_number,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.payment_portal.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
