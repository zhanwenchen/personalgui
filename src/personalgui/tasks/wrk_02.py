"""Catalog wrk_02: update the spec doc with the AUTHORITATIVE throughput target from the
project board when the doc's own inline note and an #atlas-eng chat both carry a stale,
mutually-consistent value.

Primary metric: source_of_truth — encoded by requiring the board's "4,200 events/sec"
(via required_substrings + the within-env handoff expected_value); the doc's and chat's
"3,000"/"3k" are decoys that fail the save.
Secondary: handoff_correctness (the locked number crosses board -> doc), global_success
(doc status flips to saved once the authoritative value is present).

See catalog/work_docs_projects/wrk_02_authoritative_spec_number.md
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

AUTHORITATIVE_TARGET = "4,200 events/sec"  # locked on the project board
STALE_TARGET = "3,000 events/sec"          # superseded inline estimate (decoy)


def build_wrk_02_task(authoritative_target: str = AUTHORITATIVE_TARGET) -> Task:
    return Task(
        task_id="wrk_02_v0_01",
        request=(
            "Update the spec doc so the throughput target matches what the project board "
            "says it is now, and save."
        ),
        user=SyntheticUser(
            name="alex",
            constraints={"authoritative_source": "project_board"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Work Laptop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="project_board",
                        type="MockProfileApp",
                        display_name="Atlas Ingestion — Project Board",
                        initial_state={
                            "title": "Atlas Ingestion — Project Board (Locked Spec)",
                            "name": "Atlas Ingestion — Project Board (Locked Spec)",
                            "fields": {
                                "throughput_target": authoritative_target,
                                "status": "locked",
                                "scoped_on": "2026-06-22",
                            },
                            "last_updated": "2026-06-22",
                        },
                    ),
                    AppSpec(
                        id="spec_doc",
                        type="MockDocumentEditorApp",
                        display_name="Atlas Ingestion — Spec",
                        initial_state={
                            "title": "Atlas Ingestion — Spec",
                            "body_field": (
                                f"Throughput target: {STALE_TARGET} (initial estimate)\n"
                            ),
                            # Single authoritative substring so a paste that REPLACES the body
                            # with exactly the board number satisfies the save gate.
                            "required_substrings": [authoritative_target],
                            "status": "drafting",
                        },
                    ),
                    AppSpec(
                        id="atlas_chat",
                        type="MockChatApp",
                        display_name="#atlas-eng",
                        initial_state={
                            "title": "#atlas-eng",
                            "channel": "#atlas-eng",
                            "composable": False,
                            # Reinforcing decoy: a second stale source agreeing with the doc.
                            "messages": [
                                {"sender": "Sam", "ts": "2 weeks ago",
                                 "text": "let's plan around ~3k/sec for now"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="project_board",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_board",
                    description="Read the locked throughput target from the project board.",
                    required_env="windows_desktop",
                    required_app="project_board",
                ),
                Subtask(
                    id="update_spec",
                    description="Replace the stale target in the doc with the board's and save.",
                    required_env="windows_desktop",
                    required_app="spec_doc",
                    depends_on=["read_board"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="spec_number",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=authoritative_target,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.spec_doc.status": "saved",
        },
        initial_focus_env="windows_desktop",
    )
