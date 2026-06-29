"""Catalog fin_03: reconcile a charge against the authoritative posted bank amount.

A stale budgeting note estimates "~$210"; the bank statement record (authoritative
profile) shows the posted $218.47. The reconciliation form requires the posted figure.

Primary metric: source_of_truth — encoded by making the authoritative posted amount the
value expected_fields / desired_final_state require; the note's estimate is a decoy.
Secondary: handoff_correctness (posted amount crosses statement -> form), global_success.

See catalog/finance_expenses/fin_03_reconcile-authoritative-charge.md
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

POSTED_AMOUNT = "$218.47"   # authoritative (bank statement)
ESTIMATE = "$210.00"        # stale decoy (budgeting note)
MERCHANT = "Northwind Market"


def build_fin_03_task(
    posted_amount: str = POSTED_AMOUNT, estimate: str = ESTIMATE, merchant: str = MERCHANT
) -> Task:
    return Task(
        task_id="fin_03_v0_01",
        request="Reconcile the Northwind charge — submit the amount that actually posted to the account.",
        user=SyntheticUser(name="alex", constraints={"authoritative_source": "bank_statement"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="bank_statement",
                        type="MockProfileApp",
                        display_name="Bank Statement — Posted Transaction",
                        initial_state={
                            "title": "Northwind Market — Posted Transaction",
                            "name": "Northwind Market — Posted Transaction",
                            "fields": {
                                "merchant": merchant,
                                "posted_amount": posted_amount,
                                "date": "2026-06-26",
                            },
                            "last_updated": "2026-06-27",
                        },
                    ),
                    AppSpec(
                        id="budget_note",
                        type="MockDocumentEditorApp",
                        display_name="Budget note",
                        initial_state={
                            "title": "Budget note",
                            "body_field": f"Budget note: Northwind ~{estimate} (estimate)",
                            "status": "saved",
                        },
                    ),
                    AppSpec(
                        id="recon_form",
                        type="MockBrowserFormApp",
                        display_name="Reconciliation",
                        initial_state={
                            "title": "Reconcile charge",
                            "hint": "Enter the amount that posted to the account.",
                            "success_text": "Charge reconciled.",
                            "fields": {"amount": "", "merchant": ""},
                            "field_types": {"amount": "text", "merchant": "text"},
                            "expected_fields": {"amount": posted_amount, "merchant": merchant},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="recon_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_posted",
                    description="Read the posted amount from the bank statement record.",
                    required_env="windows_desktop",
                    required_app="bank_statement",
                ),
                Subtask(
                    id="submit_recon",
                    description="Enter the posted amount on the reconciliation form and submit.",
                    required_env="windows_desktop",
                    required_app="recon_form",
                    depends_on=["read_posted"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="amount",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=posted_amount,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.recon_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
