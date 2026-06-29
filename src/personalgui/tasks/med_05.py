"""Catalog med_05: send the latest Q2 report version to a colleague, not the stale one.
A long email thread has two attachments naming the same report; the newer (v2) by
timestamp is authoritative. The agent carries the v2 file name from email to chat
(within-desktop handoff).

The older file literally contains "final"; only the v2 name matches expected_value, so
trusting the filename over recency fails the handoff (source-of-truth encoding).

Primary metric: source_of_truth (authoritative value in expected_value). Secondary:
handoff_correctness, routing_accuracy.

See catalog/media_files/med_05_latest_report_version.md
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

LATEST_FILE = "Q2_report_final_v2.pdf"   # newest, authoritative
STALE_FILE = "Q2_report_final.pdf"       # older decoy ("final" in the name)


def build_med_05_task(latest_file: str = LATEST_FILE) -> Task:
    thread_body = (
        "Latest revision attached. The first file Q2_report_final.pdf (sent 2026-06-24) had a "
        "bad revenue table; Q2_report_final_v2.pdf (sent 2026-06-25) fixes it. Use v2."
    )
    return Task(
        task_id="med_05_v0_01",
        request="Send Priya the final Q2 report file from the email thread.",
        user=SyntheticUser(name="alex", constraints={"authoritative_source": "newest_attachment"}),
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
                                    "id": "q2rep",
                                    "sender": "Finance Team",
                                    "subject": "Q2 report — final",
                                    "ts": "2026-06-25 11:40",
                                    "body": thread_body,
                                    "attachments": [
                                        {"name": STALE_FILE, "ts": "2026-06-24 16:02"},
                                        {"name": latest_file, "ts": "2026-06-25 11:40"},
                                    ],
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                    AppSpec(
                        id="chat",
                        type="MockChatApp",
                        display_name="Chat — Priya",
                        initial_state={
                            "title": "Chat — Priya",
                            "channel": "Priya Nandakumar",
                            "composable": True,
                            "messages": [
                                {"sender": "Priya Nandakumar", "ts": "today",
                                 "text": "can you send me the final Q2 report?"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="email",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="find_latest",
                    description="Open the thread; identify the newest report attachment by timestamp.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="send_latest",
                    description="Send the latest version's file name to Priya's chat.",
                    required_env="windows_desktop",
                    required_app="chat",
                    depends_on=["find_latest"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="file",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=latest_file,
                ),
            ],
        ),
        desired_final_state={},  # graded via source_of_truth / handoff_correctness
        initial_focus_env="windows_desktop",
    )
