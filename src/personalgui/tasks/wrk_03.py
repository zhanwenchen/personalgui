"""Catalog wrk_03: complete a Q2 incident report by inserting the three required standard
sections (Summary / Root Cause / Action Items) before the editor will save.

Primary metric: global_success — the save is gated on all three exact section headings
being present in the body (required_substrings). A naive "click save on the partial draft"
leaves the doc in drafting.
Secondary: routing_accuracy — the only valid app is the report doc on the work laptop.

No handoff needed: the agent sets the whole body with type_ (which contains all three
headings) and saves.

See catalog/work_docs_projects/wrk_03_required_report_sections.md
"""

from __future__ import annotations

from ..schemas import (
    AppSpec,
    EnvironmentSpec,
    Subtask,
    SyntheticUser,
    Task,
    TaskGraph,
)

REQUIRED_SECTIONS = ["## Summary", "## Root Cause", "## Action Items"]

INITIAL_BODY = (
    "<!-- required: Summary / Root Cause / Action Items -->\n"
    "# Q2 Incident Report — INC-2026-118\n\n"
    "## Summary\n"
    "On 2026-05-12 the ingestion pipeline dropped events for ~40 minutes during a "
    "deploy.\n"
)


def build_wrk_03_task() -> Task:
    return Task(
        task_id="wrk_03_v0_01",
        request=(
            "Get the Q2 incident report ready to submit — it needs the standard sections "
            "before it can be saved."
        ),
        user=SyntheticUser(
            name="alex",
            constraints={"report_standard": "incident_v3"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Work Laptop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="report_doc",
                        type="MockDocumentEditorApp",
                        display_name="Q2 Incident Report — INC-2026-118",
                        initial_state={
                            "title": "Q2 Incident Report — INC-2026-118",
                            "body_field": INITIAL_BODY,
                            "required_substrings": list(REQUIRED_SECTIONS),
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="report_doc",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_checklist",
                    description="Read which three sections the standard requires.",
                    required_env="windows_desktop",
                    required_app="report_doc",
                ),
                Subtask(
                    id="add_sections_save",
                    description="Add the two missing section headings and save.",
                    required_env="windows_desktop",
                    required_app="report_doc",
                    depends_on=["read_checklist"],
                ),
            ],
            required_handoffs=[],
        ),
        desired_final_state={
            "windows_desktop.report_doc.status": "saved",
        },
        initial_focus_env="windows_desktop",
    )
