"""Catalog home_08: pay rent via a bank transfer that requires a 2FA code from the phone
authenticator, entered into a desktop transfer form. Cross-environment handoff
(phone -> desktop).

Primary metric: handoff_correctness. Secondary: global_success.

See catalog/home_family/home_08_rent-transfer-2fa.md
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

TRANSFER_2FA = "664120"


def build_rent_transfer_2fa_task(code: str = TRANSFER_2FA) -> Task:
    return Task(
        task_id="rent_transfer_2fa_v0_01",
        request=(
            "Send this month's rent transfer. The bank needs the 2FA code from your "
            "authenticator to authorize it."
        ),
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="transfer_form",
                        type="MockBrowserFormApp",
                        display_name="Apex Bank — Authorize transfer",
                        initial_state={
                            "title": "Apex Bank — Authorize rent transfer ($1,850 to Maple Property Mgmt)",
                            "hint": "Enter the 2FA code from your authenticator to authorize.",
                            "success_text": "Transfer authorized and scheduled.",
                            "fields": {"totp": ""},
                            "field_types": {"totp": "text"},
                            "expected_fields": {"totp": code},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="transfer_form",
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
                        initial_state={"otp_code": code},
                    ),
                ],
                initial_focus_app="mock_authenticator",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_2fa",
                    description="View the 2FA code on the phone authenticator.",
                    required_env="android_phone",
                    required_app="mock_authenticator",
                ),
                Subtask(
                    id="authorize_transfer",
                    description="Enter the 2FA code on the desktop transfer form and submit.",
                    required_env="windows_desktop",
                    required_app="transfer_form",
                    depends_on=["read_2fa"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="totp",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.transfer_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
