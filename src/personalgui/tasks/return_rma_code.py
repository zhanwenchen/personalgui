"""Catalog shop_01: start a return by copying the RMA (return authorization) code from the
order email into the retailer's return web form. Within-desktop handoff.

Decoy: the email also shows an order number that looks just as code-like; the form needs
the RMA code, not the order number.

Primary metric: handoff_correctness. Secondary: global_success.

See catalog/shopping_orders/shop_01_return-rma-code.md
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

RMA_CODE = "RMA-90817"
ORDER_NUMBER = "ORD-4471552"  # decoy


def build_return_rma_code_task(rma: str = RMA_CODE, order_no: str = ORDER_NUMBER) -> Task:
    email_body = (
        f"Your return for order {order_no} is approved. Enter this return authorization "
        f"(RMA) code on the returns page to print your label:\n\n  RMA code: {rma}\n"
    )
    return Task(
        task_id="return_rma_code_v0_01",
        request="Start the return for the headphones using the RMA code Northwind emailed you.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="return_form",
                        type="MockBrowserFormApp",
                        display_name="Northwind — Returns",
                        initial_state={
                            "title": "Northwind — Start a return",
                            "hint": "Enter the RMA code from your approval email.",
                            "success_text": "Return started. Your label is ready.",
                            "fields": {"rma_code": ""},
                            "field_types": {"rma_code": "text"},
                            "expected_fields": {"rma_code": rma},
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
                                    "id": "northwind_return",
                                    "sender": "Northwind Orders",
                                    "subject": "Your return is approved",
                                    "ts": "today 8:40",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="return_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_rma",
                    description="Open the approval email to read the RMA code (not the order number).",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="submit_return",
                    description="Enter the RMA code in the returns form and submit.",
                    required_env="windows_desktop",
                    required_app="return_form",
                    depends_on=["read_rma"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="rma_code",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=rma,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.return_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
