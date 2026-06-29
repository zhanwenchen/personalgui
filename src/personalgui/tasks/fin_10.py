"""Catalog fin_10: expense a Tokyo hotel using finance's approved USD conversion, not the
yen receipt amount.

The hotel receipt photo on the phone shows a yen amount (foreign-currency decoy); finance
emailed the agreed USD conversion (authoritative) to the desktop. The expense form must
carry the USD figure. The canonical handoff is within the desktop (email -> form); the
phone is present to create the cross-currency trap.

Primary metric: source_of_truth — encoded by making the USD figure the value
expected_amount / desired_final_state require; the yen amount is the decoy.
Secondary: handoff_correctness (USD crosses email -> form), global_success.

See catalog/finance_expenses/fin_10_currency-converted-amount.md
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

USD_AMOUNT = "$327.85"     # authoritative (finance email)
YEN_AMOUNT = "¥48,900"     # foreign-currency decoy (receipt photo)
MERCHANT = "Sakura Hotel Tokyo"


def build_fin_10_task(
    usd_amount: str = USD_AMOUNT, yen_amount: str = YEN_AMOUNT, merchant: str = MERCHANT
) -> Task:
    email_body = (
        f"Approved conversion for the Tokyo hotel: claim {usd_amount} USD "
        "(rate locked 2026-06-21)."
    )
    return Task(
        task_id="fin_10_v0_01",
        request="Expense the Tokyo hotel — claim the converted USD amount finance confirmed, not the yen.",
        user=SyntheticUser(
            name="alex",
            constraints={
                "reimburse_currency": "USD",
                "authoritative_conversion": "finance_email",
            },
        ),
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
                                    "id": "finance_fx",
                                    "sender": "Finance — FX desk",
                                    "subject": "Approved USD conversion — Tokyo hotel",
                                    "ts": "today 10:05",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                    AppSpec(
                        id="expense_report",
                        type="MockExpenseReportApp",
                        display_name="Expense Report",
                        initial_state={
                            "amount_field": "",
                            "merchant_field": "",
                            "status": "drafting",
                            "expected_amount": usd_amount,
                        },
                    ),
                ],
                initial_focus_app="expense_report",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_photos",
                        type="MockPhotosApp",
                        display_name="Photos — hotel receipt",
                        initial_state={
                            "amount": yen_amount,
                            "merchant": merchant,
                            "date": "2026-06-20",
                        },
                    ),
                ],
                initial_focus_app="phone_photos",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="see_receipt",
                    description="Note the foreign-currency receipt on the phone.",
                    required_env="android_phone",
                    required_app="phone_photos",
                ),
                Subtask(
                    id="read_usd",
                    description="Read the approved USD amount from finance's email.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="file_usd",
                    description="Enter the USD amount + merchant and submit.",
                    required_env="windows_desktop",
                    required_app="expense_report",
                    depends_on=["read_usd"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="amount",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=usd_amount,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.expense_report.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
