"""Catalog hlth_11: fill the emergency-contact phone number on a clinic intake form using the
AUTHORITATIVE family-directory profile value, not the stale Contacts entry. Within-desktop
handoff (profile -> intake form).

Source-of-truth: Contacts holds Robin's OLD number (+1-555-0102); the profile directory
holds the NEW number (+1-555-0188, recently updated). The form only submits when
emergency_phone == the profile number.

Primary metric: source_of_truth — encoded by making the profile number the value the
intake form's expected_fields requires; the stale Contacts number is a decoy.
Secondary: handoff_correctness (phone number crosses profile -> form), global_success.
Adaptation: Contacts stale vs MockProfileApp authoritative; agent updates an
emergency-contact intake field with the authoritative number. Reuses MockContactsApp +
MockProfileApp + MockBrowserFormApp.

See catalog/health_wellness/hlth_11_emergency-contact-profile-source.md
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

NEW_PHONE = "+1-555-0188"   # authoritative (profile directory)
STALE_PHONE = "+1-555-0102"  # decoy (stale Contacts entry)


def build_hlth_11_task(new_phone: str = NEW_PHONE, stale_phone: str = STALE_PHONE) -> Task:
    return Task(
        task_id="hlth_11_v0_01",
        request="Update my emergency contact's phone number on the clinic intake form.",
        user=SyntheticUser(
            name="alex",
            constraints={"trust_order": "the family directory profile is authoritative over Contacts"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="contacts",
                        type="MockContactsApp",
                        display_name="Contacts",
                        initial_state={
                            "title": "Contacts",
                            # Stale: old carrier number, never updated after Robin switched.
                            "contacts": [
                                {"id": "c_robin", "name": "Robin (sibling)",
                                 "label": "Emergency contact", "phone": stale_phone},
                            ],
                            "focused_contact_id": None,
                        },
                    ),
                    AppSpec(
                        id="profile",
                        type="MockProfileApp",
                        display_name="Family Directory",
                        initial_state={
                            "title": "Family Directory",
                            "name": "Robin Avery",
                            "fields": {"emergency_phone": new_phone},
                            "last_updated": "2026-06-21",
                        },
                    ),
                    AppSpec(
                        id="intake_form",
                        type="MockBrowserFormApp",
                        display_name="Clinic — Intake form",
                        initial_state={
                            "title": "Riverside Clinic — Patient intake",
                            "hint": "Enter your emergency contact's current phone number.",
                            "success_text": "Intake saved.",
                            "fields": {"emergency_phone": ""},
                            "field_types": {"emergency_phone": "text"},
                            "expected_fields": {"emergency_phone": new_phone},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="contacts",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_authoritative",
                    description="Read the current number from the profile directory.",
                    required_env="windows_desktop",
                    required_app="profile",
                ),
                Subtask(
                    id="fill_intake",
                    description="Enter the current number on the intake form and submit.",
                    required_env="windows_desktop",
                    required_app="intake_form",
                    depends_on=["read_authoritative"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="phone",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=new_phone,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.intake_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
