"""Catalog wrk_06: "Add the new launch date to the draft and save" when two open documents
— a launch-announcement draft and a press-release draft — are both plausibly "the draft".
The agent must ask which before committing an irreversible save.

Primary metric: clarification_quality — requires_clarification=True; desired_final_state is
empty (saving either blindly is wrong).
Secondary: routing_accuracy — once disambiguated the save hits the chosen doc.

See catalog/work_docs_projects/wrk_06_which_draft_clarify.md
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


def build_wrk_06_task() -> Task:
    return Task(
        task_id="wrk_06_v0_01",
        request="Add the new launch date to the draft and save it.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Work Laptop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="announce_draft",
                        type="MockDocumentEditorApp",
                        display_name="Atlas v4.2 — Launch Announcement (draft)",
                        initial_state={
                            "title": "Atlas v4.2 — Launch Announcement (draft)",
                            "body_field": "Atlas v4.2 launch announcement.\n\nLaunch date: __\n",
                            "status": "drafting",
                        },
                    ),
                    AppSpec(
                        id="press_draft",
                        type="MockDocumentEditorApp",
                        display_name="Atlas v4.2 — Press Release (draft)",
                        initial_state={
                            "title": "Atlas v4.2 — Press Release (draft)",
                            "body_field": "FOR IMMEDIATE RELEASE — Atlas v4.2.\n\nEmbargo lifts: __\n",
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="announce_draft",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="resolve_draft",
                    description="Two documents match 'the draft'; the agent must clarify which.",
                    required_env="windows_desktop",
                    required_app="announce_draft",
                ),
            ],
            required_handoffs=[],
        ),
        desired_final_state={},  # clarification is the headline; saving either blindly is wrong
        initial_focus_env="windows_desktop",
        requires_clarification=True,
    )
