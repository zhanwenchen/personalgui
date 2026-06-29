"""Catalog fin_11: expense the receipt grand total (incl. tip), not the prominent subtotal.

The diner receipt photo's clean copyable amount is the grand total $58.10; the subtotal
$48.00 lives only in the caption as a tempting round decoy. The grand total must cross
android_phone -> windows_desktop.

Primary metric: source_of_truth — encoded by making the grand total the value
expected_amount / desired_final_state require; the subtotal is the caption decoy.
Secondary: handoff_correctness (grand total crosses phone -> desktop), global_success.

See catalog/finance_expenses/fin_11_tip-total-vs-subtotal.md
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

GRAND_TOTAL = "$58.10"   # authoritative (incl. tip)
SUBTOTAL = "$48.00"      # pre-tip decoy
TIP = "$10.10"
MERCHANT = "Bluebird Diner"


def build_fin_11_task(
    grand_total: str = GRAND_TOTAL, subtotal: str = SUBTOTAL, merchant: str = MERCHANT
) -> Task:
    caption = f"Subtotal {subtotal} · Tip {TIP} · TOTAL {grand_total}"
    return Task(
        task_id="fin_11_v0_01",
        request="Expense the Bluebird Diner receipt — file the full total including tip.",
        user=SyntheticUser(name="alex", constraints={"claim_basis": "grand_total"}),
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
                        display_name="Photos — Bluebird Diner receipt",
                        initial_state={
                            # The clean copyable amount is the grand total; the subtotal
                            # lives only in the caption as the decoy.
                            "amount": grand_total,
                            "merchant": merchant,
                            "date": "2026-06-25",
                            "caption": caption,
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
                    description="Read the grand total (incl. tip) from the receipt photo.",
                    required_env="android_phone",
                    required_app="phone_photos",
                ),
                Subtask(
                    id="file_total",
                    description="Enter the grand total + merchant on the desktop form and submit.",
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
