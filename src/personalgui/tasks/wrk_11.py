"""Catalog wrk_11: file a publish request by carrying the runbook's EXACT title and CURRENT
version from the editor header into a web form. A changelog line names an older version
(v3.1.4) as a decoy; only the current v3.2.0 is accepted.

Primary metric: handoff_correctness — two required_handoffs carry the exact title and the
current version from the doc into the form.
Secondary: global_success (form status flips to submitted when both expected fields match),
routing_accuracy (both subtasks on the work laptop).

See catalog/work_docs_projects/wrk_11_publish_request_form.md
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

DOC_TITLE = "Atlas Incident Runbook"
CURRENT_VERSION = "v3.2.0"
OLD_VERSION = "v3.1.4"

DOC_BODY = (
    "Atlas Incident Runbook\n"
    f"Version: {CURRENT_VERSION}\n\n"
    "## Steps\n"
    "1. Page the on-call.\n"
    "2. Open the incident channel.\n\n"
    f"Changelog: {OLD_VERSION} added the dashboard links.\n"
)


def build_wrk_11_task(
    doc_title: str = DOC_TITLE, version: str = CURRENT_VERSION
) -> Task:
    return Task(
        task_id="wrk_11_v0_01",
        request=(
            "Submit the publish request for the runbook — use the doc's exact title and "
            "version from the editor."
        ),
        user=SyntheticUser(
            name="alex",
            constraints={"work_account": "alex@northwind.example"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Work Laptop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="runbook_doc",
                        type="MockDocumentEditorApp",
                        display_name="Atlas Incident Runbook",
                        initial_state={
                            "title": doc_title,
                            "body_field": DOC_BODY,
                            "status": "saved",
                        },
                    ),
                    AppSpec(
                        id="publish_form",
                        type="MockBrowserFormApp",
                        display_name="Publish Request",
                        initial_state={
                            "title": "Publish Request",
                            "hint": "Enter the document's exact title and version.",
                            "success_text": "Publish request submitted.",
                            "fields": {"doc_title": "", "version": ""},
                            "field_types": {"doc_title": "text", "version": "text"},
                            "expected_fields": {
                                "doc_title": doc_title,
                                "version": version,
                            },
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="runbook_doc",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_title_version",
                    description="Read the exact title and current version from the editor header.",
                    required_env="windows_desktop",
                    required_app="runbook_doc",
                ),
                Subtask(
                    id="submit_request",
                    description="Enter both into the publish-request form and submit.",
                    required_env="windows_desktop",
                    required_app="publish_form",
                    depends_on=["read_title_version"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="doc_title",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=doc_title,
                ),
                HandoffRequirement(
                    artifact_type="version",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=version,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.publish_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
