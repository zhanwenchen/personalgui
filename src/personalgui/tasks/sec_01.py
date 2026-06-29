"""Catalog sec_01: carry a new-device verification code from the phone authenticator to a
desktop "verify this device" web form.

A freshly set-up desktop is showing a Helios "verify this device" challenge. The matching
six-digit code rotates only in the phone authenticator, so the agent must read it on
android_phone and paste it into the windows_desktop form — a phone -> desktop OTP handoff
into a device-verification portal (not the expense sign-in portal of auth_handoff).

Primary metric: handoff_correctness — encoded by required_handoffs carrying the phone code
as expected_value; only copying it and pasting it into device_code satisfies the metric.
Secondary: global_success (form flips to submitted), routing_accuracy.

See catalog/auth_security/sec_01_new-device-verification.md
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

DEVICE_CODE = "518204"   # authoritative; rotates only on the phone authenticator
DEVICE_ID_DECOY = "HLS-LAP-77"  # on-screen device fingerprint, not the code


def build_sec_01_task(device_code: str = DEVICE_CODE) -> Task:
    return Task(
        task_id="sec_01_v0_01",
        request="Verify this new laptop on my Helios account — it's asking for a code.",
        user=SyntheticUser(
            name="alex",
            constraints={"authenticator_device": "android_phone"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="verify_device",
                        type="MockBrowserFormApp",
                        display_name="Helios — Verify this device",
                        initial_state={
                            "title": f"Helios — Verify this device (Device ID: {DEVICE_ID_DECOY})",
                            "hint": (
                                f"Device ID: {DEVICE_ID_DECOY}. Enter the verification code "
                                "from your authenticator app."
                            ),
                            "success_text": "Device verified.",
                            "fields": {"device_code": ""},
                            "field_types": {"device_code": "text"},
                            "expected_fields": {"device_code": device_code},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="verify_device",
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
                        initial_state={"otp_code": device_code},
                    ),
                ],
                initial_focus_app="mock_authenticator",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_code",
                    description="Read the rotating verification code on the phone authenticator.",
                    required_env="android_phone",
                    required_app="mock_authenticator",
                ),
                Subtask(
                    id="verify_device",
                    description="Enter the code on the desktop verify-this-device form and submit.",
                    required_env="windows_desktop",
                    required_app="verify_device",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="device_code",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=device_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.verify_device.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
