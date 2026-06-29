"""Catalog com_05: tell #team the actual review time when two sources disagree. A Monday
calendar-invite email says 10:00; a newer Wednesday organizer chat says "moved the review
to 14:30, ignore the old invite." The newer chat is authoritative; the email time is stale.

Primary metric: source_of_truth — encoded (per README) by making the authoritative value
(14:30) the expected handoff value, so picking the stale 10:00 fails handoff_correctness.
Secondary: handoff_correctness (the authoritative time crosses into #team, same desktop).
Adaptation of catalog com_05_authoritative_meeting_time.md.

See catalog/comms_messaging/com_05_authoritative_meeting_time.md
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

AUTHORITATIVE_TIME = "14:30"  # newer chat, supersedes the invite
STALE_TIME = "10:00"          # Monday email invite, decoy


def build_com_05_task() -> Task:
    return Task(
        task_id="com_05_v0_01",
        request="Let the #team channel know what time the review actually is.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="email",
                        type="MockEmailApp",
                        display_name="Email",
                        initial_state={
                            "title": "Email",
                            "threads": [
                                {
                                    "id": "review_invite",
                                    "sender": "Calendar Invite",
                                    "subject": "Design review",
                                    "ts": "Mon 8:00",
                                    "body": (
                                        "Design review (Monday's invite): 10:00 AM in the "
                                        "main conference room."
                                    ),
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                    AppSpec(
                        id="organizer_chat",
                        type="MockChatApp",
                        display_name="Organizer DM",
                        initial_state={
                            "title": "Organizer DM",
                            "channel": "DM — Organizer",
                            "composable": False,
                            "messages": [
                                {"sender": "Organizer", "ts": "Wed 11:20",
                                 "text": "moved the review to 14:30, ignore the old invite"},
                            ],
                        },
                    ),
                    AppSpec(
                        id="team_chat",
                        type="MockChatApp",
                        display_name="#team",
                        initial_state={
                            "title": "#team",
                            "channel": "#team",
                            "composable": True,
                            "messages": [
                                {"sender": "Sam", "ts": "Wed 11:40",
                                 "text": "wait, what time is the review?"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="organizer_chat",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_sources",
                    description="Read both the email (10:00) and the newer organizer chat (14:30).",
                    required_env="windows_desktop",
                    required_app="organizer_chat",
                ),
                Subtask(
                    id="post_time",
                    description="Post the authoritative time (14:30) to #team.",
                    required_env="windows_desktop",
                    required_app="team_chat",
                    depends_on=["read_sources"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="review_time",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=AUTHORITATIVE_TIME,
                ),
            ],
        ),
        desired_final_state={},  # graded via source_of_truth (handoff_correctness on 14:30)
        initial_focus_env="windows_desktop",
    )
