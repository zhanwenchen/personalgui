"""Catalog med_08: read handwritten Wi-Fi note text off a phone photo and transcribe it
into the desktop Home Info document, then save. Phone -> desktop value handoff.

The photo also shows a router serial decoy ("SN: 4471-AA") in the caption; only the exact
note text satisfies the document's required_substrings, so mis-reading fails the save.

Primary metric: handoff_correctness. Secondary: global_success, routing_accuracy.

See catalog/media_files/med_08_handwritten_note_to_doc.md
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

NOTE_TEXT = "Guest WiFi: maple-river-88"


def build_med_08_task(note_text: str = NOTE_TEXT) -> Task:
    return Task(
        task_id="med_08_v0_01",
        request="Type up the Wi-Fi note I photographed into my Home Info doc and save it.",
        user=SyntheticUser(name="alex", constraints={"notes_device": "windows_desktop"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="doc_editor",
                        type="MockDocumentEditorApp",
                        display_name="Home Info",
                        initial_state={
                            "title": "Home Info",
                            "body_field": "# Home Info\n\n",
                            "required_substrings": [note_text],
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
                        id="phone_photos",
                        type="MockPhotosApp",
                        display_name="Photos",
                        initial_state={
                            # Serial decoy "SN: 4471-AA" lives in the caption; only the note
                            # text is the copyable value.
                            "amount": note_text,
                            "merchant": "Handwritten note (corner scribble: SN: 4471-AA)",
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
                    id="read_note",
                    description="Read the handwritten note text from the phone photo.",
                    required_env="android_phone",
                    required_app="phone_photos",
                ),
                Subtask(
                    id="save_note",
                    description="Paste the note text into the Home Info doc and save.",
                    required_env="windows_desktop",
                    required_app="doc_editor",
                    depends_on=["read_note"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="note_text",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=note_text,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.doc_editor.status": "saved",
        },
        initial_focus_env="windows_desktop",
    )
