"""v0 task #2: agent reads a receipt amount from the phone and enters it on the desktop expense report."""

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

DEFAULT_AMOUNT = "$47.50"
DEFAULT_MERCHANT = "Cafe Roma"


def build_receipt_amount_task(amount: str = DEFAULT_AMOUNT, merchant: str = DEFAULT_MERCHANT) -> Task:
    return Task(
        task_id="receipt_amount_v0_01",
        request=f"File the {merchant} receipt as an expense.",
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
                            "status": "drafting",
                            "expected_amount": amount,
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
                        display_name="Phone Photos",
                        initial_state={
                            "amount": amount,
                            "merchant": merchant,
                            "date": "2026-05-18",
                        },
                    ),
                ],
                initial_focus_app="phone_photos",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_amount",
                    description="Read the amount from the phone receipt photo.",
                    required_env="android_phone",
                    required_app="phone_photos",
                ),
                Subtask(
                    id="enter_amount",
                    description="Enter the amount and merchant into the desktop expense report and submit.",
                    required_env="windows_desktop",
                    required_app="expense_report",
                    depends_on=["read_amount"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="amount",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=amount,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.expense_report.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
