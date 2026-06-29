"""Catalog med_01: read a warranty code off a phone screenshot photo and register a
product on the desktop web form. Phone -> desktop value handoff.

The same photo shows decoys (model number "BW-220", "LOT 0419"); only the warranty code
matches the form's expected_fields, so hand-typing or grabbing a decoy fails.

Primary metric: handoff_correctness. Secondary: global_success, routing_accuracy.

See catalog/media_files/med_01_screenshot_code_to_form.md
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

WARRANTY_CODE = "BW-7Q4K-2310"


def build_med_01_task(warranty_code: str = WARRANTY_CODE) -> Task:
    return Task(
        task_id="med_01_v0_01",
        request="Use the warranty code from the screenshot I saved to register my Brightwave speaker.",
        user=SyntheticUser(name="alex", constraints={"registration_device": "windows_desktop"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="register_form",
                        type="MockBrowserFormApp",
                        display_name="Brightwave — Product registration",
                        initial_state={
                            "title": "Brightwave product registration",
                            "hint": "Enter the warranty code from your warranty card.",
                            "success_text": "Product registered.",
                            "fields": {"warranty_code": ""},
                            "field_types": {"warranty_code": "text"},
                            "expected_fields": {"warranty_code": warranty_code},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="register_form",
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
                            # Decoys (model "BW-220", "LOT 0419") live in the caption text;
                            # only the warranty code is the copyable value.
                            "amount": warranty_code,
                            "merchant": "Brightwave — Warranty card (model BW-220, LOT 0419)",
                            "date": "2026-06-25",
                        },
                    ),
                ],
                initial_focus_app="phone_photos",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_code",
                    description="Read the warranty code from the phone screenshot photo.",
                    required_env="android_phone",
                    required_app="phone_photos",
                ),
                Subtask(
                    id="register_product",
                    description="Paste the code into the desktop registration form and submit.",
                    required_env="windows_desktop",
                    required_app="register_form",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="warranty_code",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=warranty_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.register_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
