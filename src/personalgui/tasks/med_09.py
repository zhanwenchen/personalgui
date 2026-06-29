"""Catalog med_09: move a delivery-confirmation reference number out of an email (the PDF
mirrors it) into a desktop tracking web form. Within-desktop value handoff.

The email body shows an order number "#774-9920" beside the tracking reference as a decoy;
only the tracking reference matches the form's expected_fields.

Primary metric: handoff_correctness. Secondary: global_success, routing_accuracy.

See catalog/media_files/med_09_pdf_reference_to_web_form.md
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

TRACKING_REF = "PLX-88241-RT"


def build_med_09_task(reference: str = TRACKING_REF) -> Task:
    email_body = (
        f"Tracking reference: {reference}. Order #774-9920, est. delivery 2026-07-01. "
        "The attached confirmation PDF lists the same reference."
    )
    return Task(
        task_id="med_09_v0_01",
        request="Track my Parcelink delivery — enter the reference from the confirmation PDF.",
        user=SyntheticUser(name="alex", constraints={"tracking_device": "windows_desktop"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="tracking_form",
                        type="MockBrowserFormApp",
                        display_name="Parcelink tracking",
                        initial_state={
                            "title": "Parcelink tracking",
                            "hint": "Enter the tracking reference from your confirmation.",
                            "success_text": "Tracking your parcel.",
                            "fields": {"reference": ""},
                            "field_types": {"reference": "text"},
                            "expected_fields": {"reference": reference},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                    AppSpec(
                        id="email",
                        type="MockEmailApp",
                        display_name="Email",
                        initial_state={
                            "title": "Email",
                            "threads": [
                                {
                                    "id": "plk1",
                                    "sender": "Parcelink",
                                    "subject": "Shipment confirmed — PL-2026",
                                    "ts": "today 8:14",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="tracking_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_reference",
                    description="Open the confirmation email and read the tracking reference.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="submit_tracking",
                    description="Paste the reference into the tracking form and submit.",
                    required_env="windows_desktop",
                    required_app="tracking_form",
                    depends_on=["read_reference"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="reference",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=reference,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.tracking_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
