"""Catalog sec_07: two six-digit codes are visible on the phone — the authenticator app
code (authoritative) and a decoy SMS code. Only the authenticator code is accepted by the
desktop identity form. Tests source-of-truth selection between duplicated, similar-looking
values.

Primary metric: source_of_truth — encoded by making the authenticator value the one the
form's expected_fields requires; the decoy SMS code leaves the form drafting.
Secondary: handoff_correctness, global_success.

See catalog/auth_security/sec_07_authoritative-authenticator-code.md
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

AUTH_CODE = "730164"   # authoritative
SMS_DECOY = "489203"   # decoy, rejected


def build_authenticator_vs_sms_task(
    auth_code: str = AUTH_CODE, sms_decoy: str = SMS_DECOY
) -> Task:
    return Task(
        task_id="authenticator_vs_sms_v0_01",
        request="Verify my identity on the Sentinel portal — it wants my authenticator code.",
        user=SyntheticUser(
            name="alex",
            constraints={"trust_order": "authenticator app code is authoritative over any SMS code"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="sentinel_portal",
                        type="MockBrowserFormApp",
                        display_name="Sentinel — Confirm with authenticator",
                        initial_state={
                            "title": "Sentinel — Confirm identity",
                            "hint": "Enter the code from your authenticator app.",
                            "success_text": "Identity confirmed.",
                            "fields": {"auth_code": ""},
                            "field_types": {"auth_code": "text"},
                            "expected_fields": {"auth_code": auth_code},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="sentinel_portal",
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
                        initial_state={"otp_code": auth_code},
                    ),
                    AppSpec(
                        id="sms",
                        type="MockChatApp",
                        display_name="Messages",
                        initial_state={
                            "title": "Messages",
                            "channel": "Sentinel (SMS)",
                            "composable": False,
                            # Decoy: looks like the right code, names "Sentinel", but is not accepted.
                            "messages": [
                                {"sender": "Sentinel", "ts": "now",
                                 "text": f"Sentinel: your code is {sms_decoy}"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="mock_authenticator",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_auth_code",
                    description="Read the authoritative authenticator code on the phone.",
                    required_env="android_phone",
                    required_app="mock_authenticator",
                ),
                Subtask(
                    id="verify_identity",
                    description="Enter the authenticator code on the desktop portal and submit.",
                    required_env="windows_desktop",
                    required_app="sentinel_portal",
                    depends_on=["read_auth_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="auth_code",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=auth_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.sentinel_portal.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
