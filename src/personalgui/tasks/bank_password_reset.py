"""Task E: bank password reset — multi-source handoff.

A browser form on the desktop needs two pieces of evidence to reset a bank password:
  1. A verification code emailed by the bank (read from the desktop email app).
  2. A 2FA code from the phone authenticator.

Both must land in the right fields of the desktop browser form. Two independent
value-checked handoffs.
"""

from __future__ import annotations

from ..schemas import (
    AppSpec,
    EnvironmentSpec,
    HandoffRequirement,
    SyntheticUser,
    Subtask,
    Task,
    TaskGraph,
)

EMAIL_VERIFICATION_CODE = "847209"
PHONE_2FA_CODE = "335918"
NEW_PASSWORD = "B@nk-Reset-2026"


def build_bank_password_reset_task() -> Task:
    email_body = (
        "We received a password reset request for your account. If this was you, enter "
        f"this verification code on the reset page within 10 minutes:\n\n  {EMAIL_VERIFICATION_CODE}\n\n"
        "Then complete the 2FA challenge with your authenticator app."
    )
    return Task(
        task_id="bank_password_reset_v0_01",
        request=(
            "Reset your Apex Bank password. Use the email verification code and the 2FA "
            "code from your authenticator. New password: " + NEW_PASSWORD
        ),
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="bank_browser",
                        type="MockBrowserFormApp",
                        display_name="Apex Bank — Reset",
                        initial_state={
                            "title": "Apex Bank — Password reset",
                            "hint": "Enter the codes from your email and authenticator, then set a new password.",
                            "success_text": "Password reset. You may sign in with your new password.",
                            "fields": {
                                "verification_code": "",
                                "totp": "",
                                "new_password": "",
                            },
                            "field_types": {
                                "verification_code": "text",
                                "totp": "text",
                                "new_password": "password",
                            },
                            "expected_fields": {
                                "verification_code": EMAIL_VERIFICATION_CODE,
                                "totp": PHONE_2FA_CODE,
                                "new_password": NEW_PASSWORD,
                            },
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
                                    "id": "apex_reset",
                                    "sender": "Apex Bank Security",
                                    "subject": "Your verification code",
                                    "ts": "just now",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="bank_browser",
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
                        initial_state={"otp_code": PHONE_2FA_CODE},
                    ),
                ],
                initial_focus_app="mock_authenticator",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_email_code",
                    description="Open the bank email to read the verification code.",
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
                    id="submit_reset",
                    description="Submit the bank's password-reset form with both codes and the new password.",
                    required_env="windows_desktop",
                    required_app="bank_browser",
                    depends_on=["read_email_code", "read_2fa"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="verification_code",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=EMAIL_VERIFICATION_CODE,
                ),
                HandoffRequirement(
                    artifact_type="totp",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=PHONE_2FA_CODE,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.bank_browser.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
