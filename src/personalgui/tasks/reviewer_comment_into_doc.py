"""Catalog wrk_01: paste a reviewer comment received in chat into the document body and
save. Within-desktop handoff (chat -> document) plus a document save gated on the comment
text being present.

Primary metric: handoff_correctness (the comment text crosses chat -> doc intact).
Secondary: global_success (doc status flips to saved once the required text is present).

See catalog/work_docs_projects/wrk_01_reviewer-comment-into-doc.md
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

REVIEWER_COMMENT = "Clarify the evaluation protocol in section 3."


def build_reviewer_comment_into_doc_task(comment: str = REVIEWER_COMMENT) -> Task:
    return Task(
        task_id="reviewer_comment_into_doc_v0_01",
        request="Add the reviewer's comment from chat into the draft and save it.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="review_chat",
                        type="MockChatApp",
                        display_name="Review Chat",
                        initial_state={
                            "title": "Review Chat",
                            "channel": "#paper-review",
                            "composable": False,
                            "messages": [
                                {"sender": "Reviewer (Dr. Okafor)", "ts": "today 10:11",
                                 "text": comment},
                                {"sender": "Reviewer (Dr. Okafor)", "ts": "today 10:12",
                                 "text": "Otherwise looks good — nice work."},
                            ],
                        },
                    ),
                    AppSpec(
                        id="draft_doc",
                        type="MockDocumentEditorApp",
                        display_name="Draft — Methods",
                        initial_state={
                            "title": "Draft — Methods",
                            "body_field": "## Methods\n\n(reviewer notes to incorporate below)\n",
                            "required_substrings": [comment],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="review_chat",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_comment",
                    description="Read the reviewer's comment in chat.",
                    required_env="windows_desktop",
                    required_app="review_chat",
                ),
                Subtask(
                    id="edit_and_save",
                    description="Put the comment into the document body and save.",
                    required_env="windows_desktop",
                    required_app="draft_doc",
                    depends_on=["read_comment"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="reviewer_comment",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=comment,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.draft_doc.status": "saved",
        },
        initial_focus_env="windows_desktop",
    )
