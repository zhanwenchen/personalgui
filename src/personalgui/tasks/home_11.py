"""Catalog home_11: confirm a plumber's appointment by entering the texted confirmation
code into the desktop service portal. Cross-environment handoff (phone -> desktop).

The phone holds an SMS-style message with the confirmation code (plus an opt-out line and a
promo thread); the desktop portal flips to submitted when the exact code is entered.

Primary metric: handoff_correctness (the alphanumeric code must cross phone -> desktop intact).
Secondary: global_success (portal submitted), routing_accuracy.

Adaptation: an alphanumeric contractor confirmation code in a phone message, entered into a
generic browser portal form — distinct from home_08/fin_04 (numeric OTP via authenticator).

See catalog/home_family/home_11_contractor-confirm-portal-code.md
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

CONFIRMATION_CODE = "PLM-58213"


def build_home_11_task(code: str = CONFIRMATION_CODE) -> Task:
    message_body = (
        "Your appointment is pending. "
        f"Confirmation code: {code}. Reply STOP to opt out."
    )
    return Task(
        task_id="home_11_v0_01",
        request=(
            "Confirm the plumber's appointment on the service portal — the code is in the "
            "text they sent."
        ),
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_messages",
                        type="MockEmailApp",
                        display_name="Messages",
                        initial_state={
                            "title": "Messages",
                            "threads": [
                                {
                                    "id": "plumber_confirm",
                                    "sender": "FlowRight Plumbing",
                                    "subject": "Appointment confirmation",
                                    "ts": "now",
                                    "body": message_body,
                                },
                                {
                                    "id": "promo",
                                    "sender": "HomeDeals",
                                    "subject": "20% off gutter cleaning this week",
                                    "ts": "today 8:00",
                                    "body": "Limited-time offer — book gutter cleaning today!",
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="phone_messages",
            ),
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="service_portal",
                        type="MockBrowserFormApp",
                        display_name="FlowRight — Confirm appointment",
                        initial_state={
                            "title": "FlowRight Plumbing — Confirm appointment",
                            "hint": "Enter the confirmation code from your text message.",
                            "success_text": "Appointment confirmed.",
                            "fields": {"code": ""},
                            "field_types": {"code": "text"},
                            "expected_fields": {"code": code},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="service_portal",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_code",
                    description="Open the plumber's text and read the confirmation code.",
                    required_env="android_phone",
                    required_app="phone_messages",
                ),
                Subtask(
                    id="confirm_appt",
                    description="Enter the code on the desktop service portal and submit.",
                    required_env="windows_desktop",
                    required_app="service_portal",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="confirmation_code",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.service_portal.status": "submitted",
        },
        initial_focus_env="android_phone",
    )
