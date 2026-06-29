"""Catalog med_03: move the boarding-pass file from the phone to the desktop editor.

A file handoff (by name) phone -> desktop, received by the document editor: pasting the
file name into the doc body and saving stands in for "opened the file in the editor". A
sibling vacation image is the decoy.

Primary metric: handoff_correctness. Secondary: global_success, routing_accuracy.

See catalog/media_files/med_03_boarding_pass_file_handoff.md
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

BOARDING_PASS = "boardingpass_AX482.pdf"


def build_boarding_pass_to_editor_task(file_name: str = BOARDING_PASS) -> Task:
    return Task(
        task_id="boarding_pass_to_editor_v0_01",
        request="Send my boarding-pass PDF from my phone to the desktop and open it in the editor.",
        user=SyntheticUser(name="alex", constraints={"editing_device": "windows_desktop"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="doc_editor",
                        type="MockDocumentEditorApp",
                        display_name="Document Editor",
                        initial_state={
                            "title": "Document Editor",
                            "body_field": "",
                            "required_substrings": [file_name],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="doc_editor",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_files",
                        type="MockFileShareApp",
                        display_name="Files",
                        initial_state={
                            "title": "Files",
                            "files": [
                                {"id": "bp1", "name": file_name, "kind": "pdf", "date": "2026-06-28"},
                                {"id": "img9", "name": "vacation_dunes.jpg", "kind": "image", "date": "2026-06-27"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="phone_files",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="select_file",
                    description="Select the boarding-pass PDF on the phone.",
                    required_env="android_phone",
                    required_app="phone_files",
                ),
                Subtask(
                    id="open_in_editor",
                    description="Open the transferred file in the desktop editor and save.",
                    required_env="windows_desktop",
                    required_app="doc_editor",
                    depends_on=["select_file"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="file",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=file_name,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.doc_editor.status": "saved",
        },
        initial_focus_env="windows_desktop",
    )
