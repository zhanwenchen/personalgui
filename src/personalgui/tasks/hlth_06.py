"""Catalog hlth_06: start an insurance claim by filling in the member ID read off a photo of
the insurance card on the phone, into the desktop claim form. Phone -> desktop handoff.

Primary metric: handoff_correctness (the member ID must cross phone -> desktop).
Secondary: global_success (claim form submitted), routing_accuracy.
Adaptation: insurance member ID modeled as the card photo's copyable `amount` value; agent
enters it into a claim BrowserForm. Reuses MockPhotosApp + MockBrowserFormApp.

See catalog/health_wellness/hlth_06_insurance-member-id-claim.md
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

MEMBER_ID = "BRH-77A-309148"


def build_hlth_06_task(member_id: str = MEMBER_ID) -> Task:
    return Task(
        task_id="hlth_06_v0_01",
        request="Start my insurance claim — fill in my member ID from the photo of my card.",
        user=SyntheticUser(name="alex", constraints={"claim_device": "windows_desktop"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="claim_form",
                        type="MockBrowserFormApp",
                        display_name="BlueRidge Health — File a claim",
                        initial_state={
                            "title": "BlueRidge Health — Start a claim",
                            "hint": "Enter your member ID from your insurance card.",
                            "success_text": "Claim started.",
                            "fields": {"member_id": ""},
                            "field_types": {"member_id": "text"},
                            "expected_fields": {"member_id": member_id},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="claim_form",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_photos",
                        type="MockPhotosApp",
                        display_name="Photos — Insurance card",
                        initial_state={
                            # Member ID modeled as the copyable value on the card photo.
                            "amount": member_id,
                            "merchant": "BlueRidge Health",
                            "date": "2026-06-28",
                        },
                    ),
                ],
                initial_focus_app="phone_photos",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_member_id",
                    description="Read the member ID from the card photo.",
                    required_env="android_phone",
                    required_app="phone_photos",
                ),
                Subtask(
                    id="enter_member_id",
                    description="Enter the member ID on the claim form and submit.",
                    required_env="windows_desktop",
                    required_app="claim_form",
                    depends_on=["read_member_id"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="member_id",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=member_id,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.claim_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
