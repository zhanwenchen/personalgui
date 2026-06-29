"""Catalog trv_10: expense an airport-taxi receipt from a phone photo to the desktop report.

Two environments. The fare lives behind a phone receipt photo; the travel expense report is
desktop-only. Phone -> desktop handoff of the amount.

Primary metric: handoff_correctness (the exact fare must cross phone -> desktop intact).
Secondary: global_success (report flips to submitted), routing_accuracy.

Adaptation: same app pair as receipt_amount but with a different merchant ("SkyLine Taxi"),
amount ("$41.75"), and Aerolux-trip framing — distinct seed, not a duplicate. The merchant
is typed as a literal (not a handoff); only the amount is the value-checked handoff.

See catalog/travel/trv_10_taxi-receipt-expense.md
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

FARE = "$41.75"
MERCHANT = "SkyLine Taxi"


def build_trv_10_task(fare: str = FARE, merchant: str = MERCHANT) -> Task:
    return Task(
        task_id="trv_10_v0_01",
        request="Expense the cab I took to catch my Aerolux flight.",
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
                        display_name="Travel Expense Report",
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
                        display_name="Photos",
                        initial_state={
                            "merchant": merchant,
                            "amount": fare,
                            "date": "2026-07-09",
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
                    description="Enter the fare and merchant on the desktop form and submit.",
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
