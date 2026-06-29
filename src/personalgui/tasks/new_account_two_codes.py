"""Catalog sec_03: create a new account that needs BOTH an email verification code and a
phone 2FA code entered into a single desktop web form. Two independent value-checked
handoffs (email -> desktop, phone -> desktop).

Primary metric: handoff_correctness (two codes must cross without corruption).
Secondary: global_success (form status flips to submitted), routing_accuracy.

See catalog/auth_security/sec_03_new-account-two-codes.md
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

EMAIL_CODE = "EMC-5521"
PHONE_2FA = "771243"


def build_new_account_two_codes_task(
    email_code: str = EMAIL_CODE, phone_code: str = PHONE_2FA
) -> Task:
    email_body = (
        "Welcome to Larkspur Cloud. To activate your account, enter this email "
        f"verification code on the activation page:\n\n  {email_code}\n\n"
        "Then complete the 2FA step with the code from your authenticator app."
    )
    return Task(
        task_id="new_account_two_codes_v0_01",
        request=(
            "Activate the new Larkspur Cloud account: enter the email verification code and "
            "the 2FA code from your authenticator on the activation page."
        ),
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="activation_form",
                        type="MockBrowserFormApp",
                        display_name="Larkspur Cloud — Activate",
                        initial_state={
                            "title": "Larkspur Cloud — Activate account",
                            "hint": "Enter the email code and the 2FA code from your authenticator.",
                            "success_text": "Account activated.",
                            "fields": {"email_code": "", "auth_code": ""},
                            "field_types": {"email_code": "text", "auth_code": "text"},
                            "expected_fields": {"email_code": email_code, "auth_code": phone_code},
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
                                    "id": "larkspur_welcome",
                                    "sender": "Larkspur Cloud",
                                    "subject": "Activate your account",
                                    "ts": "just now",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="activation_form",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="mock_authenticator",
                        type="MockAuthenticatorApp",
                        display_name="Authenticator",
                        initial_state={"otp_code": phone_code},
                    ),
                ],
                initial_focus_app="mock_authenticator",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_email_code",
                    description="Open the welcome email to read the verification code.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="read_2fa",
                    description="View the 2FA code on the phone authenticator.",
                    required_env="android_phone",
                    required_app="mock_authenticator",
                ),
                Subtask(
                    id="submit_activation",
                    description="Enter both codes on the activation form and submit.",
                    required_env="windows_desktop",
                    required_app="activation_form",
                    depends_on=["read_email_code", "read_2fa"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="email_code",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=email_code,
                ),
                HandoffRequirement(
                    artifact_type="auth_code",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=phone_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.activation_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
