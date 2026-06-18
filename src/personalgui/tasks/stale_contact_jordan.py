"""Task G: stale contact info — source-of-truth on contact info.

Phone contacts has Jordan's phone number from 2 years ago (marked 'last verified 2024').
LinkedIn on the desktop has Jordan's current number from last month. The agent must
use the newer source to reach Jordan.

Same source-of-truth shape as standup_reminder but on contact info instead of a
meeting time.
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

STALE_PHONE = "+1-555-0142"
CURRENT_PHONE = "+1-555-0809"


def build_stale_contact_jordan_task() -> Task:
    return Task(
        task_id="stale_contact_jordan_v0_01",
        request="Text Jordan to set up a follow-up call next week.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="linkedin_profile",
                        type="MockProfileApp",
                        display_name="LinkedIn — Jordan",
                        initial_state={
                            "title": "LinkedIn",
                            "name": "Jordan Park",
                            "last_updated": "last month",
                            "fields": {
                                "headline": "Director of Platform, Helix",
                                "phone": CURRENT_PHONE,
                                "email": "jordan@helix.example",
                            },
                        },
                    ),
                    AppSpec(
                        id="desktop_chat",
                        type="MockChatApp",
                        display_name="iMessage",
                        initial_state={
                            "title": "iMessage",
                            "channel": "(new)",
                            "composable": True,
                            "messages": [],
                            "recipient_field": "",
                        },
                    ),
                ],
                initial_focus_app="linkedin_profile",
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
                                {"id": "jordan", "name": "Jordan Park",
                                 "label": "ex-coworker", "phone": STALE_PHONE,
                                 "last_verified": "2024-03"},
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
                    description="Find Jordan's current phone number — the LinkedIn profile is more recent than the phone contact.",
                    required_env="windows_desktop",
                    required_app="linkedin_profile",
                ),
                Subtask(
                    id="send_message",
                    description="Send the follow-up message using the current number.",
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
                    expected_value=CURRENT_PHONE,
                ),
            ],
        ),
        desired_final_state={},
        initial_focus_env="windows_desktop",
        # The stale number from the phone contacts must NOT cross into the message.
        forbidden_handoff_substrings=[STALE_PHONE],
    )
