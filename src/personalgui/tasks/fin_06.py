"""Catalog fin_06: file a client dinner but claim only up to the per-meal policy cap.

The dinner exceeded the cap. The authoritative cap is published on the internal policy
page (read-only profile); the higher receipt total is a decoy in a saved budget note. The
expense form requires the cap amount. Everything is on the desktop.

Primary metric: source_of_truth — encoded by making the cap the value expected_amount /
desired_final_state require; the receipt total is the (higher, more salient) decoy.
Secondary: handoff_correctness (cap crosses policy page -> form), global_success.

See catalog/finance_expenses/fin_06_meal-cap-policy-limit.md
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

PER_MEAL_CAP = "$75.00"      # authoritative (policy page)
RECEIPT_TOTAL = "$112.30"    # decoy (higher receipt total)
MERCHANT = "Harbor Grill"


def build_fin_06_task(
    cap: str = PER_MEAL_CAP, receipt_total: str = RECEIPT_TOTAL, merchant: str = MERCHANT
) -> Task:
    return Task(
        task_id="fin_06_v0_01",
        request="File the client dinner, but only claim up to the per-meal cap in our travel policy.",
        user=SyntheticUser(name="alex", constraints={"reimburse_rule": "per_meal_cap"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="policy_page",
                        type="MockProfileApp",
                        display_name="Travel & Expense Policy",
                        initial_state={
                            "title": "Travel & Expense Policy",
                            "name": "Travel & Expense Policy",
                            "fields": {
                                "per_meal_cap": cap,
                                "mileage_rate": "$0.67/mi",
                            },
                            "last_updated": "2026-01-15",
                        },
                    ),
                    AppSpec(
                        id="dinner_note",
                        type="MockDocumentEditorApp",
                        display_name="Dinner note",
                        initial_state={
                            "title": "Dinner note",
                            "body_field": f"Client dinner — {merchant} — receipt total {receipt_total}",
                            "status": "saved",
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
                            "expected_amount": cap,
                        },
                    ),
                ],
                initial_focus_app="expense_report",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_cap",
                    description="Read the per-meal cap from the policy page.",
                    required_env="windows_desktop",
                    required_app="policy_page",
                ),
                Subtask(
                    id="file_capped",
                    description="Enter the capped amount + merchant and submit.",
                    required_env="windows_desktop",
                    required_app="expense_report",
                    depends_on=["read_cap"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="amount",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=cap,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.expense_report.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
