"""Catalog shop_11: confirm a subscribe-and-save recurring order with the emailed confirmation code.

The activation email shows the confirmation code (what the form accepts) alongside the plan ID,
which looks like the natural "subscription" identifier but is rejected. A within-desktop handoff:
copy the confirmation code from the email, paste into the confirmation form, submit to activate.

Adaptation: MockEmailApp thread embeds the confirmation code beside a decoy plan ID;
MockBrowserFormApp's `confirmation_code` field requires the exact confirmation code.

Primary metric: handoff_correctness. Secondary: global_success, routing_accuracy.

See catalog/shopping_orders/shop_11_subscribe_and_save_confirm.md
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

CONFIRMATION_CODE = "VP-SUB-3380"
PLAN_ID = "PLAN-90217"  # decoy: looks like the natural "subscription" identifier


def build_shop_11_task(
    confirmation_code: str = CONFIRMATION_CODE, plan_id: str = PLAN_ID
) -> Task:
    email_body = (
        "You're almost subscribed to Verdant Pantry subscribe-and-save!\n\n"
        f"  Confirmation code: {confirmation_code}\n"
        f"  Plan ID: {plan_id}\n"
        "  Ships every 4 weeks\n\n"
        "Enter the confirmation code to activate your recurring order."
    )
    return Task(
        task_id="shop_11_v0_01",
        request="Confirm my Verdant Pantry subscribe-and-save — use the confirmation code they emailed.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="subscribe_form",
                        type="MockBrowserFormApp",
                        display_name="Verdant Pantry — Confirm subscription",
                        initial_state={
                            "title": "Verdant Pantry — Confirm subscription",
                            "hint": "Enter the confirmation code from your email.",
                            "success_text": "Subscription active. Ships every 4 weeks.",
                            "fields": {"confirmation_code": ""},
                            "field_types": {"confirmation_code": "text"},
                            "expected_fields": {"confirmation_code": confirmation_code},
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
                                    "id": "vp_subscribe",
                                    "sender": "Verdant Pantry",
                                    "subject": "Confirm your subscribe-and-save",
                                    "ts": "today 12:05",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="subscribe_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_code",
                    description="Open the subscribe-and-save email and read the confirmation code (not the plan ID).",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="confirm_sub",
                    description="Enter the confirmation code in the form and submit to activate.",
                    required_env="windows_desktop",
                    required_app="subscribe_form",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="confirmation_code",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=confirmation_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.subscribe_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
