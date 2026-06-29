"""Catalog shop_04: confirm a high-value camera order with the phone authenticator 2FA code.

The retailer requires a one-time 2FA code to confirm an expensive order. The code lives only
in the authenticator app on the phone; the order-confirmation web form is on the desktop.
This forces a cross-env handoff: copy the OTP on android_phone, paste into the desktop form.

Adaptation: MockAuthenticatorApp holds the copyable OTP; MockBrowserFormApp's `otp` field
requires the exact six-digit code.

Primary metric: handoff_correctness (cross-env android_phone -> windows_desktop).
Secondary: global_success, routing_accuracy.

See catalog/shopping_orders/shop_04_confirm_order_2fa.md
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

OTP_CODE = "704913"


def build_shop_04_task(otp_code: str = OTP_CODE) -> Task:
    return Task(
        task_id="shop_04_v0_01",
        request="Confirm my Halverson camera order — it needs the 2FA code from my authenticator.",
        user=SyntheticUser(
            name="alex",
            constraints={"otp_source": "android_phone"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="confirm_form",
                        type="MockBrowserFormApp",
                        display_name="Halverson — Confirm order",
                        initial_state={
                            "title": "Halverson — confirm order",
                            "hint": "Enter the 2FA code from your authenticator app.",
                            "success_text": "Order confirmed.",
                            "fields": {"otp": ""},
                            "field_types": {"otp": "text"},
                            "expected_fields": {"otp": otp_code},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="confirm_form",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="authenticator",
                        type="MockAuthenticatorApp",
                        display_name="Authenticator (Halverson Photo)",
                        initial_state={"otp_code": otp_code},
                    ),
                ],
                initial_focus_app="authenticator",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_otp",
                    description="Read the current 2FA code from the phone authenticator.",
                    required_env="android_phone",
                    required_app="authenticator",
                ),
                Subtask(
                    id="confirm_order",
                    description="Enter the OTP in the confirmation form on the desktop and submit.",
                    required_env="windows_desktop",
                    required_app="confirm_form",
                    depends_on=["read_otp"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="otp",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=otp_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.confirm_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
