"""Catalog fin_07: cancel a subscription using a confirmation code emailed by the vendor.

Single desktop environment, two apps. The cancellation code lives in an email; the
cancellation web form needs it. Within-desktop handoff (copy from email, paste into form).

Primary metric: handoff_correctness (the exact code must cross email -> form).
Secondary: global_success (form status flips to submitted).

See catalog/finance_expenses/fin_07_subscription-cancel-code.md
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

CANCEL_CODE = "CXL-7741"


def build_subscription_cancel_code_task(cancel_code: str = CANCEL_CODE) -> Task:
    email_body = (
        "You asked to cancel your StreamBox Premium subscription. To finish, enter this "
        f"cancellation confirmation code on the cancellation page:\n\n  {cancel_code}\n\n"
        "Your plan stays active until the end of the billing cycle."
    )
    return Task(
        task_id="subscription_cancel_code_v0_01",
        request="Finish cancelling the StreamBox subscription using the code StreamBox emailed you.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="cancel_form",
                        type="MockBrowserFormApp",
                        display_name="StreamBox — Cancel",
                        initial_state={
                            "title": "StreamBox — Cancel subscription",
                            "hint": "Enter the cancellation code from your email.",
                            "success_text": "Subscription cancelled.",
                            "fields": {"confirmation_code": ""},
                            "field_types": {"confirmation_code": "text"},
                            "expected_fields": {"confirmation_code": cancel_code},
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
                                    "id": "streambox_cancel",
                                    "sender": "StreamBox Billing",
                                    "subject": "Your cancellation code",
                                    "ts": "just now",
                                    "body": email_body,
                                },
                                {
                                    "id": "promo",
                                    "sender": "StreamBox",
                                    "subject": "Wait — 50% off if you stay!",
                                    "ts": "today 8:00",
                                    "body": "Use code STAY50 to keep your plan at half price.",
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="cancel_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_code",
                    description="Open the StreamBox email to read the cancellation code.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="submit_cancel",
                    description="Enter the cancellation code in the web form and submit.",
                    required_env="windows_desktop",
                    required_app="cancel_form",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="confirmation_code",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=cancel_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.cancel_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
