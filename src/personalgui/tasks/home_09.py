"""Catalog home_09: text the babysitter using her NEW number from the updated sitter
profile, not the stale number in the phone Contacts entry. Phone holds the stale contact;
the desktop holds the authoritative profile and the chat to send from.

Primary metric: source_of_truth — encoded by making the current number (+1-555-0640) the
value required_handoffs / expected_value requires; the stale number is the decoy.
Secondary: handoff_correctness (the current number carried into the chat),
minimal_transfer (forbidden_handoff_substrings = the stale number).

Adaptation: the authoritative source is a sitter-profile directory and the trigger is a
recent number change — distinct from stale_contact_jordan (LinkedIn vs phone, ex-coworker).
Per the chat-send convention desired_final_state is empty; graded via handoff + source intent.

See catalog/home_family/home_09_babysitter-new-number-authoritative.md
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

STALE_NUMBER = "+1-555-0177"    # decoy (phone contacts)
CURRENT_NUMBER = "+1-555-0640"  # authoritative (updated profile)


def build_home_09_task() -> Task:
    return Task(
        task_id="home_09_v0_01",
        request="Text the babysitter to confirm Friday night.",
        user=SyntheticUser(
            name="alex",
            constraints={"authoritative_source": "the updated profile number overrides the old contact entry"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="sitter_profile",
                        type="MockProfileApp",
                        display_name="Priya — Sitter profile",
                        initial_state={
                            "title": "Sitter profile",
                            "name": "Priya — Sitter profile",
                            "last_updated": "last week",
                            "fields": {
                                "phone": CURRENT_NUMBER,
                                "rate": "$22/hr",
                            },
                        },
                    ),
                    AppSpec(
                        id="desktop_chat",
                        type="MockChatApp",
                        display_name="Messages",
                        initial_state={
                            "title": "Messages",
                            "channel": "(new)",
                            "composable": True,
                            "messages": [],
                            "recipient_field": "",
                        },
                    ),
                ],
                initial_focus_app="sitter_profile",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_contacts",
                        type="MockContactsApp",
                        display_name="Contacts",
                        initial_state={
                            "title": "Contacts",
                            "contacts": [
                                {"id": "priya", "name": "Priya (babysitter)",
                                 "label": "sitter", "phone": STALE_NUMBER,
                                 "last_verified": "2025-11"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="phone_contacts",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="find_current_number",
                    description="Read Priya's current number from the updated sitter profile.",
                    required_env="windows_desktop",
                    required_app="sitter_profile",
                ),
                Subtask(
                    id="send_message",
                    description="Send the Friday confirmation to the current number.",
                    required_env="windows_desktop",
                    required_app="desktop_chat",
                    depends_on=["find_current_number"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="phone_number",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=CURRENT_NUMBER,
                ),
            ],
        ),
        # Chat-send sets no status field; graded via source_of_truth (correct number)
        # + the within-env handoff, with the stale number forbidden.
        desired_final_state={},
        initial_focus_env="windows_desktop",
        forbidden_handoff_substrings=[STALE_NUMBER],
    )
