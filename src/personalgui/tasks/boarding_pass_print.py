"""Catalog trv_11: move the boarding-pass file from the phone to the desktop print queue.

A genuine file handoff: the artifact is a file (by name), not a copied text value. Two
sibling images on the phone are decoys; only the boarding pass matches the queue's
expected_file.

Primary metric: handoff_correctness. Secondary: global_success, routing_accuracy.

Modeling note: uses MockFileShareApp (phone) + MockFileDropApp (desktop, framed as the
print queue; status flips to "received" = printed). The handoff value is the file name.

See catalog/travel/trv_11_boarding-pass-file-to-print.md
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

BOARDING_PASS = "boarding_pass_AX482.png"


def build_boarding_pass_print_task(file_name: str = BOARDING_PASS) -> Task:
    return Task(
        task_id="boarding_pass_print_v0_01",
        request="Print my boarding pass — it's the screenshot on my phone.",
        user=SyntheticUser(name="alex", constraints={"printer": "windows_desktop"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="print_queue",
                        type="MockFileDropApp",
                        display_name="Print Queue",
                        initial_state={
                            "title": "Print Queue",
                            "hint": "Send a file here to print it.",
                            "success_text": "Printed.",
                            "expected_file": file_name,
                            "status": "empty",
                        },
                    ),
                ],
                initial_focus_app="print_queue",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="fileshare",
                        type="MockFileShareApp",
                        display_name="Files",
                        initial_state={
                            "title": "Files",
                            "files": [
                                {"id": "f_bp", "name": file_name, "kind": "image"},
                                {"id": "f_rcpt", "name": "hotel_receipt.png", "kind": "image"},
                                {"id": "f_map", "name": "trip_map.png", "kind": "image"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="fileshare",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="select_file",
                    description="Select the boarding-pass image on the phone.",
                    required_env="android_phone",
                    required_app="fileshare",
                ),
                Subtask(
                    id="print_file",
                    description="Send the boarding pass to the desktop print queue and print.",
                    required_env="windows_desktop",
                    required_app="print_queue",
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
            "windows_desktop.print_queue.status": "received",
        },
        initial_focus_env="windows_desktop",
    )
