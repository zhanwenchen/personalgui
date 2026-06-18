"""Task A: chained submit + notify.

File the receipt expense, then tell your manager in the work chat — the confirmation
code only exists AFTER the expense form is submitted, so the second handoff has to
come after the first. This task exercises a *generated* handoff value (the confirmation
code) rather than a static value pre-baked into the task spec.
"""

from __future__ import annotations

import hashlib

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


def _expected_confirmation_code(amount: str, merchant: str) -> str:
    # Mirror MockExpenseReportApp's submit-time derivation so the task spec can carry
    # the expected confirmation_code without running the app first.
    seed = (amount + merchant).encode()
    return "EXP-" + hashlib.sha256(seed).hexdigest()[:6].upper()


def build_expense_then_notify_task(
    amount: str = DEFAULT_AMOUNT,
    merchant: str = DEFAULT_MERCHANT,
) -> Task:
    confirmation = _expected_confirmation_code(amount, merchant)
    return Task(
        task_id="expense_then_notify_v0_01",
        request=(
            f"File the {merchant} receipt ({amount}) as an expense, then send your manager "
            f"the confirmation code in the work chat."
        ),
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
                    AppSpec(
                        id="work_chat",
                        type="MockChatApp",
                        display_name="Work Chat",
                        initial_state={
                            "title": "Work Chat",
                            "channel": "#manager-dm",
                            "composable": True,
                            "messages": [
                                {"sender": "Manager", "ts": "this morning",
                                 "text": "Once you file the Cafe Roma receipt, send me the confirmation code."},
                            ],
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
                            "date": "2026-05-21",
                        },
                    ),
                ],
                initial_focus_app="phone_photos",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="submit_expense",
                    description="Submit the receipt as an expense to obtain a confirmation code.",
                    required_env="windows_desktop",
                    required_app="expense_report",
                ),
                Subtask(
                    id="notify_manager",
                    description="Forward the confirmation code to the manager in work chat.",
                    required_env="windows_desktop",
                    required_app="work_chat",
                    depends_on=["submit_expense"],
                ),
            ],
            required_handoffs=[
                # Phone receipt amount must reach the desktop expense form.
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
            "windows_desktop.expense_report.confirmation_code": confirmation,
        },
        initial_focus_env="windows_desktop",
    )
