"""Catalog med_02: read the grand total off a hardware-store receipt photo and file it as
a desktop expense report. Phone -> desktop value handoff.

The receipt photo shows a subtotal ($104.50) and tax line as decoys; only the grand total
matches expected_amount. Distinct from receipt_amount (Cafe Roma / $47.50): different
merchant, multi-line itemized receipt, subtotal-vs-total trap.

Primary metric: handoff_correctness. Secondary: global_success, routing_accuracy.

See catalog/media_files/med_02_hardware_receipt_to_expense.md
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

GRAND_TOTAL = "$112.86"
MERCHANT = "FerroMax Hardware"


def build_med_02_task(grand_total: str = GRAND_TOTAL) -> Task:
    return Task(
        task_id="med_02_v0_01",
        request="File the FerroMax hardware run as an expense — use the photo of the receipt.",
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
                            "expected_amount": grand_total,
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
                            # Subtotal ($104.50) and tax ($8.36) are decoys in the caption;
                            # only the grand total is the copyable value.
                            "amount": grand_total,
                            "merchant": f"{MERCHANT} — subtotal $104.50, tax $8.36, TOTAL {grand_total}",
                            "date": "2026-06-27",
                        },
                    ),
                ],
                initial_focus_app="phone_photos",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_total",
                    description="Read the grand total from the phone receipt photo.",
                    required_env="android_phone",
                    required_app="phone_photos",
                ),
                Subtask(
                    id="file_expense",
                    description="Enter the total + merchant on the desktop form and submit.",
                    required_env="windows_desktop",
                    required_app="expense_report",
                    depends_on=["read_total"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="amount",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=grand_total,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.expense_report.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
