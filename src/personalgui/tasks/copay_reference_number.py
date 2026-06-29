"""Catalog hlth_10: pay a medical copay on a billing portal using the account/reference
number from the bill email. Within-desktop handoff (email -> billing form).

Decoy: the email shows both a statement number and a payment reference; the form needs the
payment reference.

Primary metric: handoff_correctness. Secondary: global_success.

See catalog/health_wellness/hlth_10_copay-reference-number.md
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

PAYMENT_REF = "PAY-553042"
STATEMENT_NO = "STMT-77310"  # decoy


def build_copay_reference_number_task(
    pay_ref: str = PAYMENT_REF, statement_no: str = STATEMENT_NO
) -> Task:
    email_body = (
        "Your visit copay is due. Pay online using your payment reference.\n\n"
        f"  Statement number: {statement_no}\n"
        f"  Payment reference: {pay_ref}\n"
        "  Amount due: $35.00\n"
    )
    return Task(
        task_id="copay_reference_number_v0_01",
        request="Pay my clinic copay online using the reference number from the bill email.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="billing_portal",
                        type="MockBrowserFormApp",
                        display_name="Riverside Clinic — Pay bill",
                        initial_state={
                            "title": "Riverside Clinic — Pay your bill",
                            "hint": "Enter your payment reference to pay the copay.",
                            "success_text": "Payment received. Thank you.",
                            "fields": {"payment_reference": ""},
                            "field_types": {"payment_reference": "text"},
                            "expected_fields": {"payment_reference": pay_ref},
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
                                    "id": "clinic_bill",
                                    "sender": "Riverside Clinic Billing",
                                    "subject": "Your copay is due",
                                    "ts": "today 7:50",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="billing_portal",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_reference",
                    description="Open the bill email and read the payment reference (not the statement number).",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="pay_copay",
                    description="Enter the payment reference in the billing portal and submit.",
                    required_env="windows_desktop",
                    required_app="billing_portal",
                    depends_on=["read_reference"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="payment_reference",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=pay_ref,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.billing_portal.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
