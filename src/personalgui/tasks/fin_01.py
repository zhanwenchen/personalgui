"""Catalog fin_01: file a taxi receipt photographed on the phone as a desktop expense.

The fare lives behind a photo on the phone; the corporate expense form is desktop-only.
The amount must cross android_phone -> windows_desktop intact.

Primary metric: handoff_correctness (the exact fare crosses phone -> desktop).
Secondary: global_success (expense report status flips to submitted), routing_accuracy.

See catalog/finance_expenses/fin_01_taxi-receipt-expense.md
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

FARE = "$63.20"
MERCHANT = "MetroCab"


def build_fin_01_task(fare: str = FARE, merchant: str = MERCHANT) -> Task:
    return Task(
        task_id="fin_01_v0_01",
        request="File my MetroCab ride from this morning as an expense.",
        user=SyntheticUser(name="alex", constraints={"expense_device": "windows_desktop"}),
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
                            "status": "drafting",
                            "expected_amount": fare,
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
                        display_name="Photos — MetroCab receipt",
                        initial_state={
                            "amount": fare,
                            "merchant": merchant,
                            "date": "2026-06-28",
                        },
                    ),
                ],
                initial_focus_app="phone_photos",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_fare",
                    description="Read the fare from the phone receipt photo.",
                    required_env="android_phone",
                    required_app="phone_photos",
                ),
                Subtask(
                    id="file_expense",
                    description="Enter the fare + merchant on the desktop form and submit.",
                    required_env="windows_desktop",
                    required_app="expense_report",
                    depends_on=["read_fare"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="amount",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=fare,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.expense_report.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
